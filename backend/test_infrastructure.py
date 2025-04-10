# backend/test_infrastructure.py
import asyncio
import pprint
from app.memory.vector_store import init_pinecone, store_in_pinecone, query_pinecone
from app.memory.session import MemoryManager
# Update imports to use the wrapper functions
from app.tools import (
    search_company, get_company_news, get_company_wiki, extract_article_content,
    search_company_wrapper, get_company_news_wrapper, get_company_wiki_wrapper, extract_article_content_wrapper
)
from app.agent import generate_response

def test_pinecone_connection():
    print("Testing Pinecone connection...")
    index = init_pinecone()
    print(f"Successfully connected to Pinecone index: {index.describe_index_stats()}")
    return index

def test_memory_manager(index):
    print("\nTesting Memory Manager...")
    memory = MemoryManager(index)
    
    # Test storing user preference
    user_id = "test_user_1"
    pref_id = memory.store_user_preference(user_id, "industry", "Technology")
    print(f"Stored user preference with ID: {pref_id}")
    
    # Test storing conversation
    conv_id = memory.store_conversation(
        user_id, 
        "Tell me about Apple Inc.", 
        "Apple Inc. is a technology company that makes consumer electronics, software, and online services."
    )
    print(f"Stored conversation with ID: {conv_id}")
    
    # Test retrieving preferences
    prefs = memory.get_user_preferences(user_id)
    print(f"\nRetrieved user preferences:")
    pprint.pprint(prefs)
    
    # Test retrieving conversations
    convs = memory.get_conversation_history(user_id)
    print(f"\nRetrieved conversation history:")
    pprint.pprint(convs)
    
    return memory

def test_tools():
    print("\nTesting API Tools...")
    
    # Test Serper API
    print("\n1. Testing Serper API...")
    try:
        company_name = "Microsoft"
        result = search_company(company_name)
        if isinstance(result, dict) and "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Successfully retrieved search results for {company_name}")
            if isinstance(result, dict) and "organic" in result:
                print(f"Found {len(result.get('organic', []))} organic results")
    except Exception as e:
        print(f"Error testing Serper API: {str(e)}")
    
    # Test News API
    print("\n2. Testing News API...")
    try:
        company_name = "Tesla"
        result = get_company_news(company_name, page_size=3)
        if isinstance(result, dict) and "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Successfully retrieved news for {company_name}")
            if isinstance(result, dict) and "articles" in result:
                print(f"Found {len(result.get('articles', []))} articles")
    except Exception as e:
        print(f"Error testing News API: {str(e)}")
    
    # Test Wiki API
    print("\n3. Testing MediaWiki API...")
    try:
        company_name = "Amazon"
        result = get_company_wiki(company_name)
        if isinstance(result, dict) and "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Successfully retrieved Wikipedia information for {company_name}")
            if isinstance(result, dict) and "extract" in result:
                print(f"Extract length: {len(result.get('extract', ''))}")
    except Exception as e:
        print(f"Error testing MediaWiki API: {str(e)}")
    
    # Test Jina Reader API (optional - requires a valid URL)
    print("\n4. Testing Jina Reader API...")
    try:
        url = "https://en.wikipedia.org/wiki/Google"
        result = extract_article_content(url)
        if isinstance(result, dict) and "error" in result:
            print(f"Error: {result['error']}")
        else:
            print(f"Successfully extracted content from URL")
            print(f"Content length: {len(str(result))}")
    except Exception as e:
        print(f"Error testing Jina Reader API: {str(e)}")

async def test_agent():
    print("\nTesting Agno Agent...")
    
    try:
        user_id = "test_user_2"
        query = "Tell me about Apple's latest financial results"
        
        print(f"User query: {query}")
        response = await generate_response(user_id, query)
        print(f"\nAgent response: {response[:200]}...")  # Print first 200 chars
        
        # Test with memory
        follow_up_query = "What about their competitors?"
        print(f"\nFollow-up query: {follow_up_query}")
        response = await generate_response(user_id, follow_up_query)
        print(f"\nAgent response with memory: {response[:200]}...")  # Print first 200 chars
        
        return True
    except Exception as e:
        print(f"Error testing agent: {str(e)}")
        return False

async def main():
    # Test Phase 1: Memory System
    index = test_pinecone_connection()
    memory = test_memory_manager(index)
    
    # Test Phase 2: Tools and Agent
    test_tools()
    agent_success = await test_agent()
    
    if agent_success:
        print("\n✅ All tests completed successfully!")
    else:
        print("\n❌ Some tests failed. Please check the logs above.")

if __name__ == "__main__":
    asyncio.run(main())