"""
Script avançado para atualizar flash() calls com f-strings e multi-linha
"""

import re
from pathlib import Path

def update_flash_advanced(filepath):
    """Atualiza casos complexos de flash()"""
    print(f"\n📝 Processando casos complexos: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        content = f.read()
    
    original_content = content
    count = 0
    
    # Padrão 1: flash(f"...", "categoria")
    patterns_fstring = [
        (r'flash\(f"([^"]+)",\s*"success"\)', r'flash_success(f"\1")'),
        (r'flash\(f"([^"]+)",\s*"danger"\)', r'flash_error(f"\1")'),
        (r'flash\(f"([^"]+)",\s*"error"\)', r'flash_error(f"\1")'),
        (r'flash\(f"([^"]+)",\s*"warning"\)', r'flash_warning(f"\1")'),
        (r'flash\(f"([^"]+)",\s*"info"\)', r'flash_info(f"\1")'),
    ]
    
    for pattern, replacement in patterns_fstring:
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, replacement, content)
            count += len(matches)
            print(f"  ✓ {len(matches)} f-strings convertidas")
    
    # Padrão 2: flash(\n    "mensagem",\n    "categoria"\n)
    multiline_pattern = r'flash\(\s*\n\s*"([^"]+)",\s*"(success|danger|error|warning|info)"\s*\n?\s*\)'
    
    def replace_multiline(match):
        message = match.group(1)
        category = match.group(2)
        
        func_map = {
            'success': 'flash_success',
            'danger': 'flash_error',
            'error': 'flash_error',
            'warning': 'flash_warning',
            'info': 'flash_info'
        }
        
        func_name = func_map.get(category, 'flash_info')
        return f'{func_name}(\n    "{message}"\n)'
    
    matches = re.findall(multiline_pattern, content, re.MULTILINE | re.DOTALL)
    if matches:
        content = re.sub(multiline_pattern, replace_multiline, content, flags=re.MULTILINE | re.DOTALL)
        count += len(matches)
        print(f"  ✓ {len(matches)} multi-linha convertidas")
    
    # Padrão 3: flash(\n    f"mensagem",\n    "categoria"\n)
    multiline_fstring_pattern = r'flash\(\s*\n\s*f"([^"]+)",\s*"(success|danger|error|warning|info)"\s*\n?\s*\)'
    
    def replace_multiline_fstring(match):
        message = match.group(1)
        category = match.group(2)
        
        func_map = {
            'success': 'flash_success',
            'danger': 'flash_error',
            'error': 'flash_error',
            'warning': 'flash_warning',
            'info': 'flash_info'
        }
        
        func_name = func_map.get(category, 'flash_info')
        return f'{func_name}(\n    f"{message}"\n)'
    
    matches = re.findall(multiline_fstring_pattern, content, re.MULTILINE | re.DOTALL)
    if matches:
        content = re.sub(multiline_fstring_pattern, replace_multiline_fstring, content, flags=re.MULTILINE | re.DOTALL)
        count += len(matches)
        print(f"  ✓ {len(matches)} multi-linha f-strings convertidas")
    
    # Padrão 4: flash( "mensagem", "categoria" ) - com espaços
    space_patterns = [
        (r'flash\(\s+"([^"]+)",\s+"success"\s+\)', r'flash_success("\1")'),
        (r'flash\(\s+"([^"]+)",\s+"danger"\s+\)', r'flash_error("\1")'),
        (r'flash\(\s+"([^"]+)",\s+"error"\s+\)', r'flash_error("\1")'),
        (r'flash\(\s+"([^"]+)",\s+"warning"\s+\)', r'flash_warning("\1")'),
        (r'flash\(\s+"([^"]+)",\s+"info"\s+\)', r'flash_info("\1")'),
    ]
    
    for pattern, replacement in space_patterns:
        matches = re.findall(pattern, content)
        if matches:
            content = re.sub(pattern, replacement, content)
            count += len(matches)
            print(f"  ✓ {len(matches)} com espaços extras convertidas")
    
    if content != original_content:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.write(content)
        print(f"  ✅ {count} substituições complexas feitas")
        return count
    else:
        print("  ℹ️ Nenhuma substituição complexa necessária")
        return 0

def main():
    print("=" * 60)
    print("🔧 ATUALIZADOR AVANÇADO DE FLASH CALLS")
    print("=" * 60)
    
    base_path = Path(__file__).parent.parent
    files = [
        base_path / 'app' / 'routes.py',
        base_path / 'app' / 'blueprints' / 'system_config.py',
    ]
    
    total = 0
    for filepath in files:
        if filepath.exists():
            total += update_flash_advanced(filepath)
    
    print("\n" + "=" * 60)
    print(f"✅ CONCLUÍDO: {total} substituições complexas")
    print("=" * 60)

if __name__ == '__main__':
    main()
