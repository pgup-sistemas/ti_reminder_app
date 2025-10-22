/**
 * Modal Helpers - TI OSN System
 * Funções auxiliares para facilitar o uso de modais
 * Versão 2.0 - 2025
 */

/**
 * Helpers globais para uso fácil de modais
 * Depende de: modals.js (classe ModernModal)
 */

// Verificar se Modal está disponível
if (typeof window.Modal === 'undefined') {
    console.warn('Modal system not loaded. Please include modals.js first.');
}

/**
 * Confirmar exclusão de item
 * @param {string} itemName - Nome do item a ser excluído
 * @param {string} itemType - Tipo do item (usuário, lembrete, etc)
 * @returns {Promise<boolean>} True se confirmado
 */
async function confirmDelete(itemName, itemType = 'item') {
    const result = await window.Modal.show({
        type: 'error',
        title: `Excluir ${itemType}?`,
        message: `
            <p>Tem certeza que deseja excluir <strong>"${itemName}"</strong>?</p>
            <p class="text-danger mb-0"><i class="fas fa-exclamation-triangle me-2"></i>Esta ação não pode ser desfeita!</p>
        `,
        html: true,
        buttons: [
            { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
            { text: 'Excluir', action: 'confirm', class: 'btn-danger', icon: 'fas fa-trash' }
        ]
    });
    
    return result.action === 'confirm';
}

/**
 * Confirmar ação genérica
 * @param {string} title - Título do modal
 * @param {string} message - Mensagem de confirmação
 * @param {string} confirmText - Texto do botão de confirmação
 * @param {string} type - Tipo do modal (warning, confirm, etc)
 * @returns {Promise<boolean>} True se confirmado
 */
async function confirmAction(title, message, confirmText = 'Confirmar', type = 'confirm') {
    const result = await window.Modal.show({
        type: type,
        title: title,
        message: message,
        html: true,
        buttons: [
            { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
            { text: confirmText, action: 'confirm', class: type === 'warning' ? 'btn-warning' : 'btn-primary' }
        ]
    });
    
    return result.action === 'confirm';
}

/**
 * Mostrar mensagem de sucesso
 * @param {string} message - Mensagem de sucesso
 * @param {string} title - Título (opcional)
 */
async function showSuccess(message, title = 'Sucesso!') {
    return await window.Modal.show({
        type: 'success',
        title: title,
        message: message,
        html: true,
        buttons: [
            { text: 'OK', action: 'ok', class: 'btn-success' }
        ]
    });
}

/**
 * Mostrar mensagem de erro
 * @param {string} message - Mensagem de erro
 * @param {string} title - Título (opcional)
 */
async function showError(message, title = 'Erro') {
    return await window.Modal.show({
        type: 'error',
        title: title,
        message: message,
        html: true,
        buttons: [
            { text: 'OK', action: 'ok', class: 'btn-danger' }
        ]
    });
}

/**
 * Mostrar aviso
 * @param {string} message - Mensagem de aviso
 * @param {string} title - Título (opcional)
 */
async function showWarning(message, title = 'Atenção') {
    return await window.Modal.show({
        type: 'warning',
        title: title,
        message: message,
        html: true,
        buttons: [
            { text: 'Entendi', action: 'ok', class: 'btn-warning' }
        ]
    });
}

/**
 * Mostrar informação
 * @param {string} message - Mensagem informativa
 * @param {string} title - Título (opcional)
 */
async function showInfo(message, title = 'Informação') {
    return await window.Modal.show({
        type: 'info',
        title: title,
        message: message,
        html: true,
        buttons: [
            { text: 'OK', action: 'ok', class: 'btn-primary' }
        ]
    });
}

/**
 * Solicitar input do usuário
 * @param {string} question - Pergunta/label
 * @param {string} defaultValue - Valor padrão
 * @param {string} placeholder - Placeholder do input
 * @param {string} inputType - Tipo do input (text, email, number, etc)
 * @returns {Promise<string|null>} Valor digitado ou null se cancelado
 */
async function promptInput(question, defaultValue = '', placeholder = '', inputType = 'text') {
    const inputId = 'modal-prompt-input-' + Date.now();
    
    const result = await window.Modal.show({
        type: 'confirm',
        title: 'Entrada de Dados',
        message: `
            <div class="mb-3">
                <label for="${inputId}" class="form-label fw-semibold">${question}</label>
                <input type="${inputType}" 
                       id="${inputId}" 
                       class="form-control" 
                       value="${defaultValue}"
                       placeholder="${placeholder}"
                       autofocus>
            </div>
        `,
        html: true,
        buttons: [
            { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
            { text: 'Confirmar', action: 'confirm', class: 'btn-primary' }
        ],
        onShow: () => {
            // Focar no input após modal abrir
            setTimeout(() => {
                const input = document.getElementById(inputId);
                if (input) {
                    input.focus();
                    input.select();
                }
            }, 200);
        }
    });
    
    if (result.action === 'confirm') {
        const input = document.getElementById(inputId);
        return input ? input.value : null;
    }
    
    return null;
}

/**
 * Mostrar loading overlay
 * @param {string} message - Mensagem de loading
 * @returns {Object} Objeto modal para fechar depois
 */
function showLoading(message = 'Carregando...') {
    return window.Modal.show({
        type: 'info',
        title: 'Aguarde',
        message: `
            <div class="loading-content text-center">
                <div class="loading-spinner mx-auto mb-3"></div>
                <p class="mb-0">${message}</p>
            </div>
        `,
        html: true,
        closable: false,
        backdrop: false,
        buttons: []
    });
}

/**
 * Fechar loading
 */
function hideLoading() {
    if (window.Modal && window.Modal.activeModal) {
        window.Modal.close();
    }
}

/**
 * Confirmar operação perigosa (requer confirmação dupla)
 * @param {string} itemName - Nome do item
 * @param {string} warningMessage - Mensagem de aviso
 * @returns {Promise<boolean>} True se confirmado
 */
async function confirmDangerousAction(itemName, warningMessage) {
    const result = await window.Modal.show({
        type: 'warning',
        title: '⚠️ Ação Perigosa',
        message: `
            <div class="alert alert-danger border-danger mb-3">
                <h6 class="alert-heading mb-2"><i class="fas fa-exclamation-triangle me-2"></i>Atenção!</h6>
                <p class="mb-0">${warningMessage}</p>
            </div>
            <p class="mb-2">Você está prestes a realizar uma ação irreversível em:</p>
            <p class="fw-bold text-danger mb-3">"${itemName}"</p>
            <p class="text-muted small mb-0">Esta operação não pode ser desfeita e pode causar perda de dados.</p>
        `,
        html: true,
        size: 'medium',
        buttons: [
            { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
            { text: 'Tenho Certeza', action: 'confirm', class: 'btn-danger', icon: 'fas fa-exclamation-triangle' }
        ]
    });
    
    return result.action === 'confirm';
}

/**
 * Confirmar limpeza/reset de dados
 * @param {string} dataType - Tipo de dados a limpar
 * @param {string} details - Detalhes adicionais
 * @returns {Promise<boolean>} True se confirmado
 */
async function confirmClearData(dataType, details = '') {
    const result = await window.Modal.show({
        type: 'warning',
        title: `Limpar ${dataType}?`,
        message: `
            <p>Esta ação irá <strong>limpar permanentemente</strong> os seguintes dados:</p>
            <ul class="mb-3">
                <li>${dataType}</li>
                ${details ? `<li class="text-muted">${details}</li>` : ''}
            </ul>
            <div class="alert alert-warning border-warning mb-0">
                <small><i class="fas fa-info-circle me-2"></i>Esta operação não pode ser desfeita!</small>
            </div>
        `,
        html: true,
        buttons: [
            { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
            { text: 'Limpar Dados', action: 'confirm', class: 'btn-warning', icon: 'fas fa-broom' }
        ]
    });
    
    return result.action === 'confirm';
}

/**
 * Mostrar progresso de operação
 * @param {string} title - Título
 * @param {string} message - Mensagem
 * @param {number} estimatedSeconds - Tempo estimado em segundos
 */
async function showProgress(title, message, estimatedSeconds = 5) {
    return await window.Modal.show({
        type: 'info',
        title: title,
        message: `
            <div class="text-center">
                <div class="loading-spinner mx-auto mb-3"></div>
                <p class="mb-2">${message}</p>
                <small class="text-muted">Tempo estimado: ${estimatedSeconds} segundos</small>
            </div>
        `,
        html: true,
        closable: false,
        backdrop: false,
        buttons: []
    });
}

/**
 * Confirmar com checkbox (ex: "Não mostrar novamente")
 * @param {string} title - Título
 * @param {string} message - Mensagem
 * @param {string} checkboxLabel - Label do checkbox
 * @returns {Promise<{confirmed: boolean, checkboxValue: boolean}>}
 */
async function confirmWithCheckbox(title, message, checkboxLabel = 'Não mostrar novamente') {
    const checkboxId = 'modal-checkbox-' + Date.now();
    
    const result = await window.Modal.show({
        type: 'confirm',
        title: title,
        message: `
            <p>${message}</p>
            <div class="form-check mt-3">
                <input type="checkbox" class="form-check-input" id="${checkboxId}">
                <label class="form-check-label" for="${checkboxId}">
                    ${checkboxLabel}
                </label>
            </div>
        `,
        html: true,
        buttons: [
            { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
            { text: 'Confirmar', action: 'confirm', class: 'btn-primary' }
        ]
    });
    
    const checkbox = document.getElementById(checkboxId);
    
    return {
        confirmed: result.action === 'confirm',
        checkboxValue: checkbox ? checkbox.checked : false
    };
}

/**
 * Escolher entre múltiplas opções
 * @param {string} title - Título
 * @param {string} message - Mensagem
 * @param {Array} options - Array de opções {value, label, description}
 * @returns {Promise<string|null>} Valor selecionado ou null
 */
async function chooseOption(title, message, options) {
    const radioName = 'modal-radio-' + Date.now();
    
    const optionsHTML = options.map((opt, index) => `
        <div class="form-check mb-2">
            <input class="form-check-input" type="radio" name="${radioName}" 
                   id="${radioName}-${index}" value="${opt.value}" 
                   ${index === 0 ? 'checked' : ''}>
            <label class="form-check-label" for="${radioName}-${index}">
                <strong>${opt.label}</strong>
                ${opt.description ? `<br><small class="text-muted">${opt.description}</small>` : ''}
            </label>
        </div>
    `).join('');
    
    const result = await window.Modal.show({
        type: 'confirm',
        title: title,
        message: `
            <p class="mb-3">${message}</p>
            ${optionsHTML}
        `,
        html: true,
        buttons: [
            { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
            { text: 'Confirmar', action: 'confirm', class: 'btn-primary' }
        ]
    });
    
    if (result.action === 'confirm') {
        const selected = document.querySelector(`input[name="${radioName}"]:checked`);
        return selected ? selected.value : null;
    }
    
    return null;
}

/**
 * Substituir window.confirm nativo (opcional - descomentar para usar)
 * CUIDADO: Isso irá substituir TODOS os confirms do sistema
 */
/*
window.confirm = async function(message) {
    const result = await confirmAction('Confirmação', message);
    return result;
};
*/

/**
 * Substituir window.alert nativo (opcional - descomentar para usar)
 * CUIDADO: Isso irá substituir TODOS os alerts do sistema
 */
/*
window.alert = async function(message) {
    await showInfo(message, 'Aviso');
};
*/

// Exportar funções para uso global
window.ModalHelpers = {
    confirmDelete,
    confirmAction,
    showSuccess,
    showError,
    showWarning,
    showInfo,
    promptInput,
    showLoading,
    hideLoading,
    confirmDangerousAction,
    confirmClearData,
    showProgress,
    confirmWithCheckbox,
    chooseOption
};

// Log de inicialização
console.log('✅ Modal Helpers loaded successfully');
