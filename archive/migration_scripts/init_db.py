#!/usr/bin/env python
"""
Script de inicialização do banco de dados.
NOTA: Este script está sendo substituído por scripts/db_manager.py
Mantido por compatibilidade, mas use: python scripts/db_manager.py init
"""
import os
import sys
import subprocess
from pathlib import Path
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

# Importar utilitários
from app.utils.db_utils import DatabaseManager

def init_postgres_db():
    """
    Inicializa o banco de dados PostgreSQL.
    Cria o banco de dados se não existir.
    
    Returns:
        bool: True se a inicialização foi bem-sucedida, False caso contrário.
    """
    try:
        params = DatabaseManager.parse_database_url()
        dbname = params['dbname']
        
        print(f"Inicializando banco de dados '{dbname}'...")
        return DatabaseManager.create_database(dbname)
        
    except ValueError as e:
        print(f"Erro de configuração: {e}")
        return False
    except Exception as e:
        print(f"Erro ao inicializar banco de dados PostgreSQL: {str(e)}")
        return False

def init_migrations():
    """
    Inicializa as migrações do Flask-Migrate.
    
    Returns:
        bool: True se a inicialização foi bem-sucedida, False caso contrário.
    """
    try:
        from app import create_app
        from flask_migrate import upgrade
        
        app = create_app()
        
        with app.app_context():
            migrations_dir = Path('migrations/versions')
            
            # Verificar se migrations existem
            if not migrations_dir.exists():
                print("Inicializando estrutura de migrações...")
                subprocess.run(['flask', 'db', 'init'], check=True)
                
                # Criar migração inicial
                if not list(migrations_dir.glob('*.py')):
                    print("Criando migração inicial...")
                    subprocess.run(['flask', 'db', 'migrate', '-m', 'initial'], check=True)
            
            # Aplicar migrações
            print("Aplicando migrações...")
            upgrade()
            
            # Inicializar configurações padrão de SLA
            from app.models import SlaConfig
            SlaConfig.criar_configuracoes_padrao()
            print("Configurações padrão de SLA inicializadas!")
        
        return True
    except subprocess.CalledProcessError as e:
        print(f"Erro ao executar comando flask: {e}")
        return False
    except Exception as e:
        print(f"Erro ao inicializar migrações: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Se executado diretamente, inicializar o banco de dados e as migrações
    if init_postgres_db():
        print("Banco de dados PostgreSQL inicializado com sucesso!")
        if init_migrations():
            print("Migrações inicializadas com sucesso!")
            # Criar arquivo de flag
            with open('db_initialized.flag', 'w') as f:
                f.write('1')
        else:
            print("Falha ao inicializar migrações.")
    else:
        print("Falha ao inicializar banco de dados PostgreSQL.")