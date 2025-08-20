import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
from datetime import datetime

# Carregar variáveis de ambiente
load_dotenv()

# Obter a URL do banco de dados do arquivo .env
database_url = os.environ.get('DATABASE_URL')

# Extrair informações de conexão da URL
# Formato: postgresql://postgres:postgres@localhost:5432/ti_reminder_db
db_info = database_url.replace('postgresql://', '').split('@')
user_pass = db_info[0].split(':')
host_port_db = db_info[1].split('/')
host_port = host_port_db[0].split(':')

db_user = user_pass[0]
db_password = user_pass[1]
db_host = host_port[0]
db_port = host_port[1]
db_name = host_port_db[1]

# Conectar ao banco de dados
conn = psycopg2.connect(
    host=db_host,
    user=db_user,
    password=db_password,
    port=db_port,
    database=db_name
)
conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
cursor = conn.cursor()

# Verificar se a tabela "reminder" existe
cursor.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'reminder'
    );
""")
table_exists = cursor.fetchone()[0]

if not table_exists:
    print('A tabela "reminder" não existe. Criando tabela...')
    # Criar tabela reminder
    cursor.execute("""
    CREATE TABLE "reminder" (
        id SERIAL PRIMARY KEY,
        name VARCHAR(120) NOT NULL,
        type VARCHAR(50) NOT NULL,
        due_date DATE NOT NULL,
        responsible VARCHAR(100) NOT NULL,
        frequency VARCHAR(20),
        notified BOOLEAN DEFAULT FALSE,
        completed BOOLEAN DEFAULT FALSE,
        sector_id INTEGER REFERENCES "sector"(id),
        user_id INTEGER REFERENCES "user"(id),
        status VARCHAR(20) DEFAULT 'ativo',
        pause_until DATE,
        end_date DATE,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );
    """)
    print('Tabela "reminder" criada com sucesso!')
else:
    print('Tabela "reminder" já existe.')

# Verificar se a tabela "task" existe
cursor.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'task'
    );
""")
table_exists = cursor.fetchone()[0]

if not table_exists:
    print('A tabela "task" não existe. Criando tabela...')
    # Criar tabela task
    cursor.execute("""
    CREATE TABLE "task" (
        id SERIAL PRIMARY KEY,
        description VARCHAR(200) NOT NULL,
        date DATE DEFAULT CURRENT_DATE,
        responsible VARCHAR(100) NOT NULL,
        completed BOOLEAN DEFAULT FALSE,
        sector_id INTEGER REFERENCES "sector"(id),
        user_id INTEGER REFERENCES "user"(id)
    );
    """)
    print('Tabela "task" criada com sucesso!')
else:
    print('Tabela "task" já existe.')

# Verificar se a tabela "chamado" existe
cursor.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'chamado'
    );
""")
table_exists = cursor.fetchone()[0]

if not table_exists:
    print('A tabela "chamado" não existe. Criando tabela...')
    # Criar tabela chamado
    cursor.execute("""
    CREATE TABLE "chamado" (
        id SERIAL PRIMARY KEY,
        titulo VARCHAR(120) NOT NULL,
        descricao TEXT NOT NULL,
        status VARCHAR(50) NOT NULL DEFAULT 'Aberto',
        prioridade VARCHAR(50) NOT NULL DEFAULT 'Media',
        data_abertura TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
        data_ultima_atualizacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        data_fechamento TIMESTAMP,
        solicitante_id INTEGER REFERENCES "user"(id) NOT NULL,
        setor_id INTEGER REFERENCES "sector"(id) NOT NULL,
        responsavel_ti_id INTEGER REFERENCES "user"(id)
    );
    """)
    print('Tabela "chamado" criada com sucesso!')
else:
    print('Tabela "chamado" já existe.')

# Fechar conexão
cursor.close()
conn.close()