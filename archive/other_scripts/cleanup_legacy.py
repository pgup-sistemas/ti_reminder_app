#!/usr/bin/env python
"""
Script para mover arquivos legados/obsoletos para uma pasta de backup.
Mantém o histórico mas limpa a raiz do projeto.
"""
import os
import shutil
from pathlib import Path
from datetime import datetime


# Arquivos a serem movidos para legacy
LEGACY_FILES = [
    'apply_migration.py',
    'check_migration.py', 
    'add_satisfaction_fields.py',
    'test_db_connection.py',
    'test_notification.py',
    'config_production.py',
    'system_config_model.py',
]

# Diretório de destino
LEGACY_DIR = Path('legacy')


def create_legacy_readme():
    """Cria README explicando os arquivos legados."""
    readme_content = """# Arquivos Legados

Este diretório contém scripts e arquivos que foram refatorados ou substituídos.
Mantidos para referência histórica.

## Arquivos Movidos

### Scripts de Banco de Dados (Substituídos por `scripts/db_manager.py`)
- **apply_migration.py** - Aplicava migrations manualmente (use: `python scripts/db_manager.py migrate`)
- **check_migration.py** - Verificava status de migrations (use: `python scripts/db_manager.py status`)
- **add_satisfaction_fields.py** - Adicionava campos via SQL direto (use migrations do Flask-Migrate)
- **test_db_connection.py** - Testava conexão (use: `python scripts/db_manager.py test`)

### Scripts de Teste (Movidos para `/tests`)
- **test_notification.py** - Teste básico de notificações

### Configurações (Consolidadas em `config.py`)
- **config_production.py** - Configurações duplicadas (agora em `config.py` com classes)

### Documentação Conceitual
- **system_config_model.py** - Modelo conceitual (358 linhas de documentação)

## Novos Comandos

### Gerenciamento de Banco de Dados
```bash
# Testar conexão
python scripts/db_manager.py test

# Inicializar banco
python scripts/db_manager.py init

# Aplicar migrations
python scripts/db_manager.py migrate

# Ver status
python scripts/db_manager.py status

# Inspecionar tabela
python scripts/db_manager.py inspect user

# Backup
python scripts/db_manager.py backup
```

### Configurações
```python
# Antes (múltiplos arquivos)
from config import Config
from config_production import ProductionConfig

# Agora (um arquivo, múltiplas classes)
from config import DevelopmentConfig, ProductionConfig, TestingConfig, get_config
```

### Utilitários de Banco
```python
# Antes (conexões diretas espalhadas)
import psycopg2
conn = psycopg2.connect(...)

# Agora (centralizado)
from app.utils.db_utils import DatabaseManager

# Context manager para conexões
with DatabaseManager.get_raw_connection() as (conn, cursor):
    cursor.execute("SELECT * FROM user")
    
# Helpers úteis
DatabaseManager.test_connection()
DatabaseManager.table_exists('user')
DatabaseManager.column_exists('user', 'email')
```

## Data de Migração
{}
""".format(datetime.now().strftime('%Y-%m-%d %H:%M:%S'))
    
    return readme_content


def move_to_legacy():
    """Move arquivos legados para pasta legacy."""
    
    # Criar diretório legacy se não existir
    LEGACY_DIR.mkdir(exist_ok=True)
    
    print("🧹 Limpando arquivos legados...\n")
    
    moved_count = 0
    not_found = []
    
    for filename in LEGACY_FILES:
        source = Path(filename)
        
        if source.exists():
            destination = LEGACY_DIR / filename
            
            # Se já existe no destino, adicionar timestamp
            if destination.exists():
                timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
                name_parts = filename.rsplit('.', 1)
                if len(name_parts) == 2:
                    new_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
                else:
                    new_name = f"{filename}_{timestamp}"
                destination = LEGACY_DIR / new_name
            
            shutil.move(str(source), str(destination))
            print(f"✓ Movido: {filename} → legacy/{destination.name}")
            moved_count += 1
        else:
            not_found.append(filename)
    
    # Criar README
    readme_path = LEGACY_DIR / 'README.md'
    readme_path.write_text(create_legacy_readme(), encoding='utf-8')
    print(f"\n✓ Criado: legacy/README.md")
    
    # Resumo
    print(f"\n{'='*60}")
    print(f"Arquivos movidos: {moved_count}")
    
    if not_found:
        print(f"Não encontrados: {len(not_found)}")
        for f in not_found:
            print(f"  - {f}")
    
    print(f"\n✨ Limpeza concluída!")
    print(f"📁 Arquivos legados em: {LEGACY_DIR.absolute()}")


def restore_file(filename):
    """Restaura um arquivo da pasta legacy."""
    source = LEGACY_DIR / filename
    destination = Path(filename)
    
    if not source.exists():
        print(f"✗ Arquivo não encontrado em legacy: {filename}")
        return False
    
    if destination.exists():
        print(f"⚠️  Arquivo já existe na raiz: {filename}")
        response = input("Sobrescrever? (s/N): ")
        if response.lower() != 's':
            print("Operação cancelada")
            return False
    
    shutil.copy(str(source), str(destination))
    print(f"✓ Restaurado: {filename}")
    return True


if __name__ == '__main__':
    import sys
    
    if len(sys.argv) > 1 and sys.argv[1] == 'restore':
        if len(sys.argv) < 3:
            print("Uso: python scripts/cleanup_legacy.py restore <filename>")
            sys.exit(1)
        restore_file(sys.argv[2])
    else:
        # Confirmação antes de mover
        print("Este script irá mover os seguintes arquivos para a pasta 'legacy':")
        for f in LEGACY_FILES:
            status = "✓" if Path(f).exists() else "✗"
            print(f"  {status} {f}")
        
        print("\nArquivos serão preservados em 'legacy/' para referência.")
        response = input("\nContinuar? (s/N): ")
        
        if response.lower() == 's':
            move_to_legacy()
        else:
            print("Operação cancelada")
