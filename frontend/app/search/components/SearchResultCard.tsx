'use client'

import { motion } from 'framer-motion'
import { ExternalLink, Quote, Link2, FileText } from 'lucide-react'
import type { SearchDocument } from '../../lib/types'

const STATUS_LABEL: Record<string, string> = {
  berlaku: 'Berlaku',
  direvisi: 'Direvisi',
  dicabut:  'Dicabut',
}

function RelevanceBar({ score }: { score: number }) {
  const pct = Math.round((score ?? 0) * 100)
  const color = pct >= 75 ? '#16a34a' : pct >= 50 ? '#d97706' : '#dc2626'
  return (
    <div className="flex items-center gap-2.5">
      <div className="flex-1 h-1 bg-slate-100 rounded-full overflow-hidden">
        <motion.div
          initial={{ width: 0 }}
          animate={{ width: `${pct}%` }}
          transition={{ duration: 0.4, ease: 'easeOut', delay: 0.05 }}
          className="h-full rounded-full"
          style={{ backgroundColor: color }}
        />
      </div>
      <span className="text-xs font-semibold tabular-nums" style={{ color }}>{pct}%</span>
    </div>
  )
}

export default function SearchResultCard({ doc, index, onCite }: {
  doc: SearchDocument
  index: number
  onCite?: (doc: SearchDocument) => void
}) {
  return (
    <motion.div
      initial={{ opacity: 0, y: 6 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.2, delay: index * 0.04, ease: [0.4, 0, 0.2, 1] }}
    >
      <div
        className="group overflow-hidden transition-all duration-200 hover:shadow-md"
        style={{
          backgroundColor: '#ffffff',
          border: '1px solid #e2e8f0',
          borderRadius: '12px',
          boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
        }}
        onMouseEnter={e => {
          (e.currentTarget as HTMLDivElement).style.borderColor = 'rgba(30,58,95,0.3)'
          ;(e.currentTarget as HTMLDivElement).style.boxShadow = '0 2px 6px rgba(0,0,0,0.10)'
        }}
        onMouseLeave={e => {
          ;(e.currentTarget as HTMLDivElement).style.borderColor = '#e2e8f0'
          ;(e.currentTarget as HTMLDivElement).style.boxShadow = '0 1px 3px rgba(0,0,0,0.06)'
        }}
      >
        <div className="p-5">
          {/* ── Top row ── */}
          <div className="flex items-start justify-between gap-3 mb-3">
            <div className="flex flex-wrap items-center gap-2">
              <span className={`doc-badge ${doc.jenis}`}>{doc.jenis}</span>
              <span className="text-sm font-medium text-slate-700">
                No.&nbsp;{doc.nomor}
                {doc.tahun && <span className="text-slate-400">/{doc.tahun}</span>}
              </span>
              {doc.status && (
                <span className={`status-badge ${doc.status}`}>
                  {STATUS_LABEL[doc.status] ?? doc.status}
                </span>
              )}
              {doc.citations !== undefined && doc.citations > 0 && (
                <span
                  className="inline-flex items-center gap-1 px-2 py-0.5 rounded-full text-xs"
                  style={{ backgroundColor: '#f4f5f7', color: '#4a5568' }}
                >
                  <Quote className="w-3 h-3" />
                  {doc.citations.toLocaleString('id-ID')}
                </span>
              )}
            </div>

            {/* Actions */}
            <div
              className="flex items-center gap-0.5 sm:opacity-0 sm:group-hover:opacity-100 group-focus-within:opacity-100 transition-opacity duration-150"
              style={{ color: '#cbd5e1' }}
            >
              {onCite && (
                <button
                  onClick={() => onCite(doc)}
                  className="p-2 rounded-lg hover:bg-slate-50 active:scale-95 transition-all"
                  style={{ color: '#718096' }}
                  title="Kutip dokumen"
                  onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.color = '#b45309' }}
                  onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.color = '#718096' }}
                >
                  <Quote className="w-4 h-4" />
                </button>
              )}
              <button
                onClick={() => navigator.clipboard?.writeText(doc.url ?? '')}
                className="p-2 rounded-lg hover:bg-slate-50 active:scale-95 transition-all"
                style={{ color: '#718096' }}
                title="Salin tautan"
                onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.color = '#1e3a5f' }}
                onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.color = '#718096' }}
              >
                <Link2 className="w-4 h-4" />
              </button>
              <button
                className="p-2 rounded-lg hover:bg-slate-50 active:scale-95 transition-all"
                style={{ color: '#718096' }}
                title="Buka dokumen lengkap"
                onMouseEnter={e => { (e.currentTarget as HTMLButtonElement).style.color = '#1e3a5f' }}
                onMouseLeave={e => { (e.currentTarget as HTMLButtonElement).style.color = '#718096' }}
              >
                <ExternalLink className="w-4 h-4" />
              </button>
            </div>
          </div>

          {/* ── Title ── */}
          <h3
            className="text-base font-semibold leading-snug mb-2 transition-colors"
            style={{ color: '#1a202c' }}
            onMouseEnter={e => { (e.currentTarget as HTMLHeadingElement).style.color = '#1e3a5f' }}
            onMouseLeave={e => { (e.currentTarget as HTMLHeadingElement).style.color = '#1a202c' }}
          >
            {doc.title}
          </h3>

          {/* ── Meta ── */}
          <div className="flex flex-wrap items-center gap-x-4 gap-y-1 mb-3 text-xs text-slate-500">
            {doc.instansi && (
              <span className="flex items-center gap-1.5">
                <FileText className="w-3 h-3 text-slate-400" />
                {doc.instansi}
              </span>
            )}
          </div>

          {/* ── Excerpt ── */}
          <p className="text-sm text-slate-600 leading-relaxed mb-4 line-clamp-3">
            {doc.excerpt}
          </p>

          {/* ── Relevance bar ── */}
          {doc.relevance_score !== undefined && (
            <div>
              <div className="flex items-center justify-between mb-1.5">
                <span className="text-xs text-slate-400 font-medium">Tingkat Relevansi</span>
              </div>
              <RelevanceBar score={doc.relevance_score} />
            </div>
          )}
        </div>
      </div>
    </motion.div>
  )
}