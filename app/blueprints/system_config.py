"""
Sistema de Configurações do TI OSN System
Rotas para gerenciamento completo das configurações administrativas
"""

import os
import secrets
import io
import csv
from datetime import datetime
from flask import (
    Blueprint, current_app, jsonify, redirect,
    render_template, request, session, url_for, send_file
)
from app.utils import flash_success, flash_error, flash_warning, flash_info
from werkzeug.utils import secure_filename
from sqlalchemy import or_, and_

# Imports usando caminhos relativos padrão do Flask
from ..auth_utils import login_required
from ..models import (
    User, Sector, db, NotificationSettings,
    TaskSlaConfig, SlaConfig, EquipmentRequest
)
from ..utils.timezone_utils import get_current_time_for_db
from ..services.notification_service import NotificationService
from ..services.performance_service import PerformanceService
from ..services.satisfaction_service import SatisfactionService
from ..services.certification_service import CertificationService
from ..services.rfid_service import RFIDService
from ..forms import UserEditForm

# Decorators
def admin_required(f):
    """Decorator para verificar se usuário é admin"""
    def decorated_function(*args, **kwargs):
        if not session.get("is_admin"):
            flash_error("Acesso restrito ao administrador.")
            return redirect(url_for("main.index"))
        return f(*args, **kwargs)
    decorated_function.__name__ = f.__name__
    return decorated_function

# Blueprint
system_config = Blueprint("system_config", __name__, url_prefix="/configuracoes")

# ========================================
# USUÁRIOS
# ========================================

@system_config.route("/usuarios")
@login_required
@admin_required
def list_users():
    """Lista todos os usuários com filtros e paginação"""
    # Parâmetros de busca e filtro
    search = request.args.get('search', '').strip()
    status_filter = request.args.get('status', '')
    role_filter = request.args.get('role', '')
    page = request.args.get('page', type=int, default=1)
    per_page = 10

    # Query base
    query = User.query

    # Aplicar filtros
    if search:
        query = query.filter(
            or_(
                User.username.ilike(f'%{search}%'),
                User.email.ilike(f'%{search}%')
            )
        )

    if status_filter:
        if status_filter == 'active':
            query = query.filter(User.ativo == True)
        elif status_filter == 'inactive':
            query = query.filter(User.ativo == False)

    if role_filter:
        if role_filter == 'admin':
            query = query.filter(User.is_admin == True)
        elif role_filter == 'ti':
            query = query.filter(User.is_ti == True)
        elif role_filter == 'user':
            query = query.filter(and_(User.is_admin == False, User.is_ti == False))

    # Ordenação
    query = query.order_by(User.id.desc())

    # Paginação simples (sem flask-paginate)
    total = query.count()
    users = query.offset((page - 1) * per_page).limit(per_page).all()

    # Simular objeto de paginação
    class SimplePagination:
        def __init__(self, page, per_page, total):
            self.page = page
            self.per_page = per_page
            self.total = total
            self.pages = (total + per_page - 1) // per_page
            self.has_prev = page > 1
            self.has_next = page < self.pages
            self.prev_num = page - 1 if self.has_prev else None
            self.next_num = page + 1 if self.has_next else None

        def iter_pages(self):
            start = max(1, self.page - 2)
            end = min(self.pages + 1, self.page + 3)
            return range(start, end)

    pagination = SimplePagination(page, per_page, total)

    # Estatísticas
    stats = {
        'total_users': User.query.count(),
        'active_users': User.query.filter_by(ativo=True).count(),
        'admin_users': User.query.filter_by(is_admin=True, ativo=True).count(),
        'ti_users': User.query.filter_by(is_ti=True, ativo=True).count()
    }

    from datetime import datetime
    now = datetime.now()

    return render_template(
        "system_config/users_list.html",
        users=users,
        pagination=pagination,
        stats=stats,
        search=search,
        status_filter=status_filter,
        role_filter=role_filter,
        now=now
    )

@system_config.route("/usuarios/novo", methods=["GET", "POST"])
@login_required
@admin_required
def create_user():
    """Criar novo usuário"""
    from ..forms import UserEditForm

    form = UserEditForm()

    # Popular setores
    sectors = Sector.query.order_by(Sector.name).all()
    form.sector_id.choices = [(0, "Selecione um setor")] + [(s.id, s.name) for s in sectors]

    if form.validate_on_submit():
        # Verificar se email já existe
        existing_email = User.query.filter_by(email=form.email.data).first()
        if existing_email:
            flash_error("Este email já está em uso.")
            return render_template("system_config/user_form.html", form=form, is_edit=False)

        # Verificar se username já existe
        existing_username = User.query.filter_by(username=form.username.data).first()
        if existing_username:
            flash_error("Este nome de usuário já está em uso.")
            return render_template("system_config/user_form.html", form=form, is_edit=False)

        # Criar usuário
        user = User(
            username=form.username.data,
            email=form.email.data,
            is_admin=form.is_admin.data,
            is_ti=form.is_ti.data,
            ativo=True
        )

        if form.sector_id.data and form.sector_id.data != 0:
            user.sector_id = form.sector_id.data

        # Definir senha
        if form.new_password.data:
            if len(form.new_password.data) < 6:
                flash_error("A senha deve ter pelo menos 6 caracteres.")
                from datetime import datetime
                now = datetime.now()
    
                return render_template("system_config/user_form.html", form=form, is_edit=False, now=now)
            user.set_password(form.new_password.data)
        else:
            # Senha padrão
            user.set_password("123456")

        try:
            db.session.add(user)
            db.session.commit()

            # Criar configurações de notificação padrão
            notification_settings = NotificationSettings(user_id=user.id)
            db.session.add(notification_settings)
            db.session.commit()

            flash_success(f"Usuário {user.username} criado com sucesso!")
            return redirect(url_for('system_config.list_users'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao criar usuário: {e}")
            flash_error("Erro ao criar usuário.")

    from datetime import datetime
    now = datetime.now()

    return render_template("system_config/user_form.html", form=form, is_edit=False, now=now)

@system_config.route("/usuarios/<int:user_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(user_id):
    """Editar usuário existente"""
    from ..forms import UserEditForm

    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)

    # Popular setores
    sectors = Sector.query.order_by(Sector.name).all()
    form.sector_id.choices = [(0, "Selecione um setor")] + [(s.id, s.name) for s in sectors]

    # Preencher setor atual
    form.sector_id.data = user.sector_id or 0

    # Impedir que admin edite a si mesmo perdendo privilégios
    if user.id == session.get("user_id"):
        form.is_admin.data = True

    if form.validate_on_submit():
        try:
            # Debug: imprimir dados do formulário
            print("DEBUG: ===== INICIANDO ATUALIZAÇÃO DE USUÁRIO =====")
            print(f"DEBUG: Form data - username: {form.username.data}, email: {form.email.data}")
            print(f"DEBUG: Request form data keys: {list(request.form.keys())}")
            print(f"DEBUG: Current user email: {user.email}")

            # Verificar conflitos de email
            existing_email = User.query.filter(
                User.email == form.email.data,
                User.id != user.id
            ).first()
            if existing_email:
                print(f"DEBUG: Email conflict detected with user {existing_email.id}")
                flash_error("Este email já está em uso por outro usuário.")
                return render_template("system_config/user_form.html", form=form, user=user, is_edit=True)

            # Verificar conflitos de username
            existing_username = User.query.filter(
                User.username == form.username.data,
                User.id != user.id
            ).first()
            if existing_username:
                print(f"DEBUG: Username conflict detected with user {existing_username.id}")
                flash_error("Este nome de usuário já está em uso por outro usuário.")
                return render_template("system_config/user_form.html", form=form, user=user, is_edit=True)

            # Atualizar dados básicos
            print(f"DEBUG: Updating user {user.id} from {user.email} to {form.email.data}")
            user.username = form.username.data
            user.email = form.email.data
            user.sector_id = form.sector_id.data if form.sector_id.data and form.sector_id.data != 0 else None

            # Atualizar permissões (com verificações de segurança)
            if user.id == session.get("user_id"):
                # Admin não pode remover seus próprios privilégios
                user.is_admin = True
            else:
                # Verificar se é o último admin
                if user.is_admin and not form.is_admin.data:
                    admin_count = User.query.filter_by(is_admin=True, ativo=True).count()
                    if admin_count <= 1:
                        flash_error("Não é possível remover os privilégios de administrador do último administrador ativo.")
                        return render_template("system_config/user_form.html", form=form, user=user, is_edit=True)
                user.is_admin = form.is_admin.data

            user.is_ti = form.is_ti.data

            # Atualizar senha se fornecida
            if form.change_password.data and form.new_password.data:
                if len(form.new_password.data) < 6:
                    flash_error("A senha deve ter pelo menos 6 caracteres.")
                    return render_template("system_config/user_form.html", form=form, user=user, is_edit=True)
                user.set_password(form.new_password.data)
                flash_success("Senha atualizada com sucesso!")

            # Atualizar status ativo se fornecido
            if 'ativo' in request.form:
                user.ativo = request.form.get('ativo') == 'on'
            else:
                # Se não foi enviado, manter o status atual
                pass

            # Atualizar data de modificação
            from ..utils.timezone_utils import get_current_time_for_db
            user.updated_at = get_current_time_for_db()

            print(f"DEBUG: Before commit - user.email: {user.email}")

            db.session.commit()

            # Debug: verificar após o commit
            db.session.refresh(user)
            print(f"DEBUG: After commit - user.email: {user.email}")
            print("DEBUG: ===== ATUALIZAÇÃO CONCLUÍDA =====")

            flash_success(f"Usuário {user.username} atualizado com sucesso!")
            return redirect(url_for('system_config.list_users'))

        except Exception as e:
            db.session.rollback()
            print(f"DEBUG: ERROR updating user: {e}")
            import traceback
            print(f"DEBUG: Traceback: {traceback.format_exc()}")
            flash_error("Erro ao atualizar usuário.")
            return render_template("system_config/user_form.html", form=form, user=user, is_edit=True)

    from datetime import datetime
    now = datetime.now()

    return render_template("system_config/user_form.html", form=form, user=user, is_edit=True, now=now)

@system_config.route("/usuarios/<int:user_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_user(user_id):
    """Ativar/desativar usuário"""
    user = User.query.get_or_404(user_id)

    # Impedir que admin desative a si mesmo
    if user.id == session.get("user_id"):
        return jsonify({"success": False, "message": "Você não pode desativar sua própria conta."})

    # Verificar se é o último admin ativo
    if user.is_admin and user.ativo:
        admin_count = User.query.filter_by(is_admin=True, ativo=True).count()
        if admin_count <= 1:
            return jsonify({"success": False, "message": "Não é possível desativar o último administrador ativo."})

    user.ativo = not user.ativo
    status = "ativado" if user.ativo else "desativado"

    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": f"Usuário {status} com sucesso!",
            "status": status
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao alterar status do usuário: {e}")
        return jsonify({"success": False, "message": "Erro ao alterar status do usuário."})

@system_config.route("/usuarios/<int:user_id>/reset-senha", methods=["POST"])
@login_required
@admin_required
def reset_user_password(user_id):
    """Resetar senha do usuário"""
    user = User.query.get_or_404(user_id)

    # Gerar nova senha
    new_password = secrets.token_hex(4)  # 8 caracteres
    user.set_password(new_password)

    try:
        db.session.commit()
        return jsonify({
            "success": True,
            "message": "Senha resetada com sucesso!",
            "new_password": new_password
        })
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao resetar senha: {e}")
        return jsonify({"success": False, "message": "Erro ao resetar senha."})

@system_config.route("/usuarios/<int:user_id>/deletar", methods=["DELETE"])
@login_required
@admin_required
def delete_user(user_id):
    """Excluir usuário"""
    user = User.query.get_or_404(user_id)

    # Impedir exclusão do próprio usuário
    if user.id == session.get("user_id"):
        return jsonify({"success": False, "message": "Você não pode excluir sua própria conta."})

    # Verificar se é o último admin
    if user.is_admin:
        admin_count = User.query.filter_by(is_admin=True, ativo=True).count()
        if admin_count <= 1:
            return jsonify({"success": False, "message": "Não é possível excluir o último administrador."})

    try:
        # Remover configurações de notificação
        NotificationSettings.query.filter_by(user_id=user.id).delete()

        # Remover usuário
        db.session.delete(user)
        db.session.commit()

        return jsonify({"success": True, "message": "Usuário excluído com sucesso!"})
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(f"Erro ao excluir usuário: {e}")
        return jsonify({"success": False, "message": "Erro ao excluir usuário."})

@system_config.route("/usuarios/export")
@login_required
@admin_required
def export_users():
    """Exportar usuários para CSV"""
    # Filtrar usuários selecionados se fornecidos
    user_ids = request.args.getlist('users[]', type=int)
    query = User.query

    if user_ids:
        query = query.filter(User.id.in_(user_ids))

    users = query.all()

    # Criar CSV usando StringIO e depois converter para bytes
    output = io.StringIO()
    writer = csv.writer(output, delimiter=',', quotechar='"', quoting=csv.QUOTE_MINIMAL)

    # Cabeçalho
    writer.writerow([
        'ID', 'Nome de Usuário', 'Email', 'Admin', 'TI', 'Ativo',
        'Setor', 'Data de Criação', 'Último Login'
    ])

    # Dados
    for user in users:
        writer.writerow([
            user.id,
            user.username,
            user.email,
            'Sim' if user.is_admin else 'Não',
            'Sim' if user.is_ti else 'Não',
            'Sim' if user.ativo else 'Não',
            user.sector.name if user.sector else '',
            user.created_at.strftime('%d/%m/%Y %H:%M') if hasattr(user, 'created_at') and user.created_at else '',
            user.last_login.strftime('%d/%m/%Y %H:%M') if hasattr(user, 'last_login') and user.last_login else ''
        ])

    # Converter para bytes
    csv_data = output.getvalue()
    output.close()

    # Criar BytesIO para send_file
    bytes_output = io.BytesIO(csv_data.encode('utf-8'))

    return send_file(
        bytes_output,
        mimetype='text/csv',
        as_attachment=True,
        download_name=f'usuarios_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
    )

@system_config.route("/usuarios/perfis")
@login_required
@admin_required
def manage_profiles():
    """Gerenciar perfis e permissões"""
    # Por enquanto, redirecionar para listagem
    # Futuramente implementar gestão avançada de perfis
    flash_info("Funcionalidade de perfis em desenvolvimento.")
    return redirect(url_for('system_config.list_users'))

@system_config.route("/usuarios/bulk", methods=["GET", "POST"])
@login_required
@admin_required
def bulk_user_actions():
    """Ações em lote para usuários"""
    if request.method == "POST":
        action = request.form.get('action')
        user_ids = request.form.getlist('user_ids[]', type=int)

        if not user_ids:
            flash_warning("Nenhum usuário selecionado.")
            return redirect(url_for('system_config.bulk_user_actions'))

        if action == 'activate':
            User.query.filter(User.id.in_(user_ids)).update({'ativo': True})
            flash_success(f"{len(user_ids)} usuários ativados.")
        elif action == 'deactivate':
            # Verificar se não está desativando o último admin
            admins_to_deactivate = User.query.filter(
                User.id.in_(user_ids),
                User.is_admin == True,
                User.ativo == True
            ).count()

            if admins_to_deactivate > 0:
                remaining_admins = User.query.filter_by(is_admin=True, ativo=True).count() - admins_to_deactivate
                if remaining_admins < 1:
                    flash_error("Não é possível desativar todos os administradores.")
                    return redirect(url_for('system_config.bulk_user_actions'))

            User.query.filter(User.id.in_(user_ids)).update({'ativo': False})
            flash_success(f"{len(user_ids)} usuários desativados.")
        elif action == 'delete':
            # Verificar se não está excluindo o último admin
            admins_to_delete = User.query.filter(
                User.id.in_(user_ids),
                User.is_admin == True
            ).count()

            if admins_to_delete > 0:
                remaining_admins = User.query.filter_by(is_admin=True, ativo=True).count() - admins_to_delete
                if remaining_admins < 1:
                    flash_error("Não é possível excluir todos os administradores.")
                    return redirect(url_for('system_config.bulk_user_actions'))

            # Excluir configurações de notificação primeiro
            NotificationSettings.query.filter(NotificationSettings.user_id.in_(user_ids)).delete()
            User.query.filter(User.id.in_(user_ids)).delete()
            flash_success(f"{len(user_ids)} usuários excluídos.")

        db.session.commit()
        return redirect(url_for('system_config.list_users'))

    # GET: mostrar formulário
    users = User.query.order_by(User.id).all()
    from datetime import datetime
    now = datetime.now()

    return render_template("system_config/bulk_user_actions.html", users=users, now=now)

# ========================================
# SISTEMA GERAL
# ========================================

@system_config.route("/sistema/geral", methods=["GET", "POST"])
@login_required
@admin_required
def general_settings():
    """Configurações gerais do sistema"""
    if request.method == "POST":
        # Salvar configurações gerais
        system_name = request.form.get('system_name', 'TI OSN System')
        maintenance_mode = request.form.get('maintenance_mode') == 'on'
        timezone = request.form.get('timezone', 'America/Manaus')
        language = request.form.get('language', 'pt-BR')

        # Aqui você pode salvar no banco de dados ou arquivo de configuração
        # Por enquanto, apenas simular salvamento
        current_app.config['SYSTEM_NAME'] = system_name
        current_app.config['MAINTENANCE_MODE'] = maintenance_mode
        current_app.config['TIMEZONE'] = timezone
        current_app.config['LANGUAGE'] = language

        flash_success("Configurações gerais salvas com sucesso!")
        return redirect(url_for('system_config.general_settings'))

    # Configurações atuais
    settings = {
        'system_name': current_app.config.get('SYSTEM_NAME', 'TI OSN System'),
        'system_version': '2.0',
        'maintenance_mode': current_app.config.get('MAINTENANCE_MODE', False),
        'debug_mode': current_app.debug,
        'timezone': current_app.config.get('TIMEZONE', 'America/Manaus'),
        'language': current_app.config.get('LANGUAGE', 'pt-BR')
    }

    # Opções disponíveis
    timezones = {
        'America/Manaus': {'name': 'Manaus', 'offset': 'UTC-4'},
        'America/Sao_Paulo': {'name': 'São Paulo', 'offset': 'UTC-3'},
        'America/Rio_Branco': {'name': 'Rio Branco', 'offset': 'UTC-5'},
        'America/Porto_Velho': {'name': 'Porto Velho', 'offset': 'UTC-4'},
        'America/Boa_Vista': {'name': 'Boa Vista', 'offset': 'UTC-4'},
        'America/Araguaina': {'name': 'Araguaína', 'offset': 'UTC-3'},
        'America/Bahia': {'name': 'Bahia', 'offset': 'UTC-3'},
        'America/Belem': {'name': 'Belém', 'offset': 'UTC-3'},
        'America/Fortaleza': {'name': 'Fortaleza', 'offset': 'UTC-3'},
        'America/Maceio': {'name': 'Maceió', 'offset': 'UTC-3'},
        'America/Recife': {'name': 'Recife', 'offset': 'UTC-3'},
        'UTC': {'name': 'UTC', 'offset': 'UTC+0'}
    }

    languages = [
        ('pt-BR', 'Português (Brasil)'),
        ('en-US', 'English (US)'),
        ('es-ES', 'Español')
    ]

    from datetime import datetime
    now = datetime.now()

    return render_template("system_config/general_settings.html",
                          settings=settings,
                          timezones=timezones,
                          languages=languages,
                          now=now)

@system_config.route("/sistema/seguranca", methods=["GET", "POST"])
@login_required
@admin_required
def security_settings():
    """Configurações de segurança"""
    if request.method == "POST":
        # Salvar configurações de segurança
        password_min_length = int(request.form.get('password_min_length', 6))
        password_require_uppercase = request.form.get('password_require_uppercase') == 'on'
        password_require_lowercase = request.form.get('password_require_lowercase') == 'on'
        password_require_numbers = request.form.get('password_require_numbers') == 'on'
        password_require_special = request.form.get('password_require_special') == 'on'

        session_timeout = int(request.form.get('session_timeout', 30))
        max_login_attempts = int(request.form.get('max_login_attempts', 5))
        lockout_duration = int(request.form.get('lockout_duration', 15))

        two_factor_required = request.form.get('two_factor_required') == 'on'
        ip_whitelist_enabled = request.form.get('ip_whitelist_enabled') == 'on'
        audit_log_enabled = request.form.get('audit_log_enabled') == 'on'

        # Salvar configurações (simulado)
        current_app.config['PASSWORD_MIN_LENGTH'] = password_min_length
        current_app.config['PASSWORD_REQUIRE_UPPERCASE'] = password_require_uppercase
        current_app.config['PASSWORD_REQUIRE_LOWERCASE'] = password_require_lowercase
        current_app.config['PASSWORD_REQUIRE_NUMBERS'] = password_require_numbers
        current_app.config['PASSWORD_REQUIRE_SPECIAL'] = password_require_special

        current_app.config['SESSION_TIMEOUT'] = session_timeout
        current_app.config['MAX_LOGIN_ATTEMPTS'] = max_login_attempts
        current_app.config['LOCKOUT_DURATION'] = lockout_duration

        current_app.config['TWO_FACTOR_REQUIRED'] = two_factor_required
        current_app.config['IP_WHITELIST_ENABLED'] = ip_whitelist_enabled
        current_app.config['AUDIT_LOG_ENABLED'] = audit_log_enabled

        flash_success("Configurações de segurança salvas com sucesso!")
        return redirect(url_for('system_config.security_settings'))

    # Configurações atuais
    settings = {
        'password_min_length': current_app.config.get('PASSWORD_MIN_LENGTH', 6),
        'password_require_uppercase': current_app.config.get('PASSWORD_REQUIRE_UPPERCASE', True),
        'password_require_lowercase': current_app.config.get('PASSWORD_REQUIRE_LOWERCASE', True),
        'password_require_numbers': current_app.config.get('PASSWORD_REQUIRE_NUMBERS', True),
        'password_require_special': current_app.config.get('PASSWORD_REQUIRE_SPECIAL', False),

        'session_timeout': current_app.config.get('SESSION_TIMEOUT', 30),
        'max_login_attempts': current_app.config.get('MAX_LOGIN_ATTEMPTS', 5),
        'lockout_duration': current_app.config.get('LOCKOUT_DURATION', 15),

        'two_factor_required': current_app.config.get('TWO_FACTOR_REQUIRED', False),
        'ip_whitelist_enabled': current_app.config.get('IP_WHITELIST_ENABLED', False),
        'audit_log_enabled': current_app.config.get('AUDIT_LOG_ENABLED', True)
    }

    from datetime import datetime
    now = datetime.now()

    return render_template("system_config/security_settings.html", settings=settings, now=now)

@system_config.route("/sistema/backup", methods=["GET", "POST"])
@login_required
@admin_required
def backup_settings():
    """Configurações de backup"""
    if request.method == "POST":
        # Salvar configurações de backup
        backup_enabled = request.form.get('backup_enabled') == 'on'
        backup_frequency = request.form.get('backup_frequency', 'daily')
        backup_time = request.form.get('backup_time', '02:00')
        backup_retention_days = int(request.form.get('backup_retention_days', 30))
        backup_location = request.form.get('backup_location', 'local')

        compression_enabled = request.form.get('compression_enabled') == 'on'
        encryption_enabled = request.form.get('encryption_enabled') == 'on'
        email_notifications = request.form.get('email_notifications') == 'on'

        # Salvar configurações (simulado)
        current_app.config['BACKUP_ENABLED'] = backup_enabled
        current_app.config['BACKUP_FREQUENCY'] = backup_frequency
        current_app.config['BACKUP_TIME'] = backup_time
        current_app.config['BACKUP_RETENTION_DAYS'] = backup_retention_days
        current_app.config['BACKUP_LOCATION'] = backup_location

        current_app.config['BACKUP_COMPRESSION_ENABLED'] = compression_enabled
        current_app.config['BACKUP_ENCRYPTION_ENABLED'] = encryption_enabled
        current_app.config['BACKUP_EMAIL_NOTIFICATIONS'] = email_notifications

        flash_success("Configurações de backup salvas com sucesso!")
        return redirect(url_for('system_config.backup_settings'))

    # Configurações atuais
    settings = {
        'backup_enabled': current_app.config.get('BACKUP_ENABLED', True),
        'backup_frequency': current_app.config.get('BACKUP_FREQUENCY', 'daily'),
        'backup_time': current_app.config.get('BACKUP_TIME', '02:00'),
        'backup_retention_days': current_app.config.get('BACKUP_RETENTION_DAYS', 30),
        'backup_location': current_app.config.get('BACKUP_LOCATION', 'local'),

        'compression_enabled': current_app.config.get('BACKUP_COMPRESSION_ENABLED', True),
        'encryption_enabled': current_app.config.get('BACKUP_ENCRYPTION_ENABLED', False),
        'email_notifications': current_app.config.get('BACKUP_EMAIL_NOTIFICATIONS', True)
    }

    # Opções disponíveis
    frequencies = [
        ('hourly', 'A cada hora'),
        ('daily', 'Diariamente'),
        ('weekly', 'Semanalmente'),
        ('monthly', 'Mensalmente')
    ]

    locations = [
        ('local', 'Disco Local'),
        ('network', 'Disco de Rede'),
        ('cloud', 'Nuvem (AWS S3)')
    ]

    from datetime import datetime
    now = datetime.now()

    return render_template("system_config/backup_settings.html",
                          settings=settings,
                          frequencies=frequencies,
                          locations=locations,
                          now=now)

@system_config.route("/sistema/logs")
@login_required
@admin_required
def system_logs():
    """Visualizar logs do sistema"""
    from datetime import datetime

    # Dados simulados para logs (em produção, buscar do arquivo de log)
    current_date = datetime.now().strftime('%Y-%m-%d')

    # Estatísticas simuladas
    log_stats = {
        'errors_24h': 0,
        'warnings_24h': 3,
        'info_24h': 127,
        'log_size': '2.1 MB'
    }

    # Logs simulados (últimas entradas)
    sample_logs = [
        {
            'timestamp': '2025-10-17 09:16:36',
            'level': 'INFO',
            'message': 'Application created successfully'
        },
        {
            'timestamp': '2025-10-17 09:16:36',
            'level': 'INFO',
            'message': 'Blueprint de configurações do sistema registrado com sucesso'
        },
        {
            'timestamp': '2025-10-17 09:16:36',
            'level': 'INFO',
            'message': 'SQLAlchemy conectado em: postgresql://postgres:***@localhost:5432/ti_reminder_db'
        },
        {
            'timestamp': '2025-10-17 08:59:18',
            'level': 'WARNING',
            'message': 'Debugger is active!'
        },
        {
            'timestamp': '2025-10-17 08:59:18',
            'level': 'INFO',
            'message': 'Tarefa agendada de notificações configurada (a cada 1 hora)'
        },
        {
            'timestamp': '2025-10-17 08:59:18',
            'level': 'INFO',
            'message': 'Tarefa agendada de pesquisas de satisfação configurada (a cada 6 horas)'
        },
        {
            'timestamp': '2025-10-17 08:59:18',
            'level': 'INFO',
            'message': 'Tarefa agendada de certificações configurada (a cada 1 hora)'
        },
        {
            'timestamp': '2025-10-17 08:59:18',
            'level': 'DEBUG',
            'message': 'Scheduler started'
        }
    ]

    from datetime import datetime
    now = datetime.now()

    return render_template("system_config/system_logs.html",
                          current_date=current_date,
                          log_stats=log_stats,
                          logs=sample_logs,
                          now=now)

# ========================================
# NOTIFICAÇÕES
# ========================================

@system_config.route("/notificacoes/templates", methods=["GET", "POST"])
@login_required
@admin_required
def notification_templates():
    """Gerenciar templates de notificação"""
    if request.method == "POST":
        # Implementar gestão de templates
        flash_success("Templates de notificação salvos com sucesso!")
        return redirect(url_for('system_config.notification_templates'))

    from datetime import datetime
    now = datetime.now()

    return render_template("system_config/notification_templates.html", now=now)

@system_config.route("/notificacoes/regras", methods=["GET", "POST"])
@login_required
@admin_required
def notification_rules():
    """Configurar regras de notificação"""
    if request.method == "POST":
        # Implementar regras de notificação
        flash_success("Regras de notificação salvas com sucesso!")
        return redirect(url_for('system_config.notification_rules'))

    from datetime import datetime
    now = datetime.now()

    return render_template("system_config/notification_rules.html", now=now)

@system_config.route("/notificacoes/historico")
@login_required
@admin_required
def notification_history():
    """Histórico de notificações enviadas"""
    from datetime import datetime

    # Dados simulados para histórico de notificações
    current_date = datetime.now().strftime('%Y-%m-%d')

    # Estatísticas simuladas
    notification_stats = {
        'sent_30_days': 1247,
        'failed_30_days': 3,
        'pending': 12,
        'success_rate': '99.8%'
    }

    # Notificações simuladas
    notifications = [
        {
            'datetime': '17/10/2025 09:16',
            'type': 'chamado',
            'recipient': 'raphael.sant.emp@gmail.com',
            'subject': 'Chamado #21 Aberto: WhatsApp',
            'status': 'sent'
        },
        {
            'datetime': '17/10/2025 09:16',
            'type': 'chamado',
            'recipient': 'ti@example.com',
            'subject': 'Novo Chamado #21 Aberto por raphael',
            'status': 'sent'
        },
        {
            'datetime': '17/10/2025 08:59',
            'type': 'chamado',
            'recipient': 'raphael.sant.emp@gmail.com',
            'subject': 'Chamado #20 Aberto: Suporte Sala de Laudo',
            'status': 'sent'
        },
        {
            'datetime': '16/10/2025 14:30',
            'type': 'lembrete',
            'recipient': 'admin@example.com',
            'subject': 'Lembrete: Backup Mensal vence em 3 dias',
            'status': 'sent'
        },
        {
            'datetime': '16/10/2025 10:15',
            'type': 'tarefa',
            'recipient': 'user@example.com',
            'subject': 'Tarefa Vencida: Atualizar documentação',
            'status': 'failed'
        }
    ]

    from datetime import datetime
    now = datetime.now()

    return render_template("system_config/notification_history.html",
                          current_date=current_date,
                          notification_stats=notification_stats,
                          notifications=notifications,
                          now=now)

# ========================================
# INTEGRAÇÕES
# ========================================

@system_config.route("/integracoes/email", methods=["GET", "POST"])
@login_required
@admin_required
def email_integration():
    """Configuração de integração com email"""
    if request.method == "POST":
        # Salvar configurações de email
        smtp_server = request.form.get('smtp_server', '')
        smtp_port = int(request.form.get('smtp_port', 587))
        smtp_username = request.form.get('smtp_username', '')
        smtp_password = request.form.get('smtp_password', '')
        smtp_use_tls = request.form.get('smtp_use_tls') == 'on'
        smtp_use_ssl = request.form.get('smtp_use_ssl') == 'on'

        from_email = request.form.get('from_email', '')
        from_name = request.form.get('from_name', 'TI OSN System')

        # Testar conexão se solicitado
        if request.form.get('test_connection'):
            try:
                import smtplib
                server = smtplib.SMTP(smtp_server, smtp_port)
                server.ehlo()
                if smtp_use_tls:
                    server.starttls()
                if smtp_username and smtp_password:
                    server.login(smtp_username, smtp_password)
                server.quit()
                flash_success("Conexão SMTP testada com sucesso!")
            except Exception as e:
                flash_error(f"Erro na conexão SMTP: {str(e)}")
                return redirect(url_for('system_config.email_integration'))

        # Salvar configurações (simulado)
        current_app.config['SMTP_SERVER'] = smtp_server
        current_app.config['SMTP_PORT'] = smtp_port
        current_app.config['SMTP_USERNAME'] = smtp_username
        current_app.config['SMTP_PASSWORD'] = smtp_password
        current_app.config['SMTP_USE_TLS'] = smtp_use_tls
        current_app.config['SMTP_USE_SSL'] = smtp_use_ssl

        current_app.config['FROM_EMAIL'] = from_email
        current_app.config['FROM_NAME'] = from_name

        flash_success("Configurações de email salvas com sucesso!")
        return redirect(url_for('system_config.email_integration'))

    # Configurações atuais
    settings = {
        'smtp_server': current_app.config.get('SMTP_SERVER', ''),
        'smtp_port': current_app.config.get('SMTP_PORT', 587),
        'smtp_username': current_app.config.get('SMTP_USERNAME', ''),
        'smtp_use_tls': current_app.config.get('SMTP_USE_TLS', True),
        'smtp_use_ssl': current_app.config.get('SMTP_USE_SSL', False),

        'from_email': current_app.config.get('FROM_EMAIL', ''),
        'from_name': current_app.config.get('FROM_NAME', 'TI OSN System')
    }

    from datetime import datetime
    now = datetime.now()

    return render_template("system_config/email_integration.html", settings=settings, now=now)

@system_config.route("/integracoes/api", methods=["GET", "POST"])
@login_required
@admin_required
def api_integrations():
    """Gerenciar integrações com APIs externas"""
    if request.method == "POST":
        # Salvar configurações de API
        api_name = request.form.get('api_name', '')
        api_endpoint = request.form.get('api_endpoint', '')
        api_key = request.form.get('api_key', '')
        api_secret = request.form.get('api_secret', '')
        api_enabled = request.form.get('api_enabled') == 'on'

        # Testar conexão se solicitado
        if request.form.get('test_connection'):
            try:
                # Simular teste de API
                import requests
                headers = {}
                if api_key:
                    headers['Authorization'] = f'Bearer {api_key}'
                if api_secret:
                    headers['X-API-Secret'] = api_secret

                response = requests.get(api_endpoint, headers=headers, timeout=10)
                if response.status_code == 200:
                    flash_success("Conexão com API testada com sucesso!")
                else:
                    flash_warning(f"Erro na API: HTTP {response.status_code}")
            except Exception as e:
                flash_error(f"Erro na conexão com API: {str(e)}")
                return redirect(url_for('system_config.api_integrations'))

        # Salvar configurações (simulado)
        current_app.config[f'API_{api_name.upper()}_ENDPOINT'] = api_endpoint
        current_app.config[f'API_{api_name.upper()}_KEY'] = api_key
        current_app.config[f'API_{api_name.upper()}_SECRET'] = api_secret
        current_app.config[f'API_{api_name.upper()}_ENABLED'] = api_enabled

        flash_success("Integrações API salvas com sucesso!")
        return redirect(url_for('system_config.api_integrations'))

    # Configurações atuais (simuladas)
    apis = [
        {
            'name': 'slack',
            'title': 'Slack',
            'endpoint': current_app.config.get('API_SLACK_ENDPOINT', ''),
            'enabled': current_app.config.get('API_SLACK_ENABLED', False),
            'description': 'Integração com Slack para notificações'
        },
        {
            'name': 'teams',
            'title': 'Microsoft Teams',
            'endpoint': current_app.config.get('API_TEAMS_ENDPOINT', ''),
            'enabled': current_app.config.get('API_TEAMS_ENABLED', False),
            'description': 'Integração com Microsoft Teams'
        },
        {
            'name': 'telegram',
            'title': current_app.config.get('API_TELEGRAM_ENDPOINT', ''),
            'endpoint': '',
            'enabled': current_app.config.get('API_TELEGRAM_ENABLED', False),
            'description': 'Integração com Telegram Bot'
        },
        {
            'name': 'zapier',
            'title': 'Zapier',
            'endpoint': current_app.config.get('API_ZAPIER_ENDPOINT', ''),
            'enabled': current_app.config.get('API_ZAPIER_ENABLED', False),
            'description': 'Integração com Zapier para automação'
        }
    ]

    from datetime import datetime
    now = datetime.now()

    return render_template("system_config/api_integrations.html", apis=apis, now=now)

@system_config.route("/integracoes/rfid", methods=["GET", "POST"])
@login_required
@admin_required
def rfid_integration():
    """Configuração de integração RFID"""
    if request.method == "POST":
        # Salvar configurações RFID
        scan_interval = int(request.form.get('scan_interval', 5))
        lost_threshold_hours = int(request.form.get('lost_threshold_hours', 24))
        auto_alert_lost = request.form.get('auto_alert_lost') == 'on'
        track_movement = request.form.get('track_movement') == 'on'

        # Salvar configurações (simulado)
        current_app.config['RFID_SCAN_INTERVAL'] = scan_interval
        current_app.config['RFID_LOST_THRESHOLD_HOURS'] = lost_threshold_hours
        current_app.config['RFID_AUTO_ALERT_LOST'] = auto_alert_lost
        current_app.config['RFID_TRACK_MOVEMENT'] = track_movement

        flash_success("Configurações RFID salvas com sucesso!")
        return redirect(url_for('system_config.rfid_integration'))

    # Configurações atuais
    settings = {
        'scan_interval': current_app.config.get('RFID_SCAN_INTERVAL', 5),
        'lost_threshold_hours': current_app.config.get('RFID_LOST_THRESHOLD_HOURS', 24),
        'auto_alert_lost': current_app.config.get('RFID_AUTO_ALERT_LOST', True),
        'track_movement': current_app.config.get('RFID_TRACK_MOVEMENT', True)
    }

    # Dados simulados dos leitores
    readers = [
        {
            'id': 'READER-001',
            'name': 'Entrada Principal',
            'location': 'Recepção',
            'status': 'online',
            'last_reading': 'Há 2 minutos'
        },
        {
            'id': 'READER-002',
            'name': 'Almoxarifado',
            'location': 'Depósito',
            'status': 'online',
            'last_reading': 'Há 5 minutos'
        },
        {
            'id': 'READER-003',
            'name': 'Sala TI',
            'location': 'Setor TI',
            'status': 'offline',
            'last_reading': 'Há 2 horas'
        }
    ]

    # Estatísticas simuladas
    stats = {
        'system_status': 'active',
        'active_readers': 5,
        'registered_tags': 127,
        'lost_equipment': 2
    }

    from datetime import datetime
    now = datetime.now()

    return render_template("system_config/rfid_integration.html",
                          settings=settings,
                          readers=readers,
                          stats=stats,
                          now=now)

# ========================================
# PERFORMANCE
# ========================================

@system_config.route("/performance/metricas")
@login_required
@admin_required
def performance_metrics():
    """Métricas de performance do sistema"""
    # Reutilizar dashboard existente
    return redirect(url_for('main.performance_dashboard'))

@system_config.route("/performance/otimizacao", methods=["GET", "POST"])
@login_required
@admin_required
def performance_optimization():
    """Executar otimizações de performance"""
    if request.method == "POST":
        # Salvar configurações de performance
        cache_timeout = int(request.form.get('cache_timeout', 3600))
        max_connections = int(request.form.get('max_connections', 100))
        query_timeout = int(request.form.get('query_timeout', 30))
        memory_limit = int(request.form.get('memory_limit', 512))

        enable_caching = request.form.get('enable_caching') == 'on'
        enable_compression = request.form.get('enable_compression') == 'on'
        enable_monitoring = request.form.get('enable_monitoring') == 'on'

        # Salvar configurações (simulado)
        current_app.config['CACHE_TIMEOUT'] = cache_timeout
        current_app.config['MAX_CONNECTIONS'] = max_connections
        current_app.config['QUERY_TIMEOUT'] = query_timeout
        current_app.config['MEMORY_LIMIT'] = memory_limit

        current_app.config['ENABLE_CACHING'] = enable_caching
        current_app.config['ENABLE_COMPRESSION'] = enable_compression
        current_app.config['ENABLE_MONITORING'] = enable_monitoring

        flash_success("Configurações de performance salvas com sucesso!")
        return redirect(url_for('system_config.performance_optimization'))

    # Dados simulados para o template
    system_stats = {
        'cpu_usage': '98.5%',
        'memory_used': '2.1 GB',
        'disk_io': '45 MB',
        'avg_response_time': '1.2s'
    }

    optimization_tools = [
        {
            'name': 'clear_cache',
            'title': 'Limpar Cache',
            'description': 'Remove dados temporários em cache para liberar memória',
            'last_execution': 'Há 2 horas',
            'icon': 'memory',
            'color': 'primary'
        },
        {
            'name': 'rebuild_indexes',
            'title': 'Recriar Índices',
            'description': 'Reconstroi índices do banco de dados para melhor performance',
            'last_execution': 'Há 1 dia',
            'icon': 'database',
            'color': 'success'
        },
        {
            'name': 'optimize_queries',
            'title': 'Otimizar Queries',
            'description': 'Analisa e otimiza consultas SQL lentas',
            'last_execution': 'Há 3 dias',
            'icon': 'search',
            'color': 'info'
        },
        {
            'name': 'compact_database',
            'title': 'Compactar Banco',
            'description': 'Remove espaços vazios e otimiza armazenamento',
            'last_execution': 'Há 1 semana',
            'icon': 'compress',
            'color': 'warning'
        }
    ]

    # Configurações atuais
    settings = {
        'cache_timeout': current_app.config.get('CACHE_TIMEOUT', 3600),
        'max_connections': current_app.config.get('MAX_CONNECTIONS', 100),
        'query_timeout': current_app.config.get('QUERY_TIMEOUT', 30),
        'memory_limit': current_app.config.get('MEMORY_LIMIT', 512),

        'enable_caching': current_app.config.get('ENABLE_CACHING', True),
        'enable_compression': current_app.config.get('ENABLE_COMPRESSION', True),
        'enable_monitoring': current_app.config.get('ENABLE_MONITORING', True)
    }

    from datetime import datetime
    now = datetime.now()

    return render_template("system_config/performance_optimization.html",
                          system_stats=system_stats,
                          optimization_tools=optimization_tools,
                          settings=settings,
                          now=now)

@system_config.route("/performance/alertas", methods=["GET", "POST"])
@login_required
@admin_required
def system_alerts():
    """Configurar alertas de sistema"""
    if request.method == "POST":
        # Salvar configurações de alertas
        alert_email = request.form.get('alert_email', '')
        alert_frequency = request.form.get('alert_frequency', 'hourly')

        alert_system_errors = request.form.get('alert_system_errors') == 'on'
        alert_performance = request.form.get('alert_performance') == 'on'
        alert_disk_space = request.form.get('alert_disk_space') == 'on'
        alert_security = request.form.get('alert_security') == 'on'
        alert_database = request.form.get('alert_database') == 'on'
        alert_backup = request.form.get('alert_backup') == 'on'
        alert_network = request.form.get('alert_network') == 'on'
        alert_custom = request.form.get('alert_custom') == 'on'

        # Salvar configurações (simulado)
        current_app.config['ALERT_EMAIL'] = alert_email
        current_app.config['ALERT_FREQUENCY'] = alert_frequency

        current_app.config['ALERT_SYSTEM_ERRORS'] = alert_system_errors
        current_app.config['ALERT_PERFORMANCE'] = alert_performance
        current_app.config['ALERT_DISK_SPACE'] = alert_disk_space
        current_app.config['ALERT_SECURITY'] = alert_security
        current_app.config['ALERT_DATABASE'] = alert_database
        current_app.config['ALERT_BACKUP'] = alert_backup
        current_app.config['ALERT_NETWORK'] = alert_network
        current_app.config['ALERT_CUSTOM'] = alert_custom

        flash_success("Configurações de alertas salvas com sucesso!")
        return redirect(url_for('system_config.system_alerts'))

    # Dados simulados para o template
    alert_stats = {
        'system_status': 'active',
        'active_alerts': 8,
        'alerts_today': 2,
        'critical_alerts': 0
    }

    # Histórico de alertas simulados
    alert_history = [
        {
            'datetime': '17/10/2025 09:30',
            'type': 'performance',
            'description': 'CPU acima de 80% por mais de 5 minutos',
            'status': 'resolved'
        },
        {
            'datetime': '17/10/2025 08:15',
            'type': 'backup',
            'description': 'Backup diário concluído com sucesso',
            'status': 'resolved'
        },
        {
            'datetime': '16/10/2025 14:45',
            'type': 'error',
            'description': 'Falha na conexão com banco de dados',
            'status': 'resolved'
        },
        {
            'datetime': '16/10/2025 10:20',
            'type': 'disk',
            'description': 'Espaço em disco abaixo de 20%',
            'status': 'ongoing'
        }
    ]

    # Configurações atuais
    settings = {
        'alert_email': current_app.config.get('ALERT_EMAIL', 'admin@example.com'),
        'alert_frequency': current_app.config.get('ALERT_FREQUENCY', 'hourly'),

        'alert_system_errors': current_app.config.get('ALERT_SYSTEM_ERRORS', True),
        'alert_performance': current_app.config.get('ALERT_PERFORMANCE', True),
        'alert_disk_space': current_app.config.get('ALERT_DISK_SPACE', True),
        'alert_security': current_app.config.get('ALERT_SECURITY', True),
        'alert_database': current_app.config.get('ALERT_DATABASE', True),
        'alert_backup': current_app.config.get('ALERT_BACKUP', True),
        'alert_network': current_app.config.get('ALERT_NETWORK', False),
        'alert_custom': current_app.config.get('ALERT_CUSTOM', False)
    }

    from datetime import datetime
    now = datetime.now()

    return render_template("system_config/system_alerts.html",
                          alert_stats=alert_stats,
                          alert_history=alert_history,
                          settings=settings,
                          now=now)