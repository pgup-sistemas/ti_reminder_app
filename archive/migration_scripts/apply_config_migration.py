"""
Script para aplicar migration de SystemConfig e executar seeds
Execute: python apply_config_migration.py
"""

import sys
import os

# Adicionar o diretório raiz ao path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app, db
from app.services.system_config_service import SystemConfigService
from flask_migrate import upgrade

def main():
    """Aplica migration e executa seeds"""
    app = create_app()
    
    with app.app_context():
        print("=" * 60)
        print("APLICANDO MIGRATION DE SYSTEMCONFIG")
        print("=" * 60)
        
        try:
            # Aplicar migration
            print("\n1. Aplicando migration ao banco de dados...")
            upgrade()
            print("✅ Migration aplicada com sucesso!")
            
            # Executar seeds
            print("\n2. Executando seeds de configurações padrão...")
            SystemConfigService.seed_default_configs()
            print("✅ Seeds executados com sucesso!")
            
            # Verificar quantas configs foram criadas
            from app.models import SystemConfig
            count = SystemConfig.query.count()
            print(f"\n✅ Total de configurações no banco: {count}")
            
            # Listar algumas configurações
            print("\n📋 Algumas configurações criadas:")
            configs = SystemConfig.query.limit(5).all()
            for config in configs:
                print(f"  - {config.category}.{config.key} = {config.value}")
            
            print("\n" + "=" * 60)
            print("✅ MIGRATION E SEEDS APLICADOS COM SUCESSO!")
            print("=" * 60)
            print("\nO sistema agora está pronto para usar configurações persistentes.")
            print("Reinicie o servidor para aplicar as mudanças.")
            
        except Exception as e:
            print(f"\n❌ ERRO: {e}")
            import traceback
            traceback.print_exc()
            return 1
    
    return 0

if __name__ == "__main__":
    exit(main())
