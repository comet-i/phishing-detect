// frontend/src/App.jsx
import React, { useState } from 'react';

// Mock API call function (Replace with actual fetch/axios in production)
const checkUrlApi = async (url) => {
  // Simulating API delay
  await new Promise(resolve => setTimeout(resolve, 800)); 
  return {
    url: url,
    score: (Math.random() * 5).toFixed(1), // Mock score
    risk_level: "SUSPICIOUS", // Mock level
    explanation: "The URL contains an unusually high number of hyphens and has a highly random domain name."
  };
};

export default function App() {
  const [url, setUrl] = useState('');
  const [result, setResult] = useState(null);
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url) return;
    setLoading(true);
    try {
      const data = await checkUrlApi(url);
      setResult(data);
    } catch (error) {
      console.error(error);
    } finally {
      setLoading(false);
    }
  };

  const getScoreColor = (score) => {
    if (score <= 1) return 'bg-green-100 text-green-800 border-green-200';
    if (score <= 3) return 'bg-amber-100 text-amber-800 border-amber-200';
    return 'bg-red-100 text-red-800 border-red-200';
  };

  return (
    // Layer 1: Client Layer - Light Theme Base
    <div className="min-h-screen bg-gray-50 text-gray-800 flex flex-col items-center py-12 px-4">
      
      {/* Header */}
      <header className="mb-10 text-center">
        <h1 className="text-3xl font-bold text-gray-900">Phishing URL Scanner</h1>
        <p className="text-gray-500 mt-2">Analyze URLs for malicious intent using Cloud ML</p>
      </header>

      {/* Main Card */}
      <main className="w-full max-w-2xl bg-white rounded-xl shadow-sm border border-gray-100 p-8">
        
        {/* Input Form */}
        <form onSubmit={handleSubmit} className="space-y-4">
          <label htmlFor="url-input" className="block text-sm font-medium text-gray-700">
            Enter URL to scan
          </label>
          <div className="flex gap-3">
            <input
              id="url-input"
              type="text"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com"
              className="flex-1 px-4 py-2.5 border border-gray-200 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500 outline-none transition bg-gray-50 text-gray-900 placeholder-gray-400"
            />
            <button
              type="submit"
              disabled={loading}
              className="px-6 py-2.5 bg-blue-600 text-white font-medium rounded-lg hover:bg-blue-700 focus:ring-4 focus:ring-blue-200 transition disabled:opacity-50 disabled:cursor-not-allowed"
            >
              {loading ? 'Scanning...' : 'Scan'}
            </button>
          </div>
        </form>

        {/* Results Section */}
        {result && (
          <div className="mt-8 pt-6 border-t border-gray-100 animate-fade-in">
            <div className="flex items-center justify-between mb-4">
              <h2 className="text-lg font-semibold text-gray-900">Analysis Result</h2>
              <span className={`px-3 py-1 text-sm font-bold rounded-full border ${getScoreColor(result.score)}`}>
                Score: {result.score}/5
              </span>
            </div>
            
            <div className="bg-gray-50 p-4 rounded-lg border border-gray-100">
              <p className="text-sm font-medium text-gray-500 mb-1">Risk Level</p>
              <p className="text-lg font-bold text-gray-800 mb-3">{result.risk_level}</p>
              
              <p className="text-sm font-medium text-gray-500 mb-1">Explanation</p>
              <p className="text-gray-700 leading-relaxed">{result.explanation}</p>
            </div>
          </div>
        )}
      </main>

      {/* Footer */}
      <footer className="mt-12 text-xs text-gray-400">
        Powered by Random Forest Classifier (Cloud Hosted)
      </footer>
    </div>
  );
}
