import { NextRequest, NextResponse } from 'next/server'

export async function POST(req: NextRequest) {
  try {
    const body = await req.json()
    const { query, options = {} } = body

    if (!query || typeof query !== 'string') {
      return NextResponse.json({ error: 'Query is required' }, { status: 400 })
    }

    const backendRes = await fetch('http://localhost:8000/query', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        query: query.slice(0, 500),
        options: {
          top_k: options.top_k ?? 10,
          use_query_expansion: options.use_query_expansion ?? true,
          use_reranking: options.use_reranking ?? false,
          use_hybrid: options.use_hybrid ?? true,
        },
      }),
      signal: AbortSignal.timeout(30_000),
    })

    if (!backendRes.ok) {
      const text = await backendRes.text()
      return NextResponse.json({ error: `Backend error: ${text}` }, { status: backendRes.status })
    }

    const data = await backendRes.json()
    return NextResponse.json(data)
  } catch (err: unknown) {
    const message = err instanceof Error ? err.message : 'Unknown error'
    return NextResponse.json({ error: message }, { status: 500 })
  }
}