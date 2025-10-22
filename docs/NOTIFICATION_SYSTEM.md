# 📚 SISTEMA DE NOTIFICAÇÕES - GUIA DE USO

**TI OSN System - Sistema Unificado de Toasts**  
**Versão:** 1.0  
**Atualizado:** 22 de Outubro de 2025

---

## 📋 Índice

1. [Visão Geral](#visão-geral)
2. [Uso no Backend (Python/Flask)](#uso-no-backend)
3. [Uso no Frontend (JavaScript)](#uso-no-frontend)
4. [Exemplos Práticos](#exemplos-práticos)
5. [Opções Avançadas](#opções-avançadas)
6. [Boas Práticas](#boas-práticas)
7. [Troubleshooting](#troubleshooting)

---

## 🎯 Visão Geral

O sistema de notificações foi unificado para oferecer uma experiência consistente em todo o aplicativo. Todas as notificações são exibidas como **toasts modernos** que aparecem no canto superior direito (desktop) ou na parte superior (mobile).

### Características
- ✅ Auto-dismiss configurável
- ✅ Progress bar visual
- ✅ 4 tipos: success, error, warning, info
- ✅ Totalmente responsivo
- ✅ Dark mode automático
- ✅ Acessível (WCAG AA)

---

## 🐍 Uso no Backend

### Importação
```python
from app.utils import flash_success, flash_error, flash_warning, flash_info
```

### Notificação de Sucesso
```python
# Simples
flash_success("Usuário cadastrado com sucesso!")

# Com título personalizado
flash_success("Dados foram salvos no sistema.", title="Concluído")
```

### Notificação de Erro
```python
# Simples
flash_error("Não foi possível salvar os dados.")

# Com título personalizado
flash_error("Verifique sua conexão.", title="Erro de Rede")
```

### Notificação de Aviso
```python
# Simples
flash_warning("Alguns campos estão incompletos.")

# Com título
flash_warning("Prazo próximo do vencimento!", title="Aviso Importante")
```

### Notificação Informativa
```python
# Simples
flash_info("Nova atualização disponível.")

# Com título
flash_info("Sistema será atualizado amanhã às 02:00.", title="Manutenção Programada")
```

### Exemplo Completo em Rota
```python
@app.route('/usuario/novo', methods=['POST'])
def criar_usuario():
    try:
        # Validação
        if not request.form.get('email'):
            flash_error("O campo email é obrigatório.")
            return redirect(url_for('formulario'))
        
        # Criar usuário
        usuario = User(...)
        db.session.add(usuario)
        db.session.commit()
        
        flash_success("Usuário criado com sucesso!", title="Cadastro Completo")
        return redirect(url_for('listar_usuarios'))
        
    except Exception as e:
        db.session.rollback()
        flash_error(f"Erro ao criar usuário: {str(e)}")
        return redirect(url_for('formulario'))
```

---

## 💻 Uso no Frontend

### API Principal

#### Toasts Simples
```javascript
// Sucesso
Feedback.success('Título', 'Mensagem de sucesso');

// Erro
Feedback.error('Título', 'Mensagem de erro');

// Aviso
Feedback.warning('Título', 'Mensagem de aviso');

// Informação
Feedback.info('Título', 'Mensagem informativa');
```

#### Toast Genérico
```javascript
Feedback.toast(type, title, message, options);

// Exemplo
Feedback.toast('success', 'Salvo!', 'Dados foram salvos', {
    duration: 5000,
    closable: true
});
```

#### Loading Overlay
```javascript
// Mostrar loading
const loadingId = Feedback.showLoading(elemento, {
    message: 'Carregando dados...',
    size: 'medium'
});

// Esconder loading
Feedback.hideLoading(loadingId);
```

#### Confirmação
```javascript
Feedback.confirm('Título', 'Tem certeza?', () => {
    // Usuário confirmou
    console.log('Ação confirmada');
});
```

### Aliases Disponíveis

```javascript
// Alias simples
notify('success', 'Título', 'Mensagem');

// Compatibilidade legada
showToast('success', 'Título', 'Mensagem');
```

---

## 💡 Exemplos Práticos

### Exemplo 1: Formulário com Validação
```javascript
const form = document.getElementById('meuForm');

form.addEventListener('submit', async (e) => {
    e.preventDefault();
    
    // Validar
    const nome = form.querySelector('#nome').value;
    if (!nome.trim()) {
        Feedback.error('Validação', 'O campo nome é obrigatório');
        return;
    }
    
    // Mostrar loading
    const loadingId = Feedback.showLoading(form);
    
    try {
        const response = await fetch('/api/salvar', {
            method: 'POST',
            body: new FormData(form)
        });
        
        const data = await response.json();
        
        Feedback.hideLoading(loadingId);
        
        if (response.ok) {
            Feedback.success('Sucesso!', 'Dados salvos com sucesso');
            form.reset();
        } else {
            Feedback.error('Erro', data.message || 'Falha ao salvar');
        }
    } catch (error) {
        Feedback.hideLoading(loadingId);
        Feedback.error('Erro de Rede', 'Verifique sua conexão');
    }
});
```

### Exemplo 2: Deletar com Confirmação
```javascript
function deletarItem(id) {
    Feedback.confirm(
        'Confirmar Exclusão',
        'Tem certeza que deseja excluir este item?',
        async () => {
            const loadingId = Feedback.showLoading(document.body);
            
            try {
                const response = await fetch(`/api/item/${id}`, {
                    method: 'DELETE'
                });
                
                Feedback.hideLoading(loadingId);
                
                if (response.ok) {
                    Feedback.success('Excluído!', 'Item removido com sucesso');
                    // Recarregar lista
                    carregarLista();
                } else {
                    Feedback.error('Erro', 'Não foi possível excluir');
                }
            } catch (error) {
                Feedback.hideLoading(loadingId);
                Feedback.error('Erro', error.message);
            }
        }
    );
}
```

### Exemplo 3: Upload de Arquivo
```javascript
async function uploadArquivo(file) {
    const formData = new FormData();
    formData.append('file', file);
    
    const loadingId = Feedback.showLoading(document.body, {
        message: `Enviando ${file.name}...`
    });
    
    try {
        const response = await fetch('/api/upload', {
            method: 'POST',
            body: formData
        });
        
        Feedback.hideLoading(loadingId);
        
        if (response.ok) {
            Feedback.success('Upload', 'Arquivo enviado com sucesso!');
        } else {
            Feedback.error('Falha', 'Não foi possível enviar o arquivo');
        }
    } catch (error) {
        Feedback.hideLoading(loadingId);
        Feedback.error('Erro de Rede', 'Verifique sua conexão');
    }
}
```

---

## ⚙️ Opções Avançadas

### Configurações de Toast
```javascript
Feedback.toast('success', 'Título', 'Mensagem', {
    duration: 5000,        // Duração em ms (0 = não fecha automaticamente)
    closable: true,        // Mostrar botão fechar
    position: 'top-right', // Posição (futuro)
    actions: [             // Botões de ação
        {
            text: 'Desfazer',
            action: 'undo',
            icon: 'fas fa-undo'
        },
        {
            text: 'Ver Detalhes',
            action: 'view',
            icon: 'fas fa-eye'
        }
    ]
});
```

### Configurações de Loading
```javascript
Feedback.showLoading(elemento, {
    message: 'Carregando...',
    spinner: 'default',    // default, dots, pulse, bars
    backdrop: true,        // Overlay escuro
    size: 'medium'         // small, medium, large
});
```

### Toast com Ações
```javascript
const toastId = Feedback.toast('info', 'Atualização', 'Nova versão disponível', {
    duration: 0,  // Não fechar automaticamente
    closable: true,
    actions: [
        {
            text: 'Atualizar Agora',
            action: 'update'
        },
        {
            text: 'Depois',
            action: 'later'
        }
    ]
});

// Lidar com ações
document.addEventListener('click', (e) => {
    const action = e.target.dataset.action;
    if (action === 'update') {
        window.location.reload();
    } else if (action === 'later') {
        Feedback.removeToast(toastId);
    }
});
```

---

## ✨ Boas Práticas

### 1. Escolha o Tipo Correto
```javascript
// ✅ BOM
Feedback.success('Salvo!', 'Dados salvos com sucesso');
Feedback.error('Erro!', 'Falha ao salvar dados');

// ❌ EVITAR
Feedback.info('Erro!', 'Falha ao salvar');  // Tipo errado
```

### 2. Mensagens Claras e Concisas
```javascript
// ✅ BOM
Feedback.success('Usuário Criado', 'O usuário foi cadastrado com sucesso');

// ❌ EVITAR
Feedback.success('OK', 'A operação de criação do usuário no banco de dados foi executada com sucesso e todos os dados foram persistidos corretamente');
```

### 3. Use Loading para Operações Assíncronas
```javascript
// ✅ BOM
const loadingId = Feedback.showLoading(form);
await salvarDados();
Feedback.hideLoading(loadingId);
Feedback.success('Salvo!', 'Dados salvos');

// ❌ EVITAR
await salvarDados();  // Sem feedback visual
Feedback.success('Salvo!', 'Dados salvos');
```

### 4. Confirmação para Ações Destrutivas
```javascript
// ✅ BOM
Feedback.confirm('Excluir', 'Tem certeza?', () => {
    excluirItem();
});

// ❌ EVITAR
excluirItem();  // Sem confirmação
```

### 5. Trate Erros Adequadamente
```javascript
// ✅ BOM
try {
    await operacao();
    Feedback.success('Sucesso!', 'Operação concluída');
} catch (error) {
    Feedback.error('Erro', error.message || 'Algo deu errado');
}

// ❌ EVITAR
await operacao();  // Sem tratamento de erro
Feedback.success('Sucesso!', 'Operação concluída');
```

---

## 🐛 Troubleshooting

### Toast não aparece

**Problema:** O toast não é exibido após chamar Feedback.success()

**Soluções:**
1. Verificar se `feedback.js` está carregado:
   ```javascript
   console.log(window.Feedback);  // Deve exibir o objeto
   ```

2. Verificar erros no console do navegador

3. Verificar se o CSS está carregado:
   ```javascript
   const hasCSS = document.querySelector('link[href*="toast-notifications.css"]');
   console.log(hasCSS);
   ```

### Flash messages não convertendo

**Problema:** Mensagens flash do Flask aparecem como alerts antigos

**Soluções:**
1. Verificar se `flash-to-toast-adapter.js` está carregado
2. Verificar ordem de scripts no `base.html`:
   - `feedback.js` deve carregar antes do adapter
3. Verificar console para erros

### Progress bar não anima

**Problema:** A barra de progresso não se move

**Solução:**
```css
/* Verificar se a animação está definida no CSS */
@keyframes progressBar {
    from { width: 100%; }
    to { width: 0%; }
}
```

### Toasts não fecham automaticamente

**Problema:** Toasts ficam visíveis indefinidamente

**Solução:**
Verificar se a duração está sendo passada:
```javascript
// Com duração
Feedback.success('Título', 'Mensagem', { duration: 4000 });

// Sem duração (não fecha automaticamente)
Feedback.success('Título', 'Mensagem', { duration: 0 });
```

### Múltiplos toasts sobrepostos

**Problema:** Toasts aparecem uns sobre os outros

**Solução:**
Verificar CSS do container:
```css
.toast-container {
    display: flex;
    flex-direction: column;
    gap: 12px;
}
```

---

## 📞 Suporte

Para questões ou problemas:
1. Consultar esta documentação
2. Verificar `ANALISE_SISTEMA_NOTIFICACOES.md`
3. Verificar `SISTEMA_NOTIFICACOES_IMPLEMENTADO.md`
4. Contatar equipe de desenvolvimento

---

*Última atualização: 22 de Outubro de 2025*
