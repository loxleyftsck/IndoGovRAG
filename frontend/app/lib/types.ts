// Types mirroring the backend API responses
export interface QueryChunk {
  text?: string
  metadata?: Record<string, unknown>
  score?: number
}

export interface QueryResponse {
  answer: string
  sources: string[]
  confidence: number
  latency_ms: number
  from_cache?: boolean
  // Augmented: returned by a dedicated search endpoint or extended API
  retrieved_chunks?: QueryChunk[]
  metadata?: {
    chunks_retrieved?: number
    expansion_used?: boolean
    reranking_used?: boolean
    topic?: string
    is_high_stakes?: boolean
    status?: string
    error_type?: string
    warnings?: string[]
  }
}

export interface SearchDocument {
  id: string
  title: string
  jenis: string
  tahun: number
  nomor: string
  instansi: string
  status: string
  excerpt: string
  full_text?: string
  url?: string
  citations?: number
  relevance_score?: number
}

export interface PaginationMeta {
  page: number
  per_page: number
  total: number
  total_pages: number
}