from flask import (Blueprint, redirect, render_template, request,
                   url_for, current_app)
from app.utils import flash_success, flash_error, flash_info
from flask_login import login_user, logout_user, current_user
from flask_mail import Message
from werkzeug.security import check_password_hash, generate_password_hash
from datetime import datetime, timedelta
import logging

from . import mail, limiter
from .forms_auth import (LoginForm, RegistrationForm, RequestPasswordResetForm,
                         ResetPasswordForm)
from .models import User, db

# Logger de segurança
security_logger = logging.getLogger('security')

bp_auth = Blueprint("auth", __name__)


@bp_auth.route("/register", methods=["GET", "POST"])
@limiter.limit("3 per hour")
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
            
            # Log de segurança
            security_logger.info(
                f"Novo usuário registrado: {user.username} (email: {user.email}) | "
                f"IP: {request.remote_addr} | User-Agent: {request.headers.get('User-Agent')}"
            )
            
            flash_success("Usuário registrado com sucesso! Faça login.")
            return redirect(url_for("auth.login"))
        except Exception as e:
            db.session.rollback()
            security_logger.error(
                f"Erro ao registrar usuário: {form.username.data} | "
                f"Erro: {str(e)} | IP: {request.remote_addr}"
            )
            flash_error(
                "Ocorreu um erro ao registrar o usuário. Por favor, tente novamente."
            )

    return render_template("register.html", form=form)


@bp_auth.route("/login", methods=["GET", "POST"])
@limiter.limit("5 per minute")
def login():
    # Se usuário já está autenticado, redirecionar
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        
        # Verificar se usuário existe
        if not user:
            security_logger.warning(
                f"Tentativa de login com usuário inexistente: {form.username.data} | "
                f"IP: {request.remote_addr} | User-Agent: {request.headers.get('User-Agent')}"
            )
            flash_error("Usuário ou senha inválidos.")
            return render_template("login.html", form=form)
        
        # Verificar se conta está ativa
        if not user.ativo:
            security_logger.warning(
                f"Tentativa de login em conta desativada: {user.username} | "
                f"IP: {request.remote_addr}"
            )
            flash_error("Sua conta foi desativada. Entre em contato com o administrador.")
            return render_template("login.html", form=form)
        
        # Verificar se conta está bloqueada temporariamente
        if hasattr(user, 'locked_until') and user.locked_until:
            if user.locked_until > datetime.utcnow():
                minutes_left = int((user.locked_until - datetime.utcnow()).total_seconds() / 60)
                security_logger.warning(
                    f"Tentativa de login em conta bloqueada: {user.username} | "
                    f"IP: {request.remote_addr} | Bloqueio expira em: {minutes_left}min"
                )
                flash_error(
                    f"Conta temporariamente bloqueada devido a múltiplas tentativas falhas. "
                    f"Tente novamente em {minutes_left} minutos."
                )
                return render_template("login.html", form=form)
            else:
                # Bloqueio expirou, resetar
                user.locked_until = None
                user.login_attempts = 0
                db.session.commit()
        
        # Verificar senha
        if user.check_password(form.password.data):
            from flask import session
            
            # Atualizar o timestamp de último login e resetar tentativas
            from .utils.timezone_utils import get_current_time_for_db
            user.last_login = get_current_time_for_db()
            user.login_attempts = 0
            user.locked_until = None
            db.session.commit()
            
            # NÃO LIMPAR SESSÃO - causa problemas com Flask-Login!
            # session.clear() <- REMOVIDO
            
            # DEBUG
            with open('debug_login.txt', 'a') as f:
                f.write(f"\n[{datetime.now()}] ANTES LOGIN_USER\n")
                f.write(f"session antes: {dict(session)}\n")
            
            # Usar Flask-Login para fazer login
            remember = form.remember_me.data if hasattr(form, 'remember_me') else True
            login_user(user, remember=remember)
            
            # DEBUG
            with open('debug_login.txt', 'a') as f:
                f.write(f"DEPOIS LOGIN_USER\n")
                f.write(f"session depois: {dict(session)}\n")
                f.write(f"current_user.is_authenticated: {current_user.is_authenticated}\n")
            
            # CRÍTICO: Preencher dados da sessão (necessário para templates legados)
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            session['is_ti'] = user.is_ti
            session.permanent = remember
            
            # Log de segurança - LOGIN BEM-SUCEDIDO
            security_logger.info(
                f"Login bem-sucedido: {user.username} (ID: {user.id}) | "
                f"IP: {request.remote_addr} | User-Agent: {request.headers.get('User-Agent')}"
            )
            
            flash_success("Login realizado com sucesso!")
            
            # Redirecionar para página solicitada ou dashboard
            next_page = request.args.get('next')
            if next_page:
                return redirect(next_page)
            return redirect(url_for("main.index"))
        else:
            # Senha incorreta - incrementar tentativas falhas
            if not hasattr(user, 'login_attempts'):
                user.login_attempts = 0
            
            user.login_attempts = (user.login_attempts or 0) + 1
            
            # Bloquear conta após 5 tentativas falhas
            if user.login_attempts >= 5:
                user.locked_until = datetime.utcnow() + timedelta(minutes=15)
                db.session.commit()
                
                security_logger.warning(
                    f"Conta bloqueada por múltiplas tentativas falhas: {user.username} | "
                    f"Tentativas: {user.login_attempts} | IP: {request.remote_addr}"
                )
                
                flash_error(
                    "Sua conta foi temporariamente bloqueada devido a múltiplas tentativas de login falhas. "
                    "Tente novamente em 15 minutos ou use a opção 'Esqueceu a senha'."
                )
            else:
                db.session.commit()
                remaining_attempts = 5 - user.login_attempts
                
                security_logger.warning(
                    f"Tentativa de login falha: {user.username} | "
                    f"Tentativa {user.login_attempts}/5 | IP: {request.remote_addr}"
                )
                
                if remaining_attempts <= 2:
                    flash_error(
                        f"Usuário ou senha inválidos. Você tem mais {remaining_attempts} tentativa(s) "
                        f"antes de sua conta ser bloqueada temporariamente."
                    )
                else:
                    flash_error("Usuário ou senha inválidos.")
            
            return render_template("login.html", form=form)
    
    return render_template("login.html", form=form)


@bp_auth.route("/logout")
def logout():
    from flask import session
    
    if current_user.is_authenticated:
        # Log de segurança
        security_logger.info(
            f"Logout: {current_user.username} (ID: {current_user.id}) | "
            f"IP: {request.remote_addr}"
        )
    
    # Limpar completamente a sessão Flask-Login
    logout_user()
    
    # CRÍTICO: Limpar TODA a sessão do Flask para remover dados em cache
    session.clear()
    
    flash_info("Logout realizado com sucesso.")
    
    # Redirecionar com cache disabled para forçar reload
    response = redirect(url_for("auth.login"))
    response.headers['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response.headers['Pragma'] = 'no-cache'
    response.headers['Expires'] = '0'
    return response


@bp_auth.route("/reset_password_request", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def reset_password_request():
    # Se o usuário já está logado, redireciona para a página principal
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    form = RequestPasswordResetForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user:
            token = user.generate_reset_token()
            from .email_utils import send_password_reset_email

            try:
                send_password_reset_email(user, token)
                
                # Log de segurança
                security_logger.info(
                    f"Solicitação de reset de senha: {user.username} (email: {user.email}) | "
                    f"IP: {request.remote_addr}"
                )
                
                flash_info(
                    "Um email com instruções para redefinir sua senha foi enviado."
                )
            except Exception as e:
                security_logger.error(
                    f"Erro ao enviar email de reset: {user.username} | Erro: {str(e)}"
                )
                flash_error("Erro ao enviar email. Tente novamente mais tarde.")
            
            return redirect(url_for("auth.login"))
        else:
            # Log de tentativa com email inexistente
            security_logger.warning(
                f"Tentativa de reset com email inexistente: {form.email.data} | "
                f"IP: {request.remote_addr}"
            )
            flash_error("Email não encontrado.")

    return render_template("reset_password_request.html", form=form)


@bp_auth.route("/reset_password/<token>", methods=["GET", "POST"])
@limiter.limit("5 per hour")
def reset_password(token):
    # Se o usuário já está logado, redireciona para a página principal
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    # Encontrar o usuário com este token
    user = User.query.filter_by(reset_token=token).first()

    if not user or not user.verify_reset_token(token):
        # Log de tentativa com token inválido
        security_logger.warning(
            f"Tentativa de reset com token inválido/expirado: {token[:20]}... | "
            f"IP: {request.remote_addr}"
        )
        flash_error("O link de redefinição de senha é inválido ou expirou.")
        return redirect(url_for("auth.reset_password_request"))

    form = ResetPasswordForm()
    if form.validate_on_submit():
        user.set_password(form.password.data)
        user.clear_reset_token()
        
        # Resetar tentativas de login e bloqueio
        user.login_attempts = 0
        user.locked_until = None
        
        db.session.commit()
        
        # Log de segurança
        security_logger.info(
            f"Senha redefinida com sucesso: {user.username} | IP: {request.remote_addr}"
        )
        
        flash_success("Sua senha foi redefinida com sucesso! Faça login com a nova senha.")
        return redirect(url_for("auth.login"))

    return render_template("reset_password.html", form=form)
