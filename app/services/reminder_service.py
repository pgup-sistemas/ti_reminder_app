"""
Serviço de gerenciamento de lembretes
Responsável por processar recorrências automáticas e lógica de negócio
"""

from datetime import date, timedelta
from dateutil.relativedelta import relativedelta
from flask import current_app
from sqlalchemy import and_

from .. import db
from ..models import Reminder, ReminderHistory, User
from ..utils.timezone_utils import get_current_time_for_db


class ReminderService:
    """Serviço centralizado para gerenciar lembretes"""

    @staticmethod
    def process_recurring_reminders():
        """
        Processa lembretes recorrentes que venceram
        Cria novos lembretes baseado na frequência configurada
        
        Executa automaticamente via scheduler
        """
        try:
            today = date.today()
            processed = 0
            created = 0

            # Buscar lembretes vencidos que têm recorrência
            overdue_reminders = Reminder.query.filter(
                and_(
                    Reminder.due_date < today,
                    Reminder.notified == False,
                    Reminder.frequency.isnot(None),
                    Reminder.frequency != '',
                    Reminder.status == 'ativo',
                    # Verificar se não passou da data final
                    db.or_(
                        Reminder.end_date.is_(None),
                        Reminder.end_date > today
                    ),
                    # Verificar se não está pausado
                    db.or_(
                        Reminder.pause_until.is_(None),
                        Reminder.pause_until <= today
                    )
                )
            ).all()

            # Processando lembretes para recorrência

            for reminder in overdue_reminders:
                try:
                    # Calcular próxima data baseado na frequência
                    next_due = ReminderService._calculate_next_due_date(
                        reminder.due_date, 
                        reminder.frequency
                    )

                    if next_due is None:
                        current_app.logger.warning(f"[ReminderService] Frequência inválida para lembrete {reminder.id}")
                        continue

                    # Verificar se não passou da data final
                    if reminder.end_date and next_due > reminder.end_date:
                        # Lembrete atingiu data final, não criando recorrência
                        reminder.notified = True
                        reminder.status = 'encerrado'
                        continue

                    # Criar histórico do lembrete anterior
                    ReminderService._create_history_entry(reminder, 'recurring')

                    # Criar novo lembrete recorrente
                    new_reminder = Reminder(
                        name=reminder.name,
                        type=reminder.type,
                        due_date=next_due,
                        responsible=reminder.responsible,
                        frequency=reminder.frequency,
                        sector_id=reminder.sector_id,
                        user_id=reminder.user_id,
                        status=reminder.status,
                        pause_until=reminder.pause_until,
                        end_date=reminder.end_date,
                        priority=reminder.priority,
                        notes=reminder.notes,
                        contract_number=reminder.contract_number,
                        cost=reminder.cost,
                        supplier=reminder.supplier,
                        category=reminder.category,
                        created_at=get_current_time_for_db()
                    )
                    
                    db.session.add(new_reminder)
                    
                    # Marcar lembrete antigo como notificado
                    reminder.notified = True
                    
                    created += 1
                    # Novo lembrete recorrente criado

                except Exception as e:
                    current_app.logger.error(f"[ReminderService] Erro ao processar recorrência do lembrete {reminder.id}")
                    continue

                processed += 1

            # Commit todas as alterações
            db.session.commit()
            
            # Processamento de recorrências concluído
            
            return {
                'processed': processed,
                'created': created,
                'timestamp': get_current_time_for_db()
            }

        except Exception as e:
            db.session.rollback()
            current_app.logger.error("[ReminderService] Erro no processamento de recorrências")
            return {
                'error': str(e),
                'processed': 0,
                'created': 0
            }

    @staticmethod
    def _calculate_next_due_date(current_due_date, frequency):
        """
        Calcula a próxima data de vencimento baseado na frequência
        
        Args:
            current_due_date: Data de vencimento atual
            frequency: Frequência (diario, quinzenal, mensal, anual)
            
        Returns:
            Nova data de vencimento ou None se frequência inválida
        """
        if frequency == 'diario':
            return current_due_date + relativedelta(days=1)
        elif frequency == 'quinzenal':
            return current_due_date + relativedelta(days=15)
        elif frequency == 'mensal':
            return current_due_date + relativedelta(months=1)
        elif frequency == 'anual':
            return current_due_date + relativedelta(years=1)
        else:
            return None

    @staticmethod
    def _create_history_entry(reminder, action_type):
        """
        Cria entrada no histórico do lembrete
        
        Args:
            reminder: Objeto Reminder
            action_type: Tipo de ação (recurring, completed, skipped, etc.)
        """
        try:
            history = ReminderHistory(
                reminder_id=reminder.id,
                original_due_date=reminder.due_date,
                action_type=action_type,
                action_date=get_current_time_for_db(),
                completed=reminder.completed,
                notes=f"Recorrência automática - próxima data será calculada"
            )
            db.session.add(history)
            # Histórico de lembrete criado
        except Exception as e:
            current_app.logger.error("[ReminderService] Erro ao criar histórico")

    @staticmethod
    def complete_reminder(reminder_id, user_id, notes=None):
        """
        Marca um lembrete como concluído e cria entrada no histórico
        
        Args:
            reminder_id: ID do lembrete
            user_id: ID do usuário que completou
            notes: Observações opcionais
            
        Returns:
            True se sucesso, False caso contrário
        """
        try:
            reminder = Reminder.query.get(reminder_id)
            if not reminder:
                return False

            # Criar histórico
            history = ReminderHistory(
                reminder_id=reminder.id,
                original_due_date=reminder.due_date,
                action_type='completed',
                action_date=get_current_time_for_db(),
                completed=True,
                completed_by=user_id,
                notes=notes or f"Concluído por usuário {user_id}"
            )
            db.session.add(history)

            # Marcar como concluído
            reminder.completed = True
            db.session.commit()

            current_app.logger.info(f"[ReminderService] Lembrete {reminder_id} marcado como concluído por usuário {user_id}")
            return True

        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"[ReminderService] Erro ao completar lembrete {reminder_id}: {str(e)}")
            return False

    @staticmethod
    def get_reminder_statistics():
        """
        Retorna estatísticas dos lembretes para dashboard
        
        Returns:
            Dict com estatísticas
        """
        try:
            today = date.today()
            
            # Total de lembretes ativos
            total_active = Reminder.query.filter(
                Reminder.status == 'ativo',
                Reminder.completed == False
            ).count()

            # Lembretes vencidos
            overdue = Reminder.query.filter(
                Reminder.status == 'ativo',
                Reminder.completed == False,
                Reminder.due_date < today
            ).count()

            # Lembretes vencendo hoje
            due_today = Reminder.query.filter(
                Reminder.status == 'ativo',
                Reminder.completed == False,
                Reminder.due_date == today
            ).count()

            # Lembretes nos próximos 7 dias
            next_7_days = Reminder.query.filter(
                Reminder.status == 'ativo',
                Reminder.completed == False,
                Reminder.due_date > today,
                Reminder.due_date <= today + timedelta(days=7)
            ).count()

            # Lembretes nos próximos 30 dias
            next_30_days = Reminder.query.filter(
                Reminder.status == 'ativo',
                Reminder.completed == False,
                Reminder.due_date > today,
                Reminder.due_date <= today + timedelta(days=30)
            ).count()

            # Taxa de cumprimento (últimos 30 dias)
            last_month = today - timedelta(days=30)
            completed_last_month = ReminderHistory.query.filter(
                ReminderHistory.action_type == 'completed',
                ReminderHistory.action_date >= last_month
            ).count()

            total_last_month = ReminderHistory.query.filter(
                ReminderHistory.action_date >= last_month
            ).count()

            compliance_rate = (completed_last_month / total_last_month * 100) if total_last_month > 0 else 0

            # Custo total pendente (lembretes com custo definido)
            total_cost_pending = db.session.query(
                db.func.sum(Reminder.cost)
            ).filter(
                Reminder.status == 'ativo',
                Reminder.completed == False,
                Reminder.cost.isnot(None)
            ).scalar() or 0

            return {
                'total_active': total_active,
                'overdue': overdue,
                'due_today': due_today,
                'next_7_days': next_7_days,
                'next_30_days': next_30_days,
                'compliance_rate': round(compliance_rate, 2),
                'total_cost_pending': float(total_cost_pending),
                'generated_at': get_current_time_for_db()
            }

        except Exception as e:
            current_app.logger.error(f"[ReminderService] Erro ao gerar estatísticas: {str(e)}")
            return {
                'error': str(e)
            }

    @staticmethod
    def get_upcoming_critical_reminders(days=90):
        """
        Retorna lembretes críticos que vencerão em breve
        
        Args:
            days: Número de dias para considerar
            
        Returns:
            Lista de lembretes críticos
        """
        try:
            today = date.today()
            future_date = today + timedelta(days=days)

            critical_reminders = Reminder.query.filter(
                Reminder.status == 'ativo',
                Reminder.completed == False,
                Reminder.priority.in_(['alta', 'critica']),
                Reminder.due_date >= today,
                Reminder.due_date <= future_date
            ).order_by(Reminder.due_date.asc()).all()

            return critical_reminders

        except Exception as e:
            current_app.logger.error(f"[ReminderService] Erro ao buscar lembretes críticos: {str(e)}")
            return []
