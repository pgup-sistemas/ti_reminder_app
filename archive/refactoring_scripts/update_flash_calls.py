"""
Script para atualizar todas as chamadas flash() para usar helpers padronizados
Este script substitui automaticamente flash() por flash_success, flash_error, etc.
"""

import re
import os
from pathlib import Path

# Mapeamento de categorias antigas para novas funções
REPLACEMENTS = [
    # flash("mensagem", "success") -> flash_success("mensagem")
    (r'flash\("([^"]+)",\s*"success"\)', r'flash_success("\1")'),
    (r"flash\('([^']+)',\s*'success'\)", r"flash_success('\1')"),
    
    # flash("mensagem", "danger") -> flash_error("mensagem")
    (r'flash\("([^"]+)",\s*"danger"\)', r'flash_error("\1")'),
    (r"flash\('([^']+)',\s*'danger'\)", r"flash_error('\1')"),
    
    # flash("mensagem", "error") -> flash_error("mensagem")
    (r'flash\("([^"]+)",\s*"error"\)', r'flash_error("\1")'),
    (r"flash\('([^']+)',\s*'error'\)", r"flash_error('\1')"),
    
    # flash("mensagem", "warning") -> flash_warning("mensagem")
    (r'flash\("([^"]+)",\s*"warning"\)', r'flash_warning("\1")'),
    (r"flash\('([^']+)',\s*'warning'\)", r"flash_warning('\1')"),
    
    # flash("mensagem", "info") -> flash_info("mensagem")
    (r'flash\("([^"]+)",\s*"info"\)', r'flash_info("\1")'),
    (r"flash\('([^']+)',\s*'info'\)", r"flash_info('\1')"),
]

# Tratamento especial para flash multi-linha
MULTILINE_PATTERNS = [
    # flash(\n    "mensagem",\n    "categoria"\n)
    (r'flash\(\s*\n\s*"([^"]+)",\s*\n\s*"success"\s*\n?\s*\)', r'flash_success(\n    "\1"\n)'),
    (r'flash\(\s*\n\s*"([^"]+)",\s*\n\s*"danger"\s*\n?\s*\)', r'flash_error(\n    "\1"\n)'),
    (r'flash\(\s*\n\s*"([^"]+)",\s*\n\s*"error"\s*\n?\s*\)', r'flash_error(\n    "\1"\n)'),
    (r'flash\(\s*\n\s*"([^"]+)",\s*\n\s*"warning"\s*\n?\s*\)', r'flash_warning(\n    "\1"\n)'),
    (r'flash\(\s*\n\s*"([^"]+)",\s*\n\s*"info"\s*\n?\s*\)', r'flash_info(\n    "\1"\n)'),
]

def update_file(filepath):
    """Atualiza um arquivo Python substituindo flash() por helpers"""
    print(f"\n📝 Processando: {filepath}")
    
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            content = f.read()
        
        original_content = content
        replacements_made = 0
        
        # Aplicar substituições simples
        for pattern, replacement in REPLACEMENTS:
            matches = re.findall(pattern, content)
            if matches:
                content = re.sub(pattern, replacement, content)
                replacements_made += len(matches)
                print(f"  ✓ Substituídas {len(matches)} ocorrências: {pattern[:50]}...")
        
        # Aplicar substituições multi-linha
        for pattern, replacement in MULTILINE_PATTERNS:
            matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
            if matches:
                content = re.sub(pattern, replacement, content, flags=re.MULTILINE | re.DOTALL)
                replacements_made += len(matches)
                print(f"  ✓ Substituídas {len(matches)} ocorrências multi-linha")
        
        # Adicionar imports se necessário
        if replacements_made > 0:
            # Verificar se já tem o import
            if 'from app.utils import' not in content and 'from .utils import' not in content:
                # Encontrar linha de imports do flask
                flask_import_pattern = r'from flask import \([^)]+\)'
                flask_import_match = re.search(flask_import_pattern, content, re.DOTALL)
                
                if flask_import_match:
                    # Adicionar import após imports do Flask
                    insert_pos = flask_import_match.end()
                    new_import = '\nfrom app.utils import flash_success, flash_error, flash_warning, flash_info'
                    content = content[:insert_pos] + new_import + content[insert_pos:]
                    print("  ✓ Adicionado import dos helpers")
                else:
                    # Tentar encontrar qualquer import de flask
                    flask_simple_pattern = r'from flask import [^\n]+'
                    flask_simple_match = re.search(flask_simple_pattern, content)
                    if flask_simple_match:
                        insert_pos = flask_simple_match.end()
                        new_import = '\nfrom app.utils import flash_success, flash_error, flash_warning, flash_info'
                        content = content[:insert_pos] + new_import + content[insert_pos:]
                        print("  ✓ Adicionado import dos helpers")
            
            # Remover flash dos imports do Flask se não for mais usado
            if content.count('flash(') == 0:  # Não há mais chamadas flash() diretas
                # Remover flash dos imports
                content = re.sub(r',\s*flash\s*,', ', ', content)
                content = re.sub(r',\s*flash\)', ')', content)
                content = re.sub(r'\(flash\s*,', '(', content)
                print("  ✓ Removido flash dos imports")
        
        # Salvar se houver mudanças
        if content != original_content:
            with open(filepath, 'w', encoding='utf-8') as f:
                f.write(content)
            print(f"  ✅ Arquivo atualizado: {replacements_made} substituições feitas")
            return replacements_made
        else:
            print("  ℹ️ Nenhuma substituição necessária")
            return 0
            
    except Exception as e:
        print(f"  ❌ Erro ao processar arquivo: {e}")
        return 0

def main():
    """Processa todos os arquivos Python relevantes"""
    print("=" * 60)
    print("🚀 ATUALIZADOR DE FLASH CALLS")
    print("=" * 60)
    
    # Arquivos a processar
    base_path = Path(__file__).parent.parent
    files_to_process = [
        base_path / 'app' / 'routes.py',
        base_path / 'app' / 'blueprints' / 'system_config.py',
    ]
    
    total_replacements = 0
    
    for filepath in files_to_process:
        if filepath.exists():
            replacements = update_file(filepath)
            total_replacements += replacements
        else:
            print(f"\n⚠️ Arquivo não encontrado: {filepath}")
    
    print("\n" + "=" * 60)
    print(f"✅ CONCLUÍDO: {total_replacements} substituições totais")
    print("=" * 60)
    
    if total_replacements > 0:
        print("\n📋 Próximos passos:")
        print("1. Revisar as mudanças nos arquivos")
        print("2. Testar o sistema")
        print("3. Fazer commit das mudanças")

if __name__ == '__main__':
    main()
