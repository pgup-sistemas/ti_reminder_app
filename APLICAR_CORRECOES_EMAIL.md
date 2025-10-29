# 🔧 Instruções para Aplicar as Correções de Email

## ❗ IMPORTANTE: O servidor precisa ser reiniciado

O sistema ainda enviou para `ti@example.com` porque o servidor estava rodando com o código **ANTIGO** (iniciado às 08:40).

As correções já foram aplicadas nos arquivos, mas **só entrarão em vigor após reiniciar**.

---

## ✅ Passo a Passo

### 1️⃣ Pare o servidor Flask
No terminal onde o servidor está rodando, pressione:
```
Ctrl + C
```

### 2️⃣ Adicione a configuração no arquivo `.env`

Abra o arquivo `.env` e adicione esta linha (se ainda não existir):

```env
# Email do grupo TI para receber notificações de chamados
TI_EMAIL_GROUP=ti@alphaclin.net.br
```

**Localização do arquivo:** `c:\Users\Oezios Normando\Documents\tireminderapp\.env`

### 3️⃣ Limpe o cache Python

Execute no terminal:
```powershell
Remove-Item -Recurse -Force .\app\__pycache__
```

Ou simplesmente delete a pasta `app\__pycache__` manualmente.

### 4️⃣ Reinicie o servidor

```powershell
python run.py
```

### 5️⃣ Teste criando um novo chamado

Agora, ao criar um chamado, você verá no log:

✅ **Email enviado para:** `ti@alphaclin.net.br` (grupo TI)  
✅ **Sem tentativa de envio para:** `ti@example.com`

---

## 🎯 O que foi corrigido?

### Arquivo: `config.py`
```python
# ANTES: Configuração não existia
# DEPOIS:
TI_EMAIL_GROUP = os.environ.get('TI_EMAIL_GROUP', 'ti@alphaclin.net.br')
```

### Arquivo: `email_utils.py`
```python
# ANTES: Usava "ti@example.com" como padrão
ti_recipients = [current_app.config.get("TI_EMAIL_GROUP", "ti@example.com")]

# DEPOIS: Valida antes de enviar
ti_email = current_app.config.get("TI_EMAIL_GROUP")

if not ti_email or 'example.com' in ti_email.lower():
    print("AVISO: TI_EMAIL_GROUP não configurado. Email TI não será enviado.")
    ti_recipients = []  # NÃO ENVIA
else:
    ti_recipients = [ti_email]  # ENVIA PARA EMAIL VÁLIDO
```

### Arquivo: `.env.example`
```env
# ADICIONADO: Documentação da nova variável
TI_EMAIL_GROUP=ti@alphaclin.net.br
```

---

## 📊 Como verificar se funcionou?

Após reiniciar e criar um novo chamado, você verá nos logs:

```
Email sent to ['ti@alphaclin.net.br'] with subject: Chamado #X Aberto: ...
Email sent to ['ti@alphaclin.net.br'] with subject: Novo Chamado #X Aberto por ...
```

**NÃO** verá mais:
```
Email sent to ['ti@example.com'] ...
```

E **NÃO** receberá mais emails de erro do Gmail:
```
Mail Delivery Subsystem: Address not found
DNS Error: ... example.com doesn't receive email
```

---

## ❓ Por que isso aconteceu?

1. **Código antigo:** O sistema tinha `"ti@example.com"` como valor padrão
2. **Configuração ausente:** `TI_EMAIL_GROUP` não estava definida
3. **Servidor em execução:** O Flask carregou o código antigo na memória
4. **Cache Python:** Arquivos `.pyc` guardaram a versão compilada antiga

---

## 🚀 Pronto!

Após seguir esses passos, o sistema **NUNCA MAIS** tentará enviar emails para domínios inexistentes como `example.com`.

Todos os emails de chamados serão enviados corretamente para:
- ✉️ Solicitante: email do usuário que criou o chamado
- ✉️ Grupo TI: `ti@alphaclin.net.br` (configurável via `.env`)
