'use client'

import { useState, useEffect } from 'react'
import Link from 'next/link'
import {
  BarChart, Bar, LineChart, Line, XAxis, YAxis, CartesianGrid,
  Tooltip, ResponsiveContainer, Area, AreaChart
} from 'recharts'
import {
  Search, Users, Clock, TrendingUp, AlertTriangle,
  ChevronRight, Shield, RefreshCw, BarChart2, ShieldCheck
} from 'lucide-react'

// ─── Types ───────────────────────────────────────────────────────────────────
interface TopQuery {
  query: string
  count: number
}

interface ZeroResult {
  query: string
  last_seen: string
}

interface AnalyticsData {
  total_queries: number
  unique_users: number
  zero_result_queries: ZeroResult[]
  top_queries: TopQuery[]
  avg_confidence: number
  avg_response_time_ms: number
  p50_ms: number
  p95_ms: number
  p99_ms: number
  daily_users: Record<string, number>
}

// ─── Custom chart tooltip ───────────────────────────────────────────────────
function ChartTooltip({ active, payload, label }: any) {
  if (!active || !payload?.length) return null
  return (
    <div className="bg-white border border-slate-200 rounded-xl shadow-lg p-3 text-xs">
      <p className="font-semibold text-slate-700 mb-1">{label}</p>
      {payload.map((p: any, i: number) => (
        <p key={i} style={{ color: p.color }}>
          {p.name}: {typeof p.value === 'number' && p.name.toLowerCase().includes('ms')
            ? `${p.value}ms`
            : p.name === 'confidence'
              ? `${(p.value * 100).toFixed(1)}%`
              : p.value}
        </p>
      ))}
    </div>
  )
}

// ─── Admin Gate ──────────────────────────────────────────────────────────────
function AdminGate({ children }: { children: React.ReactNode }) {
  const [authorized, setAuthorized] = useState(false)
  const [tokenInput, setTokenInput] = useState('')
  const adminToken = process.env.NEXT_PUBLIC_ADMIN_TOKEN || ''

  useEffect(() => {
    if (!adminToken) {
      setAuthorized(true)
    } else if (sessionStorage.getItem('admin_token') === adminToken) {
      setAuthorized(true)
    }
  }, [adminToken])

  if (!authorized && adminToken) {
    const handleLogin = () => {
      if (tokenInput === adminToken) {
        sessionStorage.setItem('admin_token', tokenInput)
        setAuthorized(true)
      }
    }

    return (
      <div className="min-h-screen bg-slate-50 flex items-center justify-center px-4">
        <div className="w-full max-w-sm bg-white rounded-2xl border border-slate-200 shadow-sm p-8">
          <div className="flex items-center gap-3 mb-6">
            <div className="w-10 h-10 bg-indigo-100 rounded-xl flex items-center justify-center">
              <Shield className="w-5 h-5 text-indigo-600" />
            </div>
            <div>
              <h2 className="text-lg font-bold text-slate-900">Admin Access</h2>
              <p className="text-xs text-slate-500">Enter your admin token</p>
            </div>
          </div>
          <input
            type="password"
            value={tokenInput}
            onChange={e => setTokenInput(e.target.value)}
            onKeyDown={e => e.key === 'Enter' && handleLogin()}
            placeholder="Admin token..."
            className="w-full border border-slate-200 rounded-xl px-4 py-3 mb-4 text-sm focus:outline-none focus:border-indigo-400 focus:ring-2 focus:ring-indigo-100 transition-all"
          />
          {tokenInput && (
            <p className="text-xs text-red-500 mb-3">Invalid token. Try again.</p>
          )}
          <button
            onClick={handleLogin}
            className="w-full bg-indigo-700 hover:bg-indigo-800 text-white font-semibold py-3 rounded-xl transition-colors"
          >
            Sign In
          </button>
        </div>
      </div>
    )
  }

  return <>{children}</>
}

// ─── Stat Card ───────────────────────────────────────────────────────────────
function StatCard({
  icon, label, value, sub, color = 'blue', href
}: {
  icon: React.ReactNode
  label: string
  value: string | number
  sub?: string
  color?: string
  href?: string
}) {
  const colorMap: Record<string, { bg: string; text: string; border: string }> = {
    blue:   { bg: 'bg-blue-50',    text: 'text-blue-600',    border: 'border-blue-100' },
    green:  { bg: 'bg-green-50',   text: 'text-green-600',   border: 'border-green-100' },
    purple: { bg: 'bg-purple-50', text: 'text-purple-600',  border: 'border-purple-100' },
    amber:  { bg: 'bg-amber-50',   text: 'text-amber-600',   border: 'border-amber-100' },
    red:    { bg: 'bg-red-50',     text: 'text-red-600',     border: 'border-red-100' },
  }
  const c = colorMap[color] ?? colorMap.blue

  const content = (
    <div className={`rounded-2xl border ${c.border} ${c.bg} p-5`}>
      <div className="flex items-center justify-between mb-3">
        <span className="text-xs font-semibold text-slate-600 uppercase tracking-wide">{label}</span>
        <div className={`w-8 h-8 rounded-lg flex items-center justify-center bg-white/70 ${c.text}`}>
          {icon}
        </div>
      </div>
      <p className="text-2xl font-bold text-slate-900">{value}</p>
      {sub && <p className="text-xs text-slate-500 mt-1">{sub}</p>}
    </div>
  )

  if (href) return <Link href={href} className="block">{content}</Link>
  return content
}

// ─── Chart card wrapper ──────────────────────────────────────────────────────
function ChartCard({
  title, icon, iconColor, children, action
}: {
  title: string
  icon: React.ReactNode
  iconColor?: string
  children: React.ReactNode
  action?: React.ReactNode
}) {
  return (
    <div className="bg-white rounded-2xl border border-slate-200 p-5">
      <div className="flex items-center justify-between mb-4">
        <div className="flex items-center gap-2">
          <span className={iconColor ?? 'text-slate-600'}>{icon}</span>
          <h3 className="text-base font-bold text-slate-900">{title}</h3>
        </div>
        {action}
      </div>
      {children}
    </div>
  )
}

// ─── Empty state ─────────────────────────────────────────────────────────────
function EmptyState({ icon, title, subtitle }: { icon: React.ReactNode; title: string; subtitle: string }) {
  return (
    <div className="flex flex-col items-center justify-center py-12 text-center">
      <div className="w-12 h-12 bg-slate-100 rounded-2xl flex items-center justify-center mb-3 text-slate-400">
        {icon}
      </div>
      <p className="text-sm font-semibold text-slate-600 mb-1">{title}</p>
      <p className="text-xs text-slate-400">{subtitle}</p>
    </div>
  )
}

// ─── Main Dashboard ──────────────────────────────────────────────────────────
export default function AnalyticsPage() {
  const [data, setData] = useState<AnalyticsData | null>(null)
  const [loading, setLoading] = useState(true)
  const [error, setError] = useState<string | null>(null)
  const [lastRefresh, setLastRefresh] = useState<Date | null>(null)

  const API_BASE = 'http://localhost:8000'

  const fetchAnalytics = async () => {
    setLoading(true)
    setError(null)
    try {
      const res = await fetch(`${API_BASE}/api/analytics/summary`)
      if (!res.ok) throw new Error(`HTTP ${res.status}`)
      const json = await res.json()
      setData(json)
      setLastRefresh(new Date())
    } catch (e) {
      setError(e instanceof Error ? e.message : 'Failed to load analytics')
    } finally {
      setLoading(false)
    }
  }

  useEffect(() => { fetchAnalytics() }, [])

  // ── Chart data ──────────────────────────────────────────────────────────────
  const dailyChartData = data
    ? Object.entries(data.daily_users)
        .sort(([a], [b]) => a.localeCompare(b))
        .map(([date, count]) => ({ date, queries: count }))
    : []

  const topQueriesData = data
    ? data.top_queries.slice(0, 10).map(q => ({
        name: q.query.length > 40 ? q.query.slice(0, 40) + '…' : q.query,
        count: q.count,
      }))
    : []

  const responseTimeData = data
    ? [
        { label: 'p50', value: data.p50_ms },
        { label: 'p95', value: data.p95_ms },
        { label: 'p99', value: data.p99_ms },
      ]
    : []

  return (
    <AdminGate>
      <div className="min-h-screen bg-slate-50">

        {/* ── Top Nav ── */}
        <header className="bg-white border-b border-slate-200 sticky top-0 z-10">
          <div className="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between">
            <div className="flex items-center gap-4">
              {/* Back link */}
              <Link
                href="/admin"
                className="text-sm text-slate-500 hover:text-indigo-600 transition-colors hidden sm:block"
              >
                ← Kembali
              </Link>
              {/* Logo + breadcrumb */}
              <Link href="/admin" className="flex items-center gap-3 group">
                <div className="w-9 h-9 bg-indigo-700 rounded-xl flex items-center justify-center">
                  <BarChart2 className="w-5 h-5 text-white" />
                </div>
                <div>
                  <div className="flex items-center gap-1.5 mb-0.5">
                    <span className="text-xs text-slate-400">Admin</span>
                    <span className="text-xs text-slate-300">/</span>
                    <span className="text-xs text-slate-500">Analytics</span>
                  </div>
                  <h1 className="text-base font-bold text-slate-900 leading-tight">Analisis Pencarian</h1>
                </div>
              </Link>
            </div>

            <div className="flex items-center gap-4">
              {lastRefresh && (
                <span className="text-xs text-slate-400 hidden sm:block">
                  Diperbarui {lastRefresh.toLocaleTimeString('id-ID', { hour: '2-digit', minute: '2-digit' })}
                </span>
              )}
              <button
                onClick={fetchAnalytics}
                disabled={loading}
                className="flex items-center gap-2 px-4 py-2 bg-indigo-700 hover:bg-indigo-800 disabled:opacity-50 text-white text-sm font-semibold rounded-xl transition-colors shadow-sm"
              >
                <RefreshCw className={`w-4 h-4 ${loading ? 'animate-spin' : ''}`} />
                Refresh
              </button>
            </div>
          </div>
        </header>

        <main className="max-w-7xl mx-auto px-6 py-8 space-y-8">

          {/* ── Error state ── */}
          {error && (
            <div className="bg-red-50 border border-red-200 rounded-2xl p-5 flex items-start gap-3">
              <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0 mt-0.5" />
              <div className="flex-1 min-w-0">
                <p className="text-sm font-semibold text-red-800">Gagal memuat data analytics</p>
                <p className="text-xs text-red-600 mt-0.5">{error}</p>
              </div>
              <button
                onClick={fetchAnalytics}
                className="px-3 py-1.5 bg-red-100 hover:bg-red-200 text-red-700 text-xs font-semibold rounded-lg transition-colors shrink-0"
              >
                Coba Lagi
              </button>
            </div>
          )}

          {/* ── Loading skeleton ── */}
          {loading && !data && (
            <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
              {[...Array(4)].map((_, i) => (
                <div key={i} className="bg-white rounded-2xl border border-slate-200 h-28 animate-pulse" />
              ))}
            </div>
          )}

          {data && (
            <>

              {/* ── Stats row 1: top-level KPIs ── */}
              <div className="grid grid-cols-2 lg:grid-cols-4 gap-4">
                <StatCard
                  icon={<Search className="w-4 h-4" />}
                  label="Total Queries"
                  value={data.total_queries.toLocaleString('id-ID')}
                  sub="semua waktu"
                  color="blue"
                />
                <StatCard
                  icon={<Users className="w-4 h-4" />}
                  label="Unique Users"
                  value={data.unique_users.toLocaleString('id-ID')}
                  sub="pengguna unik"
                  color="green"
                />
                <StatCard
                  icon={<TrendingUp className="w-4 h-4" />}
                  label="Avg Confidence"
                  value={`${(data.avg_confidence * 100).toFixed(1)}%`}
                  sub="skor rata-rata"
                  color="purple"
                />
                <StatCard
                  icon={<Clock className="w-4 h-4" />}
                  label="Avg Response"
                  value={`${data.avg_response_time_ms.toFixed(0)}ms`}
                  sub="waktu respons rata-rata"
                  color="amber"
                />
              </div>

              {/* ── Stats row 2: latency percentiles ── */}
              <div className="grid grid-cols-3 gap-4">
                <StatCard
                  icon={<Clock className="w-4 h-4" />}
                  label="p50 Latency"
                  value={`${data.p50_ms.toFixed(0)}ms`}
                  sub="median"
                  color="blue"
                />
                <StatCard
                  icon={<Clock className="w-4 h-4" />}
                  label="p95 Latency"
                  value={`${data.p95_ms.toFixed(0)}ms`}
                  sub="95th percentile"
                  color="amber"
                />
                <StatCard
                  icon={<Clock className="w-4 h-4" />}
                  label="p99 Latency"
                  value={`${data.p99_ms.toFixed(0)}ms`}
                  sub="99th percentile"
                  color="red"
                />
              </div>

              {/* ── Charts grid ── */}
              <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">

                {/* Daily query volume */}
                <ChartCard
                  title="Volume Query Harian"
                  icon={<BarChart2 className="w-4 h-4" />}
                  iconColor="text-blue-600"
                >
                  {dailyChartData.length === 0 ? (
                    <EmptyState
                      icon={<BarChart2 className="w-6 h-6" />}
                      title="Belum ada data"
                      subtitle="Query akan muncul di sini setelah penggunaan dimulai"
                    />
                  ) : (
                    <ResponsiveContainer width="100%" height={200}>
                      <AreaChart data={dailyChartData}>
                        <defs>
                          <linearGradient id="queryGrad" x1="0" y1="0" x2="0" y2="1">
                            <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.15} />
                            <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
                          </linearGradient>
                        </defs>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" />
                        <XAxis
                          dataKey="date"
                          tick={{ fontSize: 11, fill: '#94a3b8' }}
                          tickFormatter={v => v.slice(5)}
                          axisLine={false}
                          tickLine={false}
                        />
                        <YAxis
                          tick={{ fontSize: 11, fill: '#94a3b8' }}
                          allowDecimals={false}
                          axisLine={false}
                          tickLine={false}
                        />
                        <Tooltip content={<ChartTooltip />} />
                        <Area
                          type="monotone"
                          dataKey="queries"
                          stroke="#3b82f6"
                          fill="url(#queryGrad)"
                          strokeWidth={2}
                          name="queries"
                        />
                      </AreaChart>
                    </ResponsiveContainer>
                  )}
                </ChartCard>

                {/* Top 10 queries */}
                <ChartCard
                  title="Top 10 Query"
                  icon={<TrendingUp className="w-4 h-4" />}
                  iconColor="text-green-600"
                >
                  {topQueriesData.length === 0 ? (
                    <EmptyState
                      icon={<TrendingUp className="w-6 h-6" />}
                      title="Belum ada query"
                      subtitle="Query populer akan muncul di sini"
                    />
                  ) : (
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={topQueriesData} layout="vertical" margin={{ left: 0, right: 16 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" horizontal={false} />
                        <XAxis
                          type="number"
                          tick={{ fontSize: 11, fill: '#94a3b8' }}
                          axisLine={false}
                          tickLine={false}
                        />
                        <YAxis
                          dataKey="name"
                          type="category"
                          tick={{ fontSize: 10, fill: '#64748b' }}
                          width={140}
                          axisLine={false}
                          tickLine={false}
                        />
                        <Tooltip content={<ChartTooltip />} />
                        <Bar dataKey="count" fill="#22c55e" radius={[0, 4, 4, 0]} name="searches" />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </ChartCard>

                {/* Confidence trend */}
                <ChartCard
                  title="Tren Confidence"
                  icon={<TrendingUp className="w-4 h-4" />}
                  iconColor="text-purple-600"
                >
                  {dailyChartData.length < 2 ? (
                    <EmptyState
                      icon={<TrendingUp className="w-6 h-6" />}
                      title="Data belum cukup"
                      subtitle="Minimal 2 hari data diperlukan untuk menampilkan tren"
                    />
                  ) : (
                    <div className="flex items-center gap-3 mb-3 px-1">
                      <span className="text-2xl font-bold text-slate-900">
                        {(data.avg_confidence * 100).toFixed(1)}%
                      </span>
                      <span className="text-xs text-slate-500">confidence rata-rata keseluruhan</span>
                    </div>
                  )}
                </ChartCard>

                {/* Response time distribution */}
                <ChartCard
                  title="Distribusi Response Time"
                  icon={<Clock className="w-4 h-4" />}
                  iconColor="text-amber-600"
                >
                  {responseTimeData.length === 0 ? (
                    <EmptyState
                      icon={<Clock className="w-6 h-6" />}
                      title="Belum ada data"
                      subtitle="Data latency akan muncul di sini"
                    />
                  ) : (
                    <ResponsiveContainer width="100%" height={200}>
                      <BarChart data={responseTimeData} margin={{ left: 0, right: 16 }}>
                        <CartesianGrid strokeDasharray="3 3" stroke="#f1f5f9" vertical={false} />
                        <XAxis dataKey="label" tick={{ fontSize: 12, fill: '#94a3b8' }} axisLine={false} tickLine={false} />
                        <YAxis
                          tick={{ fontSize: 11, fill: '#94a3b8' }}
                          axisLine={false}
                          tickLine={false}
                          tickFormatter={v => `${v}ms`}
                        />
                        <Tooltip content={<ChartTooltip />} />
                        <Bar dataKey="value" fill="#f59e0b" radius={[6, 6, 0, 0]} name="latency" />
                      </BarChart>
                    </ResponsiveContainer>
                  )}
                </ChartCard>

              </div>

              {/* ── Zero-result queries ── */}
              <div className="bg-white rounded-2xl border border-slate-200 p-5">
                <div className="flex items-center gap-2 mb-4">
                  <AlertTriangle className="w-4 h-4 text-red-500" />
                  <h3 className="text-base font-bold text-slate-900">Query Tanpa Hasil</h3>
                  {data.zero_result_queries.length > 0 && (
                    <span className="ml-1 px-2 py-0.5 bg-red-100 text-red-700 text-xs font-bold rounded-full">
                      {data.zero_result_queries.length}
                    </span>
                  )}
                  <span className="ml-auto text-xs text-slate-400">yang perlu ditindaklanjuti</span>
                </div>

                {data.zero_result_queries.length === 0 ? (
                  <div className="flex items-center gap-3 py-6 text-center justify-center">
                    <div className="w-10 h-10 bg-green-50 rounded-xl flex items-center justify-center">
                      <ShieldCheck className="w-5 h-5 text-green-600" />
                    </div>
                    <div>
                      <p className="text-sm font-semibold text-green-700">Tidak ada query tanpa hasil</p>
                      <p className="text-xs text-slate-400">Semua query berhasil menemukan dokumen relevan</p>
                    </div>
                  </div>
                ) : (
                  <div className="space-y-2">
                    {data.zero_result_queries.slice(0, 20).map((item, i) => (
                      <div
                        key={i}
                        className="flex items-start gap-3 p-3 rounded-xl hover:bg-slate-50 transition-colors"
                      >
                        <span className="mt-0.5 flex-shrink-0 w-5 h-5 bg-red-100 text-red-600 text-[10px] font-bold rounded-full flex items-center justify-center">
                          {i + 1}
                        </span>
                        <div className="flex-1 min-w-0">
                          <p className="text-sm text-slate-800 font-medium truncate">{item.query}</p>
                          <p className="text-xs text-slate-400 mt-0.5">
                            Terakhir dilihat: {new Date(item.last_seen).toLocaleString('id-ID', {
                              day: 'numeric', month: 'short', year: 'numeric',
                              hour: '2-digit', minute: '2-digit'
                            })}
                          </p>
                        </div>
                        <ChevronRight className="w-4 h-4 text-slate-300 flex-shrink-0 mt-1" />
                      </div>
                    ))}
                  </div>
                )}
              </div>

              {/* ── Full query table ── */}
              <div className="bg-white rounded-2xl border border-slate-200 p-5">
                <div className="flex items-center gap-2 mb-4">
                  <Search className="w-4 h-4 text-blue-600" />
                  <h3 className="text-base font-bold text-slate-900">20 Query Teratas</h3>
                </div>

                {data.top_queries.length === 0 ? (
                  <EmptyState
                    icon={<Search className="w-6 h-6" />}
                    title="Belum ada query tercatat"
                    subtitle="Query pencarian akan muncul di sini"
                  />
                ) : (
                  <div className="overflow-x-auto">
                    <table className="w-full text-sm">
                      <thead>
                        <tr className="text-left text-slate-500 border-b border-slate-100">
                          <th className="pb-3 pl-2 font-semibold text-xs uppercase tracking-wider w-8">#</th>
                          <th className="pb-3 font-semibold text-xs uppercase tracking-wider">Query</th>
                          <th className="pb-3 font-semibold text-xs uppercase tracking-wider text-right w-20">Jumlah</th>
                        </tr>
                      </thead>
                      <tbody>
                        {data.top_queries.map((item, i) => (
                          <tr key={i} className="border-b border-slate-50 hover:bg-slate-50 transition-colors">
                            <td className="py-3 pl-2 text-slate-400 font-medium">{i + 1}</td>
                            <td className="py-3 text-slate-800">{item.query}</td>
                            <td className="py-3 text-right">
                              <span className="inline-block bg-blue-100 text-blue-700 font-semibold px-2.5 py-0.5 rounded-lg text-xs">
                                {item.count.toLocaleString('id-ID')}
                              </span>
                            </td>
                          </tr>
                        ))}
                      </tbody>
                    </table>
                  </div>
                )}
              </div>

            </>
          )}
        </main>
      </div>
    </AdminGate>
  )
}