from fastapi import FastAPI, HTTPException, Query
import asyncio
import uuid
import time
import random
from typing import List, Optional
from .agent.company_agent import generate_response
from .tools.company_tools import get_stock_price, compare_stocks

app = FastAPI()

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

if __name__ == "__main__":
    asyncio.run(main())
