import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from flask_migrate import Migrate
from flask import Flask
from app import db, mail, migrate, bootstrap, mail_init_app

def create_app_without_scheduler():
    """Cria a aplicação Flask sem iniciar o scheduler"""
    app = Flask(__name__)
    app.config.from_object('config.Config')
    db.init_app(app)
    mail_init_app(app, mail)
    migrate.init_app(app, db)
    bootstrap.init_app(app)
    return app

def init_postgres_db():
    """Inicializa o banco de dados PostgreSQL se ele não existir"""
    try:
        # Conectar ao PostgreSQL
        conn = psycopg2.connect(
            host="localhost",
            user="postgres",
            password="postgres",
            port="5432"
        )
        conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
        cursor = conn.cursor()
        
        # Verificar se o banco de dados já existe
        cursor.execute("SELECT 1 FROM pg_database WHERE datname = 'ti_reminder_db'")
        exists = cursor.fetchone()
        
        if not exists:
            print("Criando banco de dados ti_reminder_db...")
            cursor.execute("CREATE DATABASE ti_reminder_db")
            print("Banco de dados criado com sucesso!")
        else:
            print("Banco de dados ti_reminder_db já existe.")
            
        cursor.close()
        conn.close()
        
        return True
    except Exception as e:
        print(f"Erro ao inicializar o banco de dados PostgreSQL: {e}")
        return False

def init_migrations():
    """Inicializa as migrações do Flask-Migrate"""
    try:
        # Criar aplicação sem iniciar o scheduler
        app = create_app_without_scheduler()
        with app.app_context():
            # Verificar se a pasta migrations existe
            if not os.path.exists(os.path.join(os.getcwd(), 'migrations')):
                print("Inicializando migrações...")
                from flask_migrate import init as migrate_init
                migrate_init()
            
            # Criar migração inicial
            print("Criando migração inicial...")
            from flask_migrate import migrate as migrate_func
            migrate_func(message="initial")
            
            # Aplicar migrações
            print("Aplicando migrações...")
            from flask_migrate import upgrade as upgrade_func
            upgrade_func()
            
            print("Migrações aplicadas com sucesso!")
        return True
    except Exception as e:
        print(f"Erro ao inicializar migrações: {e}")
        return False

if __name__ == "__main__":
    print("Inicializando banco de dados PostgreSQL...")
    if init_postgres_db():
        print("Inicializando migrações do Flask...")
        init_migrations()
        print("Configuração do banco de dados concluída com sucesso!")
    else:
        print("Falha na configuração do banco de dados.")