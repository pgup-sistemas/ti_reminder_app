# 🔐 Gerenciamento de Segurança - Guia do Administrador

## Visão Geral

Guia completo para administradores gerenciarem a segurança do TI OSN System v2.0, incluindo monitoramento, políticas e resposta a incidentes.

---

## 👥 Gerenciamento de Usuários

### Desbloquear Conta de Usuário

**Cenário:** Usuário bloqueado após 5 tentativas falhas.

#### Via Interface Admin
1. Acesse **Admin → Gerenciar Usuários**
2. Localize o usuário bloqueado
3. Clique em **Editar**
4. Limpe os campos:
   - `locked_until` → NULL
   - `login_attempts` → 0
5. Salve as alterações

#### Via Console Python
```python
from app import create_app, db
from app.models import User

app = create_app()
with app.app_context():
    user = User.query.filter_by(username='nome_usuario').first()
    user.locked_until = None
    user.login_attempts = 0
    db.session.commit()
    print(f"Usuário {user.username} desbloqueado!")
```

#### Via SQL Direto
```sql
UPDATE "user"
SET locked_until = NULL, login_attempts = 0
WHERE username = 'nome_usuario';
```

---

## 📊 Monitoramento de Segurança

### Dashboard de Segurança

**Queries úteis para monitoramento:**

#### 1. Contas Atualmente Bloqueadas
```sql
SELECT 
    id,
    username,
    email,
    login_attempts,
    locked_until,
    EXTRACT(MINUTE FROM (locked_until - NOW())) as minutos_restantes
FROM "user"
WHERE locked_until > NOW()
ORDER BY locked_until DESC;
```

#### 2. Usuários com Múltiplas Tentativas Falhas
```sql
SELECT 
    username,
    email,
    login_attempts,
    last_failed_login,
    last_login
FROM "user"
WHERE login_attempts > 0
ORDER BY login_attempts DESC, last_failed_login DESC
LIMIT 20;
```

#### 3. Senhas Não Alteradas Recentemente
```sql
SELECT 
    username,
    email,
    password_changed_at,
    EXTRACT(DAY FROM (NOW() - password_changed_at)) as dias_sem_alterar
FROM "user"
WHERE 
    password_changed_at < NOW() - INTERVAL '90 days'
    OR password_changed_at IS NULL
ORDER BY password_changed_at ASC NULLS FIRST;
```

#### 4. Últimos Logins
```sql
SELECT 
    username,
    email,
    last_login,
    last_failed_login,
    login_attempts
FROM "user"
ORDER BY last_login DESC NULLS LAST
LIMIT 50;
```

#### 5. Contas Inativas
```sql
SELECT 
    username,
    email,
    last_login,
    created_at,
    ativo
FROM "user"
WHERE 
    last_login < NOW() - INTERVAL '90 days'
    OR last_login IS NULL
ORDER BY last_login ASC NULLS FIRST;
```

---

## 📝 Análise de Logs de Segurança

### Localização
```
logs/security.log
```

### Comandos Úteis (PowerShell)

#### Ver últimas 50 linhas
```powershell
Get-Content logs\security.log -Tail 50
```

#### Monitorar em tempo real
```powershell
Get-Content logs\security.log -Wait
```

#### Filtrar logins bem-sucedidos hoje
```powershell
Get-Content logs\security.log | Select-String "Login bem-sucedido" | Select-String (Get-Date -Format "yyyy-MM-dd")
```

#### Filtrar tentativas falhas
```powershell
Get-Content logs\security.log | Select-String "Tentativa falha"
```

#### Contar tentativas por IP
```powershell
Get-Content logs\security.log | 
    Select-String "IP: (\d+\.\d+\.\d+\.\d+)" | 
    ForEach-Object { $_.Matches.Groups[1].Value } | 
    Group-Object | 
    Sort-Object Count -Descending
```

#### Contas bloqueadas hoje
```powershell
Get-Content logs\security.log | Select-String "Conta bloqueada" | Select-String (Get-Date -Format "yyyy-MM-dd")
```

---

## 🚨 Resposta a Incidentes

### Cenário 1: Conta Comprometida

**Sinais:**
- Logins de IPs suspeitos
- Atividade fora do horário normal
- Múltiplas tentativas de acesso

**Ações Imediatas:**

1. **Desativar conta**
```sql
UPDATE "user"
SET ativo = false
WHERE username = 'usuario_comprometido';
```

2. **Invalidar sessões**
   - Restart do servidor Flask (todas sessões expiram)
   - Ou aguarde timeout de 24h

3. **Forçar reset de senha**
```sql
UPDATE "user"
SET 
    reset_token = NULL,
    reset_token_expiry = NULL,
    login_attempts = 0,
    locked_until = NULL
WHERE username = 'usuario_comprometido';
```

4. **Notificar usuário**
   - Email informando sobre atividade suspeita
   - Instruções para reset de senha

5. **Investigar logs**
```powershell
Get-Content logs\security.log | Select-String "usuario_comprometido"
```

6. **Documentar incidente**
   - Horário da detecção
   - IPs suspeitos
   - Ações tomadas

---

### Cenário 2: Ataque de Força Bruta

**Sinais:**
- Múltiplas tentativas de login de um mesmo IP
- Tentativas em vários usuários
- Padrão automatizado

**Ações:**

1. **Identificar IP atacante**
```powershell
Get-Content logs\security.log | 
    Select-String "Tentativa falha" | 
    Select-String "IP: (\d+\.\d+\.\d+\.\d+)" | 
    ForEach-Object { $_.Matches.Groups[1].Value } | 
    Group-Object | 
    Sort-Object Count -Descending | 
    Select-Object -First 10
```

2. **Bloquear IP no firewall**
```powershell
# Windows Firewall
New-NetFirewallRule -DisplayName "Block Attacker IP" `
    -Direction Inbound `
    -RemoteAddress 192.168.1.100 `
    -Action Block
```

3. **Revisar rate limiting**
   - Verificar se está ativo
   - Ajustar limites se necessário

4. **Notificar equipe**
   - Documentar ataque
   - Compartilhar IPs suspeitos

---

### Cenário 3: Senhas Fracas Detectadas

**Ação Preventiva:**

1. **Identificar usuários afetados**
   - Verificar logs de registro antigos
   - Contas criadas antes da validação forte

2. **Forçar troca de senha**
```sql
-- Marcar senhas como expiradas (implementar campo)
UPDATE "user"
SET password_changed_at = '2020-01-01'
WHERE password_changed_at IS NULL
   OR password_changed_at < '2025-01-23';
```

3. **Comunicar política**
   - Email para todos usuários
   - Explicar novos requisitos

---

## 📋 Políticas de Segurança Recomendadas

### Política de Senhas

**Requisitos obrigatórios:**
- ✅ Mínimo 8 caracteres
- ✅ 1 maiúscula, 1 minúscula, 1 número, 1 especial
- ✅ Não usar senhas comuns
- ✅ Trocar a cada 90 dias (recomendado)

**Bloqueio:**
- ✅ 5 tentativas falhas = 15 minutos bloqueado
- ✅ Reset automático após período

### Política de Sessões

**Configuração atual:**
- ⏱️ Timeout: 24 horas de inatividade
- 🍪 Cookies: HttpOnly, Secure (produção)
- 🔒 SameSite: Lax (dev) / Strict (prod)

### Política de Auditoria

**Logs mantidos:**
- 📝 Segurança: 10 arquivos x 10MB = 100MB
- 🔄 Rotação automática
- 📊 Revisar mensalmente

**Eventos críticos:**
1. Logins (sucesso/falha)
2. Bloqueios de conta
3. Resets de senha
4. Mudanças de permissão

---

## 🔧 Configurações Avançadas

### Ajustar Rate Limiting

**Arquivo:** `app/__init__.py`

```python
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]  # Ajustar aqui
)
```

**Em rotas específicas:**
```python
@bp_auth.route("/login")
@limiter.limit("5 per minute")  # Ajustar limite
def login():
    # ...
```

### Ajustar Tempo de Bloqueio

**Arquivo:** `app/auth.py` (linha ~152)

```python
if user.login_attempts >= 5:
    user.locked_until = datetime.utcnow() + timedelta(minutes=15)  # Ajustar aqui
```

### Configurar HTTPS Obrigatório

**Arquivo:** `config.py`

```python
class ProductionConfig(Config):
    SESSION_COOKIE_SECURE = True  # Força HTTPS
    FORCE_HTTPS = True
```

---

## 📊 Relatórios de Segurança

### Script de Relatório Semanal

**Arquivo:** `scripts/security_report.py` (criar)

```python
"""Gerar relatório semanal de segurança"""
from app import create_app, db
from app.models import User
from datetime import datetime, timedelta

app = create_app()

with app.app_context():
    hoje = datetime.utcnow()
    semana_passada = hoje - timedelta(days=7)
    
    print("=" * 60)
    print("RELATÓRIO DE SEGURANÇA SEMANAL")
    print("=" * 60)
    
    # Contas bloqueadas na semana
    bloqueadas = User.query.filter(
        User.locked_until.isnot(None)
    ).count()
    print(f"\n📊 Contas bloqueadas atualmente: {bloqueadas}")
    
    # Usuários com tentativas falhas
    com_falhas = User.query.filter(
        User.login_attempts > 0
    ).count()
    print(f"⚠️  Usuários com tentativas falhas: {com_falhas}")
    
    # Senhas antigas
    senhas_antigas = User.query.filter(
        (User.password_changed_at < semana_passada) | 
        (User.password_changed_at.is_(None))
    ).count()
    print(f"🔐 Senhas não alteradas há 90+ dias: {senhas_antigas}")
    
    # Total de usuários
    total = User.query.count()
    ativos = User.query.filter_by(ativo=True).count()
    print(f"\n👥 Total de usuários: {total}")
    print(f"✅ Usuários ativos: {ativos}")
    
    print("\n" + "=" * 60)
```

### Executar
```bash
python scripts/security_report.py
```

---

## 🎓 Treinamento de Usuários

### Tópicos para Treinamento

1. **Criação de Senhas Fortes**
   - Use gerenciador de senhas
   - Evite informações pessoais
   - Unique por serviço

2. **Phishing e Engenharia Social**
   - Verificar remetente de emails
   - Não clicar em links suspeitos
   - Confirmar solicitações por outro canal

3. **Boas Práticas**
   - Logout em PCs compartilhados
   - Não compartilhar credenciais
   - Reportar atividades suspeitas

---

## 📞 Contatos de Emergência

**Incidente de Segurança:**
- 🚨 Email: pageupsistemas@gmail.com
- <i class="fab fa-github"></i> GitHub: [ti_reminder_app](https://github.com/pgup-sistemas/ti_reminder_app.git)
- 📱 Telefone: (xx) xxxx-xxxx
- 💬 Slack: #security-incidents

**Suporte Técnico:**
- 📧 Email: pageupsistemas@gmail.com
- 🎫 Sistema de chamados interno

---

## ✅ Checklist Mensal

- [ ] Revisar logs de segurança
- [ ] Verificar contas com múltiplas tentativas falhas
- [ ] Auditar permissões de usuários admin/TI
- [ ] Verificar contas inativas há mais de 90 dias
- [ ] Testar processo de reset de senha
- [ ] Backup de logs de segurança
- [ ] Atualizar dependências de segurança
- [ ] Gerar relatório mensal

---

**Última atualização:** Janeiro 2025  
**Versão:** 2.0 - Segurança Enterprise  
**Responsável:** Administradores do Sistema
