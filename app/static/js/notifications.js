
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
        if (this.permission === 'granted') {
            this.startPolling();
        }
    }

    async requestPermission() {
        if (Notification.permission === 'granted') {
            return 'granted';
        }

        if (Notification.permission !== 'denied') {
            const permission = await Notification.requestPermission();
            return permission;
        }

        return Notification.permission;
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
            const response = await fetch('/api/notifications');
            console.log('API Response:', response);
            let data;
            try {
                const responseText = await response.text();
                console.log('Response Text:', responseText);
                // Parse o texto da resposta para JSON em vez de chamar response.json()
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
        setInterval(() => {
            this.checkForUpdates();
        }, this.checkInterval);
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
