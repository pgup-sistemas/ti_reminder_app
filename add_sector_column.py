import sqlite3
import os

def add_sector_column():
    # Caminho para o banco de dados SQLite
    db_path = os.path.join(os.path.dirname(__file__), 'instance', 'reminder.db')
    
    # Se o banco de dados não estiver na pasta instance, tente o diretório raiz
    if not os.path.exists(db_path):
        db_path = os.path.join(os.path.dirname(__file__), 'reminder.db')
    
    print(f"Conectando ao banco de dados em: {db_path}")
    
    try:
        # Conectar ao banco de dados
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Verificar se a coluna já existe
        cursor.execute("PRAGMA table_info('user')")
        columns = [column[1] for column in cursor.fetchall()]
        
        if 'sector_id' not in columns:
            print("Adicionando coluna sector_id à tabela user...")
            # Adicionar a coluna sector_id
            cursor.execute('''
            ALTER TABLE user 
            ADD COLUMN sector_id INTEGER 
            REFERENCES sector(id) 
            ON DELETE SET NULL;
            ''')
            conn.commit()
            print("Coluna sector_id adicionada com sucesso!")
        else:
            print("A coluna sector_id já existe na tabela user.")
            
        # Verificar se a alteração foi bem-sucedida
        cursor.execute("PRAGMA table_info('user')")
        print("\nEstrutura atual da tabela user:")
        print("-" * 50)
        for column in cursor.fetchall():
            print(f"Nome: {column[1]}, Tipo: {column[2]}, Pode ser nulo: {not column[3]}, Valor padrão: {column[4]}")
        print("-" * 50)
        
    except sqlite3.Error as e:
        print(f"Erro ao acessar o banco de dados: {e}")
    finally:
        if conn:
            conn.close()
            print("Conexão com o banco de dados encerrada.")

if __name__ == '__main__':
    add_sector_column()
