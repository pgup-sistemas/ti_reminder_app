# Guia de Deployment - TI Reminder App

## 🚀 Visão Geral

Este documento descreve o processo completo de deployment do TI Reminder App, desde o ambiente de desenvolvimento até a produção.

## 🏗️ Arquitetura de Deployment

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Development   │    │     Staging     │    │   Production    │
│                 │    │                 │    │                 │
│ • SQLite        │───▶│ • PostgreSQL    │───▶│ • PostgreSQL    │
│ • Flask Dev     │    │ • Gunicorn      │    │ • Gunicorn      │
│ • Local Files   │    │ • Nginx         │    │ • Nginx         │
│                 │    │ • SSL (Let's E) │    │ • SSL (Let's E) │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🔧 Pré-requisitos

### Sistema Operacional
- Ubuntu 20.04+ / CentOS 8+ / Windows Server 2019+
- Python 3.9+
- PostgreSQL 13+
- Nginx 1.18+

### Dependências
```bash
# Ubuntu/Debian
sudo apt update
sudo apt install python3 python3-pip python3-venv postgresql postgresql-contrib nginx

# CentOS/RHEL
sudo yum install python3 python3-pip postgresql postgresql-server nginx
```

## 📦 Preparação do Ambiente

### 1. Criar Usuário do Sistema

```bash
# Criar usuário dedicado
sudo useradd -m -s /bin/bash tireminder
sudo usermod -aG sudo tireminder

# Trocar para o usuário
sudo su - tireminder
```

### 2. Configurar Banco de Dados

```bash
# Inicializar PostgreSQL (se necessário)
sudo postgresql-setup --initdb
sudo systemctl start postgresql
sudo systemctl enable postgresql

# Criar banco e usuário
sudo -u postgres psql
```

```sql
CREATE DATABASE ti_reminder_prod;
CREATE USER ti_reminder WITH PASSWORD 'senha_segura_aqui';
GRANT ALL PRIVILEGES ON DATABASE ti_reminder_prod TO ti_reminder;
\q
```

### 3. Configurar Aplicação

```bash
# Clonar repositório
git clone https://github.com/seu-usuario/ti-reminder-app.git
cd ti-reminder-app

# Criar ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Instalar dependências
pip install -r requirements.txt
pip install gunicorn psycopg2-binary
```

## ⚙️ Configuração

### 1. Variáveis de Ambiente

Criar arquivo `.env`:

```bash
# Produção
FLASK_ENV=production
SECRET_KEY=sua_chave_secreta_muito_segura_aqui
DATABASE_URL=postgresql://ti_reminder:senha_segura_aqui@localhost/ti_reminder_prod

# Email (opcional)
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=seu_email@gmail.com
MAIL_PASSWORD=sua_senha_app

# Logs
LOG_LEVEL=INFO
LOG_FILE=/var/log/ti-reminder/app.log
LOG_TO_STDOUT=False

# Timezone
TIMEZONE=America/Sao_Paulo
```

### 2. Configuração do Gunicorn

Criar `gunicorn.conf.py`:

```python
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Restart workers
max_requests = 1000
max_requests_jitter = 50
preload_app = True

# Logging
accesslog = "/var/log/ti-reminder/access.log"
errorlog = "/var/log/ti-reminder/error.log"
loglevel = "info"

# Process naming
proc_name = "ti-reminder"

# Server mechanics
daemon = False
pidfile = "/var/run/ti-reminder.pid"
user = "tireminder"
group = "tireminder"
tmp_upload_dir = None

# SSL (se necessário)
# keyfile = "/path/to/keyfile"
# certfile = "/path/to/certfile"
```

### 3. Configuração do Nginx

Criar `/etc/nginx/sites-available/ti-reminder`:

```nginx
server {
    listen 80;
    server_name seu-dominio.com www.seu-dominio.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name seu-dominio.com www.seu-dominio.com;
    
    # SSL Configuration
    ssl_certificate /etc/letsencrypt/live/seu-dominio.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/seu-dominio.com/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=63072000; includeSubDomains; preload";
    
    # Gzip compression
    gzip on;
    gzip_vary on;
    gzip_min_length 1024;
    gzip_types text/plain text/css text/xml text/javascript application/javascript application/xml+rss application/json;
    
    # Static files
    location /static {
        alias /home/tireminder/ti-reminder-app/app/static;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # Health check
    location /health {
        proxy_pass http://127.0.0.1:8000;
        access_log off;
    }
}
```

### 4. Serviços Systemd

Criar `/etc/systemd/system/ti-reminder.service`:

```ini
[Unit]
Description=TI Reminder App
After=network.target postgresql.service
Requires=postgresql.service

[Service]
Type=notify
User=tireminder
Group=tireminder
RuntimeDirectory=ti-reminder
WorkingDirectory=/home/tireminder/ti-reminder-app
Environment=PATH=/home/tireminder/ti-reminder-app/venv/bin
ExecStart=/home/tireminder/ti-reminder-app/venv/bin/gunicorn -c gunicorn.conf.py wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=on-failure
RestartSec=5

[Install]
WantedBy=multi-user.target
```

## 🚀 Processo de Deploy

### 1. Deploy Manual

```bash
# Script de deploy manual
#!/bin/bash
set -e

echo "🚀 Iniciando deployment..."

# Ativar ambiente virtual
source venv/bin/activate

# Atualizar código
git pull origin main

# Instalar/atualizar dependências
pip install -r requirements.txt

# Executar migrações
flask db upgrade

# Coletar arquivos estáticos (se necessário)
python scripts/minify_assets.py

# Executar testes
python scripts/run_tests.py --unit --integration

# Reiniciar serviços
sudo systemctl restart ti-reminder
sudo systemctl reload nginx

# Verificar saúde
python scripts/health_check.py --wait 10 --retry 3

echo "✅ Deploy concluído com sucesso!"
```

### 2. Deploy Automatizado

```bash
# Usar o script de deploy
python scripts/deploy.py --env production

# Ou para staging
python scripts/deploy.py --env staging
```

### 3. Deploy com Docker (Opcional)

Criar `Dockerfile`:

```dockerfile
FROM python:3.11-slim

WORKDIR /app

# Instalar dependências do sistema
RUN apt-get update && apt-get install -y \
    postgresql-client \
    && rm -rf /var/lib/apt/lists/*

# Copiar requirements e instalar dependências Python
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar código da aplicação
COPY . .

# Criar usuário não-root
RUN useradd --create-home --shell /bin/bash app \
    && chown -R app:app /app
USER app

# Expor porta
EXPOSE 8000

# Comando padrão
CMD ["gunicorn", "-c", "gunicorn.conf.py", "wsgi:app"]
```

Criar `docker-compose.yml`:

```yaml
version: '3.8'

services:
  app:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=postgresql://ti_reminder:password@db:5432/ti_reminder
      - FLASK_ENV=production
    depends_on:
      - db
    volumes:
      - ./logs:/app/logs
    restart: unless-stopped

  db:
    image: postgres:13
    environment:
      - POSTGRES_DB=ti_reminder
      - POSTGRES_USER=ti_reminder
      - POSTGRES_PASSWORD=password
    volumes:
      - postgres_data:/var/lib/postgresql/data
    restart: unless-stopped

  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
      - ./ssl:/etc/ssl
    depends_on:
      - app
    restart: unless-stopped

volumes:
  postgres_data:
```

## 🔒 Segurança

### 1. SSL/TLS com Let's Encrypt

```bash
# Instalar Certbot
sudo apt install certbot python3-certbot-nginx

# Obter certificado
sudo certbot --nginx -d seu-dominio.com -d www.seu-dominio.com

# Renovação automática
sudo crontab -e
# Adicionar: 0 12 * * * /usr/bin/certbot renew --quiet
```

### 2. Firewall

```bash
# UFW (Ubuntu)
sudo ufw allow ssh
sudo ufw allow 'Nginx Full'
sudo ufw enable

# Ou iptables
sudo iptables -A INPUT -p tcp --dport 22 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -A INPUT -p tcp --dport 443 -j ACCEPT
```

### 3. Backup Automatizado

Criar script de backup `/home/tireminder/backup.sh`:

```bash
#!/bin/bash
BACKUP_DIR="/home/tireminder/backups"
DATE=$(date +%Y%m%d_%H%M%S)

# Criar diretório de backup
mkdir -p $BACKUP_DIR

# Backup do banco de dados
pg_dump ti_reminder_prod > $BACKUP_DIR/db_backup_$DATE.sql

# Backup dos arquivos
tar -czf $BACKUP_DIR/files_backup_$DATE.tar.gz /home/tireminder/ti-reminder-app

# Manter apenas últimos 7 dias
find $BACKUP_DIR -name "*.sql" -mtime +7 -delete
find $BACKUP_DIR -name "*.tar.gz" -mtime +7 -delete

echo "Backup concluído: $DATE"
```

Adicionar ao crontab:
```bash
# Backup diário às 2h
0 2 * * * /home/tireminder/backup.sh >> /var/log/backup.log 2>&1
```

## 📊 Monitoramento

### 1. Logs

```bash
# Logs da aplicação
tail -f /var/log/ti-reminder/app.log

# Logs do Nginx
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log

# Logs do sistema
journalctl -u ti-reminder -f
```

### 2. Health Checks

```bash
# Script de monitoramento
#!/bin/bash
while true; do
    if ! python scripts/health_check.py; then
        echo "❌ Health check falhou - $(date)"
        # Enviar alerta (email, Slack, etc.)
    fi
    sleep 300  # 5 minutos
done
```

### 3. Métricas (Opcional)

Integração com Prometheus/Grafana:

```python
# requirements.txt
prometheus-flask-exporter==0.20.3

# app/__init__.py
from prometheus_flask_exporter import PrometheusMetrics

def create_app():
    app = Flask(__name__)
    
    # Métricas Prometheus
    if not app.config.get('TESTING'):
        PrometheusMetrics(app)
    
    return app
```

## 🔄 Rollback

### Processo de Rollback

```bash
#!/bin/bash
# rollback.sh

PREVIOUS_VERSION=$1

if [ -z "$PREVIOUS_VERSION" ]; then
    echo "Uso: ./rollback.sh <commit_hash>"
    exit 1
fi

echo "🔄 Iniciando rollback para $PREVIOUS_VERSION"

# Fazer checkout da versão anterior
git checkout $PREVIOUS_VERSION

# Reinstalar dependências
source venv/bin/activate
pip install -r requirements.txt

# Executar migrações (se necessário)
flask db downgrade

# Reiniciar serviços
sudo systemctl restart ti-reminder

# Verificar saúde
python scripts/health_check.py

echo "✅ Rollback concluído"
```

## 📋 Checklist de Deploy

### Pré-Deploy
- [ ] Testes passando localmente
- [ ] Code review aprovado
- [ ] Backup do banco de dados
- [ ] Variáveis de ambiente configuradas
- [ ] SSL certificado válido

### Durante Deploy
- [ ] Aplicação parada graciosamente
- [ ] Código atualizado
- [ ] Dependências instaladas
- [ ] Migrações executadas
- [ ] Arquivos estáticos coletados
- [ ] Serviços reiniciados

### Pós-Deploy
- [ ] Health check passou
- [ ] Logs sem erros
- [ ] Funcionalidades principais testadas
- [ ] Performance monitorada
- [ ] Backup pós-deploy criado

## 🆘 Troubleshooting

### Problemas Comuns

1. **Aplicação não inicia**
   ```bash
   # Verificar logs
   journalctl -u ti-reminder -n 50
   
   # Verificar configuração
   gunicorn --check-config -c gunicorn.conf.py wsgi:app
   ```

2. **Erro de conexão com banco**
   ```bash
   # Testar conexão
   psql -h localhost -U ti_reminder -d ti_reminder_prod
   
   # Verificar status PostgreSQL
   sudo systemctl status postgresql
   ```

3. **Nginx não servindo arquivos estáticos**
   ```bash
   # Verificar permissões
   ls -la /home/tireminder/ti-reminder-app/app/static/
   
   # Testar configuração Nginx
   sudo nginx -t
   ```

4. **SSL não funcionando**
   ```bash
   # Verificar certificado
   sudo certbot certificates
   
   # Renovar se necessário
   sudo certbot renew
   ```

---

**Última atualização**: 2024-12-10
**Versão**: 1.0.0
