# backend/app/config.py
import os
from dotenv import load_dotenv

load_dotenv()

GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
PINECONE_API_KEY = os.getenv("PINECONE_API_KEY")
PINECONE_ENVIRONMENT = os.getenv("PINECONE_ENV")
PINECONE_INDEX = os.getenv("PINECONE_INDEX")
NEWS_API_KEY = os.getenv("NEWS_API_KEY")
SERPER_API_KEY = os.getenv("SERPER_API_KEY")
JINA_READER_API_KEY = os.getenv("JINA_READER_API_KEY")
MEDIAWIKI_API_ENDPOINT = os.getenv("MEDIAWIKI_API_ENDPOINT")