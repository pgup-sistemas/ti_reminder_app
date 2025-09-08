/**
 * Sistema de Feedback Visual Aprimorado - TI OSN System
 * Estados de loading, sucesso e erro profissionais
 */

class FeedbackManager {
    constructor() {
        this.toastContainer = null;
        this.loadingOverlays = new Map();
        this.init();
    }

    init() {
        this.createToastContainer();
        this.setupGlobalErrorHandling();
        this.setupFormEnhancements();
    }

    // ===== SISTEMA DE TOASTS =====
    createToastContainer() {
        if (document.getElementById('toast-container')) return;

        const container = document.createElement('div');
        container.id = 'toast-container';
        container.className = 'toast-container';
        document.body.appendChild(container);
    }

    toast(type, title, message, options = {}) {
        const config = {
            duration: options.duration || (type === 'error' ? 8000 : 4000),
            closable: options.closable !== false,
            actions: options.actions || [],
            position: options.position || 'top-right',
            ...options
        };

        const toastId = `toast-${Date.now()}-${Math.random().toString(36).substr(2, 9)}`;
        const toast = this.createToast(toastId, type, title, message, config);
        
        const container = document.getElementById('toast-container');
        container.appendChild(toast);

        // Animação de entrada
        requestAnimationFrame(() => {
            toast.classList.add('show');
        });

        // Auto-remove
        if (config.duration > 0) {
            setTimeout(() => {
                this.removeToast(toastId);
            }, config.duration);
        }

        return toastId;
    }

    createToast(id, type, title, message, config) {
        const toast = document.createElement('div');
        toast.id = id;
        toast.className = `toast toast-${type}`;
        
        const iconClass = this.getToastIcon(type);
        
        toast.innerHTML = `
            <div class="toast-content">
                <div class="toast-icon">
                    <i class="${iconClass}"></i>
                </div>
                <div class="toast-body">
                    <div class="toast-title">${title}</div>
                    <div class="toast-message">${message}</div>
                    ${config.actions.length > 0 ? this.createToastActions(config.actions) : ''}
                </div>
                ${config.closable ? '<button class="toast-close" aria-label="Fechar">&times;</button>' : ''}
            </div>
            <div class="toast-progress"></div>
        `;

        // Event listeners
        if (config.closable) {
            toast.querySelector('.toast-close').addEventListener('click', () => {
                this.removeToast(id);
            });
        }

        // Progress bar
        if (config.duration > 0) {
            const progressBar = toast.querySelector('.toast-progress');
            progressBar.style.animationDuration = `${config.duration}ms`;
        }

        return toast;
    }

    createToastActions(actions) {
        return `
            <div class="toast-actions">
                ${actions.map(action => `
                    <button class="toast-action-btn" data-action="${action.action}">
                        ${action.icon ? `<i class="${action.icon}"></i>` : ''}
                        ${action.text}
                    </button>
                `).join('')}
            </div>
        `;
    }

    removeToast(id) {
        const toast = document.getElementById(id);
        if (!toast) return;

        toast.classList.add('hide');
        setTimeout(() => {
            if (toast.parentNode) {
                toast.parentNode.removeChild(toast);
            }
        }, 300);
    }

    getToastIcon(type) {
        const icons = {
            success: 'fas fa-check-circle',
            error: 'fas fa-exclamation-circle',
            warning: 'fas fa-exclamation-triangle',
            info: 'fas fa-info-circle',
            loading: 'fas fa-spinner fa-spin'
        };
        return icons[type] || icons.info;
    }

    // Métodos de conveniência para toasts
    success(title, message, options = {}) {
        return this.toast('success', title, message, options);
    }

    error(title, message, options = {}) {
        return this.toast('error', title, message, options);
    }

    warning(title, message, options = {}) {
        return this.toast('warning', title, message, options);
    }

    info(title, message, options = {}) {
        return this.toast('info', title, message, options);
    }

    // ===== SISTEMA DE LOADING =====
    showLoading(target, options = {}) {
        const config = {
            message: options.message || 'Carregando...',
            spinner: options.spinner || 'default',
            backdrop: options.backdrop !== false,
            size: options.size || 'medium',
            ...options
        };

        const loadingId = `loading-${Date.now()}`;
        let targetElement;

        if (typeof target === 'string') {
            targetElement = document.querySelector(target);
        } else if (target instanceof HTMLElement) {
            targetElement = target;
        } else {
            targetElement = document.body;
        }

        if (!targetElement) return null;

        const overlay = this.createLoadingOverlay(loadingId, config);
        targetElement.appendChild(overlay);
        
        // Armazenar referência
        this.loadingOverlays.set(loadingId, {
            overlay: overlay,
            target: targetElement
        });

        // Animação de entrada
        requestAnimationFrame(() => {
            overlay.classList.add('show');
        });

        return loadingId;
    }

    createLoadingOverlay(id, config) {
        const overlay = document.createElement('div');
        overlay.id = id;
        overlay.className = `loading-overlay loading-${config.size}`;
        
        const spinnerClass = this.getSpinnerClass(config.spinner);
        
        overlay.innerHTML = `
            <div class="loading-content">
                <div class="loading-spinner ${spinnerClass}"></div>
                <div class="loading-message">${config.message}</div>
            </div>
        `;

        return overlay;
    }

    hideLoading(loadingId) {
        const loadingData = this.loadingOverlays.get(loadingId);
        if (!loadingData) return;

        const { overlay } = loadingData;
        overlay.classList.add('hide');

        setTimeout(() => {
            if (overlay.parentNode) {
                overlay.parentNode.removeChild(overlay);
            }
            this.loadingOverlays.delete(loadingId);
        }, 300);
    }

    getSpinnerClass(type) {
        const spinners = {
            default: 'spinner-default',
            dots: 'spinner-dots',
            pulse: 'spinner-pulse',
            bars: 'spinner-bars'
        };
        return spinners[type] || spinners.default;
    }

    // ===== MELHORIAS EM FORMULÁRIOS =====
    setupFormEnhancements() {
        // Validação em tempo real
        document.addEventListener('input', (e) => {
            if (e.target.matches('.form-control, .form-select')) {
                this.validateField(e.target);
            }
        });

        // Loading em formulários
        document.addEventListener('submit', (e) => {
            const form = e.target;
            if (form.matches('form:not(.no-loading)')) {
                this.showFormLoading(form);
            }
        });
    }

    validateField(field) {
        const value = field.value.trim();
        const isRequired = field.hasAttribute('required');
        const type = field.type;
        
        // Remover classes anteriores
        field.classList.remove('is-valid', 'is-invalid');
        
        // Validações básicas
        let isValid = true;
        let message = '';

        if (isRequired && !value) {
            isValid = false;
            message = 'Este campo é obrigatório';
        } else if (value) {
            // Validações por tipo
            switch (type) {
                case 'email':
                    const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;
                    if (!emailRegex.test(value)) {
                        isValid = false;
                        message = 'Digite um e-mail válido';
                    }
                    break;
                case 'tel':
                    const phoneRegex = /^[\d\s\-\(\)\+]+$/;
                    if (!phoneRegex.test(value)) {
                        isValid = false;
                        message = 'Digite um telefone válido';
                    }
                    break;
                case 'url':
                    try {
                        new URL(value);
                    } catch {
                        isValid = false;
                        message = 'Digite uma URL válida';
                    }
                    break;
            }
        }

        // Aplicar classes e feedback
        field.classList.add(isValid ? 'is-valid' : 'is-invalid');
        
        const feedback = field.parentNode.querySelector('.invalid-feedback');
        if (feedback) {
            feedback.textContent = message;
        }

        return isValid;
    }

    showFormLoading(form) {
        const submitBtn = form.querySelector('button[type="submit"], input[type="submit"]');
        if (submitBtn) {
            submitBtn.disabled = true;
            const originalText = submitBtn.textContent;
            submitBtn.innerHTML = '<i class="fas fa-spinner fa-spin me-2"></i>Processando...';
            
            // Restaurar após timeout ou erro
            setTimeout(() => {
                submitBtn.disabled = false;
                submitBtn.textContent = originalText;
            }, 10000);
        }
    }

    // ===== TRATAMENTO GLOBAL DE ERROS =====
    setupGlobalErrorHandling() {
        // Desabilitar tratamento global de erros por enquanto
        // para evitar toasts desnecessários durante navegação
        
        // Erros de rede apenas
        this.setupNetworkErrorHandling();
    }

    setupNetworkErrorHandling() {
        // Interceptar fetch apenas para erros críticos de rede
        const originalFetch = window.fetch;
        window.fetch = async (...args) => {
            try {
                const response = await originalFetch(...args);
                
                // Só mostrar erro para códigos 5xx (erro do servidor)
                if (response.status >= 500) {
                    const errorMessage = `Erro ${response.status}: ${response.statusText}`;
                    this.error('Erro do Servidor', errorMessage);
                }
                
                return response;
            } catch (error) {
                // Só mostrar se for erro de rede real
                if (error.name === 'NetworkError' || error.message.includes('Failed to fetch')) {
                    this.error('Erro de Conexão', 'Verifique sua conexão com a internet.');
                }
                throw error;
            }
        };
    }

    // ===== MÉTODOS UTILITÁRIOS =====
    
    // Confirmar ação com feedback
    async confirmAction(message, title = 'Confirmação') {
        if (window.Modal) {
            const result = await window.Modal.confirm(message, title);
            return result.action === 'confirm';
        }
        return confirm(`${title}\n\n${message}`);
    }

    // Mostrar progresso de upload
    showUploadProgress(file, onProgress) {
        const toastId = this.toast('info', 'Upload', `Enviando ${file.name}...`, {
            duration: 0,
            closable: false
        });

        return {
            update: (percent) => {
                const toast = document.getElementById(toastId);
                if (toast) {
                    const message = toast.querySelector('.toast-message');
                    message.textContent = `Enviando ${file.name}... ${percent}%`;
                }
            },
            complete: () => {
                this.removeToast(toastId);
                this.success('Upload', `${file.name} enviado com sucesso!`);
            },
            error: (error) => {
                this.removeToast(toastId);
                this.error('Erro no Upload', `Falha ao enviar ${file.name}: ${error}`);
            }
        };
    }

    // Debounce para validações
    debounce(func, wait) {
        let timeout;
        return function executedFunction(...args) {
            const later = () => {
                clearTimeout(timeout);
                func(...args);
            };
            clearTimeout(timeout);
            timeout = setTimeout(later, wait);
        };
    }
}

// Instância global
window.Feedback = new FeedbackManager();

// Aliases para compatibilidade
window.showToast = (type, title, message, options) => window.Feedback.toast(type, title, message, options);
window.showLoading = (target, options) => window.Feedback.showLoading(target, options);
window.hideLoading = (id) => window.Feedback.hideLoading(id);

// Exportar para uso em módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = FeedbackManager;
}
