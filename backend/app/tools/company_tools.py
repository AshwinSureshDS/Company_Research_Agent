# backend/app/tools/company_tools.py
import requests
import json
import google.generativeai as genai
from ..config import SERPER_API_KEY, ALPHA_VANTAGE_API_KEY, GEMINI_API_KEY

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

def search_company(company_name):
    """Search for general information about a company."""
    try:
        url = "https://google.serper.dev/search"
        payload = {
            "q": f"{company_name} company information",
            "num": 5
        }
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        # Extract relevant information
        results = []
        if "organic" in data:
            for result in data["organic"][:3]:  # Use top 3 results
                results.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("snippet", ""),
                    "link": result.get("link", "")
                })
        
        # Use Gemini to summarize the information
        if results:
            prompt = f"""
            Summarize the following information about {company_name}:
            
            {json.dumps(results, indent=2)}
            
            Provide a concise summary of what the company does, its industry, and any notable information.
            """
            
            response = genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt)
            return {
                "company": company_name,
                "summary": response.text,
                "sources": [r["link"] for r in results]
            }
        else:
            return {
                "company": company_name,
                "summary": f"No information found for {company_name}",
                "sources": []
            }
    except Exception as e:
        return {
            "error": f"Error searching for company: {str(e)}",
            "company": company_name
        }

def get_company_financials(symbol):
    """Get financial data for a company."""
    try:
        # Use Alpha Vantage to get company overview
        url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if "Symbol" not in data:
            return {
                "error": f"No financial data found for symbol {symbol}",
                "symbol": symbol
            }
        
        # Extract key financial metrics
        financials = {
            "symbol": data.get("Symbol"),
            "company_name": data.get("Name"),
            "market_cap": data.get("MarketCapitalization"),
            "pe_ratio": data.get("PERatio"),
            "dividend_yield": data.get("DividendYield"),
            "revenue": data.get("RevenueTTM"),
            "gross_profit": data.get("GrossProfitTTM"),
            "sector": data.get("Sector"),
            "industry": data.get("Industry"),
            "description": data.get("Description")
        }
        
        return financials
    except Exception as e:
        return {
            "error": f"Error getting financials: {str(e)}",
            "symbol": symbol
        }

def get_stock_price(symbol):
    """Get the latest stock price for a company."""
    try:
        # Use Alpha Vantage to get stock price
        url = f"https://www.alphavantage.co/query?function=GLOBAL_QUOTE&symbol={symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if "Global Quote" not in data or not data["Global Quote"]:
            return {
                "error": f"No stock price found for symbol {symbol}",
                "symbol": symbol
            }
        
        quote = data["Global Quote"]
        
        price_data = {
            "symbol": symbol,
            "price": quote.get("05. price"),
            "change": quote.get("09. change"),
            "change_percent": quote.get("10. change percent"),
            "volume": quote.get("06. volume"),
            "latest_trading_day": quote.get("07. latest trading day")
        }
        
        return price_data
    except Exception as e:
        return {
            "error": f"Error getting stock price: {str(e)}",
            "symbol": symbol
        }

def get_company_symbol(company_name):
    """Look up a company's stock symbol based on its name."""
    try:
        # Use Alpha Vantage Symbol Search endpoint
        url = f"https://www.alphavantage.co/query?function=SYMBOL_SEARCH&keywords={company_name}&apikey={ALPHA_VANTAGE_API_KEY}"
        response = requests.get(url)
        data = response.json()
        
        if "bestMatches" in data and data["bestMatches"]:
            # Return the best match symbol
            return data["bestMatches"][0]["1. symbol"]
        else:
            # If no match found, try to use the input as a symbol
            return company_name
    except Exception as e:
        print(f"Error looking up symbol: {str(e)}")
        return company_name

def get_company_news(company_name):
    """Get the latest news articles about a company with summaries."""
    try:
        url = "https://google.serper.dev/news"
        payload = {
            "q": company_name,
            "num": 5
        }
        headers = {
            'X-API-KEY': SERPER_API_KEY,
            'Content-Type': 'application/json'
        }
        
        response = requests.post(url, json=payload, headers=headers)
        data = response.json()
        
        news_articles = []
        if "news" in data:
            for article in data["news"]:
                # Summarize each article
                if "snippet" in article:
                    prompt = f"""
                    Summarize the following news snippet about {company_name} in 2-3 sentences:
                    
                    {article.get('title', '')}
                    {article.get('snippet', '')}
                    """
                    
                    summary_response = genai.GenerativeModel('gemini-2.0-flash').generate_content(prompt)
                    summary = summary_response.text.strip()
                else:
                    summary = "No summary available."
                
                news_articles.append({
                    "title": article.get("title", ""),
                    "link": article.get("link", ""),
                    "published_date": article.get("date", ""),
                    "source": article.get("source", ""),
                    "snippet": article.get("snippet", ""),
                    "summary": summary
                })
        
        return {
            "company": company_name,
            "articles": news_articles,
            "count": len(news_articles)
        }
    except Exception as e:
        return {
            "error": f"Error getting news: {str(e)}",
            "company": company_name
        }


def get_news_api_articles(company_name):
    """Get news articles about a company using NEWS API."""
    try:
        from ..config import NEWS_API_KEY
        
        # Format the query for NEWS API
        query = company_name.replace(" ", "+")
        
        # Make request to NEWS API
        url = f"https://newsapi.org/v2/everything?q={query}&sortBy=publishedAt&apiKey={NEWS_API_KEY}&language=en&pageSize=5"
        response = requests.get(url)
        data = response.json()
        
        if data.get("status") != "ok" or "articles" not in data:
            return {
                "company": company_name,
                "articles": [],
                "count": 0,
                "source": "NEWS API",
                "error": data.get("message", "Unknown error")
            }
        
        # Process articles
        news_articles = []
        for article in data["articles"][:5]:  # Limit to 5 articles
            # Summarize each article
            if article.get("description"):
                prompt = f"""
                Summarize the following news snippet about {company_name} in 2-3 sentences:
                
                {article.get('title', '')}
                {article.get('description', '')}
                """
                
                summary_response = genai.GenerativeModel('gemini-2.0-flash').generate_content(prompt)
                summary = summary_response.text.strip()
            else:
                summary = "No summary available."
            
            news_articles.append({
                "title": article.get("title", ""),
                "link": article.get("url", ""),
                "published_date": article.get("publishedAt", ""),
                "source": article.get("source", {}).get("name", ""),
                "snippet": article.get("description", ""),
                "summary": summary
            })
        
        return {
            "company": company_name,
            "articles": news_articles,
            "count": len(news_articles),
            "source": "NEWS API"
        }
    except Exception as e:
        return {
            "error": f"Error getting news from NEWS API: {str(e)}",
            "company": company_name,
            "source": "NEWS API"
        }

def get_combined_news(company_name):
    """Get news from multiple sources and combine the results."""
    # Get news from Serper
    serper_news = get_company_news(company_name)
    
    # Get news from NEWS API
    news_api_articles = get_news_api_articles(company_name)
    
    # Combine results
    combined_articles = []
    
    # Add Serper articles
    if "articles" in serper_news and serper_news["articles"]:
        for article in serper_news["articles"]:
            article["source_api"] = "Serper"
            combined_articles.append(article)
    
    # Add NEWS API articles
    if "articles" in news_api_articles and news_api_articles["articles"]:
        for article in news_api_articles["articles"]:
            article["source_api"] = "NEWS API"
            combined_articles.append(article)
    
    # Sort by published date (newest first)
    try:
        from datetime import datetime
        
        def parse_date(article):
            date_str = article.get("published_date", "")
            try:
                return datetime.strptime(date_str, "%Y-%m-%dT%H:%M:%SZ")
            except:
                try:
                    return datetime.strptime(date_str, "%Y-%m-%d")
                except:
                    return datetime(1900, 1, 1)  # Default old date
        
        combined_articles.sort(key=parse_date, reverse=True)
    except Exception as e:
        print(f"Error sorting articles: {str(e)}")
    
    return {
        "company": company_name,
        "articles": combined_articles[:8],  # Limit to 8 articles total
        "count": len(combined_articles[:8]),
        "sources": ["Serper", "NEWS API"]
    }