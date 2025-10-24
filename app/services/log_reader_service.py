"""
Serviço de Leitura de Logs
Lê e processa logs reais do sistema
"""

import os
import re
from datetime import datetime, timedelta
from flask import current_app


class LogReaderService:
    """Serviço para leitura e análise de logs do sistema"""
    
    # Padrões de regex para diferentes níveis de log
    LOG_PATTERN = re.compile(
        r'(?P<timestamp>\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2},\d{3})\s+'
        r'(?P<level>\w+)\s+'
        r'(?P<message>.+?)(?:\s+\[in\s+(?P<file>[^\]]+)\])?$'
    )
    
    LEVEL_PRIORITY = {
        'DEBUG': 0,
        'INFO': 1,
        'WARNING': 2,
        'ERROR': 3,
        'CRITICAL': 4
    }
    
    @classmethod
    def get_log_file_path(cls):
        """Retorna o caminho do arquivo de log"""
        log_file = current_app.config.get('LOG_FILE')
        if log_file and os.path.exists(log_file):
            return log_file
        
        # Tentar caminhos alternativos
        alternative_paths = [
            os.path.join(os.path.dirname(current_app.root_path), 'logs', 'app.log'),
            os.path.join(current_app.root_path, '..', 'logs', 'app.log'),
            'logs/app.log',
            'app.log'
        ]
        
        for path in alternative_paths:
            if os.path.exists(path):
                return path
        
        return None
    
    @classmethod
    def read_logs(cls, level=None, limit=100, offset=0, search=None, 
                  start_date=None, end_date=None):
        """
        Lê logs do arquivo
        
        Args:
            level: Filtrar por nível (DEBUG, INFO, WARNING, ERROR, CRITICAL)
            limit: Número máximo de logs a retornar
            offset: Offset para paginação
            search: Texto para buscar nas mensagens
            start_date: Data inicial do filtro
            end_date: Data final do filtro
            
        Returns:
            dict com logs e estatísticas
        """
        log_file = cls.get_log_file_path()
        
        if not log_file:
            return {
                'logs': [],
                'total': 0,
                'error': 'Arquivo de log não encontrado',
                'file_path': None
            }
        
        try:
            logs = []
            total_count = 0
            
            # Ler arquivo de trás para frente para pegar logs mais recentes primeiro
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            # Processar linhas de trás para frente
            for line in reversed(lines):
                line = line.strip()
                if not line:
                    continue
                
                # Tentar parsear a linha
                match = cls.LOG_PATTERN.match(line)
                if match:
                    log_data = match.groupdict()
                    
                    # Aplicar filtros
                    if level and log_data['level'] != level:
                        continue
                    
                    if search and search.lower() not in log_data['message'].lower():
                        continue
                    
                    # Parsear timestamp
                    try:
                        log_timestamp = datetime.strptime(
                            log_data['timestamp'], 
                            '%Y-%m-%d %H:%M:%S,%f'
                        )
                        
                        if start_date and log_timestamp < start_date:
                            continue
                        if end_date and log_timestamp > end_date:
                            continue
                        
                        log_data['timestamp'] = log_timestamp
                    except:
                        pass
                    
                    total_count += 1
                    
                    # Aplicar paginação
                    if total_count > offset and len(logs) < limit:
                        logs.append(log_data)
                    
                    if len(logs) >= limit:
                        break
            
            return {
                'logs': logs,
                'total': total_count,
                'file_path': log_file,
                'file_size': cls._get_file_size(log_file)
            }
            
        except Exception as e:
            current_app.logger.error(f"Erro ao ler logs: {e}")
            return {
                'logs': [],
                'total': 0,
                'error': str(e),
                'file_path': log_file
            }
    
    @classmethod
    def get_log_statistics(cls, hours=24):
        """
        Retorna estatísticas dos logs
        
        Args:
            hours: Número de horas para considerar
            
        Returns:
            dict com estatísticas
        """
        log_file = cls.get_log_file_path()
        
        if not log_file:
            return {
                'errors_count': 0,
                'warnings_count': 0,
                'info_count': 0,
                'debug_count': 0,
                'total_count': 0,
                'file_size': '0 B'
            }
        
        try:
            cutoff_time = datetime.now() - timedelta(hours=hours)
            stats = {
                'DEBUG': 0,
                'INFO': 0,
                'WARNING': 0,
                'ERROR': 0,
                'CRITICAL': 0
            }
            
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as f:
                for line in f:
                    match = cls.LOG_PATTERN.match(line.strip())
                    if match:
                        log_data = match.groupdict()
                        
                        # Verificar se está dentro do período
                        try:
                            log_time = datetime.strptime(
                                log_data['timestamp'],
                                '%Y-%m-%d %H:%M:%S,%f'
                            )
                            if log_time >= cutoff_time:
                                level = log_data['level']
                                if level in stats:
                                    stats[level] += 1
                        except:
                            pass
            
            return {
                'errors_count': stats['ERROR'] + stats['CRITICAL'],
                'warnings_count': stats['WARNING'],
                'info_count': stats['INFO'],
                'debug_count': stats['DEBUG'],
                'total_count': sum(stats.values()),
                'file_size': cls._get_file_size(log_file)
            }
            
        except Exception as e:
            current_app.logger.error(f"Erro ao calcular estatísticas de logs: {e}")
            return {
                'errors_count': 0,
                'warnings_count': 0,
                'info_count': 0,
                'debug_count': 0,
                'total_count': 0,
                'file_size': '0 B'
            }
    
    @classmethod
    def clear_old_logs(cls, days=30):
        """
        Remove logs antigos do arquivo
        
        Args:
            days: Número de dias de logs para manter
            
        Returns:
            bool indicando sucesso
        """
        log_file = cls.get_log_file_path()
        
        if not log_file:
            return False
        
        try:
            cutoff_time = datetime.now() - timedelta(days=days)
            temp_file = log_file + '.tmp'
            lines_kept = 0
            lines_removed = 0
            
            with open(log_file, 'r', encoding='utf-8', errors='ignore') as infile:
                with open(temp_file, 'w', encoding='utf-8') as outfile:
                    for line in infile:
                        match = cls.LOG_PATTERN.match(line.strip())
                        if match:
                            log_data = match.groupdict()
                            try:
                                log_time = datetime.strptime(
                                    log_data['timestamp'],
                                    '%Y-%m-%d %H:%M:%S,%f'
                                )
                                if log_time >= cutoff_time:
                                    outfile.write(line)
                                    lines_kept += 1
                                else:
                                    lines_removed += 1
                            except:
                                outfile.write(line)
                                lines_kept += 1
                        else:
                            outfile.write(line)
                            lines_kept += 1
            
            # Substituir arquivo original
            os.replace(temp_file, log_file)
            
            current_app.logger.info(
                f"Logs limpos: {lines_kept} mantidas, {lines_removed} removidas"
            )
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Erro ao limpar logs antigos: {e}")
            return False
    
    @classmethod
    def _get_file_size(cls, file_path):
        """Retorna tamanho do arquivo formatado"""
        try:
            size_bytes = os.path.getsize(file_path)
            
            for unit in ['B', 'KB', 'MB', 'GB']:
                if size_bytes < 1024:
                    return f"{size_bytes:.1f} {unit}"
                size_bytes /= 1024
            
            return f"{size_bytes:.1f} TB"
            
        except:
            return "0 B"
    
    @classmethod
    def export_logs(cls, output_file, level=None, start_date=None, end_date=None):
        """
        Exporta logs para um arquivo
        
        Args:
            output_file: Caminho do arquivo de saída
            level: Filtrar por nível
            start_date: Data inicial
            end_date: Data final
            
        Returns:
            bool indicando sucesso
        """
        try:
            result = cls.read_logs(
                level=level,
                limit=999999,  # Sem limite para exportação
                start_date=start_date,
                end_date=end_date
            )
            
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(f"# Log Export - {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
                f.write(f"# Total de entradas: {result['total']}\n")
                f.write("#" + "="*70 + "\n\n")
                
                for log in result['logs']:
                    timestamp = log['timestamp'].strftime('%Y-%m-%d %H:%M:%S')
                    level = log['level']
                    message = log['message']
                    file_info = log.get('file', '')
                    
                    f.write(f"[{timestamp}] {level:8s} {message}")
                    if file_info:
                        f.write(f" [in {file_info}]")
                    f.write("\n")
            
            return True
            
        except Exception as e:
            current_app.logger.error(f"Erro ao exportar logs: {e}")
            return False
