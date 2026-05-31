'use client'

import { useCallback } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { motion } from 'framer-motion'
import {
  Filter, X, ChevronDown, RotateCcw,
} from 'lucide-react'
import { useSearchStore, type DocumentType, type StatusType, type SortType } from '../../lib/searchStore'

const JENIS_OPTIONS: { value: DocumentType; label: string }[] = [
  { value: 'UU',      label: 'Undang-Undang Dasar' },
  { value: 'PP',      label: 'Peraturan Pemerintah' },
  { value: 'Perpres', label: 'Peraturan Presiden' },
  { value: 'Permen',  label: 'Peraturan Menteri' },
  { value: 'Perda',   label: 'Peraturan Daerah' },
  { value: 'POJK',    label: 'POJK (OJK)' },
  { value: 'SE',      label: 'Surat Edaran' },
]

const STATUS_OPTIONS: { value: StatusType; label: string }[] = [
  { value: 'berlaku',  label: 'Berlaku' },
  { value: 'direvisi', label: 'Direvisi' },
  { value: 'dicabut',  label: 'Dicabut' },
  { value: 'semua',    label: 'Semua' },
]

const SORT_OPTIONS: { value: SortType; label: string }[] = [
  { value: 'relevansi',      label: 'Relevansi Tertinggi' },
  { value: 'terbaru',        label: 'Tahun Terbaru' },
  { value: 'terlama',        label: 'Tahun Terlama' },
  { value: 'paling-dikutip', label: 'Paling Banyak Dikutip' },
]

const INSTANSI_OPTIONS = [
  { value: '',             label: 'Semua Instansi' },
  { value: 'kemenkumham',  label: 'Kementerian Hukum & HAM' },
  { value: 'kemenkeu',     label: 'Kementerian Keuangan' },
  { value: 'kemenkes',     label: 'Kementerian Kesehatan' },
  { value: 'kemenag',      label: 'Kementerian Agama' },
  { value: 'kemnaker',     label: 'Kementerian Ketenagakerjaan' },
  { value: 'bkpm',         label: 'BKPM / Investasi' },
  { value: 'ojk',          label: 'Otoritas Jasa Keuangan' },
]

function SelectField({
  label, value, options, onChange,
}: {
  label?: string; value: string; options: { value: string; label: string }[]; onChange: (v: string) => void
}) {
  return (
    <div>
      {label && <label className="text-xs text-slate-500 mb-1.5 block font-medium">{label}</label>}
      <div className="relative">
        <select
          className="w-full h-9 px-3 pr-8 bg-white border border-slate-200 rounded-lg text-sm text-slate-800 appearance-none cursor-pointer outline-none transition-all focus:border-navy-800"
          value={value}
          onChange={e => onChange(e.target.value)}
        >
          {options.map(o => <option key={o.value} value={o.value}>{o.label}</option>)}
        </select>
        <ChevronDown className="absolute right-2.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
      </div>
    </div>
  )
}

function NumberField({
  label, value, placeholder, onChange,
}: {
  label?: string; value: number | null; placeholder: string; onChange: (v: number | null) => void
}) {
  return (
    <div>
      {label && <label className="text-xs text-slate-500 mb-1 block font-medium">{label}</label>}
      <input
        type="number"
        className="w-full h-9 px-3 bg-white border border-slate-200 rounded-lg text-sm text-slate-800 outline-none transition-all focus:border-navy-800 placeholder-slate-400"
        placeholder={placeholder}
        min={1945}
        max={2030}
        value={value ?? ''}
        onChange={e => onChange(e.target.value ? parseInt(e.target.value) : null)}
      />
    </div>
  )
}

// ── Collapsible filter section ─────────────────────────────────
function FilterSection({ title, count, children, first }: { title: string; count?: number; children: React.ReactNode; first?: boolean }) {
  return (
    <div className={!first ? 'border-t border-slate-100 pt-3 mt-3' : ''}>
      <details className="group" open>
        <summary className="cursor-pointer flex items-center justify-between py-1 mb-2.5 list-none">
          <div className="flex items-center gap-2">
            <span className="text-xs font-semibold uppercase tracking-wider text-slate-500">{title}</span>
            {count != null && count > 0 && (
              <span className="bg-navy-100 text-navy-800 px-1.5 py-0.5 rounded-full text-[10px] font-bold border border-navy-200">
                {count}
              </span>
            )}
          </div>
          <ChevronDown className="w-3.5 h-3.5 text-slate-400 group-open:rotate-180 transition-transform" />
        </summary>
        <div className="mb-4">
          {children}
        </div>
      </details>
    </div>
  )
}

export default function SearchFilters() {
  const router       = useRouter()
  const searchParams = useSearchParams()
  const store        = useSearchStore()

  const updateParam = useCallback((key: string, value: string | null) => {
    const params = new URLSearchParams(searchParams.toString())
    if (!value) params.delete(key)
    else params.set(key, value)
    if (key !== 'page') params.set('page', '1')
    router.push(`?${params.toString()}`, { scroll: false })
  }, [router, searchParams])

  const toggleJenis = (j: DocumentType) => {
    const next = store.jenis.includes(j)
      ? store.jenis.filter(x => x !== j)
      : [...store.jenis, j]
    store.setJenis(next)
    updateParam('jenis', next.join(',') || null)
  }

  const resetAll = () => {
    store.reset()
    router.push('/', { scroll: false })
  }

  const activeFilterCount = [
    store.jenis.length > 0,
    store.status !== 'berlaku',
    store.tahunDari !== null || store.tahunSampai !== null,
    !!store.instansi,
    store.sort !== 'relevansi',
  ].filter(Boolean).length

  return (
    <div className="space-y-1">

      {/* Header bar — solid deep navy, no gradient */}
      <div
        className="flex items-center gap-3 px-4 py-3 text-white mb-3"
        style={{ backgroundColor: '#1e3a5f', borderRadius: '12px' }}
      >
        <div
          className="w-8 h-8 rounded-lg flex items-center justify-center shrink-0"
          style={{ backgroundColor: 'rgba(255,255,255,0.12)' }}
        >
          <Filter className="w-4 h-4 text-white" />
        </div>
        <div className="flex-1 min-w-0">
          <h2 className="text-sm font-semibold text-white">Filter Pencarian</h2>
          <p className="text-xs" style={{ color: 'rgba(220,232,245,0.75)' }}>Perbaiki hasil pencarian</p>
        </div>
        {activeFilterCount > 0 && (
          <span
            className="w-5 h-5 rounded-full text-xs font-bold flex items-center justify-center shrink-0"
            style={{ backgroundColor: '#b45309', color: '#fff' }}
          >
            {activeFilterCount}
          </span>
        )}
      </div>

      {/* Filter body — white card with 1px border */}
      <div className="bg-white rounded-xl border border-slate-200 px-4 py-4">
        <FilterSection title="Jenis Dokumen" count={store.jenis.length} first>
          <div className="space-y-1">
            {JENIS_OPTIONS.map(opt => (
              <label
                key={opt.value}
                className="flex items-center gap-3 px-2 py-2 rounded-lg hover:bg-slate-50 cursor-pointer transition-colors group"
              >
                <input
                  type="checkbox"
                  checked={store.jenis.includes(opt.value)}
                  onChange={() => toggleJenis(opt.value)}
                  className="w-4 h-4 rounded border-slate-300 accent-navy-800 cursor-pointer shrink-0"
                />
                <span className="flex-1 text-sm text-slate-700 group-hover:text-slate-900 transition-colors">
                  {opt.label}
                </span>
                <span className={`doc-badge ${opt.value}`}>{opt.value}</span>
              </label>
            ))}
          </div>
        </FilterSection>

        {/* ── Status Hukum ── */}
        <FilterSection title="Status Hukum">
          <SelectField
            value={store.status}
            options={STATUS_OPTIONS}
            onChange={v => { store.setStatus(v as StatusType); updateParam('status', v) }}
          />
        </FilterSection>

        {/* ── Rentang Tahun ── */}
        <FilterSection title="Rentang Tahun">
          <div className="grid grid-cols-2 gap-2">
            <NumberField
              label="Dari"
              value={store.tahunDari}
              placeholder="cth. 2020"
              onChange={v => {
                store.setTahunRange(v, store.tahunSampai)
                updateParam('tahun_dari', v?.toString() ?? null)
              }}
            />
            <NumberField
              label="Sampai"
              value={store.tahunSampai}
              placeholder="cth. 2025"
              onChange={v => {
                store.setTahunRange(store.tahunDari, v)
                updateParam('tahun_sampai', v?.toString() ?? null)
              }}
            />
          </div>
          {(store.tahunDari || store.tahunSampai) && (
            <button
              className="flex items-center gap-1.5 text-xs text-navy-800 hover:text-navy-950 font-medium transition-colors mt-2"
              onClick={() => {
                store.setTahunRange(null, null)
                updateParam('tahun_dari', null)
                updateParam('tahun_sampai', null)
              }}
            >
              <X className="w-3 h-3" /> Hapus filter tahun
            </button>
          )}
        </FilterSection>

        {/* ── Instansi ── */}
        <FilterSection title="Instansi Penerbit">
          <SelectField
            value={store.instansi}
            options={INSTANSI_OPTIONS}
            onChange={v => { store.setInstansi(v); updateParam('instansi', v || null) }}
          />
        </FilterSection>

        {/* ── Urutan ── */}
        <FilterSection title="Urutkan">
          <SelectField
            value={store.sort}
            options={SORT_OPTIONS}
            onChange={v => { store.setSort(v as SortType); updateParam('sort', v) }}
          />
        </FilterSection>
      </div>

      {/* Reset link */}
      {store.hasActiveFilters() && (
        <motion.button
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          className="w-full flex items-center justify-center gap-1.5 py-2.5 text-xs text-navy-800 hover:text-navy-950 font-medium transition-colors"
          onClick={resetAll}
        >
          <RotateCcw className="w-3.5 h-3.5" />
          Reset semua filter
        </motion.button>
      )}
    </div>
  )
}