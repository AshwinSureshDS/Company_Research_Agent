// API base URL configuration
const API_BASE_URL = process.env.NEXT_PUBLIC_API_URL || 'http://localhost:8000';

// API endpoints
export const API = {
  // Chat endpoints
  chat: `${API_BASE_URL}/api/chat/`,
  chats: `${API_BASE_URL}/api/chats/`,
  chatById: (id) => `${API_BASE_URL}/api/chats/${id}`,
  chatTitle: (id) => `${API_BASE_URL}/api/chats/${id}/title`,
  chatMessages: (id) => `${API_BASE_URL}/api/chats/${id}/messages`,
  
  // Company data endpoints
  ingestCompany: `${API_BASE_URL}/api/ingest-company/`,
  stockPrice: (symbol) => `${API_BASE_URL}/api/stock/${symbol}`,
  compareStocks: (symbols) => `${API_BASE_URL}/api/compare-stocks/?symbols=${symbols}`,
  
  // Health check
  health: `${API_BASE_URL}/`,
};

// Generic fetch function with error handling
export const fetchAPI = async (url, options = {}) => {
  try {
    const response = await fetch(url, {
      ...options,
      headers: {
        'Content-Type': 'application/json',
        ...options.headers,
      },
    });
    
    if (!response.ok) {
      const errorData = await response.json().catch(() => ({}));
      throw new Error(errorData.detail || `API error: ${response.status}`);
    }
    
    return await response.json();
  } catch (error) {
    console.error(`API request failed: ${url}`, error);
    throw error;
  }
};

// API functions
export const apiService = {
  // Chat functions
  sendMessage: async (query, userId) => {
    return fetchAPI(API.chat, {
      method: 'POST',
      body: JSON.stringify({ query, user_id: userId }),
    });
  },
  
  getChats: async () => {
    return fetchAPI(API.chats);
  },
  
  getChat: async (chatId) => {
    return fetchAPI(API.chatById(chatId));
  },
  
  createChat: async (chat) => {
    return fetchAPI(API.chats, {
      method: 'PUT',
      body: JSON.stringify({ chat }),
    });
  },
  
  saveChat: async (chatId, chat) => {
    return fetchAPI(API.chatById(chatId), {
      method: 'PUT',
      body: JSON.stringify({ chat }),
    });
  },
  
  deleteChat: async (chatId) => {
    return fetchAPI(API.chatById(chatId), {
      method: 'DELETE',
    });
  },
  
  updateChatTitle: async (chatId, title) => {
    return fetchAPI(API.chatTitle(chatId), {
      method: 'PATCH',
      body: JSON.stringify({ title }),
    });
  },
  
  addMessageToChat: async (chatId, message) => {
    return fetchAPI(API.chatMessages(chatId), {
      method: 'POST',
      body: JSON.stringify({ message }),
    });
  },
  
  // Company data functions
  ingestCompanyData: async (companyName, companySymbol) => {
    return fetchAPI(API.ingestCompany, {
      method: 'POST',
      body: JSON.stringify({ company_name: companyName, company_symbol: companySymbol }),
    });
  },
  
  getStockPrice: async (symbol) => {
    return fetchAPI(API.stockPrice(symbol));
  },
  
  compareStocks: async (symbols) => {
    return fetchAPI(API.compareStocks(symbols));
  },
  
  // Health check
  checkHealth: async () => {
    return fetchAPI(API.health);
  },
};

export default apiService;