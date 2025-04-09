from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel
from typing import Dict, List, Optional
import asyncio
# Fix the import to use the correct module
from .agent import generate_response
from . import memory_manager

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
        # Extract the latest user message
        user_message = request.messages[-1].content
        
        # Generate response using Agno agent
        response = await generate_response(request.user_id, user_message, request.use_memory)
        
        return {
            "response": response,
            "conversation_id": "session-" + request.user_id
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
