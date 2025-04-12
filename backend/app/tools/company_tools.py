# backend/app/tools/company_tools.py
import requests
import json
import google.generativeai as genai
import time
import random
from functools import wraps  # Add this import for the wraps decorator
from ..config import SERPER_API_KEY, ALPHA_VANTAGE_API_KEY, GEMINI_API_KEY, MEDIAWIKI_API_ENDPOINT

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
            
            summary = generate_gemini_content(prompt)
            return {
                "company": company_name,
                "summary": summary,
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
        from ..config import ALPHA_VANTAGE_API_KEY
        
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

def compare_stocks(symbols):
    """Compare stock prices and performance of multiple companies."""
    try:
        if isinstance(symbols, str):
            # If input is a comma-separated string, split it
            symbols = [s.strip() for s in symbols.split(',')]
        
        results = {}
        for symbol in symbols:
            stock_data = get_stock_price(symbol)
            results[symbol] = stock_data
        
        # Create a comparison summary
        comparison = {
            "symbols": symbols,
            "prices": {},
            "changes": {},
            "summary": ""
        }
        
        valid_results = {}
        for symbol, data in results.items():
            if "error" not in data:
                valid_results[symbol] = data
                comparison["prices"][symbol] = data.get("price")
                comparison["changes"][symbol] = data.get("change_percent")
        
        if len(valid_results) > 1:
            # Generate a comparison summary using Gemini
            prompt = f"""
            Compare the following stock information:
            
            {json.dumps(valid_results, indent=2)}
            
            Provide a brief comparison of the stock prices, recent performance, and any notable differences.
            """
            
            summary = generate_gemini_content(prompt)
            comparison["summary"] = summary
        elif len(valid_results) == 1:
            symbol = list(valid_results.keys())[0]
            comparison["summary"] = f"Retrieved stock information for {symbol}. Price: ${valid_results[symbol].get('price')}, Change: {valid_results[symbol].get('change_percent')}"
        else:
            comparison["summary"] = "Could not retrieve valid stock information for any of the provided symbols."
        
        return comparison
    except Exception as e:
        return {
            "error": f"Error comparing stocks: {str(e)}",
            "symbols": symbols
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
                    
                    summary = generate_gemini_content(prompt)
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
                
                summary = generate_gemini_content(prompt)
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


def extract_article_content(url):
    """Extract content from an article URL using JINA Reader API."""
    try:
        from ..config import JINA_READER_API_KEY
        
        headers = {
            "x-api-key": JINA_READER_API_KEY,
            "Content-Type": "application/json"
        }
        
        payload = {
            "url": url,
            "include_metadata": True,
            "include_html": False,
            "include_screenshot": False
        }
        
        response = requests.post(
            "https://api.jina.ai/v1/reader",
            json=payload,
            headers=headers
        )
        
        if response.status_code != 200:
            return {
                "error": f"Error extracting content: {response.text}",
                "url": url
            }
        
        data = response.json()
        
        # Extract the main content
        content = data.get("content", "No content extracted")
        title = data.get("metadata", {}).get("title", "No title")
        
        # Summarize the content if it's too long
        if len(content) > 1000:
            import google.generativeai as genai
            from ..config import GEMINI_API_KEY
            
            genai.configure(api_key=GEMINI_API_KEY)
            
            prompt = f"""
            Summarize the following article content in 3-5 paragraphs:
            
            Title: {title}
            
            {content[:5000]}  # Limit to first 5000 chars for the summary
            """
            
            summary = generate_gemini_content(prompt)
            summary = summary.text.strip()
            
            return {
                "title": title,
                "url": url,
                "content": content[:1000] + "...",  # Truncated content
                "summary": summary,
                "full_content_length": len(content)
            }
        
        return {
            "title": title,
            "url": url,
            "content": content,
            "summary": content if len(content) < 500 else content[:500] + "..."
        }
        
    except Exception as e:
        return {
            "error": f"Error extracting content: {str(e)}",
            "url": url
        }

def analyze_company_article(company_name, url=None):
    """Analyze a specific article about a company or find and analyze a relevant article."""
    try:
        # If no URL is provided, find a relevant article
        if not url:
            # Get news about the company
            news = get_combined_news(company_name)
            
            # Select the most relevant article
            if news.get("articles") and len(news.get("articles")) > 0:
                # Use the first article
                article = news["articles"][0]
                url = article.get("link")
                
                if not url:
                    return {
                        "error": "No article URL found",
                        "company": company_name
                    }
            else:
                return {
                    "error": "No articles found for the company",
                    "company": company_name
                }
        
        # Extract content from the article
        article_data = extract_article_content(url)
        
        if "error" in article_data:
            return article_data
        
        # Analyze the content in relation to the company
        import google.generativeai as genai
        from ..config import GEMINI_API_KEY
        
        genai.configure(api_key=GEMINI_API_KEY)
        
        content = article_data.get("content", "")
        title = article_data.get("title", "")
        
        prompt = f"""
        Analyze the following article about {company_name}:
        
        Title: {title}
        
        Content: {content[:3000]}  # Limit to first 3000 chars for analysis
        
        Please provide:
        1. Key points about {company_name} from this article
        2. Any significant developments or news mentioned
        3. Potential impact on the company's business or stock
        4. Overall sentiment (positive, negative, or neutral)
        """
        
        analysis = generate_gemini_content(prompt)
        
        return {
            "company": company_name,
            "article_title": title,
            "article_url": url,
            "analysis": analysis,
            "content_preview": content[:300] + "..." if len(content) > 300 else content
        }
        
    except Exception as e:
        return {
            "error": f"Error analyzing article: {str(e)}",
            "company": company_name,
            "url": url
        }


# Add a function to batch process multiple articles
def batch_process_articles(company_name, articles, batch_size=3):
    """Process multiple articles in batches to avoid rate limits."""
    processed_articles = []
    
    # Process articles in batches
    for i in range(0, len(articles), batch_size):
        batch = articles[i:i+batch_size]
        
        for article in batch:
            try:
                url = article.get("link") or article.get("url")
                if not url:
                    continue
                
                # Extract a simple summary without making additional API calls
                summary = article.get("summary") or article.get("snippet") or "No summary available."
                
                processed_articles.append({
                    "title": article.get("title", ""),
                    "url": url,
                    "summary": summary,
                    "source": article.get("source", ""),
                    "date": article.get("published_date", "")
                })
            except Exception as e:
                print(f"Error processing article: {str(e)}")
        
        # Add a small delay between batches to avoid rate limits
        if i + batch_size < len(articles):
            time.sleep(1)
    
    return processed_articles


def get_wikipedia_info(company_name):
    """Get information about a company from Wikipedia."""
    try:
        # First, search for the company page
        search_params = {
            "action": "query",
            "format": "json",
            "list": "search",
            "srsearch": f"{company_name} company",
            "srlimit": 3
        }
        
        search_response = requests.get(MEDIAWIKI_API_ENDPOINT, params=search_params)
        search_data = search_response.json()
        
        if "query" not in search_data or "search" not in search_data["query"] or not search_data["query"]["search"]:
            return {
                "company": company_name,
                "summary": f"No Wikipedia information found for {company_name}",
                "url": None
            }
        
        # Get the page ID of the first result
        page_id = search_data["query"]["search"][0]["pageid"]
        
        # Get the page content
        content_params = {
            "action": "query",
            "format": "json",
            "prop": "extracts|info",
            "pageids": page_id,
            "exintro": 1,  # Get only the introduction section
            "explaintext": 1,  # Get plain text content
            "inprop": "url"  # Get the URL of the page
        }
        
        content_response = requests.get(MEDIAWIKI_API_ENDPOINT, params=content_params)
        content_data = content_response.json()
        
        if "query" not in content_data or "pages" not in content_data["query"] or str(page_id) not in content_data["query"]["pages"]:
            return {
                "company": company_name,
                "summary": f"Failed to retrieve Wikipedia content for {company_name}",
                "url": None
            }
        
        # Extract the content and URL
        page_data = content_data["query"]["pages"][str(page_id)]
        extract = page_data.get("extract", "No content available")
        url = page_data.get("fullurl", "")
        title = page_data.get("title", company_name)
        
        # Use Gemini to summarize and structure the information if it's too long
        if len(extract) > 500:
            prompt = f"""
            Summarize the following Wikipedia information about {company_name} in a structured way:
            
            {extract[:3000]}
            
            Please include:
            1. Brief company description
            2. Industry and main products/services
            3. Key facts (founding date, headquarters, etc.)
            4. Any notable information
            """
            
            summary = generate_gemini_content(prompt)
        else:
            summary = extract
        
        return {
            "company": company_name,
            "title": title,
            "summary": summary,
            "url": url,
            "source": "Wikipedia"
        }
    except Exception as e:
        return {
            "error": f"Error getting Wikipedia information: {str(e)}",
            "company": company_name
        }

def get_comprehensive_company_info(company_name):
    """Get comprehensive information about a company from multiple sources."""
    # Get general search information
    search_info = search_company(company_name)
    
    # Get Wikipedia information
    wiki_info = get_wikipedia_info(company_name)
    
    # Try to get the company symbol
    symbol = get_company_symbol(company_name)
    
    # Get financial information if symbol is available
    financials = {}
    if symbol:
        financials = get_company_financials(symbol)
    
    # Combine all information
    comprehensive_info = {
        "company": company_name,
        "general_info": search_info.get("summary", "No general information available"),
        "wikipedia": wiki_info.get("summary", "No Wikipedia information available"),
        "financials": financials if "error" not in financials else {},
        "sources": {
            "search": search_info.get("sources", []),
            "wikipedia": wiki_info.get("url")
        }
    }
    
    return comprehensive_info


def rate_limit_decorator(max_retries=3, base_delay=2):
    """
    Decorator to implement rate limiting with exponential backoff.
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            retries = 0
            while retries <= max_retries:
                try:
                    return func(*args, **kwargs)
                except Exception as e:
                    error_message = str(e).lower()
                    if "429" in error_message or "quota" in error_message or "resource exhausted" in error_message:
                        retries += 1
                        if retries > max_retries:
                            print(f"Maximum retries ({max_retries}) exceeded. Giving up.")
                            raise
                        
                        # Calculate delay with exponential backoff and jitter
                        delay = base_delay * (2 ** (retries - 1)) + random.uniform(0, 1)
                        print(f"Rate limit hit. Retrying in {delay:.2f} seconds... (Attempt {retries}/{max_retries})")
                        time.sleep(delay)
                    else:
                        # If it's not a rate limit error, raise immediately
                        raise
            return None  # This should never be reached
        return wrapper
    return decorator

# Apply the rate limiting decorator to functions that use the Gemini API
@rate_limit_decorator()
def generate_gemini_content(prompt, model="gemini-2.0-flash"):
    """Wrapper function for Gemini content generation with rate limiting."""
    response = genai.GenerativeModel(model).generate_content(prompt)
    return response.text.strip()

# Update the search_company function to use the rate-limited wrapper
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
            
            summary = generate_gemini_content(prompt)
            return {
                "company": company_name,
                "summary": summary,
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

# Update the get_company_news function
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
                    
                    summary = generate_gemini_content(prompt)
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