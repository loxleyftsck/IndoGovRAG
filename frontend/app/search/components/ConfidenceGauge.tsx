'use client'

import { motion } from 'framer-motion'
import { RadialBarChart, RadialBar } from 'recharts'

interface ConfidenceGaugeProps {
  confidence: number   // 0–1
  latencyMs?: number
  size?: 'sm' | 'md' | 'lg'
}

function getConfidenceLevel(c: number) {
  if (c >= 0.85) return { label: 'Tinggi', color: '#16a34a' }
  if (c >= 0.60) return { label: 'Sedang',  color: '#d97706' }
  return                       { label: 'Rendah', color: '#dc2626' }
}

const SIZE_MAP = {
  sm: { outerRadius: 38, innerRadius: 28, fontSize: 11, subFontSize: 8, height: 90 },
  md: { outerRadius: 58, innerRadius: 44, fontSize: 17, subFontSize: 11, height: 140 },
  lg: { outerRadius: 78, innerRadius: 60, fontSize: 25, subFontSize: 14, height: 190 },
}

export default function ConfidenceGauge({ confidence, latencyMs, size = 'md' }: ConfidenceGaugeProps) {
  const level = getConfidenceLevel(confidence)
  const pct   = Math.round(confidence * 100)
  const dims  = SIZE_MAP[size]

  // Recharts RadialBarChart fills clockwise from startAngle.
  // We push the start before0 so the filled portion sweeps from ~7 o'clock.
  const startDeg = -220
  const filledDeg = Math.round(pct * 2.64)   // max 660° → 264° per10%
  const endDeg    = startDeg + filledDeg

  // chartData[0] = background (full circle, gray)
  // chartData[1] = filled portion (confidence, colored)
  const chartData = [
    { index: 0, value: 100,         fill: '#e2e8f0' },
    { index: 1, value: pct,          fill: level.color },
  ]

  return (
    <div className="flex flex-col items-center gap-1.5">
      <div style={{ width: dims.height, height: dims.height, position: 'relative' }}>
        <RadialBarChart
          cx="50%"
          cy="50%"
          innerRadius={dims.innerRadius}
          outerRadius={dims.outerRadius}
          startAngle={startDeg}
          endAngle={endDeg}
          data={chartData}
          barSize={size === 'sm' ? 8 : size === 'lg' ? 14 : 11}
        >
          <RadialBar
            dataKey="value"
            background={{ fill: '#e2e8f0' }}
            isAnimationActive={true}
            animationDuration={900}
            animationEasing="ease-out"
            cornerRadius={4}
            style={{ fill: level.color }}
          />
        </RadialBarChart>

        {/* Center text — absolutely positioned over the chart */}
        <div
          className="absolute inset-0 flex flex-col items-center justify-center"
          style={{ pointerEvents: 'none' }}
        >
          <motion.span
            initial={{ opacity: 0, scale: 0.7 }}
            animate={{ opacity: 1, scale: 1 }}
            transition={{ delay: 0.4, duration: 0.3 }}
            className="font-bold leading-none"
            style={{ fontSize: dims.fontSize, color: level.color }}
          >
            {pct}%
          </motion.span>
          <motion.span
            initial={{ opacity: 0 }}
            animate={{ opacity: 1 }}
            transition={{ delay: 0.55, duration: 0.2 }}
            className="leading-none"
            style={{ fontSize: dims.subFontSize, color: '#64748b', marginTop: 2 }}
          >
            {level.label}
          </motion.span>
        </div>
      </div>

      {/* Caption */}
<div className="text-center">
        <p className="text-xs font-medium text-slate-500">Confidence</p>
        {latencyMs !== undefined && (
          <p className="text-xs text-slate-400">{Math.round(latencyMs)}ms</p>
        )}
      </div>
    </div>
  )
}