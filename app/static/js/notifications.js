
class NotificationManager {
    constructor() {
        this.isSupported = 'Notification' in window;
        this.permission = Notification.permission;
        this.checkInterval = 300000; // 5 minutos
        this.serviceWorkerRegistration = null;
        this.messageShown = false;
        this.pollingInterval = null;
        this.listenersAdded = false;
        this.notificationHistory = new Map(); // Rastrear notificações já enviadas
        this.notificationCooldowns = new Map(); // Cooldowns por tipo
        this.init();
    }

    async init() {
        if (!this.isSupported) {
            console.warn('Notificações não são suportadas neste navegador');
            this.showUnsupportedMessage();
            return;
        }

        // Verificar permissão atual
        this.permission = Notification.permission;
        console.log(`Status inicial da permissão: ${this.permission}`);
        
        // Verificar se o usuário dispensou recentemente
        if (!this.shouldShowMessage()) {
            console.log('Usuário dispensou notificações recentemente, não mostrando mensagem');
            return;
        }
        
        if (this.permission === 'granted') {
            // Registrar o Service Worker e iniciar polling
            await this.registerServiceWorker();
            this.startPolling();
            this.hidePermissionMessage();
        } else if (this.permission === 'denied') {
            // Permissão foi negada permanentemente
            this.showPermissionDeniedMessage();
        } else {
            // Permissão ainda não foi solicitada (default)
            // Aguardar um pouco antes de mostrar a mensagem para evitar aparecer na tela de login
            setTimeout(() => {
                if (this.shouldShowMessage()) {
                    this.showPermissionRequestMessage();
                }
            }, 2000);
        }
    }
    
    async registerServiceWorker() {
        if (!this.isSupported) {
            console.warn('Service Worker não é suportado neste navegador');
            return false;
        }
        
        try {
            // Verificar se já existe um service worker registrado
            const registrations = await navigator.serviceWorker.getRegistrations();
            
            if (registrations.length > 0) {
                // Verificar se algum dos registros é para o nosso SW
                const swRegistration = registrations.find(reg => 
                    reg.scope.includes(window.location.origin));
                
                if (swRegistration) {
                    console.log('Service Worker já registrado:', swRegistration);
                    this.serviceWorkerRegistration = swRegistration;
                    return true;
                }
            }
            
            // Se não houver service worker registrado, registrar novamente
            console.log('Registrando Service Worker...');
            const registration = await navigator.serviceWorker.register('/static/sw.js');
            console.log('Service Worker registrado com sucesso:', registration);
            this.serviceWorkerRegistration = registration;
            
            // Verificar se o SW está ativo
            if (registration.active) {
                console.log('Service Worker está ativo');
            } else {
                console.log('Service Worker está instalando/esperando');
                // Esperar até que o SW esteja ativo
                registration.addEventListener('updatefound', () => {
                    const newWorker = registration.installing;
                    newWorker.addEventListener('statechange', () => {
                        console.log('Service Worker mudou de estado para:', newWorker.state);
                    });
                });
            }
            
            return true;
        } catch (error) {
            console.error('Erro ao registrar Service Worker:', error);
            return false;
        }
    }
    
    showPermissionRequestMessage() {
        if (this.messageShown || document.querySelector('.notification-permission-message')) {
            return;
        }
        
        this.messageShown = true;
        const messageContainer = document.createElement('div');
        messageContainer.className = 'notification-permission-message alert alert-info alert-dismissible fade show';
        messageContainer.style.position = 'fixed';
        messageContainer.style.bottom = '20px';
        messageContainer.style.right = '20px';
        messageContainer.style.maxWidth = '350px';
        messageContainer.style.zIndex = '9999';
        
        messageContainer.innerHTML = `
            <h5><i class="fas fa-bell"></i> Ativar Notificações</h5>
            <p>Receba alertas sobre lembretes, tarefas e chamados importantes.</p>
            <div class="mt-2 d-flex gap-2">
                <button type="button" class="btn btn-sm btn-primary enable-notifications">Ativar Agora</button>
                <button type="button" class="btn btn-sm btn-outline-secondary dismiss-notifications">Agora Não</button>
            </div>
        `;
        
        document.body.appendChild(messageContainer);
        this.addMessageListeners(messageContainer);
    }
    
    showPermissionDeniedMessage() {
        if (this.messageShown || document.querySelector('.notification-permission-message')) {
            return;
        }
        
        this.messageShown = true;
        const messageContainer = document.createElement('div');
        messageContainer.className = 'notification-permission-message alert alert-warning alert-dismissible fade show';
        messageContainer.style.position = 'fixed';
        messageContainer.style.bottom = '20px';
        messageContainer.style.right = '20px';
        messageContainer.style.maxWidth = '350px';
        messageContainer.style.zIndex = '9999';
        
        messageContainer.innerHTML = `
            <h5><i class="fas fa-bell-slash"></i> Notificações Bloqueadas</h5>
            <p>Para receber alertas, clique no ícone de cadeado <i class="fas fa-lock"></i> na barra de endereços e selecione "Permitir" para notificações.</p>
            <div class="mt-2 d-flex gap-2">
                <button type="button" class="btn btn-sm btn-primary retry-notifications">Tentar Novamente</button>
                <button type="button" class="btn btn-sm btn-outline-secondary dismiss-notifications">Dispensar</button>
            </div>
        `;
        
        document.body.appendChild(messageContainer);
        this.addMessageListeners(messageContainer);
    }
    
    showUnsupportedMessage() {
        if (this.messageShown || document.querySelector('.notification-permission-message')) {
            return;
        }
        
        this.messageShown = true;
        const messageContainer = document.createElement('div');
        messageContainer.className = 'notification-permission-message alert alert-warning alert-dismissible fade show';
        messageContainer.style.position = 'fixed';
        messageContainer.style.bottom = '20px';
        messageContainer.style.right = '20px';
        messageContainer.style.maxWidth = '400px';
        messageContainer.style.zIndex = '9999';
        
        // Detectar o motivo específico
        const isHttpIP = window.location.protocol === 'http:' && window.location.hostname !== 'localhost';
        const hasNotificationAPI = 'Notification' in window;
        const hasServiceWorker = 'serviceWorker' in navigator;
        const isSecureContext = window.isSecureContext || window.location.protocol === 'https:' || window.location.hostname === 'localhost';
        
        let message = '';
        let title = '';
        
        if (!isSecureContext) {
            title = '<i class="fas fa-shield-alt"></i> Notificações Requerem HTTPS';
            message = `
                <p><strong>Notificações não funcionam em HTTP com IPs.</strong></p>
                <p><strong>Soluções:</strong></p>
                <ul class="mb-2">
                    <li>Acesse via <code>localhost:5000</code></li>
                    <li>Configure HTTPS no servidor</li>
                    <li>Use um domínio com certificado SSL</li>
                </ul>
                <p><small>Esta é uma limitação de segurança dos navegadores modernos.</small></p>
            `;
        } else if (!hasNotificationAPI) {
            title = '<i class="fas fa-exclamation-triangle"></i> API de Notificações Indisponível';
            message = '<p>Seu navegador não suporta a API de Notificações.</p>';
        } else if (!hasServiceWorker) {
            title = '<i class="fas fa-exclamation-triangle"></i> Service Worker Indisponível';
            message = '<p>Seu navegador não suporta Service Workers.</p>';
        } else {
            title = '<i class="fas fa-info-circle"></i> Notificações Indisponíveis';
            message = '<p>Notificações não estão disponíveis neste contexto.</p>';
        }
        
        messageContainer.innerHTML = `
            <h5>${title}</h5>
            ${message}
            <div class="mt-2">
                <button type="button" class="btn btn-sm btn-outline-secondary dismiss-notifications">Dispensar</button>
            </div>
        `;
        
        document.body.appendChild(messageContainer);
        this.addMessageListeners(messageContainer);
    }
    
    hidePermissionMessage() {
        const existingMessage = document.querySelector('.notification-permission-message');
        if (existingMessage) {
            existingMessage.remove();
        }
        this.messageShown = false;
    }
    
    addMessageListeners(messageContainer) {
        // Listener para ativar notificações
        const enableButton = messageContainer.querySelector('.enable-notifications');
        if (enableButton) {
            enableButton.addEventListener('click', async () => {
                this.hidePermissionMessage();
                this.permission = await this.requestPermission();
                
                if (this.permission === 'granted') {
                    await this.registerServiceWorker();
                    this.startPolling();
                    this.notify('success', 'Notificações Ativadas', 'Você receberá alertas sobre lembretes, tarefas e chamados.');
                } else {
                    // Mostrar mensagem apropriada baseada no novo status
                    if (this.permission === 'denied') {
                        this.showPermissionDeniedMessage();
                    } else {
                        this.showPermissionRequestMessage();
                    }
                }
            });
        }
        
        // Listener para tentar novamente (para permissões negadas)
        const retryButton = messageContainer.querySelector('.retry-notifications');
        if (retryButton) {
            retryButton.addEventListener('click', async () => {
                this.hidePermissionMessage();
                // Verificar novamente o status da permissão
                this.permission = Notification.permission;
                
                if (this.permission === 'granted') {
                    await this.registerServiceWorker();
                    this.startPolling();
                    this.notify('success', 'Notificações Ativadas', 'Você receberá alertas sobre lembretes, tarefas e chamados.');
                } else if (this.permission === 'default') {
                    // Tentar solicitar permissão novamente
                    this.permission = await this.requestPermission();
                    if (this.permission === 'granted') {
                        await this.registerServiceWorker();
                        this.startPolling();
                        this.notify('success', 'Notificações Ativadas', 'Você receberá alertas sobre lembretes, tarefas e chamados.');
                    } else {
                        this.showPermissionDeniedMessage();
                    }
                } else {
                    // Ainda negada, mostrar instruções
                    this.showPermissionDeniedMessage();
                }
            });
        }
        
        // Listener para dispensar mensagem
        const dismissButton = messageContainer.querySelector('.dismiss-notifications');
        if (dismissButton) {
            dismissButton.addEventListener('click', () => {
                this.hidePermissionMessage();
                // Salvar preferência para não mostrar novamente por um tempo
                localStorage.setItem('notificationDismissed', Date.now().toString());
            });
        }
        
        // Listener para testar notificações
        const testButton = messageContainer.querySelector('.test-notifications');
        if (testButton) {
            testButton.addEventListener('click', () => {
                this.testNotification();
            });
        }
    }
    
    shouldShowMessage() {
        // Verificar se o usuário dispensou a mensagem recentemente (últimas 24 horas)
        const dismissed = localStorage.getItem('notificationDismissed');
        if (dismissed) {
            const dismissedTime = parseInt(dismissed);
            const now = Date.now();
            const dayInMs = 24 * 60 * 60 * 1000;
            
            if (now - dismissedTime < dayInMs) {
                return false;
            }
        }
        
        // Não mostrar se já está sendo exibida
        if (this.messageShown || document.querySelector('.notification-permission-message')) {
            return false;
        }
        
        // Não mostrar se estivermos na página de login
        if (window.location.pathname.includes('/login') || window.location.pathname === '/') {
            return false;
        }
        
        return true;
    }

    async requestPermission() {
        try {
            // Verificar permissão atual
            this.permission = Notification.permission;
            
            if (this.permission === 'granted') {
                console.log('Permissão para notificações já concedida');
                return 'granted';
            }
            
            if (this.permission === 'denied') {
                console.log('Permissão para notificações foi negada pelo usuário');
                return 'denied';
            }

            // Solicitar permissão apenas se ainda não foi solicitada (default)
            console.log('Solicitando permissão para notificações...');
            const permission = await Notification.requestPermission();
            console.log(`Resultado da solicitação de permissão: ${permission}`);
            
            this.permission = permission;
            return permission;
        } catch (error) {
            console.error('Erro ao solicitar permissão para notificações:', error);
            return 'denied';
        }
    }

    async showNotification(title, options = {}) {
        if (this.permission !== 'granted') {
            console.log('Tentando solicitar permissão para notificações novamente...');
            this.permission = await this.requestPermission();
            if (this.permission !== 'granted') {
                console.warn('Permissão para notificações não concedida');
                return null;
            }
        }
        
        try {
            // Verificar se o Service Worker está disponível e registrado
            if ('serviceWorker' in navigator && 'PushManager' in window) {
                // Usar o Service Worker registrado na propriedade serviceWorkerRegistration
                if (this.serviceWorkerRegistration) {
                    // Tentar usar o Service Worker para mostrar a notificação
                    await this.serviceWorkerRegistration.showNotification(title, {
                        icon: '/static/favicon.ico',
                        badge: '/static/favicon.ico',
                        vibrate: [100, 50, 100],
                        requireInteraction: options.requireInteraction || false,
                        actions: [
                            {
                                action: 'view',
                                title: 'Ver Detalhes'
                            }
                        ],
                        ...options
                    });
                    
                    console.log('Notificação exibida via Service Worker registrado:', title);
                    return true;
                } else {
                    // Tentar obter o Service Worker pronto
                    console.log('Service Worker não registrado, tentando obter o pronto...');
                    const registration = await navigator.serviceWorker.ready;
                    this.serviceWorkerRegistration = registration;
                    
                    // Tentar usar o Service Worker para mostrar a notificação
                    await registration.showNotification(title, {
                        icon: '/static/favicon.ico',
                        badge: '/static/favicon.ico',
                        vibrate: [100, 50, 100],
                        requireInteraction: options.requireInteraction || false,
                        actions: [
                            {
                                action: 'view',
                                title: 'Ver Detalhes'
                            }
                        ],
                        ...options
                    });
                    
                    console.log('Notificação exibida via Service Worker:', title);
                    return true;
                }
            } else {
                // Fallback para a API de Notificação padrão
                const notification = new Notification(title, {
                    icon: '/static/favicon.ico',
                    badge: '/static/favicon.ico',
                    ...options
                });

                // Auto fechar após 10 segundos
                setTimeout(() => {
                    notification.close();
                }, 10000);

                console.log('Notificação exibida via API padrão:', title);
                return notification;
            }
        } catch (error) {
            console.error('Erro ao exibir notificação:', error);
            // Tentar registrar o Service Worker novamente
            try {
                await this.registerServiceWorker();
                console.log('Service Worker registrado novamente após erro');
                return null;
            } catch (swError) {
                console.error('Erro ao registrar Service Worker após falha na notificação:', swError);
                return null;
            }
        }
    }
    
    // Método para testar as notificações
    async testNotification() {
        const result = await this.showNotification('🧪 Teste de Notificação', {
            body: 'Se você está vendo esta mensagem, as notificações estão funcionando corretamente!',
            tag: 'test-notification',
            requireInteraction: true
        });
        
        if (result) {
            console.log('Teste de notificação enviado com sucesso');
            return true;
        } else {
            console.warn('Falha no teste de notificação');
            return false;
        }
    }

    async checkForUpdates() {
        try {
            // Verificar se o usuário está online
            if (!navigator.onLine) {
                console.log('Usuário está offline, pulando verificação de notificações');
                return;
            }
            
            // Verificar se temos permissão para notificações
            if (this.permission !== 'granted') {
                console.log('Permissão para notificações não concedida, tentando solicitar novamente...');
                this.permission = await this.requestPermission();
                
                if (this.permission !== 'granted') {
                    console.log('Permissão para notificações ainda não concedida, pulando verificação');
                    return;
                }
            }
            
            // Garantir que o Service Worker esteja registrado
            if (!this.serviceWorkerRegistration) {
                await this.registerServiceWorker();
            }
            
            // Limpar histórico antigo (mais de 24 horas)
            this.cleanOldNotifications();
            
            const response = await fetch('/api/notifications', {
                method: 'GET',
                headers: {
                    'Cache-Control': 'no-cache',
                    'Pragma': 'no-cache'
                },
                credentials: 'same-origin'
            });
            
            if (!response.ok) {
                // Se o erro for 401 ou 403, o usuário não está autenticado
                if (response.status === 401 || response.status === 403) {
                    console.log('Usuário não autenticado, redirecionando para login...');
                    // Opcional: redirecionar para a página de login
                    // window.location.href = '/login';
                    return;
                }
                throw new Error(`Erro na resposta da API: ${response.status} ${response.statusText}`);
            }
            
            let data;
            try {
                const responseText = await response.text();
                data = JSON.parse(responseText);
            } catch (parseError) {
                console.error('Erro ao analisar JSON:', parseError);
                return;
            }
            
            // Verificar se há erro de autenticação
            if (data.error === 'Não autenticado') {
                // Usuário não está autenticado, não mostrar notificações
                return;
            }

            // Verificar se há notificações para exibir
            const hasNotifications = 
                (data.reminders_expiring && data.reminders_expiring.length > 0) ||
                (data.chamados_updated && data.chamados_updated.length > 0) ||
                (data.tasks_overdue && data.tasks_overdue.length > 0);
                
            if (!hasNotifications) {
                console.log('Nenhuma notificação para exibir');
                return;
            }

            // Lembretes vencendo (máximo 1 por dia por lembrete)
            if (data.reminders_expiring && data.reminders_expiring.length > 0) {
                console.log(`${data.reminders_expiring.length} lembretes vencendo em breve`);
                for (const reminder of data.reminders_expiring) {
                    const notificationKey = `reminder-${reminder.id}`;
                    if (this.shouldShowNotification(notificationKey, 24 * 60 * 60 * 1000)) { // 24 horas
                        await this.showNotification('🔔 Lembrete Vencendo!', {
                            body: `${reminder.name} - Responsável: ${reminder.responsible}`,
                            tag: notificationKey,
                            data: {
                                url: `/reminders?highlight=${reminder.id}`,
                                id: reminder.id
                            },
                            requireInteraction: true
                        });
                        this.markNotificationShown(notificationKey);
                    }
                }
            }

            // Chamados atualizados (máximo 1 por hora por chamado)
            if (data.chamados_updated && data.chamados_updated.length > 0) {
                console.log(`${data.chamados_updated.length} chamados atualizados recentemente`);
                for (const chamado of data.chamados_updated) {
                    const notificationKey = `chamado-${chamado.id}`;
                    if (this.shouldShowNotification(notificationKey, 60 * 60 * 1000)) { // 1 hora
                        await this.showNotification('📞 Chamado Atualizado!', {
                            body: `#${chamado.id} - ${chamado.titulo} (${chamado.status})`,
                            tag: notificationKey,
                            data: {
                                url: `/chamados/${chamado.id}`,
                                id: chamado.id
                            },
                            requireInteraction: true
                        });
                        this.markNotificationShown(notificationKey);
                    }
                }
            }

            // Tarefas vencidas (máximo 1 por 4 horas)
            if (data.tasks_overdue && data.tasks_overdue.length > 0) {
                console.log(`${data.tasks_overdue.length} tarefas em atraso`);
                const notificationKey = 'tasks-overdue';
                if (this.shouldShowNotification(notificationKey, 4 * 60 * 60 * 1000)) { // 4 horas
                    await this.showNotification('⚠️ Tarefas Vencidas!', {
                        body: `${data.tasks_overdue.length} tarefa(s) em atraso`,
                        tag: notificationKey,
                        data: {
                            url: '/tasks?filter=overdue'
                        },
                        requireInteraction: true
                    });
                    this.markNotificationShown(notificationKey);
                }
            }

            console.log('Verificação de notificações concluída com sucesso');

        } catch (error) {
            console.error('Erro ao verificar notificações:', error);
            
            // Se houver erro de conexão, tentar novamente mais tarde
            if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                console.log('Erro de conexão, tentando novamente em 2 minutos...');
                setTimeout(() => this.checkForUpdates(), 120000); // 2 minutos
            }
        }
    }

    startPolling() {
        // Parar polling anterior se existir
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
        }
        
        // Verificação inicial
        this.checkForUpdates();

        // Verificação periódica
        this.pollingInterval = setInterval(() => {
            this.checkForUpdates();
        }, this.checkInterval);
        
        // Adicionar listeners para eventos de conectividade (apenas uma vez)
        if (!this.listenersAdded) {
            window.addEventListener('online', () => {
                console.log('Conexão restaurada, verificando notificações...');
                this.checkForUpdates();
            });
            
            // Registrar para eventos de visibilidade da página
            document.addEventListener('visibilitychange', () => {
                if (document.visibilityState === 'visible') {
                    console.log('Página visível, verificando notificações...');
                    this.checkForUpdates();
                }
            });
            
            this.listenersAdded = true;
        }
    }
    
    stopPolling() {
        if (this.pollingInterval) {
            clearInterval(this.pollingInterval);
            this.pollingInterval = null;
        }
    }

    // Métodos para controle de cooldown de notificações
    shouldShowNotification(key, cooldownMs) {
        const now = Date.now();
        const lastShown = this.notificationHistory.get(key);
        
        if (!lastShown) {
            return true; // Primeira vez
        }
        
        return (now - lastShown) >= cooldownMs;
    }
    
    markNotificationShown(key) {
        this.notificationHistory.set(key, Date.now());
    }
    
    cleanOldNotifications() {
        const now = Date.now();
        const dayInMs = 24 * 60 * 60 * 1000;
        
        // Remover entradas mais antigas que 24 horas
        for (const [key, timestamp] of this.notificationHistory.entries()) {
            if (now - timestamp > dayInMs) {
                this.notificationHistory.delete(key);
            }
        }
    }

    // Método para mostrar notificação manual
    notify(type, title, message) {
        const icons = {
            success: '✅',
            warning: '⚠️',
            error: '❌',
            info: 'ℹ️'
        };

        this.showNotification(`${icons[type]} ${title}`, {
            body: message,
            tag: `manual-${Date.now()}`
        });
    }
}

// Inicializar quando a página carregar
document.addEventListener('DOMContentLoaded', function() {
    // Evitar múltiplas instâncias
    if (!window.notificationManager) {
        window.notificationManager = new NotificationManager();
    }
});

// Limpar recursos quando a página for descarregada
window.addEventListener('beforeunload', function() {
    if (window.notificationManager) {
        window.notificationManager.stopPolling();
    }
});
