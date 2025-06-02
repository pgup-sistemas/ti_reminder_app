from flask import Blueprint, render_template, redirect, url_for, flash, request, session
from .forms_auth import RegistrationForm, LoginForm
from .models import User, db
from werkzeug.security import generate_password_hash, check_password_hash

bp_auth = Blueprint('auth', __name__)

@bp_auth.route('/register', methods=['GET', 'POST'])
def register():
    form = RegistrationForm()
    if form.validate_on_submit():
        # Verifica se já existe um usuário com o mesmo nome de usuário ou email
        existing_user = User.query.filter(
            (User.username == form.username.data) | 
            (User.email == form.email.data)
        ).first()
        
        if existing_user:
            flash('Nome de usuário ou email já está em uso.', 'danger')
            return render_template('register.html', form=form)
            
        user = User(
            username=form.username.data, 
            email=form.email.data,
            is_admin=False,  # Usuários comuns não são administradores
            is_ti=False,     # Nem fazem parte da equipe de TI
            ativo=True
        )
        user.set_password(form.password.data)
        
        try:
            db.session.add(user)
            db.session.commit()
            flash('Usuário registrado com sucesso! Faça login.', 'success')
            return redirect(url_for('auth.login'))
        except Exception as e:
            db.session.rollback()
            flash('Ocorreu um erro ao registrar o usuário. Por favor, tente novamente.', 'danger')
            
    return render_template('register.html', form=form)

@bp_auth.route('/login', methods=['GET', 'POST'])
def login():
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(username=form.username.data).first()
        if user and user.check_password(form.password.data):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.is_admin
            flash('Login realizado com sucesso!', 'success')
            return redirect(url_for('main.dashboard'))
        else:
            return redirect(url_for('auth.login', error='invalid_credentials'))
    return render_template('login.html', form=form)

@bp_auth.route('/logout')
def logout():
    session.clear()
    flash('Logout realizado.', 'info')
    return redirect(url_for('auth.login'))
