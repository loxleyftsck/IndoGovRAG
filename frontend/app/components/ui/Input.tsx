'use client'
import { cn } from '../../lib/utils'
import React, { forwardRef } from 'react'

interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {
  label?: string
  error?: string
  icon?: React.ReactNode
}

const Input = forwardRef<HTMLInputElement, InputProps>(
  ({ label, error, icon, className, ...props }, ref) => {
    return (
      <div className="w-full">
        {label && (
          <label className="block text-xs font-semibold text-slate-700 mb-1.5">
            {label}
          </label>
        )}
        <div className="relative">
          {icon && (
            <div className="absolute left-3 top-1/2 -translate-y-1/2 text-slate-400 pointer-events-none">
              {icon}
            </div>
          )}
          <input
            ref={ref}
            {...props}
            className={cn(
              'w-full h-9 px-3 bg-white border border-slate-300 rounded-xl text-sm',
              'placeholder-slate-400 outline-none',
              'focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500/15',
              'transition-all duration-150',
              icon && 'pl-9',
              error && 'border-red-400 focus:border-red-500 focus:ring-red-500/15',
              className
            )}
          />
        </div>
        {error && <p className="mt-1 text-xs text-red-600">{error}</p>}
      </div>
    )
  }
)
Input.displayName = 'Input'
export default Input