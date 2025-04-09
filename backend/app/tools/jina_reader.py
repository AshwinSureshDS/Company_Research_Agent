# backend/app/tools/jina_reader.py
import requests
from ..config import JINA_READER_API_KEY

def extract_article_content(url):
    """
    Extract content from a URL using Jina Reader API.
    """
    api_url = "https://api.jina.ai/v1/reader"
    headers = {
        "Authorization": f"Bearer {JINA_READER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": url
    }
    
    response = requests.post(api_url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to extract content: {response.status_code}"}