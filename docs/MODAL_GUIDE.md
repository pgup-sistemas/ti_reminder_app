# 🎨 Guia Completo do Sistema de Modais Modernos

## 📚 Índice
- [Introdução](#introdução)
- [Instalação](#instalação)
- [Uso Básico](#uso-básico)
- [Funções Helper](#funções-helper)
- [Exemplos Práticos](#exemplos-práticos)
- [API Completa](#api-completa)
- [Customização](#customização)
- [Acessibilidade](#acessibilidade)
- [Migração](#migração)

---

## 🎯 Introdução

O Sistema de Modais Modernos do TI OSN substitui completamente os `alert()` e `confirm()` nativos do JavaScript por uma solução profissional, elegante e acessível.

### ✨ Características

- ✅ **Design Moderno** - Visual profissional alinhado com o design system
- ✅ **Totalmente Acessível** - WCAG 2.1 AAA compliant
- ✅ **Responsivo** - Funciona perfeitamente em mobile
- ✅ **Dark Mode** - Suporte automático ao tema escuro
- ✅ **Animações Suaves** - Transições elegantes
- ✅ **Customizável** - Flexível para qualquer necessidade
- ✅ **Promise-based** - API moderna com async/await
- ✅ **Zero Dependências** - Apenas JavaScript vanilla

---

## 🚀 Instalação

### Já Integrado!

O sistema já está completamente integrado no `base.html`. Não é necessário nenhum setup adicional!

**Arquivos carregados automaticamente:**
- `css/modern-modals.css` - Estilos dos modais
- `js/modals.js` - Sistema principal
- `js/modal-helpers.js` - Funções auxiliares

---

## 💡 Uso Básico

### Método 1: Usando Helpers (Recomendado)

```javascript
// Confirmar exclusão
const confirmed = await confirmDelete('Relatório de Vendas', 'relatório');
if (confirmed) {
    // Executar exclusão
}

// Mostrar sucesso
await showSuccess('Usuário criado com sucesso!');

// Mostrar erro
await showError('Não foi possível salvar os dados.');

// Confirmar ação
const result = await confirmAction(
    'Limpar Cache',
    'Isso irá limpar todo o cache do sistema. Continuar?',
    'Sim, Limpar'
);
```

### Método 2: API Completa

```javascript
// Modal customizado
const result = await window.Modal.show({
    type: 'confirm',
    title: 'Confirmar Ação',
    message: 'Deseja realmente executar esta operação?',
    buttons: [
        { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
        { text: 'Confirmar', action: 'confirm', class: 'btn-primary' }
    ]
});

if (result.action === 'confirm') {
    // Executar ação
}
```

---

## 🛠️ Funções Helper

### confirmDelete(itemName, itemType)

Confirma exclusão de um item.

```javascript
const deleted = await confirmDelete('João Silva', 'usuário');
if (deleted) {
    console.log('Item excluído!');
}
```

**Parâmetros:**
- `itemName` (string) - Nome do item
- `itemType` (string) - Tipo do item (padrão: 'item')

**Retorna:** `boolean` - true se confirmado

---

### confirmAction(title, message, confirmText, type)

Confirma ação genérica.

```javascript
const confirmed = await confirmAction(
    'Reprocessar Dados',
    'Isso pode levar alguns minutos. Continuar?',
    'Sim, Reprocessar',
    'warning'
);
```

**Parâmetros:**
- `title` (string) - Título do modal
- `message` (string) - Mensagem
- `confirmText` (string) - Texto do botão (padrão: 'Confirmar')
- `type` (string) - Tipo: info, success, warning, error, confirm

**Retorna:** `boolean` - true se confirmado

---

### showSuccess(message, title)

Mostra mensagem de sucesso.

```javascript
await showSuccess('Dados salvos com sucesso!', 'Sucesso');
```

**Parâmetros:**
- `message` (string) - Mensagem
- `title` (string) - Título (padrão: 'Sucesso!')

---

### showError(message, title)

Mostra mensagem de erro.

```javascript
await showError('Falha ao conectar com o servidor.', 'Erro de Conexão');
```

**Parâmetros:**
- `message` (string) - Mensagem
- `title` (string) - Título (padrão: 'Erro')

---

### showWarning(message, title)

Mostra aviso.

```javascript
await showWarning('Esta ação não pode ser desfeita.', 'Atenção');
```

---

### showInfo(message, title)

Mostra informação.

```javascript
await showInfo('Sistema será atualizado em 5 minutos.', 'Manutenção Agendada');
```

---

### promptInput(question, defaultValue, placeholder, inputType)

Solicita input do usuário.

```javascript
const name = await promptInput(
    'Digite o nome do projeto:',
    '',
    'Ex: Projeto Alpha',
    'text'
);

if (name) {
    console.log('Nome:', name);
}
```

**Parâmetros:**
- `question` (string) - Pergunta/label
- `defaultValue` (string) - Valor padrão
- `placeholder` (string) - Placeholder
- `inputType` (string) - Tipo: text, email, number, etc

**Retorna:** `string|null` - Valor digitado ou null se cancelado

---

### showLoading(message) / hideLoading()

Mostra/esconde loading.

```javascript
showLoading('Processando dados...');

// Executar operação
await fetch('/api/process');

hideLoading();
```

---

### confirmDangerousAction(itemName, warningMessage)

Confirma operação perigosa com aviso destacado.

```javascript
const confirmed = await confirmDangerousAction(
    'Banco de Dados de Produção',
    'Esta ação irá deletar TODOS os dados permanentemente!'
);
```

---

### confirmClearData(dataType, details)

Confirma limpeza de dados.

```javascript
const clear = await confirmClearData(
    'Logs do Sistema',
    'Últimos 30 dias - aproximadamente 2GB'
);
```

---

### showProgress(title, message, estimatedSeconds)

Mostra progresso de operação.

```javascript
showProgress(
    'Otimizando Banco de Dados',
    'Recriando índices...',
    30
);

// Após completar
hideLoading();
```

---

### confirmWithCheckbox(title, message, checkboxLabel)

Confirma com opção de checkbox.

```javascript
const result = await confirmWithCheckbox(
    'Tutorial',
    'Deseja ver o tutorial do sistema?',
    'Não mostrar novamente'
);

if (result.confirmed && result.checkboxValue) {
    localStorage.setItem('hideT tutorial', 'true');
}
```

---

### chooseOption(title, message, options)

Escolhe entre múltiplas opções.

```javascript
const format = await chooseOption(
    'Exportar Dados',
    'Escolha o formato de exportação:',
    [
        { value: 'pdf', label: 'PDF', description: 'Documento em PDF' },
        { value: 'excel', label: 'Excel', description: 'Planilha Excel (.xlsx)' },
        { value: 'csv', label: 'CSV', description: 'Valores separados por vírgula' }
    ]
);

console.log('Formato escolhido:', format);
```

---

## 📖 Exemplos Práticos

### Exemplo 1: Deletar Usuário

```javascript
async function deleteUser(userId, userName) {
    const confirmed = await confirmDelete(userName, 'usuário');
    
    if (confirmed) {
        showLoading('Excluindo usuário...');
        
        try {
            const response = await fetch(`/api/users/${userId}`, {
                method: 'DELETE'
            });
            
            hideLoading();
            
            if (response.ok) {
                await showSuccess(`Usuário "${userName}" excluído com sucesso!`);
                location.reload();
            } else {
                await showError('Erro ao excluir usuário.');
            }
        } catch (error) {
            hideLoading();
            await showError('Erro de conexão com o servidor.');
        }
    }
}
```

### Exemplo 2: Limpar Cache com Confirmação Dupla

```javascript
async function clearSystemCache() {
    const confirmed = await confirmDangerousAction(
        'Cache do Sistema',
        'Limpar o cache pode causar lentidão temporária no sistema!'
    );
    
    if (!confirmed) return;
    
    showProgress('Limpando Cache', 'Aguarde...', 10);
    
    await fetch('/api/cache/clear', { method: 'POST' });
    
    hideLoading();
    await showSuccess('Cache limpo com sucesso!');
}
```

### Exemplo 3: Formulário de Input

```javascript
async function renameProject(projectId, currentName) {
    const newName = await promptInput(
        'Digite o novo nome do projeto:',
        currentName,
        'Nome do projeto',
        'text'
    );
    
    if (newName && newName !== currentName) {
        showLoading('Renomeando...');
        
        await fetch(`/api/projects/${projectId}`, {
            method: 'PATCH',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify({ name: newName })
        });
        
        hideLoading();
        await showSuccess('Projeto renomeado!');
    }
}
```

### Exemplo 4: Exportar com Opções

```javascript
async function exportData() {
    const format = await chooseOption(
        'Exportar Relatório',
        'Escolha o formato desejado:',
        [
            { value: 'pdf', label: 'PDF', description: 'Melhor para impressão' },
            { value: 'xlsx', label: 'Excel', description: 'Editável em planilhas' },
            { value: 'csv', label: 'CSV', description: 'Dados brutos' }
        ]
    );
    
    if (format) {
        showLoading(`Gerando arquivo ${format.toUpperCase()}...`);
        window.location.href = `/api/export?format=${format}`;
        
        setTimeout(hideLoading, 2000);
    }
}
```

---

## 🎨 API Completa

### Modal.show(options)

Método principal para criar modais customizados.

```javascript
const result = await Modal.show({
    type: 'confirm',           // Tipo do modal
    title: 'Título',           // Título
    message: 'Mensagem',       // Conteúdo
    html: true,                // Permite HTML no message
    size: 'medium',            // Tamanho: small, medium, large, xl
    closable: true,            // Botão X para fechar
    backdrop: true,            // Fechar ao clicar fora
    animation: true,           // Animações
    customClass: 'my-modal',   // Classes CSS adicionais
    
    // Callbacks
    onShow: () => {},          // Ao mostrar
    onHide: () => {},          // Ao esconder
    onConfirm: () => {},       // Ao confirmar
    onCancel: () => {},        // Ao cancelar
    
    // Botões customizados
    buttons: [
        {
            text: 'Cancelar',
            action: 'cancel',
            class: 'btn-outline-secondary',
            icon: 'fas fa-times'
        },
        {
            text: 'Confirmar',
            action: 'confirm',
            class: 'btn-primary',
            icon: 'fas fa-check',
            autofocus: true
        }
    ]
});

// Resultado
console.log(result.action);  // 'confirm', 'cancel', 'ok', etc
console.log(result.value);   // true/false/custom
```

### Tipos de Modal

- **info** - Informação (azul)
- **success** - Sucesso (verde)
- **warning** - Aviso (laranja)
- **error** - Erro (vermelho)
- **confirm** - Confirmação (azul sistema)

### Tamanhos

- **small** - 400px
- **medium** - 500px (padrão)
- **large** - 700px
- **xl** - 900px

---

## 🎨 Customização

### Modal com HTML Customizado

```javascript
await Modal.show({
    type: 'info',
    title: 'Informações do Sistema',
    message: `
        <div class="alert alert-info">
            <h6><i class="fas fa-info-circle me-2"></i>Versão</h6>
            <p class="mb-0">TI OSN System v2.0</p>
        </div>
        <ul class="list-unstyled mt-3">
            <li><strong>Servidor:</strong> PostgreSQL 14</li>
            <li><strong>Python:</strong> 3.11</li>
            <li><strong>Framework:</strong> Flask 3.0</li>
        </ul>
    `,
    html: true,
    size: 'large'
});
```

### Modal com Formulário Complexo

```javascript
const result = await Modal.show({
    type: 'confirm',
    title: 'Configurar Notificações',
    message: `
        <div class="mb-3">
            <label class="form-label">Email</label>
            <input type="email" id="emailNotif" class="form-control">
        </div>
        <div class="mb-3">
            <div class="form-check">
                <input type="checkbox" id="pushNotif" class="form-check-input" checked>
                <label class="form-check-label" for="pushNotif">
                    Notificações push
                </label>
            </div>
        </div>
    `,
    html: true,
    buttons: [
        { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
        { text: 'Salvar', action: 'save', class: 'btn-success' }
    ]
});

if (result.action === 'save') {
    const email = document.getElementById('emailNotif').value;
    const push = document.getElementById('pushNotif').checked;
    // Salvar configurações
}
```

---

## ♿ Acessibilidade

O sistema implementa todas as melhores práticas de acessibilidade:

### Recursos Implementados

✅ **Gerenciamento de Foco**
- Foco automático no botão primário
- Trap focus (Tab navega apenas dentro do modal)
- Restauração do foco ao fechar

✅ **Navegação por Teclado**
- `ESC` fecha o modal
- `Tab` navega entre elementos
- `Enter` confirma ação

✅ **ARIA**
- `role="dialog"`
- `aria-modal="true"`
- Labels adequados

✅ **Screen Readers**
- Anúncios automáticos
- Descrições claras

✅ **Reduced Motion**
- Respeita `prefers-reduced-motion`
- Sem animações se configurado

✅ **High Contrast**
- Bordas visíveis em modo alto contraste

---

## 🔄 Migração

### De `confirm()` para Modal

**Antes:**
```javascript
if (confirm('Deseja excluir?')) {
    deleteItem();
}
```

**Depois:**
```javascript
const confirmed = await confirmAction('Excluir Item', 'Deseja excluir?');
if (confirmed) {
    deleteItem();
}
```

### De `alert()` para Modal

**Antes:**
```javascript
alert('Operação concluída!');
```

**Depois:**
```javascript
await showSuccess('Operação concluída!');
```

### De `prompt()` para Modal

**Antes:**
```javascript
const name = prompt('Digite o nome:');
if (name) {
    saveName(name);
}
```

**Depois:**
```javascript
const name = await promptInput('Digite o nome:');
if (name) {
    saveName(name);
}
```

---

## 📋 Checklist de Migração

Use este checklist para migrar páginas:

- [ ] Identificar todos `confirm()` na página
- [ ] Identificar todos `alert()` na página
- [ ] Identificar todos `prompt()` na página
- [ ] Substituir por funções helper apropriadas
- [ ] Testar todos os fluxos
- [ ] Testar navegação por teclado
- [ ] Testar em mobile
- [ ] Testar em dark mode

---

## 💡 Dicas e Boas Práticas

### 1. Use Helpers quando possível

```javascript
// ❌ Não faça isso
Modal.show({
    type: 'error',
    title: 'Erro',
    message: 'Algo deu errado',
    buttons: [{ text: 'OK', action: 'ok', class: 'btn-danger' }]
});

// ✅ Faça isso
showError('Algo deu errado');
```

### 2. Sempre use async/await

```javascript
// ✅ Correto
async function deleteUser() {
    const confirmed = await confirmDelete('João');
    if (confirmed) {
        // deletar
    }
}

// ❌ Evite callbacks
confirmDelete('João').then(confirmed => {
    if (confirmed) {
        // deletar
    }
});
```

### 3. Forneça contexto adequado

```javascript
// ❌ Vago
confirmDelete('Item');

// ✅ Específico
confirmDelete('Relatório de Vendas Q4 2024', 'relatório');
```

### 4. Use loading para operações longas

```javascript
async function processData() {
    showLoading('Processando 1000 registros...');
    
    await heavyOperation();
    
    hideLoading();
    await showSuccess('Processamento concluído!');
}
```

---

## 🐛 Troubleshooting

### Modal não aparece

**Problema:** Modal não é exibido.

**Solução:**
1. Verifique se `modals.js` está carregado
2. Verifique console por erros
3. Confirme que está usando `await` ou `.then()`

### Foco não funciona

**Problema:** Foco não vai para o modal.

**Solução:**
- Aguarde 100-200ms após abrir
- Verifique se há outros modais abertos

### Estilo incorreto

**Problema:** Modal aparece sem estilo.

**Solução:**
1. Verifique se `modern-modals.css` está carregado
2. Limpe o cache do navegador
3. Verifique ordem de carregamento dos CSS

---

## 📞 Suporte

Para dúvidas ou problemas:

1. Consulte este guia
2. Verifique os exemplos em `/docs/examples/`
3. Contate a equipe de desenvolvimento

---

## 📝 Changelog

### v2.0 (2025-01-22)
- ✨ Sistema completo de modals modernos
- ✨ 10+ funções helper
- ✨ Suporte total a acessibilidade
- ✨ Dark mode automático
- ✨ Animações suaves
- ✨ API promise-based

---

**Desenvolvido com ❤️ para TI OSN System**
