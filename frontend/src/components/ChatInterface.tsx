'use client';

import { useState, useRef, useEffect } from 'react';
import { SendIcon, BotIcon, UserIcon, Plus } from './Icons';
import HistorySidebar from './HistorySidebar';
import { chatService } from '../services/chatService';

interface Message {
  role: 'user' | 'assistant';
  content: string;
}

export default function ChatInterface() {
  const [messages, setMessages] = useState<Message[]>([]);
  const [input, setInput] = useState('');
  const [isLoading, setIsLoading] = useState(false);
  const [backendStatus, setBackendStatus] = useState<'connecting' | 'connected' | 'error'>('connecting');
  const messagesEndRef = useRef<HTMLDivElement>(null);
  const inputRef = useRef<HTMLTextAreaElement>(null);
  
  // Chat history state
  const [isSidebarOpen, setIsSidebarOpen] = useState(false);
  const [chatHistories, setChatHistories] = useState<any[]>([]);
  const [currentChatId, setCurrentChatId] = useState<string | null>(null);

  // Initialize chat history
  useEffect(() => {
    const loadChats = async () => {
      try {
        const chats = await chatService.getChats();
        setChatHistories(chats.map(chat => ({
          id: chat.id,
          title: chat.title,
          createdAt: chat.createdAt,
          updatedAt: chat.updatedAt
        })));
        
        // If there are chats, select the most recent one
        if (chats.length > 0) {
          const sortedChats = [...chats].sort((a, b) => 
            new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
          );
          const recentChat = sortedChats[0];
          setCurrentChatId(recentChat.id);
          setMessages(recentChat.messages);
        } else {
          // Create a new chat if none exist
          handleNewChat();
        }
      } catch (error) {
        console.error('Error loading chats:', error);
        handleNewChat();
      }
    };
    
    loadChats();
  }, []);

  // Check backend connection on component mount
  useEffect(() => {
    const checkBackendConnection = async () => {
      try {
        const controller = new AbortController();
        const timeoutId = setTimeout(() => controller.abort(), 5000);
        
        const response = await fetch('http://localhost:8000/', { 
          method: 'GET',
          headers: { 'Content-Type': 'application/json' },
          signal: controller.signal
        });
        
        clearTimeout(timeoutId);
        
        if (response.ok) {
          setBackendStatus('connected');
        } else {
          setBackendStatus('error');
        }
      } catch (error) {
        console.error('Backend connection error:', error);
        setBackendStatus('error');
      }
    };
    
    checkBackendConnection();
  }, []);

  // Scroll to bottom of messages
  useEffect(() => {
    messagesEndRef.current?.scrollIntoView({ behavior: 'smooth' });
  }, [messages]);

  // Auto-resize textarea
  useEffect(() => {
    if (inputRef.current) {
      inputRef.current.style.height = 'auto';
      inputRef.current.style.height = `${inputRef.current.scrollHeight}px`;
    }
  }, [input]);

  // Handle creating a new chat
  const handleNewChat = async () => {
    try {
      const newChat = await chatService.createChat();
      setChatHistories(prev => [
        {
          id: newChat.id,
          title: newChat.title,
          createdAt: newChat.createdAt,
          updatedAt: newChat.updatedAt
        },
        ...prev
      ]);
      setCurrentChatId(newChat.id);
      setMessages([]);
    } catch (error) {
      console.error('Error creating new chat:', error);
    }
  };

  // Handle selecting a chat
  const handleSelectChat = async (chatId: string) => {
    if (chatId === currentChatId) return;
    
    try {
      const chat = await chatService.getChat(chatId);
      if (chat) {
        setCurrentChatId(chat.id);
        setMessages(chat.messages);
      }
    } catch (error) {
      console.error('Error loading chat:', error);
    }
  };

  // Handle deleting a chat
  const handleDeleteChat = async (chatId: string) => {
    try {
      await chatService.deleteChat(chatId);
      setChatHistories(prev => prev.filter(chat => chat.id !== chatId));
      
      // If the current chat was deleted, create a new one or select another
      if (chatId === currentChatId) {
        if (chatHistories.length > 1) {
          const nextChat = chatHistories.find(chat => chat.id !== chatId);
          if (nextChat) {
            handleSelectChat(nextChat.id);
          } else {
            handleNewChat();
          }
        } else {
          handleNewChat();
        }
      }
    } catch (error) {
      console.error('Error deleting chat:', error);
    }
  };

  // Handle renaming a chat
  const handleRenameChat = async (chatId: string, newTitle: string) => {
    try {
      await chatService.updateChatTitle(chatId, newTitle);
      setChatHistories(prev => prev.map(chat => 
        chat.id === chatId 
          ? { ...chat, title: newTitle, updatedAt: new Date().toISOString() }
          : chat
      ));
    } catch (error) {
      console.error('Error renaming chat:', error);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!input.trim() || backendStatus !== 'connected' || !currentChatId) return;

    // Add user message to chat
    const userMessage: Message = { role: 'user', content: input };
    setMessages(prev => [...prev, userMessage]);
    setInput('');
    setIsLoading(true);

    try {
      // Save the user message to the current chat
      await chatService.addMessageToChat(currentChatId, userMessage);
      
      // Update chat history list with potentially new title (first message)
      if (messages.length === 0) {
        const title = input.length > 30 ? input.substring(0, 30) + '...' : input;
        setChatHistories(prev => prev.map(chat => 
          chat.id === currentChatId 
            ? { ...chat, title, updatedAt: new Date().toISOString() }
            : chat
        ));
      }

      // Call the backend API with a timeout
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 30000); // 30 second timeout
      
      const response = await fetch('http://localhost:8000/api/chat/', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          user_id: currentChatId,
          query: userMessage.content,
        }),
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);

      if (!response.ok) {
        throw new Error(`Server responded with status: ${response.status}`);
      }

      const data = await response.json();
      
      // Add assistant message to chat
      const assistantMessage: Message = { role: 'assistant', content: data.response };
      setMessages(prev => [...prev, assistantMessage]);
      
      // Save the assistant message to the current chat
      await chatService.addMessageToChat(currentChatId, assistantMessage);
      
      // Update the chat history list to show this chat was updated
      setChatHistories(prev => {
        const updatedHistories = prev.map(chat => 
          chat.id === currentChatId 
            ? { ...chat, updatedAt: new Date().toISOString() }
            : chat
        );
        // Sort by most recently updated
        return updatedHistories.sort((a, b) => 
          new Date(b.updatedAt).getTime() - new Date(a.updatedAt).getTime()
        );
      });
      
    } catch (error) {
      console.error('Error:', error);
      let errorMessage = 'Sorry, I encountered an error. Please try again later.';
      
      if (error instanceof DOMException && error.name === 'AbortError') {
        errorMessage = 'The request took too long to complete. This might be due to high server load or connection issues.';
      } else if (error instanceof Error) {
        if (error.message.includes('Failed to fetch')) {
          errorMessage = 'Unable to connect to the server. Please check if the backend is running.';
          setBackendStatus('error');
        }
      }
      
      const assistantErrorMessage: Message = { role: 'assistant', content: errorMessage };
      setMessages(prev => [...prev, assistantErrorMessage]);
      
      // Save the error message to the current chat
      await chatService.addMessageToChat(currentChatId, assistantErrorMessage);
    } finally {
      setIsLoading(false);
    }
  };

  const handleKeyDown = (e: React.KeyboardEvent<HTMLTextAreaElement>) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      handleSubmit(e);
    }
  };

  return (
    <div className="flex h-screen bg-gray-50 text-gray-800 font-sans">
      {/* Sidebar */}
      <HistorySidebar 
        isOpen={isSidebarOpen}
        toggleSidebar={() => setIsSidebarOpen(!isSidebarOpen)}
        chatHistories={chatHistories}
        currentChatId={currentChatId}
        onSelectChat={handleSelectChat}
        onNewChat={handleNewChat}
        onDeleteChat={handleDeleteChat}
        onRenameChat={handleRenameChat}
      />
      
      {/* Main content */}
      <div className={`flex flex-col flex-1 transition-all duration-300 ${isSidebarOpen ? 'ml-64' : 'ml-0'}`}>
        {/* Header */}
        <header className="bg-white border-b border-gray-200 py-4 px-6 flex justify-between items-center">
          <div className="flex items-center space-x-2">
            {!isSidebarOpen && (
              <button 
                onClick={() => setIsSidebarOpen(true)}
                className="text-gray-600 hover:text-gray-900 mr-2"
                aria-label="Open sidebar"
              >
                <svg xmlns="http://www.w3.org/2000/svg" width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="2" strokeLinecap="round" strokeLinejoin="round">
                  <line x1="3" y1="12" x2="21" y2="12"></line>
                  <line x1="3" y1="6" x2="21" y2="6"></line>
                  <line x1="3" y1="18" x2="21" y2="18"></line>
                </svg>
              </button>
            )}
            <div className="h-6 w-6 text-blue-600">
              <BotIcon />
            </div>
            <h1 className="text-xl font-semibold text-gray-800">Company Research Assistant</h1>
          </div>
          <div className="flex items-center space-x-4">
            <button
              onClick={handleNewChat}
              className="text-gray-600 hover:text-gray-900 flex items-center"
            >
              <Plus />
              <span className="ml-1">New Chat</span>
            </button>
            <div className="flex items-center">
              <span className="text-sm mr-2 text-gray-600">Backend:</span>
              <span className={`inline-block w-3 h-3 rounded-full ${
                backendStatus === 'connected' ? 'bg-green-500' : 
                backendStatus === 'connecting' ? 'bg-yellow-400 animate-pulse' : 
                'bg-red-500'
              }`}></span>
            </div>
          </div>
        </header>

        {/* Main chat area */}
        <div className="flex-1 overflow-y-auto p-4 md:p-6 space-y-6">
          {backendStatus === 'error' && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
              <strong className="font-medium">Connection Error!</strong>
              <span className="block mt-1"> Unable to connect to the backend server. Please ensure it's running and try again.</span>
            </div>
          )}
          
          {messages.length === 0 ? (
            <div className="flex flex-col items-center justify-center h-full text-center text-gray-500 space-y-4">
              <div className="h-12 w-12 text-blue-600 mb-2">
                <BotIcon />
              </div>
              <h2 className="text-2xl font-semibold text-gray-700">Welcome to Company Research Assistant</h2>
              <p className="max-w-xl text-lg">
                Ask me anything about companies, their financials, news, or stock performance.
              </p>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-3 mt-6 max-w-2xl">
                {[
                  "What are Tesla's latest financial results?",
                  "Compare Apple and Microsoft stock performance",
                  "Tell me about recent news for Amazon",
                  "What is the current stock price of Google?"
                ].map((suggestion, i) => (
                  <button
                    key={i}
                    className="bg-white border border-gray-200 rounded-lg px-4 py-2 text-left hover:bg-gray-50 transition-colors text-gray-700"
                    onClick={() => setInput(suggestion)}
                  >
                    {suggestion}
                  </button>
                ))}
              </div>
            </div>
          ) : (
            <div className="space-y-6 max-w-3xl mx-auto">
              {messages.map((message, index) => (
                <div
                  key={index}
                  className={`flex ${message.role === 'user' ? 'justify-end' : 'justify-start'}`}
                >
                  <div className={`flex max-w-[85%] ${message.role === 'user' ? 'flex-row-reverse' : 'flex-row'}`}>
                    <div className={`flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center ${
                      message.role === 'user' ? 'bg-blue-100 text-blue-600 ml-3' : 'bg-gray-100 text-gray-600 mr-3'
                    }`}>
                      {message.role === 'user' ? <UserIcon /> : <BotIcon />}
                    </div>
                    <div className={`py-3 px-4 rounded-2xl ${
                      message.role === 'user' 
                        ? 'bg-blue-600 text-white' 
                        : 'bg-white border border-gray-200 text-gray-800'
                    }`}>
                      <p className="whitespace-pre-wrap text-sm md:text-base leading-relaxed">{message.content}</p>
                    </div>
                  </div>
                </div>
              ))}
              {isLoading && (
                <div className="flex justify-start">
                  <div className="flex max-w-[85%] flex-row">
                    <div className="flex-shrink-0 h-8 w-8 rounded-full flex items-center justify-center bg-gray-100 text-gray-600 mr-3">
                      <BotIcon />
                    </div>
                    <div className="py-3 px-4 rounded-2xl bg-white border border-gray-200">
                      <div className="flex space-x-2">
                        <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '0ms' }}></div>
                        <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '300ms' }}></div>
                        <div className="h-2 w-2 bg-gray-400 rounded-full animate-bounce" style={{ animationDelay: '600ms' }}></div>
                      </div>
                    </div>
                  </div>
                </div>
              )}
            </div>
          )}
          <div ref={messagesEndRef} />
        </div>

        {/* Input area */}
        <div className="border-t border-gray-200 bg-white p-4">
          <form onSubmit={handleSubmit} className="max-w-3xl mx-auto">
            <div className="relative rounded-lg border border-gray-300 focus-within:border-blue-500 focus-within:ring-1 focus-within:ring-blue-500 bg-white overflow-hidden shadow-sm">
              <textarea
                ref={inputRef}
                value={input}
                onChange={(e) => setInput(e.target.value)}
                onKeyDown={handleKeyDown}
                placeholder={backendStatus === 'connected' ? "Ask about a company..." : "Backend connection error..."}
                className="w-full py-3 px-4 outline-none resize-none max-h-32 text-gray-800"
                rows={1}
                disabled={isLoading || backendStatus !== 'connected'}
              />
              <button
                type="submit"
                className="absolute right-2 bottom-2 p-1.5 rounded-md bg-blue-600 text-white hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-blue-300 disabled:cursor-not-allowed transition-colors"
                disabled={isLoading || !input.trim() || backendStatus !== 'connected'}
              >
                <SendIcon />
              </button>
            </div>
            <p className="text-xs text-gray-500 mt-2 text-center">
              Press Enter to send, Shift+Enter for a new line
            </p>
          </form>
        </div>
      </div>
    </div>
  );