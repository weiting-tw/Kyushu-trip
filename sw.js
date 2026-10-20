/* 九州慢旅：離線快取。改了網站內容要讓手機更新時，把 VERSION 加 1。 */
const VERSION = "v6";
const CORE = `core-${VERSION}`, RUNTIME = "runtime", TILES = "tiles";
const CORE_FILES = [
  "./", "./index.html", "./manifest.webmanifest",
  "./icons/icon-192.png", "./icons/icon-512.png", "./icons/apple-touch-icon.png", "./icons/favicon-32.png",
  "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.css",
  "https://cdnjs.cloudflare.com/ajax/libs/leaflet/1.9.4/leaflet.min.js",
];
const MAX_TILES = 600;

self.addEventListener("install", e=>{
  e.waitUntil(caches.open(CORE).then(c=>c.addAll(CORE_FILES)).then(()=>self.skipWaiting()));
});
self.addEventListener("activate", e=>{
  e.waitUntil(caches.keys().then(keys=>Promise.all(
    keys.filter(k=>k.startsWith("core-") && k!==CORE).map(k=>caches.delete(k))
  )).then(()=>self.clients.claim()));
});

async function networkFirst(req, cacheName){
  const cache = await caches.open(cacheName);
  try{
    const res = await fetch(req);
    if(res.ok) cache.put(req, res.clone());
    return res;
  }catch(err){
    const hit = await cache.match(req, {ignoreSearch: req.mode==="navigate"}) || (req.mode==="navigate" && await caches.match("./index.html"));
    if(hit) return hit;
    throw err;
  }
}
async function cacheFirst(req, cacheName, limit){
  const hit = await caches.match(req);
  if(hit) return hit;
  const res = await fetch(req);
  if(res.ok || res.type==="opaque"){
    const cache = await caches.open(cacheName);
    await cache.put(req, res.clone());
    if(limit){ const keys = await cache.keys(); if(keys.length > limit) await cache.delete(keys[0]); }
  }
  return res;
}
async function staleWhileRevalidate(req){
  const cache = await caches.open(RUNTIME);
  const hit = await cache.match(req);
  const net = fetch(req).then(res=>{ if(res.ok || res.type==="opaque") cache.put(req, res.clone()); return res; }).catch(()=>hit);
  return hit || net;
}

self.addEventListener("fetch", e=>{
  const req = e.request;
  if(req.method !== "GET") return;
  const url = new URL(req.url);
  if(req.mode === "navigate" || (url.origin === location.origin && url.pathname.endsWith(".html"))){
    e.respondWith(networkFirst(req, CORE));                       // 頁面：有網路就拿最新，沒網路用快取
  }else if(url.hostname === "api.open-meteo.com"){
    e.respondWith(networkFirst(req, RUNTIME));                    // 天氣：離線時顯示最後一次查到的預報
  }else if(url.hostname.endsWith("tile.openstreetmap.org")){
    e.respondWith(cacheFirst(req, TILES, MAX_TILES));             // 地圖圖磚：看過的區域離線也能看
  }else if(url.origin === location.origin || /(^|\.)(cdnjs\.cloudflare\.com|fonts\.googleapis\.com|fonts\.gstatic\.com)$/.test(url.hostname)){
    e.respondWith(staleWhileRevalidate(req));                     // 圖示、Leaflet、字型
  }
});
