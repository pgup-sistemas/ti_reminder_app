"""
Serviço para gestão de certificações e métricas de contribuição
"""
import logging
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple

from flask import current_app

from ..models import (ComentarioTutorial, FeedbackTutorial, Tutorial,
                      UserCertification, ContributionMetrics, User, db)
from ..utils.timezone_utils import get_current_time_for_db

logger = logging.getLogger(__name__)


class CertificationService:
    """
    Serviço para gestão de certificações e cálculo de métricas de contribuição
    """

    @staticmethod
    def update_user_metrics(user_id: int) -> Dict:
        """
        Atualiza métricas de contribuição de um usuário

        Args:
            user_id: ID do usuário

        Returns:
            Dict com resultado da operação
        """
        try:
            user = User.query.get_or_404(user_id)

            # Obter ou criar métricas
            metrics = user.contribution_metrics
            if not metrics:
                metrics = ContributionMetrics(user_id=user_id)
                db.session.add(metrics)

            # Calcular métricas
            metrics.tutorials_created = Tutorial.query.filter_by(autor_id=user_id).count()

            # Visualizações dos tutoriais do usuário
            user_tutorials = Tutorial.query.filter_by(autor_id=user_id).all()
            metrics.tutorial_views = sum(len(t.visualizacoes) for t in user_tutorials)

            # Comentários feitos
            metrics.comments_made = ComentarioTutorial.query.filter_by(usuario_id=user_id).count()

            # Votos úteis recebidos
            metrics.helpful_votes = sum(
                len([f for f in t.feedbacks if f.util]) for t in user_tutorials
            )

            # Calcular pontos totais
            metrics.calculate_points()

            db.session.commit()

            logger.info(f"Métricas atualizadas para usuário {user.username}: {metrics.total_points} pontos")

            return {
                "success": True,
                "message": "Métricas atualizadas com sucesso",
                "metrics": metrics
            }

        except Exception as e:
            logger.error(f"Erro ao atualizar métricas: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": f"Erro interno: {str(e)}"
            }

    @staticmethod
    def award_certification(user_id: int, certification_type: str = None, level: int = None) -> Dict:
        """
        Atribui ou atualiza certificação para um usuário

        Args:
            user_id: ID do usuário
            certification_type: Tipo de certificação (opcional, será calculado se não informado)
            level: Nível da certificação (opcional, será calculado se não informado)

        Returns:
            Dict com resultado da operação
        """
        try:
            user = User.query.get_or_404(user_id)

            # Atualizar métricas primeiro
            metrics_result = CertificationService.update_user_metrics(user_id)
            if not metrics_result["success"]:
                return metrics_result

            metrics = metrics_result["metrics"]

            # Determinar tipo e nível se não fornecidos
            if not certification_type or not level:
                certification_type, level = metrics.get_certification_level()

            # Verificar se já possui certificação ativa do mesmo tipo
            existing_cert = UserCertification.query.filter_by(
                user_id=user_id,
                certification_type=certification_type,
                is_active=True
            ).first()

            if existing_cert:
                # Atualizar certificação existente
                if existing_cert.level != level:
                    existing_cert.level = level
                    existing_cert.awarded_at = get_current_time_for_db()
                    # Extender validade por 1 ano
                    existing_cert.expires_at = get_current_time_for_db() + timedelta(days=365)

                    db.session.commit()

                    logger.info(f"Certificação atualizada para {user.username}: {certification_type} Level {level}")

                    return {
                        "success": True,
                        "message": f"Certificação atualizada para {certification_type} Level {level}",
                        "certification": existing_cert
                    }
                else:
                    return {
                        "success": True,
                        "message": "Usuário já possui esta certificação no nível atual",
                        "certification": existing_cert
                    }
            else:
                # Criar nova certificação
                certification = UserCertification(
                    user_id=user_id,
                    certification_type=certification_type,
                    level=level,
                    points=metrics.total_points,
                    expires_at=get_current_time_for_db() + timedelta(days=365)
                )

                db.session.add(certification)
                db.session.commit()

                logger.info(f"Nova certificação atribuída para {user.username}: {certification_type} Level {level}")

                return {
                    "success": True,
                    "message": f"Certificação {certification_type} Level {level} atribuída com sucesso",
                    "certification": certification
                }

        except Exception as e:
            logger.error(f"Erro ao atribuir certificação: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": f"Erro interno: {str(e)}"
            }

    @staticmethod
    def check_expired_certifications() -> Dict:
        """
        Verifica e desativa certificações expiradas

        Returns:
            Dict com resultado da operação
        """
        try:
            now = get_current_time_for_db()

            expired_certs = UserCertification.query.filter(
                UserCertification.expires_at < now,
                UserCertification.is_active == True
            ).all()

            expired_count = 0
            for cert in expired_certs:
                cert.is_active = False
                expired_count += 1

            if expired_count > 0:
                db.session.commit()
                logger.info(f"{expired_count} certificações expiradas desativadas")

            return {
                "success": True,
                "message": f"{expired_count} certificações expiradas desativadas",
                "expired_count": expired_count
            }

        except Exception as e:
            logger.error(f"Erro ao verificar certificações expiradas: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "message": f"Erro interno: {str(e)}"
            }

    @staticmethod
    def get_leaderboard(limit: int = 10) -> List[Dict]:
        """
        Retorna ranking de contribuidores

        Args:
            limit: Número máximo de usuários no ranking

        Returns:
            Lista com ranking de contribuidores
        """
        try:
            # Buscar métricas ordenadas por pontos
            top_contributors = ContributionMetrics.query.join(User).filter(
                User.ativo == True
            ).order_by(ContributionMetrics.total_points.desc()).limit(limit).all()

            leaderboard = []
            for i, metrics in enumerate(top_contributors, 1):
                cert_type, cert_level = metrics.get_certification_level()

                leaderboard.append({
                    "rank": i,
                    "user_id": metrics.user_id,
                    "username": metrics.user.username,
                    "total_points": metrics.total_points,
                    "tutorials_created": metrics.tutorials_created,
                    "tutorial_views": metrics.tutorial_views,
                    "helpful_votes": metrics.helpful_votes,
                    "certification_type": cert_type,
                    "certification_level": cert_level
                })

            return leaderboard

        except Exception as e:
            logger.error(f"Erro ao gerar leaderboard: {str(e)}")
            return []

    @staticmethod
    def get_user_certifications(user_id: int) -> List[UserCertification]:
        """
        Retorna todas as certificações de um usuário

        Args:
            user_id: ID do usuário

        Returns:
            Lista de certificações
        """
        try:
            certifications = UserCertification.query.filter_by(
                user_id=user_id
            ).order_by(UserCertification.awarded_at.desc()).all()

            return certifications

        except Exception as e:
            logger.error(f"Erro ao buscar certificações do usuário {user_id}: {str(e)}")
            return []

    @staticmethod
    def get_certification_stats() -> Dict:
        """
        Retorna estatísticas gerais de certificações

        Returns:
            Dict com estatísticas
        """
        try:
            total_users = User.query.filter_by(ativo=True).count()
            total_certifications = UserCertification.query.filter_by(is_active=True).count()

            # Distribuição por tipo
            cert_types = db.session.query(
                UserCertification.certification_type,
                db.func.count(UserCertification.id)
            ).filter(UserCertification.is_active == True).group_by(
                UserCertification.certification_type
            ).all()

            # Distribuição por nível
            cert_levels = db.session.query(
                UserCertification.level,
                db.func.count(UserCertification.id)
            ).filter(UserCertification.is_active == True).group_by(
                UserCertification.level
            ).all()

            return {
                "total_users": total_users,
                "total_certifications": total_certifications,
                "certification_rate": round((total_certifications / total_users * 100), 1) if total_users > 0 else 0,
                "certification_types": dict(cert_types),
                "certification_levels": dict(cert_levels)
            }

        except Exception as e:
            logger.error(f"Erro ao calcular estatísticas de certificação: {str(e)}")
            return {
                "total_users": 0,
                "total_certifications": 0,
                "certification_rate": 0,
                "certification_types": {},
                "certification_levels": {}
            }

    @staticmethod
    def auto_update_certifications() -> Dict:
        """
        Método automático para atualizar certificações baseado em métricas
        Chamado pelo scheduler
        """
        try:
            # Buscar todos os usuários com métricas
            users_with_metrics = ContributionMetrics.query.all()

            updated_count = 0
            new_certifications = 0

            for metrics in users_with_metrics:
                # Verificar se certificação precisa ser atualizada
                current_cert_type, current_level = metrics.get_certification_level()

                # Verificar certificação ativa atual
                active_cert = UserCertification.query.filter_by(
                    user_id=metrics.user_id,
                    is_active=True
                ).order_by(UserCertification.awarded_at.desc()).first()

                needs_update = False
                if not active_cert:
                    needs_update = True
                elif active_cert.certification_type != current_cert_type or active_cert.level != current_level:
                    needs_update = True

                if needs_update:
                    result = CertificationService.award_certification(
                        metrics.user_id, current_cert_type, current_level
                    )
                    if result["success"]:
                        if active_cert:
                            updated_count += 1
                        else:
                            new_certifications += 1

            # Verificar certificações expiradas
            expired_result = CertificationService.check_expired_certifications()

            message = f"Certificações atualizadas: {updated_count} atualizadas, {new_certifications} novas"
            if expired_result["expired_count"] > 0:
                message += f", {expired_result['expired_count']} expiradas"

            logger.info(message)

            return {
                "success": True,
                "message": message,
                "updated": updated_count,
                "new": new_certifications,
                "expired": expired_result["expired_count"]
            }

        except Exception as e:
            logger.error(f"Erro na atualização automática de certificações: {str(e)}")
            return {
                "success": False,
                "message": f"Erro interno: {str(e)}"
            }