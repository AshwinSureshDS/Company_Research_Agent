# backend/app/agent/__init__.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import AgentExecutor, create_react_agent
from langchain.prompts import PromptTemplate
from langchain.tools import StructuredTool
import google.generativeai as genai
from ..config import GEMINI_API_KEY
from ..tools import search_company, get_company_news, get_company_wiki, extract_article_content
from .. import memory_manager

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Define tools for LangChain
tools = [
    StructuredTool.from_function(
        func=search_company,
        name="search_company",
        description="Search for general information about a company"
    ),
    StructuredTool.from_function(
        func=get_company_news,
        name="get_company_news",
        description="Get the latest news articles about a company"
    ),
    StructuredTool.from_function(
        func=get_company_wiki,
        name="get_company_wiki",
        description="Get Wikipedia information about a company"
    ),
    StructuredTool.from_function(
        func=extract_article_content,
        name="extract_article_content",
        description="Extract the content from a news article URL"
    )
]

# Create LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY)

# Create agent prompt
prompt = PromptTemplate.from_template("""
You are a company research assistant. Your goal is to help users research companies efficiently.

Always provide accurate and helpful information based on the user's query.
Use the tools to gather information about companies when needed.
Summarize information in a clear, concise manner.
If the user asks about a company, use the appropriate tools to research it.

{chat_history}

User Query: {input}

{agent_scratchpad}
""")

# Create agent
agent = create_react_agent(llm, tools, prompt)

# Create agent executor
research_agent = AgentExecutor(
    agent=agent,
    tools=tools,
    verbose=True,
    handle_parsing_errors=True
)

def extract_company_names(text):
    """Extract company names from text using simple heuristics."""
    # This is a placeholder - in a real system, you'd use NER or a more sophisticated approach
    common_companies = ["Apple", "Microsoft", "Google", "Amazon", "Tesla", "Facebook", "Meta"]
    found_companies = []
    
    for company in common_companies:
        if company.lower() in text.lower():
            found_companies.append(company)
    
    return found_companies

def get_memory_context(user_id, query):
    """Get memory context for the agent."""
    memory_context = ""
    
    # Get user preferences - optimize by limiting to most relevant
    preferences = memory_manager.get_user_preferences(user_id, top_k=3)
    if preferences and preferences.get('matches'):
        memory_context += "User preferences: "
        for match in preferences['matches']:
            if 'metadata' in match and match['metadata']:
                memory_context += f"{match['metadata'].get('preference_value', '')}. "
        memory_context += "\n\n"
    
    # Get conversation history - optimize by using the query for relevance
    history = memory_manager.get_conversation_history(user_id, query, top_k=5)
    if history and history.get('matches'):
        memory_context += "Previous relevant conversations: \n"
        for match in history['matches']:
            if 'metadata' in match and match['metadata']:
                memory_context += f"{match['metadata'].get('text', '')}\n"
        memory_context += "\n"
    
    # Get researched companies - optimize by limiting to most recent
    companies = memory_manager.get_researched_companies(user_id, top_k=5)
    if companies and companies.get('matches'):
        memory_context += "Previously researched companies: "
        for match in companies['matches']:
            if 'metadata' in match and match['metadata']:
                company_name = match['metadata'].get('company_name', '')
                if company_name:
                    memory_context += f"{company_name}, "
        memory_context = memory_context.rstrip(", ") + "\n"
    
    return memory_context

async def generate_response(user_id, query, use_memory=True):
    """Generate a response using the LangChain agent with memory context."""
    try:
        # Get memory context if needed
        memory_context = ""
        if use_memory:
            memory_context = get_memory_context(user_id, query)
        
        # Generate response with error handling
        try:
            # Use LangChain agent
            response = research_agent.invoke({
                "input": query,
                "chat_history": memory_context
            })
            final_response = response.get("output", "")
        except Exception as e:
            print(f"Error with agent: {str(e)}")
            # Fallback to direct LLM
            try:
                direct_llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash")
                response = direct_llm.invoke(f"User query: {query}\n\nPlease respond to this query about company information.")
                final_response = response.content
                final_response += "\n\nNote: I had some trouble accessing specialized research tools."
            except Exception as fallback_error:
                print(f"Fallback also failed: {str(fallback_error)}")
                final_response = "I'm sorry, I encountered an error while processing your request. Please try again."
        
        # Store conversation in memory
        memory_manager.store_conversation(user_id, query, final_response)
        
        # Extract and store company names
        company_names = extract_company_names(query)
        for company_name in company_names:
            memory_manager.store_company_research(
                user_id,
                company_name,
                {"mentioned_in": query}
            )
        
        return final_response
    except Exception as e:
        # Log the error and return a graceful message
        print(f"Error generating response: {str(e)}")
        return f"I'm sorry, I encountered an error while processing your request. Please try again."