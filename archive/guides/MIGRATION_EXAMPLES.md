# 🔄 Exemplos de Migração - Sistema de Modais

Este documento demonstra como migrar os `confirm()` e `alert()` nativos para o novo sistema de modais profissionais.

---

## 📋 Exemplo 1: Users.html - Deletar Usuário

### ❌ Código Antigo (Inline onclick)

```html
<button type="submit" class="btn btn-sm btn-danger" title="Excluir"
  onclick="return confirm('Tem certeza que deseja excluir este usuário? Esta ação não pode ser desfeita.');">
  <i class="fas fa-trash"></i>
</button>
```

### ✅ Código Novo (Com Modal Moderno)

**HTML:**
```html
<button type="button" 
        class="btn btn-sm btn-danger" 
        title="Excluir"
        onclick="deleteUser({{ user.id }}, '{{ user.username }}')">
  <i class="fas fa-trash"></i>
</button>
```

**JavaScript:**
```javascript
async function deleteUser(userId, username) {
    const confirmed = await confirmDelete(username, 'usuário');
    
    if (confirmed) {
        // Criar formulário e submeter
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/users/${userId}/delete`;
        document.body.appendChild(form);
        form.submit();
    }
}
```

---

## 📋 Exemplo 2: Users.html - Reset de Senha

### ❌ Código Antigo

```html
<button type="submit" class="btn btn-sm btn-primary" title="Redefinir Senha"
  onclick="return confirm('Tem certeza que deseja redefinir a senha deste usuário? Uma nova senha será gerada e exibida na tela.');">
  <i class="fas fa-key"></i>
</button>
```

### ✅ Código Novo

**HTML:**
```html
<button type="button" 
        class="btn btn-sm btn-primary" 
        title="Redefinir Senha"
        onclick="resetUserPassword({{ user.id }}, '{{ user.username }}')">
  <i class="fas fa-key"></i>
</button>
```

**JavaScript:**
```javascript
async function resetUserPassword(userId, username) {
    const confirmed = await confirmAction(
        'Redefinir Senha',
        `Deseja redefinir a senha do usuário <strong>${username}</strong>?<br><br>
        <small class="text-muted">Uma nova senha temporária será gerada.</small>`,
        'Redefinir',
        'warning'
    );
    
    if (confirmed) {
        showLoading('Redefinindo senha...');
        
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/admin/users/${userId}/reset-password`;
        document.body.appendChild(form);
        form.submit();
    }
}
```

---

## 📋 Exemplo 3: Reminders.html - Finalizar Lembrete

### ❌ Código Antigo

```html
<button onclick="return confirm('Deseja marcar este lembrete como concluído?');">
    <i class="fas fa-check"></i>
</button>
```

### ✅ Código Novo

**HTML:**
```html
<button type="button" onclick="completeReminder(${reminder.id}, '${reminder.titulo}')">
    <i class="fas fa-check"></i>
</button>
```

**JavaScript:**
```javascript
async function completeReminder(reminderId, titulo) {
    const confirmed = await Modal.show({
        type: 'success',
        title: 'Finalizar Lembrete',
        message: `Marcar o lembrete "<strong>${titulo}</strong>" como concluído?`,
        html: true,
        buttons: [
            { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
            { text: 'Finalizar', action: 'confirm', class: 'btn-success', icon: 'fas fa-check' }
        ]
    });
    
    if (confirmed.action === 'confirm') {
        const form = document.createElement('form');
        form.method = 'POST';
        form.action = `/lembretes/${reminderId}/finalizar`;
        document.body.appendChild(form);
        form.submit();
    }
}
```

---

## 📋 Exemplo 4: System Logs - Limpar Logs

### ❌ Código Antigo

```javascript
function clearTerminal() {
    if (confirm('Limpar todos os logs do terminal? Esta ação não afeta os logs salvos.')) {
        document.getElementById('logContainer').innerHTML = '';
        updateLogCount();
    }
}
```

### ✅ Código Novo

```javascript
async function clearTerminal() {
    const confirmed = await confirmClearData(
        'Logs do Terminal',
        'Esta ação não afeta os logs salvos no banco de dados'
    );
    
    if (confirmed) {
        showLoading('Limpando terminal...');
        
        document.getElementById('logContainer').innerHTML = '';
        updateLogCount();
        
        hideLoading();
        await showSuccess('Terminal limpo com sucesso!');
    }
}
```

---

## 📋 Exemplo 5: RFID - Remover Leitor

### ❌ Código Antigo

```javascript
function removeReader(readerId) {
    if (confirm(`Remover o leitor ${readerId}?\n\nEsta ação irá:\n- Desconectar o dispositivo\n- Remover todas as associações\n- Parar o monitoramento da zona\n\nEsta ação não pode ser desfeita.`)) {
        alert(`Leitor ${readerId} removido com sucesso!`);
        event.target.closest('tr').remove();
    }
}
```

### ✅ Código Novo

```javascript
async function removeReader(readerId) {
    const confirmed = await confirmDangerousAction(
        `Leitor ${readerId}`,
        `Esta ação irá:
        <ul class="mb-0">
            <li>Desconectar o dispositivo</li>
            <li>Remover todas as associações</li>
            <li>Parar o monitoramento da zona</li>
        </ul>`
    );
    
    if (confirmed) {
        showLoading('Removendo leitor...');
        
        // Simulação de requisição
        await new Promise(resolve => setTimeout(resolve, 1000));
        
        event.target.closest('tr').remove();
        
        hideLoading();
        await showSuccess(`Leitor ${readerId} removido com sucesso!`);
    }
}
```

---

## 📋 Exemplo 6: Performance - Limpar Cache

### ❌ Código Antigo

```javascript
function clearCache() {
    if (confirm('Limpar cache do sistema?\n\n• Cache de queries\n• Cache de templates\n• Cache de sessões\n\nIsso pode causar lentidão temporária.')) {
        executeOptimization('clearCache', 'Limpando cache...', 2000, 'Cache limpo com sucesso!\nLiberação: ~150MB de memória');
    }
}
```

### ✅ Código Novo

```javascript
async function clearCache() {
    const confirmed = await Modal.show({
        type: 'warning',
        title: 'Limpar Cache do Sistema',
        message: `
            <p>Esta ação irá limpar:</p>
            <ul>
                <li>Cache de queries</li>
                <li>Cache de templates</li>
                <li>Cache de sessões</li>
            </ul>
            <div class="alert alert-warning mb-0">
                <small><i class="fas fa-exclamation-triangle me-2"></i>
                Pode causar lentidão temporária no sistema.</small>
            </div>
        `,
        html: true,
        size: 'medium',
        buttons: [
            { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
            { text: 'Limpar Cache', action: 'confirm', class: 'btn-warning', icon: 'fas fa-broom' }
        ]
    });
    
    if (confirmed.action === 'confirm') {
        showProgress('Limpando Cache', 'Aguarde enquanto o cache é limpo...', 3);
        
        await executeOptimization('clearCache');
        
        hideLoading();
        await showSuccess('Cache limpo com sucesso!<br><small>Liberação: ~150MB de memória</small>');
    }
}
```

---

## 📋 Exemplo 7: Notification Templates - Enviar Teste

### ❌ Código Antigo

```javascript
function sendTestEmail(templateId) {
    const templateName = templates[templateId] || templateId;
    
    if (confirm(`Enviar email de teste usando o template "${templateName}"?\n\nO email será enviado para: admin@tiosn.com`)) {
        alert(`Email de teste enviado com sucesso!\n\nTemplate: ${templateName}\nDestinatário: admin@tiosn.com\nStatus: Enviado`);
    }
}
```

### ✅ Código Novo

```javascript
async function sendTestEmail(templateId) {
    const templateName = templates[templateId] || templateId;
    
    const confirmed = await Modal.show({
        type: 'confirm',
        title: 'Enviar Email de Teste',
        message: `
            <p>Enviar email de teste usando o template:</p>
            <div class="alert alert-info">
                <strong>${templateName}</strong>
            </div>
            <p class="mb-0">
                <small class="text-muted">
                    <i class="fas fa-envelope me-2"></i>
                    Será enviado para: <strong>admin@tiosn.com</strong>
                </small>
            </p>
        `,
        html: true,
        buttons: [
            { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
            { text: 'Enviar Teste', action: 'confirm', class: 'btn-primary', icon: 'fas fa-paper-plane' }
        ]
    });
    
    if (confirmed.action === 'confirm') {
        showLoading('Enviando email de teste...');
        
        // Simulação de envio
        await new Promise(resolve => setTimeout(resolve, 1500));
        
        hideLoading();
        await showSuccess(`
            <strong>Email enviado com sucesso!</strong><br><br>
            <small>
                <strong>Template:</strong> ${templateName}<br>
                <strong>Destinatário:</strong> admin@tiosn.com<br>
                <strong>Status:</strong> Enviado
            </small>
        `);
    }
}
```

---

## 📋 Exemplo 8: Bulk Actions - Selecionar Múltiplos

### ❌ Código Antigo

```javascript
function deleteSelected() {
    const selected = getSelectedItems();
    if (selected.length === 0) {
        alert('Selecione pelo menos um item.');
        return;
    }
    
    if (confirm(`Excluir ${selected.length} item(ns) selecionado(s)?`)) {
        // Executar exclusão
    }
}
```

### ✅ Código Novo

```javascript
async function deleteSelected() {
    const selected = getSelectedItems();
    
    if (selected.length === 0) {
        await showWarning('Selecione pelo menos um item para excluir.');
        return;
    }
    
    const confirmed = await Modal.show({
        type: 'error',
        title: 'Excluir Múltiplos Itens',
        message: `
            <div class="alert alert-danger">
                <h6 class="alert-heading">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    Atenção!
                </h6>
                <p class="mb-0">Você está prestes a excluir <strong>${selected.length}</strong> item(ns).</p>
            </div>
            <p class="text-danger mb-0">
                <small>Esta ação não pode ser desfeita!</small>
            </p>
        `,
        html: true,
        buttons: [
            { text: 'Cancelar', action: 'cancel', class: 'btn-outline-secondary' },
            { 
                text: `Excluir ${selected.length} item(ns)`, 
                action: 'confirm', 
                class: 'btn-danger',
                icon: 'fas fa-trash-alt'
            }
        ]
    });
    
    if (confirmed.action === 'confirm') {
        showProgress('Excluindo Itens', `Excluindo ${selected.length} item(ns)...`, selected.length * 2);
        
        // Executar exclusão
        await deleteItems(selected);
        
        hideLoading();
        await showSuccess(`${selected.length} item(ns) excluído(s) com sucesso!`);
        location.reload();
    }
}
```

---

## 📋 Exemplo 9: Formulário com Validação

### ❌ Código Antigo

```javascript
function saveForm() {
    const name = document.getElementById('name').value;
    
    if (!name) {
        alert('Por favor, preencha o nome.');
        return;
    }
    
    if (confirm('Salvar as alterações?')) {
        // Salvar
    }
}
```

### ✅ Código Novo

```javascript
async function saveForm() {
    const name = document.getElementById('name').value;
    
    if (!name) {
        await showError(
            'O campo <strong>Nome</strong> é obrigatório.',
            'Validação'
        );
        document.getElementById('name').focus();
        return;
    }
    
    const confirmed = await confirmAction(
        'Salvar Alterações',
        'Deseja salvar as alterações realizadas?'
    );
    
    if (confirmed) {
        showLoading('Salvando...');
        
        try {
            await fetch('/api/save', {
                method: 'POST',
                body: JSON.stringify({ name }),
                headers: { 'Content-Type': 'application/json' }
            });
            
            hideLoading();
            await showSuccess('Dados salvos com sucesso!');
            location.reload();
        } catch (error) {
            hideLoading();
            await showError('Erro ao salvar dados: ' + error.message);
        }
    }
}
```

---

## 📋 Exemplo 10: Com Opções Personalizadas

### ✅ Exportar com Escolha de Formato

```javascript
async function exportReport() {
    const format = await chooseOption(
        'Exportar Relatório',
        'Escolha o formato desejado:',
        [
            { 
                value: 'pdf', 
                label: 'PDF', 
                description: 'Documento para impressão' 
            },
            { 
                value: 'xlsx', 
                label: 'Excel', 
                description: 'Planilha editável' 
            },
            { 
                value: 'csv', 
                label: 'CSV', 
                description: 'Valores separados por vírgula' 
            }
        ]
    );
    
    if (format) {
        showLoading(`Gerando ${format.toUpperCase()}...`);
        
        window.location.href = `/api/export?format=${format}`;
        
        setTimeout(() => {
            hideLoading();
            showSuccess(`Relatório ${format.toUpperCase()} gerado!`);
        }, 2000);
    }
}
```

---

## 🎯 Padrões de Migração Rápida

### Padrão 1: Simples Confirm → confirmDelete

```javascript
// Antes
if (confirm('Deletar?')) { /* ação */ }

// Depois
if (await confirmDelete(itemName, 'item')) { /* ação */ }
```

### Padrão 2: Confirm com Mensagem → confirmAction

```javascript
// Antes
if (confirm('Tem certeza?')) { /* ação */ }

// Depois
if (await confirmAction('Título', 'Tem certeza?')) { /* ação */ }
```

### Padrão 3: Alert Simples → showSuccess/Error/Warning

```javascript
// Antes
alert('Sucesso!');

// Depois
await showSuccess('Sucesso!');
```

### Padrão 4: Prompt → promptInput

```javascript
// Antes
const value = prompt('Digite:');
if (value) { /* usar */ }

// Depois
const value = await promptInput('Digite:');
if (value) { /* usar */ }
```

---

## ✅ Checklist de Migração por Arquivo

### Para cada arquivo HTML/JS:

1. [ ] Identificar todos `confirm()`
2. [ ] Identificar todos `alert()`
3. [ ] Identificar todos `prompt()`
4. [ ] Escolher helper apropriado
5. [ ] Substituir inline `onclick` por função
6. [ ] Adicionar `async/await`
7. [ ] Testar funcionalidade
8. [ ] Testar keyboard navigation
9. [ ] Testar em mobile
10. [ ] Remover código antigo

---

## 🎨 Benefícios da Migração

### Antes (Confirm Nativo):
- ❌ Visual antiquado
- ❌ Sem customização
- ❌ Bloqueante
- ❌ Sem acessibilidade
- ❌ Sem dark mode
- ❌ Sem animações

### Depois (Modal Moderno):
- ✅ Visual profissional
- ✅ Totalmente customizável
- ✅ Promise-based
- ✅ 100% acessível
- ✅ Dark mode automático
- ✅ Animações suaves

---

**Migração criada para TI OSN System v2.0**
