# backend/app/tools/company_tools.py
# Let's enhance the company_tools.py file to use all available APIs

import requests
import logging
import json
from backend.app.config import (
    ALPHA_VANTAGE_API_KEY,
    NEWS_API_KEY,
    SERPER_API_KEY,
    JINA_READER_API_KEY,
    MEDIAWIKI_API_ENDPOINT
)

logger = logging.getLogger(__name__)

def get_stock_price(symbol):
    """Get the latest stock price for a company symbol."""
    try:
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if "Global Quote" in data and data["Global Quote"]:
            quote = data["Global Quote"]
            return {
                "symbol": quote.get("01. symbol", symbol),
                "price": quote.get("05. price", "N/A"),
                "change": quote.get("09. change", "N/A"),
                "change_percent": quote.get("10. change percent", "N/A"),
                "volume": quote.get("06. volume", "N/A"),
                "latest_trading_day": quote.get("07. latest trading day", "N/A")
            }
        else:
            logger.error(f"Error getting stock price for {symbol}: {data}")
            return {"error": f"Could not retrieve stock price for {symbol}"}
    except Exception as e:
        logger.error(f"Error in get_stock_price: {str(e)}")
        return {"error": f"Error retrieving stock price: {str(e)}"}

def get_company_overview(symbol):
    """Get company overview information from Alpha Vantage."""
    try:
        url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if "Symbol" in data:
            return data
        else:
            logger.error(f"Error getting company overview for {symbol}: {data}")
            return {"error": f"Could not retrieve company overview for {symbol}"}
    except Exception as e:
        logger.error(f"Error in get_company_overview: {str(e)}")
        return {"error": f"Error retrieving company overview: {str(e)}"}

def get_company_financials(symbol):
    """Get company financial data from Alpha Vantage."""
    try:
        url = f"https://www.alphavantage.co/query?function=INCOME_STATEMENT&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if "annualReports" in data:
            return {
                "income_statement": data["annualReports"][0] if data["annualReports"] else {}
            }
        else:
            logger.error(f"Error getting financials for {symbol}: {data}")
            return {"error": f"Could not retrieve financial data for {symbol}"}
    except Exception as e:
        logger.error(f"Error in get_company_financials: {str(e)}")
        return {"error": f"Error retrieving financial data: {str(e)}"}

def compare_stocks(symbols):
    """Compare stock prices for multiple companies."""
    results = {}
    for symbol in symbols:
        results[symbol] = get_stock_price(symbol)
    return results

def get_company_news(company_name):
    """Get recent news about a company using News API."""
    try:
        url = f"https://newsapi.org/v2/everything?q={company_name}&sortBy=publishedAt&apiKey={NEWS_API_KEY}&pageSize=5"
        response = requests.get(url)
        data = response.json()
        
        if data.get("status") == "ok" and data.get("articles"):
            return data.get("articles")
        else:
            logger.error(f"Error getting news for {company_name}: {data}")
            return {"error": f"Could not retrieve news for {company_name}"}
    except Exception as e:
        logger.error(f"Error in get_company_news: {str(e)}")
        return {"error": f"Error retrieving company news: {str(e)}"}

def search_company_info(company_name):
    """Search for company information using Serper API."""
    try:
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        payload = {
            "q": f"{company_name} company information",
            "num": 5
        }
        response = requests.post('https://google.serper.dev/search', headers=headers, json=payload)
        data = response.json()
        
        if "organic" in data:
            return data["organic"]
        else:
            logger.error(f"Error searching for {company_name}: {data}")
            return {"error": f"Could not find information for {company_name}"}
    except Exception as e:
        logger.error(f"Error in search_company_info: {str(e)}")
        return {"error": f"Error searching company information: {str(e)}"}

def get_wikipedia_info(company_name):
    """Get company information from Wikipedia."""
    try:
        # First search for the page
        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": f"{company_name} company",
            "srlimit": 1
        }
        search_response = requests.get(MEDIAWIKI_API_ENDPOINT, params=search_params)
        search_data = search_response.json()
        
        if "query" in search_data and "search" in search_data["query"] and search_data["query"]["search"]:
            page_title = search_data["query"]["search"][0]["title"]
            
            # Then get the page content
            content_params = {
                "action": "query",
                "format": "json",
                "prop": "extracts",
                "exintro": True,
                "explaintext": True,
                "titles": page_title
            }
            content_response = requests.get(MEDIAWIKI_API_ENDPOINT, params=content_params)
            content_data = content_response.json()
            
            pages = content_data["query"]["pages"]
            page_id = next(iter(pages))
            
            if "extract" in pages[page_id]:
                return {
                    "title": page_title,
                    "extract": pages[page_id]["extract"]
                }
        
        return {"error": f"No Wikipedia information found for {company_name}"}
    except Exception as e:
        logger.error(f"Error getting Wikipedia info: {str(e)}")
        return {"error": f"Error retrieving Wikipedia information: {str(e)}"}

def extract_info_from_url(url):
    """Extract information from a URL using Jina Reader API."""
    try:
        headers = {
            "x-api-key": JINA_READER_API_KEY
        }
        payload = {
            "url": url,
            "include_metadata": True
        }
        response = requests.post("https://api.jina.ai/v1/reader", headers=headers, json=payload)
        data = response.json()
        
        if "text" in data:
            return {
                "title": data.get("metadata", {}).get("title", ""),
                "text": data["text"]
            }
        else:
            logger.error(f"Error extracting info from URL {url}: {data}")
            return {"error": f"Could not extract information from {url}"}
    except Exception as e:
        logger.error(f"Error in extract_info_from_url: {str(e)}")
        return {"error": f"Error extracting information from URL: {str(e)}"}

async def search_company_symbol(company_name):
    """Search for a company's stock symbol."""
    try:
        # First try Alpha Vantage symbol search
        url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={company_name}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if "bestMatches" in data and data["bestMatches"]:
            # Return the symbol of the best match
            return data["bestMatches"][0]["1. symbol"]
        else:
            logger.warning(f"No symbol found for {company_name} via Alpha Vantage")
            return None
    except Exception as e:
        logger.error(f"Error searching company symbol: {str(e)}")
        return None