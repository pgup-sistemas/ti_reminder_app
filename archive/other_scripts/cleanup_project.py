#!/usr/bin/env python
"""
Script de Limpeza Automatizada do Projeto TI Reminder App
Executa a reorganização de acordo com CLEANUP_PLAN.md
"""
import os
import shutil
from pathlib import Path
from datetime import datetime


class ProjectCleaner:
    """Gerenciador de limpeza do projeto"""
    
    def __init__(self, base_path=None):
        self.base_path = Path(base_path) if base_path else Path(__file__).parent
        self.archive_path = self.base_path / 'archive'
        self.stats = {
            'scripts_moved': 0,
            'docs_moved': 0,
            'total_moved': 0
        }
    
    def create_archive_structure(self):
        """Cria estrutura de pastas de arquivo"""
        print("\n📁 Criando estrutura de arquivo...")
        
        folders = [
            'migrations_old',
            'debug_scripts',
            'refactoring_scripts',
            'docs_temp',
            'other_scripts'
        ]
        
        for folder in folders:
            path = self.archive_path / folder
            path.mkdir(parents=True, exist_ok=True)
            print(f"  ✓ {path}")
        
        # Criar README explicativo
        self._create_archive_readme()
    
    def _create_archive_readme(self):
        """Cria README.md explicativo no archive"""
        content = f"""# Archive - TI Reminder App

Esta pasta contém scripts e documentos que foram utilizados durante o desenvolvimento
mas não são mais necessários para a operação do sistema.

**Data de arquivamento:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Estrutura

### migrations_old/
Scripts de migração de banco de dados já executados. Mantidos para referência histórica.

### debug_scripts/
Scripts temporários de debug e verificação utilizados durante o desenvolvimento.

### refactoring_scripts/
Scripts de refatoração que já foram executados (conversão de flash(), alert(), etc).

### docs_temp/
Documentação temporária de desenvolvimento: análises, relatórios de bugs corrigidos,
guias de implementação de features já concluídas.

### other_scripts/
Outros scripts obsoletos ou que foram consolidados em ferramentas principais.

## Política de Retenção

Estes arquivos serão mantidos por 6 meses para referência. Após este período,
podem ser removidos permanentemente se não forem mais necessários.

## Restauração

Se precisar restaurar algum arquivo, simplesmente copie de volta para a pasta
original do projeto. Tome cuidado para não sobrescrever mudanças mais recentes.

---

**Importante:** Não modifique arquivos nesta pasta. Ela serve apenas como backup histórico.
"""
        
        readme_path = self.archive_path / 'README.md'
        readme_path.write_text(content, encoding='utf-8')
        print(f"  ✓ {readme_path}")
    
    def move_file(self, filename, destination_folder):
        """Move arquivo para pasta de arquivo"""
        source = self.base_path / filename
        
        if not source.exists():
            return False
        
        dest_path = self.archive_path / destination_folder
        destination = dest_path / filename
        
        # Se já existe, adicionar timestamp
        if destination.exists():
            timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
            name_parts = filename.rsplit('.', 1)
            if len(name_parts) == 2:
                new_name = f"{name_parts[0]}_{timestamp}.{name_parts[1]}"
            else:
                new_name = f"{filename}_{timestamp}"
            destination = dest_path / new_name
        
        shutil.move(str(source), str(destination))
        self.stats['total_moved'] += 1
        return True
    
    def cleanup_migration_scripts(self):
        """Move scripts de migração obsoletos"""
        print("\n🔄 Movendo scripts de migração obsoletos...")
        
        migration_scripts = [
            'add_columns.py',
            'add_satisfaction_fields.py',
            'apply_equipment_migration.py',
            'apply_migration.py',
            'direct_migration.py',
            'fix_certification_columns.py',
            'fix_reservation_datetime.py',
            'run_migration.py',
            'run_migration_manual.py',
        ]
        
        count = 0
        for script in migration_scripts:
            if self.move_file(script, 'migrations_old'):
                print(f"  ✓ {script}")
                count += 1
        
        self.stats['scripts_moved'] += count
        print(f"\n  Total: {count} scripts movidos")
    
    def cleanup_debug_scripts(self):
        """Move scripts de debug/teste temporários"""
        print("\n🐛 Movendo scripts de debug temporários...")
        
        debug_scripts = [
            'check_db_direct.py',
            'check_loans.py',
            'check_migration.py',
            'check_reservations.py',
            'check_tables.py',
            'check_user_table.py',
            'test_db_connection.py',
            'test_equipment_routes.py',
            'test_notification.py',
        ]
        
        count = 0
        for script in debug_scripts:
            if self.move_file(script, 'debug_scripts'):
                print(f"  ✓ {script}")
                count += 1
        
        self.stats['scripts_moved'] += count
        print(f"\n  Total: {count} scripts movidos")
    
    def cleanup_refactoring_scripts(self):
        """Move scripts de refatoração já executados"""
        print("\n🔧 Movendo scripts de refatoração executados...")
        
        # Scripts da pasta scripts/
        scripts_folder = self.base_path / 'scripts'
        refactoring_scripts = [
            'final_flash_cleanup.py',
            'update_flash_calls.py',
            'update_flash_advanced.py',
            'update_alert_calls.py',
            'validate_refactoring.py',
        ]
        
        count = 0
        for script in refactoring_scripts:
            source = scripts_folder / script
            if source.exists():
                dest = self.archive_path / 'refactoring_scripts' / script
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(dest))
                print(f"  ✓ scripts/{script}")
                count += 1
        
        self.stats['scripts_moved'] += count
        print(f"\n  Total: {count} scripts movidos")
    
    def cleanup_other_scripts(self):
        """Move outros scripts obsoletos"""
        print("\n📦 Movendo outros scripts obsoletos...")
        
        other_scripts = [
            'optimize_performance.py',
            'config_production.py',
            'system_config_model.py',
        ]
        
        count = 0
        for script in other_scripts:
            if self.move_file(script, 'other_scripts'):
                print(f"  ✓ {script}")
                count += 1
        
        # Scripts da pasta scripts/
        scripts_folder = self.base_path / 'scripts'
        scripts_to_move = [
            'code_splitting.py',
            'minify_assets.py',
            'optimize_images.py',
            'cleanup_legacy.py',
        ]
        
        for script in scripts_to_move:
            source = scripts_folder / script
            if source.exists():
                dest = self.archive_path / 'other_scripts' / script
                dest.parent.mkdir(parents=True, exist_ok=True)
                shutil.move(str(source), str(dest))
                print(f"  ✓ scripts/{script}")
                count += 1
        
        self.stats['scripts_moved'] += count
        print(f"\n  Total: {count} scripts movidos")
    
    def cleanup_temp_documentation(self):
        """Move documentação temporária"""
        print("\n📄 Movendo documentação temporária...")
        
        temp_docs = [
            'ANALISE_SISTEMA_NOTIFICACOES.md',
            'CALENDAR_FIX_REPORT.md',
            'COMO_FUNCIONA_SOLICITACAO_NOTIFICACOES.md',
            'CORRECOES_FINAIS.md',
            'DASHBOARD_ANALYSIS.md',
            'DASHBOARD_UNIFORMIZATION_COMPLETE.md',
            'DEBUG_RESERVATIONS.md',
            'DIFERENCA_NOTIFICACOES.md',
            'EQUIPMENT_AUDIT_REPORT.md',
            'EQUIPMENT_FIX_DATABASE.md',
            'EQUIPMENT_IMPROVEMENTS.md',
            'EQUIPMENT_PENDING_APPROVALS_FIX.md',
            'EQUIPMENT_RESERVATIONS_FIXED.md',
            'EQUIPMENT_ROUTES_STATUS.md',
            'EQUIPMENT_SCHEDULE_FEATURE.md',
            'EXPORTACAO_PDF_CHAMADOS.md',
            'FRONTEND_AJUSTADO.md',
            'INSTRUCOES_TESTE_DEBUG.md',
            'LIMPAR_CACHE.md',
            'MENU_REORGANIZATION_ANALYSIS.md',
            'MENU_UPDATE_DOCUMENTATION.md',
            'MIGRATION_OLD_TO_NEW_CALENDAR.md',
            'MIGRATION_SUMMARY.md',
            'PLANO_ACAO_NOTIFICACOES.md',
            'REFACTORED_RESERVATION_CALENDAR.md',
            'REFACTORING_COMPLETE_REPORT.md',
            'REFACTORING_SUMMARY.txt',
            'RELATORIO_SISTEMA_ANTIGO.md',
            'SISTEMA_EQUIPAMENTOS_V2_LIMPO.md',
            'SISTEMA_FUNCIONANDO.md',
            'SISTEMA_NOTIFICACOES_IMPLEMENTADO.md',
            'SISTEMA_V2_ATIVADO.md',
            'SISTEMA_V2_PRONTO.md',
            'SOLUCAO_FINAL_CALENDARIO.md',
            'TESTE_CALENDARIO.md',
        ]
        
        count = 0
        for doc in temp_docs:
            if self.move_file(doc, 'docs_temp'):
                print(f"  ✓ {doc}")
                count += 1
        
        self.stats['docs_moved'] += count
        print(f"\n  Total: {count} documentos movidos")
    
    def reorganize_useful_scripts(self):
        """Reorganiza scripts úteis"""
        print("\n♻️  Reorganizando scripts úteis...")
        
        # Mover create_test_data.py para scripts/
        source = self.base_path / 'create_test_data.py'
        if source.exists():
            dest = self.base_path / 'scripts' / 'create_test_data.py'
            shutil.move(str(source), str(dest))
            print(f"  ✓ create_test_data.py → scripts/")
    
    def cleanup_temp_files(self):
        """Remove arquivos temporários"""
        print("\n🗑️  Removendo arquivos temporários...")
        
        temp_files = [
            'db_initialized.flag',
            'pg_version.txt',
            '.coverage',
        ]
        
        count = 0
        for filename in temp_files:
            filepath = self.base_path / filename
            if filepath.exists():
                filepath.unlink()
                print(f"  ✓ Removido: {filename}")
                count += 1
        
        if count > 0:
            print(f"\n  Total: {count} arquivos temporários removidos")
        else:
            print("  Nenhum arquivo temporário encontrado")
    
    def print_statistics(self):
        """Imprime estatísticas da limpeza"""
        print("\n" + "="*60)
        print("📊 ESTATÍSTICAS DA LIMPEZA")
        print("="*60)
        print(f"\nScripts Python movidos: {self.stats['scripts_moved']}")
        print(f"Documentos movidos: {self.stats['docs_moved']}")
        print(f"Total de arquivos movidos: {self.stats['total_moved']}")
        print(f"\nTodos os arquivos foram preservados em: {self.archive_path}")
        print("\n" + "="*60)
    
    def run(self):
        """Executa o processo completo de limpeza"""
        print("="*60)
        print("🧹 LIMPEZA AUTOMATIZADA DO PROJETO")
        print("="*60)
        print(f"\nDiretório: {self.base_path}")
        print(f"Arquivo: {self.archive_path}")
        
        # Confirmação
        print("\n⚠️  ATENÇÃO: Esta operação irá mover vários arquivos.")
        print("Todos os arquivos serão preservados na pasta 'archive/'")
        response = input("\nDeseja continuar? (s/N): ")
        
        if response.lower() != 's':
            print("\n❌ Operação cancelada pelo usuário.")
            return
        
        # Executar limpeza
        self.create_archive_structure()
        self.cleanup_migration_scripts()
        self.cleanup_debug_scripts()
        self.cleanup_refactoring_scripts()
        self.cleanup_other_scripts()
        self.cleanup_temp_documentation()
        self.reorganize_useful_scripts()
        self.cleanup_temp_files()
        
        # Estatísticas
        self.print_statistics()
        
        print("\n✅ LIMPEZA CONCLUÍDA COM SUCESSO!")
        print("\n📋 Próximos passos:")
        print("1. Revisar as mudanças")
        print("2. Executar testes: python scripts/run_tests.py")
        print("3. Fazer commit: git add . && git commit -m 'chore: Limpeza de scripts obsoletos'")
        print("4. Revisar pasta archive/ em 6 meses")


def main():
    """Função principal"""
    cleaner = ProjectCleaner()
    cleaner.run()


if __name__ == '__main__':
    main()
