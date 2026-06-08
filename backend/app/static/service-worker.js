const CACHE_NAME = "landa-cache-v2";
const STATIC_ASSETS = [
    "/",
    "/offline",
    "/static/css/base.css",
    "/static/manifest.json",
    "/static/js/app.js",
    "/static/icons/icon-72x72.png",
    "/static/icons/icon-96x96.png",
    "/static/icons/icon-128x128.png",
    "/static/icons/icon-144x144.png",
    "/static/icons/icon-152x152.png",
    "/static/icons/icon-168x168.png",
    "/static/icons/icon-180x180.png",
    "/static/icons/icon-192x192.png",
    "/static/icons/icon-384x384.png",
    "/static/icons/icon-512x512.png",
];

const API_CACHE = "landa-api-v1";
const NAV_CACHE = "landa-nav-v1";

self.addEventListener("install", function (event) {
    self.skipWaiting();
    event.waitUntil(
        caches.open(CACHE_NAME).then(function (cache) {
            return cache.addAll(STATIC_ASSETS);
        })
    );
});

self.addEventListener("activate", function (event) {
    event.waitUntil(
        Promise.all([
            caches.keys().then(function (keys) {
                return Promise.all(
                    keys
                        .filter(function (key) {
                            return (
                                key !== CACHE_NAME &&
                                key !== API_CACHE &&
                                key !== NAV_CACHE
                            );
                        })
                        .map(function (key) {
                            return caches.delete(key);
                        })
                );
            }),
            self.clients.claim(),
        ])
    );
});

self.addEventListener("fetch", function (event) {
    const url = new URL(event.request.url);
    const isSameOrigin = url.origin === self.location.origin;
    const isApiRequest = url.pathname.startsWith("/api/");
    const isStatic =
        url.pathname.startsWith("/static/") ||
        url.pathname === "/manifest.json" ||
        url.pathname === "/service-worker.js" ||
        url.pathname === "/offline";

    if (!isSameOrigin) {
        return;
    }

    if (isApiRequest) {
        event.respondWith(networkFirst(event.request, API_CACHE));
        return;
    }

    if (isStatic) {
        event.respondWith(cacheFirst(event.request));
        return;
    }

    if (event.request.mode === "navigate") {
        event.respondWith(networkFirst(event.request, NAV_CACHE));
        return;
    }

    event.respondWith(cacheFirst(event.request));
});

function cacheFirst(request) {
    return caches.match(request).then(function (cached) {
        if (cached) {
            return cached;
        }
        return fetch(request)
            .then(function (response) {
                if (!response || response.status !== 200) {
                    return response;
                }
                var copy = response.clone();
                caches.open(CACHE_NAME).then(function (cache) {
                    cache.put(request, copy);
                });
                return response;
            })
            .catch(function () {
                if (request.mode === "navigate") {
                    return caches.match("/offline");
                }
                return new Response("Offline", { status: 503 });
            });
    });
}

function networkFirst(request, cacheName) {
    return fetch(request)
        .then(function (response) {
            if (!response || response.status !== 200) {
                return response;
            }
            var copy = response.clone();
            caches.open(cacheName).then(function (cache) {
                cache.put(request, copy);
            });
            return response;
        })
        .catch(function () {
            return caches.match(request).then(function (cached) {
                if (cached) {
                    return cached;
                }
                if (request.mode === "navigate") {
                    return caches.match("/offline");
                }
                return new Response("Offline", { status: 503 });
            });
        });
}

self.addEventListener("message", function (event) {
    if (event.data && event.data.action === "skipWaiting") {
        self.skipWaiting();
    }
});
