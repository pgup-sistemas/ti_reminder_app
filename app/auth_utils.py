"""Decoradores de autenticação e autorização."""
from functools import wraps

from flask import redirect, url_for, request
from flask_login import current_user
from app.utils import flash_error


def login_required(f):
    """
    Decorador para rotas que requerem autenticação.
    Usa Flask-Login para verificar se o usuário está autenticado.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask import session, current_app
        
        if not current_user.is_authenticated:
            # Mostrar mensagem apenas se não for acesso direto à página inicial
            if request.endpoint != 'main.index' or request.referrer:
                flash_error("Por favor, faça login para acessar esta página.")
            
            return redirect(url_for("auth.login", next=request.url))
        
        # Verificar se o usuário está ativo
        if not current_user.ativo:
            flash_error("Sua conta foi desativada pelo administrador.")
            from flask_login import logout_user
            logout_user()
            session.clear()
            return redirect(url_for("auth.login"))
        
        return f(*args, **kwargs)
    
    return decorated_function


def admin_required(f):
    """
    Decorador para rotas que requerem permissões de administrador.
    Verifica se o usuário está autenticado E é administrador.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash_error("Por favor, faça login para acessar esta página.")
            return redirect(url_for("auth.login", next=request.url))
        
        if not current_user.is_admin:
            flash_error("Acesso restrito a administradores.")
            return redirect(url_for("main.index"))
        
        return f(*args, **kwargs)
    
    return decorated_function


def ti_required(f):
    """
    Decorador para rotas que requerem permissões de TI.
    Verifica se o usuário está autenticado E é da equipe de TI ou administrador.
    """
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if not current_user.is_authenticated:
            flash_error("Por favor, faça login para acessar esta página.")
            return redirect(url_for("auth.login", next=request.url))
        
        if not (current_user.is_ti or current_user.is_admin):
            flash_error("Acesso restrito à equipe de TI.")
            return redirect(url_for("main.index"))
        
        return f(*args, **kwargs)
    
    return decorated_function
