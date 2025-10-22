"""
Script final para limpar os últimos casos de flash() multi-linha com indentação complexa
"""

import re
from pathlib import Path

def final_cleanup(filepath):
    """Limpa os últimos casos restantes"""
    print(f"\n📝 Limpeza final: {filepath}")
    
    with open(filepath, 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    modified = False
    i = 0
    while i < len(lines):
        line = lines[i]
        
        # Detectar flash( no início de uma linha
        if re.match(r'^\s+flash\(\s*$', line):
            # Ler próximas linhas até fechar o parêntese
            full_call = line
            j = i + 1
            paren_count = line.count('(') - line.count(')')
            
            while j < len(lines) and paren_count > 0:
                full_call += lines[j]
                paren_count += lines[j].count('(') - lines[j].count(')')
                j += 1
            
            # Tentar extrair mensagem e categoria
            match = re.search(r'flash\(\s*\n\s*([f]?)"([^"]+)",\s*\n\s*"(success|danger|error|warning|info)"\s*\n\s*\)', full_call, re.DOTALL)
            
            if match:
                is_fstring = match.group(1) == 'f'
                message = match.group(2)
                category = match.group(3)
                
                func_map = {
                    'success': 'flash_success',
                    'danger': 'flash_error',
                    'error': 'flash_error',
                    'warning': 'flash_warning',
                    'info': 'flash_info'
                }
                
                func_name = func_map[category]
                indent = re.match(r'^(\s+)', line).group(1)
                
                if is_fstring:
                    new_call = f'{indent}{func_name}(\n{indent}    f"{message}"\n{indent})\n'
                else:
                    new_call = f'{indent}{func_name}(\n{indent}    "{message}"\n{indent})\n'
                
                # Substituir as linhas
                lines[i:j] = [new_call]
                modified = True
                print(f"  ✓ Convertido: linha {i+1}")
            
        i += 1
    
    if modified:
        with open(filepath, 'w', encoding='utf-8') as f:
            f.writelines(lines)
        print("  ✅ Arquivo atualizado")
        return True
    else:
        print("  ℹ️ Nenhuma modificação necessária")
        return False

def main():
    print("=" * 60)
    print("🎯 LIMPEZA FINAL DE FLASH CALLS")
    print("=" * 60)
    
    base_path = Path(__file__).parent.parent
    filepath = base_path / 'app' / 'routes.py'
    
    if filepath.exists():
        final_cleanup(filepath)
    
    print("\n" + "=" * 60)
    print("✅ LIMPEZA FINAL CONCLUÍDA")
    print("=" * 60)

if __name__ == '__main__':
    main()
