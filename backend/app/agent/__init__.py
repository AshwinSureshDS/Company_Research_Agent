# backend/app/agent/__init__.py
from agno.agent import Agent
import google.generativeai as genai
from ..config import GEMINI_API_KEY
from ..tools import (
    search_company_wrapper, 
    get_company_news_wrapper, 
    get_company_wiki_wrapper, 
    extract_article_content_wrapper
)
from .. import memory_manager

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Create agent with model name instead of instance
research_agent = Agent(
    model="gemini-2.0-flash",
    description="You are a company research assistant...",
    tools=[
        search_company_wrapper,
        get_company_news_wrapper,
        get_company_wiki_wrapper,
        extract_article_content_wrapper
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
        enhanced_query = f"""Memory Context:
{memory_context}

User Query: {query}"""
        
        # Generate response with proper error handling
        try:
            # Try with structured input format
            response = await research_agent.arun({"query": enhanced_query})
            
            # Handle response based on its type
            if isinstance(response, str):
                final_response = response
            else:
                # Try to extract response text using common attributes
                final_response = getattr(response, "text", None)
                if final_response is None:
                    final_response = getattr(response, "content", None)
                if final_response is None:
                    final_response = str(response)
                
        except Exception as e:
            print(f"Error with enhanced query: {str(e)}")
            # Fallback to direct model generation
            try:
                # Use the Gemini model directly as fallback
                fallback_response = gemini_model.generate_content(query)
                final_response = fallback_response.text
                print("Fallback response generated successfully")
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

# Export the necessary functions and objects
__all__ = ['generate_response', 'research_agent']