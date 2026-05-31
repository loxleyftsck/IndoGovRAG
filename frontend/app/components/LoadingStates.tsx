'use client'

import { motion } from 'framer-motion'
import { Loader2, BookOpen, Scale, Layers } from 'lucide-react'

export type AgentStage =
  | 'query_understanding'
  | 'retrieval'
  | 'legal_reasoning'
  | 'synthesis'
  | 'general'

export interface LoadingStateProps {
  stage?: AgentStage
  customMessage?: string
  showProgress?: boolean
}

const AGENT_STAGE_CONFIG: Record<AgentStage, { icon: React.ReactNode; message: string; submessage: string }> = {
  query_understanding: {
    icon: <BookOpen className="w-5 h-5" />,
    message: 'Memahami pertanyaan Anda...',
    submessage: 'Menganalisis maksud dan konteks pertanyaan hukum Anda',
  },
  retrieval: {
    icon: <Layers className="w-5 h-5" />,
    message: 'Mengambil dokumen regulasi...',
    submessage: 'Mencari dan memfilter ribuan regulasi Indonesia',
  },
  legal_reasoning: {
    icon: <Scale className="w-5 h-5" />,
    message: 'Menganalisis konteks hukum...',
    submessage: 'Meneliti preseden, amendemen, dan konteks yuridis',
  },
  synthesis: {
    icon: <Loader2 className="w-5 h-5 animate-spin" />,
    message: 'Merangkai jawaban dari sumber resmi...',
    submessage: 'Menggabungkan temuan dari berbagai regulasi',
  },
  general: {
    icon: <Loader2 className="w-5 h-5 animate-spin" />,
    message: 'Memuat...',
    submessage: 'Mohon tunggu sebentar',
  },
}

// ─── Loading State with Stage Label ─────────────────────────────────────────

export function AgentLoadingState({ stage = 'general', customMessage, showProgress = false }: LoadingStateProps) {
  const config = AGENT_STAGE_CONFIG[stage]

  return (
    <motion.div
      initial={{ opacity: 0, scale: 0.97 }}
      animate={{ opacity: 1, scale: 1 }}
      exit={{ opacity: 0, scale: 0.97 }}
      transition={{ duration: 0.3 }}
      className="bg-white rounded-2xl border border-slate-200 p-6 sm:p-8 shadow-md"
      role="status"
      aria-live="polite"
      aria-label={customMessage ?? config.message}
    >
      <div className="flex flex-col items-center gap-4">
        {/* Icon with background */}
        <div className="w-14 h-14 bg-indigo-100 rounded-2xl flex items-center justify-center text-indigo-600">
          {config.icon}
        </div>

        {/* Message */}
        <div className="text-center">
          <p className="text-base font-semibold text-slate-900">
            {customMessage ?? config.message}
          </p>
          <p className="text-xs text-slate-500 mt-1">
            {config.submessage}
          </p>
        </div>

        {/* Progress bar */}
        {showProgress && (
          <div className="w-full max-w-xs">
            <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
              <motion.div
                className="h-full bg-gradient-to-r from-indigo-500 to-purple-500 rounded-full"
                initial={{ width: '10%' }}
                animate={{ width: '85%' }}
                transition={{ duration: 2.5, ease: 'easeInOut', repeat: Infinity, repeatType: 'reverse' }}
              />
            </div>
          </div>
        )}

        {/* Stage indicator dots */}
        <div className="flex items-center gap-1.5 mt-2">
          {(['query_understanding', 'retrieval', 'legal_reasoning', 'synthesis'] as AgentStage[]).map((s, i) => {
            const isActive = s === stage
            const isPast = [
              'query_understanding',
              'retrieval',
              'legal_reasoning',
              'synthesis',
            ].indexOf(stage) > i
            return (
              <div
                key={s}
                className={`h-2 rounded-full transition-all duration-300 ${
                  isActive
                    ? 'w-6 bg-indigo-500'
                    : isPast
                    ? 'w-2 bg-indigo-300'
                    : 'w-2 bg-slate-200'
                }`}
              />
            )
          })}
        </div>
      </div>
    </motion.div>
  )
}

// ─── Shimmer Card (inline search loading) ────────────────────────────────────

export function ShimmerCard({ lines = 4 }: { lines?: number }) {
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
          <div
            key={i}
            className="skeleton h-5 rounded"
            style={{ width: `${60 + Math.random() * 35}%` }}
          />
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

// ─── Shimmer Sources ─────────────────────────────────────────────────────────

export function ShimmerSources({ count = 3 }: { count?: number }) {
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
            <div
              className="skeleton h-5 rounded flex-1"
              style={{ width: `${50 + Math.random() * 40}%` }}
            />
          </div>
        ))}
      </div>
    </motion.div>
  )
}

// ─── Inline Spinner ──────────────────────────────────────────────────────────

export function InlineSpinner({ size = 'md' }: { size?: 'sm' | 'md' | 'lg' }) {
  const dimClass =
    size === 'sm' ? 'w-4 h-4' : size === 'lg' ? 'w-8 h-8' : 'w-5 h-5'
  return (
    <div
      className={`spinner ${dimClass}`}
      aria-label="Memuat..."
      role="status"
    />
  )
}

// ─── All Agent Stage States (for multi-stage display) ────────────────────────

export function AllStagesLoadingState({ currentStage }: { currentStage: AgentStage }) {
  const stages: AgentStage[] = [
    'query_understanding',
    'retrieval',
    'legal_reasoning',
    'synthesis',
  ]
  const currentIdx = stages.indexOf(currentStage)

  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      className="bg-white rounded-2xl border border-slate-200 p-6 shadow-md space-y-4"
      role="status"
      aria-live="polite"
    >
      <div className="flex items-center gap-2 mb-4">
        <div className="w-8 h-8 bg-indigo-100 rounded-xl flex items-center justify-center">
          <Loader2 className="w-4 h-4 text-indigo-600 animate-spin" />
        </div>
        <p className="text-sm font-bold text-slate-900">Memproses...</p>
      </div>

      <div className="space-y-3">
        {stages.map((stage, idx) => {
          const config = AGENT_STAGE_CONFIG[stage]
          const isActive = idx === currentIdx
          const isDone = idx < currentIdx
          return (
            <div key={stage} className="flex items-center gap-3">
              <div
                className={`w-6 h-6 rounded-full flex items-center justify-center flex-shrink-0 ${
                  isDone
                    ? 'bg-emerald-100 text-emerald-600'
                    : isActive
                    ? 'bg-indigo-100 text-indigo-600'
                    : 'bg-slate-100 text-slate-400'
                }`}
              >
                {isDone ? (
                  <svg className="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24">
                    <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2.5} d="M5 13l4 4L19 7" />
                  </svg>
                ) : isActive ? (
                  <Loader2 className="w-3.5 h-3.5 animate-spin" />
                ) : (
                  <span className="text-xs font-bold">{idx + 1}</span>
                )}
              </div>
              <div className="flex-1">
                <p
                  className={`text-sm ${
                    isActive
                      ? 'font-semibold text-indigo-700'
                      : isDone
                      ? 'text-slate-500 line-through'
                      : 'text-slate-400'
                  }`}
                >
                  {config.message}
                </p>
                {isActive && (
                  <p className="text-xs text-slate-400 mt-0.5">{config.submessage}</p>
                )}
              </div>
            </div>
          )
        })}
      </div>
    </motion.div>
  )
}