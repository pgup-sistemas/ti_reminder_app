# 📐 Padrões de Frontend - TI OSN System

## 🎨 Design System

### Larguras de Containers

#### Padrão Universal (Todos os Templates)
```html
<div class="container-fluid py-3">
    <div class="row">
        <div class="col-12">
            <!-- Conteúdo -->
        </div>
    </div>
</div>
```

**Características:**
- `container-fluid`: Largura total com padding lateral
- Consistência visual em todo o sistema
- Melhor aproveitamento do espaço disponível
- Mesmo comportamento em formulários, dashboards e listagens

### Headers de Página

#### Padrão Consistente
```html
<div class="d-flex justify-content-between align-items-center mb-4">
    <div>
        <h4 class="text-primary mb-1">
            <i class="fas fa-icon me-2"></i>Título da Página
        </h4>
        <p class="text-muted mb-0 small">Descrição breve da funcionalidade</p>
    </div>
    <a href="{{ url_for('route.back') }}" class="btn btn-outline-secondary btn-sm">
        <i class="fas fa-arrow-left me-1"></i>Voltar
    </a>
</div>
```

### Cards

#### Card de Formulário
```html
<div class="card shadow-sm border-0">
    <div class="card-body p-4">
        <!-- Conteúdo -->
    </div>
</div>
```

**Características:**
- `shadow-sm`: Sombra suave
- `border-0`: Sem bordas
- `p-4`: Padding generoso (1.5rem)

### Seções de Formulário

#### Estrutura de Seção
```html
<div class="mb-4">
    <h5 class="text-secondary mb-3">
        <i class="fas fa-icon me-2"></i>Título da Seção
    </h5>
    <div class="row g-3">
        <!-- Campos do formulário -->
    </div>
</div>
```

#### Separadores entre Seções
```html
<hr class="my-4">
```

### Campos de Formulário

#### Label Padrão
```html
<label for="field_id" class="form-label fw-medium">
    <i class="fas fa-icon me-1"></i>Nome do Campo <span class="text-danger">*</span>
</label>
```

**Elementos:**
- `fw-medium`: Peso médio para destaque
- Ícone contextual
- Asterisco vermelho para campos obrigatórios

#### Input com Validação
```html
<input type="text" 
       class="form-control" 
       id="field_id" 
       name="field_name" 
       placeholder="Exemplo descritivo"
       required>
<div class="invalid-feedback">Mensagem de erro específica</div>
<div class="form-text">Texto de ajuda opcional</div>
```

#### Espaçamento entre Campos
```html
<div class="row g-3">
    <div class="col-md-6"><!-- Campo 1 --></div>
    <div class="col-md-6"><!-- Campo 2 --></div>
</div>
```

**Nota:** Use `g-3` para gutters consistentes (1rem)

### Botões de Ação

#### Área de Botões
```html
<div class="d-flex gap-2 justify-content-end pt-3 border-top">
    <a href="{{ url_for('route.cancel') }}" class="btn btn-outline-secondary">
        <i class="fas fa-times me-1"></i>Cancelar
    </a>
    <button type="submit" class="btn btn-primary">
        <i class="fas fa-save me-1"></i>Salvar
    </button>
</div>
```

**Características:**
- `gap-2`: Espaçamento entre botões
- `justify-content-end`: Alinhamento à direita
- `pt-3 border-top`: Separação visual
- Ícones em todos os botões

### Validação de Formulários

#### JavaScript Padrão
```javascript
(function () {
    'use strict';
    
    const forms = document.querySelectorAll('.needs-validation');
    
    Array.from(forms).forEach(form => {
        const inputs = form.querySelectorAll('input, textarea, select');
        
        // Validação em tempo real
        inputs.forEach(input => {
            input.addEventListener('blur', function () {
                if (!input.checkValidity()) {
                    input.classList.add('is-invalid');
                    input.classList.remove('is-valid');
                } else {
                    input.classList.remove('is-invalid');
                    if (input.value) {
                        input.classList.add('is-valid');
                    }
                }
            });
        });
        
        // Validação no submit
        form.addEventListener('submit', function (event) {
            if (!form.checkValidity()) {
                event.preventDefault();
                event.stopPropagation();
                
                // Focar no primeiro campo inválido
                const firstInvalid = form.querySelector(':invalid');
                if (firstInvalid) {
                    firstInvalid.scrollIntoView({ behavior: 'smooth', block: 'center' });
                    firstInvalid.focus();
                }
            }
            
            form.classList.add('was-validated');
        });
    });
})();
```

## 🎯 Ícones FontAwesome

### Categorias Comuns

| Contexto | Ícone | Classe |
|----------|-------|--------|
| Adicionar | ➕ | `fa-plus-circle` |
| Editar | ✏️ | `fa-edit` |
| Salvar | 💾 | `fa-save` |
| Confirmar | ✓ | `fa-check` |
| Cancelar | ✕ | `fa-times` |
| Voltar | ← | `fa-arrow-left` |
| Informação | ℹ️ | `fa-info-circle` |
| Equipamento | 💻 | `fa-laptop` |
| Patrimônio | 🏷️ | `fa-barcode` |
| Categoria | 🏷️ | `fa-tag` |
| Localização | 📍 | `fa-map-marker-alt` |
| Configuração | ⚙️ | `fa-cog` |
| Calendário | 📅 | `fa-calendar-alt` |

## 🎨 Cores do Sistema

### Classes de Texto
- `text-primary`: Azul principal (#0d6efd)
- `text-secondary`: Cinza secundário (#6c757d)
- `text-success`: Verde sucesso (#198754)
- `text-danger`: Vermelho erro (#dc3545)
- `text-warning`: Amarelo aviso (#ffc107)
- `text-info`: Azul informação (#0dcaf0)
- `text-muted`: Cinza claro (#6c757d)

### Classes de Background
- `bg-primary`: Fundo azul
- `bg-light`: Fundo cinza claro (#f8f9fa)
- `bg-success`: Fundo verde
- `bg-danger`: Fundo vermelho
- `bg-warning`: Fundo amarelo
- `bg-info`: Fundo azul claro

## 📱 Responsividade

### Breakpoints Bootstrap 5
- `xs`: < 576px (mobile)
- `sm`: ≥ 576px (mobile landscape)
- `md`: ≥ 768px (tablet)
- `lg`: ≥ 992px (desktop)
- `xl`: ≥ 1200px (large desktop)
- `xxl`: ≥ 1400px (extra large)

### Padrões de Colunas
```html
<!-- 2 colunas em desktop, 1 em mobile -->
<div class="col-md-6">...</div>

<!-- 3 colunas em desktop, 1 em mobile -->
<div class="col-md-4">...</div>

<!-- 4 colunas em large, 2 em tablet, 1 em mobile -->
<div class="col-lg-3 col-md-6">...</div>
```

## ✅ Checklist de Qualidade

### Antes de Finalizar um Template

- [ ] Container: `<div class="container-fluid py-3">`
- [ ] Estrutura: `<div class="row"><div class="col-12">`
- [ ] Header com ícone dinâmico e descrição
- [ ] Card com `shadow-sm border-0`
- [ ] Padding do card: `p-4`
- [ ] Labels com `fw-medium` e ícones
- [ ] Campos obrigatórios marcados com `*`
- [ ] Placeholders descritivos
- [ ] Mensagens de validação específicas
- [ ] Form-text explicativo quando necessário
- [ ] Seções separadas com `<hr class="my-4">`
- [ ] Espaçamento: `g-3` entre campos
- [ ] Botões com ícones e alinhados à direita
- [ ] Validação JavaScript implementada
- [ ] Responsivo em todos os breakpoints
- [ ] Acessibilidade (labels, aria-labels)

## 🌓 Dark Mode e Sistema de Tokens CSS

### Design Tokens (CSS Variables)

O sistema utiliza **CSS Custom Properties (variáveis)** definidas em `app/static/css/_variables.css` para garantir consistência e suporte a temas.

#### ❌ NÃO FAÇA (cores hardcoded):
```css
.card {
    background: #ffffff;
    color: #212529;
    border: 1px solid #dee2e6;
}
```

#### ✅ FAÇA (variáveis de tema):
```css
.card {
    background: var(--bg-surface);
    color: var(--text-primary);
    border: 1px solid var(--border-color);
}
```

### Tokens Disponíveis

#### Cores de Texto
```css
--text-primary     /* Texto principal (#212529 light / #f8f9fa dark) */
--text-secondary   /* Texto secundário (#495057 light / #dee2e6 dark) */
--text-muted       /* Texto esmaecido (#6c757d light / #adb5bd dark) */
```

#### Cores de Fundo
```css
--bg-body              /* Fundo da página */
--bg-surface           /* Fundo de cards e modais */
--bg-surface-alt       /* Fundo alternativo (ex: card-header) */
--bg-surface-tertiary  /* Fundo terciário (ex: hover states) */
```

#### Cores Primárias (Escala)
```css
--primary-100   /* Muito claro */
--primary-300   /* Claro */
--primary-500   /* Padrão (cor da marca #008bcd) */
--primary-700   /* Escuro */
--primary-900   /* Muito escuro */
```

#### Outras Cores
```css
--success   /* Verde de sucesso */
--warning   /* Amarelo de aviso */
--danger    /* Vermelho de erro */
--info      /* Azul de informação */
```

#### Bordas e Sombras
```css
--border-color     /* Cor de bordas */
--border-radius    /* Arredondamento padrão */
--shadow-sm        /* Sombra pequena */
--shadow           /* Sombra média */
--shadow-lg        /* Sombra grande */
```

### Utilitários Bootstrap Compatíveis

Os seguintes utilitários Bootstrap **funcionam automaticamente** no dark mode (via `_theme-overrides.css`):

✅ **Permitidos (sobrescritos automaticamente):**
- `.bg-light` → transforma em `var(--bg-surface-alt)` no dark
- `.bg-white` → transforma em `var(--bg-surface)` no dark
- `.text-dark` → transforma em `var(--text-primary)` no dark
- `.text-muted` → usa `var(--text-muted)` no dark
- `.border-light` → usa `var(--border-color)` no dark

❌ **Evitar (não mudam automaticamente):**
- Cores inline: `style="background: #fff"`
- Gradientes fixos: `background: linear-gradient(#fff, #000)`
- Classes Bootstrap não sobrescritas: `.bg-info`, `.text-info`, etc.

### Como Adaptar Componentes para Dark Mode

#### Exemplo: Card com Gradient
```html
<!-- ❌ NÃO FAÇA (gradiente fixo) -->
<div class="card" style="background: linear-gradient(135deg, #f8f9fa, #ffffff)">
    <div class="card-body">Conteúdo</div>
</div>

<!-- ✅ FAÇA (variáveis CSS) -->
<div class="card modern-card">
    <div class="card-body">Conteúdo</div>
</div>
```

```css
/* Em dashboard.css ou arquivo CSS específico */
.modern-card {
    background: linear-gradient(135deg, var(--bg-surface-alt), var(--bg-surface));
    color: var(--text-primary);
    border: 1px solid var(--border-color);
}
```

#### Exemplo: Botões Customizados
```css
/* ❌ NÃO FAÇA */
.custom-btn {
    background: #007bff;
    color: #fff;
}

/* ✅ FAÇA */
.custom-btn {
    background: var(--primary-500);
    color: white; /* branco é sempre branco */
}

.custom-btn:hover {
    background: var(--primary-700);
}
```

### Ouvindo Mudanças de Tema (JavaScript)

Para componentes dinâmicos que precisam reagir à mudança de tema:

```javascript
// Listener para mudanças de tema
document.addEventListener('themeChanged', (e) => {
    const isDark = e.detail.isDark;
    const theme = e.detail.theme;
    
    // Exemplo: atualizar gráfico
    if (myChart) {
        updateChartColors(isDark);
        myChart.update();
    }
});
```

### Obtendo Cores CSS via JavaScript

```javascript
// Ler valor de variável CSS
const styles = getComputedStyle(document.documentElement);
const primaryColor = styles.getPropertyValue('--primary-500').trim();
const textColor = styles.getPropertyValue('--text-primary').trim();

// Usar em bibliotecas externas (ex: Chart.js)
const chartOptions = {
    scales: {
        x: {
            ticks: { color: textColor },
            grid: { color: gridColor }
        }
    }
};
```

### Checklist para Novos Componentes

- [ ] Usa variáveis CSS ao invés de cores fixas
- [ ] Testado em ambos os temas (light/dark)
- [ ] Contraste WCAG AA atendido (mínimo 4.5:1 para texto)
- [ ] Sem gradientes ou backgrounds fixos
- [ ] Bordas e sombras usam tokens
- [ ] Se usa JavaScript, ouve evento `themeChanged`

### Testando Dark Mode

1. Abrir DevTools (F12)
2. Console: `document.documentElement.setAttribute('data-theme', 'dark')`
3. Verificar visualmente:
   - Todos os textos legíveis
   - Cards e modais com fundos adequados
   - Bordas visíveis
   - Ícones e badges contrastando
4. Toggle manual via botão no header

### Ferramentas de Contraste

- **WebAIM Contrast Checker**: https://webaim.org/resources/contrastchecker/
- **Chrome DevTools**: Lighthouse > Accessibility audit
- **Axe DevTools**: Extensão para verificação automática

---

## 🚀 Exemplos de Referência

### Templates Otimizados
1. `equipment_form.html` - Formulário de solicitação
2. `equipment_form_admin.html` - Formulário administrativo
3. `performance_dashboard.html` - Dashboard de métricas
4. `index.html` - Dashboard principal (dark mode ready)
5. `dashboard.css` - Estilos tema-aware

---

**Última atualização:** Outubro 2025  
**Versão:** 2.0 (com Dark Mode)  
**Mantido por:** Equipe de Desenvolvimento TI OSN
