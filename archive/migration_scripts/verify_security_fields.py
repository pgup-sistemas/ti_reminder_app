"""Script para verificar se os campos de segurança foram adicionados corretamente."""
from app import create_app, db
from app.models import User
from sqlalchemy import inspect

app = create_app()

with app.app_context():
    # Obter informações das colunas da tabela User
    inspector = inspect(db.engine)
    columns = inspector.get_columns('user')
    
    print("=" * 60)
    print("VERIFICAÇÃO DOS CAMPOS DE SEGURANÇA NA TABELA USER")
    print("=" * 60)
    
    security_fields = [
        'login_attempts',
        'locked_until',
        'password_changed_at',
        'last_failed_login',
        'last_password_reset'
    ]
    
    existing_columns = [col['name'] for col in columns]
    
    print("\n✅ Campos de segurança esperados:")
    for field in security_fields:
        if field in existing_columns:
            print(f"   ✅ {field} - PRESENTE")
        else:
            print(f"   ❌ {field} - AUSENTE")
    
    print("\n📋 Todas as colunas da tabela User:")
    for col in columns:
        col_type = str(col['type'])
        nullable = "NULL" if col['nullable'] else "NOT NULL"
        default = f" DEFAULT {col['default']}" if col['default'] else ""
        print(f"   - {col['name']:<30} {col_type:<20} {nullable}{default}")
    
    print("\n" + "=" * 60)
    print(f"Total de campos: {len(existing_columns)}")
    print("=" * 60)
