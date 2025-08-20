import os
from flask import Flask
from app import db
from app.models import User, Sector, Reminder, Task, Chamado
from dotenv import load_dotenv

def create_app_for_script():
    """Cria a aplicação Flask para o script"""
    app = Flask(__name__)
    app.config.from_object('config.Config')
    db.init_app(app)
    return app

# Carregar variáveis de ambiente
load_dotenv()

# Verificar se estamos usando PostgreSQL
database_url = os.environ.get('DATABASE_URL')
if database_url and database_url.startswith('postgresql'):
    print(f"Usando banco de dados PostgreSQL: {database_url}")
else:
    print(f"AVISO: Não está usando PostgreSQL ou DATABASE_URL não está definido: {database_url}")

# Criar aplicação e contexto
app = create_app_for_script()

# Criar contexto da aplicação
with app.app_context():
    print("Iniciando criação/atualização das tabelas no SQLAlchemy...")
    
    # Criar todas as tabelas definidas nos modelos
    db.create_all()
    print("Tabelas criadas/atualizadas com sucesso!")
    
    # Verificar se as tabelas foram criadas
    inspector = db.inspect(db.engine)
    tables = inspector.get_table_names()
    print(f"Tabelas existentes no banco de dados: {tables}")
    
    # Verificar se as tabelas específicas existem
    required_tables = ['user', 'sector', 'reminder', 'task', 'chamado']
    for table in required_tables:
        if table in tables:
            print(f"Tabela '{table}' existe.")
        else:
            print(f"ERRO: Tabela '{table}' NÃO existe!")
    
    # Verificar se há dados nas tabelas
    try:
        user_count = User.query.count()
        print(f"Número de usuários: {user_count}")
    except Exception as e:
        print(f"Erro ao consultar usuários: {e}")
    
    try:
        sector_count = Sector.query.count()
        print(f"Número de setores: {sector_count}")
    except Exception as e:
        print(f"Erro ao consultar setores: {e}")
    
    try:
        reminder_count = Reminder.query.count()
        print(f"Número de lembretes: {reminder_count}")
    except Exception as e:
        print(f"Erro ao consultar lembretes: {e}")
    
    try:
        task_count = Task.query.count()
        print(f"Número de tarefas: {task_count}")
    except Exception as e:
        print(f"Erro ao consultar tarefas: {e}")
    
    try:
        chamado_count = Chamado.query.count()
        print(f"Número de chamados: {chamado_count}")
    except Exception as e:
        print(f"Erro ao consultar chamados: {e}")