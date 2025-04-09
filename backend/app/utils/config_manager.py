# backend/app/utils/config_manager.py
import google.generativeai as genai
from ..config import GEMINI_API_KEY

def initialize_gemini():
    """Initialize Gemini API with the API key."""
    genai.configure(api_key=GEMINI_API_KEY)
    print("Gemini API initialized successfully")
    return genai

# Initialize Gemini on import
gemini = initialize_gemini()