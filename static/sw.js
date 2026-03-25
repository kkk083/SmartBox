const CACHE_NAME = 'smartbox-v1';
const ASSETS = ['/', '/static/css/style.css', '/static/js/app.js'];

// Installation
self.addEventListener('install', e => {
    e.waitUntil(
        caches.open(CACHE_NAME).then(cache => cache.addAll(ASSETS))
    );
    self.skipWaiting();
});

// Activation
self.addEventListener('activate', e => {
    e.waitUntil(
        caches.keys().then(keys =>
            Promise.all(keys.filter(k => k !== CACHE_NAME).map(k => caches.delete(k)))
        )
    );
    self.clients.claim();
});

// Fetch — réseau d'abord, cache en fallback
self.addEventListener('fetch', e => {
    // Ignore les requêtes non GET et les API
    if (e.request.method !== 'GET') return;
    if (e.request.url.includes('/api/')) return;

    e.respondWith(
        fetch(e.request)
            .then(response => {
                const clone = response.clone();
                caches.open(CACHE_NAME).then(cache => cache.put(e.request, clone));
                return response;
            })
            .catch(() => caches.match(e.request))
    );
});

// Notification push reçue
self.addEventListener('push', e => {
    const data = e.data ? e.data.json() : {};
    const title = data.title || 'SmartBox';
    const options = {
        body:  data.body  || 'Nouvelle activité sur votre SmartBox',
        icon:  '/static/images/icon-192.png',
        badge: '/static/images/icon-192.png',
        tag:   data.tag   || 'smartbox',
        data:  { url: '/' },
        vibrate: [200, 100, 200],
        actions: [
            { action: 'open',    title: 'Ouvrir' },
            { action: 'dismiss', title: 'Ignorer' }
        ]
    };
    e.waitUntil(self.registration.showNotification(title, options));
});

// Clic sur la notification
self.addEventListener('notificationclick', e => {
    e.notification.close();
    if (e.action === 'dismiss') return;
    const url = e.notification.data?.url || '/';
    e.waitUntil(
        clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => {
            for (const client of list) {
                if ('focus' in client) return client.focus();
            }
            if (clients.openWindow) return clients.openWindow(url);
        })
    );
});