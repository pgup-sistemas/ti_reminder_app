from app import create_app, db
from sqlalchemy import text

def fix_password_hash():
    app = create_app()
    with app.app_context():
        try:
            # Altera o tipo da coluna para VARCHAR(255)
            with db.engine.connect() as conn:
                # Desativa o autocommit para usar transação
                with conn.begin():
                    # Altera o tipo da coluna
                    conn.execute(text('ALTER TABLE "user" ALTER COLUMN password_hash TYPE VARCHAR(255)'))
                    print("Coluna password_hash alterada para VARCHAR(255) com sucesso!")
            
            # Atualiza o arquivo de migração mais recente
            try:
                with open('migrations/versions/a04cc84a5342_sincronizar_modelos_com_banco_de_dados.py', 'r') as f:
                    content = f.read()
                
                # Remove a alteração problemática do arquivo de migração
                content = content.replace(
                    "with op.batch_alter_table('user', schema=None) as batch_op:\n            batch_op.alter_column('password_hash',\n               existing_type=sa.VARCHAR(length=255),\n               type_=sa.String(length=128),\n               existing_nullable=False)",
                    "# Removida alteração problemática da coluna password_hash"
                )
                
                with open('migrations/versions/a04cc84a5342_sincronizar_modelos_com_banco_de_dados.py', 'w') as f:
                    f.write(content)
                    
                print("Arquivo de migração atualizado com sucesso!")
            except Exception as e:
                print(f"Aviso: Não foi possível atualizar o arquivo de migração: {e}")
            
        except Exception as e:
            print(f"Erro ao alterar a coluna: {e}")

if __name__ == '__main__':
    fix_password_hash()
