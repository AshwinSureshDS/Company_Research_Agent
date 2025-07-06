# backend/app/data_ingestion.py
import aiohttp
import asyncio
import logging
from datetime import datetime
from langchain.text_splitter import RecursiveCharacterTextSplitter
from backend.app.config import (
    ALPHA_VANTAGE_API_KEY, 
    SERPER_API_KEY, 
    NEWS_API_KEY, 
    MEDIAWIKI_API_ENDPOINT,
    JINA_READER_API_KEY
)
from backend.app.embeddings import generate_embedding
from backend.app.memory import store_memory, initialize_pinecone

logger = logging.getLogger(__name__)

async def fetch_stock_data(company_symbol):
    """Fetch stock data from Alpha Vantage API."""
    url = f"https://www.alphavantage.co/query?function=OVERVIEW&symbol={company_symbol}&apikey={ALPHA_VANTAGE_API_KEY}"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if "Symbol" in data:
                    return data
                else:
                    logger.warning(f"No stock data found for {company_symbol}")
                    return None
            else:
                logger.error(f"Error fetching stock data: {response.status}")
                return None

async def search_company_info(company_name):
    """Search for company information using Serper API."""
    url = "https://google.serper.dev/search"
    headers = {
        "X-API-KEY": SERPER_API_KEY,
        "Content-Type": "application/json"
    }
    payload = {
        "q": f"{company_name} company information",
        "num": 5
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(url, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data
            else:
                logger.error(f"Error searching company info: {response.status}")
                return None

async def fetch_news(company_name):
    """Fetch news about the company using News API."""
    url = f"https://newsapi.org/v2/everything?q={company_name}&apiKey={NEWS_API_KEY}&pageSize=5&language=en&sortBy=publishedAt"
    
    async with aiohttp.ClientSession() as session:
        async with session.get(url) as response:
            if response.status == 200:
                data = await response.json()
                if data.get("status") == "ok" and data.get("totalResults", 0) > 0:
                    return data.get("articles", [])
                else:
                    logger.warning(f"No news found for {company_name}")
                    return []
            else:
                logger.error(f"Error fetching news: {response.status}")
                return []

async def fetch_wikipedia_info(company_name):
    """Fetch company information from Wikipedia."""
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": f"{company_name} company",
        "srlimit": 1
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.get(MEDIAWIKI_API_ENDPOINT, params=params) as response:
            if response.status == 200:
                data = await response.json()
                search_results = data.get("query", {}).get("search", [])
                
                if not search_results:
                    logger.warning(f"No Wikipedia page found for {company_name}")
                    return None
                
                page_id = search_results[0]["pageid"]
                
                # Get the full page content
                content_params = {
                    "action": "query",
                    "format": "json",
                    "prop": "extracts",
                    "pageids": page_id,
                    "explaintext": True
                }
                
                async with session.get(MEDIAWIKI_API_ENDPOINT, params=content_params) as content_response:
                    if content_response.status == 200:
                        content_data = await content_response.json()
                        page_content = content_data.get("query", {}).get("pages", {}).get(str(page_id), {}).get("extract", "")
                        return page_content
                    else:
                        logger.error(f"Error fetching Wikipedia content: {content_response.status}")
                        return None
            else:
                logger.error(f"Error searching Wikipedia: {response.status}")
                return None

# Add this function to extract content from URLs using Jina Reader
async def extract_content_from_url(url):
    """Extract content from URL using Jina Reader API."""
    api_url = "https://api.jina.ai/v1/reader"
    headers = {
        "Authorization": f"Bearer {JINA_READER_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "url": url
    }
    
    async with aiohttp.ClientSession() as session:
        async with session.post(api_url, headers=headers, json=payload) as response:
            if response.status == 200:
                data = await response.json()
                return data.get("text", "")
            else:
                logger.error(f"Error extracting content from URL: {response.status}")
                return ""

# Update the process_company_data function to use all APIs
async def process_company_data(company_name, company_symbol=None):
    """Process company data from multiple sources and store in Pinecone."""
    # Initialize Pinecone
    pinecone_index = initialize_pinecone()
    
    logger.info(f"Processing data for company: {company_name}, symbol: {company_symbol}")
    
    # Collect data from various sources
    tasks = [
        search_company_info(company_name),
        fetch_wikipedia_info(company_name),
        fetch_news(company_name)
    ]
    
    if company_symbol:
        tasks.append(fetch_stock_data(company_symbol))
    
    results = await asyncio.gather(*tasks, return_exceptions=True)
    
    # Process results safely
    serper_data = results[0] if not isinstance(results[0], Exception) else None
    wiki_data = results[1] if not isinstance(results[1], Exception) else None
    news_data = results[2] if not isinstance(results[2], Exception) else None
    stock_data = results[3] if len(results) > 3 and not isinstance(results[3], Exception) else None
    
    # Log what data was retrieved
    logger.info(f"Retrieved data: Serper: {bool(serper_data)}, Wiki: {bool(wiki_data)}, News: {bool(news_data)}, Stock: {bool(stock_data)}")
    
    # Combine and clean data
    combined_text = []
    
    # Process Serper data
    if serper_data:
        organic_results = serper_data.get("organic", [])
        for result in organic_results:
            title = result.get("title", "")
            snippet = result.get("snippet", "")
            combined_text.append(f"Title: {title}\nDescription: {snippet}")
            
            # Try to extract content from the URL using Jina Reader
            link = result.get("link")
            if link:
                try:
                    url_content = await extract_content_from_url(link)
                    if url_content:
                        combined_text.append(f"Content from {title}:\n{url_content}")
                except Exception as e:
                    logger.error(f"Error extracting content from URL {link}: {str(e)}")
    
    # Process Wikipedia data
    if wiki_data:
        combined_text.append(f"Wikipedia Information:\n{wiki_data}")
    
    # Process news data
    if news_data:
        for article in news_data:
            title = article.get("title", "")
            description = article.get("description", "")
            content = article.get("content", "")
            source = article.get("source", {}).get("name", "Unknown")
            published_at = article.get("publishedAt", "")
            
            news_text = f"News Title: {title}\nSource: {source}\nDate: {published_at}\n"
            news_text += f"Description: {description}\nContent: {content}"
            combined_text.append(news_text)
    
    # Process stock data
    if stock_data:
        stock_text = "Financial Information:\n"
        for key, value in stock_data.items():
            stock_text += f"{key}: {value}\n"
        combined_text.append(stock_text)
    
    # Split text into chunks
    text_splitter = RecursiveCharacterTextSplitter(
        chunk_size=1000,
        chunk_overlap=200,
        length_function=len,
    )
    
    all_chunks = []
    for text in combined_text:
        chunks = text_splitter.split_text(text)
        all_chunks.extend(chunks)
    
    logger.info(f"Created {len(all_chunks)} text chunks for {company_name}")
    
    # Generate embeddings and store in Pinecone
    for i, chunk in enumerate(all_chunks):
        embedding = await generate_embedding(chunk)
        if embedding:
            # Store in Pinecone
            metadata = {
                "company_name": company_name,
                "company_symbol": company_symbol,
                "text": chunk,
                "chunk_id": i,
                "timestamp": datetime.now().isoformat()
            }
            
            key = f"{company_name.lower().replace(' ', '_')}_{i}_{datetime.now().timestamp()}"
            success = store_memory(pinecone_index, key, embedding, metadata)
            
            if success:
                logger.info(f"Successfully stored embedding {i+1}/{len(all_chunks)} for {company_name}")
            else:
                logger.error(f"Failed to store embedding {i+1}/{len(all_chunks)} for {company_name}")
        else:
            logger.error(f"Failed to generate embedding for chunk {i+1}/{len(all_chunks)}")
    
    return len(all_chunks)