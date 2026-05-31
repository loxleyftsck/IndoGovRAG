'use client'

import { useState, useEffect, useRef, useCallback } from 'react'
import { useRouter } from 'next/navigation'
import { motion, AnimatePresence } from 'framer-motion'
import {
  Search, Zap, Shield, TrendingUp, CheckCircle, X, History,
  AlertTriangle, Loader2, RotateCcw, Lightbulb, WifiOff,
  BookOpen, Sparkles, Globe, Quote
} from 'lucide-react'
import AppShell from './components/AppShell'
import ConfidenceBadge from './components/ConfidenceBadge'
import LegalDisclaimer from './components/LegalDisclaimer'
import LegalQuoteBanner from './components/LegalQuoteBanner'
import PhilosophyFooter from './components/PhilosophyFooter'
import { AgentLoadingState } from './components/LoadingStates'
import { SourceCardList } from './components/SourceCard'

// ── Types ────────────────────────────────────────────────────────
interface QueryResult {
  answer: string
  sources: string[]
  confidence: number
  latency_ms: number
  from_cache?: boolean
  metadata?: {
    chunks_retrieved?: number
    expansion_used?: boolean
    reranking_used?: boolean
    warnings?: string[]
    status?: string
    is_high_stakes?: boolean
    topic?: string
  }
}
interface QueryHistoryItem {
  id: string
  query: string
  answer: string
  feedback: 'helpful' | 'not_helpful' | null
  timestamp: string
}
interface FileStats {
  total_chunks: number
  unique_files: number
  categories: Record<string, number>
}

// ── Constants ───────────────────────────────────────────────────
const HARD_TIMEOUT_SECONDS = 15
const LOW_CONFIDENCE_THRESHOLD = 0.4
const LOADING_MESSAGES = [
  'Mencari dokumen relevan...',
  'Memproses pertanyaan Anda...',
  'Mengambil sumber informasi...',
]
const POPULAR_SEARCHES = [
  'Persyaratan KTP Elektronik',
  'Persetujuan BPJS Kesehatan',
  'Aturan BPJS Kelas 3',
  'Syarat Buat SIM A',
]
const CATEGORY_CHIPS = [
  { label: 'UU',      desc: 'Undang-Undang' },
  { label: 'PP',      desc: 'Peraturan Pemerintah' },
  { label: 'Perpres', desc: 'Peraturan Presiden' },
  { label: 'Permen',  desc: 'Peraturan Menteri' },
  { label: 'Perda',   desc: 'Peraturan Daerah' },
  { label: 'POJK',    desc: 'Peraturan OJK' },
  { label: 'SE',      desc: 'Surat Edaran' },
]

const FEATURE_CARDS = [
  {
    icon: <Sparkles className="w-7 h-7" />,
    title: 'Pencarian Cerdas',
    description: 'AI memahami maksud Anda, bukan hanya kata kunci. Hybridsemantic search dengan expansion & reranking.',
    color: 'bg-amber-50 border-amber-200',
    iconBg: 'bg-amber-500',
    accent: 'text-amber-600',
    tag: 'AI-Powered',
  },
  {
    icon: <Globe className="w-7 h-7" />,
    title: 'Sumber Terverifikasi',
    description: 'Semua data berasal dari JDIH resmi dan koleksi dokumen hukum terpercaya pemerintah Indonesia.',
    color: 'bg-indigo-50 border-indigo-200',
    iconBg: 'bg-indigo-600',
    accent: 'text-indigo-600',
    tag: 'JDIH Official',
  },
  {
    icon: <Quote className="w-7 h-7" />,
    title: 'Citasi Resmi',
    description: 'Setiap jawaban menyertakan citasi regulasi asli dengan nomor, tahun, dan judul peraturan.',
    color: 'bg-emerald-50 border-emerald-200',
    iconBg: 'bg-emerald-500',
    accent: 'text-emerald-600',
    tag: 'Verified',
  },
]

const STATS_ITEMS = [
  { value: '12.847', label: 'Dokumen', icon: BookOpen },
  { value: '7',       label: 'Jenis Regulasi', icon: Shield },
  { value: '1945–2025', label: 'Rentang Tahun', icon: Globe },
  { value: 'AI-Powered', label: 'Teknologi', icon: Zap },
]

// ── Small UI components ─────────────────────────────────────────
function InlineSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const dim = size === 'sm' ? 'spinner-sm' : size === 'lg' ? 'spinner-lg' : ''
  return <div className={`spinner ${dim}`} aria-label="Memuat..." role="status" />
}

function ShimmerCard({ lines = 4 }: { lines?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3 }}
      className="bg-white rounded-2xl border border-slate-200 p-6 md:p-8 shadow-md overflow-hidden"
      aria-hidden="true"
    >
      <div className="flex items-center justify-between mb-6">
        <div className="skeleton h-7 w-28 rounded-lg" />
        <div className="flex gap-2">
          <div className="skeleton h-7 w-16 rounded-full" />
          <div className="skeleton h-7 w-24 rounded-full" />
        </div>
      </div>
      <div className="space-y-3">
        {Array.from({ length: lines }).map((_, i) => (
          <div key={i} className="skeleton h-5 rounded" style={{ width: `${60 + Math.random() * 35}%` }} />
        ))}
        <div className="skeleton h-5 rounded" style={{ width: '40%' }} />
      </div>
      <div className="mt-6 pt-6 border-t border-slate-100 grid grid-cols-4 gap-4">
        {[1, 2, 3, 4].map(i => (
          <div key={i} className="space-y-2">
            <div className="skeleton h-3 w-16 rounded" />
            <div className="skeleton h-8 w-12 rounded" />
          </div>
        ))}
      </div>
    </motion.div>
  )
}

function ShimmerSources({ count = 3 }: { count?: number }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 8 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.3, delay: 0.1 }}
      className="bg-white rounded-2xl border border-slate-200 p-6 md:p-8 shadow-md overflow-hidden"
      aria-hidden="true"
    >
      <div className="skeleton h-6 w-40 rounded-lg mb-4" />
      <div className="space-y-3">
        {Array.from({ length: count }).map((_, i) => (
          <div key={i} className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
            <div className="skeleton w-6 h-6 rounded-full flex-shrink-0" />
            <div className="skeleton h-5 rounded flex-1" style={{ width: `${50 + Math.random() * 40}%` }} />
          </div>
        ))}
      </div>
    </motion.div>
  )
}

function InlineLoadingState() {
  return (
    <AnimatePresence mode="wait">
      <motion.div
        key="loading"
        initial={{ opacity: 0 }}
        animate={{ opacity: 1 }}
        exit={{ opacity: 0 }}
        className="max-w-4xl mx-auto space-y-4 sm:space-y-6 px-3 sm:px-0"
      >
        <div className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-md">
          <div className="flex items-center gap-3 mb-5">
            <InlineSpinner size="md" />
            <div className="flex-1">
              <div className="skeleton h-5 w-48 rounded-md mb-1.5" />
              <div className="skeleton h-3 w-32 rounded" />
            </div>
          </div>
          <div className="w-full h-1.5 bg-slate-100 rounded-full overflow-hidden mb-5">
            <motion.div
              className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
              initial={{ width: '10%' }}
              animate={{ width: '85%' }}
              transition={{ duration: 2.5, ease: 'easeInOut', repeat: Infinity, repeatType: 'reverse' }}
            />
          </div>
          <div className="space-y-3">
            {[1, 2, 3, 4, 5].map(i => (
              <div key={i} className="skeleton h-5 rounded" style={{ width: `${55 + Math.random() * 40}%` }} />
            ))}
            <div className="skeleton h-5 rounded" style={{ width: '35%' }} />
          </div>
        </div>
        <ShimmerSources count={4} />
      </motion.div>
    </AnimatePresence>
  )
}

function TimeoutWarning({ elapsed, onDismiss }: { elapsed: number; onDismiss?: () => void }) {
  const isHard = elapsed >= HARD_TIMEOUT_SECONDS
  return (
    <motion.div
      initial={{ opacity: 0, y: -8 }}
      animate={{ opacity: 1, y: 0 }}
      className={`max-w-3xl mx-auto mb-6 p-4 rounded-xl flex items-center gap-3 text-sm ${
        isHard ? 'bg-amber-50 border border-amber-300 text-amber-800' : 'bg-blue-50 border border-blue-200 text-blue-700'
      }`}
      role="alert"
    >
      <div className="flex-shrink-0">
        {isHard ? <AlertTriangle className="w-5 h-5" /> : <Loader2 className="w-5 h-5 animate-spin" />}
      </div>
      <div className="flex-1">
        <p className="font-semibold">
          {isHard ? 'Waktu respons habis — menampilkan hasil dasar' : 'Proses memerlukan waktu lebih lama...'}
        </p>
        <p className="text-xs opacity-80 mt-0.5">
          {isHard
            ? 'Server memerlukan waktu lebih dari 15 detik. Hasil pencarian dasar ditampilkan.'
            : `Sudah berjalan selama ${elapsed} detik. Harap tunggu...`
          }
        </p>
      </div>
      {onDismiss && !isHard && (
        <button
          onClick={onDismiss}
          className="p-1 hover:bg-blue-100 rounded transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
          aria-label="Tutup peringatan"
        >
          <X className="w-4 h-4" />
        </button>
      )}
    </motion.div>
  )
}

function ConfidenceWarning({ confidence }: { confidence: number }) {
  if (confidence >= LOW_CONFIDENCE_THRESHOLD) return null
  const isVeryLow = confidence < 0.2
  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl mx-auto mb-4 px-3 sm:px-0"
      role="alert"
    >
      <div className={`p-3 rounded-xl flex items-start gap-3 text-sm ${
        isVeryLow ? 'bg-red-50 border border-red-200 text-red-700' : 'bg-yellow-50 border border-yellow-200 text-yellow-700'
      }`}>
        <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold">
            {isVeryLow ? 'Tingkat keyakinan sangat rendah' : 'Tingkat keyakinan rendah'}
          </p>
          <p className="text-xs opacity-80 mt-0.5">
            {isVeryLow
              ? 'Jawaban mungkin tidak akurat. Silakan verifikasi informasi dari sumber resmi.'
              : 'Silakan verifikasi informasi dari sumber resmi.'
            }
          </p>
        </div>
      </div>
    </motion.div>
  )
}

function SupersededBanner() {
  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl mx-auto mb-4 px-3 sm:px-0"
      role="alert"
    >
      <div className="p-3 rounded-xl bg-amber-50 border border-amber-300 text-amber-800 flex items-start gap-3 text-sm">
        <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold">PERHATIAN: Dokumen mungkin sudah tidak berlaku</p>
          <p className="text-xs opacity-80 mt-0.5">
            Dokumen yang digunakan sebagai sumber mungkin sudah digantikan atau tidak berlaku lagi.
            Silakan periksa peraturan terbaru sebelum menggunakan informasi ini.
          </p>
        </div>
      </div>
    </motion.div>
  )
}

function FallbackNotice({ onRetry }: { onRetry: () => void }) {
  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl mx-auto mb-4 px-3 sm:px-0"
      role="alert"
    >
      <div className="p-4 rounded-xl bg-amber-50 border border-amber-300 text-amber-800 text-sm">
        <div className="flex items-start gap-3">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5" />
          <div>
            <p className="font-semibold">Jawaban dari pencarian dasar (tanpa AI lanjutan)</p>
            <div className="mt-2 flex flex-wrap gap-2">
              <button
                onClick={onRetry}
                className="px-3 py-1.5 bg-amber-100 hover:bg-amber-200 rounded-lg text-xs font-semibold transition-colors active:scale-95 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400"
              >
                Coba lagi
              </button>
              <button
                onClick={() => window.location.reload()}
                className="px-3 py-1.5 bg-amber-100 hover:bg-amber-200 rounded-lg text-xs font-semibold transition-colors active:scale-95 focus:outline-none focus-visible:ring-2 focus-visible:ring-amber-400"
              >
                Muat ulang halaman
              </button>
            </div>
          </div>
        </div>
      </div>
    </motion.div>
  )
}

function ZeroChunksWarning() {
  return (
    <motion.div
      initial={{ opacity: 0, y: -6 }}
      animate={{ opacity: 1, y: 0 }}
      className="max-w-4xl mx-auto mb-4 px-3 sm:px-0"
      role="alert"
    >
      <div className="p-4 rounded-xl bg-orange-50 border border-orange-200 text-orange-700 flex items-start gap-3 text-sm">
        <Search className="w-5 h-5 flex-shrink-0 mt-0.5" />
        <div>
          <p className="font-semibold">Tidak ada dokumen yang ditemukan</p>
          <p className="text-xs opacity-80 mt-0.5">
            Tidak ada dokumen yang cocok dengan pertanyaan Anda.
            Coba gunakan kata kunci lain atau表述 yang lebih spesifik.
          </p>
        </div>
      </div>
    </motion.div>
  )
}

// ── History Drawer ────────────────────────────────────────────────
function HistoryDrawer({
  history, onClear, onDelete, onLoad, onClose
}: {
  history: QueryHistoryItem[]
  onClear: () => void
  onDelete: (id: string) => void
  onLoad: (item: QueryHistoryItem) => void
  onClose: () => void
}) {
  return (
    <>
      <div className="fixed inset-0 bg-black/40 z-50 backdrop-blur-sm" onClick={onClose} />
      <div className="fixed right-0 top-0 bottom-0 z-50 w-full sm:w-[380px] bg-white shadow-2xl flex flex-col animate-in slide-in-from-right">
        <div className="flex items-center justify-between px-5 py-4 border-b border-slate-200 bg-white">
          <div className="flex items-center gap-2.5">
            <div className="w-8 h-8 bg-indigo-100 rounded-xl flex items-center justify-center">
              <History className="w-4 h-4 text-indigo-600" />
            </div>
            <div>
              <h2 className="text-base font-bold text-slate-900">Riwayat Pencarian</h2>
              <p className="text-xs text-slate-500">{history.length} pertanyaan</p>
            </div>
          </div>
          <div className="flex items-center gap-2">
            {history.length > 0 && (
              <button
                onClick={onClear}
                className="px-3 py-1.5 text-xs font-medium text-red-600 hover:bg-red-50 rounded-lg transition-colors active:scale-95"
              >
                Hapus Semua
              </button>
            )}
            <button
              onClick={onClose}
              className="w-8 h-8 flex items-center justify-center text-slate-400 hover:text-slate-600 hover:bg-slate-100 rounded-lg transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-indigo-400"
              aria-label="Tutup riwayat"
            >
              <X className="w-4 h-4" />
            </button>
          </div>
        </div>

        <div className="flex-1 overflow-y-auto p-4 space-y-3">
          {history.length === 0 ? (
            <div className="flex flex-col items-center justify-center py-16 text-center">
              <div className="w-14 h-14 bg-slate-100 rounded-2xl flex items-center justify-center mb-3">
                <History className="w-7 h-7 text-slate-300" />
              </div>
              <p className="text-sm font-semibold text-slate-700">Belum ada riwayat</p>
              <p className="text-xs text-slate-400 mt-1">Pertanyaan yang Anda tanyakan akan muncul di sini</p>
            </div>
          ) : (
            history.map((item) => {
              const date = new Date(item.timestamp)
              const timeStr = date.toLocaleDateString('id-ID', {
                day: 'numeric', month: 'short', hour: '2-digit', minute: '2-digit',
              })
              return (
                <div key={item.id} className="group bg-slate-50 hover:bg-slate-100 rounded-xl p-4 transition-colors">
                  <div className="flex items-start justify-between gap-2">
                    <button
                      onClick={() => onLoad(item)}
                      className="flex-1 text-left min-h-[44px]"
                    >
                      <p className="text-sm font-semibold text-slate-900 leading-snug">{item.query}</p>
                      <p className="text-xs text-slate-500 mt-1 line-clamp-2 leading-relaxed">{item.answer}</p>
                      <p className="text-[10px] text-slate-400 mt-1.5 font-medium">{timeStr}</p>
                    </button>
                    <button
                      onClick={() => onDelete(item.id)}
                      className="w-8 h-8 flex items-center justify-center text-slate-300 hover:text-red-500 hover:bg-red-50 rounded-lg transition-colors opacity-0 group-hover:opacity-100 shrink-0"
                      aria-label="Hapus"
                    >
                      <X className="w-3.5 h-3.5" />
                    </button>
                  </div>
                  {item.feedback && (
                    <div className="flex gap-1.5 mt-2">
                      {item.feedback === 'helpful' && (
                        <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full text-[10px] font-semibold">Membantu</span>
                      )}
                      {item.feedback === 'not_helpful' && (
                        <span className="px-2 py-0.5 bg-red-100 text-red-700 rounded-full text-[10px] font-semibold">Kurang membantu</span>
                      )}
                    </div>
                  )}
                </div>
              )
            })
          )}
        </div>
      </div>
    </>
  )
}

// ── Hero Search Bar ────────────────────────────────────────────────
function HeroSearchBar({ onSearch }: { onSearch: (q: string) => void }) {
  const [value, setValue] = useState('')

  return (
    <div className="w-full max-w-2xl mx-auto">
      <form
        onSubmit={(e) => {
          e.preventDefault()
          if (value.trim()) onSearch(value.trim())
        }}
      >
        <div className="bg-white rounded-2xl shadow-xl p-2 flex flex-col sm:flex-row gap-2 ring-2 ring-white/20 focus-within:ring-indigo-400 transition-all">
          <div className="flex-1 flex items-center gap-3 px-4 py-3.5">
            <Search className="w-5 h-5 text-slate-400 shrink-0" />
            <input
              type="text"
              value={value}
              onChange={e => setValue(e.target.value)}
              placeholder="Cari dokumen hukum Indonesia..."
              aria-label="Cari dokumen hukum Indonesia"
              className="flex-1 bg-transparent text-slate-800 placeholder-slate-400 outline-none text-base min-h-[44px]"
            />
          </div>
          <button
            type="submit"
            className="w-full sm:w-auto min-h-[52px] sm:min-h-0 px-8 py-3.5 bg-indigo-600 hover:bg-indigo-700 active:bg-indigo-800 text-white font-bold rounded-xl transition-all duration-150 flex items-center justify-center gap-2 shadow-lg hover:shadow-xl active:scale-95 text-base"
          >
            <Search className="w-5 h-5" />
            <span>Cari</span>
          </button>
        </div>
      </form>

      {/* Category chips */}
      <div className="flex flex-wrap justify-center gap-2 mt-4">
        {CATEGORY_CHIPS.map(chip => (
          <button
            key={chip.label}
            onClick={() => onSearch(chip.label)}
            className="px-4 py-2 bg-white/15 hover:bg-white/25 border border-white/30 text-white rounded-xl text-xs sm:text-sm font-semibold transition-all active:scale-95"
          >
            <span className="font-bold">{chip.label}</span>
            <span className="hidden sm:inline ml-1 opacity-70 font-normal">— {chip.desc}</span>
          </button>
        ))}
      </div>
    </div>
  )
}

// ── Stats Bar ─────────────────────────────────────────────────────
function StatsBar() {
  return (
    <div className="bg-white border-b border-slate-200 shadow-sm">
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-4">
        <div className="grid grid-cols-2 sm:grid-cols-4 gap-6">
          {STATS_ITEMS.map((stat, idx) => {
            const Icon = stat.icon
            return (
              <motion.div
                key={stat.label}
                initial={{ opacity: 0, y: 8 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: idx * 0.06 }}
                className="flex items-center gap-3"
              >
                <div className="w-10 h-10 bg-indigo-50 rounded-xl flex items-center justify-center shrink-0">
                  <Icon className="w-5 h-5 text-indigo-600" />
                </div>
                <div>
                  <p className="text-lg sm:text-xl font-bold text-slate-900 leading-none">{stat.value}</p>
                  <p className="text-xs text-slate-500 mt-0.5 leading-none">{stat.label}</p>
                </div>
              </motion.div>
            )
          })}
        </div>
      </div>
    </div>
  )
}

// ── Trending Sample Cards ─────────────────────────────────────────
const SAMPLE_RESULTS = [
  {
    jenis: 'UU', nomor: '24', tahun: '2014',
    title: 'Undang-Undang No. 24 Tahun 2014 tentang BPJS',
    instansi: 'Kementerian Kesehatan',
    excerpt: 'BPJS Kesehatan adalah badan hukum yang dibentuk untuk menyelenggarakan jaminan sosial kesehatan nasional bagi seluruh rakyat Indonesia.',
    status: 'berlaku',
    tag: 'Kesehatan',
  },
  {
    jenis: 'PP', nomor: '47', tahun: '2022',
    title: 'Peraturan Pemerintah No. 47 Tahun 2022 tentang Reforma Agraria',
    instansi: 'Kementerian Agraria dan Tata Ruang',
    excerpt: 'Penyediaan tanah untuk rakyat melalui redistribusi tanah, legalisasi aset, dan penyelesaian konflik agraria secara komprehensif.',
    status: 'berlaku',
    tag: 'Agraria',
  },
  {
    jenis: 'Perpres', nomor: '98', tahun: '2023',
    title: 'Peraturan Presiden No. 98 Tahun 2023 tentang Gaji ke-14',
    instansi: 'Kementerian Keuangan',
    excerpt: ' Pemberian gaji ke-14 bagi pegawai negeri sipil, anggota TNI/POLRI, dan pejabat negara pada tahun 2023 sebesar 100% dari gaji pokok.',
    status: 'berlaku',
    tag: 'Keuangan',
  },
]

// ── Main Page ──────────────────────────────────────────────────────
export default function Home() {
  const router = useRouter()
  const [query, setQuery] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState<QueryResult | null>(null)
  const [error, setError] = useState<string | null>(null)
  const [showHistory, setShowHistory] = useState(false)
  const [history, setHistory] = useState<QueryHistoryItem[]>([])
  const [stats, setStats] = useState<FileStats | null>(null)

  const [elapsedSeconds, setElapsedSeconds] = useState(0)
  const [showTimeoutWarning, setShowTimeoutWarning] = useState(false)
  const [hardTimeoutTriggered, setHardTimeoutTriggered] = useState(false)
  const [loadingMessage, setLoadingMessage] = useState(LOADING_MESSAGES[0])
  const [successToast, setSuccessToast] = useState<string | null>(null)
  const loadingTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const secondsTimerRef = useRef<ReturnType<typeof setInterval> | null>(null)
  const hardTimeoutRef = useRef<ReturnType<typeof setTimeout> | null>(null)
  const successToastTimerRef = useRef<ReturnType<typeof setTimeout> | null>(null)

  const clearAllTimers = useCallback(() => {
    if (loadingTimerRef.current) { clearInterval(loadingTimerRef.current); loadingTimerRef.current = null }
    if (secondsTimerRef.current) { clearInterval(secondsTimerRef.current); secondsTimerRef.current = null }
    if (hardTimeoutRef.current) { clearTimeout(hardTimeoutRef.current); hardTimeoutRef.current = null }
  }, [])

  const startLoadingTimers = useCallback(() => {
    clearAllTimers()
    setElapsedSeconds(0)
    setShowTimeoutWarning(false)
    setHardTimeoutTriggered(false)
    setLoadingMessage(LOADING_MESSAGES[0])

    let msgIdx = 0
    loadingTimerRef.current = setInterval(() => {
      msgIdx = (msgIdx + 1) % LOADING_MESSAGES.length
      setLoadingMessage(LOADING_MESSAGES[msgIdx])
    }, 2500)

    secondsTimerRef.current = setInterval(() => {
      setElapsedSeconds(prev => prev + 1)
    }, 1000)

    hardTimeoutRef.current = setTimeout(() => {
      setHardTimeoutTriggered(true)
      setShowTimeoutWarning(true)
    }, HARD_TIMEOUT_SECONDS * 1000)
  }, [clearAllTimers])

  const showSuccessToast = useCallback((message: string) => {
    setSuccessToast(message)
    if (successToastTimerRef.current) clearTimeout(successToastTimerRef.current)
    successToastTimerRef.current = setTimeout(() => setSuccessToast(null), 4000)
  }, [])

  useEffect(() => {
    const saved = localStorage.getItem('indogov_history')
    if (saved) {
      try { setHistory(JSON.parse(saved)) } catch { /* ignore */ }
    }
    fetch('http://localhost:8000/stats')
      .then(r => r.json())
      .then(data => setStats(data))
      .catch(() => {})
  }, [])

  // Expose toast helper
  useEffect(() => {
    (window as unknown as { showSuccessToast: (msg: string) => void }).showSuccessToast = showSuccessToast
  }, [showSuccessToast])

  const navigateToSearch = useCallback((searchQuery: string) => {
    if (!searchQuery.trim()) return
    router.push(`/search?q=${encodeURIComponent(searchQuery.trim())}`)
  }, [router])

  const handleHomepageSearch = useCallback((q: string) => {
    router.push(`/search?q=${encodeURIComponent(q)}`)
  }, [router])

  const handleRetry = useCallback(() => {
    setError(null)
  }, [])

  const submitFeedback = useCallback((id: string, feedback: 'helpful' | 'not_helpful') => {
    setHistory(prev => {
      const updated = prev.map(item => item.id === id ? { ...item, feedback } : item)
      localStorage.setItem('indogov_history', JSON.stringify(updated))
      return updated
    })
  }, [])

  const clearHistory = useCallback(() => { setHistory([]); localStorage.removeItem('indogov_history') }, [])
  const deleteHistoryItem = useCallback((id: string) => {
    setHistory(prev => {
      const updated = prev.filter(item => item.id !== id)
      localStorage.setItem('indogov_history', JSON.stringify(updated))
      return updated
    })
  }, [])
  const loadFromHistory = useCallback((item: QueryHistoryItem) => {
    setQuery(item.query)
    setResult({ answer: item.answer, sources: [], confidence: 0, latency_ms: 0, metadata: {} })
    setShowHistory(false)
  }, [])

  // Show homepage content when no inline result
  const showHomepage = !result && !loading

  return (
    <AppShell showSearch>

      {/* ── Hero Section ── */}
      <div
        className="relative overflow-hidden"
        style={{
          background: 'linear-gradient(135deg, #091326 0%, #0f1f38 60%, #172d4c 100%)',
          minHeight: '480px',
          borderBottom: '2px solid var(--amber-500)',
        }}
      >
        {/* Background decorative elements */}
        <div className="absolute inset-0 pointer-events-none" aria-hidden="true">
          <div className="absolute top-0 left-1/4 w-96 h-96 bg-blue-900/10 rounded-full blur-3xl" />
          <div className="absolute bottom-0 right-1/4 w-80 h-80 bg-accent-500/10 rounded-full blur-3xl" />
          <div className="absolute inset-0" style={{ backgroundImage: 'radial-gradient(circle at 25% 25%, rgba(255,255,255,0.02) 1px, transparent 1px)', backgroundSize: '24px 24px' }} />
        </div>

        {/* Content */}
        <div className="relative max-w-5xl mx-auto px-4 sm:px-6 lg:px-8 pt-14 pb-10 text-center">
          {/* Live indicator */}
          {stats && (
            <motion.div
              initial={{ opacity: 0, y: -8 }}
              animate={{ opacity: 1, y: 0 }}
              className="flex justify-center mb-6"
            >
              <div className="inline-flex items-center gap-2 px-3 py-1.5 bg-emerald-500/20 border border-emerald-400/30 rounded-full text-xs font-semibold text-emerald-300">
                <div className="w-2 h-2 bg-emerald-400 rounded-full animate-pulse" />
                {stats.total_chunks.toLocaleString('id-ID')} chunk terindeks &middot; {stats.unique_files} dokumen
              </div>
            </motion.div>
          )}

          {/* Logo */}
          <motion.div
            initial={{ opacity: 0, scale: 0.9 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ duration: 0.5 }}
            className="flex justify-center mb-6"
          >
            <img
              src="/logo.svg"
              alt="IndoGovRAG"
              className="h-14 w-auto object-contain drop-shadow-lg"
            />
          </motion.div>

          {/* Headline */}
          <motion.h1
            initial={{ opacity: 0, y: 16 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.1 }}
            className="font-serif text-3xl sm:text-4xl md:text-5xl font-bold text-white mb-4 leading-tight"
          >
            Pencarian Regulasi Indonesia<br className="hidden sm:block" />
            <span className="text-amber-400">yang Akurat & Terpercaya</span>
          </motion.h1>

          {/* Subhead */}
          <motion.p
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.2 }}
            className="text-base sm:text-lg text-white/70 max-w-2xl mx-auto mb-8 leading-relaxed"
          >
            Telusuri ribuan dokumen hukum Indonesia dengan AI — UU, PP, Perpres, Permen, dan lainnya
          </motion.p>

          {/* Search bar */}
          <motion.div
            initial={{ opacity: 0, y: 12 }}
            animate={{ opacity: 1, y: 0 }}
            transition={{ duration: 0.5, delay: 0.3 }}
          >
            <HeroSearchBar onSearch={handleHomepageSearch} />
          </motion.div>

          {/* Rotating legal philosophy quote */}
          <LegalQuoteBanner />
        </div>
      </div>

      {/* ── Stats Bar ── */}
      <StatsBar />

      {/* ── Main content ── */}
      <div className="max-w-6xl mx-auto px-4 sm:px-6 lg:px-8 py-12 space-y-14">

        {/* Loading warnings */}
        {loading && showTimeoutWarning && (
          <TimeoutWarning elapsed={elapsedSeconds} onDismiss={() => setShowTimeoutWarning(false)} />
        )}

        {/* Inline search loading */}
        {loading && <InlineLoadingState />}

        {/* Error state */}
        {error && !loading && (
          <motion.div
            initial={{ opacity: 0, scale: 0.97, y: 8 }}
            animate={{ opacity: 1, scale: 1, y: 0 }}
            transition={{ duration: 0.3 }}
            className="max-w-3xl mx-auto mb-6"
            role="alert"
          >
            <div className="p-5 sm:p-6 bg-white border-2 border-red-200 rounded-2xl shadow-sm">
              <div className="flex items-start gap-3 mb-3">
                <div className="w-10 h-10 bg-red-100 rounded-xl flex items-center justify-center flex-shrink-0">
                  {error.toLowerCase().includes('fetch') || error.toLowerCase().includes('network') || error.toLowerCase().includes('failed') || error.toLowerCase().includes('econnrefused') ? (
                    <WifiOff className="w-5 h-5 text-red-600" />
                  ) : (
                    <AlertTriangle className="w-5 h-5 text-red-600" />
                  )}
                </div>
                <div>
                  <p className="font-bold text-red-800 text-sm sm:text-base">
                    {error.toLowerCase().includes('fetch') || error.toLowerCase().includes('network') || error.toLowerCase().includes('econnrefused')
                      ? 'Tidak dapat terhubung ke server'
                      : 'Terjadi kesalahan server'
                    }
                  </p>
                  <p className="text-xs text-red-600 mt-0.5">
                    {error.toLowerCase().includes('fetch') || error.toLowerCase().includes('network') || error.toLowerCase().includes('econnrefused')
                      ? 'Pastikan server backend berjalan di http://localhost:8000'
                      : 'Server tidak dapat memproses permintaan Anda'
                    }
                  </p>
                </div>
              </div>
              <div className="flex gap-2 mt-4">
                <button
                  onClick={handleRetry}
                  className="inline-flex items-center gap-1.5 px-4 py-2 bg-red-600 hover:bg-red-700 active:scale-95 text-white rounded-xl text-xs font-semibold transition-all"
                >
                  <RotateCcw className="w-3.5 h-3.5" /> Coba lagi
                </button>
              </div>
            </div>
          </motion.div>
        )}

        {/* Inline result (homepage inline search) */}
        {result && !loading && (
          <div className="max-w-4xl mx-auto space-y-4 sm:space-y-6 px-3 sm:px-0">

            <LegalDisclaimer topic={result.metadata?.topic || 'umum'} isHighStakes={result.metadata?.is_high_stakes || false} />

            {result.metadata?.status === 'bm25_fallback' && (
              <FallbackNotice onRetry={handleRetry} />
            )}

            {result.metadata?.warnings?.some((w: string) => w.includes('peraturan terbaru') || w.includes('tidak berlaku')) && <SupersededBanner />}

            <ConfidenceWarning confidence={result.confidence} />
            {result.metadata?.chunks_retrieved === 0 && <ZeroChunksWarning />}

            <motion.div
              initial={{ opacity: 0, y: 16 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.4 }}
              className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-md"
              role="article"
            >
              <div className="flex flex-col sm:flex-row items-start sm:items-center justify-between gap-3 mb-5">
                <div className="flex items-center gap-2.5">
                  <div className="w-9 h-9 bg-indigo-100 rounded-xl flex items-center justify-center">
                    <Zap className="w-5 h-5 text-indigo-600" />
                  </div>
                  <h2 className="text-lg sm:text-xl font-bold text-slate-900">Jawaban</h2>
                </div>
                <div className="flex flex-wrap items-center gap-2">
                  {result.from_cache && (
                    <span className="px-2.5 py-1 bg-blue-100 text-blue-700 rounded-full text-xs font-semibold">Cached</span>
                  )}
                  <span className="px-2.5 py-1 bg-purple-100 text-purple-700 rounded-full text-xs font-semibold">Hibrida</span>
                  {hardTimeoutTriggered && (
                    <span className="px-2.5 py-1 bg-amber-100 text-amber-700 rounded-full text-xs font-semibold">Mode Dasar</span>
                  )}
                  <ConfidenceBadge confidence={result.confidence} size="sm" />
                </div>
              </div>
              <p className="text-base md:text-lg text-slate-700 leading-relaxed whitespace-pre-wrap">{result.answer}</p>

              <div className="mt-5 pt-5 border-t border-slate-100 grid grid-cols-2 sm:grid-cols-4 gap-3">
                <div className="bg-slate-50 rounded-xl p-3 text-center">
                  <p className="text-xs text-slate-500 font-medium mb-1">Confidence</p>
                  <p className="text-2xl font-bold text-indigo-600">{(result.confidence * 100).toFixed(0)}%</p>
                </div>
                <div className="bg-slate-50 rounded-xl p-3 text-center">
                  <p className="text-xs text-slate-500 font-medium mb-1">Waktu Respons</p>
                  <p className="text-2xl font-bold text-indigo-600">{result.latency_ms}ms</p>
                </div>
                {result.metadata?.chunks_retrieved && (
                  <div className="bg-slate-50 rounded-xl p-3 text-center">
                    <p className="text-xs text-slate-500 font-medium mb-1">Chunks</p>
                    <p className="text-2xl font-bold text-indigo-600">{result.metadata.chunks_retrieved}</p>
                  </div>
                )}
                {result.metadata?.expansion_used !== undefined && (
                  <div className="bg-slate-50 rounded-xl p-3 text-center">
                    <p className="text-xs text-slate-500 font-medium mb-1">Fitur</p>
                    <div className="flex flex-wrap gap-1 mt-1 justify-center">
                      {result.metadata.expansion_used && <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded text-xs font-semibold">Expand</span>}
                      {result.metadata.reranking_used && <span className="px-2 py-0.5 bg-purple-100 text-purple-700 rounded text-xs font-semibold">Rerank</span>}
                    </div>
                  </div>
                )}
              </div>
            </motion.div>

            {result.sources && result.sources.length > 0 ? (
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                transition={{ duration: 0.4, delay: 0.1 }}
                className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-md"
              >
                <div className="flex items-center gap-2.5 mb-4">
                  <div className="w-9 h-9 bg-green-100 rounded-xl flex items-center justify-center">
                    <Shield className="w-5 h-5 text-green-600" />
                  </div>
                  <h3 className="text-lg font-bold text-slate-900">Referensi Sumber</h3>
                  <span className="ml-auto text-xs bg-green-100 text-green-700 px-2 py-0.5 rounded-full font-semibold">
                    {result.sources.length} sumber
                  </span>
                </div>
                <SourceCardList sources={result.sources} />
                <details className="mt-4">
                  <summary className="text-sm text-slate-500 cursor-pointer hover:text-indigo-600 transition-colors font-medium focus:outline-none focus-visible:text-indigo-600">
                    Lihat daftar sumber
                  </summary>
                  <div className="mt-3 space-y-2">
                    {result.sources.map((source, idx) => (
                      <div key={idx} className="flex items-start gap-3 text-slate-700 p-3 bg-slate-50 rounded-xl min-h-[44px]">
                        <div className="w-6 h-6 bg-indigo-100 text-indigo-600 rounded-full flex items-center justify-center text-sm font-semibold flex-shrink-0 mt-0.5">
                          {idx + 1}
                        </div>
                        <span className="text-sm sm:text-base leading-snug">{source}</span>
                      </div>
                    ))}
                  </div>
                </details>
              </motion.div>
            ) : (
              <motion.div
                initial={{ opacity: 0, y: 16 }}
                animate={{ opacity: 1, y: 0 }}
                className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-md text-center"
              >
                <div className="w-12 h-12 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-3">
                  <Shield className="w-6 h-6 text-slate-300" />
                </div>
                <p className="text-sm font-semibold text-slate-600 mb-1">Tidak ada sumber tersedia</p>
                <p className="text-xs text-slate-400">Informasi ditampilkan tanpa referensi dokumen.</p>
              </motion.div>
            )}

            {/* Feedback */}
            {result && (
              <div className="flex flex-col sm:flex-row sm:items-center justify-between gap-3 bg-white rounded-2xl border border-slate-200 p-4">
                <p className="text-sm text-slate-600 font-medium">Apakah jawaban ini membantu?</p>
                <div className="flex gap-2">
                  <button
                    onClick={() => {
                      const item = history.find(h => h.query === query)
                      if (item) submitFeedback(item.id, 'helpful')
                    }}
                    className="px-4 py-2 bg-green-50 hover:bg-green-100 text-green-700 rounded-xl text-sm font-semibold transition-colors active:scale-95 flex items-center gap-1.5"
                  >
                    <TrendingUp className="w-4 h-4" /> Ya, membantu
                  </button>
                  <button
                    onClick={() => {
                      const item = history.find(h => h.query === query)
                      if (item) submitFeedback(item.id, 'not_helpful')
                    }}
                    className="px-4 py-2 bg-red-50 hover:bg-red-100 text-red-700 rounded-xl text-sm font-semibold transition-colors active:scale-95 flex items-center gap-1.5"
                  >
                    <X className="w-4 h-4" /> Tidak
                  </button>
                </div>
              </div>
            )}
          </div>
        )}

        {/* ── Homepage sections (shown when no inline result) ── */}
        {showHomepage && (
          <>
            {/* Feature Cards */}
            <section>
              <div className="text-center mb-8">
                <h2 className="text-2xl sm:text-3xl font-bold text-slate-900 font-serif mb-2">
                  Mengapa IndoGovRAG?
                </h2>
                <p className="text-slate-500 text-sm sm:text-base max-w-md mx-auto">
                  Platform penelusuran regulasi yang dirancang khusus untuk kebutuhan riset hukum Indonesia
                </p>
              </div>
              <div className="grid grid-cols-1 sm:grid-cols-3 gap-5">
                {FEATURE_CARDS.map((feature, idx) => (
                  <motion.div
                    key={feature.title}
                    initial={{ opacity: 0, y: 20 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.4, delay: idx * 0.08 }}
                    className={`bg-white rounded-2xl border ${feature.color} p-6 hover:shadow-lg transition-all duration-200 group`}
                  >
                    <div className={`w-12 h-12 ${feature.iconBg} rounded-xl flex items-center justify-center mb-4 text-white shadow-sm group-hover:scale-105 transition-transform`}>
                      {feature.icon}
                    </div>
                    <div className="flex items-center gap-2 mb-2">
                      <h4 className="text-base font-bold text-slate-900">{feature.title}</h4>
                      <span className={`ml-auto text-[10px] font-semibold px-2 py-0.5 rounded-full bg-white/60 ${feature.accent}`}>
                        {feature.tag}
                      </span>
                    </div>
                    <p className="text-sm text-slate-600 leading-relaxed">{feature.description}</p>
                  </motion.div>
                ))}
              </div>
            </section>

            {/* Trending / Sample Results */}
            <section>
              <div className="flex items-center justify-between mb-6">
                <div>
                  <h2 className="text-xl sm:text-2xl font-bold text-slate-900 font-serif">
                    Trending Regulations
                  </h2>
                  <p className="text-slate-500 text-sm mt-1">
                    Dokumen populer yang paling sering diakses
                  </p>
                </div>
                <button
                  onClick={() => router.push('/search')}
                  className="px-4 py-2 bg-indigo-50 hover:bg-indigo-100 border border-indigo-200 text-indigo-700 rounded-xl text-xs font-semibold transition-all"
                >
                  Lihat semua &rarr;
                </button>
              </div>

              <div className="grid grid-cols-1 sm:grid-cols-3 gap-4">
                {SAMPLE_RESULTS.map((sample, idx) => (
                  <motion.div
                    key={sample.jenis + sample.nomor + sample.tahun}
                    initial={{ opacity: 0, y: 12 }}
                    animate={{ opacity: 1, y: 0 }}
                    transition={{ duration: 0.35, delay: idx * 0.07 }}
                    className="bg-white rounded-2xl border border-slate-200 p-5 hover:shadow-md hover:border-indigo-200 transition-all cursor-pointer group"
                    onClick={() => navigateToSearch(`${sample.jenis} ${sample.nomor} ${sample.tahun}`)}
                  >
                    <div className="flex items-center gap-2 mb-3">
                      <span className={`doc-badge ${sample.jenis}`}>{sample.jenis}</span>
                      <span className="text-xs font-medium text-slate-500">No. {sample.nomor}/{sample.tahun}</span>
                      <span className={`ml-auto status-badge ${sample.status}`}>Berlaku</span>
                    </div>
                    <h4 className="text-sm font-bold text-slate-900 leading-snug mb-2 group-hover:text-indigo-700 transition-colors">
                      {sample.title}
                    </h4>
                    <p className="text-xs text-slate-500 mb-2">{sample.instansi}</p>
                    <p className="text-xs text-slate-600 leading-relaxed line-clamp-2">{sample.excerpt}</p>
                    <div className="mt-3 flex items-center gap-1.5">
                      <span className="px-2 py-0.5 bg-slate-100 text-slate-600 rounded text-[10px] font-semibold">{sample.tag}</span>
                      <span className="text-xs text-indigo-600 ml-auto group-hover:underline font-semibold">Cari &rarr;</span>
                    </div>
                  </motion.div>
                ))}
              </div>
            </section>

            {/* Popular Searches */}
            <section className="text-center">
              <h2 className="text-lg font-bold text-slate-900 font-serif mb-4">
                Pencarian Populer
              </h2>
              <div className="flex flex-wrap gap-2 justify-center mb-4">
                {POPULAR_SEARCHES.map((kw) => (
                  <button
                    key={kw}
                    onClick={() => navigateToSearch(kw)}
                    className="px-4 py-2.5 bg-white hover:bg-indigo-50 border border-slate-200 hover:border-indigo-300 text-slate-700 hover:text-indigo-700 rounded-xl text-sm font-medium transition-all active:scale-95 shadow-sm"
                  >
                    <Search className="w-3.5 h-3.5 inline-block mr-1.5 text-slate-400" />
                    {kw}
                  </button>
                ))}
              </div>
              <p className="text-xs text-slate-400">
                Tekan Enter atau klik tombol Cari untuk memulai pencarian
              </p>
            </section>
          </>
        )}
      </div>

      {/* ── History Button (floating) ── */}
      {history.length > 0 && (
        <button
          onClick={() => setShowHistory(true)}
          className="fixed bottom-20 right-5 z-40 w-12 h-12 bg-indigo-600 hover:bg-indigo-700 active:scale-95 text-white rounded-full shadow-lg flex items-center justify-center transition-all hover:shadow-xl md:bottom-24"
          aria-label="Riwayat pencarian"
        >
          <History className="w-5 h-5" />
          <span className="absolute -top-1 -right-1 w-5 h-5 bg-red-500 rounded-full text-[9px] font-bold flex items-center justify-center">
            {history.length > 9 ? '9+' : history.length}
          </span>
        </button>
      )}

      {/* History Drawer */}
      {showHistory && (
        <HistoryDrawer
          history={history}
          onClear={clearHistory}
          onDelete={deleteHistoryItem}
          onLoad={loadFromHistory}
          onClose={() => setShowHistory(false)}
        />
      )}

      {/* Success Toast */}
      {successToast && (
        <div className="fixed bottom-24 left-1/2 -translate-x-1/2 z-50 px-4 py-3 bg-emerald-600 text-white rounded-xl shadow-xl text-sm font-semibold flex items-center gap-2 animate-in fade-in slide-in-from-bottom-4">
          <CheckCircle className="w-4 h-4" />
          {successToast}
        </div>
      )}

      {/* Philosophical footer with legal quote */}
      <PhilosophyFooter />

    </AppShell>
  )
}