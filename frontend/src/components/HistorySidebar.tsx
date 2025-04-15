'use client';

import { useState, useEffect } from 'react';
import { ChevronLeft, ChevronRight, Plus, MessageSquare, Edit2, Trash2 } from 'lucide-react';

export interface ChatHistory {
  id: string;
  title: string;
  createdAt: string;
  updatedAt: string;
}

interface HistorySidebarProps {
  isOpen: boolean;
  toggleSidebar: () => void;
  chatHistories: ChatHistory[];
  currentChatId: string | null;
  onSelectChat: (chatId: string) => void;
  onNewChat: () => void;
  onDeleteChat: (chatId: string) => void;
  onRenameChat: (chatId: string, newTitle: string) => void;
}

export default function HistorySidebar({
  isOpen,
  toggleSidebar,
  chatHistories,
  currentChatId,
  onSelectChat,
  onNewChat,
  onDeleteChat,
  onRenameChat
}: HistorySidebarProps) {
  const [editingChatId, setEditingChatId] = useState<string | null>(null);
  const [editTitle, setEditTitle] = useState('');

  const handleRenameClick = (chatId: string, currentTitle: string) => {
    setEditingChatId(chatId);
    setEditTitle(currentTitle);
  };

  const handleRenameSubmit = (chatId: string) => {
    if (editTitle.trim()) {
      onRenameChat(chatId, editTitle);
    }
    setEditingChatId(null);
  };

  const formatDate = (dateString: string) => {
    const date = new Date(dateString);
    return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric' });
  };

  return (
    <div className={`fixed top-0 left-0 h-full bg-gray-900 text-white transition-all duration-300 z-10 flex ${isOpen ? 'w-64' : 'w-0'}`}>
      <div className={`flex flex-col w-full overflow-hidden ${isOpen ? 'opacity-100' : 'opacity-0'}`}>
        <div className="p-4 border-b border-gray-700 flex justify-between items-center">
          <h2 className="font-semibold">Chat History</h2>
          <button 
            onClick={toggleSidebar}
            className="text-gray-400 hover:text-white"
            aria-label="Close sidebar"
          >
            <ChevronLeft size={20} />
          </button>
        </div>
        
        <button 
          onClick={onNewChat}
          className="mx-3 mt-3 mb-1 py-2 px-3 rounded-md bg-blue-600 hover:bg-blue-700 text-white flex items-center justify-center transition-colors"
        >
          <Plus size={16} className="mr-2" />
          New Chat
        </button>
        
        <div className="flex-1 overflow-y-auto py-2">
          {chatHistories.length === 0 ? (
            <div className="text-gray-400 text-center p-4 text-sm">
              No chat history yet
            </div>
          ) : (
            <ul className="space-y-1 px-2">
              {chatHistories.map((chat) => (
                <li key={chat.id}>
                  {editingChatId === chat.id ? (
                    <div className="flex items-center p-2 rounded-md bg-gray-800">
                      <input
                        type="text"
                        value={editTitle}
                        onChange={(e) => setEditTitle(e.target.value)}
                        onKeyDown={(e) => {
                          if (e.key === 'Enter') handleRenameSubmit(chat.id);
                          if (e.key === 'Escape') setEditingChatId(null);
                        }}
                        className="flex-1 bg-gray-700 text-white px-2 py-1 rounded text-sm border border-gray-600 focus:outline-none focus:border-blue-500"
                        autoFocus
                      />
                      <button 
                        onClick={() => handleRenameSubmit(chat.id)}
                        className="ml-2 text-gray-400 hover:text-white"
                      >
                        <Edit2 size={14} />
                      </button>
                    </div>
                  ) : (
                    <div 
                      className={`flex items-center justify-between p-2 rounded-md cursor-pointer hover:bg-gray-800 ${
                        currentChatId === chat.id ? 'bg-gray-800' : ''
                      }`}
                    >
                      <div 
                        className="flex items-center flex-1 overflow-hidden"
                        onClick={() => onSelectChat(chat.id)}
                      >
                        <MessageSquare size={16} className="mr-2 flex-shrink-0" />
                        <div className="truncate flex-1">
                          <span className="block truncate">{chat.title}</span>
                          <span className="text-xs text-gray-400">{formatDate(chat.updatedAt)}</span>
                        </div>
                      </div>
                      <div className="flex space-x-1 opacity-0 group-hover:opacity-100 transition-opacity">
                        <button 
                          onClick={(e) => {
                            e.stopPropagation();
                            handleRenameClick(chat.id, chat.title);
                          }}
                          className="text-gray-400 hover:text-white p-1"
                          aria-label="Rename chat"
                        >
                          <Edit2 size={14} />
                        </button>
                        <button 
                          onClick={(e) => {
                            e.stopPropagation();
                            onDeleteChat(chat.id);
                          }}
                          className="text-gray-400 hover:text-red-400 p-1"
                          aria-label="Delete chat"
                        >
                          <Trash2 size={14} />
                        </button>
                      </div>
                    </div>
                  )}
                </li>
              ))}
            </ul>
          )}
        </div>
      </div>
      
      {!isOpen && (
        <button 
          onClick={toggleSidebar}
          className="absolute top-4 left-4 bg-gray-800 text-white p-2 rounded-full hover:bg-gray-700 transition-colors"
          aria-label="Open sidebar"
        >
          <ChevronRight size={20} />
        </button>
      )}
    </div>
  );
}