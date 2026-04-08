from typing import Annotated, TypedDict, List, Optional
from databricks_langchain import ChatDatabricks
from langchain_core.messages import BaseMessage
from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_core.runnables import RunnableConfig
from src.tools import retrieve_policy_context, get_flight_info
from langgraph.prebuilt import tools_condition
from pyspark.sql import SparkSession
import re
import gc
import json
from pydantic import BaseModel, Field
from langgraph.checkpoint.memory import MemorySaver
memory = MemorySaver()


# Configuration
LLM_ENDPOINT = "databricks-gpt-5-nano"
MODEL = ChatDatabricks(endpoint=LLM_ENDPOINT,extra_params={"reasoning_effort": "minimal"})
spark = SparkSession.builder \
    .appName("Consumer Guide to Air Travel") \
    .enableHiveSupport() \
    .getOrCreate()


model_with_tools = MODEL.bind_tools([get_flight_info, retrieve_policy_context],
    tool_choice="auto")
# State
class AgentState(TypedDict):
    messages: Annotated[List[BaseMessage], add_messages]
    flight_number: Optional[str]
    flight_date: Optional[str]
    flight_data: Optional[str]
    intent: Optional[str]
    origin: Optional[str]
    destination: Optional[str]
    policy_context: Optional[str]
    policy_chunks: Optional[List[str]]
    final_answer: Optional[str]
    airlines : Optional[str]
    current_query : Optional[str]


def extract_json(text):
    #print(" JSON Parse" ,text)
    match = re.search(r"\{.*\}", text, re.DOTALL)
    if match:
        return json.loads(match.group())
    else:
        raise ValueError("Sorry I couldnt understand your query. Kindly rephrase")

def clean_value(val):
    if val in ["null", "None", "", None]:
        return None
    return val

# Nodes

def fetch_flight_data(state: AgentState):

    flight_data = get_flight_info.func(
    flight_num=str(state["flight_number"]), 
    date =  str(state["flight_date"])
    )
    return {"flight_data": flight_data}

def classify_intent(state: AgentState, config: RunnableConfig):
    query = state["messages"][-1].content
    prompt = f"""
    Classify the intent and extract entities:

    Allowed intents:
    - delay
    - cancellation
    - accommodation 
    - baggage
    - compensation
    - general
    
    Extraction Rules for Entities:
    1. flight_number: Extract ONLY the numeric digits (e.g., if input is "AA123", extract "123").
    2. airlines: Extract ONLY the airline code or the 2-letter IATA code (e.g., if input is "AA123", extract "AA").
    3. date: Convert any mentioned date to YYYY-MM-DD format.

    Examples:
    - "My flight AA123 is delayed" -> {{"intent": "delay", "flight_number": "123", "airlines": "AA", "date": "null"}}
    - "Is BA 99 cancelled for tomorrow?" -> {{"intent": "cancellation", "flight_number": "99", "airlines": "BA", "date": "2026-04-06"}}

    Return ONLY valid JSON:
    {{
        "intent": "...",
        "flight_number": "...",
        "date": "...",
        "airlines": "..."
    }}

    Query: {query}
    """

    response = model_with_tools.invoke(prompt,config=config)
    parsed_response = extract_json(response.content)

    airlines = clean_value(parsed_response.get("airlines"))
    flight_number = clean_value(parsed_response.get("flight_number"))
    flight_date = clean_value(parsed_response.get("date"))

    return {
        "messages": [response],
        "intent": parsed_response.get("intent"),
        "flight_number": flight_number or state.get("flight_number"),
        "flight_date": flight_date or state.get("flight_date"),
        "airlines": airlines or state.get("airlines"),
        "current_query" : query
    }

def route_based_on_intent(state: AgentState):
    #print("Routing Policy ",state)
    intent = state["intent"]
    #print("Current Intent :", intent)

    if intent in ["delay", "cancellation"]:
        policy_chunks = "policy_and_flight"
    elif intent in ["baggage","compensation","accommodation"]:
        policy_chunks = "policy_only"
    else:
        policy_chunks = "general"
    return  policy_chunks
    
def get_last_value(state, key, default=None):
    """
    Retrieve the last value stored for a key in AgentState.
    """
    if key in state and state[key]:
        return state[key][-1] if isinstance(state[key], list) else state[key]
    return default

def fetch_policy(state: AgentState):
    airline_code = get_last_value(state, "airlines", None)
    context = retrieve_policy_context.invoke({"query":state["messages"][-1].content,"airline_code":airline_code,"policy_context":state.get("intent", "general")})
    #print("context ", context)
    return { "policy_context": context}

def determine_rights(state: AgentState, config: RunnableConfig):
    query = state.get("current_query","summarise the flight_data")
    #print("DEBUG STATE:determine_rights - query", query)
    flight_data = state.get("flight_data","None provided")
    
    #print("Flight data is ",flight_data)
    policy_context = state.get("policy_context", None)
    if not state.get("policy_context"):
        policy_context = "No airline-specific policy found."
    else:
        policy_context = policy_context[-1]
    #print("policy_context is ",policy_context)
    prompt = f"""
    You are a Passenger Rights Advocate. Your goal is to answer the User Query using the provided context.

    Flight Data:
    {flight_data}

    Policy Context:
    {policy_context}

    Question:
    {query}

    Determine:
    - If flight details are available, Summarise the flight_data 
    - Identify any issues (delays, cancellations, mismatches).
    - Answer the query based *only* on this flight_data with the policy_context.
    - If no flight_data is available or says "None provided", look at policy_context and rely only on general policy guidance
    - If only flight_data is provided, summarize the flight_data with what went wrong 
    - If neither flight_data nor  policy_context provides an answer, state that you do not have enough information.
    - What went wrong
    - Passenger rights
    - Compensation eligibility
    - Suggested actions
    - Be precise and concise.
    - Do not generalize.
    """
 
    response = model_with_tools.invoke(prompt,config=config)
    print(response.content)
    return {
        "messages": [response], 
        "final_answer": response.content,
        "flight_data": flight_data, 
        "airlines" :   state.get("airlines"),
        "flight_date" :state.get("flight_date"), 
        "flight_number": state.get("flight_number")
    }


def build_agent():
    workflow = StateGraph(AgentState)
    workflow.add_node("intent_classifier", classify_intent)
    workflow.add_node("flight_details", fetch_flight_data)
    workflow.add_node("policy", fetch_policy)
    workflow.add_node("advocate", determine_rights)
    workflow.add_edge(START, "intent_classifier")
    workflow.add_conditional_edges(
    "intent_classifier",
    route_based_on_intent,
    {
        "policy_and_flight": "flight_details",
        "policy_only": "policy",
        "general": "advocate"
    }
    )
    workflow.add_edge("flight_details", "policy")
    workflow.add_edge("policy", "advocate")
    workflow.add_edge("advocate", END)
    return workflow.compile(checkpointer=memory)

agent_app = build_agent()