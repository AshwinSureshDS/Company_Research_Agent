const API_BASE_URL = 'http://localhost:8000';

export async function fetchStockPrice(symbol: string) {
  const response = await fetch(`${API_BASE_URL}/api/stock/${symbol}`);
  if (!response.ok) {
    throw new Error('Failed to fetch stock price');
  }
  return response.json();
}

export async function compareStocks(symbols: string) {
  const response = await fetch(`${API_BASE_URL}/api/compare-stocks/?symbols=${symbols}`);
  if (!response.ok) {
    throw new Error('Failed to compare stocks');
  }
  return response.json();
}

export async function sendChatMessage(userId: string, query: string) {
  const response = await fetch(`${API_BASE_URL}/api/chat/`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({ user_id: userId, query }),
  });
  
  if (!response.ok) {
    throw new Error('Failed to get response');
  }
  
  return response.json();
}