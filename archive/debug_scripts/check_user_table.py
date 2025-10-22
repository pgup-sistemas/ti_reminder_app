#!/usr/bin/env python
"""
Script para verificar a estrutura da tabela 'user'
"""
import psycopg2
from psycopg2 import sql

def check_user_table():
    try:
        # Conectar ao banco de dados
        conn = psycopg2.connect(
            host='localhost',
            database='ti_reminder_db',
            user='postgres',
            password='postgres'
        )
        
        # Criar um cursor para executar consultas
        with conn.cursor() as cur:
            # Verificar colunas da tabela user
            cur.execute("""
                SELECT column_name, data_type, is_nullable
                FROM information_schema.columns
                WHERE table_name = 'user'
                ORDER BY ordinal_position
            """)
            
            print("=== ESTRUTURA DA TABELA 'user' ===")
            print(f"{'Coluna':<20} {'Tipo':<20} {'Pode ser nulo?'}")
            print("-" * 50)
            
            for col in cur.fetchall():
                print(f"{col[0]:<20} {col[1]:<20} {col[2]}")
            
            # Verificar índices
            cur.execute("""
                SELECT indexname, indexdef
                FROM pg_indexes
                WHERE tablename = 'user'
            """)
            
            print("\n=== ÍNDICES DA TABELA 'user' ===")
            for idx in cur.fetchall():
                print(f"\n{idx[0]}:")
                print(f"  {idx[1]}")
            
            # Verificar restrições
            cur.execute("""
                SELECT conname, pg_get_constraintdef(oid)
                FROM pg_constraint
                WHERE conrelid = 'public."user"'::regclass
            """)
            
            print("\n=== RESTRIÇÕES DA TABELA 'user' ===")
            for con in cur.fetchall():
                print(f"\n{con[0]}:")
                print(f"  {con[1]}")
    
    except Exception as e:
        print(f"Erro ao verificar a tabela 'user': {e}")
    finally:
        if 'conn' in locals():
            conn.close()

if __name__ == "__main__":
    check_user_table()
