from flask import (Blueprint, flash, redirect, render_template, request,
                   session, url_for)
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
            flash("Nome de usuário ou email já está em uso.", "danger")
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
            flash("Usuário registrado com sucesso! Faça login.", "success")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            flash(
                "Ocorreu um erro ao registrar o usuário. Por favor, tente novamente.",
                "danger",
            )

    return render_template("register.html", form=form)


@bp_auth.route("/login", methods=["GET", "POST"])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            session["user_id"] = user.id
            session["username"] = user.username
            session["is_admin"] = user.is_admin
            flash("Login realizado com sucesso!", "success")
            return redirect(url_for("main.index"))
        else:
            return redirect(url_for("auth.login", error="invalid_credentials"))
    return render_template("login.html", form=form)


@bp_auth.route("/logout")
def logout():
    session.clear()
    flash("Logout realizado.", "info")
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
            flash(
                "Um email com instruções para redefinir sua senha foi enviado.", "info"
            )
            return redirect(url_for("auth.login"))
        else:
            flash("Email não encontrado.", "danger")

    return render_template("reset_password_request.html", form=form)


@bp_auth.route("/reset_password/<token>", methods=["GET", "POST"])
def reset_password(token):
    # Se o usuário já está logado, redireciona para a página principal
    if "user_id" in session:
        return redirect(url_for("main.index"))

    # Encontrar o usuário com este token
    user = User.query.filter_by(reset_token=token).first()

    if not user or not user.verify_reset_token(token):
        flash("O link de redefinição de senha é inválido ou expirou.", "danger")
        return redirect(url_for("auth.reset_password_request"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.clear_reset_token()
        db.session.commit()
        flash("Sua senha foi redefinida com sucesso!", "success")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", form=form)
