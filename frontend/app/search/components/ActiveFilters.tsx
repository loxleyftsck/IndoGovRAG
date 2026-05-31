'use client'

import { motion, AnimatePresence } from 'framer-motion'
import { X, Lightbulb, TrendingUp, BookOpen } from 'lucide-react'
import { useSearchStore, type DocumentType } from '../../lib/searchStore'
import Card from '../../components/ui/Card'

const SUGGESTIONS = [
  { label: 'Syarat pendirian PT', icon: TrendingUp },
  { label: 'Biaya pembuatan paspor', icon: BookOpen },
  { label: 'Kategori pajak UMKM', icon: Lightbulb },
  { label: 'Izin gangguan (HO)', icon: Lightbulb },
  { label: 'Tenaga kerja asing', icon: TrendingUp },
]

function Chip({ label, onRemove }: { label: string; onRemove: () => void }) {
  return (
    <motion.span
      initial={{ scale: 0.85, opacity: 0 }}
      animate={{ scale: 1, opacity: 1 }}
      exit={{ scale: 0.85, opacity: 0 }}
      transition={{ duration: 0.15 }}
      className="inline-flex items-center gap-1.5 pl-3 pr-1.5 py-1 bg-navy-50 border border-navy-200 rounded-full text-xs font-semibold text-navy-800"
    >
      {label}
      <button
        onClick={onRemove}
        className="w-4 h-4 flex items-center justify-center rounded-full hover:bg-navy-200 transition-colors"
        aria-label={`Remove ${label}`}
      >
        <X className="w-2.5 h-2.5" />
      </button>
    </motion.span>
  )
}

export default function ActiveFilters() {
  const store = useSearchStore()

  const chips: { label: string; remove: () => void }[] = [
    ...store.jenis.map(j => ({
      label: j,
      remove: () => { store.setJenis(store.jenis.filter(x => x !== j)) },
    })),
    ...(store.status !== 'berlaku' ? [{
      label: store.status === 'semua' ? 'Semua status' : store.status,
      remove: () => store.setStatus('berlaku'),
    }] : []),
    ...(store.tahunDari !== null || store.tahunSampai !== null ? [{
      label: `${store.tahunDari ?? '?'} – ${store.tahunSampai ?? '?'}`,
      remove: () => store.setTahunRange(null, null),
    }] : []),
    ...(store.instansi ? [{
      label: store.instansi,
      remove: () => store.setInstansi(''),
    }] : []),
    ...(store.sort !== 'relevansi' ? [{
      label: store.sort,
      remove: () => store.setSort('relevansi'),
    }] : []),
  ]

  const handleSuggestion = (q: string) => {
    window.location.href = `/search?q=${encodeURIComponent(q)}`
  }

  return (
    <div className="space-y-3">
      {/* Active filters */}
      <div className="bg-white rounded-xl border border-slate-200 p-4" style={{ boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
        <div className="flex items-center gap-2 mb-3">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
            style={{ backgroundColor: '#fef3c7', border: '1px solid #fde68a' }}
          >
            <svg className="w-3.5 h-3.5" style={{ color: '#b45309' }} fill="none" viewBox="0 0 24 24" stroke="currentColor" strokeWidth={2.5}>
              <path strokeLinecap="round" strokeLinejoin="round" d="M3 4a1 1 0 011-1h16a1 1 0 011 1v2.586a1 1 0 01-.293.707l-6.414 6.414a1 1 0 00-.293.707V17l-4 4v-6.586a1 1 0 00-.293-.707L3.293 7.293A1 1 0 013 6.586V4z" />
            </svg>
          </div>
          <h3 className="text-sm font-semibold text-slate-900">Filter Aktif</h3>
          {chips.length > 0 && (
            <span
              className="ml-auto text-xs px-2 py-0.5 rounded-full font-semibold"
              style={{ backgroundColor: '#1e3a5f', color: '#fff' }}
            >
              {chips.length}
            </span>
          )}
        </div>

        {chips.length === 0 ? (
          <p className="text-xs text-slate-400">Tidak ada filter aktif — semua dokumen ditampilkan</p>
        ) : (
          <div className="flex flex-wrap gap-2">
            <AnimatePresence>
              {chips.map(c => (
                <Chip key={c.label} label={c.label} onRemove={c.remove} />
              ))}
            </AnimatePresence>
          </div>
        )}
      </div>

      {/* Popular searches */}
      <div className="bg-white rounded-xl border border-slate-200 p-4" style={{ boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
        <div className="flex items-center gap-2 mb-3">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
            style={{ backgroundColor: '#fef3c7', border: '1px solid #fde68a' }}
          >
            <Lightbulb className="w-3.5 h-3.5" style={{ color: '#b45309' }} />
          </div>
          <h3 className="text-sm font-semibold text-slate-900">Pencarian Populer</h3>
        </div>
        <div className="space-y-1">
          {SUGGESTIONS.map(s => {
            const Icon = s.icon
            return (
              <button
                key={s.label}
                onClick={() => handleSuggestion(s.label)}
                className="w-full flex items-center gap-2.5 px-3 py-2 rounded-lg text-sm text-slate-600 hover:bg-slate-50 hover:text-navy-800 transition-all duration-150"
              >
                <Icon className="w-3.5 h-3.5 text-slate-400 shrink-0" />
                <span className="text-left">{s.label}</span>
                <TrendingUp className="w-3 h-3 text-slate-300 ml-auto shrink-0" />
              </button>
            )
          })}
        </div>
      </div>

      {/* Stats — light navy background per spec */}
      <div className="bg-white rounded-xl border border-slate-200 p-4" style={{ boxShadow: '0 1px 3px rgba(0,0,0,0.08)' }}>
        <div className="flex items-center gap-2 mb-3">
          <div
            className="w-7 h-7 rounded-lg flex items-center justify-center shrink-0"
            style={{ backgroundColor: '#1e3a5f' }}
          >
            <BookOpen className="w-3.5 h-3.5 text-white" />
          </div>
          <h3 className="text-sm font-semibold text-slate-900">Statistik Database</h3>
        </div>
        <div className="grid grid-cols-2 gap-2.5">
          {[
            { value: '12.847', label: 'Dokumen' },
            { value: '84.293', label: 'Pasal / Ayat' },
            { value: '7', label: 'Jenis Dokumen' },
            { value: '2025', label: 'Tahun Terakhir' },
          ].map(s => (
            <div
              key={s.label}
              className="rounded-xl p-3 text-center"
              style={{ backgroundColor: 'rgba(30,58,95,0.05)', border: '1px solid rgba(30,58,95,0.1)' }}
            >
              <p className="text-base font-bold" style={{ color: '#1e3a5f' }}>{s.value}</p>
              <p className="text-xs text-slate-500 mt-0.5">{s.label}</p>
            </div>
          ))}
        </div>
      </div>
    </div>
  )
}