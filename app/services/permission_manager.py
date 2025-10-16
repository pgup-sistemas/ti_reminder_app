from typing import Dict, Any, Optional
from flask import session

from ..models import User, Reminder


class PermissionManager:
    """Gerenciador centralizado de permissões do sistema"""

    @staticmethod
    def get_user_permissions() -> Dict[str, Any]:
        """
        Obtém permissões do usuário atual da sessão

        Returns:
            Dict com informações de permissões
        """
        return {
            'is_admin': session.get('is_admin', False),
            'is_ti': session.get('is_ti', False),
            'user_id': session.get('user_id'),
            'username': session.get('username', ''),
            'can_view_all': session.get('is_admin', False) or session.get('is_ti', False),
            'can_edit_all': session.get('is_admin', False),
            'can_approve_equipment': session.get('is_admin', False) or session.get('is_ti', False),
            'can_manage_users': session.get('is_admin', False),
            'can_view_sla': session.get('is_admin', False),
            'can_export_reports': True,  # Todos podem exportar, mas com filtros baseados em permissões
        }

    @staticmethod
    def get_user_sector(user_id: Optional[int] = None) -> Optional[int]:
        """
        Obtém o setor do usuário baseado nos lembretes

        Args:
            user_id: ID do usuário (usa da sessão se não informado)

        Returns:
            ID do setor ou None
        """
        if not user_id:
            user_id = session.get('user_id')

        if not user_id:
            return None

        primeiro_lembrete = Reminder.query.filter_by(user_id=user_id).first()
        return primeiro_lembrete.sector_id if primeiro_lembrete and primeiro_lembrete.sector_id else None

    @staticmethod
    def can_user_access_task(user_id: int, task_user_id: int) -> bool:
        """
        Verifica se usuário pode acessar uma tarefa

        Args:
            user_id: ID do usuário solicitante
            task_user_id: ID do usuário dono da tarefa

        Returns:
            True se pode acessar
        """
        permissions = PermissionManager.get_user_permissions()
        if permissions['can_view_all']:
            return True
        return user_id == task_user_id

    @staticmethod
    def can_user_access_reminder(user_id: int, reminder_user_id: int) -> bool:
        """
        Verifica se usuário pode acessar um lembrete

        Args:
            user_id: ID do usuário solicitante
            reminder_user_id: ID do usuário dono do lembrete

        Returns:
            True se pode acessar
        """
        permissions = PermissionManager.get_user_permissions()
        if permissions['can_view_all']:
            return True
        return user_id == reminder_user_id

    @staticmethod
    def can_user_access_chamado(user_id: int, chamado_solicitante_id: Optional[int],
                               chamado_setor_id: Optional[int]) -> bool:
        """
        Verifica se usuário pode acessar um chamado

        Args:
            user_id: ID do usuário solicitante
            chamado_solicitante_id: ID do solicitante do chamado
            chamado_setor_id: ID do setor do chamado

        Returns:
            True se pode acessar
        """
        permissions = PermissionManager.get_user_permissions()

        # Admin vê tudo
        if permissions['is_admin']:
            return True

        # TI vê chamados do seu setor também
        if permissions['is_ti']:
            user_sector = PermissionManager.get_user_sector(user_id)
            return (chamado_solicitante_id == user_id or
                   (user_sector and chamado_setor_id == user_sector))

        # Usuário comum vê apenas os seus ou do seu setor
        user_sector = PermissionManager.get_user_sector(user_id)
        return (chamado_solicitante_id == user_id or
               (user_sector and chamado_setor_id == user_sector))

    @staticmethod
    def can_user_access_equipment(user_id: int, equipment_requester_id: int) -> bool:
        """
        Verifica se usuário pode acessar uma solicitação de equipamento

        Args:
            user_id: ID do usuário solicitante
            equipment_requester_id: ID do solicitante do equipamento

        Returns:
            True se pode acessar
        """
        permissions = PermissionManager.get_user_permissions()
        if permissions['can_view_all']:
            return True
        return user_id == equipment_requester_id

    @staticmethod
    def can_user_edit_task(user_id: int, task_user_id: int) -> bool:
        """
        Verifica se usuário pode editar uma tarefa

        Args:
            user_id: ID do usuário solicitante
            task_user_id: ID do usuário dono da tarefa

        Returns:
            True se pode editar
        """
        permissions = PermissionManager.get_user_permissions()
        if permissions['can_edit_all']:
            return True
        return user_id == task_user_id

    @staticmethod
    def can_user_edit_reminder(user_id: int, reminder_user_id: int, reminder_autor_id: Optional[int] = None) -> bool:
        """
        Verifica se usuário pode editar um lembrete

        Args:
            user_id: ID do usuário solicitante
            reminder_user_id: ID do usuário dono do lembrete
            reminder_autor_id: ID do autor do lembrete (para TI)

        Returns:
            True se pode editar
        """
        permissions = PermissionManager.get_user_permissions()
        if permissions['can_edit_all']:
            return True
        # TI pode editar lembretes que criou
        if permissions['is_ti'] and reminder_autor_id == user_id:
            return True
        return user_id == reminder_user_id

    @staticmethod
    def can_user_edit_chamado(user_id: int, chamado_solicitante_id: int) -> bool:
        """
        Verifica se usuário pode editar um chamado (apenas o solicitante)

        Args:
            user_id: ID do usuário solicitante
            chamado_solicitante_id: ID do solicitante do chamado

        Returns:
            True se pode editar
        """
        # Apenas o solicitante pode editar chamados (não fechados)
        return user_id == chamado_solicitante_id

    @staticmethod
    def can_user_manage_chamado(user_id: int) -> bool:
        """
        Verifica se usuário pode gerenciar chamados (admin/TI)

        Args:
            user_id: ID do usuário

        Returns:
            True se pode gerenciar
        """
        permissions = PermissionManager.get_user_permissions()
        return permissions['is_admin'] or permissions['is_ti']

    @staticmethod
    def can_user_approve_equipment(user_id: int) -> bool:
        """
        Verifica se usuário pode aprovar solicitações de equipamento

        Args:
            user_id: ID do usuário

        Returns:
            True se pode aprovar
        """
        permissions = PermissionManager.get_user_permissions()
        return permissions['can_approve_equipment']

    @staticmethod
    def can_user_manage_users(user_id: int) -> bool:
        """
        Verifica se usuário pode gerenciar outros usuários

        Args:
            user_id: ID do usuário

        Returns:
            True se pode gerenciar
        """
        permissions = PermissionManager.get_user_permissions()
        return permissions['can_manage_users']

    @staticmethod
    def can_user_view_sla(user_id: int) -> bool:
        """
        Verifica se usuário pode ver dados SLA

        Args:
            user_id: ID do usuário

        Returns:
            True se pode ver SLA
        """
        permissions = PermissionManager.get_user_permissions()
        return permissions['can_view_sla']

    @staticmethod
    def can_user_export_with_filters(user_id: int, filters: Dict[str, Any]) -> bool:
        """
        Verifica se usuário pode exportar com os filtros aplicados

        Args:
            user_id: ID do usuário
            filters: Filtros aplicados

        Returns:
            True se pode exportar
        """
        permissions = PermissionManager.get_user_permissions()

        # Verificar se está tentando filtrar por usuário específico sem permissão
        if filters.get('user_id') and not permissions['can_view_all']:
            if filters['user_id'] != user_id:
                return False

        return permissions['can_export_reports']

    @staticmethod
    def filter_query_by_permissions(query, model_class: str, permissions: Dict[str, Any]):
        """
        Aplica filtros de permissão a uma query

        Args:
            query: Query do SQLAlchemy
            model_class: Nome da classe do modelo
            permissions: Dicionário de permissões

        Returns:
            Query filtrada
        """
        if permissions['can_view_all']:
            return query

        user_id = permissions['user_id']

        if model_class == 'Task':
            return query.filter_by(user_id=user_id)
        elif model_class == 'Reminder':
            return query.filter_by(user_id=user_id)
        elif model_class == 'Chamado':
            # Para chamados, incluir do setor também
            user_sector = PermissionManager.get_user_sector(user_id)
            if user_sector:
                from ..models import Chamado
                from sqlalchemy import or_
                return query.filter(
                    or_(
                        Chamado.solicitante_id == user_id,
                        Chamado.setor_id == user_sector
                    )
                )
            else:
                return query.filter_by(solicitante_id=user_id)
        elif model_class == 'EquipmentRequest':
            return query.filter_by(requester_id=user_id)

        return query