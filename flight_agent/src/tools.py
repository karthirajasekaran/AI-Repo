## TODO: Define your Structured Tools here.
from langchain_core.tools import tool
from typing import  Optional
import chromadb
from langchain_chroma import Chroma
from langchain_huggingface import HuggingFaceEmbeddings
from pyspark.sql import SparkSession

spark = SparkSession.builder \
    .appName("Consumer Guide to Air Travel") \
    .enableHiveSupport() \
    .getOrCreate()
   

# TOOL 1: SQL Flight Status
@tool
def get_flight_info(flight_num: str, date: str):
    """
    Query the ontime_cleaned table for delay minutes and cancellation codes.
    Use this to get the facts of what happened to a flight.
    """
    #print("Fetching flight details")
    query = f"SELECT * FROM hive_metastore.default.ontime_cleaned WHERE Flight_Number_Reporting_Airline = '{flight_num}' AND FlightDate = '{date}'"
    #print(query)
    return summarize_flight_data(spark.sql(query).toPandas().to_dict(orient="records"))

@tool
def retrieve_policy_context(query: str,airline_code: Optional[str] = None,policy_context: Optional[str] = None):
    """
    Fetch the right policy for a given query for all airlines.
    """

    client = chromadb.PersistentClient(path="dbfs:/user/hive/warehouse/krajasekaran.db/chroma_db_krajasekaran")
    #print("Vector Store retrieval")
    airlines=  {
        "AS": "Alaska Airlines",
        "G4": "Allegiant Air",
        "AA": "American Airlines",
        "DL": "Delta Air Lines",
        "F9": "Frontier Airlines",
        "HA": "Hawaiian Airlines",
        "B6": "JetBlue Airways",
        "WN": "Southwest Airlines",
        "NK": "Spirit Airlines",
        "UA": "United Airlines"
        }
    
    embeddings = HuggingFaceEmbeddings(model_name="all-MiniLM-L6-v2")
    vector_store = Chroma(
        client=client,
        collection_name="travel_policy_collection",
        embedding_function=embeddings
    )
    search_kwargs = {"k": 3}
    if airline_code:
        search_kwargs["filter"] = {"airline_name": airlines.get(airline_code.upper(),"general").lower()}
    else:
        search_kwargs["filter"] = {"airline_name": "general"}
    #print("Vector Store retrieval arguements" ,search_kwargs)
    retriever = vector_store.as_retriever(search_kwargs=search_kwargs)
    filtered_docs = retriever.invoke(query)
    if filtered_docs:
        return [d.page_content for d in filtered_docs]
    # fallback
    search_kwargs["filter"] = {"airline_name": "general"}
    retriever = vector_store.as_retriever(search_kwargs=search_kwargs)
    filtered_docs = retriever.invoke(query)
    return [d.page_content for d in filtered_docs]  

def summarize_flight_data(flight_rows):

    if not flight_rows:
        return "No flight data found for this query."

    summaries = ""
    row = flight_rows[0]
    summary = f"""
        Flight {row['Flight_Number_Reporting_Airline']} on {row['FlightDate']} 
        from {row['OriginCityName']} to {row['DestCityName']}:
        - Departure delay: {row['DepDelay']} minutes
        - Arrival delay: {row['ArrDelay']} minutes
        - Cancelled: {row['Cancelled']}
        - Diverted: {row['Diverted']}
        - Airline: {row['Reporting_Airline']}
        """

    return summary





