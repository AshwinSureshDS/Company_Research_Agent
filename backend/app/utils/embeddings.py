# backend/app/utils/embeddings.py
import google.generativeai as genai
from ..config import GEMINI_API_KEY

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Update the embedding model initialization if it exists
embedding_model = genai.GenerativeModel('gemini-2.0-flash')

def get_text_embedding(text):
    # Update to use the proper model.embed_content() method if it exists
    """Generate text embeddings using Gemini."""
    embedding_model = "models/embedding-001"
    result = genai.embed_content(
        model=embedding_model,
        content=text,
        task_type="retrieval_document",
    )
    return result["embedding"]

def get_query_embedding(text):
    """Generate query embeddings using Gemini."""
    embedding_model = "models/embedding-001"
    result = genai.embed_content(
        model=embedding_model,
        content=text,
        task_type="retrieval_query",
    )
    return result["embedding"]