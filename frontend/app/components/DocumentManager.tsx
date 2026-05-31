'use client'

import { useState, useCallback, useRef, useEffect } from 'react'
import {
  Upload,
  FileText,
  RefreshCw,
  X,
  CheckCircle,
  AlertCircle,
  Loader,
  Database,
  File,
  Trash,
  HardDriveDownload,
  Layers,
  FolderOpen,
  Tag,
  ChevronDown,
} from 'lucide-react'

interface UploadedFile {
  file_id: string
  file_name: string
  category: string
  doc_type: string
  chunks_count: number
  status: string
}

interface FileStats {
  total_chunks: number
  unique_files: number
  categories: Record<string, number>
  collection_name: string
}

interface UploadProgress {
  filename: string
  progress: number
  status: 'uploading' | 'processing' | 'done' | 'error'
  message?: string
}

export default function DocumentManager() {
  const [files, setFiles] = useState<UploadedFile[]>([])
  const [stats, setStats] = useState<FileStats | null>(null)
  const [uploads, setUploads] = useState<UploadProgress[]>([])
  const [isDragging, setIsDragging] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const [successBanner, setSuccessBanner] = useState<{ count: number; visible: boolean } | null>(null)
  const fileInputRef = useRef<HTMLInputElement>(null)

  const fetchFiles = useCallback(async () => {
    try {
      const resp = await fetch('http://localhost:8000/files')
      const data = await resp.json()
      setFiles(data.files || [])
    } catch {
      // silently fail on refresh
    }
  }, [])

  const fetchStats = useCallback(async () => {
    try {
      const resp = await fetch('http://localhost:8000/stats')
      const data = await resp.json()
      setStats(data)
    } catch {
      // silently fail on refresh
    }
  }, [])

  useEffect(() => {
    fetchFiles()
    fetchStats()
  }, [fetchFiles, fetchStats])

  // Auto-dismiss success banner after 4s
  useEffect(() => {
    if (successBanner?.visible) {
      const t = setTimeout(() => setSuccessBanner(null), 4000)
      return () => clearTimeout(t)
    }
  }, [successBanner])

  const handleDragOver = (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(true)
  }

  const handleDragLeave = () => {
    setIsDragging(false)
  }

  const handleDrop = async (e: React.DragEvent) => {
    e.preventDefault()
    setIsDragging(false)
    const droppedFiles = Array.from(e.dataTransfer.files)
    if (droppedFiles.length > 0) await uploadFiles(droppedFiles)
  }

  const handleFileSelect = async (e: React.ChangeEvent<HTMLInputElement>) => {
    const selectedFiles = Array.from(e.target.files || [])
    if (selectedFiles.length > 0) await uploadFiles(selectedFiles)
    if (fileInputRef.current) fileInputRef.current.value = ''
  }

  const uploadFiles = async (filesToUpload: File[]) => {
    setError(null)
    const allowedExts = ['.txt', '.pdf', '.doc', '.docx', '.md']
    const validFiles = filesToUpload.filter(f => {
      const ext = '.' + f.name.split('.').pop()?.toLowerCase()
      return allowedExts.includes(ext)
    })

    if (validFiles.length === 0) {
      setError('Tidak ada file valid. Didukung: .txt, .pdf, .doc, .docx, .md')
      return
    }

    const startIdx = uploads.length
    const newUploads: UploadProgress[] = validFiles.map(f => ({
      filename: f.name,
      progress: 0,
      status: 'uploading' as const,
    }))
    setUploads(prev => [...prev, ...newUploads])

    let successCount = 0

    for (let i = 0; i < validFiles.length; i++) {
      const file = validFiles[i]
      const uploadIdx = startIdx + i

      // Simulate progress animation
      let progressVal = 0
      const progressInterval = setInterval(() => {
        progressVal = Math.min(progressVal + Math.random() * 15, 85)
        setUploads(prev => prev.map((u, idx) =>
          idx === uploadIdx ? { ...u, progress: Math.round(progressVal) } : u
        ))
      }, 300)

      try {
        setUploads(prev => prev.map((u, idx) =>
          idx === uploadIdx ? { ...u, status: 'processing' } : u
        ))

        const formData = new FormData()
        formData.append('file', file)
        formData.append('category', 'general')

        const response = await fetch('http://localhost:8000/upload/file', {
          method: 'POST',
          body: formData,
        })

        clearInterval(progressInterval)

        const result = await response.json()

        if (result.success) {
          successCount++
          setUploads(prev => prev.map((u, idx) =>
            idx === uploadIdx ? { ...u, progress: 100, status: 'done', message: result.message } : u
          ))
        } else {
          setUploads(prev => prev.map((u, idx) =>
            idx === uploadIdx ? { ...u, progress: 0, status: 'error', message: result.message } : u
          ))
        }
      } catch {
        clearInterval(progressInterval)
        setUploads(prev => prev.map((u, idx) =>
          idx === uploadIdx ? { ...u, progress: 0, status: 'error', message: 'Upload gagal' } : u
        ))
      }
    }

    if (successCount > 0) {
      setSuccessBanner({ count: successCount, visible: true })
      setTimeout(() => {
        fetchFiles()
        fetchStats()
      }, 1500)
    }
  }

  const deleteFile = async (fileId: string) => {
    if (!confirm('Hapus file ini beserta semua chunks-nya?')) return
    try {
      const resp = await fetch(`http://localhost:8000/upload/delete/${fileId}`, { method: 'DELETE' })
      const result = await resp.json()
      if (result.success) {
        setFiles(prev => prev.filter(f => f.file_id !== fileId))
        fetchStats()
      } else {
        setError(result.message)
      }
    } catch {
      setError('Gagal menghapus file')
    }
  }

  const clearAllFiles = async () => {
    if (!confirm('Hapus SEMUA file dan chunks? Tindakan ini tidak dapat dibatalkan!')) return
    try {
      const resp = await fetch('http://localhost:8000/files/clear', { method: 'DELETE' })
      const result = await resp.json()
      if (result.success) {
        setFiles([])
        fetchStats()
      } else {
        setError(result.message)
      }
    } catch {
      setError('Gagal menghapus semua file')
    }
  }

  const downloadAllMetadata = async () => {
    if (!stats) return
    const blob = new Blob([JSON.stringify(stats, null, 2)], { type: 'application/json' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = `indogov-metadata-${new Date().toISOString().slice(0, 10)}.json`
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <div className="space-y-5">

      {/* Page header */}
      <div className="flex items-center justify-between">
        <div className="flex items-center gap-3">
          <div className="w-11 h-11 indigo-gradient rounded-xl flex items-center justify-center shadow-sm">
            <Database className="w-5 h-5 text-white" />
          </div>
          <div>
            <h2 className="text-xl font-bold font-serif text-slate-900">Kelola Dokumen</h2>
            <p className="text-sm text-slate-500">Unggah dan kelola dokumen untuk indexing RAG</p>
          </div>
        </div>
        <div className="flex items-center gap-2">
          <button
            onClick={() => { fetchFiles(); fetchStats() }}
            className="px-4 py-2 bg-white border border-slate-200 hover:border-indigo-300 hover:bg-indigo-50 text-slate-700 hover:text-indigo-700 rounded-xl flex items-center gap-2 transition-all text-sm font-semibold"
          >
            <RefreshCw className="w-4 h-4" />
            Refresh
          </button>
          {files.length > 0 && (
            <button
              onClick={clearAllFiles}
              className="px-4 py-2 bg-white border border-red-200 hover:border-red-300 hover:bg-red-50 text-red-600 hover:text-red-700 rounded-xl flex items-center gap-2 transition-all text-sm font-semibold"
            >
              <Trash className="w-4 h-4" />
              Hapus Semua
            </button>
          )}
        </div>
      </div>

      {/* Stats cards */}
      {stats && (
        <div className="grid grid-cols-3 gap-4">
          <div className="bg-white rounded-2xl border border-slate-200 p-5 text-center">
            <div className="w-9 h-9 bg-indigo-50 rounded-xl flex items-center justify-center mx-auto mb-3">
              <Layers className="w-4 h-4 text-indigo-600" />
            </div>
            <p className="text-2xl font-bold text-slate-900">{stats.total_chunks.toLocaleString('id-ID')}</p>
            <p className="text-xs text-slate-500 mt-1 font-medium">Total Chunks</p>
          </div>
          <div className="bg-white rounded-2xl border border-slate-200 p-5 text-center">
            <div className="w-9 h-9 bg-emerald-50 rounded-xl flex items-center justify-center mx-auto mb-3">
              <FolderOpen className="w-4 h-4 text-emerald-600" />
            </div>
            <p className="text-2xl font-bold text-slate-900">{stats.unique_files.toLocaleString('id-ID')}</p>
            <p className="text-xs text-slate-500 mt-1 font-medium">File Unik</p>
          </div>
          <div className="bg-white rounded-2xl border border-slate-200 p-5 text-center">
            <div className="w-9 h-9 bg-violet-50 rounded-xl flex items-center justify-center mx-auto mb-3">
              <Tag className="w-4 h-4 text-violet-600" />
            </div>
            <p className="text-2xl font-bold text-slate-900">{Object.keys(stats.categories).length}</p>
            <p className="text-xs text-slate-500 mt-1 font-medium">Kategori</p>
          </div>
        </div>
      )}

      {/* Success banner */}
      {successBanner?.visible && (
        <div className="bg-green-50 border border-green-200 rounded-xl p-3 flex items-center gap-3">
          <div className="w-8 h-8 bg-green-100 rounded-lg flex items-center justify-center shrink-0">
            <CheckCircle className="w-4 h-4 text-green-600" />
          </div>
          <p className="text-sm font-semibold text-green-800">
            {successBanner.count} dokumen berhasil diunggah
          </p>
          <button
            onClick={() => setSuccessBanner(null)}
            className="ml-auto p-1 text-green-500 hover:text-green-700 transition-colors"
          >
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Drop zone */}
      <div
        onDragOver={handleDragOver}
        onDragLeave={handleDragLeave}
        onDrop={handleDrop}
        onClick={() => fileInputRef.current?.click()}
        className={`
          border-2 border-dashed rounded-2xl p-12 text-center cursor-pointer
          transition-all duration-200
          ${isDragging
            ? 'border-indigo-400 bg-indigo-50'
            : 'border-slate-300 hover:border-indigo-300 hover:bg-indigo-50/30'
          }
        `}
      >
        <input
          ref={fileInputRef}
          type="file"
          multiple
          accept=".txt,.pdf,.doc,.docx,.md"
          onChange={handleFileSelect}
          className="hidden"
        />

        <div className={`w-16 h-16 mx-auto mb-4 rounded-2xl flex items-center justify-center transition-all duration-200 ${isDragging ? 'bg-indigo-100' : 'bg-slate-100'}`}>
          <Upload className={`w-8 h-8 transition-colors ${isDragging ? 'text-indigo-600' : 'text-slate-400'}`} />
        </div>

        <h3 className="text-lg font-semibold text-slate-900 mb-2">
          {isDragging ? 'Lepaskan untuk mengunggah!' : 'Drag & Drop dokumen'}
        </h3>
        <p className="text-sm text-slate-500 mb-2">atau klik untuk memilih file</p>
        <p className="text-xs text-slate-400">Didukung: .txt, .pdf, .doc, .docx, .md</p>
        {files.length === 0 && !uploads.length && (
          <div className="mt-4 flex flex-col items-center gap-1">
            <p className="text-xs text-slate-400">Unggah dokumen pertama untuk memulai indexing RAG</p>
            <ChevronDown className="w-4 h-4 text-indigo-400 animate-bounce" />
          </div>
        )}
      </div>

      {/* Error display */}
      {error && (
        <div className="flex items-center gap-2 p-4 bg-red-50 border border-red-200 rounded-xl">
          <AlertCircle className="w-5 h-5 text-red-600 flex-shrink-0" />
          <p className="text-sm text-red-700 flex-1">{error}</p>
          <button onClick={() => setError(null)} className="text-red-500 hover:text-red-700 transition-colors">
            <X className="w-4 h-4" />
          </button>
        </div>
      )}

      {/* Upload progress */}
      {uploads.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 p-5">
          <h3 className="font-bold text-slate-900 mb-4 text-sm">Progress Unggah</h3>
          <div className="space-y-3">
            {uploads.map((upload, idx) => (
              <div
                key={idx}
                className="bg-white rounded-xl border border-slate-200 p-4 mb-2 hover:shadow-sm transition-shadow"
              >
                <div className="flex items-center gap-3 mb-2">
                  <File className="w-4 h-4 text-slate-400 shrink-0" />
                  <p className="text-sm font-medium text-slate-800 truncate flex-1">{upload.filename}</p>
                  <div className="flex items-center gap-1.5 shrink-0">
                    {upload.status === 'uploading' && <Loader className="w-3.5 h-3.5 animate-spin text-indigo-500" />}
                    {upload.status === 'processing' && <Loader className="w-3.5 h-3.5 animate-spin text-amber-500" />}
                    {upload.status === 'done' && <CheckCircle className="w-3.5 h-3.5 text-green-500" />}
                    {upload.status === 'error' && <AlertCircle className="w-3.5 h-3.5 text-red-500" />}
                    <span className="text-xs text-slate-500">
                      {upload.status === 'uploading' && 'Mengunggah...'}
                      {upload.status === 'processing' && 'Memproses & indexing...'}
                      {upload.status === 'done' && 'Selesai'}
                      {upload.status === 'error' && (upload.message || 'Error')}
                    </span>
                  </div>
                </div>
                {(upload.status === 'uploading' || upload.status === 'processing') && (
                  <div className="h-1.5 bg-slate-100 rounded-full overflow-hidden">
                    <div
                      className="h-full rounded-full transition-all duration-500 bg-indigo-500"
                      style={{ width: `${upload.progress}%` }}
                    />
                  </div>
                )}
              </div>
            ))}
          </div>
        </div>
      )}

      {/* File list */}
      {files.length > 0 && (
        <div className="bg-white rounded-2xl border border-slate-200 shadow-sm overflow-hidden">
          <div className="px-6 py-4 border-b border-slate-200 flex items-center justify-between">
            <h3 className="font-bold text-slate-900 text-sm">File Terindex ({files.length})</h3>
            <button
              onClick={downloadAllMetadata}
              className="text-sm text-indigo-600 hover:text-indigo-800 flex items-center gap-1.5 font-semibold transition-colors"
            >
              <HardDriveDownload className="w-4 h-4" />
              Export JSON
            </button>
          </div>
          <div className="divide-y divide-slate-100 max-h-96 overflow-y-auto">
            {files.map((file) => (
              <div
                key={file.file_id}
                className="px-6 py-4 flex items-center gap-4 hover:bg-slate-50 transition-colors group"
              >
                <div className="w-10 h-10 bg-indigo-50 rounded-xl flex items-center justify-center shrink-0">
                  <FileText className="w-5 h-5 text-indigo-600" />
                </div>
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-slate-900 truncate">{file.file_name}</p>
                  <div className="flex items-center gap-3 mt-1">
                    <span className="px-2 py-0.5 bg-indigo-50 text-indigo-700 rounded-full text-[10px] font-semibold uppercase">
                      {file.doc_type || 'Dokumen'}
                    </span>
                    <span className="text-xs text-slate-500">{file.chunks_count} chunks</span>
                    <span className={`px-2 py-0.5 rounded-full text-xs font-semibold ${
                      file.status === 'indexed'
                        ? 'bg-green-50 text-green-700'
                        : 'bg-amber-50 text-amber-700'
                    }`}>
                      {file.status === 'indexed' ? 'Terindeks' : file.status}
                    </span>
                  </div>
                </div>
                <button
                  onClick={() => deleteFile(file.file_id)}
                  className="p-2 text-slate-400 hover:text-red-600 transition-colors opacity-0 group-hover:opacity-100 shrink-0"
                >
                  <Trash className="w-4 h-4" />
                </button>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Empty state */}
      {files.length === 0 && uploads.filter(u => u.status !== 'done').length === 0 && (
        <div className="text-center py-14 bg-slate-50 rounded-2xl border border-dashed border-slate-300">
          <div className="w-14 h-14 bg-slate-100 rounded-2xl flex items-center justify-center mx-auto mb-4">
            <FileText className="w-7 h-7 text-slate-400" />
          </div>
          <p className="text-slate-700 font-semibold text-sm">Belum ada dokumen terunggah</p>
          <p className="text-sm text-slate-400 mt-1">Seret & lepas file PDF di atas untuk memulai</p>
          <div className="mt-4 flex flex-wrap justify-center gap-2">
            {['UU', 'PP', 'Perpres', 'Permen'].map(t => (
              <span key={t} className="px-3 py-1.5 bg-white border border-slate-200 rounded-xl text-xs text-slate-500 font-medium">
                {t}
              </span>
            ))}
          </div>
        </div>
      )}

    </div>
  )
}