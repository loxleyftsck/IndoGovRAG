const CACHE_NAME = 'indogovrag-v1';
const OFFLINE_URL = '/offline.html';

const STATIC_ASSETS = [
  '/',
  '/offline.html',
  '/icon-192.png',
  '/icon-512.png',
];

// Install: cache static assets
self.addEventListener('install', (event) => {
  event.waitUntil(
    caches.open(CACHE_NAME).then((cache) => {
      return cache.addAll(STATIC_ASSETS);
    })
  );
  self.skipWaiting();
});

// Activate: clean old caches
self.addEventListener('activate', (event) => {
  event.waitUntil(
    caches.keys().then((keys) => {
      return Promise.all(
        keys.filter((key) => key !== CACHE_NAME).map((key) => caches.delete(key))
      );
    })
  );
  self.clients.claim();
});

// Fetch: network-first for API, cache-first for static
self.addEventListener('fetch', (event) => {
  const { request } = event;
  const url = new URL(request.url);

  // Skip non-GET requests
  if (request.method !== 'GET') return;

  // API requests: network-first, fallback to offline
  if (url.pathname.startsWith('/query') || url.pathname.startsWith('/stats') || url.pathname.startsWith('/files')) {
    event.respondWith(
      fetch(request)
        .then((response) => {
          // Cache last 10 search results
          if (response.ok && url.pathname === '/query') {
            const clone = response.clone();
            caches.open(CACHE_NAME).then((cache) => {
              cache.put(request, clone);
              trimCache(cache, 10);
            });
          }
          return response;
        })
        .catch(() => {
          // Try cache for query
          if (url.pathname === '/query') {
            return caches.match(request).then((cached) => {
              return cached || new Response(
                JSON.stringify({ answer: 'Offline: Gagal mengambil data. Mohon coba lagi.', sources: [], confidence: 0, latency_ms: 0 }),
                { headers: { 'Content-Type': 'application/json' } }
              );
            });
          }
          return new Response(
            JSON.stringify({ error: 'Offline' }),
            { status: 503, headers: { 'Content-Type': 'application/json' } }
          );
        })
    );
    return;
  }

  // Static assets: cache-first
  event.respondWith(
    caches.match(request).then((cached) => {
      if (cached) return cached;
      return fetch(request).then((response) => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then((cache) => cache.put(request, clone));
        }
        return response;
      }).catch(() => {
        // For navigation requests, show offline page
        if (request.mode === 'navigate') {
          return caches.match(OFFLINE_URL);
        }
      });
    })
  );
});

// Trim cache to keep only last N entries
function trimCache(cache, maxEntries) {
  cache.keys().then((keys) => {
    if (keys.length > maxEntries) {
      const toDelete = keys.slice(0, keys.length - maxEntries);
      toDelete.forEach((key) => cache.delete(key));
    }
  });
}