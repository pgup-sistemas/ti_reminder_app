"""
Serviço de Notificações de Configuração
Envia notificações por email quando configurações ou usuários são alterados
"""

from flask import current_app, render_template, url_for
from flask_mail import Message
from ..models import User
from .. import mail


class ConfigNotificationService:
    """Serviço para enviar notificações de alterações de configuração"""
    
    # Mapeamento de categorias para nomes amigáveis
    CATEGORY_NAMES = {
        'system': 'Sistema Geral',
        'security': 'Segurança',
        'backup': 'Backup',
        'performance': 'Performance',
        'alerts': 'Alertas',
        'email': 'Email',
        'api': 'Integrações API',
        'rfid': 'RFID'
    }
    
    # Mapeamento de campos para nomes amigáveis
    FIELD_NAMES = {
        'name': 'Nome',
        'maintenance_mode': 'Modo de Manutenção',
        'timezone': 'Fuso Horário',
        'language': 'Idioma',
        'password_min_length': 'Comprimento Mínimo da Senha',
        'password_require_uppercase': 'Exigir Maiúsculas',
        'password_require_lowercase': 'Exigir Minúsculas',
        'password_require_numbers': 'Exigir Números',
        'password_require_special': 'Exigir Caracteres Especiais',
        'session_timeout': 'Timeout de Sessão',
        'max_login_attempts': 'Máximo de Tentativas de Login',
        'lockout_duration': 'Duração do Bloqueio',
        'enabled': 'Habilitado',
        'frequency': 'Frequência',
        'time': 'Horário',
        'retention_days': 'Dias de Retenção',
        'location': 'Localização',
        'cache_timeout': 'Timeout do Cache',
        'max_connections': 'Máximo de Conexões',
        'email': 'Email',
    }
    
    @classmethod
    def send_config_change_notification(cls, actor, category, changes, notes=None):
        """
        Envia notificação de alteração de configuração para administradores
        
        Args:
            actor: Usuário que fez a alteração
            category: Categoria da configuração (system, security, etc)
            changes: Lista de dicionários com {field, old_value, new_value}
            notes: Observações adicionais (opcional)
        """
        try:
            # Buscar todos os administradores ativos
            admins = User.query.filter_by(is_admin=True, ativo=True).all()
            
            if not admins:
                current_app.logger.warning("Nenhum administrador ativo para enviar notificação")
                return
            
            # Preparar dados para o template
            category_display = cls.CATEGORY_NAMES.get(category, category.title())
            
            # Enriquecer mudanças com nomes amigáveis
            enriched_changes = []
            for change in changes:
                field = change.get('field', '')
                field_display = cls.FIELD_NAMES.get(field, field.replace('_', ' ').title())
                
                enriched_changes.append({
                    'field': field,
                    'field_display': field_display,
                    'old_value': cls._format_value(change.get('old_value')),
                    'new_value': cls._format_value(change.get('new_value'))
                })
            
            # URL para as configurações
            url = url_for('system_config.general_settings', _external=True)
            
            # Renderizar template
            html_body = render_template(
                'emails/config_changed.html',
                actor=actor,
                category=category,
                category_display=category_display,
                changes=enriched_changes,
                notes=notes,
                url=url,
                timestamp=actor.updated_at if hasattr(actor, 'updated_at') else None
            )
            
            # Enviar email para cada administrador
            for admin in admins:
                try:
                    msg = Message(
                        subject=f"[TI OSN] Configuração Alterada: {category_display}",
                        recipients=[admin.email],
                        html=html_body
                    )
                    mail.send(msg)
                    current_app.logger.info(
                        f"Notificação de config enviada para {admin.email}",
                        extra={'category': category, 'admin_id': admin.id}
                    )
                except Exception as e:
                    current_app.logger.error(
                        f"Erro ao enviar notificação para {admin.email}: {e}",
                        extra={'category': category, 'admin_id': admin.id}
                    )
            
        except Exception as e:
            current_app.logger.error(f"Erro ao enviar notificações de configuração: {e}")
    
    @classmethod
    def send_user_created_notification(cls, user, creator, temp_password=None):
        """
        Envia notificação de criação de usuário
        
        Args:
            user: Usuário criado
            creator: Usuário que criou
            temp_password: Senha temporária (se aplicável)
        """
        try:
            # URL de login
            login_url = url_for('auth.login', _external=True)
            
            # Renderizar template
            html_body = render_template(
                'emails/user_created.html',
                user=user,
                creator=creator,
                temp_password=temp_password,
                login_url=login_url
            )
            
            # Enviar email para o usuário
            msg = Message(
                subject="[TI OSN] Bem-vindo ao Sistema",
                recipients=[user.email],
                html=html_body
            )
            mail.send(msg)
            
            current_app.logger.info(
                f"Email de boas-vindas enviado para {user.email}",
                extra={'user_id': user.id}
            )
            
            # Notificar administradores
            admins = User.query.filter_by(is_admin=True, ativo=True).filter(User.id != creator.id).all()
            for admin in admins:
                try:
                    admin_msg = Message(
                        subject=f"[TI OSN] Novo Usuário Criado: {user.username}",
                        recipients=[admin.email],
                        html=f"""
                        <p>Um novo usuário foi criado no sistema:</p>
                        <ul>
                            <li><strong>Usuário:</strong> {user.username}</li>
                            <li><strong>Email:</strong> {user.email}</li>
                            <li><strong>Criado por:</strong> {creator.username}</li>
                        </ul>
                        """
                    )
                    mail.send(admin_msg)
                except Exception:
                    pass
                    
        except Exception as e:
            current_app.logger.error(f"Erro ao enviar notificação de criação de usuário: {e}")
    
    @classmethod
    def send_user_updated_notification(cls, user, updater, changes, password_changed=False):
        """
        Envia notificação de atualização de usuário
        
        Args:
            user: Usuário atualizado
            updater: Usuário que fez a atualização
            changes: Lista de mudanças
            password_changed: Se a senha foi alterada
        """
        try:
            # URL de login
            login_url = url_for('auth.login', _external=True)
            
            # Renderizar template
            html_body = render_template(
                'emails/user_updated.html',
                user=user,
                updater=updater,
                changes=changes,
                password_changed=password_changed,
                login_url=login_url,
                timestamp=user.updated_at if hasattr(user, 'updated_at') else None
            )
            
            # Enviar email para o usuário
            msg = Message(
                subject="[TI OSN] Sua Conta Foi Atualizada",
                recipients=[user.email],
                html=html_body
            )
            mail.send(msg)
            
            current_app.logger.info(
                f"Notificação de atualização enviada para {user.email}",
                extra={'user_id': user.id}
            )
            
        except Exception as e:
            current_app.logger.error(f"Erro ao enviar notificação de atualização de usuário: {e}")
    
    @classmethod
    def send_password_reset_notification(cls, user, new_password):
        """
        Envia notificação de reset de senha
        
        Args:
            user: Usuário que teve a senha resetada
            new_password: Nova senha temporária
        """
        try:
            # URL de login
            login_url = url_for('auth.login', _external=True)
            
            html_body = f"""
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <style>
                    body {{ font-family: Arial, sans-serif; line-height: 1.6; }}
                    .container {{ max-width: 600px; margin: 0 auto; padding: 20px; }}
                    .header {{ background: #667eea; color: white; padding: 20px; text-align: center; }}
                    .content {{ padding: 20px; background: #f9f9f9; }}
                    .password-box {{ background: #fff3cd; border: 2px dashed #ffc107; padding: 20px; margin: 20px 0; text-align: center; }}
                    .password {{ font-size: 24px; font-weight: bold; font-family: monospace; }}
                    .btn {{ display: inline-block; padding: 12px 24px; background: #667eea; color: white; text-decoration: none; border-radius: 4px; }}
                </style>
            </head>
            <body>
                <div class="container">
                    <div class="header">
                        <h1>🔑 Senha Resetada</h1>
                    </div>
                    <div class="content">
                        <p>Olá, <strong>{user.username}</strong>!</p>
                        <p>Sua senha foi resetada por um administrador do sistema.</p>
                        
                        <div class="password-box">
                            <p>Sua nova senha temporária:</p>
                            <div class="password">{new_password}</div>
                            <p style="margin-top: 15px;"><strong>⚠️ Importante:</strong> Altere esta senha no próximo acesso!</p>
                        </div>
                        
                        <div style="text-align: center;">
                            <a href="{login_url}" class="btn">Acessar o Sistema</a>
                        </div>
                    </div>
                </div>
            </body>
            </html>
            """
            
            msg = Message(
                subject="[TI OSN] Sua Senha Foi Resetada",
                recipients=[user.email],
                html=html_body
            )
            mail.send(msg)
            
            current_app.logger.info(
                f"Notificação de reset de senha enviada para {user.email}",
                extra={'user_id': user.id}
            )
            
        except Exception as e:
            current_app.logger.error(f"Erro ao enviar notificação de reset de senha: {e}")
    
    @classmethod
    def send_account_status_changed_notification(cls, user, actor, is_active, reason=None):
        """
        Envia notificação de ativação/desativação de conta
        
        Args:
            user: Usuário que teve status alterado
            actor: Usuário que fez a alteração
            is_active: Se a conta foi ativada (True) ou desativada (False)
            reason: Motivo da alteração (opcional)
        """
        try:
            # URL de login
            login_url = url_for('auth.login', _external=True)
            
            # Renderizar template
            html_body = render_template(
                'emails/account_status_changed.html',
                user=user,
                actor=actor,
                is_active=is_active,
                reason=reason,
                login_url=login_url,
                timestamp=user.updated_at if hasattr(user, 'updated_at') else None
            )
            
            # Enviar email para o usuário
            status_text = "Ativada" if is_active else "Desativada"
            msg = Message(
                subject=f"[TI OSN] Sua Conta Foi {status_text}",
                recipients=[user.email],
                html=html_body
            )
            mail.send(msg)
            
            current_app.logger.info(
                f"Notificação de status de conta enviada para {user.email}",
                extra={'user_id': user.id, 'is_active': is_active}
            )
            
            # Notificar administradores
            admins = User.query.filter_by(is_admin=True, ativo=True).filter(User.id != actor.id).all()
            for admin in admins:
                try:
                    admin_msg = Message(
                        subject=f"[TI OSN] Conta {status_text}: {user.username}",
                        recipients=[admin.email],
                        html=f"""
                        <p>Uma conta foi {status_text.lower()} no sistema:</p>
                        <ul>
                            <li><strong>Usuário:</strong> {user.username}</li>
                            <li><strong>Email:</strong> {user.email}</li>
                            <li><strong>Alterado por:</strong> {actor.username}</li>
                            {f'<li><strong>Motivo:</strong> {reason}</li>' if reason else ''}
                        </ul>
                        """
                    )
                    mail.send(admin_msg)
                except Exception:
                    pass
                    
        except Exception as e:
            current_app.logger.error(f"Erro ao enviar notificação de status de conta: {e}")
    
    @classmethod
    def send_account_deleted_notification(cls, user, actor, reason=None):
        """
        Envia notificação de exclusão de conta
        
        Args:
            user: Usuário que foi excluído
            actor: Usuário que excluiu
            reason: Motivo da exclusão (opcional)
        """
        try:
            # Renderizar template
            html_body = render_template(
                'emails/account_deleted.html',
                user=user,
                actor=actor,
                reason=reason,
                timestamp=user.updated_at if hasattr(user, 'updated_at') else None
            )
            
            # Enviar email para o usuário
            msg = Message(
                subject="[TI OSN] Sua Conta Foi Excluída",
                recipients=[user.email],
                html=html_body
            )
            mail.send(msg)
            
            current_app.logger.info(
                f"Notificação de exclusão de conta enviada para {user.email}",
                extra={'user_id': user.id}
            )
            
            # Notificar administradores
            admins = User.query.filter_by(is_admin=True, ativo=True).filter(User.id != actor.id).all()
            for admin in admins:
                try:
                    admin_msg = Message(
                        subject=f"[TI OSN] Conta Excluída: {user.username}",
                        recipients=[admin.email],
                        html=f"""
                        <p>Uma conta foi excluída do sistema:</p>
                        <ul>
                            <li><strong>Usuário:</strong> {user.username}</li>
                            <li><strong>Email:</strong> {user.email}</li>
                            <li><strong>Excluído por:</strong> {actor.username}</li>
                            {f'<li><strong>Motivo:</strong> {reason}</li>' if reason else ''}
                        </ul>
                        """
                    )
                    mail.send(admin_msg)
                except Exception:
                    pass
                    
        except Exception as e:
            current_app.logger.error(f"Erro ao enviar notificação de exclusão de conta: {e}")
    
    @classmethod
    def _format_value(cls, value):
        """Formata valor para exibição"""
        if value is None:
            return '<em>não definido</em>'
        if isinstance(value, bool):
            return 'Sim' if value else 'Não'
        return str(value)
