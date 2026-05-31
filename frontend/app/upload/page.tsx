'use client'

import AppShell from '../components/AppShell'
import DocumentManager from '../components/DocumentManager'

export default function UploadPage() {
  return (
    <AppShell>
      <div className="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        <div className="mb-8">
          <p className="text-xs text-slate-400 font-semibold uppercase tracking-wider mb-1">Admin</p>
          <h2 className="text-2xl font-bold text-slate-900 font-[family-name:var(--font-serif)]">
            Manajemen Dokumen
          </h2>
          <p className="text-sm text-slate-500 mt-1">
            Unggah dan kelola korpus dokumen peraturan perundang-undangan Indonesia.
          </p>
        </div>
        <DocumentManager />
      </div>
    </AppShell>
  )
}
