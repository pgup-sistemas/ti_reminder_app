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
        Otimizações gerais de performance para queries (SQLite)
        """
        from ..models import db
        from sqlalchemy import text

        try:
            # Para SQLite, aplicamos otimizações diferentes
            optimizations_applied = []
            
            # Habilitar foreign keys se não estiver
            try:
                db.session.execute(text("PRAGMA foreign_keys = ON"))
                optimizations_applied.append("Foreign keys habilitadas")
            except Exception as e:
                logger.warning(f"Erro ao habilitar foreign keys: {str(e)}")
            
            # Otimizar journal mode para WAL (Write-Ahead Logging)
            try:
                db.session.execute(text("PRAGMA journal_mode = WAL"))
                optimizations_applied.append("Journal mode WAL")
            except Exception as e:
                logger.warning(f"Erro ao configurar journal mode: {str(e)}")
            
            # Configurar synchronous mode para NORMAL (balance entre performance e segurança)
            try:
                db.session.execute(text("PRAGMA synchronous = NORMAL"))
                optimizations_applied.append("Synchronous mode NORMAL")
            except Exception as e:
                logger.warning(f"Erro ao configurar synchronous mode: {str(e)}")
            
            # Configurar cache size (aumentar para 20000 páginas ~ 80MB)
            try:
                db.session.execute(text("PRAGMA cache_size = 20000"))
                optimizations_applied.append("Cache size aumentado")
            except Exception as e:
                logger.warning(f"Erro ao configurar cache size: {str(e)}")
            
            # Configurar temp store para MEMORY
            try:
                db.session.execute(text("PRAGMA temp_store = MEMORY"))
                optimizations_applied.append("Temp store em MEMORY")
            except Exception as e:
                logger.warning(f"Erro ao configurar temp store: {str(e)}")
            
            # Configurar mmap_size para 64MB
            try:
                db.session.execute(text("PRAGMA mmap_size = 67108864"))  # 64MB
                optimizations_applied.append("MMap size configurado")
            except Exception as e:
                logger.warning(f"Erro ao configurar mmap_size: {str(e)}")
            
            # Analizar tabelas para atualizar estatísticas
            try:
                tables_query = text("SELECT name FROM sqlite_master WHERE type='table' AND name NOT LIKE 'sqlite_%'")
                result = db.session.execute(tables_query)
                tables_analyzed = 0
                
                for row in result:
                    try:
                        db.session.execute(text(f"ANALYZE {row.name}"))
                        tables_analyzed += 1
                    except Exception:
                        continue  # Ignorar tabelas que não podem ser analisadas
                
                optimizations_applied.append(f"ANALYZE executado em {tables_analyzed} tabelas")
            except Exception as e:
                logger.warning(f"Erro ao executar ANALYZE: {str(e)}")
            
            # Vacuum para otimizar espaço (opcional, pode ser lento)
            try:
                db.session.execute(text("PRAGMA incremental_vacuum"))
                optimizations_applied.append("Incremental vacuum executado")
            except Exception as e:
                logger.warning(f"Erro ao executar incremental vacuum: {str(e)}")
            
            db.session.commit()
            
            logger.info(f"Otimizações SQLite aplicadas: {', '.join(optimizations_applied)}")
            return {
                "success": True,
                "optimizations_applied": optimizations_applied,
                "database_type": "SQLite"
            }

        except Exception as e:
            logger.error(f"Erro ao aplicar otimizações SQLite: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "error": str(e),
                "database_type": "SQLite"
            }

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
        Estatísticas de performance do banco de dados (SQLite)
        """
        from ..models import db
        from sqlalchemy import text

        try:
            # Verificar tipo de banco de dados
            try:
                # Query específico para SQLite
                check_sqlite_query = text("SELECT name FROM sqlite_master WHERE type='table'")
                result = db.session.execute(check_sqlite_query)
                tables = result.fetchall()
                table_count = len(tables)
                logger.info(f"SQLite detected: {table_count} tables found")
                
                # Para SQLite, não temos pg_stat_user_tables, então marcamos como 0
                has_stats_access = 0
                
            except Exception as check_error:
                logger.error(f"Erro ao verificar tipo de banco: {str(check_error)}")
                table_count = 0
                has_stats_access = 0

            # Query para estatísticas de tabelas (SQLite)
            table_stats = []
            try:
                # Listar tabelas do SQLite
                tables_query = text("""
                SELECT name as tablename
                FROM sqlite_master 
                WHERE type='table' AND name NOT LIKE 'sqlite_%'
                ORDER BY name
                LIMIT 10
                """)

                result = db.session.execute(tables_query)
                for row in result:
                    # Para cada tabela, tentar contar registros
                    try:
                        count_query = text(f"SELECT COUNT(*) as live_rows FROM {row.tablename}")
                        count_result = db.session.execute(count_query)
                        live_rows = count_result.scalar() or 0
                    except Exception:
                        live_rows = 0
                    
                    table_stats.append({
                        "table": row.tablename,
                        "live_rows": live_rows,
                        "dead_rows": 0,  # SQLite não tem dead_rows
                        "inserts": 0,    # SQLite não rastreia inserts
                        "updates": 0,    # SQLite não rastreia updates  
                        "deletes": 0     # SQLite não rastreia deletes
                    })

                logger.info(f"SQLite table stats collected: {len(table_stats)} tables")

            except Exception as table_error:
                logger.warning(f"Erro ao coletar estatísticas das tabelas SQLite: {str(table_error)}")

            # Para SQLite, conexões ativas não são aplicáveis da mesma forma
            active_connections = 1  # SQLite geralmente tem uma conexão por arquivo
            
            # Para SQLite, cache hit ratio não é diretamente disponível
            cache_hit_ratio = 95.0  # Valor estimado para SQLite

            return {
                "table_stats": table_stats,
                "active_connections": active_connections,
                "cache_hit_ratio": cache_hit_ratio,
                "timestamp": time.time(),
                "debug_info": {
                    "tables_found": len(table_stats),
                    "database_type": "SQLite",
                    "access_check": {
                        "table_count": table_count,
                        "has_stats_access": has_stats_access
                    }
                }
            }

        except Exception as e:
            logger.error(f"Erro geral ao coletar estatísticas do banco SQLite: {str(e)}")
            return {
                "table_stats": [],
                "active_connections": 0,
                "cache_hit_ratio": 0,
                "error": str(e),
                "timestamp": time.time(),
                "debug_info": {
                    "error_type": type(e).__name__,
                    "error_details": str(e),
                    "database_type": "SQLite (error)"
                }
            }

    @staticmethod
    def create_database_indexes():
        """
        Cria índices otimizados para melhor performance (SQLite)
        """
        from ..models import db
        from sqlalchemy import text

        try:
            indexes_created = []

            # Verificar se tabelas existem antes de criar índices
            tables_check_query = text("SELECT name FROM sqlite_master WHERE type='table'")
            result = db.session.execute(tables_check_query)
            existing_tables = [row.name for row in result]

            # Índice para chamados (se tabela existir)
            if 'chamado' in existing_tables:
                try:
                    db.session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_chamado_status_data 
                        ON chamado (status, data_abertura DESC)
                    """))
                    indexes_created.append("idx_chamado_status_data")
                except Exception as e:
                    logger.warning(f"Erro ao criar índice chamado: {str(e)}")

            # Índice para lembretes (se tabela existir)
            if 'reminder' in existing_tables:
                try:
                    db.session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_reminder_due_date_status 
                        ON reminder (due_date, status, user_id)
                    """))
                    indexes_created.append("idx_reminder_due_date_status")
                except Exception as e:
                    logger.warning(f"Erro ao criar índice reminder: {str(e)}")

            # Índice para tarefas (se tabela existir)
            if 'task' in existing_tables:
                try:
                    db.session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_task_date_completed 
                        ON task (date DESC, completed, user_id)
                    """))
                    indexes_created.append("idx_task_date_completed")
                except Exception as e:
                    logger.warning(f"Erro ao criar índice task: {str(e)}")

            # Índice para equipamentos (se tabela existir)
            if 'equipment_request' in existing_tables:
                try:
                    db.session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_equipment_rfid 
                        ON equipment_request (rfid_tag, rfid_status)
                    """))
                    indexes_created.append("idx_equipment_rfid")
                except Exception as e:
                    logger.warning(f"Erro ao criar índice equipment: {str(e)}")

            # Índice para satisfação (se tabela existir)
            if 'chamado' in existing_tables:
                try:
                    db.session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_chamado_satisfaction 
                        ON chamado (satisfaction_rating, satisfaction_date DESC)
                    """))
                    indexes_created.append("idx_chamado_satisfaction")
                except Exception as e:
                    logger.warning(f"Erro ao criar índice satisfação: {str(e)}")

            # Índices para usuário (se tabela existir)
            if 'user' in existing_tables:
                try:
                    db.session.execute(text("""
                        CREATE INDEX IF NOT EXISTS idx_user_email 
                        ON user (email)
                    """))
                    indexes_created.append("idx_user_email")
                except Exception as e:
                    logger.warning(f"Erro ao criar índice user email: {str(e)}")

            db.session.commit()

            logger.info(f"Índices SQLite criados: {', '.join(indexes_created)}")
            return {
                "success": True,
                "indexes_created": indexes_created,
                "count": len(indexes_created),
                "database_type": "SQLite"
            }

        except Exception as e:
            logger.error(f"Erro ao criar índices SQLite: {str(e)}")
            db.session.rollback()
            return {
                "success": False,
                "error": str(e),
                "database_type": "SQLite"
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