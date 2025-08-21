import os
import sys
import psycopg2
from urllib.parse import urlparse
from dotenv import load_dotenv

# Carregar variáveis de ambiente
load_dotenv()

def fix_migrations():
    """
    Corrige problemas com migrações duplicadas.
    Remove a migração conflitante e limpa o estado do banco de dados.
    
    Returns:
        bool: True se a correção foi bem-sucedida, False caso contrário.
    """
    try:
        print("=== Correção de Migrações do TI Reminder App ===")
        print("Este script irá corrigir problemas com migrações duplicadas.")
        print("ATENÇÃO: Este processo pode causar perda de dados se executado incorretamente.")
        
        confirm = input("\nDeseja prosseguir com a correção? (s/n): ")
        if confirm.lower() != 's':
            print("Correção cancelada.")
            return False
        
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
        
        # Conectar ao banco de dados PostgreSQL
        conn = psycopg2.connect(
            dbname=dbname,
            user=user,
            password=password,
            host=host,
            port=port
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # 1. Remover a tabela alembic_version para limpar o estado das migrações
        print("\nLimpando estado das migrações...")
        cursor.execute("DROP TABLE IF EXISTS alembic_version;")
        print("Tabela alembic_version removida com sucesso.")
        
        # 2. Remover o arquivo de flag para forçar a reinicialização
        if os.path.exists('db_initialized.flag'):
            os.remove('db_initialized.flag')
            print("Arquivo de flag removido com sucesso.")
        
        # 3. Remover migrações conflitantes
        migration_files = [
            'migrations/versions/99c62be90766_initial.py',
            'migrations/versions/aa0bcd2a67ee_initial.py'
        ]
        
        for file in migration_files:
            if os.path.exists(file):
                os.remove(file)
                print(f"Arquivo de migração {file} removido com sucesso.")
        
        # 4. Limpar o diretório de migrações
        if os.path.exists('migrations/versions/__pycache__'):
            for file in os.listdir('migrations/versions/__pycache__'):
                os.remove(os.path.join('migrations/versions/__pycache__', file))
            print("Cache de migrações limpo com sucesso.")
        
        cursor.close()
        conn.close()
        
        print("\n=== Correção concluída com sucesso! ===")
        print("Agora você pode executar 'python run.py' para inicializar o banco de dados novamente.")
        return True
    except Exception as e:
        print(f"Erro ao corrigir migrações: {str(e)}")
        return False

if __name__ == "__main__":
    fix_migrations()