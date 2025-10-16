# Administração do Sistema de Performance

Guia completo para administradores monitorarem e otimizarem a performance do sistema TI OSN, garantindo alta disponibilidade e eficiência operacional.

## Visão Geral do Sistema

### Componentes Monitorados

#### Infraestrutura
- **Servidor**: CPU, memória, disco, rede
- **Banco de Dados**: PostgreSQL com métricas específicas
- **Aplicação**: Flask com métricas de performance
- **Cache**: Redis (se implementado)

#### Métricas Principais
- **Latência**: Tempo de resposta das APIs
- **Throughput**: Requisições por segundo
- **Disponibilidade**: Uptime do sistema
- **Erros**: Taxa de falhas por endpoint

## Configuração do Monitoramento

### 1. Thresholds de Alerta

#### Configurações Recomendadas
```python
PERFORMANCE_THRESHOLDS = {
    'cpu_warning': 70,      # % CPU para aviso
    'cpu_critical': 85,     # % CPU crítico
    'memory_warning': 80,   # % Memória para aviso
    'memory_critical': 90,  # % Memória crítico
    'disk_warning': 85,     # % Disco para aviso
    'disk_critical': 95,    # % Disco crítico
    'response_time_warning': 2.0,  # Segundos
    'response_time_critical': 5.0, # Segundos
    'error_rate_warning': 5,       # % erros
    'error_rate_critical': 10,     # % erros
}
```

#### Personalização por Ambiente
- **Desenvolvimento**: Thresholds mais permissivos
- **Homologação**: Valores intermediários
- **Produção**: Thresholds rigorosos

### 2. Canais de Notificação

#### Configuração de Alertas
```python
ALERT_CHANNELS = {
    'email': {
        'enabled': True,
        'recipients': ['admin@empresa.com', 'ti@empresa.com'],
        'severity_levels': ['warning', 'critical']
    },
    'slack': {
        'enabled': True,
        'webhook_url': 'https://hooks.slack.com/...',
        'channel': '#alerts-performance'
    },
    'sms': {
        'enabled': False,
        'provider': 'twilio',
        'numbers': ['+5511999999999']
    }
}
```

## Dashboard de Performance

### Métricas em Tempo Real

#### Visualizações Principais
- **CPU/Memória/Disco**: Gráficos de linha em tempo real
- **Conexões DB**: Número de conexões ativas
- **Cache Hit Ratio**: Eficiência do cache PostgreSQL
- **Latência de Queries**: Tempo médio de resposta

#### Drill-Down Analytics
- **Por Endpoint**: Performance por rota da API
- **Por Usuário**: Impacto de usuários específicos
- **Por Período**: Tendências horárias/diárias
- **Por Tipo de Query**: SELECT vs INSERT vs UPDATE

### Relatórios Automáticos

#### Relatório Diário
```python
DAILY_REPORT_CONFIG = {
    'metrics': [
        'avg_response_time',
        'total_requests',
        'error_rate',
        'db_connections_peak',
        'cache_hit_ratio'
    ],
    'format': 'html',  # html, pdf, json
    'recipients': ['management@empresa.com'],
    'schedule': '08:00'  # Horário de envio
}
```

#### Relatório Semanal
- **Tendências**: Comparativo com semana anterior
- **Picos de Uso**: Identificação de bottlenecks
- **Recomendações**: Ações de otimização

## Otimizações Automáticas

### 1. Otimização de Banco de Dados

#### Índices Automáticos
```sql
-- Criação automática de índices
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_performance_logs_timestamp
ON performance_logs (timestamp DESC);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_chamado_status_performance
ON chamado (status, data_abertura)
WHERE status IN ('Aberto', 'Em Andamento');
```

#### Configurações Dinâmicas
```sql
-- Ajuste automático de parâmetros PostgreSQL
ALTER SYSTEM SET work_mem = '128MB';
ALTER SYSTEM SET maintenance_work_mem = '256MB';
ALTER SYSTEM SET effective_cache_size = '2GB';
```

### 2. Otimização de Aplicação

#### Cache Inteligente
- **Query Result Cache**: Cache de resultados frequentes
- **Template Cache**: Cache de templates Jinja2
- **Static Files**: Cache de assets estáticos

#### Connection Pooling
```python
# Configuração do pool de conexões
SQLALCHEMY_POOL_SIZE = 20
SQLALCHEMY_MAX_OVERFLOW = 30
SQLALCHEMY_POOL_TIMEOUT = 30
SQLALCHEMY_POOL_RECYCLE = 3600
```

### 3. Otimização de Queries

#### Query Optimization
```python
# Exemplo de query otimizada
def get_chamados_optimized(user_id, status=None, limit=50):
    query = db.session.query(Chamado).options(
        # Carregamento eager de relacionamentos
        joinedload(Chamado.solicitante),
        joinedload(Chamado.responsavel_ti),
        joinedload(Chamado.setor)
    ).filter(Chamado.solicitante_id == user_id)

    if status:
        query = query.filter(Chamado.status == status)

    return query.order_by(Chamado.data_abertura.desc()).limit(limit).all()
```

## Troubleshooting de Performance

### Problemas Comuns e Soluções

#### 1. Alto Uso de CPU
**Sintomas**: Sistema lento, timeouts
**Causas Possíveis**:
- Queries não otimizadas
- Loops infinitos
- Processamento excessivo

**Soluções**:
```bash
# Identificar processos com alto CPU
ps aux --sort=-%cpu | head -10

# Analisar queries lentas
EXPLAIN ANALYZE SELECT * FROM tabela WHERE condicao;
```

#### 2. Alto Uso de Memória
**Sintomas**: Out of memory, swapping
**Causas Possíveis**:
- Memory leaks
- Datasets grandes em memória
- Configuração inadequada

**Soluções**:
```python
# Monitorar uso de memória
import tracemalloc
tracemalloc.start()
# ... código ...
current, peak = tracemalloc.get_traced_memory()
print(f"Current memory usage: {current / 1024 / 1024:.1f} MB")
print(f"Peak memory usage: {peak / 1024 / 1024:.1f} MB")
```

#### 3. Queries Lentas
**Sintomas**: Timeouts, lentidão geral
**Causas Possíveis**:
- Falta de índices
- Queries complexas
- Lock de tabelas

**Soluções**:
```sql
-- Analisar query lenta
EXPLAIN (ANALYZE, BUFFERS) SELECT * FROM tabela WHERE condicao;

-- Verificar locks
SELECT * FROM pg_locks WHERE NOT granted;
```

#### 4. Conexões de Banco Excedidas
**Sintomas**: Erro "too many connections"
**Causas Possíveis**:
- Connection leaks
- Pool inadequado
- Queries long-running

**Soluções**:
```sql
-- Verificar conexões ativas
SELECT count(*) as active_connections FROM pg_stat_activity;

-- Configurar pool
ALTER SYSTEM SET max_connections = 200;
```

## Estratégias de Escalabilidade

### 1. Horizontal Scaling

#### Load Balancing
```nginx
upstream ti_osn_app {
    server app1:5000;
    server app2:5000;
    server app3:5000;
}

server {
    listen 80;
    location / {
        proxy_pass http://ti_osn_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

#### Database Replication
```sql
-- Configuração de réplica
ALTER SYSTEM SET wal_level = replica;
ALTER SYSTEM SET max_wal_senders = 3;
ALTER SYSTEM SET hot_standby = on;
```

### 2. Vertical Scaling

#### Otimização de Recursos
- **CPU**: Upgrade para processadores mais rápidos
- **Memória**: Aumento de RAM
- **Disco**: SSDs de alta performance
- **Rede**: Conexões de alta velocidade

### 3. Cache Strategies

#### Redis Implementation
```python
from flask_caching import Cache

cache = Cache(config={
    'CACHE_TYPE': 'redis',
    'CACHE_REDIS_HOST': 'localhost',
    'CACHE_REDIS_PORT': 6379,
    'CACHE_REDIS_DB': 0
})

@cache.memoize(timeout=300)  # Cache por 5 minutos
def get_dashboard_data(user_id):
    # Dados do dashboard
    return expensive_query(user_id)
```

## Monitoramento Avançado

### APM (Application Performance Monitoring)

#### Ferramentas Recomendadas
- **New Relic**: Monitoramento completo
- **Datadog**: Métricas e alertas
- **Prometheus + Grafana**: Stack open source
- **Application Insights**: Para Azure

#### Métricas Customizadas
```python
from flask import g
import time

@app.before_request
def start_timer():
    g.start = time.time()

@app.after_request
def log_request(response):
    if hasattr(g, 'start'):
        duration = time.time() - g.start
        # Log para sistema de monitoramento
        log_performance_metric('request_duration', duration, {
            'endpoint': request.endpoint,
            'method': request.method,
            'status_code': response.status_code
        })
    return response
```

### Log Analysis

#### Estrutura de Logs
```json
{
    "timestamp": "2024-01-15T10:30:00Z",
    "level": "INFO",
    "service": "ti-osn",
    "endpoint": "/api/chamados",
    "user_id": 123,
    "response_time": 0.234,
    "status_code": 200,
    "user_agent": "Mozilla/5.0...",
    "ip_address": "192.168.1.100"
}
```

#### Análise com ELK Stack
- **Elasticsearch**: Indexação de logs
- **Logstash**: Processamento e transformação
- **Kibana**: Visualização e dashboards

## Plano de Contingência

### Cenários de Falha

#### 1. Falha de Banco de Dados
**Plano**:
- Failover automático para réplica
- Notificação imediata para equipe
- Roteamento de leitura para réplicas

#### 2. Sobrecarga de CPU/Memória
**Plano**:
- Auto-scaling horizontal
- Throttling de requests
- Queue de requests não críticos

#### 3. Ataque DDoS
**Plano**:
- WAF (Web Application Firewall)
- Rate limiting
- CDN para absorver tráfego

### Testes de Stress

#### Ferramentas Recomendadas
```bash
# Apache Bench
ab -n 1000 -c 10 http://localhost:5000/

# Locust (Python)
from locust import HttpUser, task

class WebsiteUser(HttpUser):
    @task
    def index(self):
        self.client.get("/")
```

## Manutenção Preventiva

### Tarefas Regulares

#### Diária
- Verificação de logs de erro
- Monitoramento de espaço em disco
- Backup de banco de dados

#### Semanal
- Análise de performance trends
- Otimização de queries lentas
- Atualização de dependências

#### Mensal
- Revisão de configurações
- Testes de carga
- Relatórios de capacity planning

### Automação de Manutenção

#### Scripts de Manutenção
```bash
#!/bin/bash
# maintenance.sh

# Backup do banco
pg_dump ti_reminder_db > backup_$(date +%Y%m%d).sql

# Limpeza de logs antigos
find /var/log/ti-osn -name "*.log" -mtime +30 -delete

# Otimização de tabelas
psql -d ti_reminder_db -c "VACUUM ANALYZE;"

# Reinício controlado
systemctl restart ti-osn-app
```

## Suporte e Documentação

### Recursos de Suporte
- **Documentação Técnica**: docs/dev-guide/
- **Runbooks**: Procedimentos de resolução
- **Equipe de Plantão**: Contatos 24/7
- **Ferramentas de Debug**: Scripts de diagnóstico

### Métricas de SLA
- **Disponibilidade**: 99.9% (8.76h downtime/mês)
- **Tempo de Resposta**: < 2s para 95% das requests
- **Taxa de Erro**: < 1% de erro
- **RPO/RTO**: 1h / 4h (objetivos de recuperação)