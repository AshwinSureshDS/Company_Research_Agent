# backend/app/embeddings.py
import google.generativeai as genai
import logging
from backend.app.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Initialize Gemini API
genai.configure(api_key=GEMINI_API_KEY)

# Update the model name in the generate_embedding function
async def generate_embedding(text):
    """Generate an embedding for a text using Google's Gemini API."""
    try:
        genai.configure(api_key=GEMINI_API_KEY)
        
        # Use the embedding model
        embedding_model = "models/embedding-001"  # This is likely a dedicated embedding model, so we don't change it
        
        # Generate embedding
        embedding_result = embedding_model.embed_content(
            content=text,
            task_type="retrieval_query"
        )
        
        # Return the embedding values
        return embedding_result.embedding
    except Exception as e:
        logger.error(f"Error generating embedding: {e}")
        return None

async def batch_generate_embeddings(texts):
    """Generate embeddings for multiple texts."""
    embeddings = []
    for text in texts:
        embedding = await generate_embedding(text)
        if embedding:
            embeddings.append(embedding)
    return embeddings

# If there are any other instances of the Gemini model being used for text generation
# in this file, update those as well