'use client'

import { CheckCircle, AlertCircle, Info, HelpCircle } from 'lucide-react'
import { useState } from 'react'

interface ConfidenceBadgeProps {
  /** Confidence score (0.0 - 1.0) */
  confidence: number
  /** Optional size variant */
  size?: 'sm' | 'md' | 'lg'
  /** Optional tooltip position */
  tooltipPosition?: 'top' | 'bottom'
}

/** Confidence level definitions */
const CONFIDENCE_LEVELS = {
  HIGH: { min: 0.8, label: 'Keyakinan tinggi', color: 'green' },
  MEDIUM: { min: 0.6, label: 'Keyakinan sedang', color: 'yellow' },
  LOW: { min: 0.0, label: 'Keyakinan rendah', color: 'red' },
}

/** Tooltip explanations */
const TOOLTIPS = {
  HIGH: 'Hasil pencarian sangat relevan dan didukung oleh banyak sumber. Jawaban ini dapat diandalkan untuk referensi umum.',
  MEDIUM: 'Hasil pencarian cukup relevan namun mungkin hanya didukung oleh sedikit sumber. Disarankan untuk memverifikasi dengan sumber resmi.',
  LOW: 'Hasil pencarian kurang relevan atau mungkin tidak menemukan informasi spesifik. Jangan digunakan sebagai dasar keputusan penting.',
}

const sizeClasses = {
  sm: { container: 'px-2 py-1 text-xs', icon: 'w-3.5 h-3.5' },
  md: { container: 'px-3 py-1.5 text-sm', icon: 'w-4 h-4' },
  lg: { container: 'px-4 py-2 text-base', icon: 'w-5 h-5' },
}

const colorClasses = {
  green: {
    bg: 'bg-green-50',
    border: 'border-green-200',
    text: 'text-green-900',
    iconColor: 'text-green-600',
  },
  yellow: {
    bg: 'bg-yellow-50',
    border: 'border-yellow-200',
    text: 'text-yellow-900',
    iconColor: 'text-yellow-600',
  },
  red: {
    bg: 'bg-red-50',
    border: 'border-red-200',
    text: 'text-red-900',
    iconColor: 'text-red-600',
  },
}

export default function ConfidenceBadge({
  confidence,
  size = 'md',
  tooltipPosition = 'bottom',
}: ConfidenceBadgeProps) {
  const [showTooltip, setShowTooltip] = useState(false)

  // Determine confidence level
  const level =
    confidence >= CONFIDENCE_LEVELS.HIGH.min
      ? 'HIGH'
      : confidence >= CONFIDENCE_LEVELS.MEDIUM.min
      ? 'MEDIUM'
      : 'LOW'

  const config = CONFIDENCE_LEVELS[level]
  const tooltip = TOOLTIPS[level]
  const colors = colorClasses[config.color as keyof typeof colorClasses]
  const sizeClass = sizeClasses[size]

  // Icon based on level
  const Icon =
    level === 'HIGH' ? CheckCircle : level === 'MEDIUM' ? Info : AlertCircle

  return (
    <div className="relative inline-block">
      <div
        className={`inline-flex items-center gap-2 rounded-full border font-semibold transition-all duration-200 ${colors.bg} ${colors.border} ${colors.text} ${sizeClass.container}`}
        onMouseEnter={() => setShowTooltip(true)}
        onMouseLeave={() => setShowTooltip(false)}
        onFocus={() => setShowTooltip(true)}
        onBlur={() => setShowTooltip(false)}
        tabIndex={0}
        role="button"
        aria-label={`Tingkat keyakinan: ${config.label}`}
      >
        <Icon className={sizeClass.icon} />
        <span>{config.label}</span>
        <span className="opacity-75">({(confidence * 100).toFixed(0)}%)</span>
        <HelpCircle className={`w-3 h-3 opacity-50 ${sizeClass.icon}`} />
      </div>

      {/* Tooltip */}
      {showTooltip && (
        <div
          className={`absolute z-50 w-72 p-3 rounded-lg shadow-xl border text-sm ${
            tooltipPosition === 'top' ? 'bottom-full mb-2' : 'top-full mt-2'
          } bg-white border-gray-200 text-gray-700 left-1/2 -translate-x-1/2`}
          role="tooltip"
        >
          <p className="leading-relaxed">{tooltip}</p>
          <div
            className={`absolute ${
              tooltipPosition === 'top' ? 'top-full' : 'bottom-full'
            } left-1/2 -translate-x-1/2 w-0 h-0 border-8 border-transparent ${
              tooltipPosition === 'top'
                ? 'border-t-white border-b-0'
                : 'border-b-white border-t-0'
            }`}
          />
        </div>
      )}
    </div>
  )
}