'use client'

import { Suspense, type ReactNode } from 'react'
import Link from 'next/link'
import { useRouter } from 'next/navigation'
import { Search, X, ChevronLeft } from 'lucide-react'
import { useState } from 'react'

function SearchPageSkeleton() {
  return (
    <div className="min-h-screen flex items-center justify-center">
      <div className="text-center">
        <div className="w-10 h-10 border-4 border-indigo-600 border-t-transparent rounded-full animate-spin mx-auto mb-3" />
        <p className="text-slate-500 text-sm">Memuat...</p>
      </div>
    </div>
  )
}

export default function SearchLayout({ children }: { children: ReactNode }) {
  return (
    <Suspense fallback={<SearchPageSkeleton />}>
      {children}
    </Suspense>
  )
}

function SearchTopBar() {
  const router = useRouter()
  const [query, setQuery] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (query.trim()) {
      router.push(`/search?q=${encodeURIComponent(query.trim())}`)
    }
  }

  return (
    <header className="fixed top-0 left-0 right-0 z-20 bg-white/90 backdrop-blur-md border-b border-slate-200 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center gap-4 h-16">
          {/* Logo */}
          <Link
            href="/"
            className="flex items-center gap-2.5 shrink-0 group"
          >
            <div className="w-9 h-9 bg-indigo-700 rounded-xl flex items-center justify-center shadow-sm group-hover:bg-indigo-800 transition-colors">
              <span className="text-white font-bold text-sm">IG</span>
            </div>
            <span className="font-bold text-slate-900 hidden sm:block text-base">IndoGovRAG</span>
          </Link>

          {/* Back link */}
          <Link
            href="/"
            className="flex items-center gap-1 text-sm text-slate-500 hover:text-indigo-700 transition-colors shrink-0"
          >
            <ChevronLeft className="w-4 h-4" />
            <span className="hidden sm:block">Beranda</span>
          </Link>

          {/* Search bar */}
          <form onSubmit={handleSubmit} className="flex-1 max-w-2xl mx-auto">
            <div className="relative flex items-center">
              <Search className="absolute left-3.5 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
              <input
                type="text"
                value={query}
                onChange={(e) => setQuery(e.target.value)}
                placeholder="Cari peraturan Indonesia..."
                className="w-full h-10 pl-10 pr-10 bg-slate-50 border border-slate-200 rounded-xl text-sm text-slate-800 placeholder-slate-400 outline-none focus:border-indigo-400 focus:bg-white focus:ring-2 focus:ring-indigo-100 transition-all"
              />
              {query && (
                <button
                  type="button"
                  onClick={() => setQuery('')}
                  className="absolute right-3 top-1/2 -translate-y-1/2 p-0.5 text-slate-400 hover:text-slate-600 transition-colors"
                >
                  <X className="w-3.5 h-3.5" />
                </button>
              )}
            </div>
          </form>

          {/* Nav links */}
          <nav className="hidden md:flex items-center gap-1 shrink-0">
            <Link
              href="/admin"
              className="px-3 py-1.5 text-sm font-medium text-slate-600 hover:text-indigo-700 hover:bg-slate-100 rounded-lg transition-colors"
            >
              Admin
            </Link>
          </nav>
        </div>
      </div>
    </header>
  )
}
