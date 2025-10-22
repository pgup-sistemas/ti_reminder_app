/**
 * Flash to Toast Adapter
 * Converte mensagens flash do Flask em toasts modernos
 * TI OSN System - 2025
 */

(function() {
    'use strict';
    
    // Aguardar que Feedback esteja disponível
    const initAdapter = () => {
        if (typeof window.Feedback === 'undefined') {
            // Feedback ainda não carregou, tentar novamente
            setTimeout(initAdapter, 100);
            return;
        }
        
        // Processar mensagens flash
        const flashContainer = document.getElementById('flask-messages');
        if (!flashContainer) {
            // Sem mensagens flash para processar
            return;
        }
        
        const messagesData = flashContainer.getAttribute('data-messages');
        if (!messagesData || messagesData.trim() === '[]') {
            // Sem mensagens ou array vazio
            flashContainer.remove();
            return;
        }
        
        try {
            const messages = JSON.parse(messagesData);
            
            // Processar cada mensagem com delay progressivo
            messages.forEach((msg, index) => {
                // Delay progressivo para múltiplas mensagens (evita sobreposição)
                setTimeout(() => {
                    // Separar título e mensagem (formato: "Título|Mensagem")
                    const parts = msg.message.split('|');
                    let title, message;
                    
                    if (parts.length > 1) {
                        title = parts[0].trim();
                        message = parts.slice(1).join('|').trim();
                    } else {
                        title = '';
                        message = msg.message.trim();
                    }
                    
                    // Mapear categorias Flask para tipos de toast
                    const typeMap = {
                        'success': 'success',
                        'error': 'error',
                        'danger': 'error', // Compatibilidade com padrão antigo
                        'warning': 'warning',
                        'info': 'info'
                    };
                    
                    const type = typeMap[msg.type] || 'info';
                    
                    // Configurar duração baseada no tipo
                    const durationMap = {
                        'success': 4000,
                        'error': 8000,
                        'warning': 6000,
                        'info': 5000
                    };
                    
                    const duration = durationMap[type] || 5000;
                    
                    // Exibir toast
                    window.Feedback.toast(type, title, message, {
                        duration: duration,
                        closable: true
                    });
                    
                }, index * 300); // 300ms entre cada toast
            });
            
            // Remover container original após processar
            setTimeout(() => {
                flashContainer.remove();
            }, messages.length * 300 + 100);
            
        } catch (error) {
            console.error('Erro ao processar flash messages:', error);
            
            // Fallback: exibir mensagem de erro genérica
            if (window.Feedback) {
                window.Feedback.error('Erro', 'Houve um problema ao exibir as notificações.');
            }
            
            // Remover container mesmo com erro
            flashContainer.remove();
        }
    };
    
    // Iniciar quando DOM estiver pronto
    if (document.readyState === 'loading') {
        document.addEventListener('DOMContentLoaded', initAdapter);
    } else {
        // DOM já está pronto
        initAdapter();
    }
    
    // Exportar função para uso manual se necessário
    window.FlashToToastAdapter = {
        init: initAdapter
    };
})();
