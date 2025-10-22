from sqlalchemy import create_engine, text
import os
import sys

# Configuração do banco de dados
DB_USER = os.environ.get('POSTGRES_USER', 'postgres')
DB_PASSWORD = os.environ.get('POSTGRES_PASSWORD', 'postgres')
DB_HOST = os.environ.get('POSTGRES_HOST', 'localhost')
DB_PORT = os.environ.get('POSTGRES_PORT', '5432')
DB_NAME = os.environ.get('POSTGRES_DB', 'ti_reminder')

# String de conexão
DB_URI = f"postgresql://{DB_USER}:{DB_PASSWORD}@{DB_HOST}:{DB_PORT}/{DB_NAME}"

def add_columns():
    # Usa a string de conexão definida acima
    db_uri = DB_URI
    
    # Cria uma conexão com o banco de dados
    engine = create_engine(db_uri)
    
    try:
        with engine.connect() as connection:
            # Verifica se a coluna já existe
            result = connection.execute(text(
                """
                SELECT column_name 
                FROM information_schema.columns 
                WHERE table_name='equipment_loan' AND column_name='loan_time';
                """
            )
            
            # Se não existir, adiciona as colunas
            if not result.fetchone():
                print("Adicionando colunas de horário...")
                
                # Adiciona a coluna loan_time
                connection.execute(text(
                    """
                    ALTER TABLE equipment_loan 
                    ADD COLUMN loan_time TIME NOT NULL DEFAULT '09:00:00';
                    """
                )
                
                # Remove o valor padrão
                connection.execute(text(
                    """
                    ALTER TABLE equipment_loan 
                    ALTER COLUMN loan_time DROP DEFAULT;
                    """
                )
                
                # Adiciona a coluna expected_return_time
                connection.execute(text(
                    """
                    ALTER TABLE equipment_loan 
                    ADD COLUMN expected_return_time TIME NOT NULL DEFAULT '18:00:00';
                    """
                )
                
                # Remove o valor padrão
                connection.execute(text(
                    """
                    ALTER TABLE equipment_loan 
                    ALTER COLUMN expected_return_time DROP DEFAULT;
                    """
                )
                
                print("Colunas adicionadas com sucesso!")
                connection.commit()
            else:
                print("As colunas já existem no banco de dados.")
                
    except Exception as e:
        print(f"Erro ao adicionar colunas: {str(e)}")
        sys.exit(1)

if __name__ == "__main__":
    add_columns()
