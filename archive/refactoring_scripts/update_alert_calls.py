"""
Script para substituir alert() por Feedback em templates HTML
"""

import re
from pathlib import Path

def update_alerts_in_file(filepath):
    """Atualiza alert() para usar Feedback nos templates"""
    print(f"\n📝 Processando: {filepath.name}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    count = 0
    
    # Padrão 1: alert('mensagem de erro')
    error_patterns = [
        r"alert\('([^']*[Ee]rro[^']*)'\)",
        r'alert\("([^"]*[Ee]rro[^"]*)"\)',
        r"alert\('([^']*[Ff]alh[^']*)'\)",
        r'alert\("([^"]*[Ff]alh[^"]*)"\)',
        r"alert\('([^']*inválid[^']*)'\)",
        r'alert\("([^"]*inválid[^"]*)"\)',
    ]
    
    for pattern in error_patterns:
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, r"Feedback.error('Erro', '\1')", content)
            count += len(matches)
    
    # Padrão 2: alert('mensagem de sucesso')
    success_patterns = [
        r"alert\('([^']*[Ss]ucesso[^']*)'\)",
        r'alert\("([^"]*[Ss]ucesso[^"]*)"\)',
        r"alert\('([^']*[Cc]onclu[íi]d[ao][^']*)'\)",
        r'alert\("([^"]*[Cc]onclu[íi]d[ao][^"]*)"\)',
    ]
    
    for pattern in success_patterns:
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, r"Feedback.success('Sucesso', '\1')", content)
            count += len(matches)
    
    # Padrão 3: alert('mensagem de aviso')
    warning_patterns = [
        r"alert\('([^']*[Aa]tenção[^']*)'\)",
        r'alert\("([^"]*[Aa]tenção[^"]*)"\)',
        r"alert\('([^']*[Aa]viso[^']*)'\)",
        r'alert\("([^"]*[Aa]viso[^"]*)"\)',
    ]
    
    for pattern in warning_patterns:
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, r"Feedback.warning('Atenção', '\1')", content)
            count += len(matches)
    
    # Padrão 4: alert('qualquer outra mensagem') -> info
    generic_patterns = [
        r"alert\('([^']+)'\)",
        r'alert\("([^"]+)"\)',
    ]
    
    for pattern in generic_patterns:
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, r"Feedback.info('', '\1')", content)
            count += len(matches)
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ {count} alert() convertidos")
        return count
    else:
        print("  ℹ️ Nenhum alert() encontrado")
        return 0

def main():
    print("=" * 60)
    print("🔔 SUBSTITUIR ALERT() POR FEEDBACK")
    print("=" * 60)
    
    base_path = Path(__file__).parent.parent
    templates_path = base_path / 'app' / 'templates'
    
    # Buscar recursivamente todos os arquivos HTML
    html_files = list(templates_path.rglob('*.html'))
    
    total = 0
    files_updated = 0
    
    for filepath in html_files:
        count = update_alerts_in_file(filepath)
        if count > 0:
            total += count
            files_updated += 1
    
    print("\n" + "=" * 60)
    print(f"✅ CONCLUÍDO")
    print(f"📊 {total} alert() convertidos em {files_updated} arquivos")
    print("=" * 60)

if __name__ == '__main__':
    main()
