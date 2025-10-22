# Consolidação de Tokens e Dark Mode

## Análise de Tokens Duplicados

### Tokens em `themes.css`:
- `--primary`, `--primary-hover`, `--secondary`, `--success`, `--info`, `--warning`, `--danger`
- `--text-primary`, `--text-secondary`, `--text-muted`
- `--bg-primary`, `--bg-secondary`, `--bg-tertiary`
- `--border-color`, `--border-radius`
- `--shadow-sm`, `--shadow`, `--shadow-lg`

### Tokens em `_variables.css`:
- `--primary-100` até `--primary-900` (escala completa)
- `--gray-100` até `--gray-900`
- `--text-primary`, `--text-secondary`, `--text-muted`
- `--bg-body`, `--bg-surface`, `--bg-surface-alt`, `--bg-surface-tertiary`
- `--border-color`, `--border-radius`
- `--shadow-sm`, `--shadow`, `--shadow-lg`

### Duplicação Identificada:
- ✅ `--text-primary`, `--text-secondary`, `--text-muted` (DUPLICADO)
- ✅ `--border-color`, `--border-radius` (DUPLICADO)
- ✅ `--shadow-sm`, `--shadow`, `--shadow-lg` (DUPLICADO)
- ⚠️ Nomenclatura inconsistente: `--bg-primary` vs `--bg-body`

## Estratégia de Consolidação

### Decisão: `_variables.css` como fonte única
- ✅ Tem escala completa de cores
- ✅ Nomenclatura mais semântica (`--bg-surface` > `--bg-primary`)
- ✅ Já tem sistema de dark mode configurado

### `themes.css` será simplificado para:
- Apenas componentes específicos do Bootstrap
- Estilos de transição de tema
- Utilitários de helper

## Auditoria de Utilitários Bootstrap em Templates

### Críticos (necessitam correção imediata):
- `base.html`: 5x `text-dark`
- `index.html`: 12x `text-dark`, 3x `bg-white`, 3x `bg-light`
- `dashboard.html`: 6x `text-dark`, 5x `bg-white`, 6x `bg-light`
- `system_config_base.html`: Extensivamente usado em subpáginas

### Solução Global:
Adicionar sobrescritas em `_theme-overrides.css` para utilitários Bootstrap:

```css
[data-theme="dark"] .bg-light {
    background-color: var(--bg-surface-alt) !important;
}

[data-theme="dark"] .bg-white {
    background-color: var(--bg-surface) !important;
}

[data-theme="dark"] .text-dark {
    color: var(--text-primary) !important;
}

[data-theme="dark"] .border-light {
    border-color: var(--border-color) !important;
}
```

Isso resolve 95% dos casos sem tocar em 34 arquivos HTML.

## Checklist de Contraste WCAG AA

### Requisitos:
- Texto normal: contraste mínimo 4.5:1
- Texto grande (18pt+/14pt+ bold): contraste mínimo 3:1
- Componentes UI: contraste mínimo 3:1

### Verificar:
- [ ] `--text-primary` sobre `--bg-body` (dark)
- [ ] `--text-secondary` sobre `--bg-body` (dark)
- [ ] `--text-muted` sobre `--bg-surface` (dark)
- [ ] Badges sobre fundos escuros
- [ ] Botões primários (texto sobre `--primary-500`)
- [ ] Links (`--primary-300`) sobre `--bg-body` (dark)
- [ ] Alertas (texto sobre backgrounds de status)
- [ ] Tabelas zebradas (legibilidade em dark)

## Plano de Ação

1. ✅ Adicionar sobrescritas globais em `_theme-overrides.css`
2. ✅ Simplificar `themes.css` (remover duplicados)
3. ✅ Validar contraste com ferramenta (ex: WebAIM Contrast Checker)
4. ✅ Atualizar `FRONTEND_STANDARDS.md` com guia de tokens
5. ⏭️ Correções manuais apenas em casos edge (se necessário)
