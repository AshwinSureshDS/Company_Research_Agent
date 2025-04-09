from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, List, Optional
import google.generativeai as genai
from .config import GEMINI_API_KEY
from . import memory_manager
import uuid

# Initialize Gemini
genai.configure(api_key=GEMINI_API_KEY)

app = FastAPI()

# Define data models
class Message(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    user_id: str
    messages: List[Message]
    use_memory: bool = True

class ChatResponse(BaseModel):
    response: str
    conversation_id: str

@app.get("/")
async def root():
    return {"message": "Company Research Chatbot API is running."}

@app.post("/chat", response_model=ChatResponse)
async def chat(request: ChatRequest):
    try:
        # Generate a conversation ID if not provided
        conversation_id = str(uuid.uuid4())
        
        # Extract the latest user message
        user_message = request.messages[-1].content
        
        # Retrieve relevant memory if use_memory is True
        memory_context = ""
        if request.use_memory:
            # Get user preferences
            preferences = memory_manager.get_user_preferences(request.user_id)
            if preferences and preferences.get('matches'):
                memory_context += "Your preferences: "
                for match in preferences['matches']:
                    memory_context += f"{match.metadata.get('preference_value', '')}. "
                memory_context += "\n\n"
            
            # Get conversation history
            history = memory_manager.get_conversation_history(request.user_id, user_message)
            if history and history.get('matches'):
                memory_context += "Previous relevant conversations: \n"
                for match in history['matches']:
                    memory_context += f"{match.metadata.get('text', '')}\n"
                memory_context += "\n"
            
            # Get researched companies
            companies = memory_manager.get_researched_companies(request.user_id)
            if companies and companies.get('matches'):
                memory_context += "Companies you've researched: "
                for match in companies['matches']:
                    memory_context += f"{match.metadata.get('company_name', '')}. "
                memory_context += "\n\n"
        
        # Prepare the prompt with memory context
        prompt = f"""You are a company research assistant. Help the user research companies efficiently.
        
{memory_context}

User query: {user_message}

Provide a helpful response based on the available information."""
        
        # Generate response using Gemini
        model = genai.GenerativeModel('gemini-1.5-pro')
        response = model.generate_content(prompt)
        
        # Store the conversation in memory
        memory_manager.store_conversation(
            request.user_id,
            user_message,
            response.text
        )
        
        # Check if the message mentions a company and store it
        # This is a simple implementation - in Phase 2 we'll use more sophisticated entity extraction
        # For now, we'll just check if the message contains "company" or "about"
        if "company" in user_message.lower() or "about" in user_message.lower():
            # Extract potential company name (simple implementation)
            words = user_message.split()
            for i, word in enumerate(words):
                if word.lower() in ["company", "about"] and i+1 < len(words):
                    potential_company = words[i+1]
                    if potential_company not in ["the", "a", "an"]:
                        # Store company research
                        memory_manager.store_company_research(
                            request.user_id,
                            potential_company,
                            {"mentioned_in": user_message}
                        )
        
        return {
            "response": response.text,
            "conversation_id": conversation_id
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/preferences")
async def store_preference(
    user_id: str = Body(...),
    preference_type: str = Body(...),
    preference_value: str = Body(...)
):
    try:
        pref_id = memory_manager.store_user_preference(
            user_id,
            preference_type,
            preference_value
        )
        return {"message": "Preference stored successfully", "id": pref_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
