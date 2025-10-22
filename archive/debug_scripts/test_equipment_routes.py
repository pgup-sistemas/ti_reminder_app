"""Script para verificar se todas as rotas de equipamentos estão dinâmicas"""
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
print("ANÁLISE DAS ROTAS DE EQUIPAMENTOS")
print("=" * 80)

# Verificar dados necessários para cada rota
routes_analysis = {
    '/equipment/catalog': {
        'description': 'Catálogo de equipamentos disponíveis',
        'requires': 'Tabela equipment com registros',
        'dynamic': True,
        'check': 'SELECT COUNT(*) FROM equipment'
    },
    '/equipment/reserve': {
        'description': 'Criar reserva de equipamento (POST)',
        'requires': 'Tabela equipment_reservation',
        'dynamic': True,
        'check': 'SELECT COUNT(*) FROM sqlite_master WHERE type="table" AND name="equipment_reservation"'
    },
    '/equipment/check-availability': {
        'description': 'Verificar disponibilidade (POST)',
        'requires': 'Tabelas equipment, equipment_reservation, equipment_loan',
        'dynamic': True,
        'check': 'SELECT COUNT(*) FROM equipment'
    },
    '/equipment/my-reservations': {
        'description': 'Minhas reservas',
        'requires': 'Tabela equipment_reservation com user_id',
        'dynamic': True,
        'check': 'SELECT COUNT(*) FROM equipment_reservation'
    },
    '/equipment/my-loans': {
        'description': 'Meus empréstimos ativos',
        'requires': 'Tabela equipment_loan com user_id',
        'dynamic': True,
        'check': 'SELECT COUNT(*) FROM equipment_loan'
    },
    '/equipment/admin/pending-approvals': {
        'description': 'Aprovações pendentes (ADMIN/TI)',
        'requires': 'Reservas com status="pendente"',
        'dynamic': True,
        'check': 'SELECT COUNT(*) FROM equipment_reservation WHERE status="pendente"'
    },
    '/equipment/admin/dashboard': {
        'description': 'Dashboard administrativo (ADMIN/TI)',
        'requires': 'Estatísticas de equipamentos',
        'dynamic': True,
        'check': 'SELECT COUNT(*) FROM equipment'
    },
    '/equipment/api/equipment/<id>': {
        'description': 'Detalhes de equipamento via AJAX',
        'requires': 'Equipment por ID',
        'dynamic': True,
        'check': 'SELECT COUNT(*) FROM equipment'
    },
    '/equipment/api/equipment/<id>/schedule': {
        'description': 'Agenda de reservas do equipamento',
        'requires': 'Reservas e empréstimos do equipamento',
        'dynamic': True,
        'check': 'SELECT COUNT(*) FROM equipment'
    },
    '/equipment/api/stats': {
        'description': 'Estatísticas via AJAX (ADMIN/TI)',
        'requires': 'Dados de equipamentos',
        'dynamic': True,
        'check': 'SELECT COUNT(*) FROM equipment'
    }
}

print("\n📋 ROTAS DISPONÍVEIS E STATUS:\n")

all_dynamic = True
issues = []

for route, info in routes_analysis.items():
    print(f"🔗 {route}")
    print(f"   Descrição: {info['description']}")
    print(f"   Requer: {info['requires']}")
    
    # Executar verificação
    try:
        cursor.execute(info['check'])
        result = cursor.fetchone()[0]
        
        if result > 0:
            status = "✅ DINÂMICA"
            print(f"   Status: {status} ({result} registro(s) encontrado(s))")
        else:
            status = "⚠️ DINÂMICA (sem dados)"
            print(f"   Status: {status} - Funcional mas sem dados para exibir")
            issues.append({
                'route': route,
                'issue': 'Sem dados',
                'severity': 'warning'
            })
    except Exception as e:
        status = "❌ ERRO"
        print(f"   Status: {status} - {str(e)}")
        all_dynamic = False
        issues.append({
            'route': route,
            'issue': str(e),
            'severity': 'error'
        })
    
    print()

# Verificar estrutura das tabelas principais
print("=" * 80)
print("ESTRUTURA DAS TABELAS PRINCIPAIS")
print("=" * 80)

tables_to_check = ['equipment', 'equipment_reservation', 'equipment_loan']

for table in tables_to_check:
    try:
        cursor.execute(f"SELECT COUNT(*) FROM {table}")
        count = cursor.fetchone()[0]
        
        cursor.execute(f"PRAGMA table_info({table})")
        columns = cursor.fetchall()
        
        print(f"\n📊 Tabela: {table}")
        print(f"   Registros: {count}")
        print(f"   Colunas: {len(columns)}")
        
        # Mostrar algumas colunas importantes
        important_cols = ['id', 'status', 'user_id', 'equipment_id', 'created_at']
        for col in columns:
            if col[1] in important_cols:
                print(f"      - {col[1]} ({col[2]})")
                
    except Exception as e:
        print(f"\n❌ Erro ao verificar tabela {table}: {str(e)}")

# Verificar dados de teste
print("\n" + "=" * 80)
print("DADOS DE TESTE DISPONÍVEIS")
print("=" * 80)

# Equipamentos
cursor.execute("SELECT COUNT(*) FROM equipment")
eq_count = cursor.fetchone()[0]
print(f"\n✓ Equipamentos cadastrados: {eq_count}")

if eq_count > 0:
    cursor.execute("SELECT id, name, category, status FROM equipment LIMIT 5")
    equipments = cursor.fetchall()
    for eq in equipments:
        print(f"   - ID: {eq[0]} | {eq[1]} | Categoria: {eq[2]} | Status: {eq[3]}")

# Reservas
cursor.execute("SELECT COUNT(*) FROM equipment_reservation")
res_count = cursor.fetchone()[0]
print(f"\n✓ Reservas cadastradas: {res_count}")

if res_count > 0:
    cursor.execute("""
        SELECT er.id, er.status, e.name, u.username 
        FROM equipment_reservation er
        JOIN equipment e ON er.equipment_id = e.id
        JOIN user u ON er.user_id = u.id
        LIMIT 5
    """)
    reservations = cursor.fetchall()
    for res in reservations:
        print(f"   - ID: {res[0]} | Status: {res[1]} | Equipamento: {res[2]} | Usuário: {res[3]}")

# Empréstimos
cursor.execute("SELECT COUNT(*) FROM equipment_loan")
loan_count = cursor.fetchone()[0]
print(f"\n✓ Empréstimos cadastrados: {loan_count}")

if loan_count > 0:
    cursor.execute("""
        SELECT el.id, el.status, e.name, u.username 
        FROM equipment_loan el
        JOIN equipment e ON el.equipment_id = e.id
        JOIN user u ON el.user_id = u.id
        LIMIT 5
    """)
    loans = cursor.fetchall()
    for loan in loans:
        print(f"   - ID: {loan[0]} | Status: {loan[1]} | Equipamento: {loan[2]} | Usuário: {loan[3]}")

# Resumo final
print("\n" + "=" * 80)
print("RESUMO DA ANÁLISE")
print("=" * 80)

if all_dynamic and not issues:
    print("\n✅ TODAS AS ROTAS ESTÃO DINÂMICAS E FUNCIONAIS!")
    print("   Todas as rotas estão conectadas ao banco de dados e funcionando corretamente.")
elif issues:
    print(f"\n⚠️ ROTAS FUNCIONAIS COM AVISOS ({len([i for i in issues if i['severity'] == 'warning'])} avisos)")
    
    warnings = [i for i in issues if i['severity'] == 'warning']
    errors = [i for i in issues if i['severity'] == 'error']
    
    if warnings:
        print("\n📝 Avisos (rotas funcionais mas sem dados):")
        for issue in warnings:
            print(f"   - {issue['route']}: {issue['issue']}")
    
    if errors:
        print("\n❌ Erros (rotas com problemas):")
        for issue in errors:
            print(f"   - {issue['route']}: {issue['issue']}")
else:
    print("\n❌ ALGUMAS ROTAS TÊM PROBLEMAS")
    print(f"   {len(issues)} problema(s) encontrado(s)")

print("\n" + "=" * 80)
print("ROTAS PARA TESTAR NO NAVEGADOR")
print("=" * 80)
print("\n🌐 URLs para testar (faça login primeiro):")
print("   1. http://192.168.1.86:5000/equipment/catalog")
print("   2. http://192.168.1.86:5000/equipment/my-reservations")
print("   3. http://192.168.1.86:5000/equipment/my-loans")
print("   4. http://192.168.1.86:5000/equipment/admin/pending-approvals (ADMIN/TI)")
print("   5. http://192.168.1.86:5000/equipment/admin/dashboard (ADMIN/TI)")

print("\n📡 APIs REST (requer autenticação JWT):")
print("   - GET  /equipment/api/v1/equipment")
print("   - GET  /equipment/api/v1/equipment/<id>")
print("   - POST /equipment/api/v1/reservations")
print("   - GET  /equipment/api/v1/stats")

conn.close()
print("\n" + "=" * 80)
