import { v4 as uuidv4 } from 'uuid';

export interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export interface Chat {
  id: string;
  title: string;
  messages: Message[];
  createdAt: string;
  updatedAt: string;
}

// Local storage implementation (fallback)
const LOCAL_STORAGE_KEY = 'company_research_chats';

export const chatService = {
  // Create a new chat
  async createChat(): Promise<Chat> {
    const newChat: Chat = {
      id: uuidv4(),
      title: 'New Conversation',
      messages: [],
      createdAt: new Date().toISOString(),
      updatedAt: new Date().toISOString()
    };
    
    try {
      // Try to save to backend first
      await this.saveChat(newChat);
      return newChat;
    } catch (error) {
      console.error('Error creating chat:', error);
      // Fallback to local storage
      this.saveToLocalStorage(newChat);
      return newChat;
    }
  },
  
  // Get all chats
  async getChats(): Promise<Chat[]> {
    try {
      // Try to fetch from backend
      const response = await fetch('http://localhost:8000/api/chats/', {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch chats');
      }
      
      const data = await response.json();
      return data.chats;
    } catch (error) {
      console.error('Error fetching chats, using local storage:', error);
      // Fallback to local storage
      return this.getFromLocalStorage();
    }
  },
  
  // Get a specific chat
  async getChat(chatId: string): Promise<Chat | null> {
    try {
      // Try to fetch from backend
      const response = await fetch(`http://localhost:8000/api/chats/${chatId}`, {
        method: 'GET',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to fetch chat');
      }
      
      const data = await response.json();
      return data.chat;
    } catch (error) {
      console.error('Error fetching chat, using local storage:', error);
      // Fallback to local storage
      const chats = this.getFromLocalStorage();
      return chats.find(chat => chat.id === chatId) || null;
    }
  },
  
  // Save a chat
  async saveChat(chat: Chat): Promise<void> {
    chat.updatedAt = new Date().toISOString();
    
    try {
      // Try to save to backend
      const response = await fetch(`http://localhost:8000/api/chats/${chat.id}`, {
        method: 'PUT',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ chat })
      });
      
      if (!response.ok) {
        throw new Error('Failed to save chat');
      }
    } catch (error) {
      console.error('Error saving chat, using local storage:', error);
      // Fallback to local storage
      this.saveToLocalStorage(chat);
    }
  },
  
  // Delete a chat
  async deleteChat(chatId: string): Promise<void> {
    try {
      // Try to delete from backend
      const response = await fetch(`http://localhost:8000/api/chats/${chatId}`, {
        method: 'DELETE',
        headers: {
          'Content-Type': 'application/json',
        }
      });
      
      if (!response.ok) {
        throw new Error('Failed to delete chat');
      }
    } catch (error) {
      console.error('Error deleting chat, using local storage:', error);
      // Fallback to local storage
      const chats = this.getFromLocalStorage();
      const updatedChats = chats.filter(chat => chat.id !== chatId);
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(updatedChats));
    }
  },
  
  // Update chat title
  async updateChatTitle(chatId: string, newTitle: string): Promise<void> {
    try {
      // Try to update on backend
      const response = await fetch(`http://localhost:8000/api/chats/${chatId}/title`, {
        method: 'PATCH',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ title: newTitle })
      });
      
      if (!response.ok) {
        throw new Error('Failed to update chat title');
      }
    } catch (error) {
      console.error('Error updating chat title, using local storage:', error);
      // Fallback to local storage
      const chats = this.getFromLocalStorage();
      const updatedChats = chats.map(chat => {
        if (chat.id === chatId) {
          return { ...chat, title: newTitle, updatedAt: new Date().toISOString() };
        }
        return chat;
      });
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(updatedChats));
    }
  },
  
  // Add message to chat
  async addMessageToChat(chatId: string, message: Message): Promise<void> {
    try {
      // Try to add message on backend
      const response = await fetch(`http://localhost:8000/api/chats/${chatId}/messages`, {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({ message })
      });
      
      if (!response.ok) {
        throw new Error('Failed to add message to chat');
      }
    } catch (error) {
      console.error('Error adding message to chat, using local storage:', error);
      // Fallback to local storage
      const chats = this.getFromLocalStorage();
      const updatedChats = chats.map(chat => {
        if (chat.id === chatId) {
          // Update title if it's the first user message and title is default
          let title = chat.title;
          if (chat.messages.length === 0 && message.role === 'user' && title === 'New Conversation') {
            title = message.content.length > 30 
              ? message.content.substring(0, 30) + '...' 
              : message.content;
          }
          
          return { 
            ...chat, 
            messages: [...chat.messages, message],
            title,
            updatedAt: new Date().toISOString()
          };
        }
        return chat;
      });
      localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(updatedChats));
    }
  },
  
  // Local storage helpers
  getFromLocalStorage(): Chat[] {
    const chatsJson = localStorage.getItem(LOCAL_STORAGE_KEY);
    if (!chatsJson) return [];
    try {
      return JSON.parse(chatsJson);
    } catch (e) {
      console.error('Error parsing chats from localStorage:', e);
      return [];
    }
  },
  
  saveToLocalStorage(chat: Chat): void {
    const chats = this.getFromLocalStorage();
    const existingChatIndex = chats.findIndex(c => c.id === chat.id);
    
    if (existingChatIndex >= 0) {
      chats[existingChatIndex] = chat;
    } else {
      chats.push(chat);
    }
    
    localStorage.setItem(LOCAL_STORAGE_KEY, JSON.stringify(chats));
  }
};