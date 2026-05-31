'use client'

import { AlertTriangle, ShieldCheck, Scale } from 'lucide-react'

interface LegalDisclaimerProps {
  /** Topic classification key (pidana/perdata/pajak/ketenagakerjaan/pertanahan/bisnis/administrasi) */
  topic?: string
  /** If true, show the high-stakes red warning banner */
  isHighStakes?: boolean
  /** Additional custom disclaimer text */
  customText?: string
}

/** Indonesian legal disclaimer text */
const STANDARD_DISCLAIMER =
  '⚖️ Informasi ini bersifat edukatif dan bukan pengganti konsultasi hukum profesional. Selalu verifikasi dengan sumber resmi dan konsultasikan dengan ahli hukum untuk kasus spesifik Anda.'

/** High-stakes warning text for pidana/pajak/ketenagakerjaan/pertanahan */
const HIGH_STAKES_WARNING =
  '⚠️ Topik ini memiliki konsekuensi hukum serius. Informasi yang diberikan mungkin tidak mencakup semua aspek. Sangat direkomendasikan untuk berkonsultasi dengan pengacara berlisensi atau kantor hukum resmi sebelum mengambil tindakan.'

/** Topic-specific additional disclaimers */
const TOPIC_ADDENDUMS: Record<string, string> = {
  pidana:
    '\n📌 Dalam kasus pidana, hak-hak Anda sebagai tersangka/terdakwa dilindungi oleh KUHAP. Hubungi penasihat hukum segera.',
  pajak:
    '\n📌 Isu perpajakan memiliki tenggat waktu ketat dan sanksi berat. Konsultasikan dengan konsultan pajak atau律师 pajak berlisensi.',
  ketenagakerjaan:
    '\n📌 Hubungan kerja diatur oleh UU Ketenagakerjaan dan PPaker. Setiap pelanggaran dapat berdampak pada hak-hak Anda sebagai pekerja.',
  pertanahan:
    '\n📌 Sertifikasi tanah memerlukan proses formal. Pastikan dokumen asli dan prosedur dari PPAT/Notaris resmi.',
}

export default function LegalDisclaimer({
  topic = 'umum',
  isHighStakes = false,
  customText,
}: LegalDisclaimerProps) {
  const topicLower = topic.toLowerCase()
  const topicAddendum = TOPIC_ADDENDUMS[topicLower] || null

  return (
    <div className="space-y-3">
      {/* Standard disclaimer — always shown */}
      <div className="flex items-start gap-3 bg-blue-50 border border-blue-200 rounded-xl px-4 py-3 text-sm text-blue-900">
        <Scale className="w-5 h-5 flex-shrink-0 mt-0.5 text-blue-600" />
        <span className="leading-relaxed">
          {STANDARD_DISCLAIMER}
          {customText && ` ${customText}`}
        </span>
      </div>

      {/* High-stakes red banner */}
      {isHighStakes && (
        <div className="flex items-start gap-3 bg-red-50 border border-red-300 rounded-xl px-4 py-3 text-sm text-red-900">
          <AlertTriangle className="w-5 h-5 flex-shrink-0 mt-0.5 text-red-600" />
          <span className="leading-relaxed">
            {HIGH_STAKES_WARNING}
            {topicAddendum && topicAddendum}
          </span>
        </div>
      )}

      {/* Topic-specific notice (non-high-stakes) */}
      {!isHighStakes && topicAddendum && (
        <div className="flex items-start gap-3 bg-amber-50 border border-amber-200 rounded-xl px-4 py-3 text-sm text-amber-900">
          <ShieldCheck className="w-5 h-5 flex-shrink-0 mt-0.5 text-amber-600" />
          <span className="leading-relaxed">{topicAddendum}</span>
        </div>
      )}
    </div>
  )
}