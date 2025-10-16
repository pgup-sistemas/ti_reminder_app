"""
Serviço para gestão de métricas de satisfação do sistema
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional

from flask import current_app

from ..models import Chamado, db
from ..utils.timezone_utils import get_current_time_for_db

logger = logging.getLogger(__name__)


class SatisfactionService:
    """
    Serviço para coleta e análise de métricas de satisfação
    """

    @staticmethod
    def send_satisfaction_survey(chamado_id: int) -> Dict:
        """
        Envia pesquisa de satisfação para um chamado fechado

        Args:
            chamado_id: ID do chamado

        Returns:
            Dict com resultado da operação
        """
        try:
            chamado = Chamado.query.get_or_404(chamado_id)

            # Verificar se chamado está fechado
            if chamado.status != "Fechado":
                return {
                    "success": False,
                    "message": "Apenas chamados fechados podem receber pesquisa de satisfação"
                }

            # Verificar se já foi enviada
            if chamado.survey_sent:
                return {
                    "success": False,
                    "message": "Pesquisa de satisfação já foi enviada para este chamado"
                }

            # Marcar como enviada
            chamado.survey_sent = True
            chamado.survey_sent_date = get_current_time_for_db()

            db.session.commit()

            # Aqui seria integrada a lógica de envio de email
            # send_satisfaction_survey_email(chamado)

            logger.info(f"Pesquisa de satisfação enviada para chamado {chamado_id}")

            return {
                "success": True,
                "message": "Pesquisa de satisfação enviada com sucesso",
                "chamado": chamado
            }

        except Exception as e:
            logger.error(f"Erro ao enviar pesquisa de satisfação: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": f"Erro interno: {str(e)}"
            }

    @staticmethod
    def record_satisfaction_rating(chamado_id: int, rating: int, comment: str = None) -> Dict:
        """
        Registra avaliação de satisfação de um chamado

        Args:
            chamado_id: ID do chamado
            rating: Avaliação (1-5)
            comment: Comentário opcional

        Returns:
            Dict com resultado da operação
        """
        try:
            # Validar rating
            if not 1 <= rating <= 5:
                return {
                    "success": False,
                    "message": "Avaliação deve ser entre 1 e 5 estrelas"
                }

            chamado = Chamado.query.get_or_404(chamado_id)

            # Verificar se chamado está fechado
            if chamado.status != "Fechado":
                return {
                    "success": False,
                    "message": "Apenas chamados fechados podem ser avaliados"
                }

            # Registrar avaliação
            chamado.satisfaction_rating = rating
            chamado.satisfaction_comment = comment
            chamado.satisfaction_date = get_current_time_for_db()

            db.session.commit()

            logger.info(f"Avaliação de satisfação registrada para chamado {chamado_id}: {rating} estrelas")

            return {
                "success": True,
                "message": "Avaliação registrada com sucesso",
                "chamado": chamado
            }

        except Exception as e:
            logger.error(f"Erro ao registrar avaliação: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": f"Erro interno: {str(e)}"
            }

    @staticmethod
    def get_satisfaction_stats(days: int = 30) -> Dict:
        """
        Obtém estatísticas de satisfação dos últimos N dias

        Args:
            days: Número de dias para análise

        Returns:
            Dict com estatísticas
        """
        try:
            cutoff_date = get_current_time_for_db() - timedelta(days=days)

            # Buscar chamados fechados no período
            chamados = Chamado.query.filter(
                Chamado.data_fechamento >= cutoff_date,
                Chamado.data_fechamento.isnot(None),
                Chamado.satisfaction_rating.isnot(None)
            ).all()

            if not chamados:
                return {
                    "total_surveys": 0,
                    "average_rating": 0,
                    "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                    "response_rate": 0,
                    "period_days": days
                }

            # Calcular estatísticas
            ratings = [c.satisfaction_rating for c in chamados]
            total_surveys = len(chamados)

            # Distribuição de ratings
            rating_distribution = {1: 0, 2: 0, 3: 0, 4: 0, 5: 0}
            for rating in ratings:
                rating_distribution[rating] += 1

            # Média
            average_rating = sum(ratings) / len(ratings)

            # Taxa de resposta (chamados fechados que receberam avaliação)
            total_closed = Chamado.query.filter(
                Chamado.data_fechamento >= cutoff_date,
                Chamado.data_fechamento.isnot(None)
            ).count()

            response_rate = (total_surveys / total_closed * 100) if total_closed > 0 else 0

            return {
                "total_surveys": total_surveys,
                "average_rating": round(average_rating, 2),
                "rating_distribution": rating_distribution,
                "response_rate": round(response_rate, 1),
                "period_days": days,
                "total_closed_chamados": total_closed
            }

        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas de satisfação: {str(e)}")
            return {
                "total_surveys": 0,
                "average_rating": 0,
                "rating_distribution": {1: 0, 2: 0, 3: 0, 4: 0, 5: 0},
                "response_rate": 0,
                "period_days": days,
                "error": str(e)
            }

    @staticmethod
    def get_pending_surveys() -> List[Chamado]:
        """
        Retorna chamados fechados que ainda não receberam pesquisa de satisfação

        Returns:
            Lista de chamados pendentes
        """
        try:
            # Chamados fechados há mais de 1 dia e menos de 30 dias, sem pesquisa enviada
            one_day_ago = get_current_time_for_db() - timedelta(days=1)
            thirty_days_ago = get_current_time_for_db() - timedelta(days=30)

            pending_chamados = Chamado.query.filter(
                Chamado.status == "Fechado",
                Chamado.data_fechamento <= one_day_ago,
                Chamado.data_fechamento >= thirty_days_ago,
                Chamado.survey_sent == False
            ).order_by(Chamado.data_fechamento.desc()).all()

            return pending_chamados

        except Exception as e:
            logger.error(f"Erro ao buscar pesquisas pendentes: {str(e)}")
            return []

    @staticmethod
    def get_satisfaction_trends(months: int = 6) -> List[Dict]:
        """
        Obtém tendências de satisfação por mês

        Args:
            months: Número de meses para análise

        Returns:
            Lista com dados por mês
        """
        try:
            trends = []

            for i in range(months):
                # Calcular período do mês
                end_date = get_current_time_for_db() - timedelta(days=30 * i)
                start_date = end_date - timedelta(days=30)

                # Buscar avaliações do mês
                month_ratings = Chamado.query.filter(
                    Chamado.satisfaction_date >= start_date,
                    Chamado.satisfaction_date < end_date,
                    Chamado.satisfaction_rating.isnot(None)
                ).all()

                if month_ratings:
                    avg_rating = sum(c.satisfaction_rating for c in month_ratings) / len(month_ratings)
                    trends.append({
                        "month": end_date.strftime("%Y-%m"),
                        "month_name": end_date.strftime("%B %Y"),
                        "average_rating": round(avg_rating, 2),
                        "total_ratings": len(month_ratings)
                    })
                else:
                    trends.append({
                        "month": end_date.strftime("%Y-%m"),
                        "month_name": end_date.strftime("%B %Y"),
                        "average_rating": 0,
                        "total_ratings": 0
                    })

            return trends[::-1]  # Ordem cronológica

        except Exception as e:
            logger.error(f"Erro ao calcular tendências de satisfação: {str(e)}")
            return []

    @staticmethod
    def get_detailed_feedback(days: int = 30) -> List[Dict]:
        """
        Obtém feedback detalhado com comentários

        Args:
            days: Dias para buscar feedback

        Returns:
            Lista de feedback detalhado
        """
        try:
            cutoff_date = get_current_time_for_db() - timedelta(days=days)

            feedback_chamados = Chamado.query.filter(
                Chamado.satisfaction_date >= cutoff_date,
                Chamado.satisfaction_rating.isnot(None)
            ).order_by(Chamado.satisfaction_date.desc()).all()

            feedback_list = []
            for chamado in feedback_chamados:
                feedback_list.append({
                    "chamado_id": chamado.id,
                    "titulo": chamado.titulo,
                    "rating": chamado.satisfaction_rating,
                    "comment": chamado.satisfaction_comment,
                    "date": chamado.satisfaction_date,
                    "solicitante": chamado.solicitante.username if chamado.solicitante else "N/A",
                    "setor": chamado.setor.name if chamado.setor else "N/A"
                })

            return feedback_list

        except Exception as e:
            logger.error(f"Erro ao buscar feedback detalhado: {str(e)}")
            return []

    @staticmethod
    def auto_send_satisfaction_surveys() -> Dict:
        """
        Método automático para enviar pesquisas de satisfação pendentes
        Chamado pelo scheduler
        """
        try:
            pending_chamados = SatisfactionService.get_pending_surveys()
            sent_count = 0

            for chamado in pending_chamados:
                result = SatisfactionService.send_satisfaction_survey(chamado.id)
                if result["success"]:
                    sent_count += 1

            logger.info(f"Pesquisas de satisfação enviadas automaticamente: {sent_count}")

            return {
                "success": True,
                "message": f"{sent_count} pesquisas enviadas automaticamente",
                "sent_count": sent_count
            }

        except Exception as e:
            logger.error(f"Erro no envio automático de pesquisas: {str(e)}")
            return {
                "success": False,
                "message": f"Erro interno: {str(e)}"
            }