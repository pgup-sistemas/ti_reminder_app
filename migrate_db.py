from app import create_app, db
from app.models import User, Sector

def migrate():
    app = create_app()
    with app.app_context():
        # Adiciona a coluna sector_id à tabela user se ainda não existir
        with db.engine.connect() as conn:
            # Verifica se a coluna já existe
            result = conn.execute(
                """
                SELECT COUNT(*)
                FROM information_schema.columns 
                WHERE table_name = 'user' AND column_name = 'sector_id';
                """
            )
            if result.scalar() == 0:
                # Adiciona a coluna sector_id
                conn.execute(
                    """
                    ALTER TABLE "user" 
                    ADD COLUMN sector_id INTEGER 
                    REFERENCES sector(id) 
                    ON DELETE SET NULL;
                    """
                )
                print("Coluna sector_id adicionada com sucesso à tabela user.")
            else:
                print("A coluna sector_id já existe na tabela user.")

if __name__ == '__main__':
    migrate()
