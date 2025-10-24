/**
 * Password Validator - Frontend
 * Valida senhas em tempo real usando API do backend
 */

class PasswordValidatorUI {
    constructor(passwordInputId, options = {}) {
        this.passwordInput = document.getElementById(passwordInputId);
        if (!this.passwordInput) {
            console.error(`Input com ID '${passwordInputId}' não encontrado`);
            return;
        }
        
        this.options = {
            showStrength: options.showStrength !== false,
            showRequirements: options.showRequirements !== false,
            showErrors: options.showErrors !== false,
            containerId: options.containerId || null,
            debounceMs: options.debounceMs || 300,
            ...options
        };
        
        this.debounceTimer = null;
        this.init();
    }
    
    init() {
        // Criar elementos visuais
        this.createUI();
        
        // Adicionar event listeners
        this.passwordInput.addEventListener('input', () => {
            this.handleInput();
        });
        
        this.passwordInput.addEventListener('focus', () => {
            this.showFeedback();
        });
        
        // Carregar requisitos inicialmente
        this.loadRequirements();
    }
    
    createUI() {
        const container = this.options.containerId 
            ? document.getElementById(this.options.containerId)
            : this.passwordInput.parentElement;
        
        // Container principal
        this.feedbackContainer = document.createElement('div');
        this.feedbackContainer.className = 'password-feedback mt-2';
        this.feedbackContainer.style.display = 'none';
        
        // Medidor de força
        if (this.options.showStrength) {
            this.strengthContainer = document.createElement('div');
            this.strengthContainer.className = 'password-strength mb-2';
            this.strengthContainer.innerHTML = `
                <div class="d-flex justify-content-between align-items-center mb-1">
                    <small class="text-muted">Força da senha:</small>
                    <small class="strength-text font-weight-bold"></small>
                </div>
                <div class="progress" style="height: 8px;">
                    <div class="progress-bar strength-bar" role="progressbar" style="width: 0%"></div>
                </div>
            `;
            this.feedbackContainer.appendChild(this.strengthContainer);
        }
        
        // Lista de requisitos
        if (this.options.showRequirements) {
            this.requirementsContainer = document.createElement('div');
            this.requirementsContainer.className = 'password-requirements mt-2';
            this.requirementsContainer.innerHTML = `
                <small class="text-muted d-block mb-1">Requisitos:</small>
                <ul class="list-unstyled mb-0 requirements-list" style="font-size: 0.875rem;">
                </ul>
            `;
            this.feedbackContainer.appendChild(this.requirementsContainer);
        }
        
        // Lista de erros
        if (this.options.showErrors) {
            this.errorsContainer = document.createElement('div');
            this.errorsContainer.className = 'password-errors mt-2';
            this.errorsContainer.innerHTML = `
                <div class="alert alert-danger py-2 mb-0 errors-list" style="display: none; font-size: 0.875rem;">
                </div>
            `;
            this.feedbackContainer.appendChild(this.errorsContainer);
        }
        
        container.appendChild(this.feedbackContainer);
    }
    
    handleInput() {
        clearTimeout(this.debounceTimer);
        this.debounceTimer = setTimeout(() => {
            this.validatePassword();
        }, this.options.debounceMs);
    }
    
    async validatePassword() {
        const password = this.passwordInput.value;
        
        if (!password) {
            this.hideFeedback();
            return;
        }
        
        try {
            const response = await fetch('/configuracoes/api/validate-password', {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                },
                body: JSON.stringify({ password: password })
            });
            
            const data = await response.json();
            this.updateUI(data);
        } catch (error) {
            console.error('Erro ao validar senha:', error);
        }
    }
    
    async loadRequirements() {
        try {
            const response = await fetch('/configuracoes/api/password-requirements');
            const data = await response.json();
            this.updateRequirements(data.requirements);
        } catch (error) {
            console.error('Erro ao carregar requisitos:', error);
        }
    }
    
    updateUI(data) {
        this.showFeedback();
        
        // Atualizar força da senha
        if (this.options.showStrength && this.strengthContainer) {
            const strengthBar = this.strengthContainer.querySelector('.strength-bar');
            const strengthText = this.strengthContainer.querySelector('.strength-text');
            
            strengthBar.style.width = data.strength + '%';
            strengthBar.className = `progress-bar strength-bar bg-${data.strength_color}`;
            strengthText.textContent = data.strength_text;
            strengthText.className = `strength-text font-weight-bold text-${data.strength_color}`;
        }
        
        // Atualizar erros
        if (this.options.showErrors && this.errorsContainer) {
            const errorsList = this.errorsContainer.querySelector('.errors-list');
            if (data.errors && data.errors.length > 0) {
                errorsList.innerHTML = data.errors.map(err => 
                    `<div><i class="fas fa-times-circle"></i> ${err}</div>`
                ).join('');
                errorsList.style.display = 'block';
            } else {
                errorsList.style.display = 'none';
            }
        }
        
        // Adicionar classe de validação ao input
        if (data.valid) {
            this.passwordInput.classList.remove('is-invalid');
            this.passwordInput.classList.add('is-valid');
        } else {
            this.passwordInput.classList.remove('is-valid');
            this.passwordInput.classList.add('is-invalid');
        }
    }
    
    updateRequirements(requirements) {
        if (!this.options.showRequirements || !this.requirementsContainer) return;
        
        const requirementsList = this.requirementsContainer.querySelector('.requirements-list');
        const items = [];
        
        if (requirements.min_length) {
            items.push(`Pelo menos ${requirements.min_length} caracteres`);
        }
        if (requirements.require_uppercase) {
            items.push('Letras maiúsculas (A-Z)');
        }
        if (requirements.require_lowercase) {
            items.push('Letras minúsculas (a-z)');
        }
        if (requirements.require_numbers) {
            items.push('Números (0-9)');
        }
        if (requirements.require_special) {
            items.push('Caracteres especiais (!@#$%^&* etc)');
        }
        
        requirementsList.innerHTML = items.map(item => 
            `<li><i class="fas fa-check-circle text-success"></i> ${item}</li>`
        ).join('');
    }
    
    showFeedback() {
        this.feedbackContainer.style.display = 'block';
    }
    
    hideFeedback() {
        this.feedbackContainer.style.display = 'none';
        this.passwordInput.classList.remove('is-valid', 'is-invalid');
    }
}

// Exportar para uso global
window.PasswordValidatorUI = PasswordValidatorUI;
