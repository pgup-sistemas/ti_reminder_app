/**
 * Sistema de Modais Modernas - TI OSN System
 * Substituição elegante para alerts básicos
 */

class ModernModal {
    constructor() {
        this.activeModal = null;
        this.modalCount = 0;
        this.init();
    }

    init() {
        // Criar container de modais se não existir
        if (!document.getElementById('modal-container')) {
            const container = document.createElement('div');
            container.id = 'modal-container';
            container.className = 'modal-container';
            document.body.appendChild(container);
        }

        // Event listeners
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.activeModal) {
                this.close();
            }
        });
    }

    /**
     * Criar e exibir modal
     * @param {Object} options - Configurações do modal
     */
    show(options = {}) {
        const config = {
            title: options.title || 'Confirmação',
            message: options.message || '',
            type: options.type || 'info', // info, success, warning, error, confirm
            size: options.size || 'medium', // small, medium, large
            buttons: options.buttons || this.getDefaultButtons(options.type),
            closable: options.closable !== false,
            backdrop: options.backdrop !== false,
            animation: options.animation !== false,
            onShow: options.onShow || null,
            onHide: options.onHide || null,
            customClass: options.customClass || ''
        };

        return new Promise((resolve, reject) => {
            const modalId = `modal-${++this.modalCount}`;
            const modal = this.createModal(modalId, config, resolve, reject);
            
            document.getElementById('modal-container').appendChild(modal);
            
            // Animação de entrada
            if (config.animation) {
                requestAnimationFrame(() => {
                    modal.classList.add('show');
                });
            } else {
                modal.classList.add('show');
            }

            this.activeModal = modal;
            
            // Callback onShow
            if (config.onShow) {
                config.onShow();
            }

            // Auto-focus no primeiro botão
            const firstButton = modal.querySelector('.modal-button');
            if (firstButton) {
                setTimeout(() => firstButton.focus(), 100);
            }
        });
    }

    /**
     * Criar elemento do modal
     */
    createModal(modalId, config, resolve, reject) {
        const modal = document.createElement('div');
        modal.className = `modal-overlay ${config.customClass}`;
        modal.id = modalId;
        
        const iconClass = this.getIconClass(config.type);
        const colorClass = this.getColorClass(config.type);

        modal.innerHTML = `
            <div class="modal-dialog modal-${config.size}">
                <div class="modal-content">
                    ${config.closable ? '<button class="modal-close" aria-label="Fechar">&times;</button>' : ''}
                    
                    <div class="modal-header ${colorClass}">
                        <div class="modal-icon">
                            <i class="${iconClass}"></i>
                        </div>
                        <h3 class="modal-title">${config.title}</h3>
                    </div>
                    
                    <div class="modal-body">
                        <div class="modal-message">${config.message}</div>
                    </div>
                    
                    <div class="modal-footer">
                        ${this.createButtons(config.buttons, resolve, reject)}
                    </div>
                </div>
            </div>
        `;

        // Event listeners
        this.attachEventListeners(modal, config, resolve, reject);

        return modal;
    }

    /**
     * Criar botões do modal
     */
    createButtons(buttons, resolve, reject) {
        return buttons.map(button => {
            const btnClass = button.class || 'btn-secondary';
            const btnType = button.type || 'button';
            
            return `
                <button type="${btnType}" 
                        class="modal-button btn ${btnClass}" 
                        data-action="${button.action}"
                        ${button.autofocus ? 'autofocus' : ''}>
                    ${button.icon ? `<i class="${button.icon}"></i>` : ''}
                    ${button.text}
                </button>
            `;
        }).join('');
    }

    /**
     * Anexar event listeners
     */
    attachEventListeners(modal, config, resolve, reject) {
        // Botão de fechar
        const closeBtn = modal.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                this.close();
                resolve({ action: 'close', value: null });
            });
        }

        // Backdrop
        if (config.backdrop) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    this.close();
                    resolve({ action: 'backdrop', value: null });
                }
            });
        }

        // Botões de ação
        const buttons = modal.querySelectorAll('.modal-button');
        buttons.forEach(button => {
            button.addEventListener('click', () => {
                const action = button.dataset.action;
                this.close();
                
                if (action === 'confirm') {
                    resolve({ action: 'confirm', value: true });
                } else if (action === 'cancel') {
                    resolve({ action: 'cancel', value: false });
                } else {
                    resolve({ action: action, value: action });
                }
            });
        });
    }

    /**
     * Fechar modal ativo
     */
    close() {
        if (!this.activeModal) return;

        this.activeModal.classList.add('hide');
        
        setTimeout(() => {
            if (this.activeModal && this.activeModal.parentNode) {
                this.activeModal.parentNode.removeChild(this.activeModal);
            }
            this.activeModal = null;
        }, 300);
    }

    /**
     * Obter botões padrão por tipo
     */
    getDefaultButtons(type) {
        switch (type) {
            case 'confirm':
                return [
                    { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
                    { text: 'Confirmar', action: 'confirm', class: 'btn-primary', autofocus: true }
                ];
            case 'error':
                return [
                    { text: 'Entendi', action: 'ok', class: 'btn-danger', autofocus: true }
                ];
            case 'success':
                return [
                    { text: 'Ótimo!', action: 'ok', class: 'btn-success', autofocus: true }
                ];
            case 'warning':
                return [
                    { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
                    { text: 'Continuar', action: 'confirm', class: 'btn-warning', autofocus: true }
                ];
            default:
                return [
                    { text: 'OK', action: 'ok', class: 'btn-primary', autofocus: true }
                ];
        }
    }

    /**
     * Obter classe do ícone por tipo
     */
    getIconClass(type) {
        const icons = {
            info: 'fas fa-info-circle',
            success: 'fas fa-check-circle',
            warning: 'fas fa-exclamation-triangle',
            error: 'fas fa-times-circle',
            confirm: 'fas fa-question-circle'
        };
        return icons[type] || icons.info;
    }

    /**
     * Obter classe de cor por tipo
     */
    getColorClass(type) {
        const colors = {
            info: 'modal-info',
            success: 'modal-success',
            warning: 'modal-warning',
            error: 'modal-error',
            confirm: 'modal-confirm'
        };
        return colors[type] || colors.info;
    }

    // Métodos de conveniência
    alert(message, title = 'Aviso') {
        return this.show({
            type: 'info',
            title: title,
            message: message
        });
    }

    confirm(message, title = 'Confirmação') {
        return this.show({
            type: 'confirm',
            title: title,
            message: message
        });
    }

    success(message, title = 'Sucesso') {
        return this.show({
            type: 'success',
            title: title,
            message: message
        });
    }

    error(message, title = 'Erro') {
        return this.show({
            type: 'error',
            title: title,
            message: message
        });
    }

    warning(message, title = 'Atenção') {
        return this.show({
            type: 'warning',
            title: title,
            message: message
        });
    }

    /**
     * Modal de loading
     */
    loading(message = 'Carregando...', title = 'Aguarde') {
        return this.show({
            title: title,
            message: `
                <div class="loading-content">
                    <div class="loading-spinner"></div>
                    <p>${message}</p>
                </div>
            `,
            type: 'info',
            closable: false,
            backdrop: false,
            buttons: []
        });
    }

    /**
     * Modal customizado com formulário
     */
    prompt(options = {}) {
        const config = {
            title: options.title || 'Entrada de Dados',
            label: options.label || 'Digite o valor:',
            placeholder: options.placeholder || '',
            defaultValue: options.defaultValue || '',
            inputType: options.inputType || 'text',
            required: options.required !== false,
            validation: options.validation || null,
            ...options
        };

        const inputId = `modal-input-${this.modalCount + 1}`;
        
        return this.show({
            ...config,
            message: `
                <div class="form-group">
                    <label for="${inputId}" class="form-label">${config.label}</label>
                    <input type="${config.inputType}" 
                           id="${inputId}"
                           class="form-control" 
                           placeholder="${config.placeholder}"
                           value="${config.defaultValue}"
                           ${config.required ? 'required' : ''}>
                    <div class="invalid-feedback"></div>
                </div>
            `,
            buttons: [
                { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
                { text: 'Confirmar', action: 'confirm', class: 'btn-primary' }
            ]
        }).then(result => {
            if (result.action === 'confirm') {
                const input = document.getElementById(inputId);
                const value = input ? input.value : '';
                
                // Validação
                if (config.required && !value.trim()) {
                    return this.error('Este campo é obrigatório.');
                }
                
                return { action: 'confirm', value: value };
            }
            return result;
        });
    }

    /**
     * Obter botões padrão por tipo
     */
    getDefaultButtons(type) {
        switch (type) {
            case 'confirm':
                return [
                    { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
                    { text: 'Confirmar', action: 'confirm', class: 'btn-primary', autofocus: true }
                ];
            case 'error':
                return [
                    { text: 'Entendi', action: 'ok', class: 'btn-danger', autofocus: true }
                ];
            case 'success':
                return [
                    { text: 'Ótimo!', action: 'ok', class: 'btn-success', autofocus: true }
                ];
            case 'warning':
                return [
                    { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
                    { text: 'Continuar', action: 'confirm', class: 'btn-warning', autofocus: true }
                ];
            default:
                return [
                    { text: 'OK', action: 'ok', class: 'btn-primary', autofocus: true }
                ];
        }
    }

    /**
     * Obter classe do ícone por tipo
     */
    getIconClass(type) {
        const icons = {
            info: 'fas fa-info-circle',
            success: 'fas fa-check-circle',
            warning: 'fas fa-exclamation-triangle',
            error: 'fas fa-times-circle',
            confirm: 'fas fa-question-circle'
        };
        return icons[type] || icons.info;
    }

    /**
     * Obter classe de cor por tipo
     */
    getColorClass(type) {
        const colors = {
            info: 'modal-info',
            success: 'modal-success',
            warning: 'modal-warning',
            error: 'modal-error',
            confirm: 'modal-confirm'
        };
        return colors[type] || colors.info;
    }

    // Métodos de conveniência
    alert(message, title = 'Aviso') {
        return this.show({
            type: 'info',
            title: title,
            message: message
        });
    }

    confirm(message, title = 'Confirmação') {
        return this.show({
            type: 'confirm',
            title: title,
            message: message
        });
    }

    success(message, title = 'Sucesso') {
        return this.show({
            type: 'success',
            title: title,
            message: message
        });
    }

    error(message, title = 'Erro') {
        return this.show({
            type: 'error',
            title: title,
            message: message
        });
    }

    warning(message, title = 'Atenção') {
        return this.show({
            type: 'warning',
            title: title,
            message: message
        });
    }

    /**
     * Modal de loading
     */
    loading(message = 'Carregando...', title = 'Aguarde') {
        return this.show({
            title: title,
            message: `
                <div class="loading-content">
                    <div class="loading-spinner"></div>
                    <p>${message}</p>
                </div>
            `,
            type: 'info',
            closable: false,
            backdrop: false,
            buttons: []
        });
    }

    /**
     * Modal customizado com formulário
     */
    prompt(options = {}) {
        const config = {
            title: options.title || 'Entrada de Dados',
            label: options.label || 'Digite o valor:',
            placeholder: options.placeholder || '',
            defaultValue: options.defaultValue || '',
            inputType: options.inputType || 'text',
            required: options.required !== false,
            validation: options.validation || null,
            ...options
        };

        const inputId = `modal-input-${this.modalCount + 1}`;
        
        return this.show({
            ...config,
            message: `
                <div class="form-group">
                    <label for="${inputId}" class="form-label">${config.label}</label>
                    <input type="${config.inputType}" 
                           id="${inputId}"
                           class="form-control" 
                           placeholder="${config.placeholder}"
                           value="${config.defaultValue}"
                           ${config.required ? 'required' : ''}>
                    <div class="invalid-feedback"></div>
                </div>
            `,
            buttons: [
                { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
                { text: 'Confirmar', action: 'confirm', class: 'btn-primary' }
            ]
        }).then(result => {
            if (result.action === 'confirm') {
                const input = document.getElementById(inputId);
                const value = input ? input.value : '';
                
                // Validação
                if (config.required && !value.trim()) {
                    return this.error('Este campo é obrigatório.');
                }
                
                if (config.validation && !config.validation(value)) {
                    return this.error('Valor inválido.');
                }
                
                return { action: 'confirm', value: value };
            }
            return result;
        });
    }
}

// Aguardar DOM estar pronto antes de inicializar
if (document.readyState === 'loading') {
    document.addEventListener('DOMContentLoaded', () => {
        window.Modal = new ModalManager();
    });
} else {
    window.Modal = new ModalManager();
}

// Exportar para uso em módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ModalManager;
}
