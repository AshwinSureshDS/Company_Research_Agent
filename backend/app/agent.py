# backend/app/agent.py
import google.generativeai as genai
from .config import GEMINI_API_KEY
from . import memory_manager

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)

class ResearchAgent:
    def __init__(self):
        self.model = genai.GenerativeModel('gemini-2.0-flash')
    
    def generate_response(self, user_id, query, use_memory=True):
        """Generate a response to the user query using Gemini and memory."""
        # Retrieve relevant memory if use_memory is True
        memory_context = ""
        if use_memory:
            # Get user preferences
            preferences = memory_manager.get_user_preferences(user_id)
            if preferences and preferences.get('matches'):
                memory_context += "User preferences: "
                for match in preferences['matches']:
                    memory_context += f"{match.metadata.get('preference_value', '')}. "
                memory_context += "\n\n"
            
            # Get conversation history
            history = memory_manager.get_conversation_history(user_id, query)
            if history and history.get('matches'):
                memory_context += "Previous relevant conversations: \n"
                for match in history['matches']:
                    memory_context += f"{match.metadata.get('text', '')}\n"
                memory_context += "\n"
            
            # Get researched companies
            companies = memory_manager.get_researched_companies(user_id)
            if companies and companies.get('matches'):
                memory_context += "Companies the user has researched: "
                for match in companies['matches']:
                    memory_context += f"{match.metadata.get('company_name', '')}. "
                memory_context += "\n\n"
        
        # Prepare the prompt with memory context
        prompt = f"""You are a company research assistant. Help the user research companies efficiently.
        
{memory_context}

User query: {query}

Provide a helpful response based on the available information."""
        
        # Generate response using Gemini
        response = self.model.generate_content(prompt)
        
        # Store the conversation in memory
        memory_manager.store_conversation(
            user_id,
            query,
            response.text
        )
        
        # Check if the query mentions a company and store it
        # This is a simple implementation - in Phase 2 we'll use more sophisticated entity extraction
        if "company" in query.lower() or "about" in query.lower():
            # Extract potential company name (simple implementation)
            words = query.split()
            for i, word in enumerate(words):
                if word.lower() in ["company", "about"] and i+1 < len(words):
                    potential_company = words[i+1]
                    if potential_company not in ["the", "a", "an"]:
                        # Store company research
                        memory_manager.store_company_research(
                            user_id,
                            potential_company,
                            {"mentioned_in": query}
                        )
        
        return response.text

# Create an instance of the agent
research_agent = ResearchAgent()