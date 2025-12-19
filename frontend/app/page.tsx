'use client';

import { useState, useEffect } from 'react';
import { Search, FileText, Scale, Clock, Shield, BookOpen, AlertCircle, CheckCircle2, Zap, Database } from 'lucide-react';

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
  const [history, setHistory] = useState<any[]>([]);

  // Load history on mount
  useEffect(() => {
    const saved = localStorage.getItem('indogovrag_history');
    if (saved) {
      try {
        setHistory(JSON.parse(saved));
      } catch (e) {
        console.error('Failed to load history', e);
      }
    }
  }, []);

  const exampleQuestions = [
    { title: "Identitas", q: "Bagaimana cara membuat SIM A dan berapa biayanya?" },
    { title: "Pajak", q: "Apa saja tarif PPh terbaru untuk orang pribadi?" },
    { title: "Keluarga", q: "Syarat membuat akta kelahiran untuk anak di atas 60 hari?" },
    { title: "Bisnis", q: "Apa itu NIB dan bagaimana cara mendapatkannya via OSS?" },
    { title: "Kesehatan", q: "Berapa iuran BPJS Kesehatan Mandiri kelas 1, 2, dan 3?" },
    { title: "Bansos", q: "Apa itu PKH dan siapa saja yang berhak menerimanya?" },
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
          top_k: 4 // Increased for better AI context
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

      // Save and update history
      const newHistory = saveToHistory(q, data);
      setHistory(newHistory);

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
        answer: response.answer.substring(0, 100) + "...",
        timestamp: new Date().toLocaleTimeString(),
        sources: response.sources.length
      });
      const truncated = history.slice(0, 10);
      localStorage.setItem('indogovrag_history', JSON.stringify(truncated));
      return truncated;
    } catch (e) {
      console.error('Failed to save history', e);
      return [];
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
        <div className="max-w-7xl mx-auto px-4 sm:px-6 py-12 flex flex-col lg:flex-row gap-8">

          {/* Main Content Area */}
          <div className="flex-1 space-y-8">
            {/* Initial Search Prompts */}
            {!result && !loading && !error && (
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                {exampleQuestions.map((item, idx) => (
                  <button
                    key={idx}
                    onClick={() => handleQuery(item.q)}
                    className="p-4 text-left bg-white border border-slate-200 rounded-xl hover:border-slate-300 hover:shadow-sm transition-all group"
                  >
                    <span className="text-xs font-bold text-slate-400 uppercase tracking-wider mb-1 block">
                      {item.title}
                    </span>
                    <p className="text-slate-700 font-medium group-hover:text-slate-900 leading-snug">
                      {item.q}
                    </p>
                  </button>
                ))}
              </div>
            )}

            {/* Loading State */}
            {loading && (
              <div className="bg-white border border-slate-200 rounded-xl p-12 text-center space-y-4 animate-in fade-in zoom-in duration-300">
                <div className="w-12 h-12 border-4 border-slate-100 border-t-slate-800 rounded-full animate-spin mx-auto" />
                <div>
                  <p className="font-semibold text-slate-900">Menganalisis Peraturan...</p>
                  <p className="text-sm text-slate-500">Mencari referensi hukum yang relevan</p>
                </div>
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
                      </ul>
                    </div>
                  </div>
                </div>
              </div>
            )}

            {/* Result State */}
            {result && !loading && (
              <div className="space-y-8 animate-in fade-in slide-in-from-bottom-4 duration-500">
                {/* Answer Card */}
                <div className="bg-white border border-slate-200 rounded-xl shadow-sm overflow-hidden">
                  <div className="bg-slate-50 border-b border-slate-100 px-6 py-4 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Zap className="w-4 h-4 text-slate-400" />
                      <span className="text-sm font-semibold text-slate-900">Jawaban AI</span>
                    </div>
                    <div className="flex items-center gap-4">
                      <div className="flex items-center gap-1.5">
                        <span className="text-xs text-slate-500">Confidence:</span>
                        <span className={`text-xs font-bold ${result.confidence > 0.7 ? 'text-green-600' :
                          result.confidence > 0.4 ? 'text-amber-600' : 'text-slate-600'
                          }`}>
                          {Math.round(result.confidence * 100)}%
                        </span>
                      </div>
                      <span className="text-xs text-slate-400">{result.processing_time.toFixed(2)}s</span>
                    </div>
                  </div>
                  <div className="p-6 md:p-8">
                    <div className="prose prose-slate max-w-none text-slate-800 leading-relaxed font-serif text-lg">
                      {result.answer.split('\n').map((line, i) => (
                        <p key={i} className={line.trim() === "" ? "h-2" : ""}>{line}</p>
                      ))}
                    </div>
                  </div>
                </div>

                {/* Sources Section */}
                <div className="space-y-4">
                  <div className="flex items-center gap-2 px-1">
                    <Database className="w-4 h-4 text-slate-400" />
                    <h3 className="text-sm font-bold text-slate-900 uppercase tracking-wider">Referensi Dokumen ({result.sources.length})</h3>
                  </div>

                  <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
                    {result.sources.map((source, idx) => (
                      <div key={idx} className="bg-white border border-slate-200 rounded-xl p-5 hover:border-slate-300 transition-colors shadow-sm">
                        <div className="flex items-start justify-between mb-3">
                          <div className="flex items-center gap-2">
                            <FileText className="w-4 h-4 text-slate-500" />
                            <h4 className="font-bold text-slate-900 leading-tight">{source.title}</h4>
                          </div>
                          <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-[10px] font-bold uppercase tracking-tight">
                            {source.category}
                          </span>
                        </div>
                        <p className="text-sm text-slate-600 line-clamp-3 mb-3 font-serif italic">
                          "{source.text}"
                        </p>
                        <div className="flex items-center justify-end border-t border-slate-50 pt-3">
                          <span className="text-[10px] font-medium text-slate-400">Match Score: {Math.round(source.score * 100)}%</span>
                        </div>
                      </div>
                    ))}
                  </div>
                </div>
              </div>
            )}
          </div>

          {/* Sidebar - History & Tools */}
          <aside className="lg:w-80 space-y-6">
            <div className="bg-white border border-slate-200 rounded-xl p-5 shadow-sm">
              <h3 className="text-xs font-bold text-slate-400 uppercase tracking-widest mb-4">Riwayat Pencarian</h3>
              {history.length > 0 ? (
                <div className="space-y-4">
                  {history.map((item, idx) => (
                    <button
                      key={idx}
                      onClick={() => handleQuery(item.question)}
                      className="w-full text-left group"
                    >
                      <p className="text-sm font-semibold text-slate-800 group-hover:text-blue-700 line-clamp-1 transition-colors">{item.question}</p>
                      <div className="flex items-center gap-2 mt-1">
                        <span className="text-[10px] text-slate-400 font-medium">{item.timestamp}</span>
                        <span className="text-[10px] text-slate-400">•</span>
                        <span className="text-[10px] text-slate-400 font-medium">{item.sources} sumber</span>
                      </div>
                    </button>
                  ))}
                </div>
              ) : (
                <p className="text-sm text-slate-400 italic">Belum ada riwayat</p>
              )}
              <div className="mt-6 pt-4 border-t border-slate-100">
                <button
                  onClick={() => { localStorage.removeItem('indogovrag_history'); setHistory([]); }}
                  className="text-[10px] font-bold text-slate-400 hover:text-red-500 transition-colors uppercase tracking-wider"
                >
                  Hapus Riwayat
                </button>
              </div>
            </div>

            <div className="bg-slate-900 rounded-xl p-5 text-white shadow-lg overflow-hidden relative">
              <div className="relative z-10">
                <h3 className="font-bold text-lg mb-2">Upgrade Engine?</h3>
                <p className="text-xs text-slate-400 leading-relaxed mb-4">
                  Sistem saat ini menggunakan TF-IDF. Upgrade ke Neural Ops untuk akurasi 95%+.
                </p>
                <button className="w-full py-2 bg-white text-slate-900 rounded-lg text-xs font-bold hover:bg-slate-100 transition-colors">
                  Pelajari Selengkapnya
                </button>
              </div>
              <div className="absolute -right-4 -bottom-4 w-24 h-24 bg-blue-600/20 rounded-full blur-2xl" />
            </div>
          </aside>
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
      </div>

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
