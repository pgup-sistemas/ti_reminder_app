from datetime import date, datetime, timedelta
from typing import Dict, List, Any, Optional
from sqlalchemy import func, case, and_, or_
from sqlalchemy.orm import Query

from ..models import (
    Task, Reminder, Chamado, EquipmentRequest, Sector, User,
    Tutorial, VisualizacaoTutorial, FeedbackTutorial, db
)


class DashboardService:
    """Serviço centralizado para lógica do dashboard"""

    @staticmethod
    def get_filtered_data(filters: Dict[str, Any], permissions: Dict[str, Any]) -> Dict[str, Any]:
        """
        Obtém dados filtrados do dashboard usando queries otimizadas

        Args:
            filters: Dicionário com filtros aplicados
            permissions: Dicionário com permissões do usuário

        Returns:
            Dict com todos os dados necessários para o dashboard
        """
        # Aplicar filtros baseados em permissões
        task_query = DashboardService._apply_base_filters(Task.query, permissions)
        reminder_query = DashboardService._apply_base_filters(Reminder.query, permissions)
        chamado_query = DashboardService._apply_base_filters_chamados(Chamado.query, permissions)
        equipment_query = DashboardService._apply_base_filters_equipment(EquipmentRequest.query, permissions)

        # Aplicar filtros específicos
        task_query = DashboardService._apply_task_filters(task_query, filters)
        reminder_query = DashboardService._apply_reminder_filters(reminder_query, filters)
        chamado_query = DashboardService._apply_chamado_filters(chamado_query, filters)
        equipment_query = DashboardService._apply_equipment_filters(equipment_query, filters)

        # Aplicar filtros de data
        task_query = DashboardService._apply_date_filters(task_query, filters, 'date')
        reminder_query = DashboardService._apply_date_filters(reminder_query, filters, 'due_date')
        chamado_query = DashboardService._apply_date_filters(chamado_query, filters, 'data_abertura')
        equipment_query = DashboardService._apply_date_filters(equipment_query, filters, 'request_date')

        # Aplicar filtros de setor
        if filters.get('sector_id'):
            task_query = task_query.filter(Task.sector_id == filters['sector_id'])
            reminder_query = reminder_query.filter(Reminder.sector_id == filters['sector_id'])
            chamado_query = chamado_query.filter(Chamado.setor_id == filters['sector_id'])
            # Para equipamentos, filtrar por setor de destino (string contains)
            sector_name = Sector.query.get(filters['sector_id']).name if Sector.query.get(filters['sector_id']) else ""
            equipment_query = equipment_query.filter(EquipmentRequest.destination_sector.contains(sector_name))

        # Aplicar filtros de usuário (apenas admin/TI)
        if filters.get('user_id') and (permissions.get('is_admin') or permissions.get('is_ti')):
            task_query = task_query.filter(Task.user_id == filters['user_id'])
            reminder_query = reminder_query.filter(Reminder.user_id == filters['user_id'])
            chamado_query = chamado_query.filter(Chamado.solicitante_id == filters['user_id'])
            equipment_query = equipment_query.filter(EquipmentRequest.requester_id == filters['user_id'])

        # Obter estatísticas otimizadas
        stats = DashboardService._calculate_optimized_stats(
            task_query, reminder_query, chamado_query, equipment_query
        )

        # Preparar dados para gráficos
        chart_data = DashboardService._prepare_chart_data(
            task_query, reminder_query, chamado_query, equipment_query, filters
        )

        # Obter dados SLA se for admin
        sla_data = {}
        if permissions.get('is_admin'):
            sla_data = DashboardService._calculate_sla_data()

        # Calculate overall performance
        performance = DashboardService._calculate_overall_performance(stats)

        return {
            'stats': stats,
            'chart_data': chart_data,
            'sla_data': sla_data,
            'performance': performance,
            'filters': filters,
            'permissions': permissions
        }

    @staticmethod
    def _apply_base_filters(query: Query, permissions: Dict[str, Any]) -> Query:
        """Aplica filtros base de permissões"""
        if not permissions.get('is_admin') and not permissions.get('is_ti'):
            # Usuário comum vê apenas seus itens
            return query.filter_by(user_id=permissions['user_id'])
        return query

    @staticmethod
    def _apply_base_filters_chamados(query: Query, permissions: Dict[str, Any]) -> Query:
        """Aplica filtros base específicos para chamados"""
        if not permissions.get('is_admin') and not permissions.get('is_ti'):
            # Usuário comum vê chamados que criou ou do seu setor
            user = User.query.get(permissions['user_id'])
            primeiro_lembrete = Reminder.query.filter_by(user_id=permissions['user_id']).first()
            setor_id_usuario = (
                primeiro_lembrete.sector_id
                if primeiro_lembrete and primeiro_lembrete.sector_id
                else None
            )
            return query.filter(
                or_(
                    Chamado.solicitante_id == permissions['user_id'],
                    Chamado.setor_id == setor_id_usuario
                )
            )
        elif not permissions.get('is_admin') and permissions.get('is_ti'):
            # TI vê chamados do seu setor também
            user = User.query.get(permissions['user_id'])
            primeiro_lembrete = Reminder.query.filter_by(user_id=permissions['user_id']).first()
            setor_id_usuario = (
                primeiro_lembrete.sector_id
                if primeiro_lembrete and primeiro_lembrete.sector_id
                else None
            )
            return query.filter(
                or_(
                    Chamado.solicitante_id == permissions['user_id'],
                    Chamado.setor_id == setor_id_usuario
                )
            )
        return query

    @staticmethod
    def _apply_base_filters_equipment(query: Query, permissions: Dict[str, Any]) -> Query:
        """Aplica filtros base específicos para equipamentos"""
        if not permissions.get('is_admin') and not permissions.get('is_ti'):
            # Usuário comum vê apenas suas solicitações
            return query.filter_by(requester_id=permissions['user_id'])
        # TI e Admin veem todas as solicitações
        return query

    @staticmethod
    def _apply_task_filters(query: Query, filters: Dict[str, Any]) -> Query:
        """Aplica filtros específicos para tarefas"""
        task_status = filters.get('task_status', '')
        if task_status == "done":
            return query.filter(Task.completed == True)
        elif task_status == "pending":
            return query.filter(
                and_(Task.completed == False, Task.date >= date.today())
            )
        elif task_status == "expired":
            return query.filter(
                and_(Task.completed == False, Task.date < date.today())
            )
        return query

    @staticmethod
    def _apply_reminder_filters(query: Query, filters: Dict[str, Any]) -> Query:
        """Aplica filtros específicos para lembretes"""
        reminder_status = filters.get('reminder_status', '')
        if reminder_status == "done":
            return query.filter(Reminder.completed == True)
        elif reminder_status == "pending":
            return query.filter(Reminder.completed == False)
        return query

    @staticmethod
    def _apply_chamado_filters(query: Query, filters: Dict[str, Any]) -> Query:
        """Aplica filtros específicos para chamados"""
        chamado_status = filters.get('chamado_status', '')
        if chamado_status:
            return query.filter(Chamado.status == chamado_status)
        return query

    @staticmethod
    def _apply_equipment_filters(query: Query, filters: Dict[str, Any]) -> Query:
        """Aplica filtros específicos para equipamentos"""
        # Por enquanto não há filtros específicos para equipamentos além dos base
        return query

    @staticmethod
    def _apply_date_filters(query: Query, filters: Dict[str, Any], date_field: str) -> Query:
        """Aplica filtros de data"""
        start_date = filters.get('start_date')
        end_date = filters.get('end_date')

        if start_date:
            query = query.filter(getattr(query.column_descriptions[0]['entity'], date_field) >= start_date)
        if end_date:
            query = query.filter(getattr(query.column_descriptions[0]['entity'], date_field) <= end_date)

        return query

    @staticmethod
    def _calculate_optimized_stats(task_query, reminder_query, chamado_query, equipment_query) -> Dict[str, Any]:
        """Calcula estatísticas usando agregações SQL otimizadas"""
        # Estatísticas de tarefas
        task_stats = db.session.query(
            func.count(Task.id).label('total'),
            func.count(case((Task.completed == True, 1))).label('done'),
            func.count(case((and_(Task.completed == False, Task.date >= date.today()), 1))).label('pending'),
            func.count(case((and_(Task.completed == False, Task.date < date.today()), 1))).label('expired')
        ).select_from(task_query.subquery()).first()

        # Estatísticas de lembretes
        reminder_stats = db.session.query(
            func.count(Reminder.id).label('total'),
            func.count(case((Reminder.completed == True, 1))).label('done'),
            func.count(case((Reminder.completed == False, 1))).label('pending')
        ).select_from(reminder_query.subquery()).first()

        # Estatísticas de chamados - removendo campos de satisfação que não existem na migração atual
        chamado_stats = db.session.query(
            func.count(Chamado.id).label('total'),
            func.count(case((Chamado.status == 'Aberto', 1))).label('aberto'),
            func.count(case((Chamado.status == 'Em Andamento', 1))).label('em_andamento'),
            func.count(case((Chamado.status == 'Resolvido', 1))).label('resolvido'),
            func.count(case((Chamado.status == 'Fechado', 1))).label('fechado')
        ).select_from(chamado_query.subquery()).first()

        # Estatísticas de equipamentos
        equipment_stats = db.session.query(
            func.count(EquipmentRequest.id).label('total'),
            func.count(case((EquipmentRequest.status == 'Solicitado', 1))).label('solicitados'),
            func.count(case((EquipmentRequest.status == 'Aprovado', 1))).label('aprovados'),
            func.count(case((EquipmentRequest.status == 'Entregue', 1))).label('entregues'),
            func.count(case((EquipmentRequest.status == 'Negado', 1))).label('negados'),
            func.count(case((EquipmentRequest.status == 'Devolvido', 1))).label('devolvidos')
        ).select_from(equipment_query.subquery()).first()

        return {
            'tasks': {
                'total': task_stats.total or 0,
                'done': task_stats.done or 0,
                'pending': task_stats.pending or 0,
                'expired': task_stats.expired or 0
            },
            'reminders': {
                'total': reminder_stats.total or 0,
                'done': reminder_stats.done or 0,
                'pending': reminder_stats.pending or 0
            },
            'chamados': {
                'total': chamado_stats.total or 0,
                'aberto': chamado_stats.aberto or 0,
                'em_andamento': chamado_stats.em_andamento or 0,
                'resolvido': chamado_stats.resolvido or 0,
                'fechado': chamado_stats.fechado or 0
            },
            'equipamentos': {
                'total': equipment_stats.total or 0,
                'solicitados': equipment_stats.solicitados or 0,
                'aprovados': equipment_stats.aprovados or 0,
                'entregues': equipment_stats.entregues or 0,
                'negados': equipment_stats.negados or 0,
                'devolvidos': equipment_stats.devolvidos or 0
            }
        }

    @staticmethod
    def _prepare_chart_data(task_query, reminder_query, chamado_query, equipment_query, filters) -> Dict[str, Any]:
        """Prepara dados para gráficos"""
        # Dados para gráfico de evolução (últimos 12 meses)
        chart_data = DashboardService._prepare_evolution_chart(task_query, reminder_query, chamado_query, equipment_query)

        # Dados para gráfico de setores
        sector_chart = DashboardService._prepare_sector_chart()

        # Dados para tutoriais
        tutorial_data = DashboardService._prepare_tutorial_data()

        return {
            'evolution': chart_data,
            'sectors': sector_chart,
            'tutorials': tutorial_data
        }

    @staticmethod
    def _prepare_evolution_chart(task_query, reminder_query, chamado_query, equipment_query):
        """Prepara dados para gráfico de evolução mensal"""
        from dateutil.relativedelta import relativedelta

        today = date.today()
        meses = []
        for i in range(11, -1, -1):
            m = today.replace(day=1) - relativedelta(months=i)
            meses.append(m)

        meses_labels = [m.strftime("%b/%Y") for m in meses]

        # Dados de tarefas por mês
        tarefas_por_mes = []
        lembretes_por_mes = []
        chamados_por_mes = []
        equipamentos_por_mes = []

        for idx, m in enumerate(meses):
            prox = m + relativedelta(months=1)

            # Tarefas no mês
            tarefas_mes = db.session.query(func.count(Task.id)).filter(
                and_(Task.date >= m, Task.date < prox)
            ).scalar()
            tarefas_por_mes.append(tarefas_mes or 0)

            # Lembretes no mês
            lembretes_mes = db.session.query(func.count(Reminder.id)).filter(
                and_(Reminder.due_date >= m, Reminder.due_date < prox)
            ).scalar()
            lembretes_por_mes.append(lembretes_mes or 0)

            # Chamados no mês
            chamados_mes = db.session.query(func.count(Chamado.id)).filter(
                and_(Chamado.data_abertura >= m, Chamado.data_abertura < prox)
            ).scalar()
            chamados_por_mes.append(chamados_mes or 0)

            # Equipamentos no mês
            equipamentos_mes = db.session.query(func.count(EquipmentRequest.id)).filter(
                and_(EquipmentRequest.request_date >= m, EquipmentRequest.request_date < prox)
            ).scalar()
            equipamentos_por_mes.append(equipamentos_mes or 0)

        return {
            'labels': meses_labels,
            'tarefas': tarefas_por_mes,
            'lembretes': lembretes_por_mes,
            'chamados': chamados_por_mes,
            'equipamentos': equipamentos_por_mes
        }

    @staticmethod
    def _prepare_sector_chart():
        """Prepara dados para gráfico de distribuição por setor"""
        sectors = Sector.query.order_by(Sector.name).all()
        setores_labels = [s.name for s in sectors]

        tarefas_por_setor = []
        lembretes_por_setor = []
        chamados_por_setor = []
        equipamentos_por_setor = []

        for sector in sectors:
            # Tarefas por setor
            tarefas_count = Task.query.filter_by(sector_id=sector.id).count()
            tarefas_por_setor.append(tarefas_count)

            # Lembretes por setor
            lembretes_count = Reminder.query.filter_by(sector_id=sector.id).count()
            lembretes_por_setor.append(lembretes_count)

            # Chamados por setor
            chamados_count = Chamado.query.filter_by(setor_id=sector.id).count()
            chamados_por_setor.append(chamados_count)

            # Equipamentos por setor (baseado em destination_sector)
            equipamentos_count = EquipmentRequest.query.filter(
                EquipmentRequest.destination_sector.contains(sector.name)
            ).count()
            equipamentos_por_setor.append(equipamentos_count)

        return {
            'labels': setores_labels,
            'tarefas': tarefas_por_setor,
            'lembretes': lembretes_por_setor,
            'chamados': chamados_por_setor,
            'equipamentos': equipamentos_por_setor
        }

    @staticmethod
    def _prepare_tutorial_data():
        """Prepara dados para estatísticas de tutoriais"""
        total_tutoriais = Tutorial.query.count()

        # Feedbacks agregados
        feedbacks = FeedbackTutorial.query.all()
        feedbacks_util = sum(1 for f in feedbacks if f.util)
        feedbacks_nao_util = sum(1 for f in feedbacks if not f.util)

        # Top tutoriais mais visualizados
        visualizacoes_por_tutorial = {}
        for v in VisualizacaoTutorial.query.all():
            if v.tutorial_id not in visualizacoes_por_tutorial:
                visualizacoes_por_tutorial[v.tutorial_id] = 0
            visualizacoes_por_tutorial[v.tutorial_id] += 1

        top_tutoriais_ids = sorted(
            visualizacoes_por_tutorial,
            key=visualizacoes_por_tutorial.get,
            reverse=True
        )[:5]

        top_tutoriais = [Tutorial.query.get(tid) for tid in top_tutoriais_ids if Tutorial.query.get(tid)]
        top_tutoriais_labels = [t.titulo for t in top_tutoriais]
        top_tutoriais_values = [visualizacoes_por_tutorial[t.id] for t in top_tutoriais]

        return {
            'total': total_tutoriais,
            'feedbacks_util': feedbacks_util,
            'feedbacks_nao_util': feedbacks_nao_util,
            'top_labels': top_tutoriais_labels,
            'top_values': top_tutoriais_values
        }

    @staticmethod
    def _calculate_sla_data():
        """Calcula dados SLA para administradores"""
        from ..utils.timezone_utils import get_current_time_for_db

        # Buscar chamados abertos
        chamados_abertos = Chamado.query.filter(Chamado.status != "Fechado").all()

        # Calcular SLA se necessário
        for chamado in chamados_abertos:
            if not chamado.prazo_sla:
                chamado.calcular_sla()

        db.session.commit()

        # Contar status SLA
        sla_vencidos = 0
        sla_criticos = 0
        sla_ok = 0

        for chamado in chamados_abertos:
            status_sla = chamado.status_sla
            if status_sla == "vencido":
                sla_vencidos += 1
            elif status_sla == "atencao":
                sla_criticos += 1
            elif status_sla == "normal":
                sla_ok += 1

        # Performance SLA (últimos 30 dias)
        trinta_dias_atras = get_current_time_for_db() - timedelta(days=30)
        chamados_fechados_30_dias = Chamado.query.filter(
            and_(
                Chamado.data_fechamento >= trinta_dias_atras,
                Chamado.data_fechamento.isnot(None)
            )
        ).all()

        performance_sla = 0
        if chamados_fechados_30_dias:
            # Calcular SLA para chamados que não têm sla_cumprido definido
            for chamado in chamados_fechados_30_dias:
                if chamado.sla_cumprido is None and chamado.prazo_sla:
                    chamado.sla_cumprido = chamado.data_fechamento <= chamado.prazo_sla

            db.session.commit()

            sla_cumpridos = len([c for c in chamados_fechados_30_dias if c.sla_cumprido])
            performance_sla = round((sla_cumpridos / len(chamados_fechados_30_dias)) * 100)

        return {
            'vencidos': sla_vencidos,
            'criticos': sla_criticos,
            'ok': sla_ok,
            'performance': performance_sla,
            'chamados_sla': chamados_abertos
        }

    @staticmethod
    def _calculate_overall_performance(stats: Dict[str, Any]) -> float:
        """
        Calculate overall system performance percentage

        Args:
            stats: Statistics dictionary

        Returns:
            Performance percentage (0-100)
        """
        total_tasks = stats['tasks']['total']
        completed_tasks = stats['tasks']['done']

        total_reminders = stats['reminders']['total']
        completed_reminders = stats['reminders']['done']

        total_chamados = stats['chamados']['total']
        completed_chamados = stats['chamados']['fechado']

        total_activities = total_tasks + total_reminders + total_chamados
        completed_activities = completed_tasks + completed_reminders + completed_chamados

        if total_activities == 0:
            return 0.0

        return round((completed_activities / total_activities) * 100, 1)