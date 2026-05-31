'use client'

import Link from 'next/link'
import { Shield, BarChart2, Database, ArrowRight, KeyRound, LayoutDashboard } from 'lucide-react'

const navCards = [
  {
    href: '/admin/analytics',
    title: 'Analisis Pencarian',
    description: 'Lihat tren query, statistik latency, query terpopuler, dan diagnostik zero-result.',
    icon: BarChart2,
    iconBg: 'bg-blue-50',
    iconText: 'text-blue-600',
    arrow: 'Buka Analytics',
    arrowColor: 'text-blue-600',
  },
  {
    href: '/upload',
    title: 'Kelola Dokumen',
    description: 'Unggah, proses, dan kelola korpus dokumen hukum Indonesia untuk indexing RAG.',
    icon: Database,
    iconBg: 'bg-green-50',
    iconText: 'text-green-600',
    arrow: 'Buka Pengelolaan',
    arrowColor: 'text-green-600',
  },
]

export default function AdminPage() {
  return (
    <div className="max-w-4xl mx-auto px-4 py-10 space-y-6">

      {/* Back link */}
      <Link
        href="/search"
        className="inline-flex items-center gap-1.5 text-sm text-slate-500 hover:text-indigo-600 transition-colors"
      >
        ← Kembali ke Pencarian
      </Link>

      {/* Page header */}
      <div className="flex items-center gap-4">
        <div className="w-12 h-12 bg-indigo-700 rounded-xl flex items-center justify-center shadow-md shrink-0">
          <Shield className="w-6 h-6 text-white" />
        </div>
        <div>
          <div className="flex items-center gap-2 mb-0.5">
            <span className="text-xs text-slate-400 font-medium">Admin</span>
            <span className="text-xs text-slate-300">/</span>
            <span className="text-xs text-slate-500 font-medium">Dashboard</span>
          </div>
          <h1 className="text-2xl font-bold font-serif text-slate-900 leading-tight">
            Dashboard Admin
          </h1>
        </div>
      </div>

      {/* Admin cards */}
      <div className="grid grid-cols-1 sm:grid-cols-2 gap-4">
        {navCards.map((card) => {
          const Icon = card.icon
          return (
            <Link
              key={card.href}
              href={card.href}
              className="group bg-white rounded-2xl border border-slate-200 p-6 hover:shadow-md hover:border-indigo-300 transition-all cursor-pointer block"
            >
              <div className={`w-11 h-11 rounded-xl flex items-center justify-center mb-4 ${card.iconBg}`}>
                <Icon className={`w-5 h-5 ${card.iconText}`} />
              </div>
              <h2 className="text-lg font-bold text-slate-900 mb-2">{card.title}</h2>
              <p className="text-sm text-slate-500 leading-relaxed mb-4">{card.description}</p>
              <div className={`flex items-center gap-1.5 ${card.arrowColor} text-sm font-semibold`}>
                {card.arrow}
                <ArrowRight className="w-4 h-4 group-hover:translate-x-1 transition-transform" />
              </div>
            </Link>
          )
        })}

        {/* API Key info card */}
        <div className="bg-white rounded-2xl border border-slate-200 p-6 col-span-1 sm:col-span-2">
          <div className="w-11 h-11 rounded-xl flex items-center justify-center mb-4 bg-slate-100">
            <KeyRound className="w-5 h-5 text-slate-500" />
          </div>
          <h2 className="text-lg font-bold text-slate-900 mb-2">Kelola API Key</h2>
          <p className="text-sm text-slate-500 leading-relaxed mb-4">
            Halaman analytics dilindungi admin token. Set variabel berikut di{' '}
            <code className="bg-slate-100 rounded-lg px-1.5 py-0.5 font-mono text-xs text-slate-800">.env.local</code>{' '}
            untuk mengaktifkan autentikasi:
          </p>
          <code className="block bg-slate-100 rounded-lg px-3 py-2 font-mono text-xs text-slate-800 border border-slate-200">
            NEXT_PUBLIC_ADMIN_TOKEN=your-secret-token
          </code>
        </div>
      </div>

      {/* Quick navigation */}
      <div className="bg-slate-50 rounded-2xl border border-slate-200 p-5">
        <div className="flex items-center gap-2 mb-3">
          <LayoutDashboard className="w-4 h-4 text-slate-400" />
          <span className="text-xs font-bold text-slate-500 uppercase tracking-wider">Navigasi Cepat</span>
        </div>
        <div className="flex flex-wrap gap-2">
          {[
            { label: 'Cari Dokumen', href: '/search' },
            { label: 'Unggah Dokumen', href: '/upload' },
            { label: 'Analytics', href: '/admin/analytics' },
          ].map((link) => (
            <Link
              key={link.href}
              href={link.href}
              className="px-3.5 py-2 bg-white border border-slate-200 hover:border-indigo-300 hover:bg-indigo-50 text-slate-600 hover:text-indigo-700 rounded-xl text-xs font-medium transition-all"
            >
              {link.label}
            </Link>
          ))}
        </div>
      </div>

    </div>
  )
}