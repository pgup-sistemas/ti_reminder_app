"""Criar arquivo .env com encoding correto"""

env_content = """SECRET_KEY=77d82e700d2843690f21106a739f9cdd8b25ce1c5d25639d49b462101e397ef1
JWT_SECRET_KEY=4daa8403ea9ff37356e49d793d0c7e9e3f1150c8beb49cff5dda9447697b6d25
FLASK_ENV=development
DEBUG=True
"""

with open('.env', 'w', encoding='utf-8') as f:
    f.write(env_content)

print("✓ Arquivo .env criado com sucesso!")
