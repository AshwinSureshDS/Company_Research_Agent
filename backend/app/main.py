from fastapi import FastAPI

app = FastAPI()

@app.get("/")
async def root():
    return {"message": "Company Research Chatbot API is running."}

# backend/app/main.py
import asyncio
import uuid
from .agent.company_agent import generate_response

async def main():
    print("Company Research Agent")
    print("Type 'exit' to quit")
    print("-" * 50)
    
    # Generate a user ID
    user_id = str(uuid.uuid4())
    
    while True:
        # Get user input
        user_input = input("\nYou: ")
        
        if user_input.lower() == 'exit':
            break
        
        # Generate response
        print("\nProcessing...")
        response = await generate_response(user_id, user_input)
        
        # Display response
        print(f"\nAgent: {response}")

if __name__ == "__main__":
    asyncio.run(main())
