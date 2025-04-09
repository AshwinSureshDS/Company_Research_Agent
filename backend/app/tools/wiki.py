# backend/app/tools/wiki.py
import requests
from ..config import MEDIAWIKI_API_ENDPOINT

def get_company_wiki(company_name):
    """
    Fetch company information from Wikipedia using MediaWiki API.
    """
    params = {
        "action": "query",
        "format": "json",
        "titles": company_name,
        "prop": "extracts",
        "exintro": True,
        "explaintext": True,
        "redirects": 1
    }
    
    response = requests.get(MEDIAWIKI_API_ENDPOINT, params=params)
    if response.status_code == 200:
        data = response.json()
        pages = data.get("query", {}).get("pages", {})
        
        # Extract the first page content
        for page_id in pages:
            return {
                "title": pages[page_id].get("title", ""),
                "extract": pages[page_id].get("extract", "No information found")
            }
    
    return {"error": "Failed to fetch Wikipedia information"}