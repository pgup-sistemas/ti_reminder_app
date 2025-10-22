"""Script para verificar tabelas no banco"""
import sqlite3
import os

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'ti_reminder.db')

if not os.path.exists(db_path):
    print(f"❌ Banco de dados não encontrado em: {db_path}")
    exit(1)

print(f"✓ Conectando ao banco: {db_path}\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("TABELAS NO BANCO DE DADOS:")
print("=" * 80)

cursor.execute("SELECT name FROM sqlite_master WHERE type='table' ORDER BY name")
tables = cursor.fetchall()

for table in tables:
    print(f"\n📋 Tabela: {table[0]}")
    cursor.execute(f"PRAGMA table_info({table[0]})")
    columns = cursor.fetchall()
    for col in columns:
        nullable = "NULL" if not col[3] else "NOT NULL"
        default = f" DEFAULT {col[4]}" if col[4] else ""
        print(f"   - {col[1]} ({col[2]}) {nullable}{default}")

# Procurar por tabelas relacionadas a reserva
print("\n" + "=" * 80)
print("PROCURANDO TABELAS DE RESERVA:")
print("=" * 80)

for table in tables:
    if 'reserv' in table[0].lower() or 'equipment' in table[0].lower():
        print(f"✓ Encontrada: {table[0]}")
        
        # Contar registros
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"  Total de registros: {count}")

conn.close()
