# backend/app/config.py
import os
from dotenv import load_dotenv
from pathlib import Path

# Load environment variables from .env file
env_path = Path("d:/College/Company_Research_Chatbot/.env")
load_dotenv(dotenv_path=env_path)

# API Keys and Endpoints
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENV = os.getenv("PINECONE_ENV")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
JINA_READER_API_KEY = os.getenv("JINA_READER_API_KEY")
MEDIAWIKI_API_ENDPOINT = os.getenv("MEDIAWIKI_API_ENDPOINT")
ALPHA_VANTAGE_API_KEY = os.getenv("ALPHA_VANTAGE_API_KEY")

# Make sure this part exists in your config.py
from pathlib import Path

# Application settings
CHAT_DIR = Path("d:/College/Company_Research_Chatbot/backend/data/chats")
CHAT_DIR.mkdir(parents=True, exist_ok=True)

# Model settings
EMBEDDING_DIMENSION = 768  # Dimension for Gemini embeddings