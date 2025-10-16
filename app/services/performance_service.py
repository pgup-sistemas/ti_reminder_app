"""
Serviço de monitoramento de performance e otimização
"""
import logging
import time
from functools import wraps

from flask import current_app, g, request

logger = logging.getLogger(__name__)


class PerformanceService:
    """
    Serviço para monitoramento de performance e otimização de queries
    """

    @staticmethod
    def time_request(f):
        """Decorator para medir tempo de execução de requests"""
        @wraps(f)
        def decorated_function(*args, **kwargs):
            start_time = time.time()
            result = f(*args, **kwargs)
            end_time = time.time()

            execution_time = end_time - start_time

            # Log se demorar mais que 1 segundo
            if execution_time > 1.0:
                logger.warning(f"Request lento: {request.path} - {execution_time:.2f}s")

            # Armazenar no contexto da requisição
            g.request_time = execution_time

            return result
        return decorated_function

    @staticmethod
    def optimize_query_performance():
        """
        Otimizações gerais de performance para queries
        """
        from ..models import db

        # Configurações de performance do SQLAlchemy
        db.session.execute("SET work_mem = '64MB'")
        db.session.execute("SET maintenance_work_mem = '128MB'")
        db.session.execute("SET effective_cache_size = '1GB'")
        db.session.commit()

        logger.info("Otimizações de performance aplicadas ao banco de dados")

    @staticmethod
    def get_performance_metrics():
        """
        Coleta métricas de performance do sistema
        """
        try:
            import psutil
            import os

            # Métricas de CPU
            cpu_percent = psutil.cpu_percent(interval=1)

            # Métricas de memória
            memory = psutil.virtual_memory()
            memory_percent = memory.percent
            memory_used_gb = memory.used / (1024**3)

            # Métricas de disco
            disk = psutil.disk_usage('/')
            disk_percent = disk.percent
            disk_used_gb = disk.used / (1024**3)

            # Métricas da aplicação
            process = psutil.Process(os.getpid())
            app_memory_mb = process.memory_info().rss / (1024**2)
            app_cpu_percent = process.cpu_percent(interval=1)

            return {
                "cpu_percent": cpu_percent,
                "memory_percent": memory_percent,
                "memory_used_gb": round(memory_used_gb, 2),
                "disk_percent": disk_percent,
                "disk_used_gb": round(disk_used_gb, 2),
                "app_memory_mb": round(app_memory_mb, 2),
                "app_cpu_percent": app_cpu_percent,
                "timestamp": time.time()
            }

        except ImportError as e:
            logger.warning(f"psutil não instalado, retornando métricas básicas: {str(e)}")
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "memory_used_gb": 0,
                "disk_percent": 0,
                "disk_used_gb": 0,
                "app_memory_mb": 0,
                "app_cpu_percent": 0,
                "timestamp": time.time(),
                "warning": "psutil não instalado - métricas limitadas"
            }

        except Exception as e:
            logger.error(f"Erro ao coletar métricas de performance: {str(e)}")
            return {
                "cpu_percent": 0,
                "memory_percent": 0,
                "memory_used_gb": 0,
                "disk_percent": 0,
                "disk_used_gb": 0,
                "app_memory_mb": 0,
                "app_cpu_percent": 0,
                "error": str(e),
                "timestamp": time.time()
            }

    @staticmethod
    def get_database_performance_stats():
        """
        Estatísticas de performance do banco de dados
        """
        from ..models import db
        from sqlalchemy import text

        try:
            # Primeiro, vamos verificar se temos acesso às tabelas de estatísticas
            check_access_query = text("""
            SELECT
                COUNT(*) as table_count,
                (SELECT COUNT(*) FROM pg_stat_user_tables LIMIT 1) as has_stats_access
            FROM information_schema.tables
            WHERE table_schema = 'information_schema'
            """)

            access_check = db.session.execute(check_access_query)
            access_result = access_check.fetchone()

            logger.info(f"Database access check: {access_result.table_count} tables, stats access: {access_result.has_stats_access}")

            # Query para estatísticas de tabelas com tratamento de erro melhorado
            table_stats = []
            try:
                table_stats_query = text("""
                SELECT
                    schemaname,
                    relname as tablename,
                    n_tup_ins as inserts,
                    n_tup_upd as updates,
                    n_tup_del as deletes,
                    n_live_tup as live_rows,
                    n_dead_tup as dead_rows
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
                ORDER BY n_live_tup DESC
                LIMIT 10
                """)

                result = db.session.execute(table_stats_query)
                for row in result:
                    table_stats.append({
                        "table": row.tablename,
                        "live_rows": row.live_rows or 0,
                        "dead_rows": row.dead_rows or 0,
                        "inserts": row.inserts or 0,
                        "updates": row.updates or 0,
                        "deletes": row.deletes or 0
                    })

                logger.info(f"Table stats collected: {len(table_stats)} tables")

            except Exception as table_error:
                logger.warning(f"Erro ao coletar estatísticas das tabelas: {str(table_error)}")
                # Tentar uma abordagem alternativa - listar tabelas básicas
                try:
                    basic_tables_query = text("""
                    SELECT
                        table_name as tablename,
                        0 as live_rows,
                        0 as dead_rows,
                        0 as inserts,
                        0 as updates,
                        0 as deletes
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                    LIMIT 10
                    """)

                    result = db.session.execute(basic_tables_query)
                    for row in result:
                        table_stats.append({
                            "table": row.tablename,
                            "live_rows": row.live_rows,
                            "dead_rows": row.dead_rows,
                            "inserts": row.inserts,
                            "updates": row.updates,
                            "deletes": row.deletes
                        })
                    logger.info(f"Basic table list collected: {len(table_stats)} tables")
                except basic_error:
                    logger.error(f"Erro ao listar tabelas básicas: {str(basic_error)}")

            # Query para conexões ativas
            active_connections = 0
            try:
                connections_query = text("""
                SELECT count(*) as active_connections
                FROM pg_stat_activity
                WHERE state = 'active' AND datname = current_database()
                """)

                result = db.session.execute(connections_query)
                active_connections = result.scalar() or 0
                logger.info(f"Active connections: {active_connections}")

            except Exception as conn_error:
                logger.warning(f"Erro ao contar conexões ativas: {str(conn_error)}")

            # Query para cache hit ratio
            cache_hit_ratio = 0
            try:
                cache_query = text("""
                SELECT
                    sum(blks_hit)::float * 100 / NULLIF((sum(blks_hit) + sum(blks_read)), 0) as cache_hit_ratio
                FROM pg_stat_database
                WHERE datname = current_database()
                """)

                result = db.session.execute(cache_query)
                cache_hit_ratio = result.scalar() or 0
                cache_hit_ratio = round(cache_hit_ratio, 2) if cache_hit_ratio else 0
                logger.info(f"Cache hit ratio: {cache_hit_ratio}%")

            except Exception as cache_error:
                logger.warning(f"Erro ao calcular cache hit ratio: {str(cache_error)}")

            return {
                "table_stats": table_stats,
                "active_connections": active_connections,
                "cache_hit_ratio": cache_hit_ratio,
                "timestamp": time.time(),
                "debug_info": {
                    "tables_found": len(table_stats),
                    "access_check": access_result._asdict() if access_result else None
                }
            }

        except Exception as e:
            logger.error(f"Erro geral ao coletar estatísticas do banco: {str(e)}")
            return {
                "table_stats": [],
                "active_connections": 0,
                "cache_hit_ratio": 0,
                "error": str(e),
                "timestamp": time.time(),
                "debug_info": {
                    "error_type": type(e).__name__,
                    "error_details": str(e)
                }
            }

    @staticmethod
    def create_database_indexes():
        """
        Cria índices otimizados para melhor performance
        """
        from ..models import db

        try:
            indexes_created = []

            # Índice para buscas rápidas em chamados por status e data
            db.session.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chamado_status_data
                ON chamado (status, data_abertura DESC)
            """)
            indexes_created.append("idx_chamado_status_data")

            # Índice para buscas em lembretes por data e status
            db.session.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_reminder_due_date_status
                ON reminder (due_date, status, user_id)
            """)
            indexes_created.append("idx_reminder_due_date_status")

            # Índice para buscas em tarefas por data e status
            db.session.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_task_date_completed
                ON task (date DESC, completed, user_id)
            """)
            indexes_created.append("idx_task_date_completed")

            # Índice para RFID
            db.session.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_equipment_rfid
                ON equipment_request (rfid_tag, rfid_status)
            """)
            indexes_created.append("idx_equipment_rfid")

            # Índice para satisfação
            db.session.execute("""
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chamado_satisfaction
                ON chamado (satisfaction_rating, satisfaction_date DESC)
            """)
            indexes_created.append("idx_chamado_satisfaction")

            db.session.commit()

            logger.info(f"Índices criados: {', '.join(indexes_created)}")
            return {
                "success": True,
                "indexes_created": indexes_created,
                "count": len(indexes_created)
            }

        except Exception as e:
            logger.error(f"Erro ao criar índices: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def cleanup_old_data(days_to_keep=365):
        """
        Limpa dados antigos para manter performance
        """
        from ..models import db
        from datetime import datetime, timedelta

        try:
            cutoff_date = datetime.utcnow() - timedelta(days=days_to_keep)

            # Limpar logs antigos (se existirem)
            # Por enquanto, apenas log da operação
            logger.info(f"Limpeza de dados antigos configurada para manter {days_to_keep} dias")

            # Em produção, poderia limpar:
            # - Logs de auditoria antigos
            # - Dados de cache expirados
            # - Backups antigos
            # - Etc.

            return {
                "success": True,
                "message": f"Configurado para manter dados dos últimos {days_to_keep} dias",
                "cutoff_date": cutoff_date.isoformat()
            }

        except Exception as e:
            logger.error(f"Erro na limpeza de dados: {str(e)}")
            return {
                "success": False,
                "error": str(e)
            }

    @staticmethod
    def generate_performance_report():
        """
        Gera relatório completo de performance
        """
        try:
            system_metrics = PerformanceService.get_performance_metrics()
            db_stats = PerformanceService.get_database_performance_stats()

            report = {
                "system_performance": system_metrics,
                "database_performance": db_stats,
                "recommendations": [],
                "generated_at": time.time()
            }

            # Análises e recomendações
            if system_metrics.get("cpu_percent", 0) > 80:
                report["recommendations"].append("CPU com uso elevado - considerar otimização de queries")

            if system_metrics.get("memory_percent", 0) > 85:
                report["recommendations"].append("Memória com uso elevado - considerar aumento de recursos")

            if db_stats.get("cache_hit_ratio", 0) < 95:
                report["recommendations"].append("Cache hit ratio baixo - considerar aumento de shared_buffers")

            if db_stats.get("active_connections", 0) > 50:
                report["recommendations"].append("Muitas conexões ativas - considerar connection pooling")

            return report

        except Exception as e:
            logger.error(f"Erro ao gerar relatório de performance: {str(e)}")
            return {
                "error": str(e),
                "generated_at": time.time()
            }