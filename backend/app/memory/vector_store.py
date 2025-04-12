# backend/app/memory/vector_store.py
import google.generativeai as genai
from ..config import PINECONE_API_KEY, PINECONE_ENV, PINECONE_INDEX, GEMINI_API_KEY, EMBEDDING_DIMENSION
import uuid

# Initialize Gemini for embeddings
genai.configure(api_key=GEMINI_API_KEY)

def init_pinecone():
    """Initialize Pinecone and return the index."""
    try:
        from pinecone import Pinecone
        
        # Initialize Pinecone client
        pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Check if index exists, create if it doesn't
        existing_indexes = pc.list_indexes().names()
        
        if PINECONE_INDEX not in existing_indexes:
            # Create index if it doesn't exist
            pc.create_index(
                name=PINECONE_INDEX,
                dimension=EMBEDDING_DIMENSION,
                metric="cosine"
            )
            print(f"Created new Pinecone index: {PINECONE_INDEX}")
        
        # Get the index
        index = pc.Index(PINECONE_INDEX)
        print(f"Connected to Pinecone index: {PINECONE_INDEX}")
        return index
            
    except Exception as e:
        print(f"Error initializing Pinecone: {str(e)}")
        print("Using mock vector store for testing...")
        return MockPineconeIndex()

class MockPineconeIndex:
    """Mock Pinecone index for testing without a connection."""
    
    def __init__(self):
        self.vectors = {}
    
    def upsert(self, vectors, namespace=""):
        """Mock upsert method."""
        if namespace not in self.vectors:
            self.vectors[namespace] = {}
        
        for vector in vectors:
            self.vectors[namespace][vector['id']] = {
                'id': vector['id'],
                'values': vector['values'],
                'metadata': vector.get('metadata', {})
            }
        
        return {"upserted_count": len(vectors)}
    
    def query(self, vector, top_k=10, namespace="", include_metadata=True):
        """Mock query method."""
        return {
            "matches": [],
            "namespace": namespace
        }

def get_embedding(text):
    """Get embedding for text using Gemini."""
    try:
        embedding = genai.embed_content(
            model="models/embedding-001",
            content=text,
            task_type="retrieval_query"
        )
        return embedding["embedding"]
    except Exception as e:
        print(f"Error getting embedding: {str(e)}")
        # Return a mock embedding for testing
        import random
        return [random.random() for _ in range(EMBEDDING_DIMENSION)]

def store_in_pinecone(index, text, metadata, namespace="company-research"):
    """Store text and metadata in Pinecone."""
    try:
        # Generate a unique ID
        vector_id = str(uuid.uuid4())
        
        # Get embedding
        embedding = get_embedding(text)
        
        # Upsert to Pinecone
        index.upsert(
            vectors=[{
                'id': vector_id,
                'values': embedding,
                'metadata': metadata
            }],
            namespace=namespace
        )
        
        return vector_id
    except Exception as e:
        print(f"Error storing in Pinecone: {str(e)}")
        return None

def query_pinecone(index, query_text, top_k=5, namespace="company-research"):
    """Query Pinecone for similar vectors."""
    try:
        # Get embedding for query
        query_embedding = get_embedding(query_text)
        
        # Query Pinecone
        results = index.query(
            vector=query_embedding,
            top_k=top_k,
            namespace=namespace,
            include_metadata=True
        )
        
        return results
    except Exception as e:
        print(f"Error querying Pinecone: {str(e)}")
        return {"matches": []}