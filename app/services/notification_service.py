"""
Serviço de notificações do sistema TI OSN
Gerencia notificações automáticas, alertas e comunicações
"""

import os
from datetime import datetime, timedelta
from flask import current_app, render_template
from flask_mail import Message

from .. import mail
from ..models import (Task, Reminder, EquipmentRequest, User, NotificationSettings,
                      TaskSlaConfig, db)
from ..utils.timezone_utils import get_current_time_for_db


class NotificationService:
    """Serviço centralizado para gerenciar notificações"""

    @staticmethod
    def send_email_notification(recipient_email, subject, template, **context):
        """Envia notificação por email"""
        try:
            msg = Message(
                subject=subject,
                recipients=[recipient_email],
                html=render_template(template, **context)
            )
            mail.send(msg)
            return True
        except Exception as e:
            current_app.logger.error("Erro ao enviar email")
            return False

    @staticmethod
    def get_user_notification_settings(user_id, notification_type):
        """Obtém configurações de notificação do usuário"""
        settings = NotificationSettings.query.filter_by(
            user_id=user_id,
            notification_type=notification_type
        ).first()

        if not settings:
            # Configurações padrão
            return {
                'enabled': True,
                'advance_hours': 24,
                'email_enabled': True,
                'browser_enabled': True
            }

        return {
            'enabled': settings.enabled,
            'advance_hours': settings.advance_hours,
            'email_enabled': settings.email_enabled,
            'browser_enabled': settings.browser_enabled
        }

    @staticmethod
    def check_task_notifications():
        """Verifica tarefas próximas do vencimento e SLA"""
        current_time = get_current_time_for_db()
        notifications_sent = 0

        # Buscar tarefas não concluídas
        tasks = Task.query.filter_by(completed=False).all()

        for task in tasks:
            if not task.date:
                continue

            task_datetime = datetime.combine(task.date, datetime.strptime("00:00:00", "%H:%M:%S").time())

            # Calcular SLA se não estiver definido
            if not task.sla_deadline and task.priority:
                sla_hours = TaskSlaConfig.get_sla_hours(task.priority)
                task.sla_deadline = task.created_at + timedelta(hours=sla_hours)
                db.session.commit()

            # Verificar notificações de vencimento (24h antes)
            notification_time = task_datetime - timedelta(hours=24)

            if (current_time >= notification_time and
                current_time < task_datetime and
                not task.notification_sent):

                # Enviar notificações para usuários relacionados
                NotificationService._notify_task_due(task)
                task.notification_sent = True
                notifications_sent += 1

            # Verificar SLA crítico (1h antes)
            if task.sla_deadline:
                sla_warning_time = task.sla_deadline - timedelta(hours=1)

                if (current_time >= sla_warning_time and
                    current_time < task.sla_deadline and
                    not task.notification_sent):

                    NotificationService._notify_task_sla_warning(task)
                    notifications_sent += 1

        db.session.commit()
        return notifications_sent

    @staticmethod
    def check_equipment_return_alerts():
        """Verifica equipamentos próximos da devolução"""
        current_time = get_current_time_for_db()
        alerts_sent = 0

        # Equipamentos entregues com data de devolução
        equipments = EquipmentRequest.query.filter(
            EquipmentRequest.status == "Entregue",
            EquipmentRequest.return_date.isnot(None),
            EquipmentRequest.return_alert_sent == False
        ).all()

        for equipment in equipments:
            return_datetime = datetime.combine(equipment.return_date, datetime.strptime("00:00:00", "%H:%M:%S").time())
            alert_time = return_datetime - timedelta(days=1)  # Alerta 1 dia antes

            if current_time >= alert_time and current_time < return_datetime:
                NotificationService._notify_equipment_return_due(equipment)
                equipment.return_alert_sent = True
                alerts_sent += 1

        db.session.commit()
        return alerts_sent

    @staticmethod
    def check_reminder_escalations():
        """Verifica lembretes que precisam de escalação"""
        current_time = get_current_time_for_db()
        escalations_done = 0

        # Lembretes ativos não realizados há mais de 7 dias
        overdue_reminders = Reminder.query.filter(
            Reminder.status == "ativo",
            Reminder.completed == False,
            Reminder.due_date < current_time.date() - timedelta(days=7),
            Reminder.escalation_level < 3  # Máximo 3 níveis de escalação
        ).all()

        for reminder in overdue_reminders:
            days_overdue = (current_time.date() - reminder.due_date).days

            # Escalar baseado no tempo de atraso
            if days_overdue >= 14 and reminder.escalation_level < 2:
                NotificationService._escalate_reminder(reminder, 2)
                reminder.escalation_level = 2
                reminder.last_escalation = current_time
                escalations_done += 1

            elif days_overdue >= 7 and reminder.escalation_level < 1:
                NotificationService._escalate_reminder(reminder, 1)
                reminder.escalation_level = 1
                reminder.last_escalation = current_time
                escalations_done += 1

        db.session.commit()
        return escalations_done

    @staticmethod
    def _notify_task_due(task):
        """Notifica sobre tarefa próxima do vencimento"""
        # Notificar responsável da tarefa
        if task.usuario and task.usuario.email:
            settings = NotificationService.get_user_notification_settings(
                task.usuario.id, 'task_reminder'
            )

            if settings['email_enabled']:
                NotificationService.send_email_notification(
                    task.usuario.email,
                    f"Tarefa próxima do vencimento: {task.description[:50]}",
                    "emails/task_due.html",
                    task=task,
                    user=task.usuario
                )

        # Notificar administradores
        admins = User.query.filter_by(is_admin=True, ativo=True).all()
        for admin in admins:
            settings = NotificationService.get_user_notification_settings(
                admin.id, 'task_reminder'
            )

            if settings['email_enabled']:
                NotificationService.send_email_notification(
                    admin.email,
                    f"[ADMIN] Tarefa próxima do vencimento: {task.description[:50]}",
                    "emails/task_due_admin.html",
                    task=task,
                    admin=admin
                )

    @staticmethod
    def _notify_task_sla_warning(task):
        """Notifica sobre SLA crítico de tarefa"""
        # Notificar responsável e administradores
        recipients = []

        if task.usuario:
            recipients.append(task.usuario)

        admins = User.query.filter_by(is_admin=True, ativo=True).all()
        recipients.extend(admins)

        for user in recipients:
            settings = NotificationService.get_user_notification_settings(
                user.id, 'task_reminder'
            )

            if settings['email_enabled']:
                NotificationService.send_email_notification(
                    user.email,
                    f"[URGENTE] SLA crítico - Tarefa: {task.description[:50]}",
                    "emails/task_sla_warning.html",
                    task=task,
                    user=user
                )

    @staticmethod
    def _notify_equipment_return_due(equipment):
        """Notifica sobre equipamento próximo da devolução"""
        # Notificar solicitante
        if equipment.requester and equipment.requester.email:
            settings = NotificationService.get_user_notification_settings(
                equipment.requester.id, 'equipment_return'
            )

            if settings['email_enabled']:
                NotificationService.send_email_notification(
                    equipment.requester.email,
                    f"Equipamento próximo da devolução: {equipment.description[:50]}",
                    "emails/equipment_return_due.html",
                    equipment=equipment,
                    user=equipment.requester
                )

        # Notificar TI
        ti_users = User.query.filter_by(is_ti=True, ativo=True).all()
        for ti_user in ti_users:
            settings = NotificationService.get_user_notification_settings(
                ti_user.id, 'equipment_return'
            )

            if settings['email_enabled']:
                NotificationService.send_email_notification(
                    ti_user.email,
                    f"[TI] Equipamento próximo da devolução: {equipment.description[:50]}",
                    "emails/equipment_return_due_ti.html",
                    equipment=equipment,
                    ti_user=ti_user
                )

    @staticmethod
    def _escalate_reminder(reminder, level):
        """Escala lembrete para nível superior"""
        escalation_targets = {
            1: "Supervisor TI",
            2: "Gerente de TI",
            3: "Diretoria"
        }

        target = escalation_targets.get(level, "Administração")

        # Encontrar usuários para escalação (lógica simplificada)
        escalation_users = User.query.filter_by(is_admin=True, ativo=True).all()

        for user in escalation_users:
            settings = NotificationService.get_user_notification_settings(
                user.id, 'reminder_escalation'
            )

            if settings['email_enabled']:
                NotificationService.send_email_notification(
                    user.email,
                    f"[ESCALAÇÃO NÍVEL {level}] Lembrete atrasado: {reminder.name}",
                    "emails/reminder_escalation.html",
                    reminder=reminder,
                    user=user,
                    level=level,
                    target=target
                )

        reminder.escalated_to = target

    @staticmethod
    def send_welcome_notification(user):
        """Envia notificação de boas-vindas para novo usuário"""
        if user.email:
            NotificationService.send_email_notification(
                user.email,
                "Bem-vindo ao Sistema TI OSN",
                "emails/welcome.html",
                user=user
            )

    @staticmethod
    def send_password_reset_notification(user, reset_token):
        """Envia notificação de redefinição de senha"""
        if user.email:
            reset_url = f"{current_app.config['FRONTEND_URL']}/reset-password/{reset_token}"

            NotificationService.send_email_notification(
                user.email,
                "Redefinição de Senha - Sistema TI OSN",
                "emails/password_reset.html",
                user=user,
                reset_url=reset_url
            )

    @staticmethod
    def check_upcoming_reminders():
        """
        Verifica lembretes que estão próximos do vencimento
        Envia notificações preventivas em intervalos configuráveis
        """
        from datetime import date, timedelta
        
        current_time = get_current_time_for_db()
        today = current_time.date()
        notifications_sent = 0
        
        # Definir intervalos de notificação (em dias antes do vencimento)
        notification_intervals = [90, 60, 30, 15, 7, 3, 1]
        
        for days_before in notification_intervals:
            target_date = today + timedelta(days=days_before)
            
            # Buscar lembretes ativos que vencem na data alvo e ainda não foram notificados
            upcoming_reminders = Reminder.query.filter(
                Reminder.status == 'ativo',
                Reminder.completed == False,
                Reminder.due_date == target_date,
                # Evitar notificar lembretes que já foram escalados recentemente
                db.or_(
                    Reminder.last_escalation.is_(None),
                    Reminder.last_escalation < current_time - timedelta(hours=24)
                )
            ).all()
            
            for reminder in upcoming_reminders:
                try:
                    # Determinar urgência baseado no tempo restante
                    if days_before <= 3:
                        urgency = "CRÍTICO"
                        priority_label = "danger"
                    elif days_before <= 7:
                        urgency = "URGENTE"
                        priority_label = "warning"
                    elif days_before <= 15:
                        urgency = "IMPORTANTE"
                        priority_label = "info"
                    else:
                        urgency = "Atenção"
                        priority_label = "primary"
                    
                    # Notificar responsável
                    if reminder.usuario and reminder.usuario.email:
                        NotificationService.send_email_notification(
                            reminder.usuario.email,
                            f"[{urgency}] Lembrete vence em {days_before} dias: {reminder.name}",
                            "emails/reminder_upcoming.html",
                            reminder=reminder,
                            user=reminder.usuario,
                            days_remaining=days_before,
                            urgency=urgency,
                            priority_label=priority_label
                        )
                        notifications_sent += 1
                    
                    # Para lembretes críticos (alta prioridade), notificar também os admins
                    if reminder.priority in ['alta', 'critica'] and days_before <= 15:
                        admins = User.query.filter_by(is_admin=True, ativo=True).all()
                        for admin in admins:
                            settings = NotificationService.get_user_notification_settings(
                                admin.id, 'reminder_upcoming'
                            )
                            
                            if settings.get('email_enabled', True):
                                NotificationService.send_email_notification(
                                    admin.email,
                                    f"[ADMIN - {urgency}] Lembrete crítico em {days_before} dias: {reminder.name}",
                                    "emails/reminder_upcoming_admin.html",
                                    reminder=reminder,
                                    admin=admin,
                                    days_remaining=days_before,
                                    urgency=urgency,
                                    priority_label=priority_label
                                )
                    
                    # Notificação enviada para lembrete
                    
                except Exception as e:
                    current_app.logger.error(f"Erro ao notificar lembrete {reminder.id}")
                    continue
        
        return notifications_sent

    @staticmethod
    def run_notification_checks():
        """Executa todas as verificações de notificação"""
        results = {
            'task_notifications': NotificationService.check_task_notifications(),
            'equipment_alerts': NotificationService.check_equipment_return_alerts(),
            'reminder_escalations': NotificationService.check_reminder_escalations(),
            'reminder_upcoming': NotificationService.check_upcoming_reminders(),
            'timestamp': get_current_time_for_db()
        }

        # Notificações processadas
        return results