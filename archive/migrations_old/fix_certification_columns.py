import psycopg2
from config import Config

def fix_certification_columns():
    try:
        # Conectar ao banco de dados
        conn = psycopg2.connect(
            dbname=Config.SQLALCHEMY_DATABASE_URI.split('/')[-1],
            user='postgres',
            password='postgres',
            host='localhost',
            port='5432'
        )
        cursor = conn.cursor()
        
        # Verificar se a tabela user_certification existe
        cursor.execute("""
            SELECT EXISTS (
                SELECT FROM information_schema.tables 
                WHERE table_name = 'user_certification'
            );
        """)
        
        if not cursor.fetchone()[0]:
            print("A tabela 'user_certification' não existe. Nenhuma ação necessária.")
            return
        
        # Verificar se a coluna certification_type já existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'user_certification' AND column_name = 'certification_type';
        """)
        
        if not cursor.fetchone():
            # Adicionar a coluna certification_type
            cursor.execute("""
                ALTER TABLE user_certification 
                ADD COLUMN certification_type VARCHAR(50) NOT NULL DEFAULT 'default';
            """)
            
            # Remover o valor padrão após a adição
            cursor.execute("""
                ALTER TABLE user_certification 
                ALTER COLUMN certification_type DROP DEFAULT;
            """)
            
            print("Coluna 'certification_type' adicionada com sucesso.")
        else:
            print("A coluna 'certification_type' já existe.")
        
        # Confirmar as alterações
        conn.commit()
        print("Atualização da tabela 'user_certification' concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro durante a atualização: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    fix_certification_columns()