import os
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash

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

# Primeiro, alterar o tamanho do campo password_hash para acomodar hashes maiores
print('Alterando o tamanho do campo password_hash...')
cursor.execute('ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(255);')
print('Tamanho do campo password_hash alterado com sucesso!')

# Buscar todos os usuários
cursor.execute('SELECT id, username, password_hash FROM "user"')
users = cursor.fetchall()

# Verificar e corrigir os hashes de senha
for user_id, username, password_hash in users:
    # Verificar se o hash da senha está no formato correto do Werkzeug
    if not password_hash.startswith('pbkdf2:sha256:') and not password_hash.startswith('scrypt:') and not password_hash.startswith('sha1:'):
        print(f'Corrigindo hash de senha para o usuário: {username}')
        
        # Para o usuário admin, definimos a senha padrão como 'admin123'
        if username == 'admin':
            new_password = 'admin123'
        else:
            # Para outros usuários, podemos definir uma senha temporária ou manter a mesma
            # Aqui estamos definindo 'password123' como senha temporária para todos os outros usuários
            new_password = 'password123'
        
        # Gerar novo hash usando Werkzeug com método sha256
        new_hash = generate_password_hash(new_password, method='pbkdf2:sha256')
        
        # Atualizar o hash da senha no banco de dados
        cursor.execute(
            'UPDATE "user" SET password_hash = %s WHERE id = %s',
            (new_hash, user_id)
        )
        
        print(f'Hash de senha atualizado para o usuário: {username}')
    else:
        print(f'O hash de senha para o usuário {username} já está no formato correto.')

print('\nProcesso de correção de hashes de senha concluído!')
print('Usuários com senhas redefinidas:')
print('- admin: admin123')
print('- outros usuários: password123 (se aplicável)')

# Fechar conexão
cursor.close()
conn.close()