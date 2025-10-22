"""Script direto para verificar reservas no banco"""
import sqlite3
import os

# Caminho do banco de dados
db_path = os.path.join(os.path.dirname(__file__), 'instance', 'ti_reminder.db')

if not os.path.exists(db_path):
    print(f"❌ Banco de dados não encontrado em: {db_path}")
    exit(1)

print(f"✓ Conectando ao banco: {db_path}\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("VERIFICANDO RESERVAS PENDENTES")
print("=" * 80)

# Verificar todas as reservas pendentes
cursor.execute("""
    SELECT 
        er.id,
        er.status,
        er.start_date,
        er.start_time,
        er.start_datetime,
        er.end_date,
        er.end_time,
        er.end_datetime,
        er.created_at,
        e.name as equipment_name,
        u.username
    FROM equipment_reservation er
    JOIN equipment e ON er.equipment_id = e.id
    JOIN user u ON er.user_id = u.id
    WHERE er.status = 'pendente'
    ORDER BY er.created_at DESC
""")

reservations = cursor.fetchall()

print(f"\n✓ Total de reservas pendentes: {len(reservations)}\n")

if reservations:
    print("-" * 80)
    print("DETALHES DAS RESERVAS:")
    print("-" * 80)
    
    for i, res in enumerate(reservations, 1):
        res_id, status, start_date, start_time, start_datetime, end_date, end_time, end_datetime, created_at, equipment, username = res
        print(f"\n[{i}] Reserva ID: {res_id}")
        print(f"    Equipamento: {equipment}")
        print(f"    Usuário: {username}")
        print(f"    Status: {status}")
        print(f"    Start Date: {start_date}")
        print(f"    Start Time: {start_time}")
        print(f"    Start DateTime: {start_datetime}")
        print(f"    End Date: {end_date}")
        print(f"    End Time: {end_time}")
        print(f"    End DateTime: {end_datetime}")
        print(f"    Created At: {created_at}")
        
        if start_datetime is None:
            print(f"    ⚠️ PROBLEMA: start_datetime está NULL!")
        if end_datetime is None:
            print(f"    ⚠️ PROBLEMA: end_datetime está NULL!")

# Contar reservas com datetime NULL
cursor.execute("""
    SELECT COUNT(*) 
    FROM equipment_reservation 
    WHERE status = 'pendente' 
    AND (start_datetime IS NULL OR end_datetime IS NULL)
""")

null_count = cursor.fetchone()[0]
print(f"\n⚠️ Reservas pendentes com datetime NULL: {null_count}")

# Verificar estrutura da tabela
print("\n" + "=" * 80)
print("ESTRUTURA DA TABELA equipment_reservation:")
print("=" * 80)
cursor.execute("PRAGMA table_info(equipment_reservation)")
columns = cursor.fetchall()
for col in columns:
    print(f"  - {col[1]} ({col[2]}) {'NOT NULL' if col[3] else 'NULL'}")

conn.close()
print("\n" + "=" * 80)
