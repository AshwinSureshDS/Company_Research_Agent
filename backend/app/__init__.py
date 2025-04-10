# backend/app/__init__.py
# First, create the memory_manager module
from .memory import vector_store
memory_manager = vector_store

# Then import other modules that depend on memory_manager
from .session import (
    ChatSession, 
    create_session, 
    get_session, 
    delete_session, 
    generate_chat_response,
    get_session_history,
    list_sessions
)
from .agent import generate_response, research_agent

# Version information
__version__ = "0.1.0"