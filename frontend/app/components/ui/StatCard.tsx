'use client'
import { cn } from '../../lib/utils'

interface StatCardProps {
  label: string
  value: string | number
  icon: React.ReactNode
  color?: 'indigo' | 'green' | 'amber' | 'blue' | 'red' | 'slate'
  trend?: { value: number; label: string }
  className?: string
}

const colorMap = {
  indigo: { bg: 'bg-indigo-100', text: 'text-indigo-700', icon: 'bg-indigo-100 text-indigo-700' },
  green:  { bg: 'bg-green-100',  text: 'text-green-700',  icon: 'bg-green-100 text-green-700' },
  amber:  { bg: 'bg-amber-100',  text: 'text-amber-700',  icon: 'bg-amber-100 text-amber-700' },
  blue:   { bg: 'bg-blue-100',   text: 'text-blue-700',   icon: 'bg-blue-100 text-blue-700' },
  red:    { bg: 'bg-red-100',    text: 'text-red-700',    icon: 'bg-red-100 text-red-700' },
  slate:  { bg: 'bg-slate-100',  text: 'text-slate-700',  icon: 'bg-slate-100 text-slate-700' },
}

export default function StatCard({
  label, value, icon, color = 'indigo', trend, className,
}: StatCardProps) {
  const c = colorMap[color]
  return (
    <div className={cn(
      'bg-white rounded-2xl border border-slate-200 p-5 shadow-xs',
      className
    )}>
      <div className="flex items-start justify-between mb-3">
        <div className={cn('w-10 h-10 rounded-xl flex items-center justify-center', c.bg)}>
          <span className={c.text}>{icon}</span>
        </div>
        {trend && (
          <span className={cn(
            'text-xs font-semibold px-1.5 py-0.5 rounded-full',
            trend.value >= 0 ? 'bg-green-100 text-green-700' : 'bg-red-100 text-red-700'
          )}>
            {trend.value >= 0 ? '+' : ''}{trend.value}%
          </span>
        )}
      </div>
      <div className="text-2xl font-bold text-slate-900 mb-0.5">{value}</div>
      <div className="text-xs text-slate-500">{label}</div>
    </div>
  )
}