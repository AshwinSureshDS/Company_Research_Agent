# backend/test_infrastructure.py
from app.memory.vector_store import init_pinecone, store_in_pinecone, query_pinecone
from app.memory.session import MemoryManager

def test_pinecone_connection():
    print("Testing Pinecone connection...")
    index = init_pinecone()
    print(f"Successfully connected to Pinecone index: {index.describe_index_stats()}")
    return index

def test_memory_manager(index):
    print("\nTesting Memory Manager...")
    memory = MemoryManager(index)
    
    # Test storing user preference
    user_id = "test_user_1"
    pref_id = memory.store_user_preference(user_id, "industry", "Technology")
    print(f"Stored user preference with ID: {pref_id}")
    
    # Test storing conversation
    conv_id = memory.store_conversation(
        user_id, 
        "Tell me about Apple Inc.", 
        "Apple Inc. is a technology company that makes consumer electronics, software, and online services."
    )
    print(f"Stored conversation with ID: {conv_id}")
    
    # Test retrieving preferences
    prefs = memory.get_user_preferences(user_id)
    print(f"\nRetrieved user preferences: {prefs}")
    
    # Test retrieving conversations
    convs = memory.get_conversation_history(user_id)
    print(f"\nRetrieved conversation history: {convs}")

if __name__ == "__main__":
    index = test_pinecone_connection()
    test_memory_manager(index)