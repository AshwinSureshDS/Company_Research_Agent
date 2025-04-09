# backend/app/memory.py
import pinecone
from backend.app.config import PINECONE_API_KEY, PINECONE_ENV

def initialize_pinecone():
    pinecone.init(api_key=PINECONE_API_KEY, environment=PINECONE_ENV)
    # Create an index if not exists
    index_name = "company-research-memory"
    if index_name not in pinecone.list_indexes():
        pinecone.create_index(index_name, dimension=768)  # adjust dimension as needed
    return pinecone.Index(index_name)
