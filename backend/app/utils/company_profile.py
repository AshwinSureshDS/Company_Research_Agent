# backend/app/utils/company_profile.py
import google.generativeai as genai
from ..config import GEMINI_API_KEY
from ..tools import search_company, get_company_wiki

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

async def get_company_profile(company_name: str) -> dict:
    """
    Get comprehensive company profile information using multiple sources.
    """
    # Get information from Wikipedia
    wiki_info = get_company_wiki(company_name)
    
    # Get information from search
    search_info = search_company(company_name)
    
    # Combine the information
    profile = {
        "company_name": company_name,
        "wiki_summary": wiki_info.get("extract", "No Wikipedia information available"),
        "search_results": search_info.get("organic", [])[:3] if "organic" in search_info else [],
    }
    
    return profile