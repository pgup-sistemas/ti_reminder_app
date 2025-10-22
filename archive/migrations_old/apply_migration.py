"""
Script para aplicar a migração add_user_timestamp_fields diretamente ao banco de dados
"""
import os
import sys
from dotenv import load_dotenv
import psycopg2
from urllib.parse import urlparse

# Carregar variáveis de ambiente
load_dotenv()

def apply_migration():
    """Aplica a migração para adicionar as colunas last_login, created_at e updated_at"""
    try:
        # Obter a URL do banco de dados
        database_url = os.environ.get('DATABASE_URL')
        
        if not database_url:
            print("Erro: DATABASE_URL não configurada no arquivo .env")
            return False
        
        # Parsear a URL do banco de dados
        url = urlparse(database_url)
        
        # Conectar ao banco de dados
        conn = psycopg2.connect(
            dbname=url.path[1:],
            user=url.username,
            password=url.password,
            host=url.hostname,
            port=url.port
        )
        conn.autocommit = False
        cursor = conn.cursor()
        
        print("Conectado ao banco de dados com sucesso!")
        
        # Verificar se as colunas já existem
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user' 
            AND column_name IN ('last_login', 'created_at', 'updated_at')
        """)
        existing_columns = [row[0] for row in cursor.fetchall()]
        
        print(f"Colunas existentes: {existing_columns}")
        
        # Adicionar colunas que não existem
        columns_to_add = []
        if 'last_login' not in existing_columns:
            columns_to_add.append(('last_login', 'TIMESTAMP'))
        if 'created_at' not in existing_columns:
            columns_to_add.append(('created_at', 'TIMESTAMP'))
        if 'updated_at' not in existing_columns:
            columns_to_add.append(('updated_at', 'TIMESTAMP'))
        
        if not columns_to_add:
            print("Todas as colunas já existem. Nenhuma alteração necessária.")
            cursor.close()
            conn.close()
            return True
        
        # Adicionar as colunas
        for column_name, column_type in columns_to_add:
            print(f"Adicionando coluna {column_name}...")
            cursor.execute(f'ALTER TABLE "user" ADD COLUMN {column_name} {column_type}')
        
        # Commit das alterações
        conn.commit()
        print("Migração aplicada com sucesso!")
        
        # Verificar se as colunas foram adicionadas
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user' 
            AND column_name IN ('last_login', 'created_at', 'updated_at')
        """)
        final_columns = [row[0] for row in cursor.fetchall()]
        print(f"Colunas após migração: {final_columns}")
        
        cursor.close()
        conn.close()
        
        return True
        
    except Exception as e:
        print(f"Erro ao aplicar migração: {str(e)}")
        if 'conn' in locals():
            conn.rollback()
            conn.close()
        return False

if __name__ == "__main__":
    if apply_migration():
        print("\n✓ Migração concluída com sucesso!")
        print("Você pode agora reiniciar o servidor Flask.")
    else:
        print("\n✗ Falha ao aplicar migração.")
        sys.exit(1)
