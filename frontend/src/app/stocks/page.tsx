'use client';

import { useState } from 'react';
import { compareStocks } from '@/utils/api';

export default function StocksPage() {
  const [symbols, setSymbols] = useState('');
  const [result, setResult] = useState<any>(null);
  const [isLoading, setIsLoading] = useState(false);
  const [error, setError] = useState('');

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    if (!symbols.trim()) return;

    setIsLoading(true);
    setError('');
    
    try {
      const data = await compareStocks(symbols);
      setResult(data);
    } catch (err) {
      setError('Failed to fetch stock data. Please check the symbols and try again.');
      console.error(err);
    } finally {
      setIsLoading(false);
    }
  };

  return (
    <div className="max-w-4xl mx-auto p-4">
      <h1 className="text-2xl font-bold mb-4">Stock Comparison</h1>
      
      <form onSubmit={handleSubmit} className="mb-6">
        <div className="flex flex-col space-y-2">
          <label htmlFor="symbols" className="font-medium">
            Enter stock symbols (comma-separated)
          </label>
          <div className="flex">
            <input
              type="text"
              id="symbols"
              value={symbols}
              onChange={(e) => setSymbols(e.target.value)}
              placeholder="e.g., AAPL,MSFT,GOOGL"
              className="flex-1 p-2 border rounded-l-lg focus:outline-none focus:ring-2 focus:ring-blue-500"
              disabled={isLoading}
            />
            <button
              type="submit"
              className="bg-blue-600 text-white px-4 py-2 rounded-r-lg hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-blue-500 disabled:bg-blue-300"
              disabled={isLoading || !symbols.trim()}
            >
              Compare
            </button>
          </div>
        </div>
      </form>

      {isLoading && <p className="text-center animate-pulse">Loading...</p>}
      
      {error && <p className="text-red-500">{error}</p>}
      
      {result && (
        <div className="border rounded-lg p-4">
          <h2 className="text-xl font-semibold mb-4">Comparison Results</h2>
          
          {result.summary && (
            <div className="mb-4 p-3 bg-gray-50 rounded">
              <h3 className="font-medium mb-2">Summary</h3>
              <p>{result.summary}</p>
            </div>
          )}
          
          {result.prices && Object.keys(result.prices).length > 0 && (
            <div className="overflow-x-auto">
              <table className="min-w-full divide-y divide-gray-200">
                <thead className="bg-gray-50">
                  <tr>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Symbol
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Price
                    </th>
                    <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                      Change
                    </th>
                  </tr>
                </thead>
                <tbody className="bg-white divide-y divide-gray-200">
                  {Object.entries(result.prices).map(([symbol, price]: [string, any]) => (
                    <tr key={symbol}>
                      <td className="px-6 py-4 whitespace-nowrap font-medium">{symbol}</td>
                      <td className="px-6 py-4 whitespace-nowrap">${price}</td>
                      <td className="px-6 py-4 whitespace-nowrap">
                        {result.changes[symbol]}
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          )}
        </div>
      )}
    </div>
  );
}