/**
 * Sistema de Modais Modernas - TI OSN System
 * Substituição elegante para alerts básicos
 * Versão 2.0 - Otimizado e profissional
 * 
 * @class ModernModal
 * @description Sistema completo de modais com suporte a confirmações, alertas, prompts e loading
 */

class ModernModal {
    constructor() {
        this.activeModal = null;
        this.modalCount = 0;
        this.modalStack = [];
        this.init();
    }

    /**
     * Inicializa o sistema de modais
     * @private
     */
    init() {
        // Criar container de modais se não existir
        if (!document.getElementById('modal-container')) {
            const container = document.createElement('div');
            container.id = 'modal-container';
            container.className = 'modal-container';
            container.setAttribute('role', 'dialog');
            container.setAttribute('aria-modal', 'true');
            document.body.appendChild(container);
        }

        // Event listeners globais
        document.addEventListener('keydown', (e) => {
            if (e.key === 'Escape' && this.activeModal) {
                this.close();
            }
        });

        // Prevenir scroll quando modal está aberto
        this.preventBodyScroll();
    }

    /**
     * Previne scroll do body quando modal está aberto
     * @private
     */
    preventBodyScroll() {
        const observer = new MutationObserver(() => {
            const hasModal = document.querySelector('.modal-overlay.show');
            document.body.style.overflow = hasModal ? 'hidden' : '';
        });

        observer.observe(document.getElementById('modal-container'), {
            childList: true,
            subtree: true,
            attributes: true,
            attributeFilter: ['class']
        });
    }

    /**
     * Criar e exibir modal
     * @param {Object} options - Configurações do modal
     * @param {string} options.title - Título do modal
     * @param {string} options.message - Mensagem/conteúdo do modal
     * @param {string} options.type - Tipo: info, success, warning, error, confirm
     * @param {string} options.size - Tamanho: small, medium, large, xl
     * @param {Array} options.buttons - Array de botões customizados
     * @param {boolean} options.closable - Se pode fechar com X
     * @param {boolean} options.backdrop - Se fecha ao clicar fora
     * @param {boolean} options.animation - Se usa animação
     * @param {Function} options.onShow - Callback ao mostrar
     * @param {Function} options.onHide - Callback ao esconder
     * @param {Function} options.onConfirm - Callback ao confirmar
     * @param {Function} options.onCancel - Callback ao cancelar
     * @param {string} options.customClass - Classes CSS adicionais
     * @returns {Promise} Promise que resolve com a ação do usuário
     */
    show(options = {}) {
        const config = {
            title: options.title || 'Confirmação',
            message: options.message || '',
            type: options.type || 'info',
            size: options.size || 'medium',
            buttons: options.buttons || this.getDefaultButtons(options.type),
            closable: options.closable !== false,
            backdrop: options.backdrop !== false,
            animation: options.animation !== false,
            onShow: options.onShow || null,
            onHide: options.onHide || null,
            onConfirm: options.onConfirm || null,
            onCancel: options.onCancel || null,
            customClass: options.customClass || '',
            html: options.html || false // Permite HTML customizado no message
        };

        return new Promise((resolve, reject) => {
            const modalId = `modal-${++this.modalCount}`;
            const modal = this.createModal(modalId, config, resolve, reject);
            
            const container = document.getElementById('modal-container');
            container.appendChild(modal);
            
            // Adicionar à pilha de modais
            this.modalStack.push(modal);
            
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
                setTimeout(() => config.onShow(), 100);
            }

            // Gestão de foco para acessibilidade
            this.manageFocus(modal);
        });
    }

    /**
     * Gerencia foco para acessibilidade
     * @private
     */
    manageFocus(modal) {
        // Salvar elemento focado antes
        const previousFocus = document.activeElement;
        
        // Focar no primeiro botão primário ou primeiro botão
        const primaryButton = modal.querySelector('.modal-button.btn-primary');
        const firstButton = modal.querySelector('.modal-button');
        const focusTarget = primaryButton || firstButton;
        
        if (focusTarget) {
            setTimeout(() => focusTarget.focus(), 150);
        }
        
        // Restaurar foco ao fechar
        modal.addEventListener('modal-closed', () => {
            if (previousFocus && previousFocus !== document.body) {
                previousFocus.focus();
            }
        }, { once: true });
        
        // Trap focus dentro do modal
        this.trapFocus(modal);
    }

    /**
     * Mantém o foco dentro do modal (trap focus)
     * @private
     */
    trapFocus(modal) {
        const focusableElements = modal.querySelectorAll(
            'button, [href], input, select, textarea, [tabindex]:not([tabindex="-1"])'
        );
        const firstElement = focusableElements[0];
        const lastElement = focusableElements[focusableElements.length - 1];

        const handleTabKey = (e) => {
            if (e.key !== 'Tab') return;

            if (e.shiftKey) {
                if (document.activeElement === firstElement) {
                    e.preventDefault();
                    lastElement.focus();
                }
            } else {
                if (document.activeElement === lastElement) {
                    e.preventDefault();
                    firstElement.focus();
                }
            }
        };

        modal.addEventListener('keydown', handleTabKey);
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
     * @private
     */
    attachEventListeners(modal, config, resolve, reject) {
        // Botão de fechar
        const closeBtn = modal.querySelector('.modal-close');
        if (closeBtn) {
            closeBtn.addEventListener('click', () => {
                if (config.onCancel) {
                    config.onCancel();
                }
                if (config.onHide) {
                    config.onHide();
                }
                this.close({ action: 'close', value: null });
                resolve({ action: 'close', value: null });
            });
        }

        // Backdrop click
        if (config.backdrop) {
            modal.addEventListener('click', (e) => {
                if (e.target === modal) {
                    if (config.onCancel) {
                        config.onCancel();
                    }
                    if (config.onHide) {
                        config.onHide();
                    }
                    this.close({ action: 'backdrop', value: null });
                    resolve({ action: 'backdrop', value: null });
                }
            });
        }

        // Botões de ação
        const buttons = modal.querySelectorAll('.modal-button');
        buttons.forEach(button => {
            button.addEventListener('click', () => {
                const action = button.dataset.action;
                
                // Executar callbacks apropriados
                if (action === 'confirm' && config.onConfirm) {
                    const shouldClose = config.onConfirm();
                    if (shouldClose === false) return; // Permite prevenir fechamento
                } else if (action === 'cancel' && config.onCancel) {
                    config.onCancel();
                }
                
                if (config.onHide) {
                    config.onHide();
                }
                
                const result = {
                    action: action,
                    value: action === 'confirm' ? true : action === 'cancel' ? false : action
                };
                
                this.close(result);
                resolve(result);
            });
        });
    }

    /**
     * Fechar modal ativo
     * @param {Object} result - Resultado a ser passado no resolve
     */
    close(result = null) {
        if (!this.activeModal) return;

        // Disparar evento customizado
        const event = new CustomEvent('modal-closed', { detail: result });
        this.activeModal.dispatchEvent(event);

        // Remover da pilha
        const index = this.modalStack.indexOf(this.activeModal);
        if (index > -1) {
            this.modalStack.splice(index, 1);
        }

        // Animação de saída
        this.activeModal.classList.remove('show');
        this.activeModal.classList.add('hide');
        
        const modalToRemove = this.activeModal;
        
        setTimeout(() => {
            if (modalToRemove && modalToRemove.parentNode) {
                modalToRemove.parentNode.removeChild(modalToRemove);
            }
            
            // Se há modais na pilha, ativar o anterior
            if (this.modalStack.length > 0) {
                this.activeModal = this.modalStack[this.modalStack.length - 1];
            } else {
                this.activeModal = null;
            }
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
        window.Modal = new ModernModal();
    });
} else {
    window.Modal = new ModernModal();
}

// Exportar para uso em módulos
if (typeof module !== 'undefined' && module.exports) {
    module.exports = ModernModal;
}
