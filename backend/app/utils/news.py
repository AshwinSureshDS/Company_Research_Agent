# backend/app/utils/news.py
import requests
from ..config import NEWS_API_KEY

def get_latest_news(company_name: str) -> dict:
    """Fetch latest news about a company using News API."""
    url = f"https://newsapi.org/v2/everything?q={company_name}&apiKey={NEWS_API_KEY}"
    response = requests.get(url)
    if response.status_code == 200:
        return response.json()
    else:
        return {"error": "Unable to fetch news"}