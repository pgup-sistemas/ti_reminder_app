# Correção da Edição de Usuários

## Problema Identificado

A rota `/configuracoes/usuarios/<id>/editar` não estava salvando as alterações dos usuários com sucesso.

## Causa Raiz

Foram identificados múltiplos problemas:

1. **JavaScript escondendo campos**: Os campos de senha eram completamente escondidos (`display: none`) quando o checkbox "Alterar Senha" não estava marcado, causando problemas na validação do formulário.

2. **Campos desabilitados não enviados**: Campos HTML com atributo `disabled` não são enviados no POST, mas o JavaScript anterior estava apenas desabilitando sem tratamento adequado.

3. **Falta de feedback de erros**: Erros de validação não eram exibidos claramente ao usuário, deixando-o sem saber o que estava errado.

4. **Validação de senha incompleta**: A validação customizada do formulário não verificava se as senhas conferiam quando `change_password` estava marcado.

## Correções Implementadas

### 1. Template `user_form.html`

**Arquivo**: `app/templates/system_config/user_form.html`

#### Alteração no JavaScript (linhas 254-276)
- **Antes**: Campos de senha eram escondidos com `display: none`
- **Depois**: Campos são desabilitados mas permanecem visíveis com opacidade reduzida
- **Benefício**: Melhor UX e evita problemas de validação

```javascript
// Não esconde os campos, apenas desabilita
const parentDiv = field.closest('.mb-3');
if (parentDiv) {
    if (isChecked) {
        parentDiv.classList.remove('opacity-50');
    } else {
        parentDiv.classList.add('opacity-50');
    }
}
```

#### Nova lógica de submit (linhas 305-312)
- Habilita temporariamente campos desabilitados antes do submit
- Garante que valores vazios sejam enviados corretamente ao servidor

```javascript
// Habilitar campos de senha temporariamente antes do submit
const changePasswordCheckbox = document.querySelector('input[name="change_password"]');
if (changePasswordCheckbox && !changePasswordCheckbox.checked) {
    passwordFields.forEach(field => {
        field.disabled = false; // Habilita temporariamente para envio
    });
}
```

#### Exibição de erros (linhas 27-44)
- Adicionado bloco de alerta no topo do formulário
- Mostra todos os erros de validação de forma clara
- Permite ao usuário corrigir os erros antes de resubmeter

```html
{% if form.errors %}
<div class="alert alert-danger alert-dismissible fade show" role="alert">
    <h5 class="alert-heading">
        <i class="fas fa-exclamation-circle me-2"></i>
        Erros de Validação
    </h5>
    <hr>
    <ul class="mb-0">
        {% for field, errors in form.errors.items() %}
            {% for error in errors %}
            <li><strong>{{ form[field].label.text }}:</strong> {{ error }}</li>
            {% endfor %}
        {% endfor %}
    </ul>
</div>
{% endif %}
```

### 2. Backend - Route Handler

**Arquivo**: `app/blueprints/system_config.py`

#### Pré-preenchimento de dados (linhas 231-234)
- Garante que checkboxes sejam preenchidos corretamente no GET
- Evita que valores sejam perdidos ao recarregar o formulário

```python
if not form.is_submitted():
    form.sector_id.data = user.sector_id or 0
    form.is_admin.data = user.is_admin
    form.is_ti.data = user.is_ti
```

#### Logs de debug (linhas 240-250)
- Adiciona logging detalhado para debug
- Registra dados recebidos e erros de validação
- Facilita troubleshooting em produção

```python
if request.method == 'POST':
    current_app.logger.info(
        "Recebida submissão de formulário de edição",
        extra={
            "user_id": user.id,
            "form_submitted": form.is_submitted(),
            "form_errors": form.errors,
            "request_form": dict(request.form)
        }
    )
```

#### Feedback de erros (linhas 409-419)
- Detecta quando formulário é submetido mas falha na validação
- Mostra mensagens flash específicas para cada erro
- Melhora a experiência do usuário

```python
if request.method == 'POST' and not form.validate():
    current_app.logger.warning(
        "Formulário de edição de usuário com erros de validação",
        extra={"user_id": user.id, "errors": form.errors}
    )
    flash_error("Por favor, corrija os erros no formulário.")
    for field, errors in form.errors.items():
        for error in errors:
            flash_error(f"{field}: {error}")
```

### 3. Validação do Formulário

**Arquivo**: `app/forms.py`

#### Melhoria na validação customizada (linhas 210-233)
- Valida conferência de senhas quando `change_password` está marcado
- Retorna erros específicos para cada campo
- Previne submissão com senhas não conferindo

```python
def validate(self, extra_validators=None):
    """Normaliza dados e executa validações adicionais."""
    # ... código de normalização ...
    
    # Validação personalizada para a senha
    if self.change_password.data:
        if not self.new_password.data:
            self.new_password.errors.append("Por favor, insira a nova senha")
            return False
        if self.new_password.data and self.confirm_password.data:
            if self.new_password.data != self.confirm_password.data:
                self.confirm_password.errors.append("As senhas não conferem")
                return False
    
    return True
```

## Como Testar

### Teste 1: Edição sem alterar senha

1. Acesse: `http://192.168.1.86:5000/configuracoes/usuarios`
2. Clique em "Editar" em qualquer usuário
3. Altere apenas o nome ou email
4. **NÃO** marque "Alterar Senha"
5. Clique em "Atualizar Usuário"
6. **Resultado esperado**: Dados salvos com sucesso

### Teste 2: Edição alterando senha

1. Acesse a edição de um usuário
2. Marque "Alterar Senha"
3. Preencha nova senha e confirmação
4. Clique em "Atualizar Usuário"
5. **Resultado esperado**: Dados e senha salvos com sucesso

### Teste 3: Validação de senhas diferentes

1. Acesse a edição de um usuário
2. Marque "Alterar Senha"
3. Preencha senhas diferentes nos dois campos
4. Clique em "Atualizar Usuário"
5. **Resultado esperado**: Erro "As senhas não conferem" exibido

### Teste 4: Edição de permissões

1. Acesse a edição de um usuário
2. Altere checkboxes "É Administrador" ou "É da Equipe de TI"
3. Altere status "Usuário Ativo"
4. Clique em "Atualizar Usuário"
5. **Resultado esperado**: Permissões atualizadas com sucesso

### Teste 5: Validação de campos obrigatórios

1. Acesse a edição de um usuário
2. Limpe o campo "Nome de Usuário"
3. Clique em "Atualizar Usuário"
4. **Resultado esperado**: Erro exibido no topo do formulário

## Logs para Monitoramento

Os seguintes logs foram adicionados para facilitar o troubleshooting:

### Log de Submissão
```
INFO: Recebida submissão de formulário de edição
Extra: user_id, form_submitted, form_errors, request_form
```

### Log de Validação com Erro
```
WARNING: Formulário de edição de usuário com erros de validação
Extra: user_id, errors
```

### Log de Sucesso
```
INFO: Usuário atualizado com sucesso
Extra: user_id, before, after
```

### Log de Erro no Banco
```
ERROR: Erro ao atualizar usuário
Extra: user_id, error
```

## Verificação de Logs

Para verificar se o sistema está funcionando corretamente, monitore os logs em:

```bash
# Verificar logs em tempo real (se configurado)
tail -f logs/app.log

# Ou verificar saída do console do servidor
```

## Arquivos Alterados

1. `app/templates/system_config/user_form.html` - Interface do usuário
2. `app/blueprints/system_config.py` - Lógica de backend
3. `app/forms.py` - Validação do formulário

## Impacto

- ✅ **Segurança**: Mantida (validações fortalecidas)
- ✅ **Performance**: Sem impacto
- ✅ **UX**: Melhorada (feedback de erros mais claro)
- ✅ **Manutenibilidade**: Melhorada (logs adicionados)

## Próximos Passos Recomendados

1. **Testes**: Execute todos os testes listados acima
2. **Monitoramento**: Verifique os logs durante os testes
3. **Validação**: Confirme que todas as funcionalidades funcionam corretamente
4. **Deploy**: Se tudo funcionar, considere criar um backup antes do deploy em produção

## Notas Técnicas

- Os campos de senha desabilitados são habilitados apenas no momento do submit
- CSRF token é mantido e validado automaticamente pelo Flask-WTF
- Logs estruturados facilitam análise e troubleshooting
- Validação acontece tanto no frontend (JavaScript) quanto no backend (Python)

## Suporte

Se encontrar problemas:

1. Verifique os logs do servidor
2. Abra o console do navegador (F12) e procure por erros JavaScript
3. Verifique se todos os campos obrigatórios estão preenchidos
4. Confirme que não há mensagens de erro exibidas no formulário

---

**Data da Correção**: 24/10/2025  
**Versão do Sistema**: 2.0  
**Arquiteto**: Sistema TI OSN
