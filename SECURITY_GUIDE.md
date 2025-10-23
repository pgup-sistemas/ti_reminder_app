# 🔐 Guia de Segurança - TI OSN System

## Visão Geral

Este documento descreve as implementações de segurança do sistema TI OSN e fornece diretrizes para manter a aplicação segura em produção.

---

## 🛡️ Funcionalidades de Segurança Implementadas

### 1. Autenticação Robusta

#### **Validação de Senha Forte**
- **Requisitos:**
  - Mínimo 8 caracteres
  - Pelo menos 1 letra maiúscula
  - Pelo menos 1 letra minúscula
  - Pelo menos 1 número
  - Pelo menos 1 caractere especial (!@#$%^&*)
  - Bloqueio de senhas comuns (lista de 30+ senhas comuns)

#### **Rate Limiting**
- **Login:** 5 tentativas por minuto por IP
- **Registro:** 3 tentativas por hora por IP
- **Reset de senha:** 3 tentativas por hora por IP
- **Token de reset:** 5 tentativas por hora por IP

#### **Bloqueio de Conta**
- Após 5 tentativas de login falhas consecutivas:
  - Conta bloqueada por 15 minutos
  - Mensagem clara ao usuário sobre o bloqueio
  - Possibilidade de desbloquear via reset de senha
- Reset automático do bloqueio após período expirado

#### **Gerenciamento de Sessão**
- Flask-Login como sistema único de autenticação (híbrido removido)
- Cookies de sessão configurados com:
  - `HttpOnly`: Proteção contra XSS
  - `Secure`: Apenas HTTPS em produção
  - `SameSite`: Proteção contra CSRF
- Timeout de sessão: 24 horas
- Logout limpa completamente a sessão

---

### 2. Proteção CSRF

- **WTForms CSRF Protection** habilitado
- Tokens CSRF em todos os formulários
- Validação automática em POST/PUT/DELETE
- SSL Strict mode em produção

---

### 3. Logging de Segurança

#### **Eventos Registrados:**
- ✅ Login bem-sucedido (username, IP, user-agent)
- ⚠️ Tentativa de login falha (username tentado, IP, tentativa N/5)
- 🚫 Bloqueio de conta (username, IP, número de tentativas)
- 📝 Registro de novo usuário (username, email, IP)
- 🔄 Solicitação de reset de senha (username, email, IP)
- ✔️ Senha redefinida com sucesso (username, IP)
- ❌ Tentativa de reset com token inválido (IP)
- 🚪 Logout (username, IP)

#### **Localização dos Logs:**
- Arquivo: `logs/security.log`
- Rotação: 10 arquivos de 10MB cada
- Formato: `YYYY-MM-DD HH:MM:SS - SECURITY - LEVEL - MESSAGE`

---

### 4. Campos de Auditoria no Banco de Dados

**Tabela `user`:**
```sql
- login_attempts (INTEGER) - Contador de tentativas falhas
- locked_until (DATETIME) - Data/hora de expiração do bloqueio
- password_changed_at (DATETIME) - Data da última troca de senha
- last_failed_login (DATETIME) - Data do último login falho
- last_password_reset (DATETIME) - Data do último reset de senha
- last_login (DATETIME) - Data do último login bem-sucedido
- created_at (DATETIME) - Data de criação da conta
- updated_at (DATETIME) - Data da última atualização
```

---

### 5. Validação de Dados

#### **Username:**
- Mínimo 3 caracteres
- Apenas letras, números, underscore e hífen
- Não pode começar com número

#### **Email:**
- Validação de formato padrão
- Verificação de unicidade

#### **Senha:**
- Validação de força (classe `StrongPassword`)
- Verificação contra senhas comuns (classe `NoCommonPassword`)
- Hashing com `Werkzeug` (PBKDF2)

---

## 📋 Checklist de Segurança para Produção

### **Antes do Deploy:**

#### 1. Variáveis de Ambiente
```bash
# Obrigatórias
✅ SECRET_KEY=<valor-seguro-64-caracteres>
✅ JWT_SECRET_KEY=<valor-seguro-64-caracteres>
✅ DATABASE_URL=<postgresql://...>
✅ MAIL_USERNAME=<email-sistema>
✅ MAIL_PASSWORD=<senha-email>

# Recomendadas
✅ FLASK_ENV=production
✅ DEBUG=False
✅ LOG_LEVEL=WARNING
```

#### 2. Configuração do Servidor Web
```nginx
# Nginx - Headers de Segurança
add_header X-Frame-Options "SAMEORIGIN" always;
add_header X-Content-Type-Options "nosniff" always;
add_header X-XSS-Protection "1; mode=block" always;
add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
```

#### 3. SSL/TLS
```
✅ Certificado SSL válido configurado
✅ Redirect HTTP → HTTPS
✅ HSTS habilitado
✅ TLS 1.2+ apenas
```

#### 4. Banco de Dados
```
✅ Backup automático configurado
✅ Senha forte para usuário do banco
✅ Acesso restrito por IP/firewall
✅ Conexões criptografadas (SSL)
```

#### 5. Monitoramento
```
✅ Logs centralizados (Sentry, Datadog, etc.)
✅ Alertas de tentativas de login falhas
✅ Monitoramento de performance
✅ Alertas de erro 500
```

---

## 🚨 Resposta a Incidentes

### **Conta Comprometida:**
1. Desativar conta imediatamente: `user.ativo = False`
2. Invalidar todas as sessões ativas
3. Forçar reset de senha
4. Verificar logs de acesso recente
5. Notificar usuário por email

### **Múltiplas Tentativas de Brute Force:**
1. Verificar IP de origem em `logs/security.log`
2. Adicionar IP ao firewall/WAF
3. Notificar administradores
4. Considerar aumentar tempo de bloqueio temporariamente

### **Vulnerabilidade Descoberta:**
1. Avaliar severidade (CVSS score)
2. Aplicar patch emergencial se crítico
3. Testar em ambiente de staging
4. Deploy em produção
5. Documentar no changelog

---

## 🔍 Auditoria de Segurança

### **Verificações Mensais:**
- [ ] Revisar logs de segurança
- [ ] Verificar contas com múltiplas tentativas falhas
- [ ] Auditar permissões de usuários admin/TI
- [ ] Verificar contas inativas há mais de 90 dias
- [ ] Testar processo de reset de senha

### **Verificações Trimestrais:**
- [ ] Scan de vulnerabilidades (OWASP ZAP, Nessus)
- [ ] Revisão de dependências (safety check)
- [ ] Teste de penetração
- [ ] Revisão de políticas de senha
- [ ] Backup e restore test

---

## 📚 Boas Práticas para Desenvolvedores

### **Ao Adicionar Novas Rotas:**
```python
from app.auth_utils import login_required, admin_required

@bp.route('/rota-protegida')
@login_required
def rota_protegida():
    # Código aqui
    pass

@bp.route('/rota-admin')
@admin_required
def rota_admin():
    # Código aqui
    pass
```

### **Ao Manipular Dados Sensíveis:**
```python
# ❌ NUNCA faça:
print(f"Senha: {user.password_hash}")
logger.info(f"Token: {token}")

# ✅ SEMPRE faça:
logger.info(f"Operação realizada para usuário ID: {user.id}")
```

### **Ao Fazer Queries:**
```python
# ❌ NUNCA faça:
query = f"SELECT * FROM user WHERE username = '{username}'"

# ✅ SEMPRE faça:
user = User.query.filter_by(username=username).first()
```

---

## 🆘 Contatos de Emergência

**Equipe de Segurança:**
- Email: security@pageup.com
- Telefone: (xx) xxxx-xxxx
- Slack: #security-incidents

**Servidores de Produção:**
- Render: https://dashboard.render.com
- PostgreSQL: [redacted]

---

## 📖 Referências

- [OWASP Top 10](https://owasp.org/www-project-top-ten/)
- [Flask Security Best Practices](https://flask.palletsprojects.com/en/latest/security/)
- [NIST Password Guidelines](https://pages.nist.gov/800-63-3/)
- [CWE Top 25](https://cwe.mitre.org/top25/)

---

**Última Atualização:** 2025-01-23  
**Versão:** 2.0  
**Responsável:** Equipe TI PageUp Sistemas
