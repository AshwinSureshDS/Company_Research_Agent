# backend/app/tools/jina_reader.py
import requests
from ..config import JINA_READER_API_KEY

def extract_article_content(url):
    """Extract content from a news article URL using Jina Reader."""
    try:
        if not url.startswith(('http://', 'https://')):
            return {"error": "Invalid URL format"}
            
        # Add proper headers with API key
        headers = {
            "x-api-key": JINA_READER_API_KEY,
            "User-Agent": "CompanyResearchBot/1.0"
        }
        
        response = requests.post(
            "https://r.jina.ai/",
            headers=headers,
            json={"url": url},
            timeout=10
        )
        
        if response.status_code == 200:
            return {"data": response.text}  # Return structured data
        return {"error": f"Failed to extract content: {response.status_code}"}
        
    except Exception as e:
        return {"error": f"Extraction error: {str(e)}"}