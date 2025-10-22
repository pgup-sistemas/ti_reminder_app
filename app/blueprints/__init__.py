# Arquivo __init__.py para tornar routes um pacote Python
# Importar o blueprint do módulo routes.py no diretório pai (app/routes.py)

# Usar importação absoluta para evitar conflito de nomes
from app import routes as routes_module

# Exportar o blueprint
bp = routes_module.bp