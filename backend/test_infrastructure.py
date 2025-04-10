# backend/test_infrastructure.py
import asyncio
import pprint
from app.memory.vector_store import init_pinecone, store_in_pinecone, query_pinecone
from app.tools.serper import search_company
from app.tools.news import get_company_news
from app.tools.wiki import get_company_wiki
from app.tools.jina_reader import extract_article_content
from app.agent import generate_response

async def test_api_tools():
    print("Testing API Tools...\n")
    
    # Test Serper API
    print("1. Testing Serper API...")
    search_results = search_company("Microsoft")
    print(f"Successfully retrieved search results for Microsoft")
    print(f"Found {len(search_results['organic'])} organic results\n")
    
    # Test News API
    print("2. Testing News API...")
    news_results = get_company_news("Tesla")
    print(f"Successfully retrieved news for Tesla")
    print(f"Found {len(news_results['articles'])} articles\n")
    
    # Test MediaWiki API
    print("3. Testing MediaWiki API...")
    wiki_results = get_company_wiki("Amazon")
    print(f"Successfully retrieved Wikipedia information for Amazon")
    print(f"Extract length: {len(wiki_results)}\n")
    
    # Test Jina Reader API
    print("4. Testing Jina Reader API...")
    article_url = "https://www.bbc.com/news/business-56142662"
    content = extract_article_content(article_url)
    print(f"Successfully extracted content from URL")
    print(f"Content length: {len(content)}\n")

async def test_langchain_agent():
    print("Testing LangChain Agent...")
    
    # Test query
    user_id = "test_user"
    query = "Tell me about Apple's latest financial results"
    print(f"User query: {query}")
    
    # Generate response
    response = await generate_response(user_id, query, use_memory=False)
    print(f"Agent response: {response[:100]}...\n")
    
    # Test follow-up query with memory
    follow_up = "What about their competitors?"
    print(f"Follow-up query: {follow_up}")
    
    # Generate response with memory
    response_with_memory = await generate_response(user_id, follow_up, use_memory=True)
    print(f"Agent response with memory: {response_with_memory[:100]}...\n")

async def main():
    # Initialize Pinecone
    init_pinecone()
    
    # Test API tools
    await test_api_tools()
    
    # Test LangChain agent
    await test_langchain_agent()
    
    print("✅ All tests completed successfully!")

if __name__ == "__main__":
    asyncio.run(main())