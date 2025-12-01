
// Configuração da versão do cache
const APP_VERSION = '1.1.3';
const CACHE_NAME = `ti-reminder-v${APP_VERSION}`;
const OFFLINE_URL = '/static/offline.html';
const CACHE_EXPIRATION_DAYS = 7;

// Estratégias de cache
const CACHE_STRATEGIES = {
    STATIC: 'static',
    API: 'api',
    IMAGE: 'image'
};

// Recursos para cache imediato
const STATIC_ASSETS = [
    { url: '/', type: CACHE_STRATEGIES.STATIC },
    { url: '/static/style.min.css', type: CACHE_STRATEGIES.STATIC },
    { url: '/static/js/components.min.js', type: CACHE_STRATEGIES.STATIC },
    { url: '/static/js/notifications.min.js', type: CACHE_STRATEGIES.STATIC },
    { url: '/static/manifest.json', type: CACHE_STRATEGIES.STATIC },
    { url: '/static/favicon.ico', type: CACHE_STRATEGIES.IMAGE },
    { url: '/static/icons/logo.svg', type: CACHE_STRATEGIES.IMAGE },
    { url: '/static/icons/icon-192x192.png', type: CACHE_STRATEGIES.IMAGE },
    { url: '/static/icons/icon-180x180.png', type: CACHE_STRATEGIES.IMAGE },
    { url: '/static/icons/icon-512x512.png', type: CACHE_STRATEGIES.IMAGE },
    { url: 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css', type: CACHE_STRATEGIES.STATIC },
    { url: 'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js', type: CACHE_STRATEGIES.STATIC },
    { url: 'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css', type: CACHE_STRATEGIES.STATIC },
    { url: 'https://cdn.jsdelivr.net/npm/chart.js', type: CACHE_STRATEGIES.STATIC },
    { url: 'https://cdn.jsdelivr.net/npm/axios/dist/axios.min.js', type: CACHE_STRATEGIES.STATIC },
    // Adicione aqui outros recursos estáticos que devem ser armazenados em cache
];

// URLs de API para cache
const API_ENDPOINTS = [
    '/api/tasks',
    '/api/reminders',
    '/api/chamados'
];

// Função para limpar caches antigos
const clearOldCaches = async () => {
    const cacheNames = await caches.keys();
    return Promise.all(
        cacheNames.filter(cacheName => {
            return cacheName.startsWith('ti-reminder-') && 
                   cacheName !== CACHE_NAME;
        }).map(cacheName => {
            console.log(`[SW] Removendo cache antigo: ${cacheName}`);
            return caches.delete(cacheName);
        })
    );
};

// Função para adicionar timestamp aos recursos em cache
const addTimestamp = (response) => {
    const headers = new Headers(response.headers);
    headers.append('sw-cache-timestamp', Date.now());
    return new Response(response.body, {
        status: response.status,
        statusText: response.statusText,
        headers: headers
    });
};

// Função para verificar se a resposta do cache está expirada
const isCacheExpired = (cachedResponse) => {
    const cacheDate = new Date(cachedResponse.headers.get('sw-cache-timestamp'));
    const expirationDate = new Date();
    expirationDate.setDate(expirationDate.getDate() - CACHE_EXPIRATION_DAYS);
    return cacheDate < expirationDate;
};

// Instalar Service Worker
self.addEventListener('install', event => {
    console.log(`[SW] Installing version ${CACHE_NAME}...`);
    
    // Pular a espera para ativação imediata
    self.skipWaiting();
    
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[SW] Caching static assets');
                const cachePromises = STATIC_ASSETS.map(asset => {
                    return cache.add(asset.url).catch(err => {
                        console.warn(`[SW] Failed to cache ${asset.url}:`, err);
                    });
                });
                return Promise.all(cachePromises);
            })
            .then(() => {
                console.log('[SW] Installation complete');
                return self.skipWaiting();
            })
            .catch(err => {
                console.error('[SW] Installation failed:', err);
            })
    );
});

// Ativar Service Worker
self.addEventListener('activate', event => {
    console.log(`[SW] Activating version ${CACHE_NAME}...`);
    
    // Garantir que o service worker controle todos os clients imediatamente
    event.waitUntil(
        clearOldCaches()
            .then(() => {
                console.log('[SW] Activation complete');
                return self.clients.claim();
            })
            .then(() => {
                // Enviar mensagem para todos os clients conectados
                self.clients.matchAll().then(clients => {
                    clients.forEach(client => {
                        client.postMessage({
                            type: 'SW_ACTIVATED',
                            version: APP_VERSION
                        });
                    });
                });
            })
            .catch(err => {
                console.error('[SW] Activation failed:', err);
            })
    );
});

// Determinar a estratégia de cache com base na URL
const getCacheStrategy = (url) => {
    if (url.pathname.startsWith('/api/')) return CACHE_STRATEGIES.API;
    if (url.pathname.match(/\.(jpg|jpeg|png|webp|gif|svg|ico)$/i)) return CACHE_STRATEGIES.IMAGE;
    if (url.pathname.startsWith('/static/')) return CACHE_STRATEGIES.STATIC;
    return null;
};

// Estratégia: Cache First
const cacheFirst = async (request) => {
    const cache = await caches.open(CACHE_NAME);
    const cachedResponse = await cache.match(request);
    
    if (cachedResponse) {
        // Verificar se o cache está expirado
        if (isCacheExpired(cachedResponse)) {
            try {
                const networkResponse = await fetch(request);
                if (networkResponse.ok) {
                    // Atualizar o cache em segundo plano
                    cache.put(request, addTimestamp(networkResponse.clone()));
                }
                return networkResponse;
            } catch (err) {
                console.warn(`[SW] Network error, serving stale cache for ${request.url}`, err);
                return cachedResponse;
            }
        }
        return cachedResponse;
    }
    
    const networkResponse = await fetch(request);
    if (networkResponse.ok) {
        cache.put(request, addTimestamp(networkResponse.clone()));
    }
    return networkResponse;
};

// Estratégia: Network First, Cache Fallback
const networkFirst = async (request) => {
    try {
        const networkResponse = await fetch(request);
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, addTimestamp(networkResponse.clone()));
        }
        return networkResponse;
    } catch (err) {
        console.warn(`[SW] Network failed, serving from cache for ${request.url}`, err);
        const cachedResponse = await caches.match(request);
        if (cachedResponse) {
            return cachedResponse;
        }
        return new Response(JSON.stringify({ error: 'Você está offline e não há dados em cache disponíveis.' }), {
            status: 503,
            statusText: 'Offline',
            headers: { 'Content-Type': 'application/json' }
        });
    }
};

// Estratégia: Stale While Revalidate
const staleWhileRevalidate = async (request) => {
    const fetchPromise = fetch(request).then(async (networkResponse) => {
        if (networkResponse.ok) {
            const cache = await caches.open(CACHE_NAME);
            cache.put(request, addTimestamp(networkResponse.clone()));
        }
        return networkResponse;
    }).catch(() => null);

    const cachedResponse = await caches.match(request);
    return cachedResponse || (await fetchPromise) || Response.error();
};

// Interceptar requisições
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);
    
    // Ignorar requisições que não são GET
    if (request.method !== 'GET') return;
    
    // Ignorar requisições de extensões do navegador
    if (url.protocol === 'chrome-extension:') return;
    
    // Determinar a estratégia de cache com base no tipo de recurso
    const strategy = getCacheStrategy(url);
    
    // Aplicar estratégia apropriada
    if (strategy === CACHE_STRATEGIES.STATIC) {
        event.respondWith(cacheFirst(request));
    } 
    else if (strategy === CACHE_STRATEGIES.API) {
        event.respondWith(networkFirst(request));
    }
    else if (strategy === CACHE_STRATEGIES.IMAGE) {
        event.respondWith(staleWhileRevalidate(request));
    }
    // Para páginas HTML, use network first com fallback para cache
    else if (request.headers.get('accept').includes('text/html')) {
        event.respondWith(
            networkFirst(request).catch(() => {
                // Se estiver offline e a página não estiver em cache, mostre a página offline
                return caches.match(OFFLINE_URL);
            })
        );
    }
});

// Background Sync para dados offline
self.addEventListener('sync', event => {
    if (event.tag === 'background-sync-reminders') {
        event.waitUntil(syncReminders());
    }
    if (event.tag === 'background-sync-tasks') {
        event.waitUntil(syncTasks());
    }
});

// Push notifications
self.addEventListener('push', event => {
    let payload;
    try {
        // Tentar analisar os dados como JSON
        if (event.data) {
            const text = event.data.text();
            try {
                payload = JSON.parse(text);
            } catch (e) {
                // Se não for JSON, usar o texto como está
                payload = { message: text };
            }
        } else {
            payload = { message: 'Nova notificação do TI OSN System' };
        }
    } catch (error) {
        console.error('Erro ao processar notificação push:', error);
        payload = { message: 'Nova notificação do TI OSN System' };
    }

    // Configurar opções da notificação
    const options = {
        body: payload.message || payload.body || 'Nova notificação do TI OSN System',
        icon: '/static/icons/icon-192x192.png',
        badge: '/static/icons/badge-72x72.png',
        vibrate: [100, 50, 100],
        data: {
            dateOfArrival: Date.now(),
            primaryKey: payload.id || '1',
            url: payload.url || '/',
            ...payload
        },
        actions: [
            {
                action: 'explore',
                title: 'Ver detalhes',
                icon: '/static/icons/checkmark.png'
            },
            {
                action: 'close',
                title: 'Fechar',
                icon: '/static/icons/xmark.png'
            }
        ],
        // Garantir que a notificação seja exibida mesmo que o dispositivo esteja em modo de economia de energia
        requireInteraction: true
    };

    const title = payload.title || 'TI OSN System';

    event.waitUntil(
        self.registration.showNotification(title, options)
    );
});

// Clique em notificações
self.addEventListener('notificationclick', event => {
    // Fechar a notificação
    event.notification.close();
    
    // Ignorar se a ação for 'close'
    if (event.action === 'close') return;
    
    // Determinar a URL de destino com base nos dados da notificação
    let targetUrl = '/';
    const notificationData = event.notification.data || {};
    
    // Se a notificação tiver uma URL específica, usá-la
    if (notificationData.url && notificationData.url !== '/') {
        targetUrl = notificationData.url;
    } else {
        // Caso contrário, determinar a URL com base no tipo de notificação
        const tag = event.notification.tag || '';
        
        if (tag.startsWith('reminder-')) {
            // Notificação de lembrete
            const reminderId = tag.replace('reminder-', '');
            targetUrl = `/reminders?highlight=${reminderId}`;
        } else if (tag.startsWith('chamado-')) {
            // Notificação de chamado
            const chamadoId = tag.replace('chamado-', '');
            targetUrl = `/chamados/detalhe/${chamadoId}`;
        } else if (tag === 'tasks-overdue') {
            // Notificação de tarefas vencidas
            targetUrl = '/tasks?filter=overdue';
        }
    }
    
    // Abrir a aplicação na URL determinada
    event.waitUntil(
        clients.matchAll({type: 'window', includeUncontrolled: true})
            .then(clientList => {
                // Verificar se já existe uma janela aberta com a URL alvo
                for (const client of clientList) {
                    const clientUrl = new URL(client.url);
                    const targetUrlObj = new URL(targetUrl, self.location.origin);
                    
                    // Se a URL base for a mesma, focar nessa janela
                    if (clientUrl.pathname === targetUrlObj.pathname && 'focus' in client) {
                        return client.focus();
                    }
                }
                
                // Se não encontrar uma janela compatível, abrir uma nova
                if (clients.openWindow) {
                    return clients.openWindow(targetUrl);
                }
            })
            .catch(error => {
                console.error('Erro ao processar clique na notificação:', error);
            })
    );
});

// Funções auxiliares
async function syncReminders() {
    try {
        const pendingData = await getStoredData('pendingReminders');
        if (pendingData && pendingData.length > 0) {
            for (const reminder of pendingData) {
                await fetch('/reminders', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(reminder)
                });
            }
            await clearStoredData('pendingReminders');
        }
    } catch (error) {
        console.error('[SW] Erro ao sincronizar lembretes:', error);
    }
}

async function syncTasks() {
    try {
        const pendingData = await getStoredData('pendingTasks');
        if (pendingData && pendingData.length > 0) {
            for (const task of pendingData) {
                await fetch('/tasks', {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                    },
                    body: JSON.stringify(task)
                });
            }
            await clearStoredData('pendingTasks');
        }
    } catch (error) {
        console.error('[SW] Erro ao sincronizar tarefas:', error);
    }
}

async function getStoredData(key) {
    const cache = await caches.open(CACHE_NAME);
    const response = await cache.match(`/offline-data/${key}`);
    if (response) {
        return await response.json();
    }
    return null;
}

async function clearStoredData(key) {
    const cache = await caches.open(CACHE_NAME);
    await cache.delete(`/offline-data/${key}`);
}
