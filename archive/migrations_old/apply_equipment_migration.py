"""Aplicar migração de equipamentos diretamente no banco"""
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
print("APLICANDO MIGRAÇÃO DE EQUIPAMENTOS")
print("=" * 80)

try:
    # Criar tabela equipment
    print("\n1. Criando tabela 'equipment'...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name VARCHAR(100) NOT NULL,
            description TEXT,
            category VARCHAR(50) NOT NULL,
            brand VARCHAR(50),
            model VARCHAR(50),
            patrimony VARCHAR(50),
            serial_number VARCHAR(100),
            status VARCHAR(20) NOT NULL DEFAULT 'disponivel',
            condition VARCHAR(20) NOT NULL DEFAULT 'bom',
            location VARCHAR(100),
            storage_location VARCHAR(100),
            purchase_date DATE,
            warranty_expiry DATE,
            last_maintenance DATE,
            next_maintenance DATE,
            maintenance_alert_sent BOOLEAN DEFAULT 0,
            requires_approval BOOLEAN DEFAULT 1,
            max_loan_days INTEGER DEFAULT 7,
            notes TEXT,
            image_url VARCHAR(200),
            is_active BOOLEAN DEFAULT 1,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)
    print("   ✓ Tabela 'equipment' criada com sucesso!")
    
    # Criar índices para equipment
    print("\n2. Criando índices para 'equipment'...")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_equipment_status ON equipment(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_equipment_category ON equipment(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_equipment_patrimony ON equipment(patrimony)")
    print("   ✓ Índices criados com sucesso!")
    
    # Criar tabela equipment_reservation
    print("\n3. Criando tabela 'equipment_reservation'...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment_reservation (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            start_date DATE NOT NULL,
            start_time TIME NOT NULL DEFAULT '09:00:00',
            end_date DATE NOT NULL,
            end_time TIME NOT NULL DEFAULT '18:00:00',
            start_datetime DATETIME NOT NULL,
            end_datetime DATETIME NOT NULL,
            expected_return_date DATE NOT NULL,
            expected_return_time TIME NOT NULL DEFAULT '18:00:00',
            status VARCHAR(20) NOT NULL DEFAULT 'pendente',
            purpose TEXT,
            approved_by_id INTEGER,
            approval_date DATETIME,
            approval_notes TEXT,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipment_id) REFERENCES equipment(id),
            FOREIGN KEY (user_id) REFERENCES user(id),
            FOREIGN KEY (approved_by_id) REFERENCES user(id)
        )
    """)
    print("   ✓ Tabela 'equipment_reservation' criada com sucesso!")
    
    # Criar índices para equipment_reservation
    print("\n4. Criando índices para 'equipment_reservation'...")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_equipment_reservation_status ON equipment_reservation(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_equipment_reservation_start_date ON equipment_reservation(start_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_equipment_reservation_end_date ON equipment_reservation(end_date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_equipment_reservation_start_datetime ON equipment_reservation(start_datetime)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_equipment_reservation_end_datetime ON equipment_reservation(end_datetime)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_equipment_reservation_created_at ON equipment_reservation(created_at)")
    print("   ✓ Índices criados com sucesso!")
    
    # Criar tabela equipment_loan
    print("\n5. Criando tabela 'equipment_loan'...")
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS equipment_loan (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            equipment_id INTEGER NOT NULL,
            user_id INTEGER NOT NULL,
            loan_date DATETIME NOT NULL,
            expected_return_date DATETIME NOT NULL,
            actual_return_date DATETIME,
            status VARCHAR(20) NOT NULL DEFAULT 'ativo',
            condition_at_loan VARCHAR(20),
            condition_at_return VARCHAR(20),
            received_by_id INTEGER,
            return_notes TEXT,
            reservation_id INTEGER,
            sla_status VARCHAR(20) DEFAULT 'normal',
            sla_deadline DATETIME,
            return_reminder_sent BOOLEAN DEFAULT 0,
            created_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (equipment_id) REFERENCES equipment(id),
            FOREIGN KEY (user_id) REFERENCES user(id),
            FOREIGN KEY (received_by_id) REFERENCES user(id),
            FOREIGN KEY (reservation_id) REFERENCES equipment_reservation(id)
        )
    """)
    print("   ✓ Tabela 'equipment_loan' criada com sucesso!")
    
    # Criar índices para equipment_loan
    print("\n6. Criando índices para 'equipment_loan'...")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_equipment_loan_status ON equipment_loan(status)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_equipment_loan_user_id ON equipment_loan(user_id)")
    cursor.execute("CREATE INDEX IF NOT EXISTS ix_equipment_loan_equipment_id ON equipment_loan(equipment_id)")
    print("   ✓ Índices criados com sucesso!")
    
    # Commit das alterações
    conn.commit()
    
    print("\n" + "=" * 80)
    print("✅ MIGRAÇÃO APLICADA COM SUCESSO!")
    print("=" * 80)
    
    # Verificar tabelas criadas
    print("\n📋 Verificando tabelas criadas:")
    cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name LIKE 'equipment%' ORDER BY name")
    tables = cursor.fetchall()
    for table in tables:
        cursor.execute(f"SELECT COUNT(*) FROM {table[0]}")
        count = cursor.fetchone()[0]
        print(f"   ✓ {table[0]} (registros: {count})")
    
except Exception as e:
    conn.rollback()
    print(f"\n❌ ERRO ao aplicar migração: {str(e)}")
    import traceback
    traceback.print_exc()
finally:
    conn.close()

print("\n" + "=" * 80)
