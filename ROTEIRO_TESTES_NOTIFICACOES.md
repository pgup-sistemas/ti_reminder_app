# 🧪 ROTEIRO DE TESTES - SISTEMA DE NOTIFICAÇÕES
**Do Login ao Logout - Validação Completa**

---

## 🚀 PREPARAÇÃO

### 1. Iniciar o Servidor
```bash
cd c:\Users\Oezios Normando\Documents\tireminderapp
python run.py
```

### 2. Abrir Navegador
- URL: `http://localhost:5000` ou `http://127.0.0.1:5000`
- Abrir DevTools (F12) → Console
- Verificar: **Sem erros no console**

---

## 📋 ROTEIRO DE TESTES

### ✅ **TESTE 1: LOGIN**

#### 1.1. Tentar Login com Credenciais Inválidas
**Ação:**
1. Acessar página de login
2. Digite usuário/senha incorretos
3. Clicar em "Login"

**Resultado Esperado:**
- 🎯 Toast VERMELHO (erro) aparece no canto superior direito
- 📝 Título: "Erro"
- 📝 Mensagem: Algo relacionado a credenciais inválidas
- ⏱️ Toast desaparece após 8 segundos
- ❌ Não é um alert() do navegador
- ❌ Não é uma div de bootstrap no meio da tela

#### 1.2. Login com Credenciais Válidas
**Ação:**
1. Digite usuário e senha corretos
2. Clicar em "Login"

**Resultado Esperado:**
- 🎯 Toast VERDE (sucesso) aparece
- 📝 Título: "Sucesso"
- 📝 Mensagem: "Login realizado com sucesso!"
- ⏱️ Toast desaparece após 4 segundos
- ✅ Redirecionado para dashboard/index

**Screenshot:**
```
┌─────────────────────────────────┐
│  ✓  Sucesso                  × │
│  Login realizado com sucesso!  │
│  ▓▓▓▓▓▓░░░░░░░░░░░░░░░░        │
└─────────────────────────────────┘
```

---

### ✅ **TESTE 2: LEMBRETES**

#### 2.1. Criar Lembrete
**Ação:**
1. Navegar para "Atividades" → "Lembretes"
2. Clicar em "Novo Lembrete"
3. Preencher formulário
4. Clicar em "Salvar"

**Resultado Esperado:**
- 🎯 Toast VERDE (sucesso)
- 📝 "Lembrete cadastrado com sucesso!"
- ⏱️ Desaparece após 4 segundos

#### 2.2. Tentar Criar Lembrete sem Campos Obrigatórios
**Ação:**
1. Clicar em "Novo Lembrete"
2. Deixar campos obrigatórios vazios
3. Clicar em "Salvar"

**Resultado Esperado:**
- 🎯 Toast VERMELHO ou validação do navegador
- 📝 Mensagem indicando campos obrigatórios

#### 2.3. Editar Lembrete
**Ação:**
1. Clicar em "Editar" em um lembrete
2. Modificar algo
3. Salvar

**Resultado Esperado:**
- 🎯 Toast VERDE
- 📝 "Lembrete atualizado!"

#### 2.4. Marcar Lembrete como Realizado
**Ação:**
1. Clicar no botão de "Marcar como Realizado"

**Resultado Esperado:**
- 🎯 Toast VERDE
- 📝 "Lembrete marcado como realizado!"

#### 2.5. Pausar Lembrete
**Ação:**
1. Clicar em "Pausar" em um lembrete ativo

**Resultado Esperado:**
- 🎯 Toast AMARELO (warning)
- 📝 "Lembrete pausado!"

#### 2.6. Cancelar Lembrete
**Ação:**
1. Clicar em "Cancelar" em um lembrete

**Resultado Esperado:**
- 🎯 Toast VERMELHO
- 📝 "Lembrete cancelado!"

#### 2.7. Deletar Lembrete
**Ação:**
1. Clicar em "Excluir" em um lembrete
2. Confirmar exclusão

**Resultado Esperado:**
- 🎯 Toast VERDE
- 📝 "Lembrete excluído!"

---

### ✅ **TESTE 3: TAREFAS**

#### 3.1. Criar Nova Tarefa
**Ação:**
1. Ir em "Atividades" → "Tarefas"
2. Criar nova tarefa
3. Salvar

**Resultado Esperado:**
- 🎯 Toast VERDE
- 📝 Mensagem de sucesso

#### 3.2. Editar Tarefa
**Resultado Esperado:**
- 🎯 Toast VERDE após salvar

#### 3.3. Excluir Tarefa
**Resultado Esperado:**
- 🎯 Toast VERDE
- 📝 Confirmação de exclusão

---

### ✅ **TESTE 4: CHAMADOS (SUPORTE)**

#### 4.1. Abrir Novo Chamado
**Ação:**
1. Navegar para "Suporte" → "Abrir Chamado"
2. Preencher formulário
3. Enviar

**Resultado Esperado:**
- 🎯 Toast VERDE
- 📝 "Chamado aberto com sucesso!"
- 🎯 Possível toast AZUL (info) sobre notificações enviadas

#### 4.2. Tentar Abrir Chamado sem Dados
**Resultado Esperado:**
- 🎯 Toast VERMELHO ou validação

#### 4.3. Editar Chamado
**Ação:**
1. Ir em "Meus Chamados"
2. Editar um chamado existente
3. Salvar

**Resultado Esperado:**
- 🎯 Toast VERDE
- 📝 "Chamado atualizado com sucesso!"

#### 4.4. Adicionar Comentário no Chamado
**Resultado Esperado:**
- 🎯 Toast VERDE após adicionar

---

### ✅ **TESTE 5: EQUIPAMENTOS** (Se tiver permissão)

#### 5.1. Solicitar Equipamento
**Ação:**
1. Ir em "Equipamentos" → "Solicitar Equipamento"
2. Escolher equipamento
3. Preencher datas
4. Enviar solicitação

**Resultado Esperado:**
- 🎯 Toast VERDE
- 📝 "Solicitação enviada com sucesso! Aguarde aprovação da equipe de TI."

#### 5.2. Tentar Solicitar com Data Inválida
**Ação:**
1. Escolher data no passado

**Resultado Esperado:**
- 🎯 Toast VERMELHO
- 📝 "Data e horário de início não podem ser no passado!"

#### 5.3. Ver Minhas Solicitações
**Ação:**
1. Ir em "Minhas Solicitações"

**Resultado Esperado:**
- Lista de solicitações carregada sem erros

---

### ✅ **TESTE 6: ADMINISTRAÇÃO** (Apenas Admin)

#### 6.1. Criar Usuário
**Ação:**
1. "Administração" → "Gerenciar Usuários"
2. "Novo Usuário"
3. Preencher dados
4. Salvar

**Resultado Esperado:**
- 🎯 Toast VERDE
- 📝 "Usuário criado com sucesso!"

#### 6.2. Tentar Criar com Email Duplicado
**Resultado Esperado:**
- 🎯 Toast VERMELHO
- 📝 "Este email já está em uso."

#### 6.3. Editar Usuário
**Ação:**
1. Editar usuário existente
2. Modificar dados
3. Salvar

**Resultado Esperado:**
- 🎯 Toast VERDE
- 📝 "Usuário atualizado com sucesso!"

#### 6.4. Tentar Remover Privilégios do Último Admin
**Ação:**
1. Editar o único admin
2. Tentar desmarcar "is_admin"
3. Salvar

**Resultado Esperado:**
- 🎯 Toast VERMELHO
- 📝 "Não é possível remover os privilégios de administrador do último administrador ativo."

#### 6.5. Desativar Usuário
**Ação:**
1. Clicar em "Ativar/Desativar" usuário

**Resultado Esperado:**
- 🎯 Toast VERDE
- 📝 "Usuário desativado com sucesso!" ou "Usuário ativado com sucesso!"

#### 6.6. Tentar Desativar Último Admin
**Resultado Esperado:**
- 🎯 Toast VERMELHO
- 📝 "Não é possível desativar o último administrador ativo do sistema."

#### 6.7. Excluir Usuário
**Resultado Esperado:**
- 🎯 Toast VERDE
- 📝 "Usuário excluído com sucesso!"

#### 6.8. Redefinir Senha de Usuário
**Ação:**
1. Clicar em "Redefinir Senha"

**Resultado Esperado:**
- 🎯 Toast VERDE
- 📝 Mensagem com a nova senha temporária

#### 6.9. Aprovar Solicitação de Equipamento
**Ação:**
1. "Equipamentos" → "Aprovar Solicitações"
2. Aprovar uma solicitação

**Resultado Esperado:**
- 🎯 Toast VERDE
- 📝 "Solicitação aprovada! Empréstimo criado com sucesso."

#### 6.10. Rejeitar Solicitação
**Resultado Esperado:**
- 🎯 Toast AZUL (info)
- 📝 "Solicitação rejeitada."

---

### ✅ **TESTE 7: PERFIL DO USUÁRIO**

#### 7.1. Alterar Senha
**Ação:**
1. Clicar no nome do usuário (canto superior direito)
2. "Meu Perfil"
3. Alterar senha
4. Salvar

**Resultado Esperado:**
- 🎯 Toast VERDE
- 📝 "Senha alterada com sucesso!"

#### 7.2. Tentar Alterar com Senha Atual Incorreta
**Resultado Esperado:**
- 🎯 Toast VERMELHO
- 📝 "Senha atual incorreta."

---

### ✅ **TESTE 8: MÚLTIPLOS TOASTS**

#### 8.1. Provocar Múltiplas Notificações Rapidamente
**Ação:**
1. Criar 3 lembretes rapidamente (um após o outro)
2. Ou salvar e editar repetidamente

**Resultado Esperado:**
- 🎯 Múltiplos toasts empilhados verticalmente
- 📝 Não se sobrepõem
- 📝 Cada um com seu progress bar
- 📝 Desaparecem na ordem (primeiro a entrar, primeiro a sair)

**Screenshot Esperado:**
```
┌─────────────────────────────────┐
│  ✓  Sucesso                  × │
│  Lembrete 3 criado!            │
│  ▓▓▓▓▓▓▓▓▓▓▓▓░░░░░░░░        │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│  ✓  Sucesso                  × │
│  Lembrete 2 criado!            │
│  ▓▓▓▓▓▓▓▓░░░░░░░░░░░░        │
└─────────────────────────────────┘

┌─────────────────────────────────┐
│  ✓  Sucesso                  × │
│  Lembrete 1 criado!            │
│  ▓▓▓░░░░░░░░░░░░░░░░░░        │
└─────────────────────────────────┘
```

---

### ✅ **TESTE 9: INTERAÇÕES COM TOAST**

#### 9.1. Fechar Toast Manualmente
**Ação:**
1. Criar uma notificação qualquer
2. Clicar no "×" do toast

**Resultado Esperado:**
- 🎯 Toast desaparece imediatamente com animação

#### 9.2. Hover no Toast
**Ação:**
1. Mover mouse sobre o toast

**Resultado Esperado:**
- 🎯 Toast fica levemente elevado (hover effect)
- 🎯 Sombra aumenta

---

### ✅ **TESTE 10: RESPONSIVIDADE**

#### 10.1. Mobile (375px)
**Ação:**
1. Abrir DevTools (F12)
2. Toggle device toolbar (Ctrl+Shift+M)
3. Selecionar iPhone SE ou similar
4. Fazer login

**Resultado Esperado:**
- 🎯 Toast ocupa largura total (com margens pequenas)
- 🎯 Posicionado no topo
- 🎯 Texto legível
- 🎯 Botão fechar acessível

#### 10.2. Tablet (768px)
**Resultado Esperado:**
- 🎯 Toast com largura adequada
- 🎯 Não muito largo nem muito estreito

#### 10.3. Desktop (1920px)
**Resultado Esperado:**
- 🎯 Toast no canto superior direito
- 🎯 Largura máxima ~420px

---

### ✅ **TESTE 11: DARK MODE** (Se implementado)

#### 11.1. Alternar Tema
**Ação:**
1. Clicar no botão de tema (sol/lua)
2. Gerar uma notificação

**Resultado Esperado:**
- 🎯 Toast com fundo escuro
- 🎯 Texto em cor clara
- 🎯 Contraste adequado

---

### ✅ **TESTE 12: LOADING OVERLAY**

#### 12.1. Formulário com Loading
**Ação:**
1. Abrir qualquer formulário
2. Preencher
3. Enviar
4. Observar durante o processamento

**Resultado Esperado:**
- 🎯 Overlay de loading aparece sobre o formulário
- 🎯 Spinner animado
- 🎯 Mensagem "Processando..." ou similar
- 🎯 Usuário não consegue clicar novamente
- 🎯 Loading desaparece após conclusão

---

### ✅ **TESTE 13: LOGOUT**

#### 13.1. Fazer Logout
**Ação:**
1. Clicar no nome do usuário (canto superior direito)
2. Clicar em "Sair do Sistema"

**Resultado Esperado:**
- 🎯 Toast AZUL (info)
- 📝 "Logout realizado."
- ✅ Redirecionado para tela de login
- ⏱️ Toast visível por ~5 segundos

---

## 📊 CHECKLIST FINAL

### Validações Gerais
- [ ] ✅ Toasts aparecem no canto superior direito (desktop)
- [ ] ✅ Toasts têm cores corretas (verde/vermelho/amarelo/azul)
- [ ] ✅ Progress bar anima corretamente
- [ ] ✅ Auto-dismiss funciona (4-8 segundos)
- [ ] ✅ Botão fechar (×) funciona
- [ ] ✅ Múltiplos toasts empilham sem sobrepor
- [ ] ✅ Animações são suaves (slide in/out)
- [ ] ✅ Não aparecem alerts() do navegador
- [ ] ✅ Não aparecem divs Bootstrap antigas no centro
- [ ] ✅ Console do navegador SEM ERROS

### Funcionalidades Testadas
- [ ] ✅ Login (sucesso e erro)
- [ ] ✅ Lembretes (criar/editar/deletar/pausar/cancelar)
- [ ] ✅ Tarefas (CRUD básico)
- [ ] ✅ Chamados (criar/editar)
- [ ] ✅ Equipamentos (solicitar/validar)
- [ ] ✅ Usuários Admin (CRUD/ativar/desativar)
- [ ] ✅ Proteções (último admin)
- [ ] ✅ Perfil (alterar senha)
- [ ] ✅ Logout

### Responsividade
- [ ] ✅ Desktop (1920px)
- [ ] ✅ Tablet (768px)
- [ ] ✅ Mobile (375px)

### Acessibilidade
- [ ] ✅ Navegação por teclado funciona
- [ ] ✅ Tab para focar em toasts
- [ ] ✅ Enter/Space para fechar
- [ ] ✅ Contraste adequado

---

## 🐛 PROBLEMAS ENCONTRADOS

**Use esta seção para anotar bugs:**

```
[ ] Bug 1: ____________________________________
    Descrição: ____________________________________
    Como reproduzir: ____________________________________

[ ] Bug 2: ____________________________________
    Descrição: ____________________________________
    Como reproduzir: ____________________________________
```

---

## ✅ RESULTADO FINAL

**Sistema de Notificações:** [ ] APROVADO  [ ] COM RESTRIÇÕES  [ ] REPROVADO

**Observações:**
_________________________________________________________
_________________________________________________________
_________________________________________________________

**Testado por:** ____________________
**Data:** ____________________
**Navegador:** ____________________
**Resolução:** ____________________

---

## 📸 SCREENSHOTS RECOMENDADOS

Tire screenshots dos seguintes cenários:
1. Toast de sucesso (verde)
2. Toast de erro (vermelho)
3. Toast de warning (amarelo)
4. Toast de info (azul)
5. Múltiplos toasts empilhados
6. Toast em mobile
7. Loading overlay

---

## 🎯 CRITÉRIOS DE ACEITAÇÃO

### Mínimo para Aprovar (P0)
- ✅ Toasts aparecem corretamente
- ✅ Auto-dismiss funciona
- ✅ Cores corretas por tipo
- ✅ Sem erros no console
- ✅ Flash messages convertendo

### Desejável (P1)
- ✅ Progress bar animando
- ✅ Hover effects
- ✅ Responsivo mobile
- ✅ Múltiplos toasts empilhando

### Opcional (P2)
- ✅ Dark mode
- ✅ Animações suaves
- ✅ Keyboard navigation

---

**BOA SORTE NOS TESTES! 🚀**
