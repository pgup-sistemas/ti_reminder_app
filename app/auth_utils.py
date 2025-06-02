from functools import wraps
from flask import session, redirect, url_for, flash

def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if 'user_id' not in session:
            return redirect(url_for('auth.login', need_login=True))
        # Bloqueia usuários inativos
        from .models import User
        user = User.query.get(session['user_id'])
        if user and not user.ativo:
            session.clear()
            flash('Seu acesso foi desativado pelo administrador.', 'danger')
            return redirect(url_for('auth.login'))
        return f(*args, **kwargs)
    return decorated_function

def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if 'user_id' not in session or not session.get('is_admin', False):
            flash('Acesso restrito ao administrador.', 'danger')
            return redirect(url_for('main.dashboard'))
        return view_func(*args, **kwargs)
    return wrapped_view
