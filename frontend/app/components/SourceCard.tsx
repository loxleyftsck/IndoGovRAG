'use client'

import { ExternalLink, Download, FileText, Calendar, Building } from 'lucide-react'
import { useState } from 'react'

interface SourceMetadata {
  title: string
  doc_type: string
  year?: string
  number?: string
  agency: string
  url?: string
  pdf_url?: string
}

interface SourceCardProps {
  index: number
  source: string | SourceMetadata
  /** Optional relevance score */
  relevanceScore?: number
  /** Optional source URL */
  sourceUrl?: string
}

/**
 * Parse a simple source string into structured metadata
 * Handles formats like: "Perpres 26/2009" or "UU No. 12 Tahun 2011"
 */
function parseSourceString(source: string): SourceMetadata {
  const lower = source.toLowerCase()

  // Detect document types
  const docTypes = {
    'uu': 'Undang-Undang',
    'perpres': 'Peraturan Presiden',
    'perpu': 'Peraturan Pemerintah Pengganti Undang-Undang',
    'pp': 'Peraturan Pemerintah',
    'permen': 'Peraturan Menteri',
    'perkap': 'Peraturan Kapolri',
    'perbup': 'Peraturan Bupati',
    'perwal': 'Peraturan Walikota',
    'keppres': 'Keputusan Presiden',
    'inpres': 'Instruksi Presiden',
    'surat edaran': 'Surat Edaran',
  }

  let docType = 'Dokumen'
  for (const [key, value] of Object.entries(docTypes)) {
    if (lower.includes(key)) {
      docType = value
      break
    }
  }

  // Extract year (4 digits)
  const yearMatch = source.match(/(\d{4})/)
  const year = yearMatch ? yearMatch[1] : undefined

  // Extract regulation number
  const numberMatch = source.match(/(?:no\.?|nomor|\/)\s*(\d+|[ivx]+)\b/i)
  const number = numberMatch ? numberMatch[1] : undefined

  // Determine agency based on doc type
  const agencyMap: Record<string, string> = {
    'Undang-Undang': 'Pemerintah Indonesia',
    'Peraturan Presiden': 'Presiden Republik Indonesia',
    'Peraturan Pemerintah': 'Pemerintah Indonesia',
    'Keputusan Presiden': 'Presiden Republik Indonesia',
    'Instruksi Presiden': 'Presiden Republik Indonesia',
  }

  const agency = agencyMap[docType] || 'Instansi Pemerintah'

  return {
    title: source,
    doc_type: docType,
    year,
    number,
    agency,
  }
}

export default function SourceCard({
  index,
  source,
  relevanceScore,
  sourceUrl,
}: SourceCardProps) {
  const [isExpanded, setIsExpanded] = useState(false)

  const metadata: SourceMetadata =
    typeof source === 'string' ? parseSourceString(source) : source

  // Generate URL based on metadata if not provided
  const generateUrl = () => {
    if (sourceUrl) return sourceUrl
    if (metadata.url) return metadata.url

    // Generate JDih URL based on doc type
    const baseUrl = 'https://peraturan.go.id'
    const query = encodeURIComponent(metadata.title)

    return `${baseUrl}/search?q=${query}`
  }

  // Generate PDF URL if not provided
  const generatePdfUrl = () => {
    if (metadata.pdf_url) return metadata.pdf_url

    // Try to find PDF on JDih
    return `${generateUrl()}&format=pdf`
  }

  const handleViewSource = (e: React.MouseEvent) => {
    e.stopPropagation()
    window.open(generateUrl(), '_blank', 'noopener,noreferrer')
  }

  const handleDownloadPdf = (e: React.MouseEvent) => {
    e.stopPropagation()
    // For now, open the URL - in a real implementation you'd need
    // access to actual PDF URLs from your backend
    window.open(generatePdfUrl(), '_blank', 'noopener,noreferrer')
  }

  return (
    <div
      className={`group bg-white border-2 rounded-xl transition-all duration-200 overflow-hidden ${
        isExpanded
          ? 'border-blue-300 shadow-md'
          : 'border-gray-200 hover:border-blue-200 hover:shadow-sm'
      }`}
      onClick={() => setIsExpanded(!isExpanded)}
      onKeyDown={(e) => { if (e.key === 'Enter' || e.key === ' ') { e.preventDefault(); setIsExpanded(!isExpanded) } }}
      role="button"
      tabIndex={0}
      aria-expanded={isExpanded}
      aria-label={`${isExpanded ? 'Tutup' : 'Buka'} detail sumber: ${metadata.title}`}
    >
      {/* Header - always visible */}
      <div className="p-4 cursor-pointer">
        <div className="flex items-start gap-3">
          {/* Index badge */}
          <div className="w-8 h-8 bg-blue-100 text-blue-600 rounded-full flex items-center justify-center text-sm font-bold flex-shrink-0">
            {index}
          </div>

          {/* Main content */}
          <div className="flex-1 min-w-0">
            {/* Title */}
            <h4 className="font-semibold text-gray-900 text-base leading-snug mb-1">
              {metadata.title}
            </h4>

            {/* Metadata pills */}
            <div className="flex flex-wrap gap-2 items-center text-sm">
              {/* Document type */}
              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-purple-50 text-purple-700 rounded-md font-medium">
                <FileText className="w-3.5 h-3.5" />
                {metadata.doc_type}
              </span>

              {/* Year */}
              {metadata.year && (
                <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-gray-50 text-gray-600 rounded-md">
                  <Calendar className="w-3.5 h-3.5" />
                  {metadata.year}
                </span>
              )}

              {/* Agency */}
              <span className="inline-flex items-center gap-1 px-2 py-0.5 bg-blue-50 text-blue-600 rounded-md">
                <Building className="w-3.5 h-3.5" />
                {metadata.agency}
              </span>

              {/* Relevance score */}
              {relevanceScore !== undefined && (
                <span className="ml-auto text-xs font-semibold text-gray-500">
                  Relevansi: {(relevanceScore * 100).toFixed(0)}%
                </span>
              )}
            </div>
          </div>
        </div>
      </div>

      {/* Expanded content */}
      {isExpanded && (
        <div className="px-4 pb-4 pt-0 border-t border-gray-100">
          <div className="pl-11 flex gap-2 pt-3">
            {/* View source button */}
            <button
              onClick={handleViewSource}
              aria-label={`Buka sumber: ${metadata.title}`}
              className="inline-flex items-center gap-2 px-3 py-2 bg-blue-600 hover:bg-blue-700 text-white rounded-lg text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-blue-400"
            >
              <ExternalLink className="w-4 h-4" />
              Lihat sumber asli
              <span className="text-xs opacity-75" aria-hidden="true">↗</span>
            </button>

            {/* Download PDF button */}
            <button
              onClick={handleDownloadPdf}
              aria-label={`Unduh PDF: ${metadata.title}`}
              className="inline-flex items-center gap-2 px-3 py-2 bg-gray-100 hover:bg-gray-200 text-gray-700 rounded-lg text-sm font-medium transition-colors focus:outline-none focus-visible:ring-2 focus-visible:ring-gray-400"
            >
              <Download className="w-4 h-4" />
              Unduh PDF
            </button>
          </div>
        </div>
      )}
    </div>
  )
}

/**
 * List of source cards component
 */
export function SourceCardList({
  sources,
  sourceUrls,
}: {
  sources: (string | SourceMetadata)[]
  sourceUrls?: string[]
}) {
  if (!sources || sources.length === 0) {
    return null
  }

  return (
    <div className="space-y-3">
      {sources.map((source, idx) => (
        <SourceCard
          key={idx}
          index={idx + 1}
          source={source}
          sourceUrl={sourceUrls?.[idx]}
        />
      ))}
    </div>
  )
}