import sys
import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv

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

# Verificar se a tabela "user" existe
cursor.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'user'
    );
""")
table_exists = cursor.fetchone()[0]

if not table_exists:
    print('A tabela "user" não existe. Criando tabela...')
    # Criar tabela user
    cursor.execute("""
    CREATE TABLE "user" (
        id SERIAL PRIMARY KEY,
        username VARCHAR(64) UNIQUE NOT NULL,
        email VARCHAR(120) UNIQUE NOT NULL,
        password_hash VARCHAR(128) NOT NULL,
        is_admin BOOLEAN DEFAULT FALSE,
        is_ti BOOLEAN DEFAULT FALSE,
        ativo BOOLEAN DEFAULT TRUE,
        sector_id INTEGER,
        reset_token VARCHAR(100),
        reset_token_expiry TIMESTAMP
    );
    """)
    print('Tabela "user" criada com sucesso!')

# Verificar se o usuário admin já existe
cursor.execute('SELECT * FROM "user" WHERE username = %s', ('admin',))
admin_exists = cursor.fetchone()

if not admin_exists:
    # Importar bcrypt para gerar o hash da senha
    import bcrypt
    
    # Gerar hash da senha
    password = 'admin123'
    password_hash = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt()).decode('utf-8')
    
    # Inserir usuário admin
    cursor.execute("""
    INSERT INTO "user" (username, email, password_hash, is_admin, ativo)
    VALUES (%s, %s, %s, %s, %s)
    """, ('admin', 'admin@admin.com', password_hash, True, True))
    
    print('Usuário admin criado com sucesso!')
else:
    print('Usuário admin já existe.')

# Fechar conexão
cursor.close()
conn.close()