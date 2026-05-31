'use client'

import { motion } from 'framer-motion'
import { Scale, Heart } from 'lucide-react'

interface PhilosophyFooterProps {
  tagline?: string
  attribution?: string
  footerNote?: string
}

const DEFAULT_TAGLINE = '"Hukum tanpa keadilan adalah neraka tanpa penjaga"'
const DEFAULT_ATTRIBUTION = '— Konsep Hukum Indonesia'
const DEFAULT_FOOTER_NOTE =
  'Didukung oleh kecerdasan buatan dengan verifikasi dari dokumen hukum resmi'

export default function PhilosophyFooter({
  tagline = DEFAULT_TAGLINE,
  attribution = DEFAULT_ATTRIBUTION,
  footerNote = DEFAULT_FOOTER_NOTE,
}: PhilosophyFooterProps) {
  return (
    <motion.footer
      initial={{ opacity: 0, y: 16 }}
      animate={{ opacity: 1, y: 0 }}
      transition={{ duration: 0.5, ease: 'easeOut' }}
      className="w-full bg-indigo-950 text-white mt-16"
 role="contentinfo"
    >
      {/* Philosophy quote section */}
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-12 sm:py-16 text-center">
        {/* Decorative scales icon */}
        <div className="flex justify-center mb-6">
          <div className="w-12 h-12 bg-indigo-800 rounded-2xl flex items-center justify-center">
            <Scale className="w-6 h-6 text-indigo-300" />
          </div>
        </div>

        {/* Main quote */}
        <p
          className="text-xl sm:text-2xl md:text-3xl leading-relaxed italic mb-4"
          style={{
            fontFamily: '"DM Serif Display", Georgia, "Times New Roman", serif',
            fontStyle: 'italic',
          }}
        >
          {tagline}
        </p>

        {/* Attribution */}
        <p className="text-indigo-300 text-sm sm:text-base font-medium tracking-wide">
          {attribution}
</p>

        {/* Divider */}
        <div className="mt-8 mb-8 flex items-center justify-center gap-3">
          <div className="h-px w-12 bg-indigo-700" />
          <div className="w-1.5 h-1.5 bg-indigo-500 rounded-full" />
          <div className="h-px w-12 bg-indigo-700" />
        </div>

        {/* Footer note */}
        <p className="text-indigo-400 text-xs sm:text-sm leading-relaxed max-w-xl mx-auto">
          {footerNote}
        </p>

        {/* System status pill */}
        <div className="mt-6 inline-flex items-center gap-2 px-3 py-1.5 bg-indigo-900/50 border border-indigo-800 rounded-full text-xs text-indigo-300">
          <div className="w-1.5 h-1.5 bg-emerald-400 rounded-full animate-pulse" />
          Sistem RAG aktif — mengambil dari basis data regulasi nasional
</div>
      </div>

      {/* Bottom bar */}
      <div className="border-t border-indigo-900">
        <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-4 flex flex-col sm:flex-row items-center justify-between gap-3">
          <div className="flex items-center gap-2 text-indigo-400 text-xs">
            <Heart className="w-3.5 h-3.5 text-red-400" />
            <span>IndoGovRAG — Platform Riset Hukum Indonesia</span>
          </div>
          <div className="text-indigo-500 text-xs">
            IndoGovRAG &copy; {new Date().getFullYear()}
</div>
        </div>
      </div>
    </motion.footer>
  )
}
