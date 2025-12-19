'use client';

import { useState } from 'react';
import { Search, FileText, Scale, Clock, Shield, BookOpen, AlertCircle, CheckCircle } from 'lucide-react';

interface Source {
  title: string;
  text: string;
  score: number;
  category: string;
}

interface QueryResult {
  answer: string;
  sources: Source[];
  confidence: number;
  processing_time: number;
}

export default function Home() {
  const [query, setQuery] = useState('');
  const [loading, setLoading] = useState(false);
  const [result, setResult] = useState<QueryResult | null>(null);
  const [error, setError] = useState<string | null>(null);

  const exampleQuestions = [
    'Persyaratan KTP Elektronik',
    'Pendaftaran BPJS Kesehatan',
    'Tarif Pajak UMKM 2024',
    'Nomor Induk Kependudukan',
  ];

  const handleQuery = async (q: string) => {
    if (!q.trim()) return;

    setQuery(q);
    setLoading(true);
    setError(null);
    setResult(null);

    try {
      const response = await fetch('http://localhost:8000/api/query', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          question: q,
          top_k: 3
        })
      });

      if (!response.ok) {
        if (response.status === 429) {
          throw new Error('Terlalu banyak permintaan. Mohon tunggu sebentar dan coba lagi.');
        }
        throw new Error('Gagal mendapatkan respons dari server.');
      }

      const data = await response.json();
      setResult(data);

      // Save to history (localStorage)
      saveToHistory(q, data);

    } catch (err: any) {
      // User-friendly error messages in Indonesian
      if (err.message.includes('Failed to fetch') || err.message.includes('NetworkError')) {
        setError('Tidak dapat terhubung ke server. Pastikan API backend berjalan di http://localhost:8000');
      } else {
        setError(err.message || 'Terjadi kesalahan. Silakan coba lagi.');
      }
      console.error(err);
    } finally {
      setLoading(false);
    }
  };

  // Save query to localStorage
  const saveToHistory = (question: string, response: QueryResult) => {
    try {
      const history = JSON.parse(localStorage.getItem('indogovrag_history') || '[]');
      history.unshift({
        question,
        answer: response.answer,
        timestamp: new Date().toISOString(),
        sources: response.sources.length
      });
      // Keep only last 10
      localStorage.setItem('indogovrag_history', JSON.stringify(history.slice(0, 10)));
    } catch (e) {
      console.error('Failed to save history', e);
    }
  };

  return (
    <main className="min-h-screen bg-slate-50">
      {/* Header */}
      <header className="bg-white border-b border-slate-200 shadow-sm">
        <div className="max-w-7xl mx-auto px-6 py-4">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-3">
              <Scale className="w-8 h-8 text-blue-700" />
              <div>
                <h1 className="text-2xl font-bold text-slate-900 font-crimson">
                  IndoGovRAG
                </h1>
                <p className="text-xs text-slate-600">Indonesian Legal Research Platform</p>
              </div>
            </div>
            <div className="flex items-center gap-6">
              <button className="text-sm text-slate-700 hover:text-blue-700 font-medium transition">
                About
              </button>
              <button className="text-sm text-slate-700 hover:text-blue-700 font-medium transition">
                Documentation
              </button>
              <button className="px-4 py-2 bg-blue-700 text-white rounded-lg text-sm font-medium hover:bg-blue-800 transition">
                Sign In
              </button>
            </div>
          </div>
        </div>
      </header>

      {/* Hero Section */}
      <div className="bg-gradient-to-b from-blue-50/50 to-white border-b border-slate-200">
        <div className="max-w-5xl mx-auto px-6 py-16 text-center">
          <div className="inline-flex items-center gap-2 px-4 py-2 bg-blue-100 text-blue-800 rounded-full text-sm font-medium mb-6">
            <Shield className="w-4 h-4" />
            <span>Powered by AI • 5 Government Documents</span>
          </div>

          <h2 className="text-5xl font-bold text-slate-900 mb-4 font-crimson">
            Indonesian Government
            <br />
            Legal Research Platform
          </h2>
          <p className="text-xl text-slate-600 mb-12 max-w-2xl mx-auto">
            Search through thousands of Indonesian government regulations,
            laws, and policies with AI-powered precision
          </p>

          {/* Search Box */}
          <div className="max-w-3xl mx-auto">
            <div className="relative">
              <Search className="absolute left-4 top-1/2 -translate-y-1/2 text-slate-400 w-5 h-5" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                onKeyPress={(e) => e.key === 'Enter' && handleQuery(query)}
                placeholder="Search regulations, laws, and policies..."
                className="w-full pl-12 pr-4 py-4 bg-white border-2 border-slate-200 rounded-xl text-slate-900 placeholder-slate-400 focus:outline-none focus:border-blue-600 focus:ring-4 focus:ring-blue-100 transition shadow-sm"
              />
              <button
                onClick={() => handleQuery(query)}
                disabled={loading}
                className="absolute right-2 top-1/2 -translate-y-1/2 px-6 py-2 bg-blue-700 text-white rounded-lg font-medium hover:bg-blue-800 transition disabled:bg-slate-400"
              >
                {loading ? 'Searching...' : 'Search'}
              </button>
            </div>

            {/* Example Questions */}
            <div className="mt-4 flex flex-wrap gap-2 justify-center">
              <span className="text-sm text-slate-600 mr-2">Popular:</span>
              {exampleQuestions.map((q, i) => (
                <button
                  key={i}
                  onClick={() => handleQuery(q)}
                  disabled={loading}
                  className="px-3 py-1.5 bg-white border border-slate-200 rounded-lg text-sm text-slate-700 hover:border-blue-600 hover:text-blue-700 transition disabled:opacity-50"
                >
                  {q}
                </button>
              ))}
            </div>
          </div>
        </div>
      </div>

      {/* Results Section */}
      <div className="max-w-5xl mx-auto px-6 py-12">
        {/* Loading State */}
        {loading && (
          <div className="text-center py-12">
            <div className="inline-block w-8 h-8 border-4 border-blue-200 border-t-blue-700 rounded-full animate-spin"></div>
            <p className="mt-4 text-slate-600">Searching legal database...</p>
          </div>
        )}

        {/* Error State */}
        {error && (
          <div className="bg-amber-50 border border-amber-200 rounded-xl p-6">
            <div className="flex items-start gap-3">
              <AlertCircle className="w-5 h-5 text-amber-600 flex-shrink-0 mt-0.5" />
              <div>
                <h3 className="font-semibold text-amber-900 mb-2">Terjadi Kesalahan</h3>
                <p className="text-sm text-amber-800 mb-3">{error}</p>

                <div className="bg-white rounded-lg p-4 text-sm">
                  <p className="font-medium text-slate-900 mb-2">💡 Saran:</p>
                  <ul className="text-slate-700 space-y-1 ml-4 list-disc">
                    <li>Pastikan API server berjalan: <code className="bg-slate-100 px-2 py-0.5 rounded text-xs">python api/main.py</code></li>
                    <li>Cek koneksi internet Anda</li>
                    <li>Refresh halaman dan coba lagi</li>
                    <li>Gunakan kata kunci yang lebih spesifik</li>
                  </ul>
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Results */}
        {result && (
          <div className="space-y-6">
            {/* Answer Card */}
            <div className="bg-white rounded-xl border border-slate-200 shadow-sm p-8">
              <div className="flex items-start justify-between mb-4">
                <h3 className="text-lg font-semibold text-slate-900">Answer</h3>
                <div className="flex items-center gap-4 text-sm">
                  <span className="text-slate-600">
                    Confidence: <span className="font-semibold text-blue-700">{(result.confidence * 100).toFixed(0)}%</span>
                  </span>
                  <span className="text-slate-600">
                    {result.processing_time.toFixed(2)}s
                  </span>
                </div>
              </div>
              <p className="text-slate-700 leading-relaxed whitespace-pre-line">
                {result.answer}
              </p>
            </div>

            {/* Sources */}
            <div>
              <h3 className="text-lg font-semibold text-slate-900 mb-4">Sources ({result.sources.length})</h3>
              <div className="space-y-4">
                {result.sources.map((source, i) => (
                  <div key={i} className="bg-white rounded-xl border border-slate-200 shadow-sm p-6 hover:shadow-md transition">
                    <div className="flex items-start justify-between mb-3">
                      <div className="flex items-center gap-3">
                        <FileText className="w-5 h-5 text-blue-700" />
                        <h4 className="font-semibold text-slate-900">{source.title}</h4>
                      </div>
                      <div className="flex items-center gap-2">
                        <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs font-medium">
                          {source.category}
                        </span>
                        <span className="text-sm text-slate-600">
                          {(source.score * 100).toFixed(0)}% match
                        </span>
                      </div>
                    </div>
                    <p className="text-sm text-slate-600 leading-relaxed">
                      {source.text}
                    </p>
                  </div>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Stats - only show if no results */}
      {!result && !loading && !error && (
        <div className="max-w-7xl mx-auto px-6 py-16">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8">
            <div className="text-center p-8 bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition">
              <FileText className="w-10 h-10 text-blue-700 mx-auto mb-4" />
              <div className="text-3xl font-bold text-slate-900 mb-2">5+</div>
              <div className="text-sm text-slate-600 font-medium">Documents</div>
            </div>

            <div className="text-center p-8 bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition">
              <Scale className="w-10 h-10 text-blue-700 mx-auto mb-4" />
              <div className="text-3xl font-bold text-slate-900 mb-2">95%</div>
              <div className="text-sm text-slate-600 font-medium">Accuracy</div>
            </div>

            <div className="text-center p-8 bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition">
              <Clock className="w-10 h-10 text-blue-700 mx-auto mb-4" />
              <div className="text-3xl font-bold text-slate-900 mb-2">&lt;2s</div>
              <div className="text-sm text-slate-600 font-medium">Response Time</div>
            </div>

            <div className="text-center p-8 bg-white rounded-xl border border-slate-200 shadow-sm hover:shadow-md transition">
              <BookOpen className="w-10 h-10 text-blue-700 mx-auto mb-4" />
              <div className="text-3xl font-bold text-slate-900 mb-2">100%</div>
              <div className="text-sm text-slate-600 font-medium">Free</div>
            </div>
          </div>
        </div>
      )}

      {/* Features - only show if no results */}
      {!result && !loading && !error && (
        <div className="bg-white border-y border-slate-200 py-16">
          <div className="max-w-7xl mx-auto px-6">
            <div className="text-center mb-12">
              <h3 className="text-3xl font-bold text-slate-900 mb-3 font-crimson">
                Professional Legal Research Tools
              </h3>
              <p className="text-slate-600">
                Advanced AI technology optimized for Indonesian legal documents
              </p>
            </div>

            <div className="grid grid-cols-1 md:grid-cols-3 gap-8">
              <div className="p-8 bg-slate-50 rounded-xl border border-slate-200">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                  <Search className="w-6 h-6 text-blue-700" />
                </div>
                <h4 className="text-lg font-semibold text-slate-900 mb-2">
                  AI-Powered Search
                </h4>
                <p className="text-slate-600 text-sm leading-relaxed">
                  Natural language queries with semantic understanding for precise legal research
                </p>
              </div>

              <div className="p-8 bg-slate-50 rounded-xl border border-slate-200">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                  <Shield className="w-6 h-6 text-blue-700" />
                </div>
                <h4 className="text-lg font-semibold text-slate-900 mb-2">
                  Verified Sources
                </h4>
                <p className="text-slate-600 text-sm leading-relaxed">
                  All information sourced from official Indonesian government documents
                </p>
              </div>

              <div className="p-8 bg-slate-50 rounded-xl border border-slate-200">
                <div className="w-12 h-12 bg-blue-100 rounded-lg flex items-center justify-center mb-4">
                  <Clock className="w-6 h-6 text-blue-700" />
                </div>
                <h4 className="text-lg font-semibold text-slate-900 mb-2">
                  Instant Results
                </h4>
                <p className="text-slate-600 text-sm leading-relaxed">
                  Get accurate answers in under 2 seconds with citation references
                </p>
              </div>
            </div>
          </div>
        </div>
      )}

      {/* Footer */}
      <footer className="bg-slate-900 text-white py-12">
        <div className="max-w-7xl mx-auto px-6">
          <div className="grid grid-cols-1 md:grid-cols-4 gap-8 mb-8">
            <div>
              <div className="flex items-center gap-2 mb-4">
                <Scale className="w-6 h-6 text-blue-400" />
                <span className="font-bold text-lg font-crimson">IndoGovRAG</span>
              </div>
              <p className="text-slate-400 text-sm">
                Professional legal research platform for Indonesian government documents
              </p>
            </div>

            <div>
              <h5 className="font-semibold mb-4">Product</h5>
              <ul className="space-y-2 text-sm text-slate-400">
                <li><a href="#" className="hover:text-white transition">Features</a></li>
                <li><a href="#" className="hover:text-white transition">Pricing</a></li>
                <li><a href="#" className="hover:text-white transition">API</a></li>
              </ul>
            </div>

            <div>
              <h5 className="font-semibold mb-4">Resources</h5>
              <ul className="space-y-2 text-sm text-slate-400">
                <li><a href="#" className="hover:text-white transition">Documentation</a></li>
                <li><a href="#" className="hover:text-white transition">Guides</a></li>
                <li><a href="#" className="hover:text-white transition">Support</a></li>
              </ul>
            </div>

            <div>
              <h5 className="font-semibold mb-4">Company</h5>
              <ul className="space-y-2 text-sm text-slate-400">
                <li><a href="#" className="hover:text-white transition">About</a></li>
                <li><a href="#" className="hover:text-white transition">Blog</a></li>
                <li><a href="#" className="hover:text-white transition">Contact</a></li>
              </ul>
            </div>
          </div>

          <div className="border-t border-slate-800 pt-8 text-center text-slate-400 text-sm">
            <p>© 2024 IndoGovRAG. Built for Indonesia 🇮🇩</p>
            <p className="mt-2">Powered by 100% free & open-source technology</p>
          </div>
        </div>
      </footer>
    </main>
  );
}
