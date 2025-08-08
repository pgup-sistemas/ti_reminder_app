import re

# Ler o arquivo
with open('app/routes.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Substituir as ocorrências problemáticas
content = re.sub(
    r'if form\.imagem\.data:\s*\n\s*if file:',
    'if form.imagem.data:\n            file = form.imagem.data\n            if file:',
    content
)

# Escrever o arquivo corrigido
with open('app/routes.py', 'w', encoding='utf-8') as f:
    f.write(content)

print("Arquivo routes.py corrigido com sucesso!")
