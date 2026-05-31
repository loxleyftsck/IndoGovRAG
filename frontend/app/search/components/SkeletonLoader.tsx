'use client'

import { motion } from 'framer-motion'

interface SkeletonCardProps {
  index?: number
}

export function SkeletonCard({ index = 0 }: SkeletonCardProps) {
  return (
    <motion.div
      initial={{ opacity: 0 }}
      animate={{ opacity: 1 }}
      transition={{ delay: index * 0.06, duration: 0.2 }}
      className="bg-white rounded-xl border border-slate-100 p-5 space-y-4"
    >
      {/* Top row */}
      <div className="flex items-center gap-3">
        <div className="skeleton h-5 w-14 rounded-full" />
        <div className="skeleton h-4 w-32 rounded" />
        <div className="skeleton h-4 w-20 rounded ml-auto" />
      </div>

      {/* Title */}
      <div className="space-y-2">
        <div className="skeleton h-5 w-full rounded" />
        <div className="skeleton h-5 w-3/4 rounded" />
      </div>

      {/* Meta */}
      <div className="flex gap-3">
        <div className="skeleton h-3 w-24 rounded" />
        <div className="skeleton h-3 w-20 rounded" />
      </div>

      {/* Excerpt lines */}
      <div className="space-y-1.5">
        <div className="skeleton h-3.5 w-full rounded" />
        <div className="skeleton h-3.5 w-full rounded" />
        <div className="skeleton h-3.5 w-2/3 rounded" />
      </div>

      {/* Bottom bar */}
      <div className="flex items-center gap-2">
        <div className="skeleton h-1 flex-1 rounded-full" />
        <div className="skeleton h-3 w-10 rounded" />
      </div>
    </motion.div>
  )
}

export default function SkeletonLoader({ count = 5 }: { count?: number }) {
  return (
    <div className="space-y-4">
      {Array.from({ length: count }).map((_, i) => (
        <SkeletonCard key={i} index={i} />
      ))}
    </div>
  )
}

// Summary skeleton
export function SummarySkeleton() {
  return (
    <div className="bg-white rounded-xl border border-slate-200 shadow-xs px-5 py-4 mb-5">
      <div className="flex items-center justify-between">
        <div className="space-y-2">
          <div className="skeleton h-7 w-72 rounded-md" />
          <div className="flex items-center gap-3">
            <div className="skeleton h-4 w-20 rounded" />
            <div className="skeleton h-4 w-16 rounded" />
          </div>
        </div>
        <div className="skeleton h-9 w-32 rounded-full" />
      </div>
    </div>
  )
}

// Result list skeleton
export function ResultListSkeleton({ count = 5 }: { count?: number }) {
  return <SkeletonLoader count={count} />
}