#!/usr/bin/env python
"""
Script de validação da refatoração.
Verifica se todas as mudanças foram aplicadas corretamente.
"""
import sys
import os
from pathlib import Path

# Adicionar raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()


class Colors:
    """Cores ANSI para output."""
    GREEN = '\033[92m'
    RED = '\033[91m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    RESET = '\033[0m'
    BOLD = '\033[1m'


def print_header(text):
    """Imprime cabeçalho."""
    print(f"\n{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{text}{Colors.RESET}")
    print(f"{Colors.BOLD}{Colors.BLUE}{'='*60}{Colors.RESET}\n")


def print_success(text):
    """Imprime sucesso."""
    print(f"{Colors.GREEN}✓{Colors.RESET} {text}")


def print_error(text):
    """Imprime erro."""
    print(f"{Colors.RED}✗{Colors.RESET} {text}")


def print_warning(text):
    """Imprime aviso."""
    print(f"{Colors.YELLOW}⚠{Colors.RESET} {text}")


def print_info(text):
    """Imprime informação."""
    print(f"{Colors.BLUE}ℹ{Colors.RESET} {text}")


def check_file_exists(filepath, should_exist=True):
    """Verifica se arquivo existe."""
    path = Path(filepath)
    exists = path.exists()
    
    if should_exist:
        if exists:
            print_success(f"Arquivo existe: {filepath}")
            return True
        else:
            print_error(f"Arquivo não encontrado: {filepath}")
            return False
    else:
        if not exists:
            print_success(f"Arquivo removido/movido: {filepath}")
            return True
        else:
            print_warning(f"Arquivo ainda existe (deveria estar em legacy/): {filepath}")
            return False


def check_import(module_path, item=None):
    """Verifica se módulo/item pode ser importado."""
    try:
        if item:
            exec(f"from {module_path} import {item}")
            print_success(f"Import OK: from {module_path} import {item}")
        else:
            exec(f"import {module_path}")
            print_success(f"Import OK: import {module_path}")
        return True
    except Exception as e:
        print_error(f"Import falhou: {module_path}.{item if item else ''} - {e}")
        return False


def check_database_connection():
    """Verifica conexão com banco de dados."""
    try:
        from app.utils.db_utils import DatabaseManager
        
        if DatabaseManager.test_connection(verbose=False):
            print_success("Conexão com banco de dados OK")
            return True
        else:
            print_error("Falha na conexão com banco de dados")
            return False
    except Exception as e:
        print_error(f"Erro ao testar conexão: {e}")
        return False


def check_config():
    """Verifica configurações."""
    try:
        from config import Config, DevelopmentConfig, ProductionConfig, TestingConfig, get_config
        
        print_success("Classes de configuração importadas")
        
        # Testar get_config
        config = get_config('development')
        if config == DevelopmentConfig:
            print_success("get_config('development') retorna DevelopmentConfig")
        else:
            print_error("get_config('development') não retorna DevelopmentConfig")
            return False
        
        # Verificar atributos essenciais
        essential_attrs = [
            'SECRET_KEY', 'SQLALCHEMY_DATABASE_URI', 'MAIL_SERVER',
            'TIMEZONE', 'JWT_SECRET_KEY', 'LOG_LEVEL'
        ]
        
        for attr in essential_attrs:
            if hasattr(Config, attr):
                print_success(f"Config.{attr} existe")
            else:
                print_error(f"Config.{attr} não existe")
                return False
        
        return True
    except Exception as e:
        print_error(f"Erro ao verificar configurações: {e}")
        return False


def check_db_utils():
    """Verifica utilitários de banco."""
    try:
        from app.utils.db_utils import DatabaseManager, MigrationHelper
        
        print_success("DatabaseManager importado")
        print_success("MigrationHelper importado")
        
        # Verificar métodos essenciais
        essential_methods = [
            'get_database_url',
            'parse_database_url',
            'get_raw_connection',
            'database_exists',
            'create_database',
            'column_exists',
            'table_exists',
            'get_table_columns',
            'test_connection'
        ]
        
        for method in essential_methods:
            if hasattr(DatabaseManager, method):
                print_success(f"DatabaseManager.{method} existe")
            else:
                print_error(f"DatabaseManager.{method} não existe")
                return False
        
        return True
    except Exception as e:
        print_error(f"Erro ao verificar db_utils: {e}")
        return False


def check_environment():
    """Verifica variáveis de ambiente."""
    required_vars = ['DATABASE_URL']
    optional_vars = ['SECRET_KEY', 'MAIL_USERNAME', 'MAIL_PASSWORD']
    
    all_ok = True
    
    for var in required_vars:
        if os.environ.get(var):
            print_success(f"Variável de ambiente OK: {var}")
        else:
            print_error(f"Variável de ambiente não configurada: {var}")
            all_ok = False
    
    for var in optional_vars:
        if os.environ.get(var):
            print_success(f"Variável de ambiente OK: {var}")
        else:
            print_warning(f"Variável de ambiente não configurada (opcional): {var}")
    
    return all_ok


def main():
    """Executa todas as validações."""
    print_header("VALIDAÇÃO DA REFATORAÇÃO - TI REMINDER APP")
    
    results = {}
    
    # 1. Verificar novos arquivos
    print_header("1. Verificando Novos Arquivos")
    results['new_files'] = all([
        check_file_exists('app/utils/db_utils.py'),
        check_file_exists('scripts/db_manager.py'),
        check_file_exists('scripts/cleanup_legacy.py'),
        check_file_exists('scripts/validate_refactoring.py'),
        check_file_exists('REFACTORING_GUIDE.md'),
    ])
    
    # 2. Verificar arquivos modificados
    print_header("2. Verificando Arquivos Modificados")
    results['modified_files'] = all([
        check_file_exists('config.py'),
        check_file_exists('init_db.py'),
    ])
    
    # 3. Verificar arquivos legados (opcional - podem estar movidos)
    print_header("3. Verificando Arquivos Legados")
    legacy_files = [
        'apply_migration.py',
        'check_migration.py',
        'add_satisfaction_fields.py',
        'test_db_connection.py',
        'test_notification.py',
        'config_production.py',
        'system_config_model.py',
    ]
    
    legacy_moved = 0
    for f in legacy_files:
        if not Path(f).exists():
            legacy_moved += 1
    
    if legacy_moved > 0:
        print_info(f"{legacy_moved}/{len(legacy_files)} arquivos legados foram movidos")
    else:
        print_warning("Arquivos legados ainda na raiz (execute cleanup_legacy.py)")
    
    results['legacy_cleanup'] = legacy_moved > 0
    
    # 4. Verificar imports
    print_header("4. Verificando Imports")
    results['imports'] = all([
        check_import('app.utils.db_utils', 'DatabaseManager'),
        check_import('app.utils.db_utils', 'MigrationHelper'),
        check_import('config', 'Config'),
        check_import('config', 'DevelopmentConfig'),
        check_import('config', 'ProductionConfig'),
        check_import('config', 'get_config'),
    ])
    
    # 5. Verificar configurações
    print_header("5. Verificando Configurações")
    results['config'] = check_config()
    
    # 6. Verificar db_utils
    print_header("6. Verificando Utilitários de Banco")
    results['db_utils'] = check_db_utils()
    
    # 7. Verificar variáveis de ambiente
    print_header("7. Verificando Variáveis de Ambiente")
    results['environment'] = check_environment()
    
    # 8. Verificar conexão com banco (opcional)
    print_header("8. Verificando Conexão com Banco de Dados")
    try:
        results['database'] = check_database_connection()
    except Exception as e:
        print_warning(f"Não foi possível testar conexão: {e}")
        results['database'] = None
    
    # Resumo
    print_header("RESUMO DA VALIDAÇÃO")
    
    total_checks = len(results)
    passed = sum(1 for v in results.values() if v is True)
    failed = sum(1 for v in results.values() if v is False)
    skipped = sum(1 for v in results.values() if v is None)
    
    print(f"\nTotal de verificações: {total_checks}")
    print_success(f"Passou: {passed}")
    if failed > 0:
        print_error(f"Falhou: {failed}")
    if skipped > 0:
        print_warning(f"Pulado: {skipped}")
    
    print("\nDetalhes:")
    for check, result in results.items():
        status = "✓" if result is True else ("✗" if result is False else "⚠")
        color = Colors.GREEN if result is True else (Colors.RED if result is False else Colors.YELLOW)
        print(f"  {color}{status}{Colors.RESET} {check}")
    
    # Resultado final
    print(f"\n{Colors.BOLD}{'='*60}{Colors.RESET}")
    if failed == 0:
        print(f"{Colors.GREEN}{Colors.BOLD}✓ VALIDAÇÃO CONCLUÍDA COM SUCESSO!{Colors.RESET}")
        print(f"\n{Colors.GREEN}A refatoração foi aplicada corretamente.{Colors.RESET}")
        return 0
    else:
        print(f"{Colors.RED}{Colors.BOLD}✗ VALIDAÇÃO FALHOU{Colors.RESET}")
        print(f"\n{Colors.RED}Corrija os erros acima antes de continuar.{Colors.RESET}")
        return 1


if __name__ == '__main__':
    sys.exit(main())
