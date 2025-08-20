
class NotificationManager {
    constructor() {
        this.isSupported = 'Notification' in window;
        this.permission = null;
        this.checkInterval = 60000; // 1 minuto
        this.init();
    }

    async init() {
        if (!this.isSupported) {
            console.warn('Notificações não são suportadas neste navegador');
            return;
        }

        this.permission = await this.requestPermission();
        console.log(`Status da permissão de notificações: ${this.permission}`);
        
        if (this.permission === 'granted') {
            this.startPolling();
            // Mostrar notificação de confirmação
            setTimeout(() => {
                this.notify('success', 'Notificações Ativadas', 'Você receberá notificações sobre lembretes, tarefas e chamados.');
            }, 2000);
        } else if (this.permission === 'denied') {
            // Informar o usuário sobre como habilitar notificações
            console.warn('Permissão para notificações negada pelo usuário');
            // Adicionar um elemento na interface para informar o usuário
            this.showPermissionMessage();
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
            <button type="button" class="btn-close" data-bs-dismiss="alert" aria-label="Fechar"></button>
        `;
        
        document.body.appendChild(messageContainer);
    }

    async requestPermission() {
        try {
            if (Notification.permission === 'granted') {
                console.log('Permissão para notificações já concedida');
                return 'granted';
            }

            if (Notification.permission !== 'denied') {
                console.log('Solicitando permissão para notificações...');
                const permission = await Notification.requestPermission();
                console.log(`Resultado da solicitação de permissão: ${permission}`);
                
                // Se a permissão foi concedida, verificar o registro do service worker
                if (permission === 'granted' && 'serviceWorker' in navigator) {
                    const registration = await navigator.serviceWorker.ready;
                    console.log('Service Worker pronto para notificações:', registration);
                }
                
                return permission;
            }

            console.log('Permissão para notificações foi negada anteriormente');
            return Notification.permission;
        } catch (error) {
            console.error('Erro ao solicitar permissão para notificações:', error);
            return 'denied';
        }
    }

    showNotification(title, options = {}) {
        if (this.permission === 'granted') {
            const notification = new Notification(title, {
                icon: '/static/favicon.ico',
                badge: '/static/favicon.ico',
                ...options
            });

            // Auto fechar após 10 segundos
            setTimeout(() => {
                notification.close();
            }, 10000);

            return notification;
        }
    }

    async checkForUpdates() {
        try {
            // Verificar se o usuário está online
            if (!navigator.onLine) {
                console.log('Usuário está offline, pulando verificação de notificações');
                return;
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

            // Lembretes vencendo
            if (data.reminders_expiring && data.reminders_expiring.length > 0) {
                data.reminders_expiring.forEach(reminder => {
                    this.showNotification('🔔 Lembrete Vencendo!', {
                        body: `${reminder.name} - Responsável: ${reminder.responsible}`,
                        tag: `reminder-${reminder.id}`,
                        requireInteraction: true
                    });
                });
            }

            // Chamados atualizados
            if (data.chamados_updated && data.chamados_updated.length > 0) {
                data.chamados_updated.forEach(chamado => {
                    this.showNotification('📞 Chamado Atualizado!', {
                        body: `#${chamado.id} - ${chamado.titulo}`,
                        tag: `chamado-${chamado.id}`,
                        requireInteraction: true
                    });
                });
            }

            // Tarefas vencidas
            if (data.tasks_overdue && data.tasks_overdue.length > 0) {
                this.showNotification('⚠️ Tarefas Vencidas!', {
                    body: `${data.tasks_overdue.length} tarefa(s) em atraso`,
                    tag: 'tasks-overdue',
                    requireInteraction: true
                });
            }

        } catch (error) {
            console.error('Erro ao verificar notificações:', error);
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
