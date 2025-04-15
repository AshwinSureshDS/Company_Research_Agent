# backend/app/memory/__init__.py
from pinecone import Pinecone
import logging
from backend.app.config import PINECONE_API_KEY, PINECONE_ENV, PINECONE_INDEX, EMBEDDING_DIMENSION

logger = logging.getLogger(__name__)

def initialize_pinecone():
    """Initialize Pinecone and return the index."""
    try:
        # Create a Pinecone client instance
        pc = Pinecone(api_key=PINECONE_API_KEY)
        
        # Use the index name from config
        index_name = PINECONE_INDEX
        
        # Check if index exists, if not create it
        existing_indexes = pc.list_indexes().names()
        if index_name not in existing_indexes:
            # Create the index
            pc.create_index(
                name=index_name,
                dimension=EMBEDDING_DIMENSION,
                metric='cosine'
            )
            logger.info(f"Created new Pinecone index: {index_name}")
        
        # Get the index
        return pc.Index(index_name)
    except Exception as e:
        logger.error(f"Error initializing Pinecone: {str(e)}")
        raise

def store_memory(index, key: str, vector: list, metadata: dict = None):
    """Store a vector in Pinecone with optional metadata."""
    try:
        if metadata is None:
            metadata = {}
        
        index.upsert(
            vectors=[(key, vector, metadata)]
        )
        return True
    except Exception as e:
        logger.error(f"Error storing memory: {str(e)}")
        return False

def retrieve_memory(index, key: str):
    """Retrieve a specific vector by key."""
    try:
        result = index.fetch(ids=[key])
        return result
    except Exception as e:
        logger.error(f"Error retrieving memory: {str(e)}")
        return None

def query_similar(index, query_vector: list, top_k: int = 5, filter: dict = None):
    """Query Pinecone for similar vectors with optional filtering."""
    try:
        results = index.query(
            vector=query_vector,
            top_k=top_k,
            include_metadata=True,
            filter=filter
        )
        return results
    except Exception as e:
        logger.error(f"Error querying similar vectors: {str(e)}")
        return None

def delete_company_data(index, company_name: str):
    """Delete all data for a specific company."""
    try:
        # Delete by metadata filter
        index.delete(
            filter={"company_name": company_name}
        )
        return True
    except Exception as e:
        logger.error(f"Error deleting company data: {str(e)}")
        return False