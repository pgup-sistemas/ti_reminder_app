/**
 * Modal Actions - TI OSN System
 * Ações comuns padronizadas usando modais modernos
 * Versão 2.0 - 2025
 * 
 * Este arquivo contém funções prontas para ações comuns do sistema.
 * Substitui completamente os confirms/alerts nativos.
 */

// ============================================
// AÇÕES COMUNS DO SISTEMA
// ============================================

/**
 * Ações de Limpeza de Dados
 */
window.SystemActions = {
    
    /**
     * Limpar cache do sistema
     */
    async clearCache() {
        const confirmed = await confirmClearData(
            'Cache do Sistema',
            'Cache de queries, templates e sessões'
        );
        
        if (confirmed) {
            showProgress('Limpando Cache', 'Removendo dados temporários...', 3);
            return true;
        }
        return false;
    },
    
    /**
     * Limpar logs
     */
    async clearLogs(logType = 'sistema') {
        const confirmed = await confirmClearData(
            `Logs de ${logType}`,
            'Os logs serão removidos permanentemente'
        );
        
        if (confirmed) {
            showLoading('Limpando logs...');
            return true;
        }
        return false;
    },
    
    /**
     * Resetar configurações
     */
    async resetSettings() {
        const confirmed = await confirmDangerousAction(
            'Configurações do Sistema',
            `Esta ação irá:
            <ul class="mb-0">
                <li>Restaurar valores padrão</li>
                <li>Remover personalizações</li>
                <li>Limpar preferências salvas</li>
            </ul>`
        );
        
        if (confirmed) {
            showLoading('Restaurando configurações padrão...');
            return true;
        }
        return false;
    },
    
    /**
     * Executar otimização
     */
    async runOptimization(optimizationType, estimatedTime = 5) {
        const confirmed = await confirmAction(
            'Executar Otimização',
            `Esta operação pode levar até ${estimatedTime} minutos. Continuar?`,
            'Executar',
            'warning'
        );
        
        if (confirmed) {
            showProgress(
                'Otimizando Sistema',
                `Executando ${optimizationType}...`,
                estimatedTime * 60
            );
            return true;
        }
        return false;
    },
    
    /**
     * Reindexar banco de dados
     */
    async reindexDatabase() {
        const confirmed = await confirmDangerousAction(
            'Reindexação do Banco de Dados',
            `⚠️ <strong>Operação Pesada</strong>
            <ul class="mb-0 mt-2">
                <li>Pode bloquear writes temporariamente</li>
                <li>Tempo estimado: 10-30 minutos</li>
                <li>Recomendado apenas em horário de manutenção</li>
            </ul>`
        );
        
        if (confirmed) {
            showProgress(
                'Reindexando Banco',
                'Esta operação pode levar vários minutos...',
                900 // 15 minutos
            );
            return true;
        }
        return false;
    },
    
    /**
     * Backup do sistema
     */
    async createBackup() {
        const confirmed = await confirmAction(
            'Criar Backup',
            'Deseja criar um backup completo do sistema?',
            'Criar Backup',
            'info'
        );
        
        if (confirmed) {
            showProgress(
                'Criando Backup',
                'Copiando dados do sistema...',
                60
            );
            return true;
        }
        return false;
    },
    
    /**
     * Restaurar backup
     */
    async restoreBackup(backupName) {
        const confirmed = await confirmDangerousAction(
            `Restaurar Backup: ${backupName}`,
            `⚠️ <strong>ATENÇÃO!</strong>
            <ul class="mb-0 mt-2">
                <li>Todos os dados atuais serão <strong>substituídos</strong></li>
                <li>Esta operação <strong>NÃO PODE</strong> ser desfeita</li>
                <li>Faça um backup antes de continuar</li>
            </ul>`
        );
        
        if (confirmed) {
            showProgress(
                'Restaurando Backup',
                'Substituindo dados do sistema...',
                120
            );
            return true;
        }
        return false;
    },
    
    /**
     * Enviar email de teste
     */
    async sendTestEmail(templateName, recipient) {
        const confirmed = await window.Modal.show({
            type: 'confirm',
            title: 'Enviar Email de Teste',
            message: `
                <p>Enviar email de teste usando o template:</p>
                <div class="alert alert-info">
                    <strong>${templateName}</strong>
                </div>
                <p class="mb-0">
                    <small class="text-muted">
                        <i class="fas fa-envelope me-2"></i>
                        Destinatário: <strong>${recipient}</strong>
                    </small>
                </p>
            `,
            html: true,
            buttons: [
                { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
                { text: 'Enviar', action: 'confirm', class: 'btn-primary', icon: 'fas fa-paper-plane' }
            ]
        });
        
        if (confirmed.action === 'confirm') {
            showLoading('Enviando email de teste...');
            return true;
        }
        return false;
    },
    
    /**
     * Testar alertas
     */
    async testAlerts() {
        const confirmed = await confirmAction(
            'Testar Sistema de Alertas',
            `Enviar um alerta de teste para todos os canais configurados?
            <ul class="mt-2 mb-0">
                <li>Email</li>
                <li>Notificações push</li>
                <li>Slack/Teams (se configurado)</li>
            </ul>`,
            'Enviar Teste',
            'info'
        );
        
        if (confirmed) {
            showLoading('Enviando alertas de teste...');
            return true;
        }
        return false;
    },
    
    /**
     * Habilitar todos os alertas
     */
    async enableAllAlerts() {
        const confirmed = await confirmAction(
            'Habilitar Todos os Alertas',
            'Isso ativará todas as regras de monitoramento do sistema.',
            'Habilitar Todos',
            'warning'
        );
        
        if (confirmed) {
            showSuccess('Todos os alertas foram habilitados!');
            return true;
        }
        return false;
    },
    
    /**
     * Reconhecer todos os alertas
     */
    async acknowledgeAllAlerts() {
        const confirmed = await confirmAction(
            'Reconhecer Todos os Alertas',
            'Os alertas permanecerão visíveis mas serão marcados como reconhecidos.',
            'Reconhecer Todos',
            'info'
        );
        
        if (confirmed) {
            showSuccess('Todos os alertas foram reconhecidos!');
            return true;
        }
        return false;
    }
};

/**
 * Ações de RFID
 */
window.RFIDActions = {
    
    /**
     * Remover leitor RFID
     */
    async removeReader(readerId) {
        const confirmed = await confirmDangerousAction(
            `Leitor RFID ${readerId}`,
            `Esta ação irá:
            <ul class="mb-0">
                <li>Desconectar o dispositivo</li>
                <li>Remover todas as associações</li>
                <li>Parar o monitoramento da zona</li>
            </ul>`
        );
        
        if (confirmed) {
            showLoading('Removendo leitor...');
            return true;
        }
        return false;
    },
    
    /**
     * Deletar zona RFID
     */
    async deleteZone(zoneName) {
        const confirmed = await confirmDelete(zoneName, 'zona RFID');
        
        if (confirmed) {
            showSuccess('Zona excluída! Todos os leitores foram desassociados.');
            return true;
        }
        return false;
    },
    
    /**
     * Desativar tag RFID
     */
    async deactivateTag(tagId) {
        const confirmed = await confirmAction(
            'Desativar Tag RFID',
            `A tag ${tagId} não será mais rastreada pelo sistema.`,
            'Desativar',
            'warning'
        );
        
        if (confirmed) {
            showSuccess('Tag desativada com sucesso!');
            return true;
        }
        return false;
    }
};

/**
 * Ações de Notificações
 */
window.NotificationActions = {
    
    /**
     * Reenviar notificação
     */
    async retryNotification(notificationId) {
        const confirmed = await confirmAction(
            'Reenviar Notificação',
            'Será feita uma nova tentativa de envio.',
            'Reenviar',
            'info'
        );
        
        if (confirmed) {
            showLoading('Reenviando notificação...');
            return true;
        }
        return false;
    },
    
    /**
     * Enviar notificação agora
     */
    async sendNow(notificationId) {
        const confirmed = await confirmAction(
            'Enviar Agora',
            'A notificação será processada imediatamente.',
            'Enviar',
            'warning'
        );
        
        if (confirmed) {
            showLoading('Enviando notificação...');
            return true;
        }
        return false;
    },
    
    /**
     * Cancelar notificação agendada
     */
    async cancelScheduled(notificationId) {
        const confirmed = await confirmAction(
            'Cancelar Notificação',
            'A notificação agendada será removida da fila.',
            'Cancelar Envio',
            'warning'
        );
        
        if (confirmed) {
            showSuccess('Notificação cancelada com sucesso!');
            return true;
        }
        return false;
    }
};

/**
 * Ações em Lote (Bulk Actions)
 */
window.BulkActions = {
    
    /**
     * Deletar múltiplos itens
     */
    async deleteMultiple(selectedCount, itemType = 'item') {
        if (selectedCount === 0) {
            await showWarning('Selecione pelo menos um item para excluir.');
            return false;
        }
        
        const confirmed = await window.Modal.show({
            type: 'error',
            title: 'Excluir Múltiplos Itens',
            message: `
                <div class="alert alert-danger">
                    <h6 class="alert-heading">
                        <i class="fas fa-exclamation-triangle me-2"></i>
                        Atenção!
                    </h6>
                    <p class="mb-0">
                        Você está prestes a excluir <strong>${selectedCount}</strong> ${itemType}(s).
                    </p>
                </div>
                <p class="text-danger mb-0">
                    <small>Esta ação não pode ser desfeita!</small>
                </p>
            `,
            html: true,
            buttons: [
                { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
                { 
                    text: `Excluir ${selectedCount} ${itemType}(s)`, 
                    action: 'confirm', 
                    class: 'btn-danger',
                    icon: 'fas fa-trash-alt'
                }
            ]
        });
        
        if (confirmed.action === 'confirm') {
            showProgress(
                'Excluindo Itens',
                `Excluindo ${selectedCount} ${itemType}(s)...`,
                selectedCount * 2
            );
            return true;
        }
        return false;
    },
    
    /**
     * Duplicar templates
     */
    async duplicateTemplates(templateNames) {
        const confirmed = await confirmAction(
            'Duplicar Templates',
            `Duplicar ${templateNames.length} template(s): ${templateNames.join(', ')}?`,
            'Duplicar',
            'info'
        );
        
        if (confirmed) {
            showSuccess('Templates duplicados com sucesso!');
            return true;
        }
        return false;
    }
};

/**
 * Utilitários
 */
window.ModalUtils = {
    
    /**
     * Confirmar com senha
     */
    async confirmWithPassword(action) {
        const password = await promptInput(
            'Digite sua senha para confirmar:',
            '',
            'Senha',
            'password'
        );
        
        if (password) {
            showLoading('Verificando senha...');
            return password;
        }
        return null;
    },
    
    /**
     * Escolher formato de exportação
     */
    async chooseExportFormat() {
        return await chooseOption(
            'Exportar Dados',
            'Escolha o formato de exportação:',
            [
                { value: 'pdf', label: 'PDF', description: 'Documento para impressão' },
                { value: 'xlsx', label: 'Excel', description: 'Planilha editável' },
                { value: 'csv', label: 'CSV', description: 'Valores separados por vírgula' },
                { value: 'json', label: 'JSON', description: 'Formato de dados estruturados' }
            ]
        );
    },
    
    /**
     * Confirmar com "não mostrar novamente"
     */
    async confirmWithDontShowAgain(storageKey, message, title = 'Confirmação') {
        // Verificar se usuário marcou "não mostrar novamente"
        if (localStorage.getItem(storageKey) === 'true') {
            return true;
        }
        
        const result = await confirmWithCheckbox(
            title,
            message,
            'Não mostrar novamente'
        );
        
        if (result.checkboxValue) {
            localStorage.setItem(storageKey, 'true');
        }
        
        return result.confirmed;
    }
};

// Log de inicialização
console.log('✅ Modal Actions loaded successfully');
