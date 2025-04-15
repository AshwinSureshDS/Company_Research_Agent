# backend/app/agent/company_agent.py
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.chains import LLMChain
from langchain.prompts import PromptTemplate
import logging
import re
from backend.app.memory import initialize_pinecone, query_similar
from backend.app.embeddings import generate_embedding
from backend.app.data_ingestion import process_company_data
from backend.app.config import GEMINI_API_KEY

logger = logging.getLogger(__name__)

# Initialize Pinecone
pinecone_index = initialize_pinecone()

async def extract_company_info(query):
    """Extract company name and possibly stock symbol from the query."""
    # Use Gemini to extract company information
    llm = ChatGoogleGenerativeAI(
        model="gemini-2.0-flash",
        google_api_key=GEMINI_API_KEY,
        temperature=0.1
    )
    
    prompt = PromptTemplate(
        template="""
        Extract the company name and stock symbol (if present) from the following query.
        
        Query: {query}
        
        IMPORTANT: You must respond ONLY with a valid JSON object in the following format:
        {{
            "company_name": "extracted company name or null if none found",
            "company_symbol": "extracted stock symbol or null if none found"
        }}
        
        Do not include any explanations, notes, or additional text before or after the JSON.
        """,
        input_variables=["query"]
    )
    
    chain = LLMChain(llm=llm, prompt=prompt)
    
    try:
        response = await chain.arun(query=query)
        # Clean the response to ensure it's valid JSON
        response = response.strip()
        # Remove any markdown formatting that might be present
        if response.startswith("```json"):
            response = response.replace("```json", "", 1)
        if response.endswith("```"):
            response = response.replace("```", "", 1)
        response = response.strip()
        
        # Parse the JSON response
        import json
        result = json.loads(response)
        
        # Ensure the result has the expected structure
        if not isinstance(result, dict):
            raise ValueError("Response is not a dictionary")
        
        # Ensure company_name is present
        if "company_name" not in result:
            result["company_name"] = None
        
        # Ensure company_symbol is present
        if "company_symbol" not in result:
            result["company_symbol"] = None
            
        return result
    except Exception as e:
        logger.error(f"Error extracting company info: {str(e)}")
        # Attempt to extract company name directly from the query as a fallback
        company_names = ["Reliance", "Tesla", "Apple", "Microsoft", "Google", "Amazon", "Facebook", "Netflix"]
        for name in company_names:
            if name.lower() in query.lower():
                return {"company_name": name, "company_symbol": None}
        
        # If all else fails, return a default dictionary
        return {"company_name": None, "company_symbol": None}

# Update the model name in the check_query_relevance function
# Update the check_query_relevance function to be more nuanced
async def check_query_relevance(query: str):
    """
    Determine if a query is a general greeting/conversation or company-related.
    Returns:
    - "greeting" for general greetings and small talk
    - "company" for company-related queries
    - "general" for general knowledge questions
    """
    try:
        # Use Gemini to check relevance
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=GEMINI_API_KEY,
            temperature=0.1
        )
        
        prompt = PromptTemplate(
            template="""
            Classify the following query into one of these categories:
            
            Query: {query}
            
            - GREETING: If it's a greeting, small talk, or asking about capabilities (e.g., "hello", "how are you", "what can you do")
            - COMPANY: If it's related to companies, business, finance, stocks, or corporate information
            - GENERAL: If it's about general knowledge, entertainment, personal topics, or other non-business subjects
            
            Respond with ONLY "GREETING", "COMPANY", or "GENERAL".
            """,
            input_variables=["query"]
        )
        
        chain = LLMChain(llm=llm, prompt=prompt)
        response = await chain.arun(query=query)
        
        # Clean up response and check
        response = response.strip().upper()
        if "GREETING" in response:
            return "greeting"
        elif "COMPANY" in response:
            return "company"
        else:
            return "general"
    except Exception as e:
        logger.error(f"Error checking query relevance: {str(e)}")
        # If there's an error, default to allowing the query
        return "company"

# Update the generate_response function to use all available tools

async def generate_response(user_id, query):
    """Generate a response to a user query using Gemini and Pinecone."""
    try:
        # First, check what type of query this is
        query_type = await check_query_relevance(query)
        
        # Initialize the LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.0-flash",
            google_api_key=GEMINI_API_KEY,
            temperature=0.7
        )
        
        # Handle greeting/small talk
        if query_type == "greeting":
            # Handle greeting logic...
            from datetime import datetime
            current_date = datetime.now().strftime("%B %d, %Y")
            current_time = datetime.now().strftime("%H:%M:%S")
            
            prompt = PromptTemplate(
                template="""
                You are a friendly AI assistant specialized in company research and financial information.
                
                Current date: {current_date}
                Current time: {current_time}
                
                Respond to this greeting or small talk in a friendly, concise way. Mention that you're 
                specialized in company information but can also chat casually.
                
                User message: {query}
                
                Response:
                """,
                input_variables=["query", "current_date", "current_time"]
            )
            
            chain = LLMChain(llm=llm, prompt=prompt)
            return await chain.arun(query=query, current_date=current_date, current_time=current_time)
        
        # Handle general knowledge
        elif query_type == "general":
            # Handle general knowledge logic...
            prompt = PromptTemplate(
                template="""
                You are an AI assistant specialized in company research and financial information.
                
                The user has asked a general knowledge question that's not related to companies or business.
                
                User message: {query}
                
                Politely explain that while you're primarily designed to help with company and business information,
                you can try to assist with their question. Then provide a brief, helpful response to their query
                if possible, or suggest they ask about company-related topics where you can provide more detailed information.
                
                Response:
                """,
                input_variables=["query"]
            )
            
            chain = LLMChain(llm=llm, prompt=prompt)
            return await chain.arun(query=query)
        
        # For company-related queries
        else:
            # Extract company information
            company_info = await extract_company_info(query)
            
            # Fix here: Check if company_info is a tuple and handle it properly
            if isinstance(company_info, tuple):
                company_name = company_info[0] if len(company_info) > 0 else None
                company_symbol = company_info[1] if len(company_info) > 1 else None
                company_info = {
                    "company_name": company_name,
                    "company_symbol": company_symbol
                }
            
            # Now safely get the company name and symbol
            company_name = company_info.get("company_name")
            company_symbol = company_info.get("company_symbol")
            
            # If no company name was extracted, inform the user
            if not company_name:
                return "I couldn't identify a specific company in your query. Could you please mention the company name more clearly?"
            
            logger.info(f"Extracted company: {company_name}, symbol: {company_symbol}")
            
            # Generate embedding for the query
            query_embedding = await generate_embedding(query)
            
            # Search for similar information in Pinecone
            similar_info = []
            
            # Try to find company by name first
            try:
                results = query_similar(
                    pinecone_index, 
                    query_embedding, 
                    filter={"company_name": {"$eq": company_name}},
                    top_k=5
                )
                
                if results and hasattr(results, 'matches') and results.matches:
                    for match in results.matches:
                        if match.score > 0.7:  # Relevance threshold
                            similar_info.append(match.metadata.get("content", ""))
            except Exception as e:
                logger.error(f"Error querying Pinecone by company name: {str(e)}")
            
            # If no results by exact name, try a more flexible search
            if not similar_info:
                try:
                    # Query without company filter to find any relevant information
                    results = query_similar(
                        pinecone_index,
                        query_embedding,
                        top_k=5
                    )
                    
                    if results and hasattr(results, 'matches') and results.matches:
                        for match in results.matches:
                            if match.score > 0.7:  # Relevance threshold
                                similar_info.append(match.metadata.get("content", ""))
                except Exception as e:
                    logger.error(f"Error querying Pinecone without filter: {str(e)}")
            
            # If we still don't have information, fetch it from external APIs
            if not similar_info:
                logger.info(f"No data found in Pinecone for {company_name}, fetching from external sources")
                
                # Import here to avoid circular imports
                from backend.app.tools.company_tools import (
                    get_company_overview,
                    get_stock_price,
                    get_company_news,
                    search_company_info,
                    get_wikipedia_info,
                    get_company_financials,
                    extract_info_from_url
                )
                
                # Fetch company data from multiple sources
                company_data = {}
                
                # Try to get stock symbol if not provided
                if not company_symbol:
                    try:
                        # Search for the company symbol
                        from backend.app.tools.company_tools import search_company_symbol
                        company_symbol = await search_company_symbol(company_name)
                        logger.info(f"Found symbol for {company_name}: {company_symbol}")
                    except Exception as e:
                        logger.error(f"Error finding symbol for {company_name}: {str(e)}")
                
                # Get company overview from Alpha Vantage
                try:
                    if company_symbol:
                        overview = get_company_overview(company_symbol)
                        if overview and not isinstance(overview, str) and "error" not in overview:
                            company_data["overview"] = overview
                            similar_info.append(f"Company Overview: {overview}")
                except Exception as e:
                    logger.error(f"Error getting company overview: {str(e)}")
                
                # Get company financials from Alpha Vantage
                try:
                    if company_symbol:
                        financials = get_company_financials(company_symbol)
                        if financials and not isinstance(financials, str) and "error" not in financials:
                            company_data["financials"] = financials
                            similar_info.append(f"Financial Data: {financials}")
                except Exception as e:
                    logger.error(f"Error getting company financials: {str(e)}")
                
                # Get stock price
                try:
                    if company_symbol:
                        price_data = get_stock_price(company_symbol)
                        if price_data and "error" not in price_data:
                            company_data["stock_price"] = price_data
                            similar_info.append(f"Stock Price: {price_data}")
                except Exception as e:
                    logger.error(f"Error getting stock price: {str(e)}")
                
                # Get company news
                try:
                    news = get_company_news(company_name)
                    if news and not isinstance(news, str) and "error" not in news:
                        company_data["news"] = news
                        for article in news[:3]:  # Limit to top 3 news items
                            similar_info.append(f"News: {article.get('title')} - {article.get('description')}")
                except Exception as e:
                    logger.error(f"Error getting company news: {str(e)}")
                
                # Search for general company information
                try:
                    search_results = search_company_info(company_name)
                    if search_results and not isinstance(search_results, str) and "error" not in search_results:
                        company_data["search_results"] = search_results
                        for result in search_results[:3]:  # Limit to top 3 results
                            similar_info.append(f"Info: {result.get('title')} - {result.get('snippet')}")
                            
                            # Try to extract more info from the top result URL
                            if result.get("link") and len(similar_info) < 10:
                                url_info = extract_info_from_url(result.get("link"))
                                if url_info and "error" not in url_info:
                                    similar_info.append(f"Additional Info: {url_info.get('text', '')[:500]}...")
                except Exception as e:
                    logger.error(f"Error searching company info: {str(e)}")
                
                # Get Wikipedia information
                try:
                    wiki_info = get_wikipedia_info(company_name)
                    if wiki_info and "error" not in wiki_info:
                        company_data["wikipedia"] = wiki_info
                        similar_info.append(f"Wikipedia: {wiki_info.get('extract', '')}")
                except Exception as e:
                    logger.error(f"Error getting Wikipedia info: {str(e)}")
                
                # In the generate_response function, there's a syntax error with nested try blocks
                # Let's fix the part where you're storing data in Pinecone
                
                # Store the newly fetched data in Pinecone for future use
                if company_data:
                    try:
                        # Import process_company_data from the correct module
                        from backend.app.data_ingestion import process_company_data
                        
                        # Process and store the company data
                        await process_company_data(company_name, company_data)
                        logger.info(f"Stored new data for {company_name} in Pinecone")
                    except Exception as e:
                        logger.error(f"Error storing company data: {str(e)}")
                
                # If we still don't have information, inform the user
                if not similar_info:
                    return f"I couldn't find specific information about {company_name}. Could you please provide more details or ask about a different company?"
                
                # Combine the similar information into context
                context = "\n\n".join(similar_info)
                
                # Generate a response using the context and query
                prompt = PromptTemplate(
                    template="""
                    You are an AI assistant specialized in company research and financial information.
                    
                    Use the following information to answer the user's question about {company_name}.
                    
                    Context information:
                    {context}
                    
                    User question: {query}
                    
                    Provide a comprehensive but concise answer based on the context information.
                    If the context doesn't contain enough information to fully answer the question,
                    acknowledge this and provide what you can based on the available information.
                    
                    Response:
                    """,
                    input_variables=["company_name", "context", "query"]
                )
                
                chain = LLMChain(llm=llm, prompt=prompt)
                return await chain.arun(company_name=company_name, context=context, query=query)
    
    except Exception as e:
        logger.error(f"Error generating response: {str(e)}")
        return f"I apologize, but I encountered an error while processing your request. Please try again."