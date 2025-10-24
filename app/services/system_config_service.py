"""
Serviço para gerenciamento de configurações do sistema
Fornece interface unificada para acesso e atualização de configurações persistentes
"""

from flask import current_app
from sqlalchemy.exc import IntegrityError
from ..models import SystemConfig, db
from ..utils.timezone_utils import get_current_time_for_db


class SystemConfigService:
    """Serviço centralizado para gerenciamento de configurações do sistema"""
    
    # Cache em memória das configurações
    _cache = {}
    _cache_loaded = False
    
    @classmethod
    def get(cls, category, key, default=None):
        """
        Busca uma configuração do banco de dados
        
        Args:
            category: Categoria da configuração (system, security, backup, etc)
            key: Chave da configuração
            default: Valor padrão se não encontrado
            
        Returns:
            Valor da configuração (convertido para o tipo correto) ou default
        """
        # Garantir que o cache está carregado
        if not cls._cache_loaded:
            cls.reload_cache()
        
        cache_key = f"{category}.{key}"
        
        # Tentar pegar do cache primeiro
        if cache_key in cls._cache:
            return cls._cache[cache_key]
        
        # Se não está no cache, buscar do banco
        config = SystemConfig.query.filter_by(category=category, key=key).first()
        
        if config:
            value = config.get_typed_value()
            cls._cache[cache_key] = value
            return value
        
        # Se não encontrou, retornar padrão e adicionar ao cache
        cls._cache[cache_key] = default
        return default
    
    @classmethod
    def set(cls, category, key, value, value_type='string', description=None, user_id=None):
        """
        Define uma configuração no banco de dados
        
        Args:
            category: Categoria da configuração
            key: Chave da configuração
            value: Valor a ser salvo
            value_type: Tipo do valor (string, int, bool, json, float)
            description: Descrição da configuração
            user_id: ID do usuário que fez a alteração
            
        Returns:
            True se salvou com sucesso, False caso contrário
        """
        try:
            # Buscar configuração existente
            config = SystemConfig.query.filter_by(category=category, key=key).first()
            
            if config:
                # Atualizar existente
                old_value = config.get_typed_value()
                config.set_typed_value(value)
                config.value_type = value_type
                config.updated_at = get_current_time_for_db()
                if user_id:
                    config.updated_by_id = user_id
                if description:
                    config.description = description
            else:
                # Criar nova
                config = SystemConfig(
                    category=category,
                    key=key,
                    value_type=value_type,
                    description=description,
                    updated_by_id=user_id
                )
                config.set_typed_value(value)
                db.session.add(config)
                old_value = None
            
            db.session.commit()
            
            # Atualizar cache
            cache_key = f"{category}.{key}"
            cls._cache[cache_key] = config.get_typed_value()
            
            # Atualizar config do Flask também
            flask_key = f"{category.upper()}_{key.upper()}"
            current_app.config[flask_key] = config.get_typed_value()
            
            # Log da mudança
            current_app.logger.info(
                f"Configuração atualizada: {category}.{key}",
                extra={
                    "category": category,
                    "key": key,
                    "old_value": old_value,
                    "new_value": value,
                    "user_id": user_id
                }
            )
            
            return True
            
        except IntegrityError as e:
            db.session.rollback()
            current_app.logger.error(f"Erro de integridade ao salvar configuração: {e}")
            return False
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao salvar configuração: {e}")
            return False
    
    @classmethod
    def get_category(cls, category):
        """
        Retorna todas as configurações de uma categoria
        
        Args:
            category: Categoria das configurações
            
        Returns:
            Dict com as configurações {key: value}
        """
        configs = SystemConfig.query.filter_by(category=category).all()
        return {config.key: config.get_typed_value() for config in configs}
    
    @classmethod
    def get_all(cls):
        """
        Retorna todas as configurações do sistema
        
        Returns:
            Dict com todas as configurações {category.key: value}
        """
        configs = SystemConfig.query.all()
        return {
            f"{config.category}.{config.key}": config.get_typed_value()
            for config in configs
        }
    
    @classmethod
    def delete(cls, category, key):
        """
        Remove uma configuração do banco de dados
        
        Args:
            category: Categoria da configuração
            key: Chave da configuração
            
        Returns:
            True se removeu com sucesso, False caso contrário
        """
        try:
            config = SystemConfig.query.filter_by(category=category, key=key).first()
            if config:
                db.session.delete(config)
                db.session.commit()
                
                # Remover do cache
                cache_key = f"{category}.{key}"
                if cache_key in cls._cache:
                    del cls._cache[cache_key]
                
                current_app.logger.info(f"Configuração removida: {category}.{key}")
                return True
            return False
        except Exception as e:
            db.session.rollback()
            current_app.logger.error(f"Erro ao remover configuração: {e}")
            return False
    
    @classmethod
    def reload_cache(cls):
        """
        Recarrega todas as configurações do banco para o cache
        """
        try:
            cls._cache.clear()
            configs = SystemConfig.query.all()
            
            for config in configs:
                cache_key = f"{config.category}.{config.key}"
                cls._cache[cache_key] = config.get_typed_value()
                
                # Atualizar config do Flask também
                flask_key = f"{config.category.upper()}_{config.key.upper()}"
                current_app.config[flask_key] = config.get_typed_value()
            
            cls._cache_loaded = True
            current_app.logger.info(f"Cache de configurações recarregado: {len(configs)} configurações")
            
        except Exception as e:
            current_app.logger.error(f"Erro ao recarregar cache de configurações: {e}")
    
    @classmethod
    def seed_default_configs(cls):
        """
        Popula o banco com configurações padrão
        """
        default_configs = [
            # Sistema Geral
            ('system', 'name', 'TI OSN System', 'string', 'Nome do sistema'),
            ('system', 'version', '2.0', 'string', 'Versão do sistema'),
            ('system', 'maintenance_mode', False, 'bool', 'Modo de manutenção'),
            ('system', 'timezone', 'America/Manaus', 'string', 'Timezone do sistema'),
            ('system', 'language', 'pt-BR', 'string', 'Idioma do sistema'),
            
            # Segurança
            ('security', 'password_min_length', 6, 'int', 'Comprimento mínimo da senha'),
            ('security', 'password_require_uppercase', True, 'bool', 'Senha requer maiúsculas'),
            ('security', 'password_require_lowercase', True, 'bool', 'Senha requer minúsculas'),
            ('security', 'password_require_numbers', True, 'bool', 'Senha requer números'),
            ('security', 'password_require_special', False, 'bool', 'Senha requer caracteres especiais'),
            ('security', 'session_timeout', 30, 'int', 'Timeout de sessão (minutos)'),
            ('security', 'max_login_attempts', 5, 'int', 'Máximo de tentativas de login'),
            ('security', 'lockout_duration', 15, 'int', 'Duração do bloqueio (minutos)'),
            ('security', 'two_factor_required', False, 'bool', 'Exigir autenticação de dois fatores'),
            ('security', 'ip_whitelist_enabled', False, 'bool', 'Habilitar whitelist de IPs'),
            ('security', 'audit_log_enabled', True, 'bool', 'Habilitar logs de auditoria'),
            
            # Backup
            ('backup', 'enabled', True, 'bool', 'Backup habilitado'),
            ('backup', 'frequency', 'daily', 'string', 'Frequência do backup'),
            ('backup', 'time', '02:00', 'string', 'Horário do backup'),
            ('backup', 'retention_days', 30, 'int', 'Dias de retenção'),
            ('backup', 'location', 'local', 'string', 'Localização do backup'),
            ('backup', 'compression_enabled', True, 'bool', 'Compressão habilitada'),
            ('backup', 'encryption_enabled', False, 'bool', 'Criptografia habilitada'),
            ('backup', 'email_notifications', True, 'bool', 'Notificações por email'),
            
            # Performance
            ('performance', 'cache_timeout', 3600, 'int', 'Timeout do cache (segundos)'),
            ('performance', 'max_connections', 100, 'int', 'Máximo de conexões'),
            ('performance', 'query_timeout', 30, 'int', 'Timeout de queries (segundos)'),
            ('performance', 'memory_limit', 512, 'int', 'Limite de memória (MB)'),
            ('performance', 'enable_caching', True, 'bool', 'Habilitar cache'),
            ('performance', 'enable_compression', True, 'bool', 'Habilitar compressão'),
            ('performance', 'enable_monitoring', True, 'bool', 'Habilitar monitoramento'),
            
            # Alertas
            ('alerts', 'email', 'admin@example.com', 'string', 'Email para alertas'),
            ('alerts', 'frequency', 'hourly', 'string', 'Frequência de alertas'),
            ('alerts', 'system_errors', True, 'bool', 'Alertas de erros de sistema'),
            ('alerts', 'performance', True, 'bool', 'Alertas de performance'),
            ('alerts', 'disk_space', True, 'bool', 'Alertas de espaço em disco'),
            ('alerts', 'security', True, 'bool', 'Alertas de segurança'),
            ('alerts', 'database', True, 'bool', 'Alertas de banco de dados'),
            ('alerts', 'backup', True, 'bool', 'Alertas de backup'),
            ('alerts', 'network', False, 'bool', 'Alertas de rede'),
            ('alerts', 'custom', False, 'bool', 'Alertas personalizados'),
            
            # RFID
            ('rfid', 'scan_interval', 5, 'int', 'Intervalo de scan (segundos)'),
            ('rfid', 'lost_threshold_hours', 24, 'int', 'Horas para considerar perdido'),
            ('rfid', 'auto_alert_lost', True, 'bool', 'Alertar automaticamente equipamentos perdidos'),
            ('rfid', 'track_movement', True, 'bool', 'Rastrear movimentação'),
        ]
        
        count = 0
        for category, key, value, value_type, description in default_configs:
            # Verificar se já existe
            existing = SystemConfig.query.filter_by(category=category, key=key).first()
            if not existing:
                config = SystemConfig(
                    category=category,
                    key=key,
                    value_type=value_type,
                    description=description
                )
                config.set_typed_value(value)
                db.session.add(config)
                count += 1
        
        if count > 0:
            try:
                db.session.commit()
                current_app.logger.info(f"Seed de configurações criado: {count} configurações adicionadas")
            except Exception as e:
                db.session.rollback()
                current_app.logger.error(f"Erro ao criar seed de configurações: {e}")
        else:
            current_app.logger.info("Seed de configurações já existe")
        
        # Recarregar cache após seed
        cls.reload_cache()
