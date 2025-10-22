"""
Serviço para gestão de equipamentos - nova arquitetura profissional
"""
from datetime import datetime, timedelta, time
from typing import List, Dict, Optional, Tuple
from flask import current_app
from sqlalchemy import and_, or_, func, case
from flask import current_app

from .. import db
from ..models import (
    Equipment, EquipmentReservation, EquipmentLoan, User,
    EquipmentRequest
)
from .notification_service import NotificationService


class EquipmentService:
    """Serviço central para gestão de equipamentos"""

    @staticmethod
    def create_equipment(data: Dict) -> Equipment:
        """Cria um novo equipamento no inventário"""
        equipment = Equipment(**data)
        db.session.add(equipment)
        db.session.commit()
        return equipment

    @staticmethod
    def get_equipment_catalog(filters: Dict = None) -> List[Equipment]:
        """Retorna catálogo de equipamentos disponíveis"""
        query = Equipment.query.filter(Equipment.status == "disponivel")

        if filters:
            if filters.get('category'):
                query = query.filter(Equipment.category == filters['category'])
            if filters.get('brand'):
                query = query.filter(Equipment.brand == filters['brand'])
            if filters.get('location'):
                query = query.filter(Equipment.location == filters['location'])
            if filters.get('search'):
                search_term = f"%{filters['search']}%"
                query = query.filter(
                    or_(
                        Equipment.name.ilike(search_term),
                        Equipment.description.ilike(search_term),
                        Equipment.patrimony.ilike(search_term)
                    )
                )

        return query.order_by(Equipment.name).all()

    @staticmethod
    def check_equipment_availability(
        equipment_id: int,
        start_date: datetime.date,
        end_date: datetime.date,
        start_time: str = '00:00',
        end_time: str = '23:59'
    ) -> Tuple[bool, str]:
        """
        Verifica disponibilidade do equipamento para o período e horários especificados
        
        Args:
            equipment_id: ID do equipamento
            start_date: Data de início (date)
            end_date: Data de término (date)
            start_time: Hora de início (HH:MM)
            end_time: Hora de término (HH:MM)
            
        Returns:
            Tuple[bool, str]: (disponivel, motivo_indisponibilidade)
        """
        from datetime import time as dt_time
        
        # Converter strings de tempo para objetos time
        if isinstance(start_time, str):
            start_time = datetime.strptime(start_time, '%H:%M').time()
        if isinstance(end_time, str):
            end_time = datetime.strptime(end_time, '%H:%M').time()
            
        # Criar objetos datetime completos
        start_datetime = datetime.combine(start_date, start_time)
        end_datetime = datetime.combine(end_date, end_time)
        
        # Verificar se a data/hora final é maior que a inicial
        if end_datetime <= start_datetime:
            return False, "A data/hora final deve ser posterior à data/hora inicial"
            
        equipment = Equipment.query.get_or_404(equipment_id)

        # Verificar status básico do equipamento
        if equipment.status != "disponivel":
            return False, f"Equipamento {equipment.status}"
            
        if equipment.condition not in ["novo", "bom", "regular"]:
            return False, f"Equipamento em condição inadequada: {equipment.condition}"

        # Verificar empréstimos ativos que conflitam
        conflicting_loans = EquipmentLoan.query.filter(
            and_(
                EquipmentLoan.equipment_id == equipment_id,
                EquipmentLoan.status == "ativo",
                or_(
                    and_(
                        EquipmentLoan.loan_date <= end_datetime,
                        EquipmentLoan.expected_return_date >= start_datetime
                    )
                )
            )
        ).all()

        if conflicting_loans:
            loan = conflicting_loans[0]
            return False, f"Emprestado para {loan.user.username} até {loan.expected_return_date}"

        # Verificar reservas confirmadas que conflitam
        conflicting_reservations = EquipmentReservation.query.filter(
            and_(
                EquipmentReservation.equipment_id == equipment_id,
                EquipmentReservation.status == "confirmada",
                EquipmentReservation.start_datetime.isnot(None),
                EquipmentReservation.end_datetime.isnot(None),
                EquipmentReservation.start_datetime < end_datetime,
                EquipmentReservation.end_datetime > start_datetime
            )
        ).all()

        if conflicting_reservations:
            reservation = conflicting_reservations[0]
            start = reservation.start_datetime.strftime('%d/%m/%Y %H:%M')
            end = reservation.end_datetime.strftime('%d/%m/%Y %H:%M')
            return False, f"Reservado por {reservation.user.username} de {start} a {end}"

        return True, ""

    @staticmethod
    def create_reservation(
        equipment_id: int,
        user_id: int,
        start_date: datetime.date,
        end_date: datetime.date,
        start_time: str = '09:00',
        end_time: str = '18:00',
        purpose: str = None
    ) -> Tuple[Optional[EquipmentReservation], str]:
        """
        Cria uma reserva de equipamento com suporte a horários
        
        Args:
            equipment_id: ID do equipamento
            user_id: ID do usuário solicitante
            start_date: Data de início (date)
            end_date: Data de término (date)
            start_time: Hora de início (HH:MM)
            end_time: Hora de término (HH:MM)
            purpose: Finalidade da reserva
            
        Returns:
            Tuple[Optional[EquipmentReservation], str]: (reserva, mensagem_erro)
        """
        from datetime import time as dt_time
        
        # Validar e converter horários
        try:
            if isinstance(start_time, str):
                start_time_obj = datetime.strptime(start_time, '%H:%M').time()
            else:
                start_time_obj = start_time
                
            if isinstance(end_time, str):
                end_time_obj = datetime.strptime(end_time, '%H:%M').time()
            else:
                end_time_obj = end_time
        except ValueError:
            return None, "Formato de horário inválido. Use HH:MM"
            
        # Verificar se o horário final é maior que o inicial
        start_datetime = datetime.combine(start_date, start_time_obj)
        end_datetime = datetime.combine(end_date, end_time_obj)
        
        if end_datetime <= start_datetime:
            return None, "A data/hora final deve ser posterior à data/hora inicial"
            
        # Verificar se a duração é maior que o período máximo permitido (7 dias por padrão)
        max_duration_days = 7
        if (end_date - start_date).days + 1 > max_duration_days:
            return None, f"Período máximo de reserva é de {max_duration_days} dias"

        equipment = Equipment.query.get_or_404(equipment_id)
        user = User.query.get_or_404(user_id)

        # Verificar permissões
        if not equipment.can_be_reserved_by(user):
            return None, "Usuário não tem permissão para reservar este equipamento"

        # Verificar disponibilidade
        available, reason = EquipmentService.check_equipment_availability(
            equipment_id=equipment_id,
            start_date=start_date,
            end_date=end_date,
            start_time=start_time_obj,
            end_time=end_time_obj
        )
        
        if not available:
            return None, f"Equipamento não disponível: {reason}"

        # Verificar limites de empréstimo
        days_requested = (end_date - start_date).days + 1
        if days_requested > equipment.max_loan_days:
            return None, f"Período máximo de empréstimo é {equipment.max_loan_days} dias"

        # Aplicar regras de aprovação automática baseadas no perfil do usuário
        requires_approval = EquipmentService._check_auto_approval_rules(user, equipment, days_requested)

        try:
            # Criar reserva
            reservation = EquipmentReservation(
                equipment_id=equipment_id,
                user_id=user_id,
                start_date=start_date,
                start_time=start_time_obj,
                end_date=end_date,
                end_time=end_time_obj,
                expected_return_date=end_date,
                expected_return_time=end_time_obj,
                purpose=purpose,
                status="pendente" if requires_approval else "confirmada"
            )

            db.session.add(reservation)
            db.session.commit()

            # Se não requer aprovação, criar empréstimo automaticamente
            if not requires_approval:
                loan, error = EquipmentService.convert_reservation_to_loan(reservation.id)
                if error:
                    current_app.logger.error(f"Erro ao converter reserva {reservation.id} para empréstimo: {error}"
                    )
                    return reservation, f"Reserva criada, mas erro na conversão: {error}"

            return reservation, ""
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao criar reserva: {str(e)}")
            return None, f"Erro ao processar a reserva: {str(e)}"

    @staticmethod
    def _check_auto_approval_rules(user, equipment, days_requested):
        """
        Verifica se a reserva pode ser aprovada automaticamente
        baseado em regras de negócio
        """
        # Regra 1: Equipamentos que não requerem aprovação por padrão
        if not equipment.requires_approval:
            return False

        # Regra 2: Administradores e TI sempre aprovam automaticamente
        if user.is_admin or user.is_ti:
            return False

        # Regra 3: Empréstimos curtos (até 7 dias) podem ser auto-aprovados
        if days_requested <= 7:
            return False

        # Regra 4: Equipamentos de baixo valor/risco podem ser auto-aprovados
        low_risk_categories = ['Acessórios', 'Monitor']
        if equipment.category in low_risk_categories and days_requested <= 14:
            return False

        # Regra 5: Usuários com bom histórico podem ter aprovação automática
        user_history = EquipmentService._get_user_loan_history(user.id)
        if user_history['on_time_returns'] >= 5 and user_history['overdue_loans'] == 0:
            return False

        # Caso contrário, requer aprovação
        return True

    @staticmethod
    def get_pending_reservations():
        """
        Retorna lista de reservas pendentes de aprovação
        Com eager loading para evitar N+1 queries
        """
        from sqlalchemy.orm import joinedload
        from sqlalchemy import or_
        from app.models import User  # Importação necessária para o joinedload
        
        try:
            # Garante que temos acesso ao logger
            if not hasattr(current_app, 'logger'):
                import logging
                current_app.logger = logging.getLogger(__name__)
            
            # Log inicial
            current_app.logger.info("[DEBUG] Buscando reservas pendentes...")
            
            # Busca as reservas pendentes (verifica ambos os status)
            query = EquipmentReservation.query\
                .filter(or_(
                    EquipmentReservation.status == 'pendente',
                    EquipmentReservation.status == 'pending'
                ))\
                .options(
                    joinedload(EquipmentReservation.equipment),
                    joinedload(EquipmentReservation.user).joinedload(User.sector),
                    joinedload(EquipmentReservation.approved_by)
                )\
                .order_by(EquipmentReservation.created_at.desc())
            
            # Log da query SQL
            current_app.logger.debug(f"[DEBUG] Query SQL: {str(query)}")
            
            # Executa a consulta
            reservations = query.all()
            
            # Log detalhado dos resultados
            current_app.logger.info(f"[DEBUG] Total de reservas encontradas: {len(reservations)}")
            
            # Log detalhado de cada reserva (apenas em modo debug)
            if current_app.debug and reservations:
                for i, res in enumerate(reservations, 1):
                    current_app.logger.debug(
                        f"[DEBUG] Reserva {i}: ID={res.id}, "
                        f"Status='{res.status}', "
                        f"Usuário={getattr(res.user, 'username', 'N/A') if hasattr(res, 'user') else 'N/A'}, "
                        f"Equipamento={getattr(res.equipment, 'name', 'N/A') if hasattr(res, 'equipment') else 'N/A'}"
                    )
            
            return reservations
            
        except Exception as e:
            # Log do erro completo
            current_app.logger.error(
                f"Erro ao buscar reservas pendentes: {str(e)}",
                exc_info=True
            )
            # Em caso de erro, retorna lista vazia
            return []
            # Em caso de erro, retorna lista vazia
            return []
        
    @staticmethod
    def get_equipment_schedule(equipment_id: int, start_date: datetime.date, end_date: datetime.date = None):
        """
        Retorna o calendário de reservas de um equipamento
        
        Args:
            equipment_id: ID do equipamento
            start_date: Data inicial
            end_date: Data final (opcional, padrão = start_date + 7 dias)
            
        Returns:
            List[dict]: Lista de reservas no formato para o calendário
        """
        if end_date is None:
            end_date = start_date + timedelta(days=7)
            
        reservations = EquipmentReservation.query.filter(
            EquipmentReservation.equipment_id == equipment_id,
            EquipmentReservation.status == 'confirmada',
            EquipmentReservation.end_datetime >= start_date,
            EquipmentReservation.start_datetime <= end_date
        ).order_by(
            EquipmentReservation.start_datetime.asc()
        ).all()
        
        return [r.to_dict() for r in reservations]
        
    @staticmethod
    def reject_reservation(reservation_id: int, rejected_by_id: int, reason: str) -> Tuple[bool, str]:
        """
        Rejeita uma reserva pendente
        
        Args:
            reservation_id: ID da reserva a ser rejeitada
            rejected_by_id: ID do usuário que está rejeitando
            reason: Motivo da rejeição
            
        Returns:
            Tuple[bool, str]: (success, message)
        """
        from ..models import User  # Importação local para evitar importação circular
        
        try:
            reservation = EquipmentReservation.query.get_or_404(reservation_id)
            rejected_by = User.query.get_or_404(rejected_by_id)
            
            if reservation.status != "pendente":
                return False, "Apenas reservas pendentes podem ser rejeitadas"
                
            # Atualizar status da reserva
            reservation.status = "rejeitada"
            reservation.approved_by_id = rejected_by_id
            reservation.approval_date = datetime.utcnow()
            reservation.approval_notes = f"Reserva rejeitada. Motivo: {reason}"
            
            db.session.commit()
            
            # Enviar notificação para o usuário
            try:
                NotificationService.send_email_notification(
                    reservation.user.email,
                    f"❌ Reserva não aprovada - {reservation.equipment.name}",
                    "emails/reservation_rejected.html",
                    reservation=reservation,
                    rejected_by=rejected_by,
                    reason=reason
                )
            except Exception as e:
                current_app.logger.error(f"Erro ao enviar notificação de rejeição: {str(e)}")
            
            return True, "Reserva rejeitada com sucesso"
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao rejeitar reserva {reservation_id}: {str(e)}")
            return False, f"Erro ao processar a rejeição: {str(e)}"

    @staticmethod
    def count_pending_approvals() -> int:
        """Retorna a quantidade de reservas pendentes de aprovação"""
        from ..models import EquipmentReservation
        return EquipmentReservation.query.filter_by(status='pendente').count()
        
    @staticmethod
    def _get_user_loan_history(user_id):
        """Retorna histórico de empréstimos do usuário"""
        loans = EquipmentLoan.query.filter_by(user_id=user_id).all()

        on_time_returns = 0
        overdue_loans = 0
        total_loans = len(loans)

        for loan in loans:
            if loan.status == "devolvido":
                if loan.is_overdue():
                    overdue_loans += 1
                else:
                    on_time_returns += 1

        return {
            'total_loans': total_loans,
            'on_time_returns': on_time_returns,
            'overdue_loans': overdue_loans,
            'success_rate': (on_time_returns / total_loans * 100) if total_loans > 0 else 0
        }

    @staticmethod
    def approve_reservation(reservation_id: int, approved_by_id: int, notes: str = None) -> Tuple[bool, str]:
        """Aprova uma reserva pendente"""
        from ..models import User  # Importação local para evitar importação circular
        
        reservation = EquipmentReservation.query.get_or_404(reservation_id)
        approver = User.query.get(approved_by_id)

        if reservation.status != "pendente":
            return False, "Reserva não está pendente de aprovação"

        # Verificar disponibilidade novamente antes de aprovar
        available, reason = EquipmentService.check_equipment_availability(
            reservation.equipment_id,
            reservation.start_date,
            reservation.end_date
        )
        
        if not available:
            # Atualizar status para rejeitada automaticamente
            reservation.status = "rejeitada"
            reservation.approval_notes = f"Aprovação automática falhou: {reason}"
            db.session.commit()
            return False, f"Não foi possível aprovar a reserva: {reason}"

        # Atualizar status da reserva
        reservation.status = "confirmada"
        reservation.approved_by_id = approved_by_id
        reservation.approval_date = datetime.utcnow()
        reservation.approval_notes = notes

        try:
            db.session.commit()
            
            # Criar empréstimo
            loan, error = EquipmentService.convert_reservation_to_loan(reservation_id)
            if error:
                return False, f"Reserva aprovada, mas erro na criação do empréstimo: {error}"

            # Enviar notificação para o usuário
            try:
                NotificationService.send_email_notification(
                    reservation.user.email,
                    f"✅ Sua reserva foi aprovada - {reservation.equipment.name}",
                    "emails/reservation_approved.html",
                    reservation=reservation,
                    approver=approver,
                    loan=loan
                )
            except Exception as e:
                current_app.logger.error(f"Erro ao enviar notificação de aprovação: {str(e)}")

            return True, ""
            
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao aprovar reserva {reservation_id}: {str(e)}")
            return False, f"Erro ao processar a aprovação: {str(e)}"

    @staticmethod
    def convert_reservation_to_loan(reservation_id: int) -> Tuple[Optional[EquipmentLoan], str]:
        """Converte reserva confirmada em empréstimo ativo"""
        reservation = EquipmentReservation.query.get_or_404(reservation_id)

        if reservation.status != "confirmada":
            return None, "Reserva deve estar confirmada"

        # Verificar novamente disponibilidade (por segurança)
        available, reason = EquipmentService.check_equipment_availability(
            equipment_id=reservation.equipment_id,
            start_date=reservation.start_date,
            end_date=reservation.end_date,
            start_time=reservation.start_time.strftime('%H:%M') if reservation.start_time else '00:00',
            end_time=reservation.end_time.strftime('%H:%M') if reservation.end_time else '23:59'
        )
        if not available:
            return None, f"Equipamento não está mais disponível: {reason}"

        # Criar empréstimo com os horários da reserva
        loan = EquipmentLoan(
            equipment_id=reservation.equipment_id,
            user_id=reservation.user_id,
            loan_date=reservation.start_datetime,
            expected_return_date=datetime.combine(
                reservation.expected_return_date,
                reservation.expected_return_time if reservation.expected_return_time else time(23, 59)
            ),
            reservation_id=reservation.id,
            condition_at_loan=reservation.equipment.condition
        )

        # Calcular SLA do empréstimo
        loan.calculate_sla()

        # Atualizar status do equipamento
        reservation.equipment.status = "emprestado"

        # Marcar reserva como convertida
        reservation.status = "convertida"

        db.session.add(loan)
        db.session.commit()

        return loan, ""

    @staticmethod
    def return_equipment(loan_id: int, returned_by_id: int, condition: str = None, notes: str = None) -> Tuple[bool, str]:
        """Processa devolução de equipamento"""
        loan = EquipmentLoan.query.get_or_404(loan_id)

        if loan.status != "ativo":
            return False, "Empréstimo não está ativo"

        # Atualizar empréstimo
        loan.status = "devolvido"
        loan.actual_return_date = datetime.utcnow()
        loan.received_by_id = returned_by_id
        loan.condition_at_return = condition or loan.equipment.condition
        loan.return_notes = notes

        # Atualizar status do equipamento
        loan.equipment.status = "disponivel"
        loan.equipment.condition = condition or loan.equipment.condition
        loan.equipment.location = loan.equipment.storage_location  # Retornar ao local de armazenamento

        db.session.commit()

        # Verificar se houve atraso e calcular multa se necessário
        if loan.is_overdue():
            days_overdue = loan.days_overdue()
            # TODO: Implementar sistema de multas/penalidades

        return True, ""

    @staticmethod
    def get_user_active_loans(user_id: int) -> List[EquipmentLoan]:
        """Retorna empréstimos ativos do usuário"""
        return EquipmentLoan.query.filter(
            and_(
                EquipmentLoan.user_id == user_id,
                EquipmentLoan.status == "ativo"
            )
        ).join(Equipment).order_by(EquipmentLoan.expected_return_date).all()

    @staticmethod
    def get_overdue_loans() -> List[EquipmentLoan]:
        """Retorna empréstimos em atraso"""
        today = datetime.utcnow().date()
        return EquipmentLoan.query.filter(
            and_(
                EquipmentLoan.status == "ativo",
                EquipmentLoan.expected_return_date < today
            )
        ).join(Equipment).order_by(EquipmentLoan.expected_return_date).all()

    @staticmethod
    def send_return_reminders():
        """Envia lembretes de devolução próximos"""
        tomorrow = datetime.utcnow().date() + timedelta(days=1)

        due_loans = EquipmentLoan.query.filter(
            and_(
                EquipmentLoan.status == "ativo",
                EquipmentLoan.expected_return_date == tomorrow,
                EquipmentLoan.return_reminder_sent == False
            )
        ).join(Equipment).all()

        reminders_sent = 0
        for loan in due_loans:
            try:
                # Atualizar status SLA antes de notificar
                loan.update_sla_status()

                # Notificar usuário
                NotificationService.send_email_notification(
                    loan.user.email,
                    f"Lembrete: Devolução do equipamento {loan.equipment.name}",
                    "emails/equipment_return_reminder.html",
                    loan=loan,
                    user=loan.user
                )

                # Notificar TI se necessário
                ti_users = User.query.filter_by(is_ti=True).all()
                for ti_user in ti_users:
                    NotificationService.send_email_notification(
                        ti_user.email,
                        f"[TI] Lembrete: Equipamento {loan.equipment.name} deve ser devolvido amanhã",
                        "emails/equipment_return_reminder_ti.html",
                        loan=loan,
                        ti_user=ti_user
                    )

                loan.return_reminder_sent = True
                reminders_sent += 1

            except Exception as e:
                current_app.logger.error(f"Erro ao enviar lembrete para empréstimo {loan.id}: {str(e)}")

        db.session.commit()
        return reminders_sent

    @staticmethod
    def check_sla_status():
        """Verifica e atualiza status de SLA de todos os empréstimos ativos"""
        active_loans = EquipmentLoan.query.filter_by(status="ativo").all()

        updated_count = 0
        for loan in active_loans:
            old_status = loan.sla_status
            loan.update_sla_status()

            if old_status != loan.sla_status:
                updated_count += 1

                # Notificar se SLA estiver em atenção ou vencido
                if loan.sla_status in ["atencao", "vencido"]:
                    try:
                        # Notificar TI sobre SLA crítico
                        ti_users = User.query.filter_by(is_ti=True).all()
                        for ti_user in ti_users:
                            NotificationService.send_email_notification(
                                ti_user.email,
                                f"[SLA] {loan.sla_status.upper()}: Equipamento {loan.equipment.name}",
                                "emails/equipment_sla_alert.html",
                                loan=loan,
                                ti_user=ti_user
                            )
                    except Exception as e:
                        current_app.logger.error(f"Erro ao enviar alerta SLA para empréstimo {loan.id}: {str(e)}")

        db.session.commit()
        return updated_count

    @staticmethod
    def get_sla_stats() -> Dict:
        """Retorna estatísticas de SLA"""
        sla_stats = db.session.query(
            func.count(EquipmentLoan.id).label('total'),
            func.count(case((EquipmentLoan.sla_status == 'cumprido', 1))).label('cumpridos'),
            func.count(case((EquipmentLoan.sla_status == 'normal', 1))).label('normais'),
            func.count(case((EquipmentLoan.sla_status == 'atencao', 1))).label('atencao'),
            func.count(case((EquipmentLoan.sla_status == 'vencido', 1))).label('vencidos')
        ).filter(EquipmentLoan.status.in_(['ativo', 'devolvido'])).first()

        return {
            'total_loans': sla_stats.total or 0,
            'sla_cumpridos': sla_stats.cumpridos or 0,
            'sla_normais': sla_stats.normais or 0,
            'sla_atencao': sla_stats.atencao or 0,
            'sla_vencidos': sla_stats.vencidos or 0,
            'sla_compliance_rate': round(
                (sla_stats.cumpridos or 0) / (sla_stats.total or 1) * 100, 1
            )
        }

    @staticmethod
    def check_maintenance_alerts():
        """Verifica equipamentos que precisam de manutenção"""
        # Equipamentos com manutenção vencida ou próxima (7 dias)
        today = datetime.utcnow().date()
        alert_date = today + timedelta(days=7)

        maintenance_due = Equipment.query.filter(
            Equipment.status.in_(['disponivel', 'emprestado']),
            Equipment.next_maintenance.isnot(None),
            Equipment.next_maintenance <= alert_date,
            Equipment.maintenance_alert_sent == False
        ).all()

        alerts_sent = 0
        for equipment in maintenance_due:
            try:
                # Notificar TI sobre manutenção necessária
                ti_users = User.query.filter_by(is_ti=True).all()
                for ti_user in ti_users:
                    NotificationService.send_email_notification(
                        ti_user.email,
                        f"[Manutenção] Equipamento {equipment.name} precisa de manutenção",
                        "emails/equipment_maintenance_alert.html",
                        equipment=equipment,
                        ti_user=ti_user
                    )

                equipment.maintenance_alert_sent = True
                alerts_sent += 1

            except Exception as e:
                current_app.logger.error(f"Erro ao enviar alerta de manutenção para equipamento {equipment.id}: {str(e)}")

        db.session.commit()
        return alerts_sent

    @staticmethod
    def get_maintenance_stats() -> Dict:
        """Retorna estatísticas de manutenção"""
        today = datetime.utcnow().date()

        stats = db.session.query(
            func.count(Equipment.id).label('total'),
            func.count(case((Equipment.next_maintenance <= today, 1))).label('overdue'),
            func.count(case((and_(Equipment.next_maintenance > today, Equipment.next_maintenance <= today + timedelta(days=7)), 1))).label('due_soon'),
            func.count(case((and_(Equipment.next_maintenance > today + timedelta(days=7), Equipment.next_maintenance <= today + timedelta(days=30)), 1))).label('upcoming')
        ).filter(Equipment.next_maintenance.isnot(None)).first()

        return {
            'total_with_maintenance': stats.total or 0,
            'overdue_maintenance': stats.overdue or 0,
            'due_soon_maintenance': stats.due_soon or 0,
            'upcoming_maintenance': stats.upcoming or 0
        }

    @staticmethod
    def get_equipment_stats() -> Dict:
        """Retorna estatísticas gerais dos equipamentos"""
        stats = db.session.query(
            func.count(Equipment.id).label('total'),
            func.count(case((Equipment.status == 'disponivel', 1))).label('disponiveis'),
            func.count(case((Equipment.status == 'emprestado', 1))).label('emprestados'),
            func.count(case((Equipment.status == 'manutencao', 1))).label('manutencao'),
            func.count(case((Equipment.status == 'danificado', 1))).label('danificados')
        ).first()

        active_loans = EquipmentLoan.query.filter_by(status="ativo").count()
        overdue_loans = len(EquipmentService.get_overdue_loans())

        return {
            'total_equipment': stats.total or 0,
            'available_equipment': stats.disponiveis or 0,
            'loaned_equipment': stats.emprestados or 0,
            'maintenance_equipment': stats.manutencao or 0,
            'damaged_equipment': stats.danificados or 0,
            'active_loans': active_loans,
            'overdue_loans': overdue_loans
        }

    @staticmethod
    def migrate_legacy_requests():
        """Migra solicitações antigas para o novo sistema (se necessário)"""
        # TODO: Implementar migração quando necessário
        pass