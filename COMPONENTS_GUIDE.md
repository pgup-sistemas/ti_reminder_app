# 🎨 Guia de Componentes - TI OSN System

## 📋 Visão Geral

Este guia documenta todos os novos componentes implementados nas **FASE 1** e **FASE 2** do plano de modernização do TI OSN System. Os componentes foram desenvolvidos com foco em **profissionalismo**, **responsividade** e **experiência do usuário**.

## 🚀 Acesso Rápido

Para visualizar todos os componentes em ação, acesse: **Menu do Usuário → Demo Componentes**

---

## 📦 Componentes Implementados

### 1. 🪟 Sistema de Modais Modernas

**Arquivos:** `modals.js`, `modal-styles.css`

#### Funcionalidades:
- Modais com animações suaves
- Tipos: info, success, warning, error, confirm, prompt, custom
- Backdrop com blur effect
- Botões customizáveis
- Responsivo para mobile

#### Como Usar:
```javascript
// Modal básico
Modal.info('Título', 'Mensagem');
Modal.success('Sucesso!', 'Operação concluída');
Modal.error('Erro', 'Algo deu errado');

// Modal de confirmação
const result = await Modal.confirm('Confirma a exclusão?', 'Atenção');
if (result.action === 'confirm') {
    // Usuário confirmou
}

// Modal com input
const result = await Modal.prompt('Digite o nome:', 'Novo Item');
if (result.action === 'confirm') {
    console.log('Valor digitado:', result.value);
}

// Modal customizado
Modal.custom({
    title: 'Título Personalizado',
    content: '<p>HTML customizado</p>',
    buttons: [
        { text: 'Cancelar', action: 'cancel', class: 'btn-secondary' },
        { text: 'OK', action: 'ok', class: 'btn-primary' }
    ]
});
```

---

### 2. 🧭 Sistema de Breadcrumbs

**Arquivos:** `breadcrumbs.js`, `breadcrumb-styles.css`

#### Funcionalidades:
- Navegação hierárquica automática
- Ícones personalizados para cada seção
- Responsivo com colapso inteligente
- Integração automática com rotas

#### Como Usar:
```javascript
// Automático - detecta a rota atual
// Já funciona em todas as páginas

// Personalizar título da página atual
Breadcrumbs.setCurrentTitle('Minha Página', 'fas fa-star');

// Adicionar breadcrumb customizado
Breadcrumbs.addCustomBreadcrumb('Detalhes', 'fas fa-eye');

// Adicionar nova rota
Breadcrumbs.addRoute('/nova-rota', {
    title: 'Nova Página',
    icon: 'fas fa-plus',
    parent: '/'
});
```

---

### 3. 🔔 Sistema de Feedback Visual

**Arquivos:** `feedback.js`, `feedback-styles.css`

#### Funcionalidades:
- Toast notifications elegantes
- Loading overlays profissionais
- Validação de formulários em tempo real
- Progress bars animadas
- Estados de erro globais

#### Como Usar:
```javascript
// Toast notifications
Feedback.success('Título', 'Mensagem de sucesso');
Feedback.error('Erro', 'Mensagem de erro');
Feedback.warning('Aviso', 'Mensagem de aviso');
Feedback.info('Info', 'Mensagem informativa');

// Loading states
const loadingId = Feedback.showLoading('body', {
    message: 'Carregando...',
    spinner: 'default' // default, dots, pulse, bars
});
Feedback.hideLoading(loadingId);

// Aliases globais
showToast('success', 'Título', 'Mensagem');
const loading = showLoading('.meu-container');
hideLoading(loading);
```

---

### 4. 📊 Tabelas Responsivas Avançadas

**Arquivos:** `responsive-tables.css`

#### Funcionalidades:
- Layout dual: tabela (desktop) + cards (mobile)
- Ordenação visual
- Filtros integrados
- Paginação moderna
- Estados de loading e vazio
- Ações contextuais

#### Como Usar:
```html
<!-- Container responsivo -->
<div class="table-responsive-advanced">
    <!-- Filtros -->
    <div class="table-filters">
        <div class="row">
            <div class="col-md-6">
                <div class="table-search">
                    <input type="text" class="form-control" placeholder="Buscar...">
                    <i class="fas fa-search"></i>
                </div>
            </div>
        </div>
    </div>

    <!-- Tabela -->
    <table class="table table-modern table-sortable">
        <thead>
            <tr>
                <th>Nome</th>
                <th>Status</th>
                <th>Ações</th>
            </tr>
        </thead>
        <tbody>
            <tr>
                <td>Item 1</td>
                <td>
                    <span class="status-badge status-success">
                        <i class="fas fa-check"></i>Ativo
                    </span>
                </td>
                <td>
                    <div class="table-actions">
                        <a href="#" class="table-action-btn btn-view">
                            <i class="fas fa-eye"></i>
                        </a>
                        <a href="#" class="table-action-btn btn-edit">
                            <i class="fas fa-edit"></i>
                        </a>
                    </div>
                </td>
            </tr>
        </tbody>
    </table>

    <!-- Paginação -->
    <div class="pagination-modern">
        <div class="pagination-info">Mostrando 1-10 de 50</div>
        <div class="pagination-controls">
            <a href="#" class="pagination-btn active">1</a>
            <a href="#" class="pagination-btn">2</a>
        </div>
    </div>
</div>

<!-- Versão mobile (cards) -->
<div class="table-responsive-stack d-lg-none">
    <div class="table-card">
        <div class="table-card-header">
            <h6 class="table-card-title">Item 1</h6>
        </div>
        <div class="table-card-body">
            <div class="table-card-field">
                <span class="table-card-label">Status:</span>
                <span class="table-card-value">Ativo</span>
            </div>
        </div>
        <div class="table-card-actions">
            <button class="btn btn-sm btn-primary">Ver</button>
        </div>
    </div>
</div>
```

---

### 5. 📱 Formulários Mobile Otimizados

**Arquivos:** `mobile-forms.css`

#### Funcionalidades:
- Labels flutuantes
- Inputs com ícones
- Switches modernos
- Upload de arquivos drag & drop
- Validação visual
- Seções colapsáveis

#### Como Usar:
```html
<!-- Container mobile -->
<div class="form-mobile-container">
    <!-- Label flutuante -->
    <div class="form-floating-mobile">
        <input type="text" class="form-control" id="campo" placeholder=" ">
        <label for="campo">Nome do Campo</label>
    </div>

    <!-- Input com ícone -->
    <div class="input-with-icon">
        <input type="email" class="form-control" placeholder="E-mail">
        <i class="fas fa-envelope input-icon"></i>
    </div>

    <!-- Switch moderno -->
    <div class="form-switch-modern">
        <div>
            <div class="switch-label">Notificações</div>
            <div class="switch-description">Receber alertas</div>
        </div>
        <div class="switch-toggle" onclick="toggleSwitch(this)"></div>
    </div>

    <!-- Botão mobile -->
    <button class="btn-mobile btn-primary">
        <i class="fas fa-save me-2"></i>Salvar
    </button>
</div>
```

---

### 6. 🎨 Formulários Padronizados

**Arquivos:** `form-styles.css`

#### Funcionalidades:
- Estilos consistentes
- Variáveis CSS para temas
- Estados de validação
- Grupos organizados
- Responsividade automática

#### Como Usar:
```html
<form class="form-modern">
    <div class="form-group-modern">
        <label class="form-label-modern">Campo Obrigatório</label>
        <input type="text" class="form-control-modern" required>
        <div class="form-help-modern">Texto de ajuda</div>
    </div>

    <div class="form-actions-modern">
        <button type="submit" class="btn btn-primary btn-modern">
            Enviar
        </button>
        <button type="reset" class="btn btn-secondary btn-modern">
            Limpar
        </button>
    </div>
</form>
```

---

## 🎯 Classes Utilitárias

### Badges de Status
```html
<span class="status-badge status-success">Ativo</span>
<span class="status-badge status-warning">Pendente</span>
<span class="status-badge status-danger">Erro</span>
<span class="status-badge status-info">Info</span>
```

### Badges de Prioridade
```html
<span class="priority-badge priority-high">Alta</span>
<span class="priority-badge priority-medium">Média</span>
<span class="priority-badge priority-low">Baixa</span>
```

### Animações
```html
<div class="fade-in">Fade In</div>
<div class="bounce">Bounce</div>
<div class="shake">Shake (para erros)</div>
```

---

## 📱 Responsividade

### Breakpoints Utilizados:
- **Mobile:** < 576px
- **Tablet:** 576px - 991px
- **Desktop:** ≥ 992px

### Estratégias:
- **Mobile First:** Estilos base para mobile, depois desktop
- **Progressive Enhancement:** Funcionalidades adicionais em telas maiores
- **Graceful Degradation:** Fallbacks para dispositivos limitados

---

## 🎨 Variáveis CSS

### Cores Principais:
```css
:root {
    --primary: #008BCD;
    --primary-hover: #0077B6;
    --primary-light: rgba(0, 139, 205, 0.1);
    --success: #28a745;
    --warning: #ffc107;
    --danger: #dc3545;
    --info: #17a2b8;
}
```

### Espaçamentos:
```css
:root {
    --spacing-xs: 0.25rem;
    --spacing-sm: 0.5rem;
    --spacing-md: 1rem;
    --spacing-lg: 1.5rem;
    --spacing-xl: 3rem;
}
```

---

## 🔧 Configuração e Integração

### 1. Arquivos CSS (já incluídos no base.html):
```html
<link rel="stylesheet" href="{{ url_for('static', filename='form-styles.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='modal-styles.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='breadcrumb-styles.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='feedback-styles.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='responsive-tables.css') }}">
<link rel="stylesheet" href="{{ url_for('static', filename='mobile-forms.css') }}">
```

### 2. Arquivos JavaScript (já incluídos no base.html):
```html
<script src="{{ url_for('static', filename='js/modals.js') }}"></script>
<script src="{{ url_for('static', filename='js/breadcrumbs.js') }}"></script>
<script src="{{ url_for('static', filename='js/feedback.js') }}"></script>
```

### 3. Instâncias Globais Disponíveis:
- `window.Modal` - Sistema de modais
- `window.Breadcrumbs` - Sistema de breadcrumbs
- `window.Feedback` - Sistema de feedback
- `showToast()` - Alias para toasts
- `showLoading()` / `hideLoading()` - Aliases para loading

---

## 🧪 Testando os Componentes

### Página de Demonstração:
Acesse `/demo-components` para ver todos os componentes em ação com exemplos interativos.

### Testes Manuais:
1. **Responsividade:** Redimensione a janela do navegador
2. **Modais:** Teste todos os tipos e interações
3. **Formulários:** Valide campos e estados de erro
4. **Tabelas:** Teste em diferentes tamanhos de tela
5. **Toasts:** Verifique posicionamento e animações

---

## 🔮 Próximas Fases

### FASE 3 - Funcionalidades Avançadas:
- [ ] Notificações em tempo real
- [ ] Filtros avançados com tags
- [ ] Dashboard com analytics
- [ ] Exportação de dados

### FASE 4 - Performance:
- [ ] Lazy loading de componentes
- [ ] Cache inteligente
- [ ] Compressão de assets
- [ ] Service Workers (PWA)

### FASE 5 - Segurança e Auditoria:
- [ ] Logs de auditoria
- [ ] Controle de sessão avançado
- [ ] Backup automático
- [ ] Monitoramento de performance

---

## 📞 Suporte

Para dúvidas sobre implementação ou customização dos componentes:

1. **Documentação:** Consulte este guia
2. **Demo:** Use a página `/demo-components`
3. **Código:** Verifique os arquivos fonte comentados
4. **Testes:** Execute em ambiente de desenvolvimento

---

**Desenvolvido com ❤️ para o TI OSN System**  
*Versão 2.0 - Janeiro 2025*
