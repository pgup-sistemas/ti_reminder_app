from app import create_app, db
from sqlalchemy import text, inspect
import sqlite3

def fix_database():
    app = create_app()
    with app.app_context():
        try:
            # Verifica se é SQLite
            is_sqlite = 'sqlite' in str(db.engine.url)
            
            with db.engine.connect() as conn:
                with conn.begin():
                    # Para SQLite, precisamos de uma abordagem diferente
                    if is_sqlite:
                        print("✓ Usando SQLite - Ajustando esquema...")
                        
                        # SQLite não suporta ALTER COLUMN TYPE diretamente
                        # Vamos criar uma nova tabela com a estrutura correta
                        
                        # 1. Renomear a tabela user existente
                        conn.execute(text('ALTER TABLE "user" RENAME TO user_old;'))
                        
                        # 2. Criar a tabela user com a estrutura correta
                        conn.execute(text('''
                            CREATE TABLE "user" (
                                id INTEGER NOT NULL, 
                                username VARCHAR(64), 
                                email VARCHAR(120), 
                                password_hash VARCHAR(255), 
                                is_admin BOOLEAN, 
                                is_ti BOOLEAN, 
                                ativo BOOLEAN, 
                                sector_id INTEGER, 
                                reset_token VARCHAR(100), 
                                reset_token_expiry DATETIME, 
                                PRIMARY KEY (id), 
                                FOREIGN KEY(sector_id) REFERENCES sector (id), 
                                UNIQUE (username), 
                                UNIQUE (email), 
                                CHECK (is_ti IN (0, 1)), 
                                CHECK (is_admin IN (0, 1)), 
                                CHECK (ativo IN (0, 1))
                            )
                        '''))
                        
                        # 3. Copiar os dados da tabela antiga para a nova
                        conn.execute(text('''
                            INSERT INTO "user" (id, username, email, password_hash, is_admin, is_ti, ativo, sector_id, reset_token, reset_token_expiry)
                            SELECT id, username, email, password_hash, is_admin, is_ti, ativo, sector_id, reset_token, reset_token_expiry 
                            FROM user_old
                        '''))
                        
                        # 4. Remover a tabela antiga
                        conn.execute(text('DROP TABLE user_old;'))
                        
                        print("✓ Estrutura da tabela user atualizada")
                    
                    # Adiciona colunas de SLA faltantes (compatível com SQLite)
                    inspector = inspect(db.engine)
                    columns = [col['name'] for col in inspector.get_columns('chamado')]
                    
                    if 'prazo_sla' not in columns:
                        conn.execute(text('ALTER TABLE chamado ADD COLUMN prazo_sla TIMESTAMP'))
                    if 'data_primeira_resposta' not in columns:
                        conn.execute(text('ALTER TABLE chamado ADD COLUMN data_primeira_resposta TIMESTAMP'))
                    if 'sla_cumprido' not in columns:
                        conn.execute(text('ALTER TABLE chamado ADD COLUMN sla_cumprido BOOLEAN'))
                    if 'tempo_resposta_horas' not in columns:
                        conn.execute(text('ALTER TABLE chamado ADD COLUMN tempo_resposta_horas FLOAT'))
                    
                    print("✓ Colunas de SLA verificadas")
                    
                    # Cria a tabela sla_config se não existir
                    if not inspector.has_table('sla_config'):
                        conn.execute(text('''
                            CREATE TABLE sla_config (
                                id INTEGER NOT NULL, 
                                prioridade VARCHAR(50) NOT NULL, 
                                tempo_resposta_hours INTEGER NOT NULL, 
                                tempo_resolucao_horas INTEGER, 
                                ativo BOOLEAN, 
                                PRIMARY KEY (id), 
                                UNIQUE (prioridade)
                            )
                        '''))
                        
                        # Insere configurações padrão de SLA
                        for config in [
                            ('Baixa', 48, 168, True),
                            ('Media', 24, 72, True),
                            ('Alta', 4, 24, True)
                        ]:
                            try:
                                conn.execute(text('''
                                    INSERT INTO sla_config 
                                    (prioridade, tempo_resposta_horas, tempo_resolucao_horas, ativo)
                                    VALUES (:p, :tr, :ts, :a)
                                '''), {'p': config[0], 'tr': config[1], 'ts': config[2], 'a': config[3]})
                            except Exception as e:
                                print(f"Aviso: {e}")
                        
                        print("✓ Tabela sla_config criada com configurações padrão")
                    
                    # Atualiza a versão do banco de dados
                    if inspector.has_table('alembic_version'):
                        conn.execute(text('''
                            UPDATE alembic_version 
                            SET version_num = 'b91b0d7d62b4'
                        '''))
                    
                    print("✓ Banco de dados atualizado com sucesso!")
                    
        except Exception as e:
            print(f"Erro ao atualizar o banco de dados: {e}")
            raise

if __name__ == '__main__':
    fix_database()
