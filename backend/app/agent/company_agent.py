# backend/app/agent/company_agent.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.memory import ConversationBufferWindowMemory
import google.generativeai as genai
import uuid
import json
from ..config import GEMINI_API_KEY
from ..tools.company_tools import (
    search_company, 
    get_company_financials, 
    get_stock_price, 
    get_company_symbol,
    get_combined_news,
    analyze_company_article,
    get_wikipedia_info,
    get_comprehensive_company_info,
    compare_stocks  # Add the new function
)
from ..memory.vector_store import init_pinecone, store_in_pinecone, query_pinecone

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Create LLM with the specified model
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY)

# Initialize Pinecone
pinecone_index = init_pinecone()

# Define tools for LangChain
tools = [
    Tool(
        name="CompanySearch",
        func=search_company,
        description="Search for general information about a company. Input should be the company name."
    ),
    Tool(
        name="CompanyNews",
        func=get_combined_news,
        description="Get the latest news articles about a company from multiple sources. Input should be the company name."
    ),
    Tool(
        name="CompanyFinancials",
        func=get_company_financials,
        description="Get financial data for a company. Input should be the company's stock symbol (e.g., AAPL for Apple)."
    ),
    Tool(
        name="StockPrice",
        func=get_stock_price,
        description="Get the latest stock price for a company. Input should be the company's stock symbol."
    ),
    Tool(
        name="CompareStocks",
        func=compare_stocks,
        description="Compare stock prices and performance of multiple companies. Input should be a comma-separated list of stock symbols (e.g., 'AAPL,MSFT,GOOGL')."
    ),
    Tool(
        name="CompanySymbol",
        func=get_company_symbol,
        description="Look up a company's stock symbol based on its name. Input should be the company name."
    ),
    Tool(
        name="ArticleAnalysis",
        func=analyze_company_article,
        description="Analyze a specific article about a company or find and analyze a relevant article. Input should be the company name, or company name and article URL separated by a comma."
    ),
    Tool(
        name="WikipediaInfo",
        func=get_wikipedia_info,
        description="Get information about a company from Wikipedia. Input should be the company name."
    ),
    Tool(
        name="ComprehensiveInfo",
        func=get_comprehensive_company_info,
        description="Get comprehensive information about a company from multiple sources including search, Wikipedia, and financials. Input should be the company name."
    )
]

# Create a dictionary of tools for easy access
tools_dict = {tool.name: tool for tool in tools}

# Add a rate limiting wrapper for the LLM
def create_rate_limited_llm(max_retries=5, base_delay=2):
    """Create an LLM with rate limiting capabilities."""
    original_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY)
    
    # Store the original __call__ method
    original_call = original_llm.__call__
    
    # Define a new __call__ method with rate limiting
    def rate_limited_call(*args, **kwargs):
        retries = 0
        while True:
            try:
                return original_call(*args, **kwargs)
            except Exception as e:
                error_message = str(e).lower()
                if ("429" in error_message or 
                    "quota" in error_message or 
                    "resource exhausted" in error_message) and retries < max_retries:
                    
                    retries += 1
                    delay = base_delay * (2 ** (retries - 1)) + random.random()
                    print(f"Rate limit hit. Retrying in {delay:.2f} seconds... (Attempt {retries}/{max_retries})")
                    import time
                    time.sleep(delay)
                else:
                    # If it's not a rate limit error or we've exceeded max retries, raise the error
                    if retries >= max_retries:
                        print(f"Maximum retries ({max_retries}) exceeded. Giving up.")
                    raise
        
    # Replace the original __call__ method with our rate-limited version
    original_llm.__call__ = rate_limited_call
    
    return original_llm

# Create rate-limited LLM
llm = create_rate_limited_llm()

# Create memory with a window of 5 interactions
memory = ConversationBufferWindowMemory(
    k=5,
    return_messages=True,
    memory_key="chat_history",
    input_key="input"
)

# Create the agent with a custom prefix to identify itself as "Company Research Agent"
prefix = """You are the Company Research Agent, an AI assistant specialized in providing information about companies, their financials, news, and stock performance. 
I will assist you with any questions about companies, industries, stocks, and market information.

IMPORTANT: I CAN provide real-time stock prices and comparisons using Alpha Vantage data. When users ask about stock prices or comparisons, I should use the StockPrice or CompareStocks tools.

For stock prices, I need the company's stock symbol (e.g., AAPL for Apple, TSLA for Tesla).
For stock comparisons, I can compare multiple companies by using a comma-separated list of symbols.
"""

# Create the agent
research_agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,
    memory=memory,
    handle_parsing_errors=True,
    max_iterations=3,
    agent_kwargs={
        "prefix": prefix
    }
)

def determine_query_intent(query):
    """
    Determine the intent of the user's query to select appropriate tools.
    """
    # Quick check for common keywords to avoid unnecessary API calls
    query_lower = query.lower()
    
    # Check for stock/financial keywords
    if any(term in query_lower for term in ["stock", "price", "share", "market", "trading", "compare", "financial", "revenue", "profit"]):
        return {
            "general_info": True,
            "financial_data": True,
            "news": False,
            "article_analysis": False,
            "wikipedia": False
        }
    
    # Check for news keywords
    if any(term in query_lower for term in ["news", "recent", "latest", "article", "announcement"]):
        return {
            "general_info": True,
            "financial_data": False,
            "news": True,
            "article_analysis": True,
            "wikipedia": False
        }
    
    # Check for Wikipedia keywords
    if any(term in query_lower for term in ["wiki", "wikipedia", "background", "history", "about"]):
        return {
            "general_info": True,
            "financial_data": False,
            "news": False,
            "article_analysis": False,
            "wikipedia": True
        }
    
    try:
        # Only use the API if we couldn't determine intent from keywords
        prompt = f"""
        Analyze the following user query and determine what information they're looking for.
        Respond with a JSON object containing boolean values for each category.
        
        Query: "{query}"
        
        Categories:
        - general_info: User wants general information about a company
        - financial_data: User wants financial metrics or stock information
        - news: User wants recent news about a company
        - article_analysis: User wants detailed analysis of articles or content about a company
        - wikipedia: User wants information from Wikipedia about a company
        
        JSON response:
        """
        
        # Use a simpler model for intent detection to reduce quota usage
        response = genai.GenerativeModel('gemini-1.5-flash').generate_content(prompt)
        intent_text = response.text.strip()
        
        # Parse the JSON response
        try:
            intents = json.loads(intent_text)
            return intents
        except:
            # Fallback if JSON parsing fails
            return {
                "general_info": True,
                "financial_data": False,
                "news": False,
                "article_analysis": False,
                "wikipedia": False
            }
    except Exception as e:
        print(f"Error determining query intent: {str(e)}")
        # Default to general info only
        return {
            "general_info": True,
            "financial_data": False,
            "news": False,
            "article_analysis": False,
            "wikipedia": False
        }

async def generate_response(user_id, query, use_memory=True):
    """Generate a response using the LangChain agent with RAG."""
    try:
        # Determine query intent
        intents = determine_query_intent(query)
        
        # Select appropriate tools based on intent
        selected_tools = []
        
        # Always include these core tools
        selected_tools.append(tools_dict["CompanySearch"])
        selected_tools.append(tools_dict["CompanySymbol"])
        selected_tools.append(tools_dict["StockPrice"])
        selected_tools.append(tools_dict["CompareStocks"])
        
        # Add other tools based on intent
        if intents.get("financial_data", False):
            selected_tools.append(tools_dict["CompanyFinancials"])
        
        if intents.get("news", False):
            selected_tools.append(tools_dict["CompanyNews"])
        
        if intents.get("wikipedia", False):
            selected_tools.append(tools_dict["WikipediaInfo"])
        
        if intents.get("article_analysis", False):
            selected_tools.append(tools_dict["ArticleAnalysis"])
        
        if intents.get("general_info", False):
            selected_tools.append(tools_dict["ComprehensiveInfo"])
        
        # Ensure we don't have duplicate tools
        selected_tools = list({tool.name: tool for tool in selected_tools}.values())
        
        # Create a custom agent with selected tools and the Company Research Agent identity
        try:
            custom_agent = initialize_agent(
                selected_tools,
                llm,
                agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
                verbose=True,
                memory=memory,
                handle_parsing_errors=True,
                max_iterations=3,
                agent_kwargs={
                    "prefix": prefix
                }
            )
        except Exception as e:
            print(f"Error initializing agent: {str(e)}")
            # Fallback to using fewer tools if initialization fails
            custom_agent = initialize_agent(
                [tools_dict["CompanySearch"], tools_dict["CompanySymbol"]],
                llm,
                agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
                verbose=True,
                memory=memory,
                handle_parsing_errors=True,
                max_iterations=2,
                agent_kwargs={
                    "prefix": prefix
                }
            )
        
        # Retrieve relevant context from vector store
        if use_memory:
            context_results = query_pinecone(
                pinecone_index,
                query,
                top_k=3,
                namespace=user_id
            )
            
            context = ""
            for match in context_results.get("matches", []):
                if match.get("metadata") and "text" in match.get("metadata", {}):
                    context += match["metadata"]["text"] + "\n\n"
            
            if context:
                query = f"Context: {context}\n\nUser query: {query}"
        
        # Generate response
        response = custom_agent.run(input=query)
        
        # Store the interaction in vector store for future reference
        if use_memory:
            store_in_pinecone(
                pinecone_index,
                f"Query: {query}\nResponse: {response}",
                {"text": f"Query: {query}\nResponse: {response}", "timestamp": str(uuid.uuid4())},
                namespace=user_id
            )
        
        return response
    except Exception as e:
        print(f"Error generating response: {str(e)}")
        return f"I'm sorry, I encountered an error while processing your request. Please try again."