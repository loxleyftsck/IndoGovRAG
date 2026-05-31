'use client'

import Link from 'next/link'
import Navbar from './Navbar'
import { CheckCircle } from 'lucide-react'

interface AppShellProps {
  children: React.ReactNode
  showSearch?: boolean
}

export default function AppShell({ children, showSearch = false }: AppShellProps) {
  return (
    <div className="min-h-screen bg-[var(--surface-secondary)] flex flex-col">

      {/* ── Top Header via Navbar ── */}
      <Navbar showSearch={showSearch} />

      {/* ── Main Content ── */}
      <main className="flex-1">
        {children}
      </main>

      {/* ── Footer ── */}
      <footer className="hidden md:block border-t border-slate-200 bg-white mt-auto">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-5">
          <div className="flex items-center justify-between gap-4 text-xs text-slate-500">
            <div className="flex items-center gap-2">
              <img src="/logo.svg" alt="IndoGovRAG" className="h-5 w-auto object-contain opacity-60" />
              <span>— Platform Penelusuran Regulasi &amp; Dokumen Hukum Indonesia powered by AI &amp; RAG</span>
            </div>
            <div className="flex items-center gap-3">
              <Link href="/search" className="hover:text-indigo-600 transition-colors">Pencarian</Link>
              <Link href="/admin/analytics" className="hover:text-indigo-600 transition-colors">Analytics</Link>
              <span className="px-2 py-0.5 bg-green-100 text-green-700 rounded-full font-semibold text-[10px]">v1.0 Production</span>
            </div>
          </div>
        </div>
      </footer>
    </div>
  )
}