"""
Serviço de Backup e Restauração
Gerencia backups de banco de dados e arquivos do sistema
"""

import os
import subprocess
import shutil
import gzip
import hashlib
import json
from datetime import datetime, timedelta
from pathlib import Path
from flask import current_app


class BackupService:
    """Serviço para backup e restauração do sistema"""
    
    @staticmethod
    def get_backup_dir():
        """Retorna diretório de backups"""
        from ..services.system_config_service import SystemConfigService
        
        location = SystemConfigService.get('backup', 'location', 'local')
        
        if location == 'local':
            backup_dir = os.path.join(current_app.root_path, '..', 'backups')
        elif location == 'network':
            # Configurar caminho de rede
            backup_dir = SystemConfigService.get('backup', 'network_path', 'backups')
        else:  # cloud
            backup_dir = os.path.join(current_app.root_path, '..', 'backups_temp')
        
        # Criar diretório se não existir
        Path(backup_dir).mkdir(parents=True, exist_ok=True)
        
        return backup_dir
    
    @staticmethod
    def create_database_backup():
        """
        Cria backup do banco de dados PostgreSQL
        
        Returns:
            dict: Informações do backup ou None em caso de erro
        """
        from ..services.system_config_service import SystemConfigService
        
        try:
            # Obter configurações
            compression_enabled = SystemConfigService.get('backup', 'compression_enabled', True)
            encryption_enabled = SystemConfigService.get('backup', 'encryption_enabled', False)
            
            # Diretório de backup
            backup_dir = BackupService.get_backup_dir()
            db_backup_dir = os.path.join(backup_dir, 'database')
            Path(db_backup_dir).mkdir(parents=True, exist_ok=True)
            
            # Nome do arquivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"db_backup_{timestamp}.sql"
            filepath = os.path.join(db_backup_dir, filename)
            
            # Obter configurações do banco
            database_url = current_app.config.get('SQLALCHEMY_DATABASE_URI')
            
            # Parsear URL do banco
            # Format: postgresql://user:password@host:port/database
            import re
            match = re.match(r'postgresql://([^:]+):([^@]+)@([^:]+):(\d+)/(.+)', database_url)
            
            if not match:
                current_app.logger.error("Formato de DATABASE_URI inválido")
                return None
            
            user, password, host, port, database = match.groups()
            
            # Executar pg_dump
            env = os.environ.copy()
            env['PGPASSWORD'] = password
            
            cmd = [
                'pg_dump',
                '-h', host,
                '-p', port,
                '-U', user,
                '-d', database,
                '-F', 'p',  # Plain text format
                '-f', filepath
            ]
            
            result = subprocess.run(
                cmd,
                env=env,
                capture_output=True,
                text=True,
                timeout=300  # 5 minutos
            )
            
            if result.returncode != 0:
                current_app.logger.error(f"Erro ao executar pg_dump: {result.stderr}")
                return None
            
            # Comprimir se habilitado
            if compression_enabled:
                compressed_filepath = filepath + '.gz'
                with open(filepath, 'rb') as f_in:
                    with gzip.open(compressed_filepath, 'wb') as f_out:
                        shutil.copyfileobj(f_in, f_out)
                os.remove(filepath)
                filepath = compressed_filepath
                filename = filename + '.gz'
            
            # Calcular hash do arquivo
            file_hash = BackupService._calculate_file_hash(filepath)
            file_size = os.path.getsize(filepath)
            
            backup_info = {
                'type': 'database',
                'filename': filename,
                'filepath': filepath,
                'size': file_size,
                'size_human': BackupService._format_size(file_size),
                'hash': file_hash,
                'compressed': compression_enabled,
                'encrypted': encryption_enabled,
                'timestamp': timestamp,
                'created_at': datetime.now().isoformat()
            }
            
            # Salvar metadata
            BackupService._save_backup_metadata(backup_info)
            
            current_app.logger.info(f"Backup de banco de dados criado: {filename}")
            
            return backup_info
            
        except subprocess.TimeoutExpired:
            current_app.logger.error("Timeout ao criar backup do banco de dados")
            return None
        except Exception as e:
            current_app.logger.exception(f"Erro ao criar backup do banco de dados: {e}")
            return None
    
    @staticmethod
    def create_files_backup():
        """
        Cria backup de arquivos importantes do sistema
        
        Returns:
            dict: Informações do backup ou None em caso de erro
        """
        from ..services.system_config_service import SystemConfigService
        
        try:
            # Obter configurações
            compression_enabled = SystemConfigService.get('backup', 'compression_enabled', True)
            
            # Diretório de backup
            backup_dir = BackupService.get_backup_dir()
            files_backup_dir = os.path.join(backup_dir, 'files')
            Path(files_backup_dir).mkdir(parents=True, exist_ok=True)
            
            # Nome do arquivo
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            filename = f"files_backup_{timestamp}.tar"
            if compression_enabled:
                filename += '.gz'
            filepath = os.path.join(files_backup_dir, filename)
            
            # Diretórios para backup
            app_root = Path(current_app.root_path)
            
            dirs_to_backup = [
                app_root / 'static' / 'uploads',  # Arquivos enviados
                app_root / 'static' / 'profile_pics',  # Fotos de perfil
                app_root / '..' / 'logs',  # Logs
            ]
            
            # Criar arquivo tar
            import tarfile
            mode = 'w:gz' if compression_enabled else 'w'
            
            with tarfile.open(filepath, mode) as tar:
                for dir_path in dirs_to_backup:
                    if dir_path.exists():
                        tar.add(str(dir_path), arcname=dir_path.name)
            
            # Calcular hash e tamanho
            file_hash = BackupService._calculate_file_hash(filepath)
            file_size = os.path.getsize(filepath)
            
            backup_info = {
                'type': 'files',
                'filename': filename,
                'filepath': filepath,
                'size': file_size,
                'size_human': BackupService._format_size(file_size),
                'hash': file_hash,
                'compressed': compression_enabled,
                'timestamp': timestamp,
                'created_at': datetime.now().isoformat(),
                'directories': [str(d) for d in dirs_to_backup if d.exists()]
            }
            
            # Salvar metadata
            BackupService._save_backup_metadata(backup_info)
            
            current_app.logger.info(f"Backup de arquivos criado: {filename}")
            
            return backup_info
            
        except Exception as e:
            current_app.logger.exception(f"Erro ao criar backup de arquivos: {e}")
            return None
    
    @staticmethod
    def create_full_backup():
        """
        Cria backup completo (banco + arquivos)
        
        Returns:
            dict: Informações dos backups criados
        """
        results = {
            'database': None,
            'files': None,
            'success': False,
            'errors': []
        }
        
        # Backup do banco
        db_backup = BackupService.create_database_backup()
        if db_backup:
            results['database'] = db_backup
        else:
            results['errors'].append('Falha ao criar backup do banco de dados')
        
        # Backup de arquivos
        files_backup = BackupService.create_files_backup()
        if files_backup:
            results['files'] = files_backup
        else:
            results['errors'].append('Falha ao criar backup de arquivos')
        
        results['success'] = db_backup is not None and files_backup is not None
        
        return results
    
    @staticmethod
    def list_backups(backup_type=None):
        """
        Lista backups disponíveis
        
        Args:
            backup_type: Tipo de backup (database, files) ou None para todos
            
        Returns:
            list: Lista de backups
        """
        try:
            backup_dir = BackupService.get_backup_dir()
            metadata_file = os.path.join(backup_dir, 'backups_metadata.json')
            
            if not os.path.exists(metadata_file):
                return []
            
            with open(metadata_file, 'r') as f:
                all_backups = json.load(f)
            
            if backup_type:
                return [b for b in all_backups if b.get('type') == backup_type]
            
            return all_backups
            
        except Exception as e:
            current_app.logger.exception(f"Erro ao listar backups: {e}")
            return []
    
    @staticmethod
    def delete_backup(filename):
        """
        Deleta um backup
        
        Args:
            filename: Nome do arquivo de backup
            
        Returns:
            bool: True se deletado com sucesso
        """
        try:
            backup_dir = BackupService.get_backup_dir()
            
            # Procurar arquivo em database ou files
            for subdir in ['database', 'files']:
                filepath = os.path.join(backup_dir, subdir, filename)
                if os.path.exists(filepath):
                    os.remove(filepath)
                    
                    # Remover do metadata
                    BackupService._remove_from_metadata(filename)
                    
                    current_app.logger.info(f"Backup deletado: {filename}")
                    return True
            
            return False
            
        except Exception as e:
            current_app.logger.exception(f"Erro ao deletar backup: {e}")
            return False
    
    @staticmethod
    def cleanup_old_backups():
        """
        Remove backups antigos conforme configuração de retenção
        
        Returns:
            int: Número de backups removidos
        """
        from ..services.system_config_service import SystemConfigService
        
        try:
            retention_days = SystemConfigService.get('backup', 'retention_days', 30)
            cutoff_date = datetime.now() - timedelta(days=retention_days)
            
            backups = BackupService.list_backups()
            removed_count = 0
            
            for backup in backups:
                created_at = datetime.fromisoformat(backup['created_at'])
                if created_at < cutoff_date:
                    if BackupService.delete_backup(backup['filename']):
                        removed_count += 1
            
            if removed_count > 0:
                current_app.logger.info(f"{removed_count} backups antigos removidos")
            
            return removed_count
            
        except Exception as e:
            current_app.logger.exception(f"Erro ao limpar backups antigos: {e}")
            return 0
    
    @staticmethod
    def verify_backup_integrity(filename):
        """
        Verifica integridade de um backup
        
        Args:
            filename: Nome do arquivo de backup
            
        Returns:
            bool: True se íntegro
        """
        try:
            backup_dir = BackupService.get_backup_dir()
            
            # Procurar arquivo
            filepath = None
            for subdir in ['database', 'files']:
                test_path = os.path.join(backup_dir, subdir, filename)
                if os.path.exists(test_path):
                    filepath = test_path
                    break
            
            if not filepath:
                return False
            
            # Buscar hash original do metadata
            backups = BackupService.list_backups()
            original_hash = None
            for backup in backups:
                if backup['filename'] == filename:
                    original_hash = backup.get('hash')
                    break
            
            if not original_hash:
                current_app.logger.warning(f"Hash original não encontrado para {filename}")
                return False
            
            # Calcular hash atual
            current_hash = BackupService._calculate_file_hash(filepath)
            
            is_valid = current_hash == original_hash
            
            if not is_valid:
                current_app.logger.error(f"Backup corrompido: {filename}")
            
            return is_valid
            
        except Exception as e:
            current_app.logger.exception(f"Erro ao verificar integridade: {e}")
            return False
    
    @staticmethod
    def _calculate_file_hash(filepath):
        """Calcula hash SHA256 de um arquivo"""
        sha256_hash = hashlib.sha256()
        with open(filepath, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    @staticmethod
    def _format_size(size_bytes):
        """Formata tamanho em bytes para formato legível"""
        for unit in ['B', 'KB', 'MB', 'GB', 'TB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.2f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.2f} PB"
    
    @staticmethod
    def _save_backup_metadata(backup_info):
        """Salva metadata de backup"""
        try:
            backup_dir = BackupService.get_backup_dir()
            metadata_file = os.path.join(backup_dir, 'backups_metadata.json')
            
            # Carregar metadata existente
            if os.path.exists(metadata_file):
                with open(metadata_file, 'r') as f:
                    all_backups = json.load(f)
            else:
                all_backups = []
            
            # Adicionar novo backup
            all_backups.append(backup_info)
            
            # Salvar
            with open(metadata_file, 'w') as f:
                json.dump(all_backups, f, indent=2)
                
        except Exception as e:
            current_app.logger.exception(f"Erro ao salvar metadata: {e}")
    
    @staticmethod
    def _remove_from_metadata(filename):
        """Remove backup do metadata"""
        try:
            backup_dir = BackupService.get_backup_dir()
            metadata_file = os.path.join(backup_dir, 'backups_metadata.json')
            
            if not os.path.exists(metadata_file):
                return
            
            with open(metadata_file, 'r') as f:
                all_backups = json.load(f)
            
            # Filtrar backup removido
            all_backups = [b for b in all_backups if b['filename'] != filename]
            
            # Salvar
            with open(metadata_file, 'w') as f:
                json.dump(all_backups, f, indent=2)
                
        except Exception as e:
            current_app.logger.exception(f"Erro ao remover do metadata: {e}")
