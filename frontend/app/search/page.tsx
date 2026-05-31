'use client'

import { useSearchParams, useRouter } from 'next/navigation'
import { useQuery } from '@tanstack/react-query'
import { useCallback, useState, useEffect, Suspense } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Search, ArrowLeft, SlidersHorizontal, X, Settings } from 'lucide-react'
import { useSearchStore } from '../lib/searchStore'
import { type QueryResponse, type SearchDocument } from '../lib/types'
import SearchFilters from './components/SearchFilters'
import ActiveFilters from './components/ActiveFilters'
import SearchSummary from './components/SearchSummary'
import SearchResultCard from './components/SearchResultCard'
import Pagination from './components/Pagination'
import SkeletonLoader from './components/SkeletonLoader'
import ConfidenceGauge from './components/ConfidenceGauge'

const API = process.env.NEXT_PUBLIC_API_URL ?? 'http://localhost:8000'
const PER_PAGE = 10

// ── Parse a source string into SearchDocument ───────────────────
function parseSource(source: string, index: number): SearchDocument {
  // Sources look like: "UU No.11 Tahun 2020 tentang..." or just "UU 11/2020"
  const text = source.trim()

  // Detect jenis from the start of the string
  const jenisPatterns = ['UU', 'PP', 'Perpres', 'Permen', 'Perda', 'POJK', 'SE']
  let jenis = 'Dokumen'
  let remainder = text

  for (const j of jenisPatterns) {
    if (text.startsWith(j) || text.startsWith(j + ' ') || text.startsWith(j + ' No') || text.startsWith(j + '.')) {
      jenis = j
      remainder = text.slice(j.length).trim()
      break
    }
  }

  // Extract tahun (year): 4-digit number starting with 19 or 20
  const tahunMatch = remainder.match(/\b(19\d{2}|20\d{2})\b/)
  const tahun = tahunMatch ? parseInt(tahunMatch[1], 10) : 0

  // Extract nomor: "No.123" or "Nomor 45" or standalone number before tahun
  const nomorMatch = remainder.match(/(?:No\.?\s*|Nomor\s*|#?\s*)([\d]+)/)
  const nomor = nomorMatch ? nomorMatch[1] : ''

  // Instansi detection
  const instansiPatterns: [RegExp, string][] = [
    [/kemenkumham|kemen\.?\s*hukum|kumham/i, 'Kementerian Hukum & HAM'],
    [/kemenkeu|kemen\.?\s*keu/i, 'Kementerian Keuangan'],
    [/kemenkes|kemen\.?\s*kese/i, 'Kementerian Kesehatan'],
    [/kemenag|kemen\.?\s*agama/i, 'Kementerian Agama'],
    [/kemnaker|kemen\.?\s*nakal|kemen\.?\s*kerja/i, 'Kementerian Ketenagakerjaan'],
    [/ojk|otoritas\s*jasa/i, 'Otoritas Jasa Keuangan'],
    [/bkpm/i, 'BKPM / Investasi'],
    [/presiden|kepres/i, 'Presiden RI'],
    [/mpr|dpd/i, 'MPR/DPD'],
    [/dpr|dprd/i, 'DPR/DPRD'],
  ]
  let instansi = ''
  for (const [re, label] of instansiPatterns) {
    if (re.test(text)) { instansi = label; break }
  }

  // Title: strip "tentang", "mengenai" clauses, clean up
  let title = text
    .replace(/\bTENTANG\b/gi, '—')
    .replace(/\bMENGENAI\b/gi, '—')
    .replace(/\b tentang\b/gi, ' —')
    .replace(/\b mengenai\b/gi, ' —')
    .replace(/\bNo\.?\s*[\d]+\/[\d]+\s*/g, '')
    .replace(/\(.*?\)/g, '')
    .trim()
  if (title.length > 100) title = title.slice(0, 97) + '...'
  if (!title) title = `${jenis}${nomor ? ' No.' + nomor : ''}${tahun ? ' Tahun ' + tahun : ''}`

  // Excerpt: use answer-like cleaned-up text
  const excerpt = text
    .replace(/\s+/g, ' ')
    .slice(0, 280)
    .trim()

  return {
    id: `source-${index}`,
    title,
    jenis,
    tahun,
    nomor: nomor ? `${jenis} No.${nomor}` : '',
    instansi,
    status: 'berlaku',
    excerpt,
    relevance_score: Math.max(0.3, 1 - index * 0.08),
    citations: 0,
  }
}

// ── Fetch search results ─────────────────────────────────────────
async function fetchSearchResults(query: string, signal: AbortSignal): Promise<QueryResponse> {
  const headers: Record<string, string> = {
    'Content-Type': 'application/json',
  }

  if (typeof window !== 'undefined') {
    const customGroq = localStorage.getItem('custom_groq_api_key')
    const customGemini = localStorage.getItem('custom_gemini_api_key')
    if (customGroq) headers['X-Custom-Groq-Key'] = customGroq.trim()
    if (customGemini) headers['X-Custom-Gemini-Key'] = customGemini.trim()
  }

  const resp = await fetch(`${API}/query`, {
    method: 'POST',
    headers,
    body: JSON.stringify({ query, options: { top_k: 30 } }),
    signal,
  })
  if (!resp.ok) throw new Error(`API error ${resp.status}`)
  return resp.json() as Promise<QueryResponse>
}

// ── Empty state ──────────────────────────────────────────────────
function EmptyState({ query }: { query: string }) {
  const router = useRouter()
  return (
    <div className="flex flex-col items-center justify-center py-24 text-center">
      <div
        className="w-20 h-20 rounded-3xl flex items-center justify-center mb-6"
        style={{ backgroundColor: '#eef2ff' }}
      >
        <Search className="w-10 h-10" style={{ color: '#818cf8' }} />
      </div>
      <h2 className="text-xl font-semibold text-slate-700 mb-2">
        {query ? 'Tidak ada hasil ditemukan' : 'Masukkan kata kunci pencarian'}
      </h2>
      <p className="text-sm text-slate-400 max-w-sm">
        {query
          ? `Tidak ada dokumen yang cocok dengan "${query}". Coba kata kunci lain atau ubah filter.`
          : 'Gunakan bilah pencarian di atas untuk mencari dokumen regulasi pemerintah Indonesia.'}
      </p>
      {!query && (
        <button
          onClick={() => router.push('/')}
          className="mt-6 flex items-center gap-2 px-5 py-2.5 text-white rounded-xl text-sm font-medium transition-colors"
          style={{ backgroundColor: '#1e3a5f' }}
          onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.backgroundColor = '#2c4a6e' }}
          onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.backgroundColor = '#1e3a5f' }}
        >
          <ArrowLeft className="w-4 h-4" />
          Kembali ke Beranda
        </button>
      )}
    </div>
  )
}

// ── Error state ──────────────────────────────────────────────────
function ErrorState({ message }: { message: string }) {
  return (
    <div
      className="rounded-xl p-6 text-center border"
      style={{ backgroundColor: '#fef2f2', borderColor: '#fecaca' }}
    >
      <p className="font-semibold mb-1" style={{ color: '#b91c1c' }}>Terjadi kesalahan</p>
      <p className="text-sm" style={{ color: '#ef4444' }}>{message}</p>
    </div>
  )
}

// ── Mobile filter drawer ──────────────────────────────────────────
function FilterDrawer({ open, onClose }: { open: boolean; onClose: () => void }) {
  return (
    <AnimatePresence>
      {open && (
        <>
          {/* Overlay */}
          <motion.div
            key="overlay"
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            exit={{ opacity: 0 }}
            transition={{ duration: 0.2 }}
            className="drawer-overlay"
            onClick={onClose}
          />
          {/* Panel */}
          <motion.div
            key="panel"
            initial={{ x: '100%' }}
            animate={{ x: 0 }}
            exit={{ x: '100%' }}
            transition={{ duration: 0.25, ease: [0.4, 0, 0.2, 1] }}
            className="drawer-panel"
          >
            <div className="flex items-center justify-between p-4 border-b border-slate-200 sticky top-0 bg-white z-10">
              <h2 className="text-sm font-semibold text-slate-900">Filter Pencarian</h2>
              <button
                onClick={onClose}
                className="p-2 rounded-lg hover:bg-slate-100 transition-colors"
                aria-label="Tutup filter"
              >
                <X className="w-5 h-5 text-slate-500" />
              </button>
            </div>
            <div className="p-4">
              <SearchFilters />
            </div>
          </motion.div>
        </>
      )}
    </AnimatePresence>
  )
}

// ── Main page ─────────────────────────────────────────────────────
function SearchPageInner() {
  const searchParams = useSearchParams()
  const router       = useRouter()
  const store        = useSearchStore()
  const [drawerOpen, setDrawerOpen] = useState(false)

  const query = (searchParams.get('q') ?? '').trim()
  const page  = parseInt(searchParams.get('page') ?? '1', 10)

  // Sync URL params → Zustand store
  useEffect(() => {
    store.setQuery(query)
    store.setPage(page)
    const jenisParam = searchParams.get('jenis')
    if (jenisParam) {
      store.setJenis(jenisParam.split(',').filter(Boolean) as Parameters<typeof store.setJenis>[0])
    }
    const statusParam = searchParams.get('status')
    if (statusParam) store.setStatus(statusParam as Parameters<typeof store.setStatus>[0])
    const tahunDariParam = searchParams.get('tahun_dari')
    const tahunSampaiParam = searchParams.get('tahun_sampai')
    if (tahunDariParam || tahunSampaiParam) {
      store.setTahunRange(
        tahunDariParam ? parseInt(tahunDariParam) : null,
        tahunSampaiParam ? parseInt(tahunSampaiParam) : null,
      )
    }
    const instansiParam = searchParams.get('instansi')
    if (instansiParam) store.setInstansi(instansiParam)
    const sortParam = searchParams.get('sort')
    if (sortParam) store.setSort(sortParam as Parameters<typeof store.setSort>[0])
  }, [searchParams])

  const { data, isLoading, isError, error } = useQuery<QueryResponse, Error>({
    queryKey: ['search', query],
    queryFn: ({ signal }) => fetchSearchResults(query, signal),
    enabled: query.length > 0,
    staleTime: 30_000,
  })

  // Transform API sources → SearchDocument[]
  const allDocuments: SearchDocument[] = (data?.sources ?? []).map((s, i) => parseSource(s, i))

  // Apply client-side filters (mirrors Zustand store state)
  const filteredDocuments = allDocuments.filter(doc => {
    if (store.jenis.length > 0 && !store.jenis.includes(doc.jenis as Parameters<typeof store.setJenis>[0][number])) return false
    if (store.status !== 'semua' && store.status !== 'berlaku' && doc.status !== store.status) return false
    if (store.tahunDari !== null && doc.tahun !== null && doc.tahun < store.tahunDari) return false
    if (store.tahunSampai !== null && doc.tahun !== null && doc.tahun > store.tahunSampai) return false
    if (store.instansi && !doc.instansi.toLowerCase().includes(store.instansi.toLowerCase())) return false
    return true
  })

  // Sort
  if (store.sort === 'terbaru') {
    filteredDocuments.sort((a, b) => (b.tahun ?? 0) - (a.tahun ?? 0))
  } else if (store.sort === 'terlama') {
    filteredDocuments.sort((a, b) => (a.tahun ?? 9999) - (b.tahun ?? 9999))
  }

  // Paginate
  const total      = filteredDocuments.length
  const totalPages = Math.max(1, Math.ceil(total / PER_PAGE))
  const safePage   = Math.min(Math.max(1, page), totalPages)
  const pageDocs   = filteredDocuments.slice((safePage - 1) * PER_PAGE, safePage * PER_PAGE)

  const handlePageChange = useCallback((p: number) => {
    const params = new URLSearchParams(searchParams.toString())
    params.set('page', String(p))
    router.push(`?${params.toString()}`, { scroll: false })
  }, [router, searchParams])

  const handleSearchSubmit = useCallback((value: string) => {
    if (!value.trim()) return
    const params = new URLSearchParams()
    params.set('q', value.trim())
    router.push(`?${params.toString()}`)
  }, [router])

  const handleConfidenceChange = useCallback((c: number) => {
    store.setConfidence(c)
  }, [store])

  return (
    <div className="min-h-screen" style={{ backgroundColor: '#f8fafc' }}>
      {/* ── Sticky top nav ───────────────────────────────────── */}
      <header
        className="sticky top-0 z-40 bg-white border-b border-slate-200"
        style={{ boxShadow: '0 1px 3px rgba(0,0,0,0.06)' }}
      >
        <div className="max-w-screen-xl mx-auto px-4 lg:px-6 py-3 flex items-center gap-3">
          <button
            onClick={() => router.push('/')}
            className="flex items-center gap-1.5 text-sm text-slate-500 hover:text-indigo-700 transition-colors shrink-0"
          >
            <ArrowLeft className="w-4 h-4" />
            <span className="hidden sm:inline">Beranda</span>
          </button>
          <div className="w-px h-5 bg-slate-200 shrink-0" />
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
            <input
              type="search"
              defaultValue={query}
              placeholder="Cari regulasi, UU, PP, Perpres..."
              className="w-full pl-10 pr-4 py-2.5 rounded-xl text-sm transition-all outline-none"
              style={{
                backgroundColor: '#f8fafc',
                border: '1px solid #e2e8f0',
              }}
              onFocus={e => {
                (e.currentTarget as HTMLInputElement).style.borderColor = '#6366f1'
                ;(e.currentTarget as HTMLInputElement).style.boxShadow = '0 0 0 3px rgba(99,102,241,0.1)'
              }}
              onBlur={e => {
                (e.currentTarget as HTMLInputElement).style.borderColor = '#e2e8f0'
                ;(e.currentTarget as HTMLInputElement).style.boxShadow = 'none'
              }}
              onKeyDown={e => {
                if (e.key === 'Enter') handleSearchSubmit((e.target as HTMLInputElement).value)
              }}
            />
          </div>
          {/* Mobile filter button */}
          <button
            className="lg:hidden flex items-center gap-1.5 px-3 py-2 rounded-xl text-sm font-medium border transition-all shrink-0"
            style={{ borderColor: '#e2e8f0', color: '#475569' }}
            onClick={() => setDrawerOpen(true)}
          >
            <SlidersHorizontal className="w-4 h-4" />
            <span className="hidden sm:inline">Filter</span>
          </button>
          <span className="hidden md:inline text-xs text-slate-400 shrink-0">IndoGovRAG</span>
          <button
            onClick={() => useSearchStore.getState().setSettingsOpen(true)}
            className="flex items-center justify-center w-9 h-9 rounded-xl text-slate-500 hover:text-slate-950 hover:bg-slate-100 transition-all focus:outline-none shrink-0"
            title="Pengaturan API Key LLM"
          >
            <Settings className="w-4 h-4" />
          </button>
        </div>
      </header>

      {/* ── Page content ──────────────────────────────────────── */}
      <div className="max-w-screen-xl mx-auto px-4 lg:px-6 py-6">
        {!query ? (
          <EmptyState query={query} />
        ) : (
          <div className="search-layout">
            {/* Left sidebar — desktop only */}
            <aside className="left-sidebar hidden lg:block">
              <SearchFilters />
            </aside>

            {/* Main content */}
            <main className="main-content min-w-0">
              <SearchSummary
                total={total}
                query={query}
                timeMs={data?.latency_ms}
                loading={isLoading}
                confidence={data?.confidence}
                onConfidenceChange={handleConfidenceChange}
              />

              {isLoading ? (
                <SkeletonLoader count={5} />
              ) : isError ? (
                <ErrorState message={error?.message ?? 'Gagal memuat hasil pencarian.'} />
              ) : pageDocs.length === 0 ? (
                <EmptyState query={query} />
              ) : (
                <>
                  {/* Result cards */}
                  <div className="space-y-3">
                    <AnimatePresence>
                      {pageDocs.map((doc, i) => (
                        <SearchResultCard key={doc.id} doc={doc} index={i} />
                      ))}
                    </AnimatePresence>
                  </div>

                  {/* AI Answer card */}
                  {data?.answer && (
                    <motion.div
                      initial={{ opacity: 0, y: 16 }}
                      animate={{ opacity: 1, y: 0 }}
                      transition={{ duration: 0.4, delay: 0.15 }}
                      className="mt-6 rounded-2xl border overflow-hidden"
                      style={{ borderColor: '#fde68a', boxShadow: '0 2px 8px rgba(180,83,9,0.08)' }}
                    >
                      <div
                        className="flex items-center gap-3 px-5 py-4"
                        style={{ backgroundColor: '#fffbeb', borderBottom: '1px solid #fde68a' }}
                      >
                        <div
                          className="w-8 h-8 rounded-xl flex items-center justify-center shrink-0"
                          style={{ backgroundColor: '#fef3c7' }}
                        >
                          <svg className="w-4 h-4" style={{ color: '#b45309' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2}>
                            <path strokeLinecap="round" strokeLinejoin="round" d="M13 10V3L4 14h7v7l9-11h-7z" />
                          </svg>
                        </div>
                        <h2 className="font-semibold text-slate-900 text-sm">Jawaban AI</h2>
                        {data.confidence !== undefined && (
                          <div className="ml-auto">
                            <ConfidenceGauge confidence={data.confidence} latencyMs={data.latency_ms} size="sm" />
                          </div>
                        )}
                      </div>
                      <div className="px-5 py-5 bg-white">
                        <p
                          className="text-base leading-relaxed"
                          style={{ color: '#374151', fontFamily: "var(--font-serif), 'DM Serif Display', Georgia, serif" }}
                        >
                          {data.answer}
                        </p>

                        {/* Sources */}
                        {data.sources && data.sources.length > 0 && (
                          <div className="mt-4 pt-4" style={{ borderTop: '1px solid #fef3c7' }}>
                            <p className="text-xs font-semibold text-slate-500 uppercase tracking-wider mb-2">
                              Sumber Referensi
                            </p>
                            <div className="flex flex-wrap gap-2">
                              {data.sources.slice(0, 8).map((src, i) => (
                                <span key={i} className="doc-badge PP">
                                  {src.length > 50 ? src.slice(0, 47) + '...' : src}
                                </span>
                              ))}
                            </div>
                          </div>
                        )}
                      </div>
                    </motion.div>
                  )}

                  {/* Pagination */}
                  <Pagination
                    total={total}
                    perPage={PER_PAGE}
                    currentPage={safePage}
                    onPageChange={handlePageChange}
                  />
                </>
              )}
            </main>

            {/* Right sidebar — desktop only */}
            <aside className="right-sidebar hidden lg:block">
              <ActiveFilters />
            </aside>
          </div>
        )}
      </div>

      {/* Mobile filter drawer */}
      <FilterDrawer open={drawerOpen} onClose={() => setDrawerOpen(false)} />
    </div>
  )
}

// Wrap in Suspense for useSearchParams
export default function SearchPage() {
  return (
    <Suspense fallback={
      <div className="min-h-screen flex items-center justify-center" style={{ backgroundColor: '#f8fafc' }}>
        <div className="spinner spinner-lg" />
      </div>
    }>
      <SearchPageInner />
    </Suspense>
  )
}