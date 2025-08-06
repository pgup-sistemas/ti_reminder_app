
class OfflineManager {
    constructor() {
        this.isOnline = navigator.onLine;
        this.pendingData = new Map();
        this.init();
    }

    init() {
        // Listeners de conectividade
        window.addEventListener('online', () => {
            this.isOnline = true;
            this.showConnectionStatus('online');
            this.syncPendingData();
        });

        window.addEventListener('offline', () => {
            this.isOnline = false;
            this.showConnectionStatus('offline');
        });

        // Interceptar formulários para cache offline
        this.interceptForms();
        
        // Mostrar status inicial
        if (!this.isOnline) {
            this.showConnectionStatus('offline');
        }
    }

    showConnectionStatus(status) {
        const message = status === 'online' 
            ? { type: 'success', title: 'Conectado', message: 'Conexão restaurada!' }
            : { type: 'warning', title: 'Offline', message: 'Trabalhando offline. Dados serão sincronizados quando voltar a conexão.' };

        if (window.components) {
            window.components.toast(message.type, message.title, message.message);
        }

        // Badge visual no topo da página
        this.updateConnectionBadge(status);
    }

    updateConnectionBadge(status) {
        let badge = document.getElementById('connection-status');
        
        if (!badge) {
            badge = document.createElement('div');
            badge.id = 'connection-status';
            badge.style.cssText = `
                position: fixed;
                top: 10px;
                right: 10px;
                z-index: 9999;
                padding: 8px 16px;
                border-radius: 20px;
                font-size: 12px;
                font-weight: bold;
                text-transform: uppercase;
                letter-spacing: 0.5px;
                transition: all 0.3s ease;
            `;
            document.body.appendChild(badge);
        }

        if (status === 'offline') {
            badge.textContent = '🔴 Offline';
            badge.style.background = 'rgba(220, 53, 69, 0.9)';
            badge.style.color = 'white';
            badge.style.display = 'block';
        } else {
            badge.textContent = '🟢 Online';
            badge.style.background = 'rgba(25, 135, 84, 0.9)';
            badge.style.color = 'white';
            badge.style.display = 'block';
            
            // Auto-hide após 3 segundos
            setTimeout(() => {
                badge.style.display = 'none';
            }, 3000);
        }
    }

    interceptForms() {
        document.addEventListener('submit', (e) => {
            const form = e.target;
            
            // Apenas para formulários de criação/edição
            if (form.method.toLowerCase() === 'post' && !this.isOnline) {
                e.preventDefault();
                this.storeFormData(form);
                
                if (window.components) {
                    window.components.toast('info', 'Dados Salvos', 'Formulário salvo offline. Será enviado quando a conexão for restaurada.');
                }
            }
        });
    }

    storeFormData(form) {
        const formData = new FormData(form);
        const data = Object.fromEntries(formData.entries());
        const timestamp = Date.now();
        const key = `form_${form.action}_${timestamp}`;

        // Armazenar no localStorage
        const pendingForms = JSON.parse(localStorage.getItem('pendingForms') || '[]');
        pendingForms.push({
            key,
            action: form.action,
            method: form.method,
            data,
            timestamp
        });
        
        localStorage.setItem('pendingForms', JSON.stringify(pendingForms));
        
        this.pendingData.set(key, {
            action: form.action,
            method: form.method,
            data,
            timestamp
        });
    }

    async syncPendingData() {
        const pendingForms = JSON.parse(localStorage.getItem('pendingForms') || '[]');
        
        if (pendingForms.length === 0) return;

        let syncCount = 0;
        const errors = [];

        for (const formData of pendingForms) {
            try {
                const response = await fetch(formData.action, {
                    method: formData.method,
                    headers: {
                        'Content-Type': 'application/x-www-form-urlencoded',
                    },
                    body: new URLSearchParams(formData.data)
                });

                if (response.ok) {
                    syncCount++;
                    // Remover do localStorage
                    const remaining = pendingForms.filter(f => f.key !== formData.key);
                    localStorage.setItem('pendingForms', JSON.stringify(remaining));
                } else {
                    errors.push(`Erro ao sincronizar formulário: ${response.status}`);
                }
            } catch (error) {
                errors.push(`Erro de rede: ${error.message}`);
            }
        }

        // Mostrar resultados
        if (syncCount > 0) {
            if (window.components) {
                window.components.toast('success', 'Sincronização', `${syncCount} formulário(s) sincronizado(s) com sucesso!`);
            }
        }

        if (errors.length > 0) {
            console.error('Erros de sincronização:', errors);
        }
    }

    // API pública
    getPendingCount() {
        const pending = JSON.parse(localStorage.getItem('pendingForms') || '[]');
        return pending.length;
    }

    clearPendingData() {
        localStorage.removeItem('pendingForms');
        this.pendingData.clear();
    }
}

// Inicializar quando a página carregar
document.addEventListener('DOMContentLoaded', () => {
    window.offlineManager = new OfflineManager();
});
