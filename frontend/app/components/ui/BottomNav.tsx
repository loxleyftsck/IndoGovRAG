import React from 'react'
import Link from 'next/link'
import { usePathname } from 'next/navigation'
import { Home, Search, BarChart2, Upload } from 'lucide-react'

const navItems = [
  { id: 'home', label: 'Beranda', icon: Home, href: '/' },
  { id: 'search', label: 'Cari', icon: Search, href: '/search' },
  { id: 'upload', label: 'Dokumen', icon: Upload, href: '/upload' },
  { id: 'analytics', label: 'Analytics', icon: BarChart2, href: '/admin/analytics' },
]

export default function BottomNav() {
  const pathname = usePathname()

  const isActive = (href: string) => {
    if (href === '/') return pathname === '/'
    return pathname.startsWith(href)
  }

  return (
    <nav className="fixed bottom-0 left-0 right-0 bg-white border-t border-slate-200 z-40 md:hidden safe-area-inset-bottom">
      <div className="flex items-center justify-around h-16">
        {navItems.map((item) => {
          const Icon = item.icon
          const active = isActive(item.href)
          return (
            <Link
              key={item.id}
              href={item.href}
              className={`flex flex-col items-center justify-center gap-0.5 w-full h-full min-h-[64px] transition-colors ${
                active
                  ? 'text-indigo-600'
                  : 'text-slate-400 hover:text-slate-600'
              }`}
            >
              {active && (
                <div className="absolute top-0 left-1/2 -translate-x-1/2 w-8 h-0.5 bg-indigo-600 rounded-full" />
              )}
              <Icon className="w-5 h-5" strokeWidth={active ? 2.5 : 1.75} />
              <span className={`text-[10px] font-medium ${active ? 'font-semibold' : ''}`}>
                {item.label}
              </span>
            </Link>
          )
        })}
      </div>
    </nav>
  )
}