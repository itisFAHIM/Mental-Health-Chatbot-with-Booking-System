const CACHE = 'mhchat-v1';
self.addEventListener('install', e=>{ e.waitUntil(caches.open(CACHE).then(c=>c.addAll(['/static/css/style.css','/static/js/app.js','/static/manifest.json']))); });
self.addEventListener('fetch', e=>{ e.respondWith(caches.match(e.request).then(r=>r||fetch(e.request))); });
