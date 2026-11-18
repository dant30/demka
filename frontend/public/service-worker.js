const CACHE_PREFIX = 'demka-app-shell-';
const CACHE_NAME = `${CACHE_PREFIX}v1`;
const APP_SHELL = ['/', '/index.html', '/manifest.json', '/favicon.svg', '/app-icon.svg'];

self.addEventListener('install', (event) => {
	event.waitUntil((async () => {
		const manifestResponse = await fetch('/precache-manifest.json', { cache: 'no-store' });
		if (!manifestResponse.ok) throw new Error('Unable to load the app-shell asset manifest.');
		const assets = await manifestResponse.json();
		const cache = await caches.open(CACHE_NAME);
		await cache.addAll([...APP_SHELL, ...assets]);
		await self.skipWaiting();
	})());
});

self.addEventListener('activate', (event) => {
	event.waitUntil((async () => {
		const cacheNames = await caches.keys();
		await Promise.all(
			cacheNames
				.filter((cacheName) => cacheName.startsWith(CACHE_PREFIX) && cacheName !== CACHE_NAME)
				.map((cacheName) => caches.delete(cacheName)),
		);
		await self.clients.claim();
	})());
});

self.addEventListener('fetch', (event) => {
	const { request } = event;
	const url = new URL(request.url);
	if (request.method !== 'GET' || url.origin !== self.location.origin) return;
	if (/^\/(api|media|admin|static)(\/|$)/.test(url.pathname)) return;

	if (request.mode === 'navigate') {
		event.respondWith(
			fetch(request).catch(async () => {
				const cachedShell = await caches.match('/index.html');
				return cachedShell || Response.error();
			}),
		);
		return;
	}

	if (
		url.pathname.startsWith('/assets/') ||
		url.pathname === '/manifest.json' ||
		url.pathname === '/favicon.svg' ||
		url.pathname === '/app-icon.svg'
	) {
		event.respondWith((async () => {
			const cached = await caches.match(request);
			if (cached) return cached;
			const response = await fetch(request);
			if (response.ok && response.type === 'basic') {
				const cache = await caches.open(CACHE_NAME);
				await cache.put(request, response.clone());
			}
			return response;
		})());
	}
});
