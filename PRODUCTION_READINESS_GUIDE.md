# Guia de Prontidão para Produção - TI Reminder App

## 🎯 Verificação Automática de Prontidão

### Comando Principal
```bash
# Executar verificação completa
python scripts/production_readiness_check.py
```

Este script verifica automaticamente:
- ✅ Dependências instaladas e compatíveis
- ✅ Qualidade do código (flake8, black, isort)
- ✅ Vulnerabilidades de segurança
- ✅ Todos os testes (unitários, integração, coverage)
- ✅ Migrações do banco de dados
- ✅ Configurações essenciais
- ✅ Otimizações de performance

### Códigos de Saída
- `0`: Sistema pronto para produção
- `1`: Pronto com avisos (pode prosseguir)
- `2`: Não está pronto (problemas críticos)
- `3`: Erro inesperado

## 📋 Passo a Passo para Produção

### **FASE 1: Preparação Local**

#### 1.1 Instalar Dependências de Teste
```bash
pip install -r requirements-test.txt
```

#### 1.2 Configurar Variáveis de Ambiente
```bash
# Criar arquivo .env para produção
cat > .env << EOF
FLASK_ENV=production
SECRET_KEY=$(python -c "import secrets; print(secrets.token_hex(32))")
DATABASE_URL=postgresql://usuario:senha@host:5432/ti_reminder_prod
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USE_TLS=True
MAIL_USERNAME=seu_email@empresa.com
MAIL_PASSWORD=sua_senha_app
LOG_LEVEL=INFO
LOG_FILE=/var/log/ti-reminder/app.log
TIMEZONE=America/Sao_Paulo
EOF
```

#### 1.3 Verificar Prontidão
```bash
# Executar verificação automática
python scripts/production_readiness_check.py

# Se houver problemas, corrigi-los antes de continuar
```

### **FASE 2: Validação Completa**

#### 2.1 Executar Pipeline de Testes
```bash
# Pipeline completo com todos os testes
python scripts/run_tests.py --all

# Ou executar por partes
python scripts/run_tests.py --lint --security
python scripts/run_tests.py --unit --integration
```

#### 2.2 Verificar Coverage
```bash
# Coverage deve ser >= 70%
pytest --cov=app --cov-report=html --cov-report=term-missing --cov-fail-under=70

# Ver relatório detalhado
open htmlcov/index.html
```

#### 2.3 Testes de Segurança
```bash
# Verificar vulnerabilidades
safety check

# Análise estática de segurança
bandit -r app/ -f json
```

### **FASE 3: Preparação do Servidor**

#### 3.1 Configurar Servidor de Produção
```bash
# No servidor de produção
sudo apt update
sudo apt install python3 python3-pip python3-venv postgresql nginx

# Criar usuário dedicado
sudo useradd -m -s /bin/bash tireminder
sudo usermod -aG sudo tireminder
```

#### 3.2 Configurar Banco de Dados
```bash
# PostgreSQL
sudo -u postgres psql
CREATE DATABASE ti_reminder_prod;
CREATE USER ti_reminder WITH PASSWORD 'senha_forte_aqui';
GRANT ALL PRIVILEGES ON DATABASE ti_reminder_prod TO ti_reminder;
\q
```

#### 3.3 Deploy da Aplicação
```bash
# No servidor
git clone https://github.com/seu-usuario/ti-reminder-app.git
cd ti-reminder-app

# Ambiente virtual
python3 -m venv venv
source venv/bin/activate

# Dependências
pip install -r requirements.txt
pip install gunicorn psycopg2-binary

# Configurar variáveis de ambiente
cp .env.example .env
# Editar .env com configurações de produção
```

### **FASE 4: Deploy Automatizado**

#### 4.1 Deploy para Staging (Opcional)
```bash
# Deploy para ambiente de teste
python scripts/deploy.py --env staging

# Testar funcionalidades críticas
python scripts/health_check.py --url http://staging.seudominio.com
```

#### 4.2 Deploy para Produção
```bash
# Backup antes do deploy
python scripts/deploy.py --env production

# Ou deploy manual com verificações
./deploy_manual.sh
```

#### 4.3 Verificação Pós-Deploy
```bash
# Health check completo
python scripts/health_check.py --retry 3 --wait 10

# Testar endpoints críticos
curl -f http://seudominio.com/health
curl -f http://seudominio.com/auth/login
```

## 🔍 Checklist de Validação Manual

### **Antes do Deploy**
- [ ] Todos os testes passando (unitários, integração)
- [ ] Coverage >= 70%
- [ ] Sem vulnerabilidades críticas de segurança
- [ ] Código formatado (black, isort, flake8)
- [ ] Variáveis de ambiente configuradas
- [ ] SECRET_KEY forte (>= 32 caracteres)
- [ ] DATABASE_URL configurada para produção
- [ ] Migrações atualizadas
- [ ] Backup do banco atual

### **Durante o Deploy**
- [ ] Aplicação parada graciosamente
- [ ] Código atualizado (git pull)
- [ ] Dependências atualizadas
- [ ] Migrações executadas
- [ ] Arquivos estáticos coletados
- [ ] Serviços reiniciados
- [ ] Health check passou

### **Após o Deploy**
- [ ] Aplicação respondendo
- [ ] Login funcionando
- [ ] Funcionalidades principais testadas
- [ ] Logs sem erros críticos
- [ ] Performance aceitável
- [ ] SSL funcionando (se aplicável)
- [ ] Backup pós-deploy criado

## 🚨 Critérios de Bloqueio

### **NÃO FAZER DEPLOY SE:**
- ❌ Testes unitários falhando
- ❌ Coverage < 70%
- ❌ Vulnerabilidades críticas de segurança
- ❌ SECRET_KEY padrão ou muito simples
- ❌ FLASK_DEBUG=True
- ❌ Migrações pendentes
- ❌ Dependências com conflitos

### **AVISOS (Pode prosseguir com cuidado):**
- ⚠️ Alguns testes de integração falhando
- ⚠️ Problemas menores de formatação
- ⚠️ Assets não minificados
- ⚠️ Logs não configurados

## 🔧 Comandos Essenciais

### **Verificação Rápida**
```bash
# Status geral do sistema
python scripts/production_readiness_check.py

# Apenas testes críticos
python scripts/run_tests.py --unit --security

# Health check da aplicação
python scripts/health_check.py
```

### **Deploy Completo**
```bash
# Pipeline completo automatizado
python scripts/deploy.py --env production

# Deploy manual com controle
python scripts/run_tests.py --all && \
python scripts/deploy.py --env production && \
python scripts/health_check.py --retry 3
```

### **Rollback de Emergência**
```bash
# Voltar para versão anterior
git log --oneline -10  # Ver últimos commits
./rollback.sh <commit_hash>

# Ou usar backup
pg_restore backup_db_YYYYMMDD_HHMMSS.sql
```

## 📊 Métricas de Qualidade

### **Mínimas para Produção:**
- **Coverage de Testes**: >= 70%
- **Tempo de Resposta**: < 2 segundos
- **Disponibilidade**: >= 99%
- **Vulnerabilidades**: 0 críticas
- **Erros de Código**: 0 (flake8)

### **Ideais:**
- **Coverage de Testes**: >= 85%
- **Tempo de Resposta**: < 1 segundo
- **Disponibilidade**: >= 99.9%
- **Performance Score**: >= 90

## 🎯 Exemplo de Execução Completa

```bash
# 1. Verificação inicial
echo "🔍 Verificando prontidão..."
python scripts/production_readiness_check.py

# 2. Se passou, executar testes completos
if [ $? -eq 0 ]; then
    echo "✅ Sistema pronto! Executando testes..."
    python scripts/run_tests.py --all
    
    # 3. Se testes passaram, fazer deploy
    if [ $? -eq 0 ]; then
        echo "🚀 Fazendo deploy..."
        python scripts/deploy.py --env production
        
        # 4. Verificar se deploy funcionou
        if [ $? -eq 0 ]; then
            echo "🎉 Deploy concluído! Verificando saúde..."
            python scripts/health_check.py --retry 3
        fi
    fi
fi
```

## 📞 Suporte e Troubleshooting

### **Problemas Comuns:**

1. **Testes falhando**
   ```bash
   pytest tests/ -v --tb=long  # Ver detalhes
   pytest --lf  # Executar apenas os que falharam
   ```

2. **Erro de dependências**
   ```bash
   pip install -r requirements.txt --upgrade
   pip check  # Verificar conflitos
   ```

3. **Problemas de migração**
   ```bash
   flask db current  # Ver migração atual
   flask db upgrade  # Aplicar migrações
   ```

4. **Aplicação não responde**
   ```bash
   systemctl status ti-reminder  # Ver status do serviço
   journalctl -u ti-reminder -f  # Ver logs
   ```

### **Contatos de Emergência:**
- **DevOps**: devops@empresa.com
- **DBA**: dba@empresa.com  
- **Segurança**: security@empresa.com

---

**🎯 RESUMO**: Use `python scripts/production_readiness_check.py` para verificação automática completa. Se retornar código 0, o sistema está pronto para produção!
