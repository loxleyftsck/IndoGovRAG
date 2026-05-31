'use client'

import { create } from 'zustand'

export type DocumentType = 'UU' | 'PP' | 'Perpres' | 'Permen' | 'Perda' | 'POJK' | 'SE'
export type StatusType = 'berlaku' | 'direvisi' | 'dicabut' | 'semua'
export type SortType = 'relevansi' | 'terbaru' | 'terlama' | 'paling-dikutip'

export interface SearchState {
  query: string
  jenis: DocumentType[]
  status: StatusType
  tahunDari: number | null
  tahunSampai: number | null
  instansi: string
  sort: SortType
  page: number
  confidence: number | null
  isSettingsOpen: boolean
  // Actions
  setQuery: (q: string) => void
  setJenis: (j: DocumentType[]) => void
  setStatus: (s: StatusType) => void
  setTahunRange: (dari: number | null, sampai: number | null) => void
  setInstansi: (i: string) => void
  setSort: (s: SortType) => void
  setPage: (p: number) => void
  setConfidence: (c: number | null) => void
  setSettingsOpen: (open: boolean) => void
  reset: () => void
  hasActiveFilters: () => boolean
}

const initial = {
  query: '',
  jenis: [] as DocumentType[],
  status: 'berlaku' as StatusType,
  tahunDari: null,
  tahunSampai: null,
  instansi: '',
  sort: 'relevansi' as SortType,
  page: 1,
  confidence: null,
  isSettingsOpen: false,
}

export const useSearchStore = create<SearchState>((set, get) => ({
  ...initial,

  setQuery: (q) => set({ query: q }),
  setJenis: (j) => set({ jenis: j, page: 1 }),
  setStatus: (s) => set({ status: s, page: 1 }),
  setTahunRange: (dari, sampai) => set({ tahunDari: dari, tahunSampai: sampai, page: 1 }),
  setInstansi: (i) => set({ instansi: i, page: 1 }),
  setSort: (s) => set({ sort: s, page: 1 }),
  setPage: (p) => set({ page: p }),
  setConfidence: (c) => set({ confidence: c }),
  setSettingsOpen: (open) => set({ isSettingsOpen: open }),

  reset: () => set({ ...initial }),

  hasActiveFilters: () => {
    const s = get()
    return (
      s.jenis.length > 0 ||
      s.status !== 'berlaku' ||
      s.tahunDari !== null ||
      s.tahunSampai !== null ||
      s.instansi !== '' ||
      s.sort !== 'relevansi' ||
      s.confidence !== null
    )
  },
}))