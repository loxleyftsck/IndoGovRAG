'use client'

import Link from 'next/link'
import Image from 'next/image'
import { Shield, Search, Home, Database, BarChart2, ChevronRight, Settings } from 'lucide-react'
import { useRouter, usePathname } from 'next/navigation'
import { useState } from 'react'
import { useSearchStore } from '../lib/searchStore'

const navItems = [
  { id: 'home',   label: 'Beranda',    href: '/',       icon: Home },
  { id: 'search', label: 'Pencarian',  href: '/search',  icon: Search },
  { id: 'upload', label: 'Dokumen',    href: '/upload',  icon: Database },
  { id: 'admin',  label: 'Admin',      href: '/admin',   icon: BarChart2 },
]

interface NavbarProps {
  showSearch?: boolean
}

export default function Navbar({ showSearch = false }: NavbarProps) {
  const router   = useRouter()
  const pathname = usePathname()
  const [searchVal, setSearchVal] = useState('')

  const currentLabel = navItems.find(
    n => pathname === n.href || (n.href !== '/' && pathname.startsWith(n.href))
  )?.label ?? ''

  const handleSearch = (e: React.FormEvent) => {
    e.preventDefault()
    if (searchVal.trim()) router.push(`/search?q=${encodeURIComponent(searchVal.trim())}`)
  }

  return (
    <header className="sticky top-0 z-50 bg-white/90 backdrop-blur-md border-b border-slate-200 shadow-xs">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div className="flex items-center justify-between h-14 gap-4">

          {/* Logo */}
          <Link href="/" className="flex items-center gap-2.5 shrink-0 group">
            <img
              src="/logo.svg"
              alt="IndoGovRAG"
              className="h-8 w-auto object-contain"
            />
          </Link>

          {/* Search bar */}
          {showSearch && (
            <form onSubmit={handleSearch} className="flex-1 max-w-xl">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 -translate-y-1/2 w-4 h-4 text-slate-400 pointer-events-none" />
                <input
                  type="text"
                  value={searchVal}
                  onChange={e => setSearchVal(e.target.value)}
                  placeholder="Cari peraturan..."
                  className="w-full h-9 pl-9 pr-4 bg-slate-50 border border-slate-200 rounded-xl text-sm placeholder-slate-400 outline-none focus:bg-white focus:border-accent-500 focus:ring-2 focus:ring-accent-500/15 transition-all"
                />
              </div>
            </form>
          )}

          {/* Breadcrumb hint */}
          {currentLabel && pathname !== '/' && (
            <div className="hidden md:flex items-center gap-1.5 text-xs text-slate-500 shrink-0">
              <ChevronRight className="w-3 h-3" />
              <span className="font-medium text-slate-700">{currentLabel}</span>
            </div>
          )}

          {/* Nav */}
          <nav className="flex items-center gap-1">
            {navItems.map(({ id, label, href, icon: Icon }) => {
              const active = pathname === href || (href !== '/' && pathname.startsWith(href))
              return (
                <Link
                  key={id}
                  href={href}
                  className={`flex items-center gap-1.5 px-3 h-9 rounded-xl text-xs font-semibold transition-all ${
                    active
                      ? 'bg-accent-50 text-accent-700 border border-accent-200'
                      : 'text-slate-500 hover:text-slate-900 hover:bg-slate-100'
                  }`}
                >
                  <Icon className="w-3.5 h-3.5" />
                  <span className="hidden lg:inline">{label}</span>
                </Link>
              )
            })}
            <button
              onClick={() => useSearchStore.getState().setSettingsOpen(true)}
              className="flex items-center justify-center w-9 h-9 rounded-xl text-slate-500 hover:text-slate-950 hover:bg-slate-100 transition-all focus:outline-none shrink-0"
              title="Pengaturan API Key LLM"
            >
              <Settings className="w-4 h-4" />
            </button>
          </nav>
        </div>
      </div>
    </header>
  )
}