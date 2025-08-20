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

# Lista de tabelas a serem verificadas e criadas
tabelas = [
    {
        "nome": "comentario_chamado",
        "sql": """
        CREATE TABLE "comentario_chamado" (
            id SERIAL PRIMARY KEY,
            chamado_id INTEGER REFERENCES "chamado"(id) NOT NULL,
            usuario_id INTEGER REFERENCES "user"(id) NOT NULL,
            texto TEXT NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            tipo VARCHAR(20) DEFAULT 'comentario'
        );
        """
    },
    {
        "nome": "tutorial",
        "sql": """
        CREATE TABLE "tutorial" (
            id SERIAL PRIMARY KEY,
            titulo VARCHAR(150) NOT NULL,
            conteudo TEXT NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP NOT NULL,
            autor_id INTEGER REFERENCES "user"(id) NOT NULL,
            categoria VARCHAR(100)
        );
        """
    },
    {
        "nome": "tutorial_image",
        "sql": """
        CREATE TABLE "tutorial_image" (
            id SERIAL PRIMARY KEY,
            tutorial_id INTEGER REFERENCES "tutorial"(id) NOT NULL,
            filename VARCHAR(255) NOT NULL,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    },
    {
        "nome": "comentario_tutorial",
        "sql": """
        CREATE TABLE "comentario_tutorial" (
            id SERIAL PRIMARY KEY,
            tutorial_id INTEGER REFERENCES "tutorial"(id) NOT NULL,
            usuario_id INTEGER REFERENCES "user"(id) NOT NULL,
            texto TEXT NOT NULL,
            data_criacao TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            chamado_id INTEGER REFERENCES "chamado"(id)
        );
        """
    },
    {
        "nome": "feedback_tutorial",
        "sql": """
        CREATE TABLE "feedback_tutorial" (
            id SERIAL PRIMARY KEY,
            tutorial_id INTEGER REFERENCES "tutorial"(id) NOT NULL,
            usuario_id INTEGER REFERENCES "user"(id) NOT NULL,
            util BOOLEAN NOT NULL,
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    },
    {
        "nome": "visualizacao_tutorial",
        "sql": """
        CREATE TABLE "visualizacao_tutorial" (
            id SERIAL PRIMARY KEY,
            tutorial_id INTEGER REFERENCES "tutorial"(id) NOT NULL,
            usuario_id INTEGER REFERENCES "user"(id),
            data TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        );
        """
    },
    {
        "nome": "equipment_request",
        "sql": """
        CREATE TABLE "equipment_request" (
            id SERIAL PRIMARY KEY,
            description TEXT NOT NULL,
            patrimony VARCHAR(50),
            delivery_date DATE,
            return_date DATE,
            conference_status VARCHAR(50),
            observations TEXT,
            requester_id INTEGER REFERENCES "user"(id) NOT NULL,
            received_by_id INTEGER REFERENCES "user"(id),
            approved_by_id INTEGER REFERENCES "user"(id),
            status VARCHAR(20) NOT NULL DEFAULT 'Solicitado',
            request_date TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            approval_date TIMESTAMP,
            equipment_type VARCHAR(50),
            destination_sector VARCHAR(100),
            request_reason TEXT,
            created_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP NOT NULL DEFAULT CURRENT_TIMESTAMP
        );
        """
    }
]

# Verificar e criar cada tabela
tabelas_criadas = 0
tabelas_existentes = 0

for tabela in tabelas:
    # Verificar se a tabela existe
    cursor.execute(f"""
        SELECT EXISTS (
            SELECT FROM information_schema.tables 
            WHERE table_schema = 'public' 
            AND table_name = '{tabela["nome"]}'
        );
    """)
    table_exists = cursor.fetchone()[0]
    
    if not table_exists:
        print(f'A tabela "{tabela["nome"]}" não existe. Criando tabela...')
        # Criar tabela
        cursor.execute(tabela["sql"])
        print(f'Tabela "{tabela["nome"]}" criada com sucesso!')
        tabelas_criadas += 1
    else:
        print(f'Tabela "{tabela["nome"]}" já existe.')
        tabelas_existentes += 1

# Fechar conexão
cursor.close()
conn.close()

print(f"\nResumo da operação:")
print(f"- {tabelas_criadas} tabelas foram criadas")
print(f"- {tabelas_existentes} tabelas já existiam")
print(f"- {len(tabelas)} tabelas verificadas no total")