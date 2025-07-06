import { useState, useEffect } from 'react';

export default function BackendStatus() {
  const [status, setStatus] = useState<'checking' | 'online' | 'offline'>('checking');
  const [lastChecked, setLastChecked] = useState<Date | null>(null);

  const checkBackend = async () => {
    try {
      setStatus('checking');
      const controller = new AbortController();
      const timeoutId = setTimeout(() => controller.abort(), 5000);
      
      const response = await fetch('http://localhost:8000/', {
        signal: controller.signal
      });
      
      clearTimeout(timeoutId);
      setStatus(response.ok ? 'online' : 'offline');
    } catch (error) {
      setStatus('offline');
    }
    
    setLastChecked(new Date());
  };

  useEffect(() => {
    checkBackend();
    
    // Check status every 30 seconds
    const interval = setInterval(checkBackend, 30000);
    
    return () => clearInterval(interval);
  }, []);

  return (
    <div className="fixed bottom-4 right-4 bg-white shadow-lg rounded-lg p-3 z-50">
      <div className="flex items-center space-x-2">
        <div 
          className={`w-3 h-3 rounded-full ${
            status === 'online' ? 'bg-green-500' : 
            status === 'checking' ? 'bg-yellow-500 animate-pulse' : 
            'bg-red-500'
          }`}
        />
        <span className="text-sm font-medium">
          Backend: {status === 'online' ? 'Connected' : status === 'checking' ? 'Checking...' : 'Disconnected'}
        </span>
      </div>
      {lastChecked && (
        <div className="text-xs text-gray-500 mt-1">
          Last checked: {lastChecked.toLocaleTimeString()}
        </div>
      )}
      <button 
        onClick={checkBackend}
        className="mt-2 text-xs text-blue-600 hover:text-blue-800"
      >
        Check now
      </button>
    </div>
  );
}