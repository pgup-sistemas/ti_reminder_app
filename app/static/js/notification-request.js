/**
 * Sistema de Solicitação de Permissão de Notificações
 * Aparece após login para pedir autorização de forma elegante
 */

class NotificationRequestManager {
    constructor() {
        this.storageKey = 'notification_permission_asked';
        this.init();
    }

    init() {
        // Verificar se deve mostrar solicitação após login
        this.checkAndShowRequest();
    }

    hasAlreadyAsked() {
        // Verificar se já pedimos permissão
        const asked = localStorage.getItem(this.storageKey);
        const permission = Notification.permission;
        
        // Se já tem permissão (granted ou denied), não pedir novamente
        if (permission !== 'default') {
            return true;
        }
        
        // Se já pedimos nas últimas 7 dias, não pedir novamente
        if (asked) {
            const askedTime = parseInt(asked);
            const now = Date.now();
            const sevenDays = 7 * 24 * 60 * 60 * 1000;
            
            if (now - askedTime < sevenDays) {
                return true;
            }
        }
        
        return false;
    }

    checkAndShowRequest() {
        // Verificar se notificações são suportadas
        if (!('Notification' in window)) {
            return;
        }

        // Verificar se já pedimos
        if (this.hasAlreadyAsked()) {
            return;
        }

        // Aguardar 3 segundos após o carregamento para não ser invasivo
        setTimeout(() => {
            this.showRequestToast();
        }, 3000);
    }

    showRequestToast() {
        // Usar nosso sistema de toasts
        if (!window.Feedback) {
            console.warn('FeedbackManager não disponível');
            return;
        }

        // Toast com ações customizadas
        const toastId = window.Feedback.toast('info', 
            '🔔 Ativar Notificações', 
            'Receba alertas sobre lembretes, tarefas e chamados importantes mesmo quando não estiver no sistema.',
            {
                duration: 0, // Não fechar automaticamente
                closable: true,
                actions: [
                    {
                        text: 'Ativar Agora',
                        action: 'enable'
                    },
                    {
                        text: 'Talvez Depois',
                        action: 'later'
                    }
                ]
            }
        );

        // Adicionar listeners para as ações
        setTimeout(() => {
            // Botão "Ativar Agora"
            const enableBtn = document.querySelector('[data-action="enable"]');
            if (enableBtn) {
                enableBtn.addEventListener('click', () => {
                    this.requestPermission();
                    window.Feedback.removeToast(toastId);
                });
            }

            // Botão "Talvez Depois"
            const laterBtn = document.querySelector('[data-action="later"]');
            if (laterBtn) {
                laterBtn.addEventListener('click', () => {
                    this.markAsAsked();
                    window.Feedback.removeToast(toastId);
                    window.Feedback.info('OK!', 'Você pode ativar as notificações depois nas configurações.');
                });
            }

            // Botão fechar (X)
            const closeBtn = document.querySelector(`#${toastId} .toast-close`);
            if (closeBtn) {
                closeBtn.addEventListener('click', () => {
                    this.markAsAsked();
                });
            }
        }, 100);
    }

    async requestPermission() {
        try {
            const permission = await Notification.requestPermission();
            
            this.markAsAsked();

            if (permission === 'granted') {
                // Permissão concedida!
                window.Feedback.success(
                    'Notificações Ativadas!',
                    'Você receberá alertas importantes mesmo quando não estiver usando o sistema.'
                );

                // Inicializar o sistema de notificações nativas
                if (window.notificationManager) {
                    window.notificationManager.init();
                }

                // Mostrar notificação de teste
                this.showTestNotification();
            } else if (permission === 'denied') {
                // Permissão negada
                window.Feedback.warning(
                    'Notificações Bloqueadas',
                    'Você pode ativar depois clicando no ícone de cadeado na barra de endereços.'
                );
            } else {
                // Default - usuário fechou sem decidir
                window.Feedback.info(
                    'Decisão Adiada',
                    'Você pode ativar as notificações depois nas configurações.'
                );
            }
        } catch (error) {
            console.error('Erro ao solicitar permissão:', error);
            window.Feedback.error(
                'Erro',
                'Não foi possível solicitar permissão para notificações.'
            );
        }
    }

    showTestNotification() {
        // Mostrar notificação de teste após 2 segundos
        setTimeout(() => {
            if (window.notificationManager) {
                window.notificationManager.showNotification(
                    '✅ Notificações Funcionando!',
                    {
                        body: 'Você receberá alertas importantes sobre lembretes, tarefas e chamados.',
                        icon: '/static/favicon.ico',
                        tag: 'test-notification'
                    }
                );
            } else {
                // Fallback se o NotificationManager não estiver disponível
                new Notification('✅ Notificações Funcionando!', {
                    body: 'Você receberá alertas importantes sobre lembretes, tarefas e chamados.',
                    icon: '/static/favicon.ico'
                });
            }
        }, 2000);
    }

    markAsAsked() {
        // Marcar que já pedimos permissão
        localStorage.setItem(this.storageKey, Date.now().toString());
    }
}

// Inicializar quando o DOM estiver pronto
// Mas só em páginas que NÃO são de login
document.addEventListener('DOMContentLoaded', () => {
    // Verificar se não estamos na página de login
    const isLoginPage = window.location.pathname.includes('/login') || 
                        window.location.pathname === '/';
    
    // Verificar se há indicação de login recente
    const justLoggedIn = sessionStorage.getItem('just_logged_in');
    
    if (!isLoginPage && justLoggedIn) {
        // Remover flag
        sessionStorage.removeItem('just_logged_in');
        
        // Inicializar solicitação de notificações
        new NotificationRequestManager();
    }
});
