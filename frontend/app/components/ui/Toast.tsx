'use client'
import { useEffect, useState } from 'react'
import { CheckCircle, XCircle, AlertTriangle, X } from 'lucide-react'
import { cn } from '../../lib/utils'

interface ToastProps {
  message: string
  type?: 'success' | 'error' | 'warning' | 'info'
  duration?: number
  onDismiss?: () => void
}

const configs = {
  success: { icon: CheckCircle, bg: 'bg-green-50', border: 'border-green-200', text: 'text-green-800', iconColor: 'text-green-600' },
  error:   { icon: XCircle,    bg: 'bg-red-50',   border: 'border-red-200',   text: 'text-red-800',   iconColor: 'text-red-600' },
  warning: { icon: AlertTriangle, bg: 'bg-amber-50', border: 'border-amber-200', text: 'text-amber-800', iconColor: 'text-amber-600' },
  info:    { icon: AlertTriangle, bg: 'bg-blue-50',  border: 'border-blue-200',  text: 'text-blue-800',  iconColor: 'text-blue-600' },
}

export default function Toast({ message, type = 'info', duration = 4000, onDismiss }: ToastProps) {
  const [visible, setVisible] = useState(true)
  const c = configs[type]

  useEffect(() => {
    const timer = setTimeout(() => { setVisible(false); onDismiss?.() }, duration)
    return Object.assign(() => clearTimeout(timer), { displayName: 'cleanup' })
  }, [duration, onDismiss])

  if (!visible) return null

  return (
    <div className={cn(
      'fixed bottom-20 right-4 z-50',
      'flex items-center gap-3 px-4 py-3 rounded-xl border shadow-lg',
      'max-w-sm w-full',
      c.bg, c.border
    )}>
      <div className={c.iconColor}><c.icon className="w-5 h-5" /></div>
      <p className={cn('text-sm font-medium flex-1', c.text)}>{message}</p>
      <button onClick={() => { setVisible(false); onDismiss?.() }} className="text-slate-400 hover:text-slate-600">
        <X className="w-4 h-4" />
      </button>
    </div>
  )
}
