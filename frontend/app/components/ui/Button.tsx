'use client'
import { cn } from '../../lib/utils'
import React from 'react'

interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: 'primary' | 'secondary' | 'ghost' | 'danger' | 'outline'
  size?: 'xs' | 'sm' | 'md' | 'lg'
  loading?: boolean
}

const variants = {
  primary:  'bg-indigo-700 hover:bg-indigo-800 active:bg-indigo-900 text-white shadow-sm',
  secondary:'bg-slate-100 hover:bg-slate-200 active:bg-slate-300 text-slate-800',
  ghost:    'bg-transparent hover:bg-slate-100 active:bg-slate-200 text-slate-600',
  danger:   'bg-red-600 hover:bg-red-700 active:bg-red-800 text-white',
  outline:  'bg-transparent hover:bg-indigo-50 active:bg-indigo-100 text-indigo-700 border border-indigo-300',
}

const sizes = {
  xs: 'h-7 px-2.5 text-xs rounded-lg',
  sm: 'h-8 px-3 text-xs rounded-xl',
  md: 'h-9 px-4 text-sm rounded-xl',
  lg: 'h-11 px-6 text-base rounded-xl',
}

export default function Button({
  variant = 'primary', size = 'md', loading = false,
  className, disabled, children, ...props
}: ButtonProps) {
  return (
    <button
      {...props}
      disabled={disabled || loading}
      className={cn(
        'inline-flex items-center justify-center gap-2 font-semibold transition-all duration-150 cursor-pointer',
        'focus-visible:outline-none focus-visible:ring-2 focus-visible:ring-indigo-500 focus-visible:ring-offset-1',
        'disabled:opacity-50 disabled:cursor-not-allowed',
        variants[variant],
        sizes[size],
        className
      )}
    >
      {loading && (
        <svg className="animate-spin w-3.5 h-3.5" viewBox="0 0 24 24" fill="none">
          <circle className="opacity-25" cx="12" cy="12" r="10" stroke="currentColor" strokeWidth="4" />
          <path className="opacity-75" fill="currentColor" d="M4 12a8 8 0 018-8v4a4 4 0 00-4 4H4z" />
        </svg>
      )}
      {children}
    </button>
  )
}