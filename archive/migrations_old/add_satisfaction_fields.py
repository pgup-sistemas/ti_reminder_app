#!/usr/bin/env python
"""
Script para adicionar campos de satisfação ao modelo Chamado
"""
from app import create_app
from app.models import db, Chamado

def add_satisfaction_fields():
    """Adiciona campos de satisfação ao banco de dados"""

    app = create_app()

    with app.app_context():
        try:
            print("=== ADICIONANDO CAMPOS DE SATISFAÇÃO ===")

            # Verificar se os campos já existem
            inspector = db.inspect(db.engine)
            columns = [col['name'] for col in inspector.get_columns('chamado')]

            campos_para_adicionar = [
                'satisfaction_rating',
                'satisfaction_comment',
                'satisfaction_date',
                'survey_sent',
                'survey_sent_date'
            ]

            campos_existentes = [campo for campo in campos_para_adicionar if campo in columns]
            campos_faltando = [campo for campo in campos_para_adicionar if campo not in columns]

            if campos_faltando:
                print(f"Campos a adicionar: {', '.join(campos_faltando)}")

                # Adicionar campos via SQL direto
                with db.engine.connect() as conn:
                    # Adicionar campos de satisfação
                    try:
                        conn.execute(db.text("""
                            ALTER TABLE chamado
                            ADD COLUMN IF NOT EXISTS satisfaction_rating INTEGER,
                            ADD COLUMN IF NOT EXISTS satisfaction_comment TEXT,
                            ADD COLUMN IF NOT EXISTS satisfaction_date TIMESTAMP,
                            ADD COLUMN IF NOT EXISTS survey_sent BOOLEAN DEFAULT FALSE,
                            ADD COLUMN IF NOT EXISTS survey_sent_date TIMESTAMP
                        """))
                        conn.commit()
                        print("SUCESSO: Campos de satisfacao adicionados com sucesso!")
                    except Exception as e:
                        print(f"ERRO ao adicionar campos: {e}")
                        return False
            else:
                print("SUCESSO: Todos os campos de satisfacao ja existem!")

            # Verificar se há chamados de teste
            chamados_count = Chamado.query.count()
            print(f"Total de chamados no banco: {chamados_count}")

            if chamados_count == 0:
                print("INFO: Nenhum chamado encontrado. Crie alguns chamados e teste o sistema de satisfacao.")
            else:
                print("SUCESSO: Chamados encontrados. Sistema de satisfacao pronto para uso!")

            return True

        except Exception as e:
            print(f"ERRO geral: {e}")
            import traceback
            traceback.print_exc()
            return False

if __name__ == "__main__":
    success = add_satisfaction_fields()
    if success:
        print("\nSUCESSO: Configuracao de satisfacao concluida com sucesso!")
    else:
        print("\nERRO na configuracao de satisfacao!")
        exit(1)