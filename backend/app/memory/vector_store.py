# backend/app/memory/vector_store.py
from pinecone import Pinecone, ServerlessSpec
import google.generativeai as genai
from datetime import datetime
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

# Make sure these functions are defined and exported
# Initialize Pinecone once
_pinecone_index = None

def get_index():
    """Get or initialize the Pinecone index."""
    global _pinecone_index
    if _pinecone_index is None:
        _pinecone_index = init_pinecone()
    return _pinecone_index

def store_conversation(user_id, query, response):
    """Store conversation in vector database for future retrieval."""
    index = get_index()
    
    # Create a combined text for better context
    conversation_text = f"User: {query}\nAssistant: {response}"
    
    # Create a unique ID for this conversation
    import uuid
    conversation_id = f"conv_{user_id}_{uuid.uuid4()}"
    
    # Store with metadata
    metadata = {
        "user_id": user_id,
        "type": "conversation",
        "query": query,
        "response": response,
        "timestamp": str(datetime.now().isoformat())
    }
    
    return store_in_pinecone(index, conversation_id, conversation_text, metadata)

def get_conversation_history(user_id, query, top_k=5):
    """Retrieve relevant conversation history based on the query."""
    index = get_index()
    
    # Filter for this user's conversations
    filter_params = {
        "user_id": user_id,
        "type": "conversation"
    }
    
    # Query for relevant conversations
    results = query_pinecone(index, query, top_k=top_k, filter=filter_params)
    return results

def store_user_preferences(user_id, preference_value):
    """Store user preferences in vector database."""
    index = get_index()
    
    # Create a unique ID for this preference
    import uuid
    preference_id = f"pref_{user_id}_{uuid.uuid4()}"
    
    # Store with metadata
    metadata = {
        "user_id": user_id,
        "type": "preference",
        "preference_value": preference_value,
        "timestamp": str(datetime.now().isoformat())
    }
    
    return store_in_pinecone(index, preference_id, preference_value, metadata)

def get_user_preferences(user_id, top_k=3):
    """Retrieve user preferences."""
    index = get_index()
    
    # Filter for this user's preferences
    filter_params = {
        "user_id": user_id,
        "type": "preference"
    }
    
    # Use a generic query to get most recent preferences
    # In a real system, you might want to sort by timestamp
    results = query_pinecone(index, "user preferences", top_k=top_k, filter=filter_params)
    return results

def store_company_research(user_id, company_name, metadata=None):
    """Store information about companies the user has researched."""
    index = get_index()
    
    if metadata is None:
        metadata = {}
    
    # Create a unique ID for this research
    import uuid
    research_id = f"comp_{user_id}_{uuid.uuid4()}"
    
    # Combine with required metadata
    full_metadata = {
        "user_id": user_id,
        "type": "company_research",
        "company_name": company_name,
        "timestamp": str(datetime.now().isoformat()),
        **metadata
    }
    
    return store_in_pinecone(index, research_id, f"Research on {company_name}", full_metadata)

def get_researched_companies(user_id, top_k=5):
    """Retrieve companies the user has researched."""
    index = get_index()
    
    # Filter for this user's company research
    filter_params = {
        "user_id": user_id,
        "type": "company_research"
    }
    
    # Use a generic query to get most recent research
    results = query_pinecone(index, "company research", top_k=top_k, filter=filter_params)
    return results