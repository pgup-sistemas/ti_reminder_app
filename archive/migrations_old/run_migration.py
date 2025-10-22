from app import create_app, db
from flask_migrate import upgrade, migrate, init, stamp
import os

# Criar a aplicação
app = create_app()

# Configurar o contexto da aplicação
app.app_context().push()

# Executar a migração
print("Criando migração...")
os.system('flask db migrate -m "add_time_fields_to_equipment_loan"')

print("Migração criada com sucesso!")
print("Agora execute 'flask db upgrade' para aplicar as alterações ao banco de dados.")
