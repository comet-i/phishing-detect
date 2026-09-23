import React, { useState } from 'react';

const checkUrlApi = async (url) => {
  const response = await fetch('/api/v1/check-url', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ url }),
  });
  if (!response.ok) {
    const error = await response.json().catch(() => ({}));
    throw new Error(error.detail || 'Unable to analyze URL');
  }
  return response.json();
};

export default function App() {
  const [url, setUrl] = useState('');
  const [result, setResult] = useState(null);
  const [error, setError] = useState('');
  const [loading, setLoading] = useState(false);

  const handleSubmit = async (e) => {
    e.preventDefault();
    if (!url.trim()) return;
    setLoading(true);
    setError('');
    try {
      setResult(await checkUrlApi(url.trim()));
    } catch (err) {
      setResult(null);
      setError(err.message);
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
    <div className="min-h-screen bg-gray-50 text-gray-800 flex flex-col items-center py-12 px-4">
      <header className="mb-10 text-center">
        <h1 className="text-3xl font-bold text-gray-900">Phishing URL Scanner</h1>
        <p className="text-gray-500 mt-2">Analyze URLs for malicious intent using Cloud ML</p>
      </header>
      <main className="w-full max-w-2xl bg-white rounded-xl shadow-sm border border-gray-100 p-8">
        <form onSubmit={handleSubmit} className="space-y-4">
          <label htmlFor="url-input" className="block text-sm font-medium text-gray-700">Enter URL to scan</label>
          <div className="flex gap-3">
            <input id="url-input" type="text" value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://example.com" className="flex-1 px-4 py-2.5 border border-gray-200 rounded-lg bg-gray-50 text-gray-900" />
            <button type="submit" disabled={loading} className="px-6 py-2.5 bg-blue-600 text-white font-medium rounded-lg disabled:opacity-50">{loading ? 'Scanning...' : 'Scan'}</button>
          </div>
        </form>
        {error && <p className="mt-4 text-red-600" role="alert">{error}</p>}
        {result && <div className="mt-8 pt-6 border-t border-gray-100">
          <div className="flex items-center justify-between mb-4"><h2 className="text-lg font-semibold text-gray-900">Analysis Result</h2><span className={`px-3 py-1 text-sm font-bold rounded-full border ${getScoreColor(result.score)}`}>Score: {result.score}/5</span></div>
          <div className="bg-gray-50 p-4 rounded-lg border border-gray-100"><p className="text-sm font-medium text-gray-500 mb-1">Risk Level</p><p className="text-lg font-bold text-gray-800 mb-3">{result.risk_level}</p><p className="text-sm font-medium text-gray-500 mb-1">Explanation</p><p className="text-gray-700 leading-relaxed">{result.explanation}</p></div>
        </div>}
      </main>
      <footer className="mt-12 text-xs text-gray-400">Powered by Random Forest Classifier (Cloud Hosted)</footer>
    </div>
  );
}
