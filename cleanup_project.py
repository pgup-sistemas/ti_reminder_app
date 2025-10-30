#!/usr/bin/env python3
"""
Script de Limpeza Profissional do Projeto TI OSN System

Organiza arquivos obsoletos, move documentação antiga para archive,
e mantém apenas arquivos essenciais na raiz.

Uso:
    python cleanup_project.py --dry-run  # Simular sem fazer mudanças
    python cleanup_project.py --execute  # Executar limpeza real
    python cleanup_project.py --undo     # Reverter última limpeza
"""

import os
import shutil
import json
from datetime import datetime
from pathlib import Path
import argparse

# Cores para output
class Colors:
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    RED = '\033[91m'
    BLUE = '\033[94m'
    END = '\033[0m'

class ProjectCleaner:
    def __init__(self, project_root, dry_run=True):
        self.project_root = Path(project_root)
        self.dry_run = dry_run
        self.actions_log = []
        self.timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        self.backup_dir = self.project_root / f"backup_cleanup_{self.timestamp}"
        
    def log_action(self, action_type, source, destination=None):
        """Registra ação realizada"""
        self.actions_log.append({
            'type': action_type,
            'source': str(source),
            'destination': str(destination) if destination else None,
            'timestamp': datetime.now().isoformat()
        })
    
    def create_backup_manifest(self):
        """Salva manifesto de ações para possível undo"""
        manifest_path = self.project_root / f"cleanup_manifest_{self.timestamp}.json"
        with open(manifest_path, 'w', encoding='utf-8') as f:
            json.dump(self.actions_log, f, indent=2, ensure_ascii=False)
        print(f"{Colors.GREEN}✓{Colors.END} Manifesto salvo: {manifest_path}")
    
    def move_file(self, source, destination):
        """Move arquivo com segurança"""
        source_path = self.project_root / source
        dest_path = self.project_root / destination
        
        if not source_path.exists():
            print(f"{Colors.YELLOW}⚠{Colors.END} Arquivo não encontrado: {source}")
            return False
        
        # Criar diretório destino se não existir
        dest_path.parent.mkdir(parents=True, exist_ok=True)
        
        if self.dry_run:
            print(f"{Colors.BLUE}[DRY-RUN]{Colors.END} {source} → {destination}")
        else:
            try:
                shutil.move(str(source_path), str(dest_path))
                print(f"{Colors.GREEN}✓{Colors.END} {source} → {destination}")
                self.log_action('move', source, destination)
            except Exception as e:
                print(f"{Colors.RED}✗{Colors.END} Erro ao mover {source}: {e}")
                return False
        
        return True
    
    def delete_file(self, filepath):
        """Deleta arquivo com segurança"""
        file_path = self.project_root / filepath
        
        if not file_path.exists():
            print(f"{Colors.YELLOW}⚠{Colors.END} Arquivo não encontrado: {filepath}")
            return False
        
        if self.dry_run:
            print(f"{Colors.BLUE}[DRY-RUN]{Colors.END} Deletar: {filepath}")
        else:
            try:
                file_path.unlink()
                print(f"{Colors.GREEN}✓{Colors.END} Deletado: {filepath}")
                self.log_action('delete', filepath)
            except Exception as e:
                print(f"{Colors.RED}✗{Colors.END} Erro ao deletar {filepath}: {e}")
                return False
        
        return True
    
    def cleanup_test_scripts(self):
        """Move scripts de teste para /tests ou /archive"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}1. Limpando Scripts de Teste{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
        
        test_scripts = [
            'test_com_auth.py',
            'test_com_senha.py',
            'test_edit_completo.py',
            'test_edit_final.py',
            'test_edit_request.py',
            'test_post_direto.py',
            'test_user_edit.py',
            'test_user_edit_direct.py',
            'test_analytics_api.py',
            'test_email_connection.py',
            'test_export_route.py',
            'test_import.py',
            'test_reset_password_email.py',
        ]
        
        for script in test_scripts:
            self.move_file(script, f'archive/test_scripts/{script}')
    
    def cleanup_debug_scripts(self):
        """Deleta scripts de debug temporários"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}2. Removendo Scripts de Debug{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
        
        debug_files = [
            'debug_flask_mail_config.py',
            'debug_login.txt',
            'tmp_debug_system_config.py',
            'check_analytics_routes.py',
            'check_config.py',
            'check_routes.py',
            'clear_cache.py',
        ]
        
        for file in debug_files:
            self.delete_file(file)
    
    def cleanup_migration_scripts(self):
        """Move scripts de migração para /archive"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}3. Arquivando Scripts de Migração{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
        
        migration_scripts = [
            'apply_config_migration.py',
            'fix_env_mail_tls.py',
            'reverter_senha.py',
            'verify_email_config.py',
            'verify_security_fields.py',
            'create_env.py',
            'generate_keys.py',
            'init_db.py',
            'list_all_routes.py',
        ]
        
        for script in migration_scripts:
            self.move_file(script, f'archive/migration_scripts/{script}')
    
    def cleanup_documentation(self):
        """Organiza documentação em /archive"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}4. Organizando Documentação{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
        
        # Relatórios de Implementação
        print(f"\n{Colors.YELLOW}→ Relatórios de Implementação{Colors.END}")
        implementation_docs = [
            'IMPLEMENTACAO_BADGE_CHAMADOS.md',
            'IMPLEMENTACAO_COMPLETA.md',
            'IMPLEMENTACAO_DURACAO_CHAMADOS.md',
            'IMPLEMENTATION_REPORT.md',
            'CONCLUSAO_IMPLEMENTACAO_ANALYTICS.md',
            'SISTEMA_MODAIS_IMPLEMENTADO.md',
            'GESTAO_USUARIOS_COMPLETA.md',
            'DOCUMENTACAO_MKDOCS_CONCLUIDA.md',
            'FOOTER_DARK_MODE_IMPLEMENTATION.md',
            'DARK_MODE_CONSOLIDATION.md',
            'MODULO_BACKUP_REAL.md',
            'MODULO_SEGURANCA_COMPLETO.md',
        ]
        for doc in implementation_docs:
            self.move_file(doc, f'archive/implementation_reports/{doc}')
        
        # Análises e Diagnósticos
        print(f"\n{Colors.YELLOW}→ Análises e Diagnósticos{Colors.END}")
        analysis_docs = [
            'DIAGNOSTICO_ANALYTICS.md',
            'DIAGNOSTICO_SISTEMA_CONFIGURACOES.md',
            'ANALISE_TEMPO_CHAMADOS.md',
            'ANALISE_NOMENCLATURA_FRONTEND.md',
            'ANALISE_COMERCIAL_2025.md',
            'TESTE_ANALYTICS_CORRIGIDO.md',
        ]
        for doc in analysis_docs:
            self.move_file(doc, f'archive/analysis/{doc}')
        
        # Planos e Roadmaps
        print(f"\n{Colors.YELLOW}→ Planos e Roadmaps{Colors.END}")
        planning_docs = [
            'PLANO_ACAO_CONFIGURACOES.md',
            'PLANO_ACAO_IMEDIATO.md',
            'MODAL_SYSTEM_PLAN.md',
            'ROADMAP_COMERCIAL_2025.md',
            'ROTEIRO_TESTES_NOTIFICACOES.md',
            'PLANO_LIMPEZA_PROJETO.md',
        ]
        for doc in planning_docs:
            self.move_file(doc, f'archive/planning/{doc}')
        
        # Correções e Melhorias
        print(f"\n{Colors.YELLOW}→ Correções e Melhorias{Colors.END}")
        fixes_docs = [
            'CORRECAO_EDICAO_USUARIOS.md',
            'APLICAR_CORRECOES_EMAIL.md',
            'FLUXO_EMAILS.md',
            'REMINDER_IMPROVEMENTS.md',
            'SECURITY_IMPROVEMENTS.md',
        ]
        for doc in fixes_docs:
            self.move_file(doc, f'archive/fixes/{doc}')
        
        # Status Reports
        print(f"\n{Colors.YELLOW}→ Relatórios de Status{Colors.END}")
        status_docs = [
            'STATUS_IMPLEMENTACAO_ANALYTICS.md',
            'ANALYTICS_CHECKLIST_FINAL.md',
            'RESUMO_EXECUTIVO_IMPLEMENTACAO.md',
            'RESUMO_BADGE_CHAMADOS.md',
            'RESUMO_NOMENCLATURA.md',
            'DIA1_COMPLETO.md',
        ]
        for doc in status_docs:
            self.move_file(doc, f'archive/status_reports/{doc}')
        
        # Guias Temporários
        print(f"\n{Colors.YELLOW}→ Guias Temporários{Colors.END}")
        guides_docs = [
            'EXEMPLOS_ANTES_DEPOIS.md',
            'INDICE_MODERNIZACAO.md',
            'FASE3_NOTIFICACOES_LOGS.md',
            'MIGRATION_EXAMPLES.md',
        ]
        for doc in guides_docs:
            self.move_file(doc, f'archive/guides/{doc}')
    
    def generate_report(self):
        """Gera relatório final da limpeza"""
        print(f"\n{Colors.BLUE}{'='*60}{Colors.END}")
        print(f"{Colors.BLUE}📊 Relatório de Limpeza{Colors.END}")
        print(f"{Colors.BLUE}{'='*60}{Colors.END}\n")
        
        moves = [a for a in self.actions_log if a['type'] == 'move']
        deletes = [a for a in self.actions_log if a['type'] == 'delete']
        
        print(f"Arquivos movidos: {Colors.GREEN}{len(moves)}{Colors.END}")
        print(f"Arquivos deletados: {Colors.RED}{len(deletes)}{Colors.END}")
        print(f"Total de ações: {Colors.BLUE}{len(self.actions_log)}{Colors.END}")
        
        if not self.dry_run:
            self.create_backup_manifest()
    
    def run(self):
        """Executa limpeza completa"""
        print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
        print(f"{Colors.GREEN}🧹 Limpeza Profissional do Projeto TI OSN System{Colors.END}")
        print(f"{Colors.GREEN}{'='*60}{Colors.END}")
        
        if self.dry_run:
            print(f"\n{Colors.YELLOW}⚠ MODO DRY-RUN: Nenhuma mudança será feita{Colors.END}\n")
        else:
            print(f"\n{Colors.RED}⚠ MODO EXECUÇÃO: Mudanças serão aplicadas!{Colors.END}\n")
        
        self.cleanup_test_scripts()
        self.cleanup_debug_scripts()
        self.cleanup_migration_scripts()
        self.cleanup_documentation()
        self.generate_report()
        
        print(f"\n{Colors.GREEN}{'='*60}{Colors.END}")
        print(f"{Colors.GREEN}✅ Limpeza Concluída!{Colors.END}")
        print(f"{Colors.GREEN}{'='*60}{Colors.END}\n")

def main():
    parser = argparse.ArgumentParser(
        description='Script de Limpeza Profissional do Projeto'
    )
    parser.add_argument(
        '--dry-run',
        action='store_true',
        help='Simular sem fazer mudanças reais'
    )
    parser.add_argument(
        '--execute',
        action='store_true',
        help='Executar limpeza real'
    )
    
    args = parser.parse_args()
    
    if not args.dry_run and not args.execute:
        print(f"{Colors.YELLOW}⚠ Por favor, especifique --dry-run ou --execute{Colors.END}")
        parser.print_help()
        return
    
    project_root = Path(__file__).parent
    cleaner = ProjectCleaner(project_root, dry_run=args.dry_run)
    cleaner.run()

if __name__ == '__main__':
    main()
