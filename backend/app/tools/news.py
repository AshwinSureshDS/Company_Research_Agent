# backend/app/tools/news.py
import requests
import time
from ..config import NEWS_API_KEY

def get_company_news(company_name, page_size=5, max_retries=3):
    """
    Fetch latest news about a company using News API with improved error handling.
    """
    url = f"https://newsapi.org/v2/everything"
    params = {
        "q": company_name,
        "pageSize": page_size,
        "sortBy": "publishedAt",
        "language": "en",
        "apiKey": NEWS_API_KEY
    }
    
    # Implement retry mechanism
    for attempt in range(max_retries):
        try:
            response = requests.get(url, params=params, timeout=10)
            
            if response.status_code == 200:
                return response.json()
            elif response.status_code == 429:  # Rate limit exceeded
                # Exponential backoff
                wait_time = (2 ** attempt) + 1
                time.sleep(wait_time)
                continue
            else:
                return {"error": f"Failed to fetch news: {response.status_code}", "details": response.text}
        
        except requests.exceptions.Timeout:
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            return {"error": "Request timed out"}
        
        except requests.exceptions.RequestException as e:
            return {"error": f"Request failed: {str(e)}"}
    
    return {"error": "Maximum retries exceeded"}