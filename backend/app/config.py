# backend/app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")
MEDIAWIKI_API_ENDPOINT="https://en.wikipedia.org/w/api.php"

# Model settings
EMBEDDING_DIMENSION = 768  # Dimension for Gemini embeddings