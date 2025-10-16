#!/usr/bin/env python
"""
Script simples para testar conexão com banco de dados
"""
import os
from sqlalchemy import create_engine, text

def test_db_connection():
    # Configuração da conexão
    database_url = 'postgresql://postgres:postgres@localhost:5432/ti_reminder_db'
    engine = create_engine(database_url)

    try:
        with engine.connect() as conn:
            print('=== CONEXÃO COM BANCO ESTABELECIDA ===')

            # Listar tabelas
            result = conn.execute(text("""
                SELECT schemaname, tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """))
            tables = result.fetchall()
            print(f'Total de tabelas: {len(tables)}')
            for table in tables:
                print(f'  - {table.schemaname}.{table.tablename}')

            print()
            print('=== TESTANDO ESTATÍSTICAS ===')

            # Testar estatísticas das tabelas
            result = conn.execute(text("""
                SELECT COUNT(*)
                FROM pg_stat_user_tables
                WHERE schemaname = 'public'
            """))
            count = result.scalar()
            print(f'Tabelas com estatísticas: {count}')

            if count > 0:
                result = conn.execute(text("""
                    SELECT relname as tablename, n_live_tup, n_dead_tup
                    FROM pg_stat_user_tables
                    WHERE schemaname = 'public'
                    ORDER BY n_live_tup DESC
                    LIMIT 5
                """))
                for row in result:
                    print(f'  {row.tablename}: {row.n_live_tup} ativos, {row.n_dead_tup} mortos')

            print()
            print('=== CONEXÕES ATIVAS ===')
            result = conn.execute(text("""
                SELECT count(*) as active_connections
                FROM pg_stat_activity
                WHERE state = 'active' AND datname = current_database()
            """))
            active = result.scalar()
            print(f'Conexões ativas: {active}')

            return True

    except Exception as e:
        print(f'ERRO: {e}')
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_db_connection()