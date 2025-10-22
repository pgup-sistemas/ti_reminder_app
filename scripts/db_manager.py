#!/usr/bin/env python
"""
Script CLI unificado para gerenciamento de banco de dados.
Substitui: init_db.py, apply_migration.py, check_migration.py, test_db_connection.py

Uso:
    python scripts/db_manager.py init          # Inicializa banco e migrations
    python scripts/db_manager.py test          # Testa conexão
    python scripts/db_manager.py migrate       # Aplica migrations pendentes
    python scripts/db_manager.py status        # Status das migrations
"""
import sys
import os
from pathlib import Path

# Adicionar diretório raiz ao path
sys.path.insert(0, str(Path(__file__).parent.parent))

from dotenv import load_dotenv
load_dotenv()

import click
from flask_migrate import upgrade, current, stamp
from app import create_app
from app.utils.db_utils import DatabaseManager, MigrationHelper


@click.group()
def cli():
    """Gerenciador de banco de dados TI Reminder."""
    pass


@cli.command()
@click.option('--verbose', '-v', is_flag=True, help='Modo verboso')
def test(verbose):
    """Testa a conexão com o banco de dados."""
    click.echo("🔍 Testando conexão com banco de dados...")
    
    try:
        if DatabaseManager.test_connection(verbose=verbose):
            click.echo("✓ Teste concluído com sucesso!")
            sys.exit(0)
        else:
            click.echo("✗ Falha no teste de conexão")
            sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Erro: {e}")
        sys.exit(1)


@cli.command()
@click.option('--force', '-f', is_flag=True, help='Força recriação do banco')
def init(force):
    """Inicializa o banco de dados e migrations."""
    click.echo("🚀 Inicializando banco de dados...")
    
    try:
        # 1. Criar banco se não existir
        params = DatabaseManager.parse_database_url()
        dbname = params['dbname']
        
        if force:
            click.echo(f"⚠️  Modo force ativado - recriando banco '{dbname}'")
            # Implementar drop database se necessário
        
        if not DatabaseManager.create_database(dbname):
            click.echo("✗ Falha ao criar banco de dados")
            sys.exit(1)
        
        # 2. Criar app e aplicar migrations
        click.echo("📦 Criando aplicação Flask...")
        app = create_app()
        
        with app.app_context():
            click.echo("🔄 Aplicando migrations...")
            
            # Verificar se migrations existem
            migrations_dir = Path('migrations/versions')
            if not migrations_dir.exists() or not list(migrations_dir.glob('*.py')):
                click.echo("⚠️  Nenhuma migration encontrada")
                click.echo("   Execute: flask db init && flask db migrate -m 'initial'")
            else:
                upgrade()
                click.echo("✓ Migrations aplicadas com sucesso!")
            
            # 3. Inicializar dados padrão
            click.echo("📝 Inicializando configurações padrão...")
            from app.models import SlaConfig
            SlaConfig.criar_configuracoes_padrao()
            
            # Criar flag de inicialização
            flag_file = Path('db_initialized.flag')
            flag_file.write_text('1')
            
            click.echo("✓ Banco de dados inicializado com sucesso!")
            
    except Exception as e:
        click.echo(f"✗ Erro durante inicialização: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
def migrate():
    """Aplica migrations pendentes."""
    click.echo("🔄 Aplicando migrations...")
    
    try:
        app = create_app()
        
        with app.app_context():
            # Verificar revisão atual
            try:
                current_rev = current()
                click.echo(f"Revisão atual: {current_rev}")
            except Exception:
                click.echo("⚠️  Nenhuma revisão aplicada ainda")
            
            # Aplicar migrations
            upgrade()
            click.echo("✓ Migrations aplicadas com sucesso!")
            
    except Exception as e:
        click.echo(f"✗ Erro ao aplicar migrations: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


@cli.command()
def status():
    """Mostra status das migrations."""
    click.echo("📊 Status das migrations...")
    
    try:
        app = create_app()
        
        with app.app_context():
            # Revisão atual
            try:
                current_rev = current()
                click.echo(f"Revisão atual: {current_rev}")
            except Exception as e:
                click.echo(f"⚠️  Erro ao obter revisão: {e}")
            
            # Listar migrations disponíveis
            migrations_dir = Path('migrations/versions')
            if migrations_dir.exists():
                migrations = list(migrations_dir.glob('*.py'))
                click.echo(f"\nMigrations disponíveis: {len(migrations)}")
                for migration in sorted(migrations):
                    click.echo(f"  - {migration.stem}")
            else:
                click.echo("⚠️  Diretório de migrations não encontrado")
            
            # Informações do banco
            click.echo("\n📊 Informações do banco:")
            params = DatabaseManager.parse_database_url()
            click.echo(f"  Host: {params['host']}:{params['port']}")
            click.echo(f"  Database: {params['dbname']}")
            click.echo(f"  User: {params['user']}")
            
            # Contar tabelas
            with DatabaseManager.get_raw_connection() as (conn, cursor):
                cursor.execute("""
                    SELECT COUNT(*) 
                    FROM information_schema.tables 
                    WHERE table_schema = 'public'
                """)
                table_count = cursor.fetchone()[0]
                click.echo(f"  Tabelas: {table_count}")
            
    except Exception as e:
        click.echo(f"✗ Erro: {e}")
        sys.exit(1)


@cli.command()
@click.argument('table_name')
def inspect(table_name):
    """Inspeciona uma tabela específica."""
    click.echo(f"🔍 Inspecionando tabela '{table_name}'...")
    
    try:
        if not DatabaseManager.table_exists(table_name):
            click.echo(f"✗ Tabela '{table_name}' não existe")
            sys.exit(1)
        
        columns = DatabaseManager.get_table_columns(table_name)
        click.echo(f"\nColunas ({len(columns)}):")
        for col in columns:
            click.echo(f"  - {col}")
        
        # Contar registros
        with DatabaseManager.get_raw_connection() as (conn, cursor):
            cursor.execute(f'SELECT COUNT(*) FROM "{table_name}"')
            count = cursor.fetchone()[0]
            click.echo(f"\nRegistros: {count}")
            
    except Exception as e:
        click.echo(f"✗ Erro: {e}")
        sys.exit(1)


@cli.command()
@click.option('--backup-dir', default='backups', help='Diretório para backup')
def backup(backup_dir):
    """Cria backup do banco de dados."""
    click.echo("💾 Criando backup...")
    
    try:
        import subprocess
        from datetime import datetime
        
        params = DatabaseManager.parse_database_url()
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        backup_file = Path(backup_dir) / f"backup_{params['dbname']}_{timestamp}.sql"
        
        # Criar diretório se não existir
        backup_file.parent.mkdir(exist_ok=True)
        
        # Executar pg_dump
        env = os.environ.copy()
        env['PGPASSWORD'] = params['password']
        
        cmd = [
            'pg_dump',
            '-h', params['host'],
            '-p', str(params['port']),
            '-U', params['user'],
            '-d', params['dbname'],
            '-f', str(backup_file)
        ]
        
        subprocess.run(cmd, env=env, check=True)
        
        click.echo(f"✓ Backup criado: {backup_file}")
        click.echo(f"  Tamanho: {backup_file.stat().st_size / 1024:.2f} KB")
        
    except subprocess.CalledProcessError as e:
        click.echo(f"✗ Erro ao criar backup: {e}")
        sys.exit(1)
    except Exception as e:
        click.echo(f"✗ Erro: {e}")
        sys.exit(1)


if __name__ == '__main__':
    cli()
