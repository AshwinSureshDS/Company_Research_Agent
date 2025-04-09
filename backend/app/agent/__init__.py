# backend/app/agent/__init__.py
# Let's use a simpler approach based on the actual Agno repository
from agno.agent import Agent
import google.generativeai as genai
from ..config import GEMINI_API_KEY
from ..tools import search_company, get_company_news, get_company_wiki, extract_article_content
from .. import memory_manager

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Create the agent directly using the Agent class
research_agent = Agent(
    model="gemini-1.5-pro",
    description="You are a company research assistant. Your goal is to help users research companies efficiently.",
    tools=[
        {
            "name": "search_company",
            "description": "Search for general information about a company",
            "function": search_company
        },
        {
            "name": "get_company_news",
            "description": "Get the latest news articles about a company",
            "function": get_company_news
        },
        {
            "name": "get_company_wiki",
            "description": "Get Wikipedia information about a company",
            "function": get_company_wiki
        },
        {
            "name": "extract_article_content",
            "description": "Extract the content from a news article URL",
            "function": extract_article_content
        }
    ],
    instructions=[
        "Always provide accurate and helpful information based on the user's query.",
        "Use the tools to gather information about companies when needed.",
        "Summarize information in a clear, concise manner.",
        "If the user asks about a company, use the appropriate tools to research it."
    ],
    show_tool_calls=True,
    markdown=True
)

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
        memory_context += "Companies the user has researched: "
        for match in companies['matches']:
            if 'metadata' in match and match['metadata']:
                memory_context += f"{match['metadata'].get('company_name', '')}. "
        memory_context += "\n\n"
    
    return memory_context

# Improved entity extraction function
def extract_company_names(query):
    """Extract potential company names from the query."""
    # This is a simple implementation - in a production system, 
    # you would use a more sophisticated NER model
    potential_companies = []
    
    # Check for common patterns
    words = query.split()
    for i, word in enumerate(words):
        if word.lower() in ["company", "about", "corporation", "inc", "corp", "ltd"] and i > 0:
            potential_company = words[i-1]
            if potential_company.lower() not in ["the", "a", "an", "this", "that"]:
                potential_companies.append(potential_company)
    
    return potential_companies

async def generate_response(user_id, query, use_memory=True):
    """Generate a response using the Agno agent with memory context."""
    try:
        # Get memory context if needed
        memory_context = ""
        if use_memory:
            memory_context = get_memory_context(user_id, query)
        
        # Add memory context to the query
        enhanced_query = f"""
        Memory Context:
        {memory_context}
        
        User Query: {query}
        """
        
        # Generate response with error handling
        try:
            # Properly handle AgentResponse object
            agent_response = await research_agent.arun(enhanced_query)
            response = agent_response.output  # Extract actual response text
        except Exception as e:
            print(f"Error with enhanced query: {str(e)}")
            # Fallback with proper error handling
            try:
                agent_response = await research_agent.arun(query)
                response = agent_response.output if hasattr(agent_response, 'output') else str(agent_response)
            except Exception as fallback_error:
                response = f"Error processing request: {str(fallback_error)}"
            response += "\n\nNote: I had some trouble accessing your previous context."
        
        # Store conversation in memory
        memory_manager.store_conversation(user_id, query, response)
        
        # Extract and store company names
        company_names = extract_company_names(query)
        for company_name in company_names:
            memory_manager.store_company_research(
                user_id,
                company_name,
                {"mentioned_in": query}
            )
        
        return response
    except Exception as e:
        # Log the error and return a graceful message
        print(f"Error generating response: {str(e)}")
        return f"I'm sorry, I encountered an error while processing your request. Please try again."

# Export the necessary functions and objects
__all__ = ['generate_response', 'research_agent']