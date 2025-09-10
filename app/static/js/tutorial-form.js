/**
 * Script para melhorar a acessibilidade e usabilidade do formulário de tutoriais
 * Inclui validação, feedback visual e melhorias de acessibilidade
 */

document.addEventListener('DOMContentLoaded', function() {
    const form = document.querySelector('.needs-validation');
    
    if (!form) return;
    
    // Configuração inicial
    initFormValidation(form);
    initFileUpload();
    initTooltips();
    addKeyboardNavigation();
});

/**
 * Inicializa a validação do formulário
 */
function initFormValidation(form) {
    // Validação em tempo real
    const inputs = form.querySelectorAll('input, textarea, select');
    
    inputs.forEach(input => {
        // Validação ao sair do campo
        input.addEventListener('blur', function() {
            validateField(this);
        });
        
        // Feedback imediato durante a digitação (após o usuário começar a digitar)
        let hasInteracted = false;
        input.addEventListener('input', function() {
            if (!hasInteracted) return;
            validateField(this);
        });
        
        // Marcar como interagido após o primeiro input
        input.addEventListener('keydown', function() {
            hasInteracted = true;
        });
    });
    
    // Validação no envio do formulário
    form.addEventListener('submit', function(event) {
        if (!form.checkValidity()) {
            event.preventDefault();
            event.stopPropagation();
            
            // Rolar até o primeiro campo inválido
            const firstInvalid = form.querySelector(':invalid');
            if (firstInvalid) {
                firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                firstInvalid.focus();
                firstInvalid.classList.add('is-invalid');
                
                // Adicionar mensagem de erro para leitores de tela
                const errorMessage = firstInvalid.getAttribute('data-error-message') || 'Campo obrigatório';
                announceToScreenReader(errorMessage);
            }
        }
        
        form.classList.add('was-validated');
    });
}

/**
 * Valida um campo individual
 */
function validateField(field) {
    const isValid = field.checkValidity();
    const errorContainer = field.nextElementSibling;
    
    if (isValid) {
        field.classList.remove('is-invalid');
        field.classList.add('is-valid');
        
        // Remover mensagem de erro se existir
        if (errorContainer && errorContainer.classList.contains('invalid-feedback')) {
            errorContainer.remove();
        }
    } else {
        field.classList.remove('is-valid');
        field.classList.add('is-invalid');
        
        // Adicionar mensagem de erro se não existir
        if (!errorContainer || !errorContainer.classList.contains('invalid-feedback')) {
            const errorDiv = document.createElement('div');
            errorDiv.className = 'invalid-feedback d-block';
            errorDiv.role = 'alert';
            errorDiv.innerHTML = `<i class="fas fa-exclamation-circle me-1"></i>${getErrorMessage(field)}`;
            field.parentNode.insertBefore(errorDiv, field.nextSibling);
        }
    }
}

/**
 * Retorna mensagem de erro apropriada para o campo
 */
function getErrorMessage(field) {
    if (field.validity.valueMissing) {
        return 'Este campo é obrigatório.';
    } else if (field.validity.typeMismatch) {
        if (field.type === 'email') {
            return 'Por favor, insira um endereço de e-mail válido.';
        } else if (field.type === 'url') {
            return 'Por favor, insira uma URL válida.';
        }
    } else if (field.validity.tooShort) {
        return `O campo deve ter no mínimo ${field.minLength} caracteres.`;
    } else if (field.validity.tooLong) {
        return `O campo deve ter no máximo ${field.maxLength} caracteres.`;
    } else if (field.validity.patternMismatch) {
        return field.getAttribute('data-pattern-error') || 'Formato inválido.';
    }
    
    return 'Valor inválido.';
}

/**
 * Inicializa o componente de upload de arquivos
 */
function initFileUpload() {
    const fileInputs = document.querySelectorAll('input[type="file"]');
    
    fileInputs.forEach(input => {
        const wrapper = input.closest('.file-upload-wrapper');
        if (!wrapper) return;
        
        // Criar elementos de interface
        const label = document.createElement('span');
        label.className = 'file-upload-label';
        label.textContent = input.getAttribute('data-text') || 'Nenhum arquivo selecionado';
        
        const button = document.createElement('button');
        button.type = 'button';
        button.className = 'btn btn-sm btn-outline-secondary';
        button.textContent = input.getAttribute('data-browse') || 'Procurar';
        button.addEventListener('click', () => input.click());
        
        // Atualizar interface quando arquivos forem selecionados
        input.addEventListener('change', function() {
            const files = Array.from(this.files).map(f => f.name);
            
            if (files.length === 0) {
                label.textContent = input.getAttribute('data-text') || 'Nenhum arquivo selecionado';
            } else if (files.length === 1) {
                label.textContent = files[0];
            } else {
                label.textContent = `${files.length} arquivos selecionados`;
            }
            
            // Anunciar para leitores de tela
            announceToScreenReader(`${files.length} arquivo(s) selecionado(s)`);
        });
        
        // Limpar wrapper e adicionar novos elementos
        wrapper.innerHTML = '';
        wrapper.appendChild(label);
        wrapper.appendChild(button);
        wrapper.appendChild(input);
        
        // Tornar o input acessível via teclado
        input.style.position = 'absolute';
        input.style.width = '1px';
        input.style.height = '1px';
        input.style.padding = '0';
        input.style.margin = '-1px';
        input.style.overflow = 'hidden';
        input.style.clip = 'rect(0, 0, 0, 0)';
        input.style.border = '0';
    });
}

/**
 * Inicializa tooltips para melhorar a acessibilidade
 */
function initTooltips() {
    const tooltipTriggerList = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
    tooltipTriggerList.map(function (tooltipTriggerEl) {
        return new bootstrap.Tooltip(tooltipTriggerEl, {
            trigger: 'hover focus',
            container: 'body',
            boundary: 'window',
            delay: { show: 500, hide: 100 }
        });
    });
}

/**
 * Adiciona navegação por teclado aprimorada
 */
function addKeyboardNavigation() {
    // Adicionar navegação por teclado entre campos de formulário
    document.addEventListener('keydown', function(e) {
        if (e.key === 'Enter' && e.target.tagName !== 'TEXTAREA') {
            e.preventDefault();
            
            const form = e.target.closest('form');
            if (!form) return;
            
            const formElements = Array.from(form.elements);
            const currentIndex = formElements.indexOf(e.target);
            
            if (currentIndex < formElements.length - 1) {
                formElements[currentIndex + 1].focus();
            }
        }
    });
    
    // Adicionar atalhos de teclado
    document.addEventListener('keydown', function(e) {
        // Ctrl+Enter para submeter o formulário
        if ((e.ctrlKey || e.metaKey) && e.key === 'Enter') {
            const form = document.activeElement.closest('form');
            if (form) {
                form.dispatchEvent(new Event('submit'));
            }
        }
        
        // Esc para limpar o campo atual
        if (e.key === 'Escape') {
            const activeElement = document.activeElement;
            if (activeElement.tagName === 'INPUT' || activeElement.tagName === 'TEXTAREA') {
                activeElement.value = '';
                activeElement.dispatchEvent(new Event('input'));
            }
        }
    });
}

/**
 * Anuncia mensagens para leitores de tela
 */
function announceToScreenReader(message, priority = 'polite') {
    const liveRegion = document.getElementById('a11y-live-region') || createLiveRegion();
    liveRegion.setAttribute('aria-live', priority);
    
    // Limpar mensagens anteriores
    liveRegion.textContent = '';
    
    // Adicionar nova mensagem
    setTimeout(() => {
        liveRegion.textContent = message;
    }, 100);
}

/**
 * Cria uma região de anúncio para leitores de tela
 */
function createLiveRegion() {
    const liveRegion = document.createElement('div');
    liveRegion.id = 'a11y-live-region';
    liveRegion.className = 'visually-hidden';
    liveRegion.setAttribute('aria-live', 'polite');
    liveRegion.setAttribute('aria-atomic', 'true');
    document.body.appendChild(liveRegion);
    return liveRegion;
}

// Exportar funções para uso em outros arquivos
window.tutorialForm = {
    validateField,
    announceToScreenReader
};
