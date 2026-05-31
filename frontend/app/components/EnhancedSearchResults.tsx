'use client'

import { Shield, Zap } from 'lucide-react'
import ConfidenceBadge from './ConfidenceBadge'
import LegalDisclaimer from './LegalDisclaimer'
import { SourceCardList } from './SourceCard'
import { useState } from 'react'

interface EnhancedQueryResult {
  answer: string
  sources: string[]
  confidence: number
  latency_ms: number
  from_cache?: boolean
  metadata?: {
    chunks_retrieved?: number
    expansion_used?: boolean
    reranking_used?: boolean
    topic?: string
    is_high_stakes?: boolean
  }
}

interface EnhancedSearchResultsProps {
  result: EnhancedQueryResult
}

export default function EnhancedSearchResults({
  result,
}: EnhancedSearchResultsProps) {
  const [showFullDisclaimer, setShowFullDisclaimer] = useState(true)

  const topic = result.metadata?.topic || 'umum'
  const isHighStakes = result.metadata?.is_high_stakes ?? false

  return (
    <div className="space-y-6">
      {/* ── Legal Disclaimer ── */}
      {showFullDisclaimer && (
        <LegalDisclaimer topic={topic} isHighStakes={isHighStakes} />
      )}

      {/* ── Answer Card ── */}
      <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-xl">
        {/* Header */}
        <div className="flex items-start justify-between mb-6">
          <h3 className="text-2xl font-bold text-gray-900 flex items-center gap-2">
            <Zap className="w-6 h-6 text-blue-600" />
            Jawaban
          </h3>
          <div className="flex flex-wrap items-center gap-2">
            {result.from_cache && (
              <span className="px-3 py-1 bg-blue-100 text-blue-700 rounded-full text-sm font-medium">
                Cached
              </span>
            )}
            <ConfidenceBadge confidence={result.confidence} size="md" />
          </div>
        </div>

        {/* Answer text */}
        <p className="text-lg text-gray-700 leading-relaxed whitespace-pre-wrap">
          {result.answer}
        </p>

        {/* Metadata grid */}
        <div className="mt-6 pt-6 border-t border-gray-200 grid grid-cols-2 md:grid-cols-4 gap-4">
          <div>
            <p className="text-sm text-gray-500 mb-1">Confidence</p>
            <p className="text-2xl font-bold text-blue-600">
              {(result.confidence * 100).toFixed(0)}%
            </p>
          </div>
          <div>
            <p className="text-sm text-gray-500 mb-1">Response Time</p>
            <p className="text-2xl font-bold text-blue-600">
              {result.latency_ms}ms
            </p>
          </div>
          {result.metadata?.chunks_retrieved && (
            <div>
              <p className="text-sm text-gray-500 mb-1">Chunks</p>
              <p className="text-2xl font-bold text-blue-600">
                {result.metadata.chunks_retrieved}
              </p>
            </div>
          )}
          {result.metadata?.expansion_used !== undefined && (
            <div>
              <p className="text-sm text-gray-500 mb-1">Features</p>
              <div className="flex gap-1 mt-1">
                {result.metadata.expansion_used && (
                  <span className="px-2 py-1 bg-green-100 text-green-700 rounded text-xs font-medium">
                    Expand
                  </span>
                )}
                {result.metadata.reranking_used && (
                  <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs font-medium">
                    Rerank
                  </span>
                )}
              </div>
            </div>
          )}
        </div>
      </div>

      {/* ── Sources Card ── */}
      {result.sources && result.sources.length > 0 && (
        <div className="bg-white rounded-2xl border border-gray-200 p-8 shadow-xl">
          <h3 className="text-xl font-bold text-gray-900 mb-4 flex items-center gap-2">
            <Shield className="w-5 h-5 text-green-600" />
            Referensi Sumber
          </h3>

          <SourceCardList sources={result.sources} />
        </div>
      )}

      {/* ── Bottom disclaimer reminder ── */}
      <div className="text-center">
        <p className="text-sm text-gray-500">
          Informasi ini bersifat edukatif. Untuk kasus hukum spesifik,
          <button
            onClick={() => setShowFullDisclaimer(!showFullDisclaimer)}
            className="text-blue-600 hover:underline ml-1"
          >
            {showFullDisclaimer ? 'sembunyikan disclaimer' : 'lihat disclaimer'}
          </button>
        </p>
      </div>
    </div>
  )
}