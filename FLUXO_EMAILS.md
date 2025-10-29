# 📧 Fluxo de Emails - Sistema TI Reminder

## Visão Geral

O sistema possui múltiplos pontos de envio de emails para diferentes eventos. Todos os emails passam pela função central `send_email()` em `email_utils.py`.

## Arquitetura de Emails

```
┌─────────────────────────────────────────────────────────────┐
│                     EVENTOS DO SISTEMA                       │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   FUNÇÕES DE EMAIL                           │
│  • send_chamado_aberto_email()         (Novo chamado)       │
│  • send_chamado_atualizado_email()     (Atualização)        │
│  • send_password_reset_email()         (Reset senha)        │
│  • send_lembrete_email()               (Lembretes)          │
│  • send_tarefa_email()                 (Tarefas)            │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│              send_email(subject, recipients, body)           │
│                    (Função Central)                          │
└─────────────────────────────────────────────────────────────┘
                            │
                            ▼
┌─────────────────────────────────────────────────────────────┐
│                   Flask-Mail (SMTP)                          │
│              smtp.gmail.com:587 (TLS)                        │
└─────────────────────────────────────────────────────────────┘
```

## Fluxo de Criação de Chamado

### 1. **Usuário Cria Chamado**
   - **Arquivo:** `app/routes.py` → `abrir_chamado()`
   - **Linha:** 2946

### 2. **Sistema Chama Função de Email**
```python
send_chamado_aberto_email(novo_chamado)
```

### 3. **Função Prepara 2 Emails**
   - **Arquivo:** `app/email_utils.py` → `send_chamado_aberto_email()`
   - **Linhas:** 29-63

#### Email 1: Para o Solicitante
```python
recipient: chamado.solicitante.email  # Email do usuário que abriu o chamado
subject: "Chamado #{id} Aberto: {titulo}"
```

#### Email 2: Para o Grupo TI
```python
recipient: config.TI_EMAIL_GROUP  # Email do grupo TI (da configuração)
subject: "Novo Chamado #{id} Aberto por {username} ({setor}): {titulo}"
```

### 4. **Validação de Destinatários**
```python
# Obter email do grupo TI da configuração
ti_email = current_app.config.get("TI_EMAIL_GROUP")

# Validar que não é um domínio de exemplo
if not ti_email or 'example.com' in ti_email.lower():
    print("AVISO: TI_EMAIL_GROUP não configurado. Email TI não será enviado.")
    ti_recipients = []
else:
    ti_recipients = [ti_email]
```

### 5. **Envio via SMTP**
   - Cada email é enviado individualmente
   - Usa credenciais do Gmail configuradas em `.env`
   - Protocolo: SMTP sobre TLS (porta 587)

## Configurações Necessárias

### Variáveis de Ambiente (`.env`)

```env
# Servidor SMTP
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=pageupsistemas@gmail.com
MAIL_PASSWORD=yaqv dtkz gwyx zehv
MAIL_DEFAULT_SENDER=pageupsistemas@gmail.com

# Email do grupo TI para receber notificações
TI_EMAIL_GROUP=ti@alphaclin.net.br
```

### Arquivo de Configuração (`config.py`)

```python
class Config:
    # Email
    MAIL_SERVER = os.environ.get('MAIL_SERVER', 'smtp.gmail.com')
    MAIL_PORT = int(os.environ.get('MAIL_PORT', 587))
    MAIL_USE_TLS = os.environ.get('MAIL_USE_TLS', 'True').lower() == 'true'
    MAIL_USERNAME = os.environ.get('MAIL_USERNAME')
    MAIL_PASSWORD = os.environ.get('MAIL_PASSWORD')
    MAIL_DEFAULT_SENDER = os.environ.get('MAIL_DEFAULT_SENDER', 'pageupsistemas@gmail.com')
    
    # Email do grupo TI
    TI_EMAIL_GROUP = os.environ.get('TI_EMAIL_GROUP', 'ti@alphaclin.net.br')
```

## Problema Anterior e Solução

### ❌ Problema Identificado

O sistema estava enviando emails para `ti@example.com` (domínio inexistente) porque:

1. A configuração `TI_EMAIL_GROUP` **não estava definida** em `config.py`
2. O código usava um valor padrão com domínio de exemplo
3. O Gmail aceitava o envio, mas o email retornava como "não entregue"

### ✅ Solução Implementada

1. **Adicionada configuração** `TI_EMAIL_GROUP` em `config.py`
2. **Validação de domínios** antes do envio
3. **Valor padrão seguro** (`ti@alphaclin.net.br`)
4. **Logs de aviso** quando email não está configurado corretamente

### Código de Validação
```python
if not ti_email or 'example.com' in ti_email.lower():
    print(f"AVISO: TI_EMAIL_GROUP não está configurado corretamente.")
    ti_recipients = []  # Não envia email
else:
    ti_recipients = [ti_email]  # Envia para email válido
```

## Outros Tipos de Email

### Email de Atualização de Chamado
- **Função:** `send_chamado_atualizado_email()`
- **Destinatários:** Solicitante + Responsável TI
- **Trigger:** Quando administrador atualiza status/comentário

### Email de Reset de Senha
- **Função:** `send_password_reset_email()`
- **Destinatários:** Usuário que solicitou
- **Trigger:** Usuário esqueceu a senha

### Emails de Lembretes (Agendados)
- **Serviço:** `notification_service.py`
- **Scheduler:** APScheduler (tarefas em background)
- **Trigger:** Data de vencimento próxima

### Emails de Tarefas (Agendados)
- **Serviço:** `notification_service.py`
- **Scheduler:** APScheduler
- **Trigger:** Prazos e vencimentos

## Logs de Debug

Para debugar problemas de email, procure por:

```python
print(f"Email sent to {recipients} with subject: {subject}")  # Sucesso
print(f"Error sending email: {e}")  # Erro
```

Nos logs do Flask, você verá detalhes do protocolo SMTP:
```
send: 'ehlo ...'
reply: b'250 smtp.gmail.com at your service...'
send: 'mail from:<pageupsistemas@gmail.com>'
send: 'rcpt to:<destinatario@dominio.com>'
```

## Reiniciar Servidor Após Mudanças

⚠️ **IMPORTANTE:** Sempre que modificar arquivos de configuração ou código:

```bash
# Parar o servidor (Ctrl+C)
# Limpar cache Python
python -c "import shutil; shutil.rmtree('app/__pycache__', ignore_errors=True)"

# Reiniciar
python run.py
```

Ou simplesmente reinicie com hot-reload ativado (modo DEBUG).

## Segurança

### Gmail App Password
- **Nunca use** a senha normal do Gmail
- Use uma **"Senha de App"** gerada nas configurações de segurança do Google
- A senha atual no sistema já é uma "App Password"

### Variáveis Sensíveis
- Todas as credenciais estão em `.env` (não versionado)
- O `.gitignore` bloqueia commit acidental
- Em produção, use variáveis de ambiente do servidor (Render, Heroku, etc.)

## Monitoramento

Para monitorar emails enviados:

1. **Logs do Flask** - Console do servidor
2. **Banco de dados** - Tabela de logs de notificações (futura implementação)
3. **Gmail** - Caixa de "Enviados" do `pageupsistemas@gmail.com`

## Troubleshooting

### Email não chega
1. Verificar credenciais SMTP no `.env`
2. Verificar configuração `TI_EMAIL_GROUP`
3. Checar logs do Flask para erros
4. Verificar se o domínio do destinatário existe (MX records)

### Email vai para spam
1. Configurar SPF/DKIM no domínio remetente
2. Usar templates HTML bem formatados
3. Evitar palavras que disparam filtros de spam

### Erro "Connection refused"
1. Verificar firewall/antivírus bloqueando porta 587
2. Verificar se `MAIL_USE_TLS=True`
3. Testar conexão direta ao Gmail via telnet

## Melhorias Futuras

- [ ] Sistema de templates de email com Jinja2
- [ ] Fila de emails com Celery para envios assíncronos
- [ ] Logs estruturados de todas as tentativas de envio
- [ ] Dashboard de monitoramento de emails
- [ ] Suporte a múltiplos grupos de destinatários
- [ ] Email em lote com BCC
- [ ] Retry automático em caso de falha temporária
