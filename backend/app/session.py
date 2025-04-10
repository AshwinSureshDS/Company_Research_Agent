# backend/app/session.py
import uuid
from datetime import datetime
import google.generativeai as genai
from .config import GEMINI_API_KEY
from . import memory_manager

# Configure Gemini
genai.configure(api_key=GEMINI_API_KEY)

# Initialize the chat model
chat_model = genai.GenerativeModel('gemini-2.0-flash')

# Add safety settings for the model
safety_settings = [
    {
        "category": "HARM_CATEGORY_HARASSMENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_HATE_SPEECH",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_SEXUALLY_EXPLICIT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    },
    {
        "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
        "threshold": "BLOCK_MEDIUM_AND_ABOVE"
    }
]

class ChatSession:
    def __init__(self, user_id=None, session_id=None):
        self.user_id = user_id or str(uuid.uuid4())
        self.session_id = session_id or str(uuid.uuid4())
        self.messages = []
        self.created_at = datetime.now().isoformat()
        self.last_updated = self.created_at
    
    def add_message(self, role, content):
        """Add a message to the session history."""
        message = {
            "role": role,
            "content": content,
            "timestamp": datetime.now().isoformat()
        }
        self.messages.append(message)
        self.last_updated = message["timestamp"]
        return message
    
    def get_messages(self, limit=None):
        """Get the message history, optionally limited to the most recent messages."""
        if limit:
            return self.messages[-limit:]
        return self.messages
    
    def to_dict(self):
        """Convert session to dictionary for storage."""
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "messages": self.messages,
            "created_at": self.created_at,
            "last_updated": self.last_updated
        }
    
    @classmethod
    def from_dict(cls, data):
        """Create a session from dictionary data."""
        session = cls(user_id=data.get("user_id"), session_id=data.get("session_id"))
        session.messages = data.get("messages", [])
        session.created_at = data.get("created_at", datetime.now().isoformat())
        session.last_updated = data.get("last_updated", session.created_at)
        return session

# Session storage - in a production app, this would be a database
_sessions = {}

def get_session(session_id):
    """Get a session by ID, or create a new one if it doesn't exist."""
    if session_id in _sessions:
        return _sessions[session_id]
    return None

def create_session(user_id=None):
    """Create a new chat session."""
    session = ChatSession(user_id=user_id)
    _sessions[session.session_id] = session
    return session

def delete_session(session_id):
    """Delete a session by ID."""
    if session_id in _sessions:
        del _sessions[session_id]
        return True
    return False

async def generate_chat_response(session_id, message_content, user_id=None):
    """Generate a response using the chat model and update the session."""
    # Get or create session
    session = get_session(session_id)
    if not session:
        session = create_session(user_id)
        _sessions[session.session_id] = session
    
    # Add user message to session
    session.add_message("user", message_content)
    
    try:
        # Format messages for the model
        formatted_messages = []
        for msg in session.get_messages():
            # Ensure proper role mapping for Gemini API
            if msg["role"] == "user":
                role = "user"
            elif msg["role"] == "assistant":
                role = "model"
            else:
                continue  # Skip system messages or other roles
                
            formatted_messages.append({"role": role, "parts": [msg["content"]]})
        
        # Generate response with safety settings
        response = chat_model.generate_content(
            formatted_messages,
            safety_settings=safety_settings,
            generation_config={"temperature": 0.7, "top_p": 0.95, "top_k": 40}
        )
        response_text = response.text
        
        # Add assistant message to session
        session.add_message("assistant", response_text)
        
        # Store in memory for future context
        if user_id:
            memory_manager.store_conversation(
                user_id, 
                message_content, 
                response_text
            )
        
        return {
            "session_id": session.session_id,
            "response": response_text,
            "messages": session.get_messages()
        }
    except Exception as e:
        error_message = f"Error generating response: {str(e)}"
        print(error_message)
        
        # Add error message to session
        session.add_message("system", error_message)
        
        return {
            "session_id": session.session_id,
            "response": error_message,
            "messages": session.get_messages(),
            "error": True
        }

def get_session_history(session_id, limit=None):
    """Get the message history for a session."""
    session = get_session(session_id)
    if not session:
        return []
    return session.get_messages(limit)

def list_sessions(user_id=None):
    """List all sessions, optionally filtered by user ID."""
    if user_id:
        return [s.to_dict() for s in _sessions.values() if s.user_id == user_id]
    return [s.to_dict() for s in _sessions.values()]