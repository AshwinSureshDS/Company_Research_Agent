# backend/app/utils/embeddings.py
import google.generativeai as genai
from ..config import GEMINI_API_KEY

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

def get_text_embedding(text):
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