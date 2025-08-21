
class NotificationManager {
    constructor() {
        this.isSupported = 'Notification' in window;
        this.permission = null;
        this.checkInterval = 60000; // 1 minuto
        this.serviceWorkerRegistration = null;
        this.init();
    }

    async init() {
        if (!this.isSupported) {
            console.warn('Notificações não são suportadas neste navegador');
            return;
        }

        // Registrar o Service Worker antes de solicitar permissão
        await this.registerServiceWorker();

        this.permission = await this.requestPermission();
        console.log(`Status da permissão de notificações: ${this.permission}`);
        
        if (this.permission === 'granted') {
            this.startPolling();
            // Mostrar notificação de confirmação
            setTimeout(() => {
                this.notify('success', 'Notificações Ativadas', 'Você receberá notificações sobre lembretes, tarefas e chamados.');
            }, 2000);
        } else {
            // Informar o usuário sobre como habilitar notificações
            console.warn('Permissão para notificações negada pelo usuário');
            // Adicionar um elemento na interface para informar o usuário
            this.showPermissionMessage();
            
            // Adicionar botão para tentar novamente
            this.addRetryButton();
        }
    }
    
    async registerServiceWorker() {
        if (!('serviceWorker' in navigator)) {
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
    
    showPermissionMessage() {
        // Verificar se já existe uma mensagem
        if (document.querySelector('.notification-permission-message')) {
            return;
        }
        
        // Criar elemento de mensagem
        const messageContainer = document.createElement('div');
        messageContainer.className = 'notification-permission-message alert alert-warning alert-dismissible fade show';
        messageContainer.style.position = 'fixed';
        messageContainer.style.bottom = '20px';
        messageContainer.style.right = '20px';
        messageContainer.style.maxWidth = '350px';
        messageContainer.style.zIndex = '9999';
        
        messageContainer.innerHTML = `
            <h5><i class="fas fa-bell-slash"></i> Notificações Desativadas</h5>
            <p>Para receber alertas sobre lembretes, tarefas e chamados, habilite as notificações nas configurações do navegador.</p>
            <div class="mt-2 d-flex gap-2">
                <button type="button" class="btn btn-sm btn-primary retry-notifications">Tentar Novamente</button>
                <button type="button" class="btn btn-sm btn-outline-secondary test-notifications">Testar Notificações</button>
            </div>
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
        `;
        
        document.body.appendChild(messageContainer);
        
        // Adicionar listener para o botão de teste
        const testButton = messageContainer.querySelector('.test-notifications');
        if (testButton) {
            testButton.addEventListener('click', () => {
                this.testNotification();
            });
        }
    }
    
    addRetryButton() {
        // Aguardar um momento para garantir que a mensagem foi adicionada ao DOM
        setTimeout(() => {
            const retryButton = document.querySelector('.retry-notifications');
            if (retryButton) {
                retryButton.addEventListener('click', async () => {
                    // Remover a mensagem atual
                    const messageContainer = document.querySelector('.notification-permission-message');
                    if (messageContainer) {
                        messageContainer.remove();
                    }
                    
                    // Solicitar permissão novamente
                    this.permission = await this.requestPermission();
                    
                    if (this.permission === 'granted') {
                        this.startPolling();
                        this.notify('success', 'Notificações Ativadas', 'Você receberá notificações sobre lembretes, tarefas e chamados.');
                        // Testar notificação automaticamente
                        setTimeout(() => {
                            this.testNotification();
                        }, 3000);
                    } else {
                        this.showPermissionMessage();
                        this.addRetryButton();
                    }
                });
            }
            
            // Já adicionamos o listener para o botão de teste no método showPermissionMessage
        }, 500);
    }

    async requestPermission() {
        try {
            if (Notification.permission === 'granted') {
                console.log('Permissão para notificações já concedida');
                return 'granted';
            }

            // Mesmo que a permissão tenha sido negada anteriormente, vamos tentar solicitar novamente
            // Isso permite que o usuário mude de ideia se já negou antes
            console.log('Solicitando permissão para notificações...');
            const permission = await Notification.requestPermission();
            console.log(`Resultado da solicitação de permissão: ${permission}`);
            
            // Se a permissão foi concedida, verificar o registro do service worker
            if (permission === 'granted' && 'serviceWorker' in navigator) {
                try {
                    const registration = await navigator.serviceWorker.ready;
                    console.log('Service Worker pronto para notificações:', registration);
                } catch (swError) {
                    console.error('Erro ao verificar Service Worker:', swError);
                    // Tentar registrar novamente o service worker
                    await navigator.serviceWorker.register('/static/sw.js');
                }
            }
            
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
                this.showPermissionMessage();
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

            // Lembretes vencendo
            if (data.reminders_expiring && data.reminders_expiring.length > 0) {
                console.log(`${data.reminders_expiring.length} lembretes vencendo em breve`);
                for (const reminder of data.reminders_expiring) {
                    await this.showNotification('🔔 Lembrete Vencendo!', {
                        body: `${reminder.name} - Responsável: ${reminder.responsible}`,
                        tag: `reminder-${reminder.id}`,
                        data: {
                            url: `/reminders?highlight=${reminder.id}`,
                            id: reminder.id
                        },
                        requireInteraction: true
                    });
                }
            }

            // Chamados atualizados
            if (data.chamados_updated && data.chamados_updated.length > 0) {
                console.log(`${data.chamados_updated.length} chamados atualizados recentemente`);
                for (const chamado of data.chamados_updated) {
                    await this.showNotification('📞 Chamado Atualizado!', {
                        body: `#${chamado.id} - ${chamado.titulo}`,
                        tag: `chamado-${chamado.id}`,
                        data: {
                            url: `/chamados/detalhe/${chamado.id}`,
                            id: chamado.id
                        },
                        requireInteraction: true
                    });
                }
            }

            // Tarefas vencidas
            if (data.tasks_overdue && data.tasks_overdue.length > 0) {
                console.log(`${data.tasks_overdue.length} tarefas em atraso`);
                await this.showNotification('⚠️ Tarefas Vencidas!', {
                    body: `${data.tasks_overdue.length} tarefa(s) em atraso`,
                    tag: 'tasks-overdue',
                    data: {
                        url: '/tasks?filter=overdue'
                    },
                    requireInteraction: true
                });
            }

            console.log('Verificação de notificações concluída com sucesso');

        } catch (error) {
            console.error('Erro ao verificar notificações:', error);
            
            // Se houver erro de conexão, tentar novamente mais tarde
            if (error.name === 'TypeError' && error.message.includes('Failed to fetch')) {
                console.log('Erro de conexão, tentando novamente em 30 segundos...');
                setTimeout(() => this.checkForUpdates(), 30000);
            }
        }
    }

    startPolling() {
        // Verificação inicial
        this.checkForUpdates();

        // Verificação periódica
        this.pollingInterval = setInterval(() => {
            this.checkForUpdates();
        }, this.checkInterval);
        
        // Adicionar listeners para eventos de conectividade
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
    window.notificationManager = new NotificationManager();
});
