'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { X, Key, Eye, EyeOff, Check, AlertCircle, Trash2, RefreshCw } from 'lucide-react'
import { useSearchStore } from '../lib/searchStore'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'

export default function SettingsModal() {
  const store = useSearchStore()
  
  // Local state for keys (initial empty to avoid hydration mismatch)
  const [groqKey, setGroqKey] = useState('')
  const [geminiKey, setGeminiKey] = useState('')
  
  // Password visibility
  const [showGroq, setShowGroq] = useState(false)
  const [showGemini, setShowGemini] = useState(false)
  
  // Test connection state
  const [testState, setTestState] = useState<'idle' | 'testing' | 'success' | 'failed'>('idle')
  const [testResult, setTestResult] = useState('')
  const [modelUsed, setModelUsed] = useState('')

  // Hydrate keys from localStorage on mount (prevents SSR mismatch)
  useEffect(() => {
    if (typeof window !== 'undefined') {
      setGroqKey(localStorage.getItem('custom_groq_api_key') ?? '')
      setGeminiKey(localStorage.getItem('custom_gemini_api_key') ?? '')
    }
  }, [store.isSettingsOpen])

  if (!store.isSettingsOpen) return null

  const handleSave = () => {
    if (typeof window !== 'undefined') {
      localStorage.setItem('custom_groq_api_key', groqKey.trim())
      localStorage.setItem('custom_gemini_api_key', geminiKey.trim())
      
      // Call global toast helper if registered
      const w = window as any
      if (w.showSuccessToast) {
        w.showSuccessToast('Pengaturan API Key berhasil disimpan!')
      }
      
      store.setSettingsOpen(false)
    }
  }

  const handleClear = () => {
    setGroqKey('')
    setGeminiKey('')
    if (typeof window !== 'undefined') {
      localStorage.removeItem('custom_groq_api_key')
      localStorage.removeItem('custom_gemini_api_key')
      
      const w = window as any
      if (w.showSuccessToast) {
        w.showSuccessToast('API Key telah dihapus. Menggunakan default server.')
      }
    }
    setTestState('idle')
    setTestResult('')
  }

  const handleTestConnection = async () => {
    setTestState('testing')
    setTestResult('')
    setModelUsed('')
    
    try {
      const headers: Record<string, string> = {
        'Content-Type': 'application/json',
      }
      if (groqKey.trim()) headers['X-Custom-Groq-Key'] = groqKey.trim()
      if (geminiKey.trim()) headers['X-Custom-Gemini-Key'] = geminiKey.trim()

      const response = await fetch(`${API}/query`, {
        method: 'POST',
        headers,
        body: JSON.stringify({
          query: 'Tes koneksi sistem legal AI',
          options: {
            top_k: 1,
            use_cache: false, // Bypass cache to test the keys directly
          }
        }),
      })

      if (!response.ok) {
        throw new Error(`API error ${response.status}`)
      }

      const data = await response.json()
      const usedModel = data.metadata?.model_used ?? 'unknown'
      
      setTestState('success')
      setModelUsed(usedModel)
      setTestResult('Koneksi berhasil terhubung dengan server!')
    } catch (err: any) {
      setTestState('failed')
      setTestResult(err.message || 'Gagal terhubung dengan LLM API. Periksa kembali Key Anda.')
    }
  }

  return (
    <AnimatePresence>
      <div className="fixed inset-0 z-50 flex items-center justify-center p-4">
        {/* Backdrop */}
        <motion.div
          initial={{ opacity: 0 }}
          animate={{ opacity: 1 }}
          exit={{ opacity: 0 }}
          className="absolute inset-0 bg-slate-900/60 backdrop-blur-xs"
          onClick={() => store.setSettingsOpen(false)}
        />

        {/* Modal Panel */}
        <motion.div
          initial={{ opacity: 0, scale: 0.95, y: 16 }}
          animate={{ opacity: 1, scale: 1, y: 0 }}
          exit={{ opacity: 0, scale: 0.95, y: 16 }}
          transition={{ duration: 0.2, ease: 'easeOut' }}
          className="relative w-full max-w-lg bg-white border border-slate-200 rounded-xl shadow-2xl overflow-hidden z-10"
        >
          {/* Header */}
          <div className="flex items-center justify-between px-6 py-4 border-b border-slate-200 bg-slate-50">
            <div className="flex items-center gap-2.5">
              <div className="w-8 h-8 bg-accent-100 rounded-lg flex items-center justify-center shrink-0">
                <Key className="w-4 h-4 text-accent-500" />
              </div>
              <div>
                <h3 className="font-serif text-base font-bold text-slate-900">Custom LLM API Keys</h3>
                <p className="text-[11px] text-slate-500">Konfigurasikan kunci API Anda sendiri</p>
              </div>
            </div>
            <button
              onClick={() => store.setSettingsOpen(false)}
              className="p-1.5 hover:bg-slate-200 rounded-lg transition-colors text-slate-400 hover:text-slate-600 focus:outline-none"
              aria-label="Tutup"
            >
              <X className="w-4 h-4" />
            </button>
          </div>

          {/* Body */}
          <div className="p-6 space-y-5">
            <p className="text-xs text-slate-600 leading-relaxed">
              Jika Anda mengalami limitasi kuota server (rate limit), masukkan API Key pribadi Anda di bawah ini.
              Kunci Anda hanya akan disimpan secara lokal di browser Anda (`localStorage`) dan langsung dikirim ke model.
            </p>

            {/* Groq Key Input */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700 block">Groq API Key (Llama 3.3 70B)</label>
              <div className="relative">
                <input
                  type={showGroq ? 'text' : 'password'}
                  value={groqKey}
                  onChange={(e) => setGroqKey(e.target.value)}
                  placeholder="gsk_..."
                  className="w-full h-10 pl-3 pr-10 border border-slate-200 rounded-lg text-sm bg-slate-50 focus:bg-white focus:border-accent-500 focus:ring-2 focus:ring-accent-500/10 transition-all outline-none"
                />
                <button
                  type="button"
                  onClick={() => setShowGroq(!showGroq)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-0.5 rounded focus:outline-none"
                >
                  {showGroq ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Gemini Key Input */}
            <div className="space-y-1.5">
              <label className="text-xs font-bold text-slate-700 block">Gemini API Key (Gemini Pro/Flash)</label>
              <div className="relative">
                <input
                  type={showGemini ? 'text' : 'password'}
                  value={geminiKey}
                  onChange={(e) => setGeminiKey(e.target.value)}
                  placeholder="AIzaSy..."
                  className="w-full h-10 pl-3 pr-10 border border-slate-200 rounded-lg text-sm bg-slate-50 focus:bg-white focus:border-accent-500 focus:ring-2 focus:ring-accent-500/10 transition-all outline-none"
                />
                <button
                  type="button"
                  onClick={() => setShowGemini(!showGemini)}
                  className="absolute right-3 top-1/2 -translate-y-1/2 text-slate-400 hover:text-slate-600 p-0.5 rounded focus:outline-none"
                >
                  {showGemini ? <EyeOff className="w-4 h-4" /> : <Eye className="w-4 h-4" />}
                </button>
              </div>
            </div>

            {/* Test Connection Output */}
            {testState !== 'idle' && (
              <div
                className={`p-3.5 rounded-lg border text-xs flex items-start gap-2.5 ${
                  testState === 'testing'
                    ? 'bg-slate-50 border-slate-200 text-slate-600'
                    : testState === 'success'
                    ? 'bg-emerald-50 border-emerald-200 text-emerald-800'
                    : 'bg-red-50 border-red-200 text-red-800'
                }`}
              >
                {testState === 'testing' && <RefreshCw className="w-4 h-4 animate-spin text-slate-500 shrink-0 mt-0.5" />}
                {testState === 'success' && <Check className="w-4 h-4 text-emerald-600 shrink-0 mt-0.5" />}
                {testState === 'failed' && <AlertCircle className="w-4 h-4 text-red-600 shrink-0 mt-0.5" />}
                <div>
                  <p className="font-semibold">
                    {testState === 'testing' && 'Menguji koneksi ke API server...'}
                    {testState === 'success' && 'Uji Koneksi Berhasil!'}
                    {testState === 'failed' && 'Uji Koneksi Gagal'}
                  </p>
                  <p className="opacity-90 mt-0.5">{testResult}</p>
                  {modelUsed && (
                    <p className="mt-1 text-[10px] font-mono bg-emerald-100/50 text-emerald-700 px-1.5 py-0.5 rounded inline-block">
                      Model Terpakai: {modelUsed}
                    </p>
                  )}
                </div>
              </div>
            )}
          </div>

          {/* Footer Actions */}
          <div className="flex items-center justify-between px-6 py-4 border-t border-slate-200 bg-slate-50">
            <button
              onClick={handleClear}
              className="flex items-center gap-1.5 px-3 py-2 text-xs font-semibold text-red-600 hover:bg-red-50 rounded-lg transition-colors focus:outline-none"
              title="Reset ke Default Server"
            >
              <Trash2 className="w-3.5 h-3.5" />
              <span>Hapus Key</span>
            </button>

            <div className="flex gap-2">
              <button
                onClick={handleTestConnection}
                disabled={testState === 'testing'}
                className="px-4 py-2 border border-slate-200 hover:border-slate-300 rounded-lg text-xs font-bold text-slate-700 bg-white hover:bg-slate-50 active:scale-95 transition-all focus:outline-none disabled:opacity-55"
              >
                Uji Koneksi
              </button>
              <button
                onClick={handleSave}
                className="px-4 py-2 bg-accent-500 hover:bg-accent-600 text-white rounded-lg text-xs font-bold active:scale-95 transition-all shadow-sm focus:outline-none"
              >
                Simpan &amp; Terapkan
              </button>
            </div>
          </div>
        </motion.div>
      </div>
    </AnimatePresence>
  )
}
