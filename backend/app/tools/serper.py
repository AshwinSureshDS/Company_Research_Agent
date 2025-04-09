# backend/app/tools/serper.py
import requests
from ..config import SERPER_API_KEY

def search_company(company_name, num_results=5):
    """
    Search for company information using Serper API.
    """
    url = "https://google.serper.dev/search"
    payload = {
        "q": f"{company_name} company information",
        "num": num_results
    }
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    
    response = requests.post(url, json=payload, headers=headers)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": f"Failed to fetch data: {response.status_code}"}