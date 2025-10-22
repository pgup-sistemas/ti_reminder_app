"""
Sistema de Notificações Padronizado
Helpers para uso consistente de flash messages
TI OSN System - 2025

Este módulo fornece funções padronizadas para exibir notificações
que serão automaticamente convertidas em toasts modernos pelo frontend.
"""

from flask import flash as flask_flash


def flash_success(message, title="Sucesso"):
    """
    Exibe notificação de sucesso (verde).
    
    Args:
        message (str): Mensagem a ser exibida
        title (str): Título da notificação (padrão: "Sucesso")
    
    Exemplo:
        flash_success("Usuário cadastrado com sucesso!")
        flash_success("Dados atualizados!", title="Atualização")
    """
    flask_flash(f"{title}|{message}", "success")


def flash_error(message, title="Erro"):
    """
    Exibe notificação de erro (vermelho).
    
    Args:
        message (str): Mensagem a ser exibida
        title (str): Título da notificação (padrão: "Erro")
    
    Exemplo:
        flash_error("Não foi possível salvar os dados.")
        flash_error("Falha na conexão", title="Erro de Rede")
    """
    flask_flash(f"{title}|{message}", "error")


def flash_warning(message, title="Atenção"):
    """
    Exibe notificação de aviso (amarelo/laranja).
    
    Args:
        message (str): Mensagem a ser exibida
        title (str): Título da notificação (padrão: "Atenção")
    
    Exemplo:
        flash_warning("Alguns campos estão incompletos.")
        flash_warning("Prazo próximo do vencimento!", title="Aviso")
    """
    flask_flash(f"{title}|{message}", "warning")


def flash_info(message, title="Informação"):
    """
    Exibe notificação informativa (azul).
    
    Args:
        message (str): Mensagem a ser exibida
        title (str): Título da notificação (padrão: "Informação")
    
    Exemplo:
        flash_info("Nova atualização disponível.")
        flash_info("Sistema será atualizado em breve.", title="Manutenção")
    """
    flask_flash(f"{title}|{message}", "info")


# Aliases para compatibilidade e conveniência
notify_success = flash_success
notify_error = flash_error
notify_warning = flash_warning
notify_info = flash_info


# Para uso com categorias simples (compatibilidade com código legado)
def flash_message(message, category="info", title=None):
    """
    Exibe notificação com categoria customizada.
    
    Args:
        message (str): Mensagem a ser exibida
        category (str): Tipo de notificação (success, error, warning, info)
        title (str): Título da notificação (opcional)
    
    Exemplo:
        flash_message("Operação concluída", "success")
        flash_message("Erro ao processar", "error", "Falha")
    """
    if title is None:
        title_map = {
            "success": "Sucesso",
            "error": "Erro",
            "warning": "Atenção",
            "info": "Informação"
        }
        title = title_map.get(category, "Notificação")
    
    flask_flash(f"{title}|{message}", category)


# Função auxiliar para mensagens sem título (retrocompatibilidade)
def flash_simple(message, category="info"):
    """
    Exibe notificação simples sem título.
    
    Args:
        message (str): Mensagem a ser exibida
        category (str): Tipo de notificação (success, error, warning, info)
    
    Exemplo:
        flash_simple("Dados salvos!", "success")
    """
    flask_flash(message, category)
