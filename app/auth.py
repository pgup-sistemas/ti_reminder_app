from flask import (Blueprint, redirect, render_template, request,
                   session, url_for)
from app.utils import flash_success, flash_error, flash_info
from flask_login import login_user, logout_user
from flask_mail import Message
from werkzeug.security import check_password_hash, generate_password_hash

from . import mail
from .forms_auth import (LoginForm, RegistrationForm, RequestPasswordResetForm,
                         ResetPasswordForm)
from .models import User, db

bp_auth = Blueprint("auth", __name__)


@bp_auth.route("/register", methods=["GET", "POST"])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Verifica se já existe um usuário com o mesmo nome de usuário ou email
        existing_user = User.query.filter(
            (User.username == form.username.data) | (User.email == form.email.data)
        ).first()

        if existing_user:
            flash_error("Nome de usuário ou email já está em uso.")
            return render_template("register.html", form=form)

        user = User(
            username=form.username.data,
            email=form.email.data,
            is_admin=False,  # Usuários comuns não são administradores
            is_ti=False,  # Nem fazem parte da equipe de TI
            ativo=True,
        )
        user.set_password(form.password.data)

        try:
            db.session.add(user)
            db.session.commit()
            flash_success("Usuário registrado com sucesso! Faça login.")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            flash_error(
                "Ocorreu um erro ao registrar o usuário. Por favor, tente novamente."
            )

    return render_template("register.html", form=form)


@bp_auth.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            # Atualizar o timestamp de último login
            from .utils.timezone_utils import get_current_time_for_db
            user.last_login = get_current_time_for_db()
            db.session.commit()
            
            # Usar Flask-Login para fazer login
            login_user(user, remember=True)
            
            # Manter sessão para compatibilidade com código legado
            session["user_id"] = user.id
            session["username"] = user.username
            session["is_admin"] = user.is_admin
            session["is_ti"] = user.is_ti
            flash_success("Login realizado com sucesso!")
            return redirect(url_for("main.index"))
        else:
            return redirect(url_for("auth.login", error="invalid_credentials"))
    return render_template("login.html", form=form)


@bp_auth.route("/logout")
def logout():
    logout_user()
    session.clear()
    flash_info("Logout realizado.")
    return redirect(url_for("auth.login"))


@bp_auth.route("/reset_password_request", methods=["GET", "POST"])
def reset_password_request():
    # Se o usuário já está logado, redireciona para a página principal
    if "user_id" in session:
        return redirect(url_for("main.index"))

    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            from .email_utils import send_password_reset_email

            send_password_reset_email(user, token)
            flash_info(
                "Um email com instruções para redefinir sua senha foi enviado."
            )
            return redirect(url_for("auth.login"))
        else:
            flash_error("Email não encontrado.")

    return render_template("reset_password_request.html", form=form)


@bp_auth.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    # Se o usuário já está logado, redireciona para a página principal
    if "user_id" in session:
        return redirect(url_for("main.index"))

    # Encontrar o usuário com este token
    user = User.query.filter_by(reset_token=token).first()

    if not user or not user.verify_reset_token(token):
        flash_error("O link de redefinição de senha é inválido ou expirou.")
        return redirect(url_for("auth.reset_password_request"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.clear_reset_token()
        db.session.commit()
        flash_success("Sua senha foi redefinida com sucesso!")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", form=form)
