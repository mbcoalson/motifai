# to call use the following command 
# from utils.embedding_utils import embed_query
# query_vector = embed_query("Tell me about John")

import os
from langchain.embeddings import OpenAIEmbeddings

# Load API Key
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize Embedding Model
embedding_model = OpenAIEmbeddings(openai_api_key=OPENAI_API_KEY)

def embed_query(query: str) -> list:
    """Embeds a query and returns a vector."""
    return embedding_model.embed_query(query)
