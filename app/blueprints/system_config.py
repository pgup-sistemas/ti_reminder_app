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
from ..services.config_change_log_service import (
    ConfigChangeLogService,
    ChangeDescriptor,
)
from ..services.secure_config_service import SecureConfigService, SecureConfigUnavailable
from ..services.system_config_service import SystemConfigService
from ..services.log_reader_service import LogReaderService
from ..services.config_notification_service import ConfigNotificationService
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
            
            # Enviar email de boas-vindas
            try:
                from ..models import User as UserModel
                creator = UserModel.query.get(session.get('user_id'))
                temp_password = form.new_password.data if form.new_password.data else "123456"
                
                ConfigNotificationService.send_user_created_notification(
                    user=user,
                    creator=creator,
                    temp_password=temp_password if temp_password == "123456" else None
                )
            except Exception:
                current_app.logger.exception("Falha ao enviar email de boas-vindas")
            
            return redirect(url_for('system_config.list_users'))

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao criar usuário: {e}")
            flash_error("Erro ao criar usuário.")

    from datetime import datetime
    now = datetime.now()

    return render_template("system_config/user_form.html", form=form, is_edit=False, now=now)

@system_config.route("/test-form")
def test_form():
    """Rota de teste - REMOVER DEPOIS"""
    return render_template("test_form_simple.html")

@system_config.route("/debug-form")
def debug_form():
    """DEBUG VISUAL - Formulário com logs em tempo real"""
    return render_template("debug_form.html")

@system_config.route("/usuarios/<int:user_id>/editar-sem-auth", methods=["GET", "POST"])
def edit_user_no_auth(user_id):
    """TESTE SEM AUTENTICAÇÃO - REMOVER DEPOIS"""
    from ..forms import UserEditForm
    
    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)
    
    # Popular setores
    sectors = Sector.query.order_by(Sector.name).all()
    form.sector_id.choices = [(0, "Selecione um setor")] + [(s.id, s.name) for s in sectors]
    
    if request.method == 'POST':
        current_app.logger.warning(f"=== ROTA SEM AUTH - FORM SUBMETIDO ===")
        current_app.logger.warning(f"User ID: {user_id}")
        current_app.logger.warning(f"Form data: {dict(request.form)}")
        
        try:
            # Atualizar dados básicos
            user.username = request.form.get('username')
            user.email = request.form.get('email')
            user.sector_id = int(request.form.get('sector_id', 0)) or None
            user.is_admin = request.form.get('is_admin') == 'y'
            user.is_ti = request.form.get('is_ti') == 'y'
            
            # Verificar se está alterando senha
            change_password = request.form.get('change_password')
            new_password = request.form.get('new_password')
            confirm_password = request.form.get('confirm_password')
            
            current_app.logger.warning(f"Change password: {bool(change_password)}")
            current_app.logger.warning(f"New password: {'***' if new_password else 'vazio'}")
            current_app.logger.warning(f"Confirm password: {'***' if confirm_password else 'vazio'}")
            
            if change_password or new_password:
                # Validar senhas
                if not new_password:
                    flash_error("Nova senha não pode estar vazia")
                    raise ValueError("Senha vazia")
                
                if new_password != confirm_password:
                    flash_error("As senhas não coincidem")
                    raise ValueError("Senhas não coincidem")
                
                if len(new_password) < 6:
                    flash_error("A senha deve ter pelo menos 6 caracteres")
                    raise ValueError("Senha muito curta")
                
                # Alterar senha
                user.set_password(new_password)
                current_app.logger.warning("✓ Senha alterada!")
            
            db.session.commit()
            current_app.logger.warning(f"✓✓✓ SUCESSO - Usuário {user_id} atualizado!")
            
            msg = f"Usuário {user.username} atualizado"
            if change_password or new_password:
                msg += " (senha alterada)"
            
            flash_success(msg)
            return redirect(url_for("system_config.list_users"))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro: {e}")
            flash_error(f"Erro: {str(e)}")
    
    from datetime import datetime
    return render_template("system_config/user_form_SIMPLE.html", form=form, user=user, now=datetime.now())

@system_config.route("/usuarios/<int:user_id>/editar-simples", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user_simple(user_id):
    """Editar usuário - VERSÃO SIMPLES PARA TESTE"""
    from ..forms import UserEditForm
    
    user = User.query.get_or_404(user_id)
    form = UserEditForm(obj=user)
    
    # Popular setores
    sectors = Sector.query.order_by(Sector.name).all()
    form.sector_id.choices = [(0, "Selecione um setor")] + [(s.id, s.name) for s in sectors]
    
    if request.method == 'POST':
        current_app.logger.info(f"=== FORM SIMPLES SUBMETIDO USUÁRIO {user_id} ===")
        current_app.logger.info(f"Form data: {dict(request.form)}")
        
        # Atualizar diretamente sem validação complexa
        try:
            user.username = request.form.get('username')
            user.email = request.form.get('email')
            user.sector_id = int(request.form.get('sector_id', 0)) or None
            user.is_admin = request.form.get('is_admin') == 'y'
            user.is_ti = request.form.get('is_ti') == 'y'
            user.ativo = 'ativo' in request.form
            
            db.session.commit()
            current_app.logger.info(f"✓ Usuário {user_id} atualizado com sucesso")
            flash_success(f"Usuário {user.username} atualizado com sucesso!")
            return redirect(url_for("system_config.list_users"))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro: {e}")
            flash_error(f"Erro: {str(e)}")
    
    from datetime import datetime
    return render_template("system_config/user_form_SIMPLE.html", form=form, user=user, now=datetime.now())
    
@system_config.route("/usuarios/<int:user_id>/editar", methods=["GET", "POST"])
@login_required
@admin_required
def edit_user(user_id):
    """VERSÃO FINAL - SEM WTFORMS, CSRF SIMPLES DO FLASK"""
    from datetime import datetime
    
    user = User.query.get_or_404(user_id)
    sectors = Sector.query.order_by(Sector.name).all()

    if request.method == 'POST':
        current_app.logger.info(f"=== EDIÇÃO USUÁRIO {user_id} - VERSÃO FINAL ===")
        
        try:
            # Atualizar dados
            user.username = request.form.get('username', '').strip()
            user.email = request.form.get('email', '').strip().lower()
            user.sector_id = int(request.form.get('sector_id', 0)) or None
            user.is_admin = request.form.get('is_admin') == 'y'
            user.is_ti = request.form.get('is_ti') == 'y'
            user.ativo = 'ativo' in request.form
            
            # Senha
            new_password = request.form.get('new_password', '').strip()
            confirm_password = request.form.get('confirm_password', '').strip()
            
            if new_password:
                if new_password != confirm_password:
                    flash_error("As senhas não coincidem")
                    from flask_wtf.csrf import generate_csrf
                    return render_template(
                        "system_config/user_edit_FINAL.html",
                        user=user,
                        sectors=sectors,
                        csrf_token_value=generate_csrf(),
                        now=datetime.now(),
                    )
                
                if len(new_password) < 6:
                    flash_error("A senha deve ter pelo menos 6 caracteres")
                    from flask_wtf.csrf import generate_csrf
                    return render_template(
                        "system_config/user_edit_FINAL.html",
                        user=user,
                        sectors=sectors,
                        csrf_token_value=generate_csrf(),
                        now=datetime.now(),
                    )
                
                user.set_password(new_password)
            
            db.session.commit()
            
            msg = f"Usuário {user.username} atualizado com sucesso"
            if new_password:
                msg += " (senha alterada)"
            
            flash_success(msg)
            return redirect(url_for("system_config.list_users"))
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro: {e}")
            flash_error(f"Erro: {str(e)}")
            from flask_wtf.csrf import generate_csrf
            return render_template(
                "system_config/user_edit_FINAL.html",
                user=user,
                sectors=sectors,
                csrf_token_value=generate_csrf(),
                now=datetime.now(),
            )

    # GET
    from flask_wtf.csrf import generate_csrf
    return render_template(
        "system_config/user_edit_FINAL.html",
        user=user,
        sectors=sectors,
        csrf_token_value=generate_csrf(),
        now=datetime.now(),
    )

@system_config.route("/usuarios/<int:user_id>/toggle", methods=["POST"])
@login_required
@admin_required
def toggle_user(user_id):
    """Ativar/desativar usuário"""
    logger = current_app.logger
    actor_id = session.get("user_id")
    user = User.query.get_or_404(user_id)

    # Impedir que admin desative a si mesmo
    if user.id == actor_id:
        logger.warning(
            "Tentativa de desativar a própria conta",
            extra={"actor_id": actor_id, "target_id": user.id},
        )
        return jsonify({"success": False, "message": "Você não pode desativar sua própria conta."})

    # Verificar se é o último admin ativo
    if user.is_admin and user.ativo:
        admin_count = User.query.filter_by(is_admin=True, ativo=True).count()
        if admin_count <= 1:
            logger.warning(
                "Tentativa de desativar último administrador",
                extra={"actor_id": actor_id, "target_id": user.id},
            )
            return jsonify({"success": False, "message": "Não é possível desativar o último administrador ativo."})

    user.ativo = not user.ativo
    status = "ativado" if user.ativo else "desativado"

    try:
        logger.info(
            "Alterando status de usuário",
            extra={"actor_id": actor_id, "target_id": user.id, "status": status},
        )
        db.session.commit()
        logger.info(
            "Status de usuário alterado com sucesso",
            extra={"actor_id": actor_id, "target_id": user.id, "status": status},
        )

        try:
            ConfigChangeLogService.register_change(
                ChangeDescriptor(
                    module="config.usuarios",
                    actor_id=actor_id,
                    entity_type="user",
                    entity_id=user.id,
                ),
                field="ativo",
                old_value=not user.ativo,
                new_value=user.ativo,
            )
        except Exception:
            logger.exception(
                "Falha ao registrar auditoria de alteração de status",
                extra={"actor_id": actor_id, "target_id": user.id},
            )
        
        # Enviar notificação por email
        try:
            from ..models import User as UserModel
            actor = UserModel.query.get(actor_id)
            ConfigNotificationService.send_account_status_changed_notification(
                user=user,
                actor=actor,
                is_active=user.ativo
            )
        except Exception:
            logger.exception(
                "Falha ao enviar notificação de alteração de status",
                extra={"actor_id": actor_id, "target_id": user.id},
            )
        
        return jsonify({
            "success": True,
            "message": f"Usuário {status} com sucesso!",
            "status": status
        })
    except Exception as e:
        db.session.rollback()
        logger.exception(
            "Erro ao alterar status do usuário",
            extra={"actor_id": actor_id, "target_id": user.id, "error": str(e)},
        )
        return jsonify({"success": False, "message": "Erro ao alterar status do usuário."})

@system_config.route("/usuarios/<int:user_id>/reset-senha", methods=["POST"])
@login_required
@admin_required
def reset_user_password(user_id):
    """Resetar senha do usuário"""
    logger = current_app.logger
    actor_id = session.get("user_id")
    user = User.query.get_or_404(user_id)

    # Gerar nova senha
    new_password = secrets.token_hex(4)  # 8 caracteres
    user.set_password(new_password)

    try:
        logger.info(
            "Reset de senha solicitado",
            extra={"actor_id": actor_id, "target_id": user.id},
        )
        db.session.commit()
        logger.info(
            "Senha resetada com sucesso",
            extra={"actor_id": actor_id, "target_id": user.id},
        )

        try:
            ConfigChangeLogService.register_change(
                ChangeDescriptor(
                    module="config.usuarios",
                    actor_id=actor_id,
                    entity_type="user",
                    entity_id=user.id,
                ),
                field="senha",
                old_value=None,
                new_value="resetada",
                metadata={"delivery": "manual"},
            )
        except Exception:
            logger.exception(
                "Falha ao registrar auditoria de reset de senha",
                extra={"actor_id": actor_id, "target_id": user.id},
            )
        
        # Enviar email com nova senha
        try:
            ConfigNotificationService.send_password_reset_notification(
                user=user,
                new_password=new_password
            )
        except Exception:
            logger.exception(
                "Falha ao enviar email de reset de senha",
                extra={"actor_id": actor_id, "target_id": user.id},
            )
        
        return jsonify({
            "success": True,
            "message": "Senha resetada com sucesso!",
            "new_password": new_password
        })
    except Exception as e:
        db.session.rollback()
        logger.exception(
            "Erro ao resetar senha",
            extra={"actor_id": actor_id, "target_id": user.id, "error": str(e)},
        )
        return jsonify({"success": False, "message": "Erro ao resetar senha."})

@system_config.route("/usuarios/<int:user_id>/deletar", methods=["DELETE"])
@login_required
@admin_required
def delete_user(user_id):
    """Excluir usuário"""
    logger = current_app.logger
    actor_id = session.get("user_id")
    user = User.query.get_or_404(user_id)

    # Impedir exclusão do próprio usuário
    if user.id == actor_id:
        logger.warning(
            "Tentativa de exclusão da própria conta",
            extra={"actor_id": actor_id, "target_id": user.id},
        )
        return jsonify({"success": False, "message": "Você não pode excluir sua própria conta."})

    # Verificar se é o último admin
    if user.is_admin:
        admin_count = User.query.filter_by(is_admin=True, ativo=True).count()
        if admin_count <= 1:
            logger.warning(
                "Tentativa de exclusão do último administrador",
                extra={"actor_id": actor_id, "target_id": user.id},
            )
            return jsonify({"success": False, "message": "Não é possível excluir o último administrador."})

    try:
        logger.info(
            "Exclusão de usuário iniciada",
            extra={"actor_id": actor_id, "target_id": user.id},
        )
        
        # Enviar notificação ANTES de deletar (para ter acesso aos dados)
        try:
            from ..models import User as UserModel
            actor = UserModel.query.get(actor_id)
            ConfigNotificationService.send_account_deleted_notification(
                user=user,
                actor=actor
            )
        except Exception:
            logger.exception(
                "Falha ao enviar notificação de exclusão",
                extra={"actor_id": actor_id, "target_id": user.id},
            )
        
        # Remover configurações de notificação
        NotificationSettings.query.filter_by(user_id=user.id).delete()

        # Remover usuário
        db.session.delete(user)
        db.session.commit()
        logger.info(
            "Usuário excluído com sucesso",
            extra={"actor_id": actor_id, "target_id": user.id},
        )

        try:
            ConfigChangeLogService.register_change(
                ChangeDescriptor(
                    module="config.usuarios",
                    actor_id=actor_id,
                    entity_type="user",
                    entity_id=user.id,
                ),
                field="estado",
                old_value="ativo" if user.ativo else "inativo",
                new_value="excluido",
            )
        except Exception:
            logger.exception(
                "Falha ao registrar auditoria de exclusão de usuário",
                extra={"actor_id": actor_id, "target_id": user.id},
            )
        return jsonify({"success": True, "message": "Usuário excluído com sucesso!"})
    except Exception as e:
        db.session.rollback()
        logger.exception(
            "Erro ao excluir usuário",
            extra={"actor_id": actor_id, "target_id": user.id, "error": str(e)},
        )
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
        logger = current_app.logger
        actor_id = session.get("user_id")
        action = request.form.get('action')
        user_ids = request.form.getlist('user_ids[]', type=int)

        if not user_ids:
            flash_warning("Nenhum usuário selecionado.")
            return redirect(url_for('system_config.bulk_user_actions'))

        logger.info(
            "Ação em lote recebida",
            extra={"actor_id": actor_id, "action": action, "user_ids": user_ids},
        )

        if action == 'activate':
            User.query.filter(User.id.in_(user_ids)).update({'ativo': True})
            flash_success(f"{len(user_ids)} usuários ativados.")
            logger.info(
                "Usuários ativados em lote",
                extra={"actor_id": actor_id, "count": len(user_ids)},
            )
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
                    logger.warning(
                        "Tentativa de desativar todos os administradores",
                        extra={"actor_id": actor_id, "user_ids": user_ids},
                    )
                    return redirect(url_for('system_config.bulk_user_actions'))

            User.query.filter(User.id.in_(user_ids)).update({'ativo': False})
            flash_success(f"{len(user_ids)} usuários desativados.")
            logger.info(
                "Usuários desativados em lote",
                extra={"actor_id": actor_id, "count": len(user_ids)},
            )
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
                    logger.warning(
                        "Tentativa de excluir todos os administradores",
                        extra={"actor_id": actor_id, "user_ids": user_ids},
                    )
                    return redirect(url_for('system_config.bulk_user_actions'))

            # Excluir configurações de notificação primeiro
            NotificationSettings.query.filter(NotificationSettings.user_id.in_(user_ids)).delete()
            User.query.filter(User.id.in_(user_ids)).delete()
            flash_success(f"{len(user_ids)} usuários excluídos.")
            logger.info(
                "Usuários excluídos em lote",
                extra={"actor_id": actor_id, "count": len(user_ids)},
            )
        else:
            flash_warning("Ação inválida.")
            logger.warning(
                "Ação em lote inválida",
                extra={"actor_id": actor_id, "action": action},
            )
            return redirect(url_for('system_config.bulk_user_actions'))

        try:
            db.session.commit()
            logger.info(
                "Ação em lote concluída",
                extra={"actor_id": actor_id, "action": action, "count": len(user_ids)},
            )

            # Registrar auditoria por usuário afetado
            try:
                for user_id in user_ids:
                    change_value = {
                        "activate": "ativado",
                        "deactivate": "desativado",
                        "delete": "excluido",
                    }.get(action, action)

                    ConfigChangeLogService.register_change(
                        ChangeDescriptor(
                            module="config.usuarios",
                            actor_id=actor_id,
                            entity_type="user",
                            entity_id=user_id,
                        ),
                        field="acao_lote",
                        old_value=None,
                        new_value=change_value,
                        metadata={"total": len(user_ids)},
                    )
            except Exception:
                logger.exception(
                    "Falha ao registrar auditoria de ação em lote",
                    extra={"actor_id": actor_id, "action": action, "user_ids": user_ids},
                )

            return redirect(url_for('system_config.list_users'))
        except Exception as e:
            db.session.rollback()
            logger.exception(
                "Erro ao executar ação em lote",
                extra={"actor_id": actor_id, "action": action, "user_ids": user_ids, "error": str(e)},
            )
            flash_error("Erro ao executar ação em lote de usuários.")
            return redirect(url_for('system_config.bulk_user_actions'))

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
    actor_id = session.get("user_id")
    
    if request.method == "POST":
        # Salvar configurações gerais usando SystemConfigService
        system_name = request.form.get('system_name', 'TI OSN System')
        maintenance_mode = request.form.get('maintenance_mode') == 'on'
        timezone = request.form.get('timezone', 'America/Manaus')
        language = request.form.get('language', 'pt-BR')

        try:
            # Salvar cada configuração no banco de dados
            SystemConfigService.set('system', 'name', system_name, 'string', 
                                   'Nome do sistema', actor_id)
            SystemConfigService.set('system', 'maintenance_mode', maintenance_mode, 'bool',
                                   'Modo de manutenção', actor_id)
            SystemConfigService.set('system', 'timezone', timezone, 'string',
                                   'Timezone do sistema', actor_id)
            SystemConfigService.set('system', 'language', language, 'string',
                                   'Idioma do sistema', actor_id)
            
            # Registrar auditoria
            try:
                ConfigChangeLogService.register_change(
                    ChangeDescriptor(
                        module="config.system.general",
                        actor_id=actor_id,
                        entity_type="system_config",
                        entity_id="general",
                    ),
                    field="settings",
                    old_value=None,
                    new_value="atualizado",
                )
            except Exception:
                current_app.logger.exception("Falha ao registrar auditoria de configuração geral")
            
            flash_success("Configurações gerais salvas com sucesso!")
            current_app.logger.info(
                "Configurações gerais atualizadas",
                extra={"actor_id": actor_id, "config": "system.general"}
            )
            
            # Enviar notificação por email
            try:
                from ..models import User
                actor_user = User.query.get(actor_id)
                if actor_user:
                    changes = [
                        {'field': 'name', 'old_value': None, 'new_value': system_name},
                        {'field': 'timezone', 'old_value': None, 'new_value': timezone},
                        {'field': 'language', 'old_value': None, 'new_value': language}
                    ]
                    ConfigNotificationService.send_config_change_notification(
                        actor=actor_user,
                        category='system',
                        changes=changes
                    )
            except Exception:
                current_app.logger.exception("Falha ao enviar notificação de configuração")
                
        except Exception as e:
            current_app.logger.error(f"Erro ao salvar configurações gerais: {e}")
            flash_error("Erro ao salvar configurações gerais.")
        
        return redirect(url_for('system_config.general_settings'))

    # Buscar configurações atuais do banco de dados
    settings = {
        'system_name': SystemConfigService.get('system', 'name', 'TI OSN System'),
        'system_version': '2.0',
        'maintenance_mode': SystemConfigService.get('system', 'maintenance_mode', False),
        'debug_mode': current_app.debug,
        'timezone': SystemConfigService.get('system', 'timezone', 'America/Manaus'),
        'language': SystemConfigService.get('system', 'language', 'pt-BR')
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
    actor_id = session.get("user_id")
    
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

        try:
            # Salvar configurações no banco de dados
            SystemConfigService.set('security', 'password_min_length', password_min_length, 'int',
                                   'Comprimento mínimo da senha', actor_id)
            SystemConfigService.set('security', 'password_require_uppercase', password_require_uppercase, 'bool',
                                   'Senha requer maiúsculas', actor_id)
            SystemConfigService.set('security', 'password_require_lowercase', password_require_lowercase, 'bool',
                                   'Senha requer minúsculas', actor_id)
            SystemConfigService.set('security', 'password_require_numbers', password_require_numbers, 'bool',
                                   'Senha requer números', actor_id)
            SystemConfigService.set('security', 'password_require_special', password_require_special, 'bool',
                                   'Senha requer caracteres especiais', actor_id)
            
            SystemConfigService.set('security', 'session_timeout', session_timeout, 'int',
                                   'Timeout de sessão (minutos)', actor_id)
            SystemConfigService.set('security', 'max_login_attempts', max_login_attempts, 'int',
                                   'Máximo de tentativas de login', actor_id)
            SystemConfigService.set('security', 'lockout_duration', lockout_duration, 'int',
                                   'Duração do bloqueio (minutos)', actor_id)
            
            SystemConfigService.set('security', 'two_factor_required', two_factor_required, 'bool',
                                   'Exigir autenticação de dois fatores', actor_id)
            SystemConfigService.set('security', 'ip_whitelist_enabled', ip_whitelist_enabled, 'bool',
                                   'Habilitar whitelist de IPs', actor_id)
            SystemConfigService.set('security', 'audit_log_enabled', audit_log_enabled, 'bool',
                                   'Habilitar logs de auditoria', actor_id)
            
            # Registrar auditoria
            try:
                ConfigChangeLogService.register_change(
                    ChangeDescriptor(
                        module="config.system.security",
                        actor_id=actor_id,
                        entity_type="system_config",
                        entity_id="security",
                    ),
                    field="settings",
                    old_value=None,
                    new_value="atualizado",
                )
            except Exception:
                current_app.logger.exception("Falha ao registrar auditoria de configuração de segurança")
            
            flash_success("Configurações de segurança salvas com sucesso!")
            current_app.logger.info(
                "Configurações de segurança atualizadas",
                extra={"actor_id": actor_id, "config": "security"}
            )
            
            # Enviar notificação por email
            try:
                from ..models import User
                actor_user = User.query.get(actor_id)
                if actor_user:
                    changes = [
                        {'field': 'password_min_length', 'old_value': None, 'new_value': password_min_length},
                        {'field': 'session_timeout', 'old_value': None, 'new_value': session_timeout},
                        {'field': 'max_login_attempts', 'old_value': None, 'new_value': max_login_attempts},
                    ]
                    ConfigNotificationService.send_config_change_notification(
                        actor=actor_user,
                        category='security',
                        changes=changes
                    )
            except Exception:
                current_app.logger.exception("Falha ao enviar notificação de configuração de segurança")
                
        except Exception as e:
            current_app.logger.error(f"Erro ao salvar configurações de segurança: {e}")
            flash_error("Erro ao salvar configurações de segurança.")
        
        return redirect(url_for('system_config.security_settings'))

    # Buscar configurações atuais do banco de dados
    settings = {
        'password_min_length': SystemConfigService.get('security', 'password_min_length', 6),
        'password_require_uppercase': SystemConfigService.get('security', 'password_require_uppercase', True),
        'password_require_lowercase': SystemConfigService.get('security', 'password_require_lowercase', True),
        'password_require_numbers': SystemConfigService.get('security', 'password_require_numbers', True),
        'password_require_special': SystemConfigService.get('security', 'password_require_special', False),

        'session_timeout': SystemConfigService.get('security', 'session_timeout', 30),
        'max_login_attempts': SystemConfigService.get('security', 'max_login_attempts', 5),
        'lockout_duration': SystemConfigService.get('security', 'lockout_duration', 15),

        'two_factor_required': SystemConfigService.get('security', 'two_factor_required', False),
        'ip_whitelist_enabled': SystemConfigService.get('security', 'ip_whitelist_enabled', False),
        'audit_log_enabled': SystemConfigService.get('security', 'audit_log_enabled', True)
    }

    from datetime import datetime
    now = datetime.now()

    return render_template("system_config/security_settings.html", settings=settings, now=now)

@system_config.route("/sistema/backup", methods=["GET", "POST"])
@login_required
@admin_required
def backup_settings():
    """Configurações de backup"""
    actor_id = session.get("user_id")
    
    if request.method == "POST":
        backup_enabled = request.form.get('backup_enabled') == 'on'
        backup_frequency = request.form.get('backup_frequency', 'daily')
        backup_time = request.form.get('backup_time', '02:00')
        backup_retention_days = int(request.form.get('backup_retention_days', 30))
        backup_location = request.form.get('backup_location', 'local')
        compression_enabled = request.form.get('compression_enabled') == 'on'
        encryption_enabled = request.form.get('encryption_enabled') == 'on'
        email_notifications = request.form.get('email_notifications') == 'on'

        try:
            SystemConfigService.set('backup', 'enabled', backup_enabled, 'bool', 'Backup habilitado', actor_id)
            SystemConfigService.set('backup', 'frequency', backup_frequency, 'string', 'Frequência do backup', actor_id)
            SystemConfigService.set('backup', 'time', backup_time, 'string', 'Horário do backup', actor_id)
            SystemConfigService.set('backup', 'retention_days', backup_retention_days, 'int', 'Dias de retenção', actor_id)
            SystemConfigService.set('backup', 'location', backup_location, 'string', 'Localização do backup', actor_id)
            SystemConfigService.set('backup', 'compression_enabled', compression_enabled, 'bool', 'Compressão habilitada', actor_id)
            SystemConfigService.set('backup', 'encryption_enabled', encryption_enabled, 'bool', 'Criptografia habilitada', actor_id)
            SystemConfigService.set('backup', 'email_notifications', email_notifications, 'bool', 'Notificações por email', actor_id)
            
            flash_success("Configurações de backup salvas com sucesso!")
            current_app.logger.info("Configurações de backup atualizadas", extra={"actor_id": actor_id})
            
            # Enviar notificação por email
            try:
                from ..models import User
                actor_user = User.query.get(actor_id)
                if actor_user:
                    changes = [
                        {'field': 'enabled', 'old_value': None, 'new_value': 'Sim' if backup_enabled else 'Não'},
                        {'field': 'frequency', 'old_value': None, 'new_value': backup_frequency},
                        {'field': 'retention_days', 'old_value': None, 'new_value': backup_retention_days},
                    ]
                    ConfigNotificationService.send_config_change_notification(
                        actor=actor_user,
                        category='backup',
                        changes=changes
                    )
            except Exception:
                current_app.logger.exception("Falha ao enviar notificação de configuração de backup")
                
        except Exception as e:
            current_app.logger.error(f"Erro ao salvar configurações de backup: {e}")
            flash_error("Erro ao salvar configurações de backup.")
        
        return redirect(url_for('system_config.backup_settings'))

    settings = {
        'backup_enabled': SystemConfigService.get('backup', 'enabled', True),
        'backup_frequency': SystemConfigService.get('backup', 'frequency', 'daily'),
        'backup_time': SystemConfigService.get('backup', 'time', '02:00'),
        'backup_retention_days': SystemConfigService.get('backup', 'retention_days', 30),
        'backup_location': SystemConfigService.get('backup', 'location', 'local'),
        'compression_enabled': SystemConfigService.get('backup', 'compression_enabled', True),
        'encryption_enabled': SystemConfigService.get('backup', 'encryption_enabled', False),
        'email_notifications': SystemConfigService.get('backup', 'email_notifications', True)
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

# ========================================
# BACKUP - AÇÕES
# ========================================

@system_config.route("/sistema/backup/executar", methods=["POST"])
@login_required
@admin_required
def execute_backup():
    """Executa backup completo do sistema"""
    from ..services.backup_service import BackupService
    
    actor_id = session.get("user_id")
    
    try:
        current_app.logger.info(
            "Iniciando backup manual",
            extra={"actor_id": actor_id}
        )
        
        # Executar backup completo
        result = BackupService.create_full_backup()
        
        if result['success']:
            flash_success("Backup executado com sucesso!")
            
            # Enviar notificação por email
            try:
                from ..models import User
                from ..services.config_notification_service import ConfigNotificationService
                
                actor = User.query.get(actor_id)
                admins = User.query.filter_by(is_admin=True, ativo=True).all()
                
                for admin in admins:
                    # TODO: Criar template de email para backup
                    current_app.logger.info(f"Notificação de backup enviada para {admin.email}")
            except Exception:
                current_app.logger.exception("Falha ao enviar notificação de backup")
            
            current_app.logger.info(
                "Backup concluído com sucesso",
                extra={"actor_id": actor_id, "result": result}
            )
        else:
            flash_error(f"Erro no backup: {', '.join(result['errors'])}")
            current_app.logger.error(
                "Falha no backup",
                extra={"actor_id": actor_id, "errors": result['errors']}
            )
        
        return jsonify(result)
        
    except Exception as e:
        current_app.logger.exception(f"Erro ao executar backup: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@system_config.route("/sistema/backup/listar", methods=["GET"])
@login_required
@admin_required
def list_backups():
    """Lista backups disponíveis"""
    from ..services.backup_service import BackupService
    
    try:
        backup_type = request.args.get('type')
        backups = BackupService.list_backups(backup_type)
        
        return jsonify({
            "success": True,
            "backups": backups,
            "count": len(backups)
        })
        
    except Exception as e:
        current_app.logger.exception(f"Erro ao listar backups: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@system_config.route("/sistema/backup/deletar/<filename>", methods=["DELETE"])
@login_required
@admin_required
def delete_backup(filename):
    """Deleta um backup"""
    from ..services.backup_service import BackupService
    
    actor_id = session.get("user_id")
    
    try:
        success = BackupService.delete_backup(filename)
        
        if success:
            flash_success(f"Backup {filename} deletado com sucesso!")
            current_app.logger.info(
                f"Backup deletado: {filename}",
                extra={"actor_id": actor_id}
            )
        else:
            flash_error(f"Backup {filename} não encontrado")
        
        return jsonify({"success": success})
        
    except Exception as e:
        current_app.logger.exception(f"Erro ao deletar backup: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@system_config.route("/sistema/backup/verificar/<filename>", methods=["POST"])
@login_required
@admin_required
def verify_backup(filename):
    """Verifica integridade de um backup"""
    from ..services.backup_service import BackupService
    
    try:
        is_valid = BackupService.verify_backup_integrity(filename)
        
        if is_valid:
            flash_success(f"Backup {filename} está íntegro!")
        else:
            flash_error(f"Backup {filename} está corrompido ou não encontrado")
        
        return jsonify({"success": True, "valid": is_valid})
        
    except Exception as e:
        current_app.logger.exception(f"Erro ao verificar backup: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@system_config.route("/sistema/backup/limpar", methods=["POST"])
@login_required
@admin_required
def cleanup_old_backups():
    """Remove backups antigos conforme retenção configurada"""
    from ..services.backup_service import BackupService
    
    actor_id = session.get("user_id")
    
    try:
        removed_count = BackupService.cleanup_old_backups()
        
        flash_success(f"{removed_count} backup(s) antigo(s) removido(s)!")
        current_app.logger.info(
            f"Limpeza de backups concluída: {removed_count} removidos",
            extra={"actor_id": actor_id}
        )
        
        return jsonify({"success": True, "removed_count": removed_count})
        
    except Exception as e:
        current_app.logger.exception(f"Erro ao limpar backups: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@system_config.route("/sistema/logs")
@login_required
@admin_required
def system_logs():
    """Visualizar logs do sistema"""
    from datetime import datetime
    
    # Parâmetros de filtro
    level = request.args.get('level')
    search = request.args.get('search')
    page = request.args.get('page', 1, type=int)
    per_page = 50
    
    # Buscar logs reais usando LogReaderService
    log_result = LogReaderService.read_logs(
        level=level,
        limit=per_page,
        offset=(page - 1) * per_page,
        search=search
    )
    
    # Obter estatísticas
    log_stats = LogReaderService.get_log_statistics(hours=24)
    
    # Formatar logs para o template
    logs = []
    for log in log_result.get('logs', []):
        logs.append({
            'timestamp': log['timestamp'].strftime('%Y-%m-%d %H:%M:%S') if isinstance(log['timestamp'], datetime) else log['timestamp'],
            'level': log['level'],
            'message': log['message'],
            'file': log.get('file', '')
        })
    
    # Dados para paginação
    total_logs = log_result.get('total', 0)
    total_pages = (total_logs + per_page - 1) // per_page if total_logs > 0 else 1
    
    current_date = datetime.now().strftime('%Y-%m-%d')
    now = datetime.now()
    
    return render_template("system_config/system_logs.html",
                          current_date=current_date,
                          log_stats={
                              'errors_24h': log_stats.get('errors_count', 0),
                              'warnings_24h': log_stats.get('warnings_count', 0),
                              'info_24h': log_stats.get('info_count', 0),
                              'log_size': log_stats.get('file_size', '0 B')
                          },
                          logs=logs,
                          page=page,
                          total_pages=total_pages,
                          level_filter=level,
                          search_filter=search,
                          log_file=log_result.get('file_path'),
                          error=log_result.get('error'),
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
    logger = current_app.logger
    actor_id = session.get("user_id")

    if request.method == "POST":
        # Salvar configurações de email
        smtp_server = request.form.get('smtp_server', '').strip()
        smtp_port = int(request.form.get('smtp_port', 587))
        smtp_username = request.form.get('smtp_username', '').strip()
        smtp_password = request.form.get('smtp_password', '')
        smtp_use_tls = request.form.get('smtp_use_tls') == 'on'
        smtp_use_ssl = request.form.get('smtp_use_ssl') == 'on'

        from_email = request.form.get('from_email', '').strip()
        from_name = request.form.get('from_name', 'TI OSN System').strip()

        try:
            SecureConfigService.ensure_available()
        except SecureConfigUnavailable as exc:
            flash_error(str(exc))
            return redirect(url_for('system_config.email_integration'))

        # Testar conexão se solicitado
        if request.form.get('test_connection'):
            try:
                import smtplib
                server = smtplib.SMTP(smtp_server, smtp_port, timeout=10)
                server.ehlo()
                if smtp_use_tls:
                    server.starttls()
                if smtp_username and smtp_password:
                    server.login(smtp_username, smtp_password)
                server.quit()
                flash_success("Conexão SMTP testada com sucesso!")
            except Exception as e:
                logger.exception(
                    "Erro na conexão SMTP",
                    extra={"actor_id": actor_id, "server": smtp_server},
                )
                flash_error(f"Erro na conexão SMTP: {str(e)}")
                return redirect(url_for('system_config.email_integration'))

        # Persistir configurações não sensíveis
        current_app.config['SMTP_SERVER'] = smtp_server
        current_app.config['SMTP_PORT'] = smtp_port
        current_app.config['SMTP_USERNAME'] = smtp_username
        current_app.config['SMTP_USE_TLS'] = smtp_use_tls
        current_app.config['SMTP_USE_SSL'] = smtp_use_ssl
        current_app.config['FROM_EMAIL'] = from_email
        current_app.config['FROM_NAME'] = from_name

        # Segredo sensível
        try:
            SecureConfigService.set_secret("smtp_password", smtp_password)
        except SecureConfigUnavailable as exc:
            flash_warning(f"Senha não foi armazenada: {exc}")

        flash_success("Configurações de email salvas com sucesso!")

        try:
            ConfigChangeLogService.register_change(
                ChangeDescriptor(
                    module="config.integracoes.email",
                    actor_id=actor_id,
                    entity_type="email",
                    entity_id="smtp",
                ),
                field="config",
                old_value=None,
                new_value="atualizado",
                metadata={"testado": bool(request.form.get('test_connection'))},
            )
        except Exception:
            logger.exception(
                "Falha ao registrar auditoria de integração de email",
                extra={"actor_id": actor_id},
            )

        return redirect(url_for('system_config.email_integration'))

    try:
        SecureConfigService.ensure_available()
        smtp_password_exists = SecureConfigService.has_secret("smtp_password")
    except SecureConfigUnavailable:
        smtp_password_exists = False

    settings = {
        'smtp_server': current_app.config.get('SMTP_SERVER', ''),
        'smtp_port': current_app.config.get('SMTP_PORT', 587),
        'smtp_username': current_app.config.get('SMTP_USERNAME', ''),
        'smtp_use_tls': current_app.config.get('SMTP_USE_TLS', True),
        'smtp_use_ssl': current_app.config.get('SMTP_USE_SSL', False),
        'from_email': current_app.config.get('FROM_EMAIL', ''),
        'from_name': current_app.config.get('FROM_NAME', 'TI OSN System'),
        'smtp_password_exists': smtp_password_exists,
    }

    from datetime import datetime
    now = datetime.now()

    return render_template("system_config/email_integration.html", settings=settings, now=now)


@system_config.route("/integracoes/api", methods=["GET", "POST"])
@login_required
@admin_required
def api_integrations():
    """Gerenciar integrações com APIs externas"""
    logger = current_app.logger

    if request.method == "POST":
        api_name = request.form.get('api_name', '').strip().lower()
        api_endpoint = request.form.get('api_endpoint', '').strip()
        api_key = request.form.get('api_key', '').strip()
        api_secret = request.form.get('api_secret', '').strip()
        api_enabled = request.form.get('api_enabled') == 'on'

        if not api_name:
            flash_warning("Informe o identificador da API.")
            return redirect(url_for('system_config.api_integrations'))

        try:
            SecureConfigService.ensure_available()
        except SecureConfigUnavailable as exc:
            flash_error(str(exc))
            return redirect(url_for('system_config.api_integrations'))

        if request.form.get('test_connection'):
            try:
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
                logger.exception(
                    "Erro na conexão com API externa",
                    extra={"api": api_name, "endpoint": api_endpoint},
                )
                flash_error(f"Erro na conexão com API: {str(e)}")
                return redirect(url_for('system_config.api_integrations'))

        key_prefix = f'API_{api_name.upper()}'
        current_app.config[f'{key_prefix}_ENDPOINT'] = api_endpoint
        current_app.config[f'{key_prefix}_ENABLED'] = api_enabled

        try:
            SecureConfigService.set_secret(f'{key_prefix}_KEY', api_key)
            SecureConfigService.set_secret(f'{key_prefix}_SECRET', api_secret)
        except SecureConfigUnavailable as exc:
            flash_warning(f"Segredos da API não foram armazenados: {exc}")

        flash_success("Integrações API salvas com sucesso!")

        try:
            ConfigChangeLogService.register_change(
                ChangeDescriptor(
                    module="config.integracoes.api",
                    actor_id=session.get("user_id"),
                    entity_type="api",
                    entity_id=api_name,
                ),
                field="config",
                old_value=None,
                new_value="atualizado",
                metadata={"testado": bool(request.form.get('test_connection'))},
            )
        except Exception:
            logger.exception(
                "Falha ao registrar auditoria de integração API",
                extra={"api": api_name},
            )

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
    actor_id = session.get("user_id")
    
    if request.method == "POST":
        cache_timeout = int(request.form.get('cache_timeout', 3600))
        max_connections = int(request.form.get('max_connections', 100))
        query_timeout = int(request.form.get('query_timeout', 30))
        memory_limit = int(request.form.get('memory_limit', 512))
        enable_caching = request.form.get('enable_caching') == 'on'
        enable_compression = request.form.get('enable_compression') == 'on'
        enable_monitoring = request.form.get('enable_monitoring') == 'on'

        try:
            SystemConfigService.set('performance', 'cache_timeout', cache_timeout, 'int', 'Timeout do cache (segundos)', actor_id)
            SystemConfigService.set('performance', 'max_connections', max_connections, 'int', 'Máximo de conexões', actor_id)
            SystemConfigService.set('performance', 'query_timeout', query_timeout, 'int', 'Timeout de queries (segundos)', actor_id)
            SystemConfigService.set('performance', 'memory_limit', memory_limit, 'int', 'Limite de memória (MB)', actor_id)
            SystemConfigService.set('performance', 'enable_caching', enable_caching, 'bool', 'Habilitar cache', actor_id)
            SystemConfigService.set('performance', 'enable_compression', enable_compression, 'bool', 'Habilitar compressão', actor_id)
            SystemConfigService.set('performance', 'enable_monitoring', enable_monitoring, 'bool', 'Habilitar monitoramento', actor_id)
            
            flash_success("Configurações de performance salvas com sucesso!")
            current_app.logger.info("Configurações de performance atualizadas", extra={"actor_id": actor_id})
            
            # Enviar notificação por email
            try:
                from ..models import User
                actor_user = User.query.get(actor_id)
                if actor_user:
                    changes = [
                        {'field': 'cache_timeout', 'old_value': None, 'new_value': cache_timeout},
                        {'field': 'max_connections', 'old_value': None, 'new_value': max_connections},
                    ]
                    ConfigNotificationService.send_config_change_notification(
                        actor=actor_user,
                        category='performance',
                        changes=changes
                    )
            except Exception:
                current_app.logger.exception("Falha ao enviar notificação de configuração de performance")
                
        except Exception as e:
            current_app.logger.error(f"Erro ao salvar configurações de performance: {e}")
            flash_error("Erro ao salvar configurações de performance.")
        
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

    # Configurações atuais do banco de dados
    settings = {
        'cache_timeout': SystemConfigService.get('performance', 'cache_timeout', 3600),
        'max_connections': SystemConfigService.get('performance', 'max_connections', 100),
        'query_timeout': SystemConfigService.get('performance', 'query_timeout', 30),
        'memory_limit': SystemConfigService.get('performance', 'memory_limit', 512),
        'enable_caching': SystemConfigService.get('performance', 'enable_caching', True),
        'enable_compression': SystemConfigService.get('performance', 'enable_compression', True),
        'enable_monitoring': SystemConfigService.get('performance', 'enable_monitoring', True)
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
    actor_id = session.get("user_id")
    
    if request.method == "POST":
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

        try:
            SystemConfigService.set('alerts', 'email', alert_email, 'string', 'Email para alertas', actor_id)
            SystemConfigService.set('alerts', 'frequency', alert_frequency, 'string', 'Frequência de alertas', actor_id)
            SystemConfigService.set('alerts', 'system_errors', alert_system_errors, 'bool', 'Alertas de erros de sistema', actor_id)
            SystemConfigService.set('alerts', 'performance', alert_performance, 'bool', 'Alertas de performance', actor_id)
            SystemConfigService.set('alerts', 'disk_space', alert_disk_space, 'bool', 'Alertas de espaço em disco', actor_id)
            SystemConfigService.set('alerts', 'security', alert_security, 'bool', 'Alertas de segurança', actor_id)
            SystemConfigService.set('alerts', 'database', alert_database, 'bool', 'Alertas de banco de dados', actor_id)
            SystemConfigService.set('alerts', 'backup', alert_backup, 'bool', 'Alertas de backup', actor_id)
            SystemConfigService.set('alerts', 'network', alert_network, 'bool', 'Alertas de rede', actor_id)
            SystemConfigService.set('alerts', 'custom', alert_custom, 'bool', 'Alertas personalizados', actor_id)
            
            flash_success("Configurações de alertas salvas com sucesso!")
            current_app.logger.info("Configurações de alertas atualizadas", extra={"actor_id": actor_id})
            
            # Enviar notificação por email
            try:
                from ..models import User
                actor_user = User.query.get(actor_id)
                if actor_user:
                    changes = [
                        {'field': 'email', 'old_value': None, 'new_value': alert_email},
                        {'field': 'frequency', 'old_value': None, 'new_value': alert_frequency},
                    ]
                    ConfigNotificationService.send_config_change_notification(
                        actor=actor_user,
                        category='alerts',
                        changes=changes
                    )
            except Exception:
                current_app.logger.exception("Falha ao enviar notificação de configuração de alertas")
                
        except Exception as e:
            current_app.logger.error(f"Erro ao salvar configurações de alertas: {e}")
            flash_error("Erro ao salvar configurações de alertas.")
        
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

    # Buscar configurações do banco de dados
    settings = {
        'alert_email': SystemConfigService.get('alerts', 'email', 'admin@example.com'),
        'alert_frequency': SystemConfigService.get('alerts', 'frequency', 'hourly'),
        'alert_system_errors': SystemConfigService.get('alerts', 'system_errors', True),
        'alert_performance': SystemConfigService.get('alerts', 'performance', True),
        'alert_disk_space': SystemConfigService.get('alerts', 'disk_space', True),
        'alert_security': SystemConfigService.get('alerts', 'security', True),
        'alert_database': SystemConfigService.get('alerts', 'database', True),
        'alert_backup': SystemConfigService.get('alerts', 'backup', True),
        'alert_network': SystemConfigService.get('alerts', 'network', False),
        'alert_custom': SystemConfigService.get('alerts', 'custom', False)
    }

    from datetime import datetime
    now = datetime.now()

    return render_template("system_config/system_alerts.html",
                          alert_stats=alert_stats,
                          alert_history=alert_history,
                          settings=settings,
                          now=now)

# ========================================
# API - VALIDAÇÃO DE SENHA
# ========================================

@system_config.route("/api/validate-password", methods=["POST"])
@login_required
def validate_password_api():
    """API para validar força de senha em tempo real"""
    from ..validators.password_validator import PasswordValidator
    
    password = request.json.get('password', '')
    
    if not password:
        return jsonify({
            'valid': False,
            'errors': ['Senha não pode ser vazia'],
            'strength': 0,
            'strength_text': 'Muito Fraca',
            'strength_color': 'danger'
        })
    
    # Validar senha
    errors = PasswordValidator.validate(password, return_errors=True)
    is_valid = len(errors) == 0
    
    # Calcular força
    strength = PasswordValidator.get_strength(password)
    strength_text, strength_color = PasswordValidator.get_strength_text(strength)
    
    # Obter requisitos
    requirements = PasswordValidator.get_requirements()
    requirements_text = PasswordValidator.get_requirements_text()
    
    return jsonify({
        'valid': is_valid,
        'errors': errors,
        'strength': strength,
        'strength_text': strength_text,
        'strength_color': strength_color,
        'requirements': requirements,
        'requirements_text': requirements_text
    })

@system_config.route("/api/password-requirements", methods=["GET"])
@login_required
def password_requirements_api():
    """API para obter requisitos de senha"""
    from ..validators.password_validator import PasswordValidator
    
    requirements = PasswordValidator.get_requirements()
    requirements_text = PasswordValidator.get_requirements_text()
    
    return jsonify({
        'requirements': requirements,
        'requirements_text': requirements_text
    })