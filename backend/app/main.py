from fastapi import FastAPI, HTTPException, Query, Body
import asyncio
import uuid
import time
import random
import os
import sys
from typing import List, Optional
from fastapi.middleware.cors import CORSMiddleware
from .agent.company_agent import generate_response
from .tools.company_tools import get_stock_price, compare_stocks
import json
from pathlib import Path
from datetime import datetime

# Increase socket buffer size for Windows
if sys.platform == 'win32':
    import socket
    socket.setdefaulttimeout(30)  # 30 second timeout
    
    # Try to increase the socket buffer size
    try:
        # Attempt to free up socket resources
        for i in range(10):
            try:
                s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
                s.close()
            except:
                pass
    except:
        pass

# Create a directory for storing chat history
CHAT_DIR = Path("d:/College/Company_Research_Chatbot/backend/data/chats")
CHAT_DIR.mkdir(parents=True, exist_ok=True)

app = FastAPI()

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],  # Specifically allow your Next.js frontend
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/")
async def root():
    return {"message": "Company Research Chatbot API is running."}

@app.get("/api/stock/{symbol}")
async def stock_price(symbol: str):
    """Get the latest stock price for a company symbol."""
    result = get_stock_price(symbol)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.get("/api/compare-stocks/")
async def compare_stock_prices(symbols: str = Query(..., description="Comma-separated list of stock symbols")):
    """Compare stock prices for multiple companies."""
    symbol_list = [s.strip() for s in symbols.split(',')]
    result = compare_stocks(symbol_list)
    if "error" in result:
        raise HTTPException(status_code=404, detail=result["error"])
    return result

@app.post("/api/chat/")
async def chat(request: dict):
    """Generate a response to a user query."""
    user_id = request.get("user_id", str(uuid.uuid4()))
    query = request.get("query")
    
    if not query:
        raise HTTPException(status_code=400, detail="Query is required")
    
    try:
        response = await retry_with_backoff(generate_response, user_id, query)
        return {"response": response, "user_id": user_id}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

# Add logging for better error tracking
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

@app.get("/api/chats/")
async def get_chats():
    """Get all chat histories."""
    chats = []
    try:
        logger.info(f"Fetching chats from {CHAT_DIR}")
        for chat_file in CHAT_DIR.glob("*.json"):
            with open(chat_file, "r") as f:
                chat = json.load(f)
                chats.append(chat)
        return {"chats": chats}
    except Exception as e:
        logger.error(f"Error fetching chats: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/chats/{chat_id}")
async def get_chat(chat_id: str):
    """Get a specific chat history."""
    chat_path = CHAT_DIR / f"{chat_id}.json"
    if not chat_path.exists():
        raise HTTPException(status_code=404, detail="Chat not found")
    
    try:
        with open(chat_path, "r") as f:
            chat = json.load(f)
        return {"chat": chat}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.put("/api/chats/{chat_id}")
async def save_chat(chat_id: str, chat_data: dict = Body(...)):
    """Save a chat history."""
    chat = chat_data.get("chat")
    if not chat:
        raise HTTPException(status_code=400, detail="Chat data is required")
    
    try:
        chat_path = CHAT_DIR / f"{chat_id}.json"
        with open(chat_path, "w") as f:
            json.dump(chat, f)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.delete("/api/chats/{chat_id}")
async def delete_chat(chat_id: str):
    """Delete a chat history."""
    chat_path = CHAT_DIR / f"{chat_id}.json"
    if not chat_path.exists():
        raise HTTPException(status_code=404, detail="Chat not found")
    
    try:
        os.remove(chat_path)
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.patch("/api/chats/{chat_id}/title")
async def update_chat_title(chat_id: str, title_data: dict = Body(...)):
    """Update a chat title."""
    new_title = title_data.get("title")
    if not new_title:
        raise HTTPException(status_code=400, detail="Title is required")
    
    chat_path = CHAT_DIR / f"{chat_id}.json"
    if not chat_path.exists():
        raise HTTPException(status_code=404, detail="Chat not found")
    
    try:
        with open(chat_path, "r") as f:
            chat = json.load(f)
        
        chat["title"] = new_title
        chat["updatedAt"] = datetime.now().isoformat()
        
        with open(chat_path, "w") as f:
            json.dump(chat, f)
        
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@app.post("/api/chats/{chat_id}/messages")
async def add_message_to_chat(chat_id: str, message_data: dict = Body(...)):
    """Add a message to a chat."""
    message = message_data.get("message")
    if not message:
        raise HTTPException(status_code=400, detail="Message is required")
    
    chat_path = CHAT_DIR / f"{chat_id}.json"
    
    try:
        if chat_path.exists():
            with open(chat_path, "r") as f:
                chat = json.load(f)
        else:
            # Create a new chat if it doesn't exist
            chat = {
                "id": chat_id,
                "title": "New Conversation",
                "messages": [],
                "createdAt": datetime.now().isoformat(),
                "updatedAt": datetime.now().isoformat()
            }
        
        # Update title if it's the first user message and title is default
        if len(chat["messages"]) == 0 and message["role"] == "user" and chat["title"] == "New Conversation":
            content = message["content"]
            chat["title"] = content[:30] + "..." if len(content) > 30 else content
        
        chat["messages"].append(message)
        chat["updatedAt"] = datetime.now().isoformat()
        
        with open(chat_path, "w") as f:
            json.dump(chat, f)
        
        return {"success": True}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

async def retry_with_backoff(func, *args, max_retries=5, base_delay=2, **kwargs):
    """Retry a function with exponential backoff when rate limit errors occur."""
    retries = 0
    while True:
        try:
            return await func(*args, **kwargs)
        except Exception as e:
            error_message = str(e).lower()
            if ("429" in error_message or 
                "quota" in error_message or 
                "resource exhausted" in error_message) and retries < max_retries:
                
                retries += 1
                delay = base_delay * (2 ** (retries - 1)) + random.uniform(0, 1)
                print(f"\nRate limit hit. Retrying in {delay:.2f} seconds... (Attempt {retries}/{max_retries})")
                time.sleep(delay)
            else:
                # If it's not a rate limit error or we've exceeded max retries, raise the error
                if retries >= max_retries:
                    print(f"\nMaximum retries ({max_retries}) exceeded. Please try again later.")
                    return f"I'm sorry, I'm currently experiencing high demand. Please try again in a few minutes."
                else:
                    print(f"\nError: {str(e)}")
                    return f"I encountered an error: {str(e)}"

async def main():
    print("Company Research Agent")
    print("Ask me anything about companies, their financials, news, or stock performance")
    print("Type 'exit' to quit")
    print("-" * 50)
    
    # Generate a user ID
    user_id = str(uuid.uuid4())
    
    while True:
        # Get user input
        user_input = input("\nYou: ")
        
        if user_input.lower() == 'exit':
            break
        
        # Generate response with retry mechanism
        print("\nProcessing...")
        response = await retry_with_backoff(generate_response, user_id, user_input)
        
        # Display response
        print(f"\nAgent: {response}")

# Use uvicorn to run the app instead of asyncio.run
if __name__ == "__main__":
    import uvicorn
    uvicorn.run("backend.app.main:app", host="0.0.0.0", port=8000, reload=True)
