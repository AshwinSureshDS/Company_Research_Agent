# backend/app/memory/vector_store.py
from pinecone import Pinecone, ServerlessSpec
import google.generativeai as genai
from ..config import PINECONE_API_KEY, PINECONE_ENVIRONMENT, PINECONE_INDEX, GEMINI_API_KEY

# Initialize Gemini for embeddings
genai.configure(api_key=GEMINI_API_KEY)

# Dimension for Gemini embeddings
EMBEDDING_DIMENSION = 768

def init_pinecone():
    """Initialize Pinecone and create index if it doesn't exist."""
    # Create Pinecone client
    pc = Pinecone(api_key=PINECONE_API_KEY)
    
    # Check if index exists, if not create it
    if PINECONE_INDEX not in pc.list_indexes().names():
        pc.create_index(
            name=PINECONE_INDEX,
            dimension=EMBEDDING_DIMENSION,
            metric="cosine",
            spec=ServerlessSpec(
                cloud="aws",
                region="us-east-1"
            )
        )
        print(f"Created new Pinecone index: {PINECONE_INDEX}")
    
    # Get the index
    index = pc.Index(PINECONE_INDEX)
    return index

def get_embeddings(text):
    """Generate embeddings using Gemini."""
    embedding_model = "models/embedding-001"
    embedding = genai.embed_content(
        model=embedding_model,
        content=text,
        task_type="retrieval_document",
    )
    return embedding["embedding"]

def store_in_pinecone(index, id, text, metadata=None):
    """Store text embeddings in Pinecone with metadata."""
    if metadata is None:
        metadata = {}
    
    # Generate embeddings
    embedding = get_embeddings(text)
    
    # Store in Pinecone
    index.upsert(
        vectors=[(id, embedding, {**metadata, "text": text})],
    )
    return id

def query_pinecone(index, query_text, top_k=5, filter=None):
    """Query Pinecone for similar vectors."""
    # Generate query embeddings
    query_embedding = get_embeddings(query_text)
    
    # Query Pinecone
    results = index.query(
        vector=query_embedding,
        top_k=top_k,
        include_metadata=True,
        filter=filter
    )
    
    return results