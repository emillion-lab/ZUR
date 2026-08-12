// Zürich Taxi Radar — Service Worker
// Кешира статичните файлове за офлайн работа.
// Модел преписан от BAK/sw.js, адаптиран за пътищата на ZUR.

const CACHE_NAME = 'zur-taxi-v2';
const STATIC_FILES = [
  '/ZUR/',
  '/ZUR/index.html',
  '/ZUR/app.js',
  '/ZUR/theme.js',
  '/ZUR/weather-sky.js',
  '/ZUR/leaflet.min.js',
  '/ZUR/manifest.json',
];

// Инсталация — кешира статичните файлове
self.addEventListener('install', event => {
  event.waitUntil(
    caches.open(CACHE_NAME).then(cache => {
      return cache.addAll(STATIC_FILES);
    })
  );
  self.skipWaiting();
});

// Активация — изтрива стари кешове
self.addEventListener('activate', event => {
  event.waitUntil(
    caches.keys().then(keys =>
      Promise.all(
        keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k))
      )
    )
  );
  self.clients.claim();
});

// Fetch — network first, cache fallback
// Динамичните данни — винаги от мрежата, никога от кеш
self.addEventListener('fetch', event => {
  const url = new URL(event.request.url);

  const dynamicPatterns = [
    'openweathermap.org',
    'open-meteo.com',
    'aviationstack.com',
    'nominatim.openstreetmap.org',
    'workers.dev',
    'flight-cache.json',
    'config.json',
  ];

  const isDynamic = dynamicPatterns.some(p => url.href.includes(p));

  if (isDynamic) {
    event.respondWith(
      fetch(event.request).catch(() => new Response('{}', {
        headers: {'Content-Type': 'application/json'}
      }))
    );
    return;
  }

  event.respondWith(
    fetch(event.request, {cache: 'no-cache'})
      .then(response => {
        if (response.ok) {
          const clone = response.clone();
          caches.open(CACHE_NAME).then(cache => cache.put(event.request, clone));
        }
        return response;
      })
      .catch(() => caches.match(event.request))
  );
});
