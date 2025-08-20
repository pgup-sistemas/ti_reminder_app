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

# Verificar se a tabela "sector" existe
cursor.execute("""
    SELECT EXISTS (
        SELECT FROM information_schema.tables 
        WHERE table_schema = 'public' 
        AND table_name = 'sector'
    );
""")
table_exists = cursor.fetchone()[0]

if not table_exists:
    print('A tabela "sector" não existe. Criando tabela...')
    # Criar tabela sector
    cursor.execute("""
    CREATE TABLE "sector" (
        id SERIAL PRIMARY KEY,
        name VARCHAR(100) UNIQUE NOT NULL
    );
    """)
    print('Tabela "sector" criada com sucesso!')
    
    # Inserir alguns setores padrão
    setores = [
        "TI",
        "Administrativo",
        "Financeiro",
        "Recursos Humanos",
        "Comercial",
        "Operacional"
    ]
    
    for setor in setores:
        cursor.execute('INSERT INTO "sector" (name) VALUES (%s)', (setor,))
    
    print(f'Foram inseridos {len(setores)} setores padrão.')
else:
    print('Tabela "sector" já existe.')

# Fechar conexão
cursor.close()
conn.close()