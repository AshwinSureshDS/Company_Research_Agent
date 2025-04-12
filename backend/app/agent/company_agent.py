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
    get_company_news
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
        func=get_company_news,
        description="Get the latest news articles about a company with summaries. Input should be the company name."
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
        name="CompanySymbol",
        func=get_company_symbol,
        description="Look up a company's stock symbol based on its name. Input should be the company name."
    )
]

# Create memory with a window of 5 interactions
memory = ConversationBufferWindowMemory(
    k=5,
    return_messages=True,
    memory_key="chat_history",
    input_key="input"
)

# Create the agent
research_agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,
    memory=memory,
    handle_parsing_errors=True,
    max_iterations=3
)

def determine_query_intent(query):
    """
    Determine the intent of the user's query to select appropriate tools.
    """
    try:
        prompt = f"""
        Analyze the following user query and determine what information they're looking for.
        Respond with a JSON object containing boolean values for each category.
        
        Query: "{query}"
        
        Categories:
        - general_info: User wants general information about a company
        - financial_data: User wants financial metrics or stock information
        - news: User wants recent news about a company
        
        JSON response:
        """
        
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
                "news": False
            }
    except Exception as e:
        print(f"Error determining query intent: {str(e)}")
        # Default to general info only
        return {
            "general_info": True,
            "financial_data": False,
            "news": False
        }

async def generate_response(user_id, query, use_memory=True):
    """Generate a response using the LangChain agent with RAG."""
    try:
        # Determine query intent
        intents = determine_query_intent(query)
        
        # Select appropriate tools based on intent
        selected_tools = []
        
        # Always include general search
        selected_tools.append(tools_dict["CompanySearch"])
        
        # Add other tools based on intent
        if intents.get("financial_data", False):
            selected_tools.append(tools_dict["CompanyFinancials"])
            selected_tools.append(tools_dict["StockPrice"])
            selected_tools.append(tools_dict["CompanySymbol"])
        
        if intents.get("news", False):
            selected_tools.append(tools_dict["CompanyNews"])
        
        # Create a custom agent with selected tools
        custom_agent = initialize_agent(
            selected_tools,
            llm,
            agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
            verbose=True,
            memory=memory,
            handle_parsing_errors=True,
            max_iterations=3
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

# Create a dictionary of tools for easy access
tools_dict = {tool.name: tool for tool in tools}