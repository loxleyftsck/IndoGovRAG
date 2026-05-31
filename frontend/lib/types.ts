/**
 * Shared TypeScript types for IndoGovRAG
 */

// ============ Auth Types ============
export interface AuthUser {
  id: string;
  email: string;
  name: string;
  image?: string;
  provider?: string;
}

export interface AuthSession {
  user?: AuthUser;
  expires?: string;
}

// ============ Query Types ============
export interface QueryOptions {
  use_query_expansion?: boolean;
  use_reranking?: boolean;
  use_hybrid?: boolean;
  top_k?: number;
  use_cache?: boolean;
}

export interface QueryRequest {
  query: string;
  options?: QueryOptions;
}

export interface QueryMetadata {
  chunks_retrieved?: number;
  expansion_used?: boolean;
  reranking_used?: boolean;
  model_used?: string;
  tokens_used?: number;
  from_cache?: boolean;
  status?: string;
  error_type?: string;
}

export interface QueryResponse {
  answer: string;
  sources: string[];
  confidence: number;
  latency_ms: number;
  metadata?: QueryMetadata;
}

export interface QueryHistoryItem {
  id: string;
  query: string;
  answer: string;
  feedback: 'helpful' | 'not_helpful' | null;
  timestamp: string;
  metadata?: QueryMetadata;
}

// ============ File Types ============
export interface FileStats {
  total_chunks: number;
  unique_files: number;
  categories: Record<string, number>;
  error?: string;
}

export interface FileInfo {
  file_id: string;
  file_name: string;
  category: string;
  doc_type: string;
  chunks_count: number;
  status: 'pending' | 'indexed';
}

export interface FileUploadResponse {
  success: boolean;
  file_id: string;
  filename: string;
  file_type: string;
  file_size: number;
  chunks_created: number;
  message: string;
}

// ============ API Key Types ============
export interface APIKeyInfo {
  key_id: string;
  name: string;
  tier: 'free' | 'pro' | 'enterprise';
  created_at: string;
  rate_limit: string;
  is_active: boolean;
}

export interface APIKeyCreateRequest {
  name: string;
  tier?: 'free' | 'pro' | 'enterprise';
}

export interface RateLimitTier {
  limit: number;
  window_seconds: number;
  description: string;
}

export interface RateLimitsResponse {
  tiers: {
    anonymous?: RateLimitTier;
    free?: RateLimitTier;
    pro?: RateLimitTier;
    enterprise?: RateLimitTier;
  };
}

// ============ Error Types ============
export interface RateLimitError {
  error: string;
  message: string;
  rate_limit: {
    tier: string;
    limit: number;
    remaining: number;
    reset_in_seconds: number;
  };
  retry_after: number;
}

// ============ Search Types ============
export interface SearchDocument {
  id: string
  title: string
  jenis: string
  nomor: string
  tahun: number | null
  instansi: string
  status?: string
  excerpt: string
  citations?: number
  relevance_score?: number
}

// ============ Health Types ============
export interface HealthStatus {
  status: 'healthy' | 'degraded' | 'down';
  rag_initialized: boolean;
  groq_api_key_set: boolean;
  gemini_api_key_set: boolean;
  timestamp: number;
}
