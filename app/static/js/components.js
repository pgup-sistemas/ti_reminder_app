
// Sistema de Componentes Reutilizáveis
class ComponentManager {
    constructor() {
        this.components = new Map();
        this.init();
    }

    init() {
        this.registerComponents();
        this.initializeComponents();
    }

    registerComponents() {
        // Toast Notifications
        this.components.set('toast', {
            create: (type, title, message, duration = 5000) => {
                const toastId = `toast-${Date.now()}`;
                const toastHTML = `
                    <div id="${toastId}" class="toast-modern toast-${type} fade-in">
                        <div class="d-flex align-items-center">
                            <div class="me-3">
                                ${this.getIcon(type)}
                            </div>
                            <div class="flex-grow-1">
                                <div class="fw-bold">${title}</div>
                                <div class="small text-muted">${message}</div>
                            </div>
                            <button type="button" class="btn-close ms-2" onclick="this.closest('.toast-modern').remove()"></button>
                        </div>
                        <div class="toast-progress">
                            <div class="toast-progress-bar" style="animation: progress ${duration}ms linear;"></div>
                        </div>
                    </div>
                `;

                let container = document.querySelector('.toast-container');
                if (!container) {
                    container = document.createElement('div');
                    container.className = 'toast-container';
                    document.body.appendChild(container);
                }

                container.insertAdjacentHTML('beforeend', toastHTML);

                // Auto remove
                setTimeout(() => {
                    const toast = document.getElementById(toastId);
                    if (toast) {
                        toast.style.animation = 'slideOutRight 0.3s ease-in';
                        setTimeout(() => toast.remove(), 300);
                    }
                }, duration);

                return toastId;
            }
        });

        // Modal Component
        this.components.set('modal', {
            create: (title, content, options = {}) => {
                const modalId = `modal-${Date.now()}`;
                const modalHTML = `
                    <div class="modal fade" id="${modalId}" tabindex="-1">
                        <div class="modal-dialog modal-lg">
                            <div class="modal-content modern-card">
                                <div class="modal-header modern-card-header">
                                    <h5 class="modal-title">${title}</h5>
                                    <button type="button" class="btn-close btn-close-white" data-bs-dismiss="modal"></button>
                                </div>
                                <div class="modal-body p-4">
                                    ${content}
                                </div>
                                ${options.showFooter !== false ? `
                                <div class="modal-footer">
                                    <button type="button" class="btn btn-secondary" data-bs-dismiss="modal">Fechar</button>
                                    ${options.primaryButton || ''}
                                </div>
                                ` : ''}
                            </div>
                        </div>
                    </div>
                `;

                document.body.insertAdjacentHTML('beforeend', modalHTML);
                const modal = new bootstrap.Modal(document.getElementById(modalId));
                
                // Cleanup on hide
                document.getElementById(modalId).addEventListener('hidden.bs.modal', function() {
                    this.remove();
                });

                return modal;
            }
        });

        // Loading Overlay
        this.components.set('loading', {
            show: (message = 'Carregando...') => {
                const loadingHTML = `
                    <div id="loading-overlay" class="position-fixed top-0 start-0 w-100 h-100 d-flex align-items-center justify-content-center" style="background: rgba(0,0,0,0.5); z-index: 9999;">
                        <div class="modern-card p-4 text-center">
                            <div class="loading-spinner mb-3"></div>
                            <div>${message}</div>
                        </div>
                    </div>
                `;
                document.body.insertAdjacentHTML('beforeend', loadingHTML);
            },
            hide: () => {
                const overlay = document.getElementById('loading-overlay');
                if (overlay) overlay.remove();
            }
        });

        // Confirmation Dialog
        this.components.set('confirm', {
            show: (title, message, onConfirm, onCancel = null) => {
                const content = `
                    <div class="text-center">
                        <i class="fas fa-question-circle text-warning fs-1 mb-3"></i>
                        <p class="mb-0">${message}</p>
                    </div>
                `;
                
                const modal = this.components.get('modal').create(title, content, {
                    primaryButton: `
                        <button type="button" class="btn btn-danger" id="confirm-yes">Sim, confirmar</button>
                    `
                });

                modal.show();

                // Event listeners
                document.getElementById('confirm-yes').addEventListener('click', () => {
                    modal.hide();
                    if (onConfirm) onConfirm();
                });

                if (onCancel) {
                    document.querySelector('[data-bs-dismiss="modal"]').addEventListener('click', onCancel);
                }
            }
        });
    }

    getIcon(type) {
        const icons = {
            success: '<i class="fas fa-check-circle text-success"></i>',
            error: '<i class="fas fa-times-circle text-danger"></i>',
            warning: '<i class="fas fa-exclamation-triangle text-warning"></i>',
            info: '<i class="fas fa-info-circle text-info"></i>'
        };
        return icons[type] || icons.info;
    }

    initializeComponents() {
        // Auto-initialize existing elements
        this.initDatePickers();
        this.initFormValidation();
        this.initTableSearch();
        this.initTooltips();
    }

    initDatePickers() {
        // Modern date picker styling
        document.querySelectorAll('input[type="date"]').forEach(input => {
            input.classList.add('form-control-modern');
        });
    }

    initFormValidation() {
        // Real-time form validation
        document.querySelectorAll('form').forEach(form => {
            form.addEventListener('submit', function(e) {
                const requiredFields = this.querySelectorAll('[required]');
                let isValid = true;

                requiredFields.forEach(field => {
                    if (!field.value.trim()) {
                        field.classList.add('is-invalid');
                        isValid = false;
                    } else {
                        field.classList.remove('is-invalid');
                    }
                });

                if (!isValid) {
                    e.preventDefault();
                    components.get('toast').create('error', 'Erro', 'Preencha todos os campos obrigatórios');
                }
            });
        });
    }

    initTableSearch() {
        // Live table search
        document.querySelectorAll('[data-table-search]').forEach(input => {
            const tableId = input.getAttribute('data-table-search');
            const table = document.getElementById(tableId);
            
            if (table) {
                input.addEventListener('input', function() {
                    const searchTerm = this.value.toLowerCase();
                    const rows = table.querySelectorAll('tbody tr');
                    
                    rows.forEach(row => {
                        const text = row.textContent.toLowerCase();
                        row.style.display = text.includes(searchTerm) ? '' : 'none';
                    });
                });
            }
        });
    }

    initTooltips() {
        // Initialize Bootstrap tooltips
        const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
        tooltipTriggerList.map(function (tooltipTriggerEl) {
            return new bootstrap.Tooltip(tooltipTriggerEl);
        });
    }

    // Public API
    get(componentName) {
        return this.components.get(componentName);
    }

    toast(type, title, message, duration) {
        return this.get('toast').create(type, title, message, duration);
    }

    modal(title, content, options) {
        return this.get('modal').create(title, content, options);
    }

    loading(show = true, message) {
        if (show) {
            this.get('loading').show(message);
        } else {
            this.get('loading').hide();
        }
    }

    confirm(title, message, onConfirm, onCancel) {
        return this.get('confirm').show(title, message, onConfirm, onCancel);
    }
}

// CSS adicional para progress bar
const additionalCSS = `
    @keyframes progress {
        from { width: 100%; }
        to { width: 0%; }
    }
    
    .toast-progress {
        position: absolute;
        bottom: 0;
        left: 0;
        width: 100%;
        height: 3px;
        background: rgba(0,0,0,0.1);
        border-radius: 0 0 12px 12px;
    }
    
    .toast-progress-bar {
        height: 100%;
        background: currentColor;
        border-radius: 0 0 12px 12px;
        opacity: 0.6;
    }
    
    @keyframes slideOutRight {
        to {
            opacity: 0;
            transform: translateX(100%);
        }
    }
`;

// Inject CSS
const style = document.createElement('style');
style.textContent = additionalCSS;
document.head.appendChild(style);

// Global instance
window.components = new ComponentManager();

// Export for modules
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ComponentManager;
}
