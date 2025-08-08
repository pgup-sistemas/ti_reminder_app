"""
Script para adicionar controle de status e data de fim aos lembretes
"""
import sqlite3
from datetime import date

def add_reminder_control_fields():
    """Adiciona campos de controle ao modelo Reminder"""
    
    # Conectar ao banco
    conn = sqlite3.connect('instance/reminder.db')
    cursor = conn.cursor()
    
    # Verificar se a coluna created_at existe
    cursor.execute("PRAGMA table_info(reminder)")
    columns = cursor.fetchall()
    column_names = [column[1] for column in columns]
    
    try:
        # Adicionar novos campos se não existirem
        if 'status' not in column_names:
            cursor.execute("""
                ALTER TABLE reminder 
                ADD COLUMN status TEXT DEFAULT 'ativo'
            """)
            print("✅ Campo status adicionado com sucesso!")
        
        if 'pause_until' not in column_names:
            cursor.execute("""
                ALTER TABLE reminder 
                ADD COLUMN pause_until DATE
            """)
            print("✅ Campo pause_until adicionado com sucesso!")
        
        if 'end_date' not in column_names:
            cursor.execute("""
                ALTER TABLE reminder 
                ADD COLUMN end_date DATE
            """)
            print("✅ Campo end_date adicionado com sucesso!")
        
        if 'created_at' not in column_names:
            # SQLite não permite adicionar colunas com DEFAULT não constante
            # Vamos adicionar a coluna sem o DEFAULT e depois atualizar os valores existentes
            cursor.execute("""
                ALTER TABLE reminder 
                ADD COLUMN created_at TIMESTAMP
            """)
            
            # Atualizar registros existentes com a data atual
            import time
            current_time = time.strftime('%Y-%m-%d %H:%M:%S')
            cursor.execute(f"""
                UPDATE reminder 
                SET created_at = '{current_time}'
                WHERE created_at IS NULL
            """)
            print("✅ Campo created_at adicionado com sucesso!")
        
        # Atualizar lembretes existentes para status 'ativo'
        cursor.execute("""
            UPDATE reminder 
            SET status = 'ativo' 
            WHERE status IS NULL
        """)
        
        print("✅ Lembretes existentes atualizados!")
        
        conn.commit()
        
    except sqlite3.OperationalError as e:
        if "duplicate column name" in str(e):
            print("ℹ️ Campos já existem no banco")
        else:
            print(f"❌ Erro: {e}")
    except Exception as e:
        print(f"❌ Erro: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    add_reminder_control_fields()
