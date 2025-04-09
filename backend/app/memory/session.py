# backend/app/memory/session.py
import uuid
import json
import time
from .vector_store import store_in_pinecone, query_pinecone

class MemoryManager:
    def __init__(self, pinecone_index):
        self.index = pinecone_index
        self.session_id = str(uuid.uuid4())
    
    def store_user_preference(self, user_id, preference_type, preference_value):
        """Store user preferences like industries of interest, companies researched."""
        id = f"pref_{user_id}_{preference_type}_{int(time.time())}"
        text = f"User {user_id} is interested in {preference_type}: {preference_value}"
        metadata = {
            "type": "preference",
            "preference_type": preference_type,
            "preference_value": preference_value,
            "user_id": user_id,
            "timestamp": time.time()
        }
        return store_in_pinecone(self.index, id, text, metadata)
    
    def store_conversation(self, user_id, query, response):
        """Store conversation history."""
        id = f"conv_{user_id}_{int(time.time())}"
        text = f"User Query: {query}\nAI Response: {response}"
        metadata = {
            "type": "conversation",
            "user_id": user_id,
            "query": query,
            "timestamp": time.time(),
            "session_id": self.session_id
        }
        return store_in_pinecone(self.index, id, text, metadata)
    
    def store_company_research(self, user_id, company_name, research_data):
        """Store information about companies researched."""
        id = f"company_{user_id}_{company_name}_{int(time.time())}"
        text = f"Research about {company_name}: {json.dumps(research_data)}"
        metadata = {
            "type": "company_research",
            "user_id": user_id,
            "company_name": company_name,
            "timestamp": time.time()
        }
        return store_in_pinecone(self.index, id, text, metadata)
    
    def get_user_preferences(self, user_id, preference_type=None, top_k=5):
        """Retrieve user preferences."""
        filter_dict = {"type": "preference", "user_id": user_id}
        if preference_type:
            filter_dict["preference_type"] = preference_type
        
        # Query for similar preferences
        results = query_pinecone(
            self.index,
            f"User {user_id} preferences",
            top_k=top_k,
            filter=filter_dict
        )
        
        return results
    
    def get_conversation_history(self, user_id, query=None, top_k=10):
        """Retrieve conversation history relevant to the current query."""
        filter_dict = {"type": "conversation", "user_id": user_id}
        
        # If query is provided, use semantic search, otherwise just get recent conversations
        if query:
            results = query_pinecone(
                self.index,
                query,
                top_k=top_k,
                filter=filter_dict
            )
        else:
            # This is a simplified approach - in a real implementation, 
            # you might want to sort by timestamp in your application code
            results = query_pinecone(
                self.index,
                f"Recent conversations with user {user_id}",
                top_k=top_k,
                filter=filter_dict
            )
        
        return results
    
    def get_researched_companies(self, user_id, top_k=10):
        """Retrieve companies the user has researched."""
        filter_dict = {"type": "company_research", "user_id": user_id}
        
        results = query_pinecone(
            self.index,
            f"Companies researched by user {user_id}",
            top_k=top_k,
            filter=filter_dict
        )
        
        return results