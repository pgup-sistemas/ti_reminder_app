# 🔐 Segurança e Autenticação

## Visão Geral

O TI OSN System v2.0 implementa as mais modernas práticas de segurança para proteger seus dados e garantir acesso seguro ao sistema.

---

## 🔑 Sistema de Login

### Acessando o Sistema

1. **URL de Acesso**: `http://[servidor]:5000/auth/login`
2. **Credenciais**: Use seu usuário e senha fornecidos pelo administrador
3. **Lembrar-me**: Marque para manter sessão ativa por 24 horas

### Requisitos de Senha Forte

Para garantir a segurança da sua conta, todas as senhas devem atender aos seguintes critérios:

!!! warning "Requisitos Obrigatórios"
    - ✅ **Mínimo 8 caracteres**
    - ✅ **Pelo menos 1 letra MAIÚSCULA** (A-Z)
    - ✅ **Pelo menos 1 letra minúscula** (a-z)
    - ✅ **Pelo menos 1 número** (0-9)
    - ✅ **Pelo menos 1 caractere especial** (!@#$%^&*)

**Exemplos:**
- ❌ `senha123` - Muito simples
- ❌ `Senha123` - Falta caractere especial
- ✅ `S3nh@Fort3!` - Senha forte e válida
- ✅ `M1nh@S3nh@2025!` - Excelente senha

### Senhas Proibidas

O sistema bloqueia senhas comuns para sua segurança:

- ❌ password, password123, 12345678
- ❌ qwerty, abc123, admin
- ❌ Admin123, Senha123, Teste123

---

## 🛡️ Proteção de Conta

### Bloqueio Automático

Para proteger contra ataques de força bruta:

!!! danger "Atenção: Tentativas de Login"
    - **1ª a 2ª tentativa falha**: Acesso normal
    - **3ª tentativa falha**: Aviso de 2 tentativas restantes
    - **4ª tentativa falha**: Aviso de 1 tentativa restante
    - **5ª tentativa falha**: **Conta bloqueada por 15 minutos**

**Se sua conta for bloqueada:**
1. Aguarde 15 minutos para desbloqueio automático
2. OU use a opção **"Esqueceu a senha?"** para reset imediato

### Limite de Requisições

O sistema limita requisições para prevenir abuso:

| Ação | Limite | Período |
|------|--------|---------|
| **Login** | 5 tentativas | Por minuto |
| **Registro** | 3 cadastros | Por hora |
| **Reset de senha** | 3 solicitações | Por hora |

!!! info "Proteção Automática"
    Se você atingir o limite, aguarde alguns minutos antes de tentar novamente.

---

## 🔄 Recuperação de Senha

### Como Redefinir sua Senha

1. **Acesse** a página de login
2. **Clique** em "Esqueceu sua senha?"
3. **Informe** seu e-mail cadastrado
4. **Verifique** seu e-mail (cheque spam/lixo eletrônico)
5. **Clique** no link recebido (válido por 1 hora)
6. **Defina** uma nova senha forte
7. **Confirme** a senha
8. **Faça login** com a nova senha

!!! warning "Link de Reset"
    - ⏱️ Válido por **1 hora**
    - 🔐 Uso único (expira após uso)
    - 📧 Enviado para o e-mail cadastrado

---

## 👤 Criando uma Conta

### Cadastro de Novo Usuário

1. **Acesse**: `/auth/register`
2. **Preencha**:
   - Nome de usuário (mínimo 3 caracteres)
   - E-mail válido
   - Senha forte (veja requisitos acima)
   - Confirmação de senha
3. **Clique** em "Cadastrar"
4. **Aguarde** aprovação do administrador (se necessário)
5. **Faça login** com suas credenciais

### Requisitos do Nome de Usuário

- ✅ Mínimo 3 caracteres
- ✅ Apenas letras, números, underscore (_) e hífen (-)
- ✅ Não pode começar com número
- ❌ Sem espaços ou caracteres especiais

**Exemplos:**
- ✅ `joao_silva`
- ✅ `maria-santos`
- ✅ `usuario123`
- ❌ `123usuario` (começa com número)
- ❌ `joão@silva` (caracteres inválidos)

---

## 🔒 Sessões e Logout

### Gerenciamento de Sessão

- **Duração**: 24 horas de inatividade
- **Cookies Seguros**: Protegidos contra XSS
- **Logout automático**: Após 24 horas sem atividade

### Como Fazer Logout

1. **Clique** no menu do usuário (canto superior direito)
2. **Selecione** "Sair" ou "Logout"
3. **Confirme** se solicitado

!!! tip "Boa Prática"
    Sempre faça logout ao usar computadores compartilhados!

---

## 🔐 Boas Práticas de Segurança

### Para Proteger sua Conta

1. **✅ Use senha forte e única**
   - Não reutilize senhas de outros sites
   - Use gerenciador de senhas (LastPass, Bitwarden)

2. **✅ Mantenha seu e-mail seguro**
   - Seu e-mail é a chave de recuperação
   - Use autenticação de dois fatores no e-mail

3. **✅ Cuidado com phishing**
   - Verifique o URL do site
   - Não clique em links suspeitos por e-mail

4. **✅ Faça logout em computadores compartilhados**
   - Sempre saia do sistema após uso
   - Não marque "Lembrar-me" em PCs públicos

5. **✅ Atualize sua senha regularmente**
   - Recomendado a cada 3-6 meses
   - Altere imediatamente se suspeitar de comprometimento

---

## ⚠️ Problemas Comuns

### "Usuário ou senha inválidos"

**Causas possíveis:**
- ❌ Usuário digitado incorretamente
- ❌ Senha incorreta
- ❌ Caps Lock ativado
- ❌ Conta desativada pelo administrador

**Soluções:**
1. Verifique se Caps Lock está desativado
2. Confirme o nome de usuário correto
3. Use "Esqueceu a senha?" se necessário
4. Entre em contato com o administrador

### "Conta temporariamente bloqueada"

**Causa:**
- 5 tentativas de login falhas consecutivas

**Solução:**
1. **Opção 1**: Aguarde 15 minutos para desbloqueio automático
2. **Opção 2**: Use "Esqueceu a senha?" para reset imediato

### "Link de redefinição inválido ou expirado"

**Causas:**
- Link usado há mais de 1 hora
- Link já foi utilizado
- Token inválido

**Solução:**
1. Solicite um novo link de reset
2. Use o link dentro de 1 hora

### "Esta senha é muito comum"

**Causa:**
- Senha na lista de senhas proibidas

**Solução:**
- Crie uma senha mais complexa e única
- Combine letras, números e símbolos de forma criativa

---

## 📞 Suporte

### Precisa de Ajuda?

**Conta bloqueada ou problemas de acesso:**
- 📧 Email: suporte@ti-osn.com
- 🎫 Abra um chamado (se conseguir acessar)
- 👤 Contate o administrador do sistema

**Esqueceu seu nome de usuário:**
- Entre em contato com o administrador
- Informe seu e-mail cadastrado

**Conta desativada:**
- Verifique com o administrador
- Pode ser política de inatividade ou término de contrato

---

## 🏆 Status de Segurança

O TI OSN System v2.0 atende aos mais altos padrões de segurança:

- ✅ **OWASP Top 10** - Proteção contra vulnerabilidades críticas
- ✅ **Rate Limiting** - Proteção contra ataques automatizados
- ✅ **Senhas Seguras** - Validação forte obrigatória
- ✅ **Sessões Protegidas** - Cookies HttpOnly e Secure
- ✅ **CSRF Protection** - Proteção contra falsificação de requisições
- ✅ **Logging Completo** - Auditoria de todas ações de segurança
- ✅ **Headers HTTP Seguros** - HSTS, CSP, X-Frame-Options

!!! success "Sistema Certificado"
    **Score de Segurança: 9.3/10** - Sistema pronto para ambiente corporativo

---

**Última atualização:** Janeiro 2025  
**Versão:** 2.0 - Sistema de Segurança Completo
