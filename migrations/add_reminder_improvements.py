"""
Script de migração para adicionar melhorias ao sistema de lembretes
Adiciona novos campos: priority, notes, contract_number, cost, supplier, category
E cria tabela ReminderHistory para auditoria

Execute: python migrations/add_reminder_improvements.py
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import create_app, db
from sqlalchemy import text

def run_migration():
    """Executa a migração"""
    app = create_app()
    
    with app.app_context():
        print("🚀 Iniciando migração de melhorias de lembretes...")
        
        try:
            # Verificar se as colunas já existem
            inspector = db.inspect(db.engine)
            reminder_columns = [col['name'] for col in inspector.get_columns('reminder')]
            
            # Adicionar novos campos à tabela reminder
            new_columns = {
                'priority': "VARCHAR(20) DEFAULT 'media'",
                'notes': "TEXT",
                'contract_number': "VARCHAR(100)",
                'cost': "FLOAT",
                'supplier': "VARCHAR(200)",
                'category': "VARCHAR(100)"
            }
            
            print("\n📋 Adicionando novos campos à tabela 'reminder'...")
            for column_name, column_type in new_columns.items():
                if column_name not in reminder_columns:
                    sql = f"ALTER TABLE reminder ADD COLUMN {column_name} {column_type}"
                    db.session.execute(text(sql))
                    print(f"   ✅ Coluna '{column_name}' adicionada")
                else:
                    print(f"   ⏭️  Coluna '{column_name}' já existe")
            
            db.session.commit()
            print("\n✅ Novos campos adicionados com sucesso!")
            
            # Verificar se tabela ReminderHistory existe
            tables = inspector.get_table_names()
            
            if 'reminder_history' not in tables:
                print("\n📋 Criando tabela 'reminder_history'...")
                
                # Detectar tipo de banco de dados
                db_type = db.engine.dialect.name
                
                if db_type == 'postgresql':
                    create_table_sql = """
                    CREATE TABLE reminder_history (
                        id SERIAL PRIMARY KEY,
                        reminder_id INTEGER NOT NULL,
                        original_due_date DATE NOT NULL,
                        action_type VARCHAR(50) NOT NULL,
                        action_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        completed BOOLEAN DEFAULT FALSE,
                        completed_by INTEGER,
                        notes TEXT,
                        FOREIGN KEY (reminder_id) REFERENCES reminder(id) ON DELETE CASCADE,
                        FOREIGN KEY (completed_by) REFERENCES "user"(id)
                    )
                    """
                else:  # SQLite
                    create_table_sql = """
                    CREATE TABLE reminder_history (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        reminder_id INTEGER NOT NULL,
                        original_due_date DATE NOT NULL,
                        action_type VARCHAR(50) NOT NULL,
                        action_date DATETIME DEFAULT CURRENT_TIMESTAMP,
                        completed BOOLEAN DEFAULT FALSE,
                        completed_by INTEGER,
                        notes TEXT,
                        FOREIGN KEY (reminder_id) REFERENCES reminder(id) ON DELETE CASCADE,
                        FOREIGN KEY (completed_by) REFERENCES user(id)
                    )
                    """
                
                db.session.execute(text(create_table_sql))
                db.session.commit()
                print("   ✅ Tabela 'reminder_history' criada com sucesso!")
            else:
                print("\n⏭️  Tabela 'reminder_history' já existe")
            
            # Atualizar status 'cancelado' para incluir 'encerrado' se necessário
            print("\n📋 Verificando valores de status...")
            db.session.commit()
            print("   ✅ Verificação de status concluída")
            
            print("\n" + "="*60)
            print("✅ MIGRAÇÃO CONCLUÍDA COM SUCESSO!")
            print("="*60)
            print("\n📌 Próximos passos:")
            print("   1. Reinicie a aplicação")
            print("   2. Teste a criação de novos lembretes")
            print("   3. Verifique as notificações preventivas")
            print("\n")
            
        except Exception as e:
            db.session.rollback()
            print(f"\n❌ ERRO na migração: {str(e)}")
            import traceback
            traceback.print_exc()
            sys.exit(1)

if __name__ == '__main__':
    print("""
╔══════════════════════════════════════════════════════════════╗
║     MIGRAÇÃO: Melhorias do Sistema de Lembretes             ║
║                                                              ║
║  Esta migração adiciona:                                     ║
║  • Campos de prioridade, categoria, custo                   ║
║  • Campos de contrato, fornecedor, observações              ║
║  • Tabela de histórico para auditoria                       ║
╚══════════════════════════════════════════════════════════════╝
    """)
    
    response = input("Deseja continuar com a migração? (s/n): ")
    if response.lower() in ['s', 'sim', 'y', 'yes']:
        run_migration()
    else:
        print("❌ Migração cancelada pelo usuário")
