
const CACHE_NAME = 'ti-reminder-v1.0.1';
const OFFLINE_URL = '/static/offline.html';

// Recursos para cache
const STATIC_ASSETS = [
    '/',
    '/static/style.css',
    '/static/js/components.js',
    '/static/js/notifications.js',
    '/static/manifest.json',
    '/static/icons/icon-192x192.png',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/css/bootstrap.min.css',
    'https://cdn.jsdelivr.net/npm/bootstrap@5.3.2/dist/js/bootstrap.bundle.min.js',
    'https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css'
];

// Instalar Service Worker
self.addEventListener('install', event => {
    console.log(`[SW] Installing version ${CACHE_NAME}...`);
    event.waitUntil(
        caches.open(CACHE_NAME)
            .then(cache => {
                console.log('[SW] Caching static assets');
                return cache.addAll(STATIC_ASSETS);
            })
            .then(() => {
                console.log('[SW] Installation complete');
                return self.skipWaiting();
            })
    );
});

// Ativar Service Worker
self.addEventListener('activate', event => {
    console.log(`[SW] Activating version ${CACHE_NAME}...`);
    event.waitUntil(
        caches.keys().then(cacheNames => {
            return Promise.all(
                cacheNames.map(cacheName => {
                    if (cacheName !== CACHE_NAME) {
                        console.log('[SW] Deleting old cache:', cacheName);
                        return caches.delete(cacheName);
                    }
                })
            );
        }).then(() => {
            console.log('[SW] Activation complete');
            return self.clients.claim();
        })
    );
});

// Interceptar requisições
self.addEventListener('fetch', event => {
    const { request } = event;
    const url = new URL(request.url);

    // Cache first para assets estáticos
    if (STATIC_ASSETS.includes(url.pathname) || 
        url.pathname.startsWith('/static/')) {
        event.respondWith(
            caches.match(request)
                .then(response => {
                    return response || fetch(request);
                })
        );
        return;
    }

    // Network first para APIs e páginas dinâmicas
    if (url.pathname.startsWith('/api/') || 
        request.method !== 'GET') {
        event.respondWith(
            fetch(request)
                .then(response => {
                    // Cache successful responses
                    if (response.status === 200) {
                        const responseClone = response.clone();
                        caches.open(CACHE_NAME)
                            .then(cache => {
                                cache.put(request, responseClone);
                            });
                    }
                    return response;
                })
                .catch(() => {
                    // Fallback para cache se offline
                    return caches.match(request);
                })
        );
        return;
    }

    // Cache first com network fallback para páginas
    event.respondWith(
        caches.match(request)
            .then(response => {
                return response || fetch(request)
                    .then(fetchResponse => {
                        // Cache páginas importantes
                        if (fetchResponse.status === 200) {
                            const responseClone = fetchResponse.clone();
                            caches.open(CACHE_NAME)
                                .then(cache => {
                                    cache.put(request, responseClone);
                                });
                        }
                        return fetchResponse;
                    })
                    .catch(() => {
                        // Página offline para navegação
                        if (request.mode === 'navigate') {
                            return caches.match(OFFLINE_URL);
                        }
                    });
            })
    );
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
