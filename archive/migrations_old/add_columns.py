import psycopg2
from config import Config

def add_columns():
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
        
        # Verificar se as colunas já existem
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'equipment_loan' AND column_name = 'loan_time';
        """)
        
        if not cursor.fetchone():
            # Adicionar a coluna loan_time
            cursor.execute("""
                ALTER TABLE equipment_loan 
                ADD COLUMN loan_time TIME NOT NULL DEFAULT '09:00:00';
            """)
            
            # Remover o valor padrão
            cursor.execute("""
                ALTER TABLE equipment_loan 
                ALTER COLUMN loan_time DROP DEFAULT;
            """)
            
            print("Coluna 'loan_time' adicionada com sucesso.")
        else:
            print("A coluna 'loan_time' já existe.")
        
        # Verificar se a coluna expected_return_time já existe
        cursor.execute("""
            SELECT column_name 
            FROM information_schema.columns 
            WHERE table_name = 'equipment_loan' AND column_name = 'expected_return_time';
        """)
        
        if not cursor.fetchone():
            # Adicionar a coluna expected_return_time
            cursor.execute("""
                ALTER TABLE equipment_loan 
                ADD COLUMN expected_return_time TIME NOT NULL DEFAULT '18:00:00';
            """)
            
            # Remover o valor padrão
            cursor.execute("""
                ALTER TABLE equipment_loan 
                ALTER COLUMN expected_return_time DROP DEFAULT;
            """)
            
            print("Coluna 'expected_return_time' adicionada com sucesso.")
        else:
            print("A coluna 'expected_return_time' já existe.")
        
        # Confirmar as alterações
        conn.commit()
        print("Migração concluída com sucesso!")
        
    except Exception as e:
        print(f"Erro durante a migração: {e}")
        if 'conn' in locals():
            conn.rollback()
    finally:
        if 'cursor' in locals():
            cursor.close()
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    add_columns()