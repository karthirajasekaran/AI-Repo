Summary : 
  The task is to build a Python application where an LLM Agent acts as a Travel Advocate. 

Design: 
  Data sources: We have two data source
    - a table with the flight details
    - a text file listing the policies of the flight 
  
    Architecture:
    User Query -> Orchestrator -> Intent Classifier -> Routing Layer  -> Agent -> Flight Data Tool (Databricks / Spark) ->  Policy Retrieval Tool (ChromaDB RAG) -> Response Generator -> User Response

    -  Databricks Model Serving is used for llm.
    -  Orchestration is done using Langgraph 
    -  RAG framework is used for policy retrieval .
    -  Spark framework is used for flight data retrival 

    RAG  
     - ChromaDB is used to ingest the policy data as vectors 
     - There is a seperate RAG ingestion pipeline created in the notebooks - refer the comments 
     - The ingestion is done based on the airlines classification, so that the relevant information is retrived. 
     - Retrieval is done using Vector Search Client using HuggingFace Embedding Model 
    
    AGENT 
     -  OpenAI GPT-5 nano Databricks-hosted foundation llm used 
     -  Langgraph is used for orchestration 
     -  There was a intent classifier which classifies the purpose of the query.
     -  Based on the purpose of the query . The agent was instructed to provide the details of the policies relavant to the airlines and the query provided.
     -  There is a router implemented to decide whether to go and fetch the flight details based in the flight data provided
     -  Also if the flight data is provided the agent fetches the relavant data from the spark and provide the summary of the data to the decision maker of the agent. 
     - There is a determin_rights function which decides the response to the user based in the flight data, context of the query and the query combined together

     PROMPTS
     - relavant basic prompts are used to instruct the llms to decide on the replies to the users query. 

    Trade offs :
     The memory was very less and there were restrictions on the cluster. I have retrict with using ChromaDB rather than Databricks for storing the vector db
     The prompts were direcly used as the prompt engineering in itself was a separate design
     The cluster was too small for the excercise and kept crashing so has to be careful on using the additional libraries etc. 

    Retrospective 
      The size of the cluster could have been better as it ended up crashing and couldnt debug the memory parameters of the cluster without admin rights. 
      
