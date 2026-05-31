'use client'

import { useCallback } from 'react'
import { useRouter, useSearchParams } from 'next/navigation'
import { motion } from 'framer-motion'
import { ChevronLeft, ChevronRight } from 'lucide-react'

import { useSearchStore } from '../../lib/searchStore'

interface PaginationProps {
  total: number
  perPage: number
  currentPage: number
  onPageChange?: (page: number) => void
}

function getPageNumbers(current: number, total: number): (number | '...')[] {
  if (total <= 7) return Array.from({ length: total }, (_, i) => i + 1)

  const pages: (number | '...')[] = [1]

  if (current > 3) pages.push('...')

  const start = Math.max(2, current - 1)
  const end   = Math.min(total - 1, current + 1)
  for (let i = start; i <= end; i++) pages.push(i)

  if (current < total - 2) pages.push('...')
  pages.push(total)

  return pages
}

export default function Pagination({ total, perPage, currentPage }: PaginationProps) {
  const router       = useRouter()
  const searchParams = useSearchParams()
  const store        = useSearchStore()

  const totalPages = Math.max(1, Math.ceil(total / perPage))

  const goToPage = useCallback(
    (n: number) => {
      store.setPage(n)
      const params = new URLSearchParams(searchParams.toString())
      params.set('page', String(n))
      router.push(`?${params.toString()}`, { scroll: false })
    },
    [router, searchParams, store]
  )

  if (totalPages <= 1) return null

  const pages      = getPageNumbers(currentPage, totalPages)
  const start      = (currentPage - 1) * perPage + 1
  const end        = Math.min(currentPage * perPage, total)
  const isMobile   = typeof window !== 'undefined' && window.innerWidth < 640

  const handlePrev = () => { if (currentPage > 1) goToPage(currentPage - 1) }
  const handleNext = () => { if (currentPage < totalPages) goToPage(currentPage + 1) }

  return (
    <div className="flex flex-col items-center gap-4 py-6">
      {/* Result count */}
      <p className="text-sm text-slate-500">
        Menampilkan{' '}
        <span className="font-medium text-slate-700">{start}&ndash;{end}</span>{' '}
        dari{' '}
        <span className="font-medium text-slate-700">{total.toLocaleString('id-ID')}</span>{' '}
        hasil
      </p>

      <div className="flex items-center gap-1">
        {/* Previous */}
        <PaginationButton
          onClick={handlePrev}
          disabled={currentPage <= 1}
          label="Sebelumnya"
          icon={<ChevronLeft className="w-4 h-4" />}
        />

        {/* Mobile: show current page badge instead of page numbers */}
        {isMobile ? (
          <span className="w-10 h-9 flex items-center justify-center text-sm font-medium text-indigo-700 bg-indigo-50 rounded-lg">
            {currentPage}/{totalPages}
          </span>
        ) : (
          /* Desktop / tablet: page number buttons */
          pages.map((p, i) =>
            p === '...' ? (
              <span key={`ellipsis-${i}`} className="px-1.5 text-slate-400 select-none text-sm">
                ···
              </span>
            ) : (
              <motion.button
                key={p}
                onClick={() => goToPage(p as number)}
                className={`w-9 h-9 rounded-lg text-sm font-medium transition-all ${
                  p === currentPage
                    ? 'bg-indigo-600 text-white shadow-sm cursor-default'
                    : 'text-slate-600 hover:bg-indigo-50 hover:text-indigo-700'
                }`}
                whileTap={p !== currentPage ? { scale: 0.95 } : {}}
              >
                {p}
              </motion.button>
            )
          )
        )}

        {/* Next */}
        <PaginationButton
          onClick={handleNext}
          disabled={currentPage >= totalPages}
          label="Berikutnya"
          icon={<ChevronRight className="w-4 h-4" />}
          iconPosition="right"
        />
      </div>
    </div>
  )
}

function PaginationButton({
  onClick,
  disabled,
  label,
  icon,
  iconPosition = 'left',
}: {
  onClick: () => void
  disabled?: boolean
  label: string
  icon: React.ReactNode
  iconPosition?: 'left' | 'right'
}) {
  return (
    <motion.button
      onClick={onClick}
      disabled={disabled}
      aria-label={label}
      className={`flex items-center gap-1.5 h-9 px-3 rounded-lg text-sm font-medium transition-all ${
        disabled
          ? 'text-slate-300 cursor-not-allowed'
          : 'text-slate-600 hover:bg-indigo-50 hover:text-indigo-700 active:bg-indigo-100'
      }`}
      whileTap={disabled ? {} : { scale: 0.95 }}
    >
      {iconPosition === 'left' ? (
        <>
          {icon}
          <span className="hidden sm:inline">{label}</span>
        </>
      ) : (
        <>
          <span className="hidden sm:inline">{label}</span>
          {icon}
        </>
      )}
    </motion.button>
  )
}