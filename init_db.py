import os
import sys
import psycopg2
from urllib.parse import urlparse
from flask import Flask
from flask_migrate import Migrate
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def init_postgres_db():
    """
    Inicializa o banco de dados PostgreSQL.
    Cria o banco de dados se não existir.
    
    Returns:
        bool: True se a inicialização foi bem-sucedida, False caso contrário.
    """
    try:
        # Obter a URL do banco de dados do arquivo .env
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url or not database_url.startswith('postgresql'):
            print("Erro: DATABASE_URL não configurada ou não é PostgreSQL.")
            print("Verifique o arquivo .env e configure DATABASE_URL=postgresql://usuario:senha@localhost:5432/ti_reminder_db")
            return False
        
        # Parsear a URL do banco de dados
        url = urlparse(database_url)
        dbname = url.path[1:]
        user = url.username
        password = url.password
        host = url.hostname
        port = url.port
        
        # Conectar ao servidor PostgreSQL (banco postgres padrão)
        conn = psycopg2.connect(
            dbname="postgres",
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Verificar se o banco de dados já existe
        cursor.execute(f"SELECT 1 FROM pg_catalog.pg_database WHERE datname = '{dbname}'")
        exists = cursor.fetchone()
        
        if not exists:
            # Criar o banco de dados
            cursor.execute(f"CREATE DATABASE {dbname}")
            print(f"Banco de dados '{dbname}' criado com sucesso!")
        else:
            print(f"Banco de dados '{dbname}' já existe.")
        
        cursor.close()
        conn.close()
        
        return True
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
        # Criar uma aplicação Flask temporária para inicializar as migrações
        app = Flask(__name__)
        app.config['SQLALCHEMY_DATABASE_URI'] = os.environ.get('DATABASE_URL')
        app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
        
        # Importar os modelos e inicializar o banco de dados
        from app.models import db
        db.init_app(app)
        
        # Inicializar o Flask-Migrate
        migrate = Migrate(app, db)
        
        with app.app_context():
            # Verificar se a pasta migrations/versions existe
            if not os.path.exists('migrations/versions'):
                # Se não existir, criar a estrutura de migrações
                os.system('flask db init')
                
                # Criar uma migração inicial se não houver nenhuma
                if not os.listdir('migrations/versions'):
                    os.system('flask db migrate -m "initial"')
                
                # Aplicar as migrações
                os.system('flask db upgrade')
            else:
                # Se já existem migrações, apenas verificar se há alterações pendentes
                # e aplicar as migrações existentes sem criar novas
                print("Migrações já existem. Aplicando migrações existentes...")
                os.system('flask db upgrade')
            
            # Inicializar configurações padrão de SLA
            from app.models import SlaConfig
            SlaConfig.criar_configuracoes_padrao()
            print("Configurações padrão de SLA inicializadas!")
        
        return True
    except Exception as e:
        print(f"Erro ao inicializar migrações: {str(e)}")
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