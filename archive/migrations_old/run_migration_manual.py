from app import create_app, db
from datetime import datetime
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

def upgrade():
    # Cria a aplicação
    app = create_app()
    
    # Cria um contexto de aplicação
    with app.app_context():
        # Verifica se as colunas já existem
        inspector = sa.inspect(db.engine)
        columns = [col['name'] for col in inspector.get_columns('equipment_loan')]
        
        # Adiciona a coluna loan_time se não existir
        if 'loan_time' not in columns:
            print("Adicionando coluna 'loan_time'...")
            op = db.get_engine().begin()
            op.execute("""
                ALTER TABLE equipment_loan 
                ADD COLUMN loan_time TIME NOT NULL DEFAULT '09:00:00';
            """)
            # Remove o valor padrão após a migração
            op.execute("""
                ALTER TABLE equipment_loan 
                ALTER COLUMN loan_time DROP DEFAULT;
            """)
            print("Coluna 'loan_time' adicionada com sucesso.")
        else:
            print("Coluna 'loan_time' já existe.")
        
        # Adiciona a coluna expected_return_time se não existir
        if 'expected_return_time' not in columns:
            print("Adicionando coluna 'expected_return_time'...")
            op = db.get_engine().begin()
            op.execute("""
                ALTER TABLE equipment_loan 
                ADD COLUMN expected_return_time TIME NOT NULL DEFAULT '18:00:00';
            """)
            # Remove o valor padrão após a migração
            op.execute("""
                ALTER TABLE equipment_loan 
                ALTER COLUMN expected_return_time DROP DEFAULT;
            """)
            print("Coluna 'expected_return_time' adicionada com sucesso.")
        else:
            print("Coluna 'expected_return_time' já existe.")

if __name__ == '__main__':
    upgrade()
    print("Migração concluída com sucesso!")
