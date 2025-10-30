"""Script para corrigir MAIL_USE_TLS no arquivo .env"""
import os

env_file = '.env'

print("=" * 60)
print("CORRIGINDO MAIL_USE_TLS NO ARQUIVO .env")
print("=" * 60)

if not os.path.exists(env_file):
    print(f"\n❌ Arquivo {env_file} não encontrado!")
    exit(1)

# Ler conteúdo
with open(env_file, 'r', encoding='utf-8') as f:
    lines = f.readlines()

# Corrigir linhas
updated = False
new_lines = []
for line in lines:
    if line.strip().startswith('MAIL_USE_TLS='):
        old_value = line.strip()
        if 'MAIL_USE_TLS=1' in line or 'MAIL_USE_TLS=0' in line:
            new_line = 'MAIL_USE_TLS=True\n'
            new_lines.append(new_line)
            print(f"\n✏️  Corrigindo:")
            print(f"  ANTES: {old_value}")
            print(f"  DEPOIS: {new_line.strip()}")
            updated = True
        else:
            new_lines.append(line)
    else:
        new_lines.append(line)

if updated:
    # Salvar arquivo
    with open(env_file, 'w', encoding='utf-8') as f:
        f.writelines(new_lines)
    
    print("\n✅ Arquivo .env corrigido com sucesso!")
    print("\n⚠️  IMPORTANTE: Reinicie o servidor Flask para aplicar as mudanças")
else:
    print("\n✓ MAIL_USE_TLS já está configurado corretamente")

print("\n" + "=" * 60)
