# backend/app/__init__.py
from .memory.vector_store import init_pinecone
from .memory.session import MemoryManager

# Initialize Pinecone
pinecone_index = init_pinecone()

# Create a memory manager instance
memory_manager = MemoryManager(pinecone_index)