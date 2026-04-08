# TODO: Define your Retrieval logic here.
import pandas as pd
from langchain_text_splitters import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import TextLoader

def ingest_policies(policy_file_path: str, ontime_dict_file_path: str):
    docs = []
    for file in [policy_file_path, ontime_dict_file_path]:
        loader = TextLoader(file)
        docs.extend(loader.load())

    splitter = RecursiveCharacterTextSplitter(chunk_size=1000, chunk_overlap=100)
    chunks = splitter.split_documents(docs)

    # 2. Pushing to Delta Table (Required for Databricks Vector Search)
    from pyspark.sql import SparkSession
    spark = SparkSession.builder \
        .appName("Consumer Guide to Air Travel") \
        .enableHiveSupport() \
        .getOrCreate()
    table_path = "hive_metastore.krajasekaran.travel_knowledge_base"
    df = spark.createDataFrame([{"id": i, "content": c.page_content, "metadata": str(c.metadata)} for i, c in enumerate(chunks)])
    df.write.format("delta").mode("overwrite").option("delta.enableChangeDataFeed", "true").saveAsTable(table_path)
    return 

def embed_policies_using_chromadb():

    from pyspark.sql import SparkSession
    spark = SparkSession.builder \
        .appName("Consumer Guide to Air Travel") \
        .enableHiveSupport() \
        .getOrCreate()
    # Load your data from the legacy hive_metastore
    df = spark.table("hive_metastore.krajasekaran.travel_knowledge_base")

    # Converting to a list of strings (assuming 'text_column' contains your data)
    documents = [row.content for row in df.select("content").collect()]
    metadatas = [{"id": i} for i in range(len(documents))]
    ids = [str(i) for i in range(len(documents))]
    import chromadb
    from chromadb.utils import embedding_functions
    client = chromadb.PersistentClient(path="dbfs:/user/hive/warehouse/krajasekaran.db/chroma_db_krajasekaran")
    # Creating a collection (similar to a table in SQL)
    # Using a default HuggingFace model for embeddings (all-MiniLM-L6-v2)
    emb_fn = embedding_functions.DefaultEmbeddingFunction()
    collection = client.get_or_create_collection(name="travel_policy_collection", embedding_function=emb_fn)

    # Adding documents to the collection
    collection.add(
        documents=documents,
        metadatas=metadatas,
        ids=ids
)

def embed_policies_using_chromadb_updated_with_airlines():

    from pyspark.sql import SparkSession
    import chromadb
    from chromadb.utils import embedding_functions

    spark = SparkSession.builder \
        .appName("Consumer Guide to Air Travel") \
        .enableHiveSupport() \
        .getOrCreate()

    df = spark.table("hive_metastore.krajasekaran.travel_knowledge_base")

    rows = df.select("content").collect()

    documents = [row["content"] for row in rows]

    # ✅ Infer airline name
    def infer_airline_name(text):
        text = text.lower()
        if "united" in text:
            return "united airlines"
        elif "delta" in text:
            return "delta air lines"
        elif "american" in text:
            return "american airlines"
        elif "southwest" in text:
            return "southwest airlines"
        elif "jetblue" in text:
            return "jetblue airways"
        elif "alaska" in text:
            return "alaska airlines"
        elif "spirit" in text:
            return "spirit airlines"
        elif "frontier" in text:
            return "frontier airlines"
        elif "hawaiian" in text:
            return "hawaiian airlines"
        elif "allegiant" in text:
            return "allegiant air"
        else:
            return "general"

    metadata = [
        {
            "id": str(i),
            "airline_name": infer_airline_name(row["content"])
        }
        for i, row in enumerate(rows)
    ]

    ids = [str(i) for i in range(len(documents))]

    client = chromadb.PersistentClient(
        path="dbfs:/user/hive/warehouse/krajasekaran.db/chroma_db_krajasekaran"
    )

    emb_fn = embedding_functions.DefaultEmbeddingFunction()

    # 🔥 IMPORTANT: reset collection
    try:
        client.delete_collection("travel_policy_collection")
    except:
        pass

    collection = client.get_or_create_collection(
        name="travel_policy_collection",
        embedding_function=emb_fn
    )

    collection.add(
        documents=documents,
        metadatas=metadata,
        ids=ids
    )

    

def embed_policies():
    from databricks.vector_search.client import VectorSearchClient
    vsc = VectorSearchClient()
    # 1. Create a Vector Search Endpoint (if you don't have one)
    vsc.create_endpoint(name="travel_policy_endpoint", endpoint_type="STANDARD")
    # 2. Create the Index (Delta Sync automatically handles embedding)
    vsc.create_delta_sync_index(
        endpoint_name="travel_policy_endpoint",
        source_table_name="hive_metastore.krajasekaran.policy_chunks",
        index_name="hive_metastore.krajasekaran.policy_index",
        pipeline_type='TRIGGERED',
        primary_key="id", # Ensure your table has a unique ID column
        embedding_source_column="content",
        embedding_model_endpoint_name="databricks-gte-large-en" # High-quality managed model
    )
    return 
    
def data_retrieval_based_on_client(query: str):
    from databricks.vector_search.client import VectorSearchClient
    vsc = VectorSearchClient()
    # 3. Run a Vector Search Query
    results = vsc.query_endpoint(
        endpoint_name="travel_policy_endpoint",
        index_name="hive_metastore.krajasekaran.policy_index",
        query=query,
        top_k=3,
        filter=None,
        return_embedding=False,
        return_source=True,
        return_score=True,
    )
    return results
  
def data_retrieval_based_on_tool(query: str):  
    from databricks_langchain import VectorSearchRetrieverTool
    # Create the retriever tool for the LLM Agent
    retriever_tool = VectorSearchRetrieverTool(
        index_name="hive_metastore.krajasekaran.policy_index",
        num_results=3, # Retrieve top 3 most relevant policy chunks
        tool_name="policy_lookup",
        tool_description="Useful for finding airline passenger rights and compensation rules."
    )

    # Test a retrieval
    results = retriever_tool.invoke(query)
    print(results)
    return results
