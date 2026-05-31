'use client'

import { motion } from 'framer-motion'
import { Clock, Database, Zap } from 'lucide-react'
import ConfidenceGauge from './ConfidenceGauge'

interface SearchSummaryProps {
  total: number
  query: string
  timeMs?: number
  loading?: boolean
  confidence?: number
  onConfidenceChange?: (c: number) => void
}

export default function SearchSummary({
  total, query, timeMs, loading,
  confidence,
  onConfidenceChange,
}: SearchSummaryProps) {
  return (
    <div
      className="px-5 py-4 mb-5 flex items-start justify-between flex-wrap gap-3"
      style={{
        backgroundColor: '#ffffff',
        border: '1px solid #e2e8f0',
        borderRadius: '12px 12px 0 0',
        boxShadow: '0 1px 3px rgba(0,0,0,0.06)',
      }}
    >
      <div className="flex flex-col gap-2 min-w-0">
        {loading ? (
          <div className="skeleton h-6 w-56 rounded-md" />
        ) : (
          <h2 className="text-base font-semibold" style={{ color: '#1a202c' }}>
            {total.toLocaleString('id-ID')} hasil untuk&nbsp;
            <span style={{ color: '#1e3a5f' }}>&ldquo;{query}&rdquo;</span>
          </h2>
        )}

        <div className="flex flex-wrap items-center gap-2">
          {loading ? (
            <>
              <div className="skeleton h-4 w-20 rounded" />
              <div className="skeleton h-4 w-20 rounded" />
            </>
          ) : (
            <>
              {timeMs !== undefined && (
                <div
                  className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full"
                  style={{ backgroundColor: '#f7f8fa', color: '#718096' }}
                >
                  <Clock className="w-3 h-3" />
                  {timeMs < 1000 ? `${Math.round(timeMs)}ms` : `${(timeMs / 1000).toFixed(1)}s`}
                </div>
              )}
              <div
                className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full"
                style={{ backgroundColor: '#eef2ff', color: '#4338ca' }}
              >
                <Zap className="w-3 h-3" />
                AI RAG
              </div>
              <div
                className="flex items-center gap-1.5 text-xs px-2.5 py-1 rounded-full"
                style={{ backgroundColor: '#f7f8fa', color: '#718096' }}
              >
                <Database className="w-3 h-3" />
                {total} dokumen
              </div>
            </>
          )}
        </div>
      </div>

      {/* Confidence gauge — right side */}
      {!loading && confidence !== undefined && (
        <motion.div
          initial={{ opacity: 0, scale: 0.8 }}
          animate={{ opacity: 1, scale: 1 }}
          transition={{ duration: 0.3, delay: 0.1 }}
          className="shrink-0"
        >
          <ConfidenceGauge
            confidence={confidence}
            size="sm"
          />
        </motion.div>
      )}
    </div>
  )
}