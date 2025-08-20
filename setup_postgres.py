import os
import sys
from init_db import init_postgres_db, init_migrations

def setup_postgres():
    print("=== Configuração do PostgreSQL para o TI Reminder App ===")
    print("Este script irá criar o banco de dados PostgreSQL e inicializar as migrações.")
    print("Certifique-se de que o PostgreSQL está instalado e em execução.")
    print("\nConfiguração atual (arquivo .env):")
    
    # Ler configuração atual
    with open('.env', 'r') as f:
        for line in f:
            if line.startswith('DATABASE_URL='):
                print(f"  {line.strip()}")
    
    confirm = input("\nDeseja prosseguir com a configuração? (s/n): ")
    if confirm.lower() != 's':
        print("Configuração cancelada.")
        return
    
    # Inicializar banco de dados
    print("\nInicializando banco de dados PostgreSQL...")
    if init_postgres_db():
        print("Banco de dados PostgreSQL inicializado com sucesso!")
        
        # Inicializar migrações
        print("\nInicializando migrações do Flask...")
        if init_migrations():
            print("Migrações inicializadas com sucesso!")
            
            # Criar arquivo de flag
            with open('db_initialized.flag', 'w') as f:
                f.write('1')
            
            print("\n=== Configuração concluída com sucesso! ===")
            print("O sistema está pronto para ser executado com PostgreSQL.")
            print("Execute 'python run.py' para iniciar a aplicação.")
        else:
            print("Falha ao inicializar migrações.")
    else:
        print("Falha ao inicializar banco de dados PostgreSQL.")

if __name__ == "__main__":
    setup_postgres()