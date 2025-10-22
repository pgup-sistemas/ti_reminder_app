"""Script para criar dados de teste de equipamentos e reservas"""
import sqlite3
import os
from datetime import datetime, timedelta

db_path = os.path.join(os.path.dirname(__file__), 'instance', 'ti_reminder.db')

if not os.path.exists(db_path):
    print(f"❌ Banco de dados não encontrado em: {db_path}")
    exit(1)

print(f"✓ Conectando ao banco: {db_path}\n")

conn = sqlite3.connect(db_path)
cursor = conn.cursor()

print("=" * 80)
print("CRIANDO DADOS DE TESTE")
print("=" * 80)

try:
    # Verificar se há usuários no sistema
    cursor.execute("SELECT id, username, is_admin, is_ti FROM user LIMIT 5")
    users = cursor.fetchall()
    
    if not users:
        print("\n❌ Nenhum usuário encontrado no banco de dados!")
        print("   Por favor, crie usuários primeiro.")
        exit(1)
    
    print(f"\n✓ Encontrados {len(users)} usuários:")
    for user in users:
        admin_flag = "ADMIN" if user[2] else ""
        ti_flag = "TI" if user[3] else ""
        flags = f" [{admin_flag} {ti_flag}]" if admin_flag or ti_flag else ""
        print(f"   - ID: {user[0]} | Username: {user[1]}{flags}")
    
    # Pegar primeiro usuário admin/ti
    admin_user = None
    regular_user = None
    
    for user in users:
        if (user[2] or user[3]) and not admin_user:
            admin_user = user
        elif not (user[2] or user[3]) and not regular_user:
            regular_user = user
    
    if not admin_user:
        admin_user = users[0]
    if not regular_user:
        regular_user = users[-1] if len(users) > 1 else users[0]
    
    print(f"\n✓ Usando usuário admin: {admin_user[1]} (ID: {admin_user[0]})")
    print(f"✓ Usando usuário regular: {regular_user[1]} (ID: {regular_user[0]})")
    
    # Criar equipamentos de teste
    print("\n1. Criando equipamentos de teste...")
    
    equipments = [
        ("Notebook Dell Latitude 5420", "Notebook corporativo Dell", "Notebook", "Dell", "Latitude 5420", "NB001", "SN123456", "disponivel", "bom", "TI - Sala 101", "TI - Armário 1", 1, 7),
        ("Monitor LG 24 polegadas", "Monitor Full HD 24\"", "Monitor", "LG", "24MK430H", "MON001", "SN789012", "disponivel", "bom", "TI - Sala 101", "TI - Armário 2", 0, 14),
        ("Mouse Logitech MX Master 3", "Mouse sem fio ergonômico", "Acessórios", "Logitech", "MX Master 3", "ACC001", "SN345678", "disponivel", "novo", "TI - Sala 101", "TI - Gaveta 1", 0, 7),
        ("Teclado Mecânico Keychron K2", "Teclado mecânico wireless", "Acessórios", "Keychron", "K2", "ACC002", "SN901234", "disponivel", "bom", "TI - Sala 101", "TI - Gaveta 1", 0, 7),
        ("Projetor Epson PowerLite", "Projetor para apresentações", "Projetor", "Epson", "PowerLite X41+", "PROJ001", "SN567890", "disponivel", "bom", "Sala de Reuniões", "TI - Armário 3", 1, 3),
    ]
    
    equipment_ids = []
    for eq in equipments:
        cursor.execute("""
            INSERT INTO equipment (
                name, description, category, brand, model, patrimony, serial_number,
                status, condition, location, storage_location, requires_approval, max_loan_days,
                created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, eq)
        equipment_ids.append(cursor.lastrowid)
        print(f"   ✓ Criado: {eq[0]} (ID: {cursor.lastrowid})")
    
    # Criar reservas pendentes de teste
    print("\n2. Criando reservas pendentes de teste...")
    
    now = datetime.now()
    tomorrow = now + timedelta(days=1)
    next_week = now + timedelta(days=7)
    
    reservations = [
        (equipment_ids[0], regular_user[0], tomorrow.date(), "09:00:00", (tomorrow + timedelta(days=3)).date(), "18:00:00", 
         datetime.combine(tomorrow.date(), datetime.strptime("09:00:00", "%H:%M:%S").time()),
         datetime.combine((tomorrow + timedelta(days=3)).date(), datetime.strptime("18:00:00", "%H:%M:%S").time()),
         (tomorrow + timedelta(days=3)).date(), "18:00:00", "pendente", "Necessário para projeto de desenvolvimento"),
        
        (equipment_ids[4], regular_user[0], (tomorrow + timedelta(days=1)).date(), "14:00:00", (tomorrow + timedelta(days=1)).date(), "17:00:00",
         datetime.combine((tomorrow + timedelta(days=1)).date(), datetime.strptime("14:00:00", "%H:%M:%S").time()),
         datetime.combine((tomorrow + timedelta(days=1)).date(), datetime.strptime("17:00:00", "%H:%M:%S").time()),
         (tomorrow + timedelta(days=1)).date(), "17:00:00", "pendente", "Apresentação para cliente"),
        
        (equipment_ids[1], regular_user[0], next_week.date(), "08:00:00", (next_week + timedelta(days=5)).date(), "18:00:00",
         datetime.combine(next_week.date(), datetime.strptime("08:00:00", "%H:%M:%S").time()),
         datetime.combine((next_week + timedelta(days=5)).date(), datetime.strptime("18:00:00", "%H:%M:%S").time()),
         (next_week + timedelta(days=5)).date(), "18:00:00", "pendente", "Trabalho remoto - monitor adicional"),
    ]
    
    for res in reservations:
        cursor.execute("""
            INSERT INTO equipment_reservation (
                equipment_id, user_id, start_date, start_time, end_date, end_time,
                start_datetime, end_datetime, expected_return_date, expected_return_time,
                status, purpose, created_at, updated_at
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, CURRENT_TIMESTAMP, CURRENT_TIMESTAMP)
        """, res)
        print(f"   ✓ Criada reserva ID: {cursor.lastrowid} - Equipamento: {res[0]}")
    
    # Commit das alterações
    conn.commit()
    
    print("\n" + "=" * 80)
    print("✅ DADOS DE TESTE CRIADOS COM SUCESSO!")
    print("=" * 80)
    
    # Verificar dados criados
    print("\n📊 Resumo dos dados criados:")
    
    cursor.execute("SELECT COUNT(*) FROM equipment")
    eq_count = cursor.fetchone()[0]
    print(f"   ✓ Equipamentos: {eq_count}")
    
    cursor.execute("SELECT COUNT(*) FROM equipment_reservation WHERE status = 'pendente'")
    res_count = cursor.fetchone()[0]
    print(f"   ✓ Reservas pendentes: {res_count}")
    
    # Mostrar reservas pendentes
    print("\n📋 Reservas pendentes criadas:")
    cursor.execute("""
        SELECT 
            er.id,
            e.name,
            u.username,
            er.start_date,
            er.end_date,
            er.purpose
        FROM equipment_reservation er
        JOIN equipment e ON er.equipment_id = e.id
        JOIN user u ON er.user_id = u.id
        WHERE er.status = 'pendente'
        ORDER BY er.created_at DESC
    """)
    
    pending = cursor.fetchall()
    for p in pending:
        print(f"   - ID: {p[0]} | {p[1]} | Usuário: {p[2]} | {p[3]} a {p[4]}")
        print(f"     Finalidade: {p[5]}")
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ ERRO ao criar dados de teste: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    conn.close()

print("\n" + "=" * 80)
print("Agora você pode acessar: http://192.168.1.86:5000/equipment/admin/pending-approvals")
print("=" * 80)
