import React from 'react'

type BadgeVariant = 'default' | 'indigo' | 'emerald' | 'amber' | 'red' | 'purple'

interface BadgeProps {
  children: React.ReactNode
  variant?: BadgeVariant
  size?: 'sm' | 'md'
  dot?: boolean
  className?: string
}

const variants: Record<BadgeVariant, string> = {
  default:  'bg-slate-100 text-slate-700 border-slate-200',
  indigo:   'bg-indigo-50 text-indigo-700 border-indigo-200',
  emerald:  'bg-emerald-50 text-emerald-700 border-emerald-200',
  amber:    'bg-amber-50 text-amber-700 border-amber-200',
  red:      'bg-red-50 text-red-700 border-red-200',
  purple:   'bg-purple-50 text-purple-700 border-purple-200',
}

export default function Badge({
  children,
  variant = 'default',
  size = 'sm',
  dot = false,
  className = '',
}: BadgeProps) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 border rounded-full font-semibold tracking-wide uppercase ${variants[variant]} ${size === 'sm' ? 'px-2 py-0.5 text-[10px]' : 'px-2.5 py-1 text-xs'} ${className}`}
    >
      {dot && (
        <span className="w-1.5 h-1.5 rounded-full bg-current opacity-70" />
      )}
      {children}
    </span>
  )
}