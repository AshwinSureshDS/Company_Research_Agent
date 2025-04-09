# backend/app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY", "your_gemini_api_key")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY", "your_pinecone_api_key")
PINECONE_ENV = os.getenv("PINECONE_ENV", "your_pinecone_environment")