"""
Analytics Service
Serviço responsável por gerar métricas e análises do sistema
"""
from datetime import datetime, timedelta
from sqlalchemy import func, and_, or_
from app import db
from app.models import Chamado, User, Reminder, Task, EquipmentLoan, Sector


class AnalyticsService:
    """Serviço de analytics e métricas"""
    
    @staticmethod
    def get_chamados_por_periodo(start_date, end_date, group_by='day'):
        """
        Retorna chamados agrupados por período
        
        Args:
            start_date: Data inicial
            end_date: Data final
            group_by: Agrupamento ('day', 'week', 'month')
            
        Returns:
            Lista de dicionários com período e total
        """
        try:
            # PostgreSQL date_trunc
            query = db.session.query(
                func.date_trunc(group_by, Chamado.data_abertura).label('periodo'),
                func.count(Chamado.id).label('total')
            ).filter(
                Chamado.data_abertura.between(start_date, end_date)
            ).group_by('periodo').order_by('periodo')
            
            results = query.all()
            return [
                {
                    'periodo': r.periodo.strftime('%Y-%m-%d') if r.periodo else '',
                    'total': r.total
                }
                for r in results
            ]
        except Exception as e:
            print(f"Erro ao buscar chamados por período: {e}")
            return []
    
    @staticmethod
    def get_chamados_por_status():
        """Retorna distribuição de chamados por status"""
        try:
            query = db.session.query(
                Chamado.status,
                func.count(Chamado.id).label('total')
            ).group_by(Chamado.status).all()
            
            return [
                {'status': r.status, 'total': r.total}
                for r in query
            ]
        except Exception as e:
            print(f"Erro ao buscar chamados por status: {e}")
            return []
    
    @staticmethod
    def get_chamados_por_prioridade(start_date=None, end_date=None):
        """Retorna distribuição de chamados por prioridade"""
        try:
            query = db.session.query(
                Chamado.prioridade,
                func.count(Chamado.id).label('total')
            )
            
            if start_date and end_date:
                query = query.filter(Chamado.data_abertura.between(start_date, end_date))
            
            query = query.group_by(Chamado.prioridade).all()
            
            return [
                {'prioridade': r.prioridade, 'total': r.total}
                for r in query
            ]
        except Exception as e:
            print(f"Erro ao buscar chamados por prioridade: {e}")
            return []
    
    @staticmethod
    def get_sla_compliance(start_date, end_date):
        """
        Retorna taxa de cumprimento de SLA
        
        Args:
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Dicionário com total, cumpridos e taxa
        """
        try:
            total = Chamado.query.filter(
                Chamado.data_abertura.between(start_date, end_date)
            ).count()
            
            cumpridos = Chamado.query.filter(
                Chamado.data_abertura.between(start_date, end_date),
                Chamado.sla_cumprido == True
            ).count()
            
            taxa = (cumpridos / total * 100) if total > 0 else 0
            
            return {
                'total': total,
                'cumpridos': cumpridos,
                'nao_cumpridos': total - cumpridos,
                'taxa': round(taxa, 1)
            }
        except Exception as e:
            print(f"Erro ao calcular SLA compliance: {e}")
            return {'total': 0, 'cumpridos': 0, 'nao_cumpridos': 0, 'taxa': 0}
    
    @staticmethod
    def get_performance_por_tecnico(start_date, end_date):
        """
        Retorna performance de cada técnico
        
        Args:
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            Lista de dicionários com dados do técnico
        """
        try:
            query = db.session.query(
                User.username,
                User.email,
                func.count(Chamado.id).label('total_chamados'),
                func.avg(Chamado.tempo_resposta_horas).label('tempo_medio'),
                func.sum(
                    func.cast(Chamado.sla_cumprido == True, db.Integer)
                ).label('sla_cumprido')
            ).join(
                Chamado, Chamado.responsavel_ti_id == User.id
            ).filter(
                Chamado.data_abertura.between(start_date, end_date),
                User.is_ti == True
            ).group_by(User.id, User.username, User.email).all()
            
            return [
                {
                    'tecnico': r.username,
                    'email': r.email,
                    'total': r.total_chamados,
                    'tempo_medio': round(r.tempo_medio or 0, 2),
                    'sla_cumprido': r.sla_cumprido or 0,
                    'sla_taxa': round((r.sla_cumprido / r.total_chamados * 100) if r.total_chamados > 0 else 0, 1)
                }
                for r in query
            ]
        except Exception as e:
            print(f"Erro ao buscar performance por técnico: {e}")
            return []
    
    @staticmethod
    def get_chamados_por_setor(start_date=None, end_date=None):
        """Retorna distribuição de chamados por setor"""
        try:
            query = db.session.query(
                Sector.name,
                func.count(Chamado.id).label('total')
            ).join(
                Chamado, Chamado.setor_id == Sector.id
            )
            
            if start_date and end_date:
                query = query.filter(Chamado.data_abertura.between(start_date, end_date))
            
            query = query.group_by(Sector.id, Sector.name).order_by(func.count(Chamado.id).desc()).all()
            
            return [
                {'setor': r.name, 'total': r.total}
                for r in query
            ]
        except Exception as e:
            print(f"Erro ao buscar chamados por setor: {e}")
            return []
    
    @staticmethod
    def get_dashboard_kpis():
        """
        Retorna KPIs principais para o dashboard
        
        Returns:
            Dicionário com métricas principais
        """
        try:
            hoje = datetime.now().date()
            mes_atual = hoje.replace(day=1)
            mes_anterior = (mes_atual - timedelta(days=1)).replace(day=1)
            
            # Chamados abertos
            chamados_abertos = Chamado.query.filter(
                Chamado.status.in_(['Aberto', 'Em Andamento'])
            ).count()
            
            # Chamados do mês atual
            chamados_mes = Chamado.query.filter(
                Chamado.data_abertura >= mes_atual
            ).count()
            
            # Chamados mês anterior
            chamados_mes_ant = Chamado.query.filter(
                Chamado.data_abertura >= mes_anterior,
                Chamado.data_abertura < mes_atual
            ).count()
            
            # Variação percentual
            variacao = 0
            if chamados_mes_ant > 0:
                variacao = ((chamados_mes - chamados_mes_ant) / chamados_mes_ant) * 100
            
            # SLA do mês
            sla_data = AnalyticsService.get_sla_compliance(mes_atual, hoje)
            
            # Satisfação média
            satisfacao = db.session.query(
                func.avg(Chamado.satisfaction_rating)
            ).filter(
                Chamado.satisfaction_date >= mes_atual,
                Chamado.satisfaction_rating.isnot(None)
            ).scalar() or 0
            
            # Lembretes ativos
            lembretes_ativos = Reminder.query.filter(
                Reminder.status == 'ativo',
                Reminder.completed == False
            ).count()
            
            # Lembretes vencidos
            lembretes_vencidos = Reminder.query.filter(
                Reminder.status == 'ativo',
                Reminder.completed == False,
                Reminder.due_date < hoje
            ).count()
            
            # Equipamentos em uso
            equipamentos_uso = EquipmentLoan.query.filter(
                EquipmentLoan.status.in_(['Aprovado', 'Entregue'])
            ).count()
            
            return {
                'chamados_abertos': chamados_abertos,
                'chamados_mes': chamados_mes,
                'variacao_percentual': round(variacao, 1),
                'sla_taxa': sla_data['taxa'],
                'satisfacao_media': round(satisfacao, 1),
                'lembretes_ativos': lembretes_ativos,
                'lembretes_vencidos': lembretes_vencidos,
                'equipamentos_uso': equipamentos_uso
            }
        except Exception as e:
            print(f"Erro ao buscar KPIs do dashboard: {e}")
            return {
                'chamados_abertos': 0,
                'chamados_mes': 0,
                'variacao_percentual': 0,
                'sla_taxa': 0,
                'satisfacao_media': 0,
                'lembretes_ativos': 0,
                'lembretes_vencidos': 0,
                'equipamentos_uso': 0
            }
    
    @staticmethod
    def get_tempo_medio_resolucao(start_date, end_date):
        """Retorna tempo médio de resolução de chamados"""
        try:
            # Apenas chamados fechados
            query = db.session.query(
                func.avg(
                    func.extract('epoch', Chamado.data_fechamento - Chamado.data_abertura) / 3600
                ).label('tempo_medio_horas')
            ).filter(
                Chamado.data_fechamento.isnot(None),
                Chamado.data_abertura.between(start_date, end_date)
            ).scalar()
            
            return round(query or 0, 2)
        except Exception as e:
            print(f"Erro ao calcular tempo médio de resolução: {e}")
            return 0
    
    @staticmethod
    def get_satisfacao_mensal(meses=6):
        """Retorna evolução da satisfação nos últimos meses"""
        try:
            hoje = datetime.now().date()
            data_inicio = hoje - timedelta(days=meses * 30)
            
            query = db.session.query(
                func.date_trunc('month', Chamado.satisfaction_date).label('mes'),
                func.avg(Chamado.satisfaction_rating).label('media')
            ).filter(
                Chamado.satisfaction_date >= data_inicio,
                Chamado.satisfaction_rating.isnot(None)
            ).group_by('mes').order_by('mes').all()
            
            return [
                {
                    'mes': r.mes.strftime('%Y-%m') if r.mes else '',
                    'media': round(r.media, 1)
                }
                for r in query
            ]
        except Exception as e:
            print(f"Erro ao buscar satisfação mensal: {e}")
            return []
