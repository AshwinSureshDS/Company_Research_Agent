# backend/app/agent/__init__.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import initialize_agent, AgentType
from langchain.tools import Tool
from langchain.memory import ConversationBufferMemory
from langchain.chains import ConversationChain
import google.generativeai as genai
from ..config import GEMINI_API_KEY, PINECONE_API_KEY
from ..tools.serper import search_company
from ..tools.news import get_company_news
from ..tools.wiki import get_company_wiki
from ..tools.jina_reader import extract_article_content
from ..memory.vector_store import query_pinecone

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Create LLM
llm = ChatGoogleGenerativeAI(model="gemini-2.0-flash", google_api_key=GEMINI_API_KEY)

# Define tools for LangChain
tools = [
    Tool(
        name="search_company",
        func=search_company,
        description="Search for general information about a company. Input should be the company name."
    ),
    Tool(
        name="get_company_news",
        func=get_company_news,
        description="Get the latest news articles about a company. Input should be the company name."
    ),
    Tool(
        name="get_company_wiki",
        func=get_company_wiki,
        description="Get Wikipedia information about a company. Input should be the company name."
    ),
    Tool(
        name="extract_article_content",
        func=extract_article_content,
        description="Extract the content from a news article URL. Input should be the URL."
    )
]

# Create memory
memory = ConversationBufferMemory(memory_key="chat_history", return_messages=True)

# Create agent
research_agent = initialize_agent(
    tools,
    llm,
    agent=AgentType.CHAT_CONVERSATIONAL_REACT_DESCRIPTION,
    verbose=True,
    memory=memory,
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
    """Get memory context from Pinecone."""
    # Query Pinecone for relevant context
    results = query_pinecone(
        text=query,  # Changed from 'query' to 'text'
        filter={"user_id": user_id}  # Added filter instead of namespace
    )
    
    memory_context = ""
    if results and results.get('matches'):
        for match in results['matches']:
            if 'metadata' in match and match['metadata']:
                memory_context += f"{match['metadata'].get('text', '')}\n"
    
    return memory_context

async def generate_response(user_id, query, use_memory=True):
    """Generate a response using the LangChain agent with memory context."""
    try:
        # Get memory context if needed
        if use_memory:
            memory_context = get_memory_context(user_id, query)
            # Add memory context to the agent's memory
            if memory_context:
                memory.chat_memory.add_user_message("Previous context: " + memory_context)
        
        # Generate response with error handling
        try:
            # Use LangChain agent
            response = research_agent.invoke({"input": query})
            final_response = response["output"]
        except Exception as e:
            print(f"Error with agent: {str(e)}")
            # Fallback to direct LLM
            try:
                conversation = ConversationChain(llm=llm, verbose=True)
                response = conversation.predict(input=f"User query: {query}\n\nPlease respond to this query about company information.")
                final_response = response
                final_response += "\n\nNote: I had some trouble accessing specialized research tools."
            except Exception as fallback_error:
                print(f"Fallback also failed: {str(fallback_error)}")
                final_response = "I'm sorry, I encountered an error while processing your request. Please try again."
        
        # Store conversation in Pinecone
        from ..memory.vector_store import store_in_pinecone
        store_in_pinecone(
            text=f"User: {query}\nAssistant: {final_response}",
            metadata={"user_id": user_id, "text": f"User: {query}\nAssistant: {final_response}"}
            # Removed namespace parameter
        )
        
        # Extract and store company names
        company_names = extract_company_names(query)
        for company_name in company_names:
            store_in_pinecone(
                text=f"Researched company: {company_name}",
                metadata={"user_id": user_id, "company_name": company_name, "mentioned_in": query}
                # Removed namespace parameter
            )
        
        return final_response
    except Exception as e:
        # Log the error and return a graceful message
        print(f"Error generating response: {str(e)}")
        return f"I'm sorry, I encountered an error while processing your request. Please try again."