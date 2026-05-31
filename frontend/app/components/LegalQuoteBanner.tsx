'use client'

import { useState, useEffect } from 'react'
import { motion, AnimatePresence } from 'framer-motion'
import { Scale } from 'lucide-react'

const HERO_QUOTES = [
  {
    text: '"Tidak ada negara tanpa hukum, tidak ada hukum tanpa negara"',
    author: 'Karl Olivecrona',
    context: 'Teori Hukum Realis Skandinavia',
  },
  {
    text: '"Keadilan bukan hanya tentang memberi setiap orang apa yang menjadi haknya, tetapi juga memastikan hukum diterapkan secara adil bagi semua"',
    author: 'Konsep Hukum Pancasila',
    context: 'Sila ke-4: Kerakyatan',
  },
  {
    text: '"Hukum progresif adalah hukum yang berkeadilan — hukum yang tidak hanya berlaku secara formil, tetapi juga memenuhi rasa keadilan masyarakat"',
    author: 'Prof. Dr. Satjipto Rahardjo',
    context: 'Teori Hukum Progresif',
  },
  {
    text: '"Negara hukum yang sejati adalah negara yang menempatkan hukum sebagai panglima tertinggi, bukan kekuasaan atau kehendak seorang individu"',
    author: 'Prof. Dr. Mochtar Kusumaatmadja',
    context: 'Mantan Ketua Mahkamah Konstitusi',
  },
  {
    text: '"Pancasila adalah dasar negara yang memberi arah pada seluruh hukum Indonesia. Tanpa Pancasila, hukum kehilangan jiwanya"',
    author: 'Prof. Dr. Jimly Asshiddiqie',
    context: 'Guru Besar Hukum Tata Negara UI',
  },
  {
    text: '"Hukum adat tidak tertulis tetapi berlaku living law — hukum yang hidup dalam masyarakat. Ketidaktertulisannya bukan berarti ketidakberlakuan"',
    author: 'Prof. Dr. Soerojo Wignyodipuro',
    context: 'Guru Besar Hukum Adat',
  },
  {
    text: '"Hukum harus bersifat adil, bijaksana, dan bermanfaat bagi rakyat. Tanpa ketiganya, hukum hanya akan menjadi sekadar teks tanpa jiwa"',
    author: 'M. Yahya Harahap',
    context: 'Hakim Agung & Pakar Hukum Acara',
  },
  {
    text: '"Permusyawaratan adalah jiwa dari demokrasi Indonesia. Dalam hukum, musyawarah berarti mencari keadilan substantif, bukan sekadar prosedural"',
    author: 'Prof. Dr. Jimly Asshiddiqie',
    context: 'Guru Besar Hukum Tata Negara UI',
  },
  {
    text: '"Pembagian kekuasaan bukan sekadar teknis, melainkan penjamin bahwa kebebasan individu tidak dapat diabaikan oleh satu tangan kekuasaan saja"',
    author: 'Charles-Louis de Secondat, Baron de Montesquieu',
    context: 'Teori Pemisahan Kekuasaan',
  },
  {
    text: '"Hukum Indonesia dibangun di atas tiga sendi: hukum adat, hukum Islam, dan hukum Barat (BW). Ketiganya saling memperkaya"',
    author: 'Prof. Dr. Soerojo Wignyodipuro',
    context: 'Guru Besar Hukum Adat',
  },
]

const QUOTE_INTERVAL_MS = 10000

export default function LegalQuoteBanner() {
  const [currentIndex, setCurrentIndex] = useState(0)
  const [isVisible, setIsVisible] = useState(true)

  useEffect(() => {
    const timer = setInterval(() => {
      setIsVisible(false)
      setTimeout(() => {
        setCurrentIndex((prev) => (prev + 1) % HERO_QUOTES.length)
        setIsVisible(true)
      }, 400)
    }, QUOTE_INTERVAL_MS)

    return () => clearInterval(timer)
  }, [])

  const quote = HERO_QUOTES[currentIndex]

  return (
    <div className="w-full max-w-3xl mx-auto mt-6 mb-2">
      <div
        className="relative overflow-hidden rounded-2xl border border-amber-200/60 bg-gradient-to-r from-amber-50 via-orange-50 to-amber-50 px-6 py-5"
        role="region"
        aria-label="Kutipan filosofi hukum Indonesia"
      >
        {/* Subtle gradient overlay */}
        <div className="absolute inset-0 bg-gradient-to-r from-amber-100/0 via-orange-50/30 to-amber-100/0 pointer-events-none" />

        <AnimatePresence mode="wait">
          {isVisible && (
            <motion.div
              key={currentIndex}
              initial={{ opacity: 0, y: 8 }}
              animate={{ opacity: 1, y: 0 }}
              exit={{ opacity: 0, y: -8 }}
              transition={{ duration: 0.4, ease: 'easeInOut' }}
              className="relative flex items-start gap-4"
            >
              {/* Scales icon */}
              <div className="flex-shrink-0 mt-0.5">
                <div className="w-8 h-8 bg-amber-200/60 rounded-xl flex items-center justify-center">
                  <Scale className="w-4 h-4 text-amber-700" />
                </div>
              </div>

              {/* Quote content */}
              <div className="flex-1 min-w-0">
                <p
                  className="font-serif text-base sm:text-lg leading-relaxed text-slate-800 italic"
                  style={{ fontFamily: '"DM Serif Display", Georgia, serif' }}
                >
                  {quote.text}
                </p>
                <div className="mt-2 flex items-center gap-2">
                  <span className="text-xs font-semibold text-amber-700">
                    {quote.author}
                  </span>
                  <span className="text-amber-400 text-xs">·</span>
                  <span className="text-xs text-amber-600/70 italic">
                    {quote.context}
                  </span>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>

        {/* Dot indicators */}
        <div className="relative mt-4 flex items-center gap-1.5 justify-center">
          {HERO_QUOTES.map((_, idx) => (
            <button
              key={idx}
              onClick={() => {
                setIsVisible(false)
                setTimeout(() => {
                  setCurrentIndex(idx)
                  setIsVisible(true)
                }, 300)
              }}
              aria-label={`Lihat kutipan ${idx + 1}`}
              className={`h-1.5 rounded-full transition-all duration-300 ${
                idx === currentIndex
                  ? 'w-5 bg-amber-500'
                  : 'w-1.5 bg-amber-300/50 hover:bg-amber-400/60'
              }`}
            />
          ))}
        </div>
      </div>
    </div>
  )
}