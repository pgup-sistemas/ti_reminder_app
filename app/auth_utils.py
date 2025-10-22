from functools import wraps

from flask import redirect, session, url_for
from app.utils import flash_error


def login_required(f):
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if "user_id" not in session:
            return redirect(url_for("auth.login", need_login=True))
        # Bloqueia usuários inativos
        from .models import User

        user = User.query.get(session["user_id"])
        if user and not user.ativo:
            session.clear()
            flash_error("Seu acesso foi desativado pelo administrador.")
            return redirect(url_for("auth.login"))
        return f(*args, **kwargs)

    return decorated_function


def admin_required(view_func):
    @wraps(view_func)
    def wrapped_view(*args, **kwargs):
        if "user_id" not in session or not session.get("is_admin", False):
            flash_error("Acesso restrito ao administrador.")
            return redirect(url_for("main.dashboard"))
        return view_func(*args, **kwargs)

    return wrapped_view
