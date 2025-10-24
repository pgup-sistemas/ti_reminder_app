# Plano de Ação - Correção Completa do Sistema de Configurações

**Data**: 24/10/2025  
**Status**: ⚠️ PRONTO PARA IMPLEMENTAÇÃO  
**Impacto**: ALTO - Sistema completamente funcional e confiável

---

## 🎯 Resumo Executivo

### Problema Principal
O sistema de configurações atual não persiste dados entre reinicializações. Todas as alterações em Configurações Gerais, Segurança, Backup, Integrações e Performance são perdidas quando o servidor é reiniciado.

### Solução Implementada
Criar sistema de persistência baseado em banco de dados com modelo `SystemConfig` e serviço `SystemConfigService` que gerencia configurações de forma confiável e auditável.

---

## ✅ O Que Já Foi Feito

### 1. Modelo de Dados (✅ COMPLETO)
**Arquivo**: `app/models.py`

```python
class SystemConfig(db.Model):
    # Modelo completo para armazenamento persistente
    # Suporta tipos: string, int, bool, json, float
    # Inclui auditoria (quem atualizou, quando)
    # Constraint unique em (category, key)
```

**Recursos**:
- ✅ Armazenamento persistente
- ✅ Conversão automática de tipos
- ✅ Auditoria de mudanças
- ✅ Suporte a valores sensíveis

### 2. Serviço de Configuração (✅ COMPLETO)
**Arquivo**: `app/services/system_config_service.py`

```python
class SystemConfigService:
    get(category, key, default)      # Busca configuração
    set(category, key, value)        # Define configuração
    get_category(category)           # Todas configs de uma categoria
    reload_cache()                   # Recarrega cache
    seed_default_configs()           # Popula configs padrão
```

**Recursos**:
- ✅ Cache em memória para performance
- ✅ Sincronização com Flask config
- ✅ Logging de todas as operações
- ✅ Seeds de configurações padrão

### 3. Migration de Banco (✅ COMPLETO)
**Arquivo**: `migrations/versions/add_system_config_table.py`

```python
# Cria tabela system_config
# Adiciona índices para performance
# Inclui função de downgrade
```

---

## 📋 O Que Precisa Ser Feito

### Fase 1: Aplicar Migration e Seeds (⏱️ 5 minutos)

```bash
# 1. Aplicar migration ao banco de dados
flask db upgrade

# 2. Executar seed de configurações padrão
flask shell
>>> from app.services.system_config_service import SystemConfigService
>>> SystemConfigService.seed_default_configs()
>>> exit()
```

**Resultado esperado**: Tabela `system_config` criada com 40+ configurações padrão

### Fase 2: Atualizar Rotas (⏱️ 2-3 horas)

Migrar cada rota de configuração para usar `SystemConfigService`:

#### 2.1 Sistema Geral (`/sistema/geral`)
**Antes**:
```python
current_app.config['SYSTEM_NAME'] = system_name  # ❌ Não persiste
```

**Depois**:
```python
SystemConfigService.set('system', 'name', system_name, 'string', user_id=actor_id)  # ✅ Persiste
```

#### 2.2 Segurança (`/sistema/seguranca`)
#### 2.3 Backup (`/sistema/backup`)
#### 2.4 Integrações Email (`/integracoes/email`)
#### 2.5 Integrações API (`/integracoes/api`)
#### 2.6 RFID (`/integracoes/rfid`)
#### 2.7 Performance (`/performance/otimizacao`)
#### 2.8 Alertas (`/performance/alertas`)

### Fase 3: Sistema de Notificações (⏱️ 1-2 horas)

#### 3.1 Criar Templates de Email
```
app/templates/emails/
├── config_changed.html       # Configuração alterada
├── user_created.html          # Usuário criado
├── user_updated.html          # Usuário atualizado
└── password_reset.html        # Senha resetada
```

#### 3.2 Implementar Helper de Notificação
```python
def send_config_change_notification(actor, category, changes):
    """Envia notificação de alteração de configuração"""
    # Enviar para todos os administradores
    # Incluir detalhes da mudança
    # Registrar no histórico
```

#### 3.3 Adicionar Notificações em Todas as Rotas
- Após cada alteração bem-sucedida
- Incluir detalhes do que foi alterado
- Enviar para usuários relevantes

### Fase 4: Logs Reais do Sistema (⏱️ 1 hora)

#### 4.1 Implementar Leitor de Logs
```python
def read_system_logs(level=None, limit=100, offset=0):
    """Lê logs reais do arquivo"""
    log_file = current_app.config['LOG_FILE']
    # Parse do arquivo
    # Filtros por nível, data, módulo
    # Retorna lista de entradas
```

#### 4.2 Atualizar Rota de Logs
```python
@system_config.route("/sistema/logs")
def system_logs():
    # Buscar logs reais em vez de dados simulados
    logs = read_system_logs(...)
    # Implementar paginação
    # Implementar filtros
```

### Fase 5: Sistema de Backup Real (⏱️ 2-3 horas)

#### 5.1 Implementar Backup de Banco
```python
def backup_database():
    """Cria backup do banco de dados PostgreSQL"""
    # Usar pg_dump
    # Compressão opcional
    # Criptografia opcional
```

#### 5.2 Implementar Backup de Arquivos
```python
def backup_files():
    """Cria backup de arquivos uploaded"""
    # Arquivos de usuários
    # Logs
    # Configurações
```

#### 5.3 Implementar Agendamento
```python
# Adicionar job ao APScheduler
scheduler.add_job(
    id='system_backup',
    func=run_system_backup,
    trigger='cron',
    hour=2,  # 2h da manhã
    minute=0
)
```

#### 5.4 Implementar Restauração
```python
def restore_backup(backup_file):
    """Restaura backup do sistema"""
    # Validar arquivo
    # Restaurar banco
    # Restaurar arquivos
```

---

## 📊 Checklist de Implementação

### Fundação
- [x] Modelo `SystemConfig` criado
- [x] Serviço `SystemConfigService` criado
- [x] Migration criada
- [ ] Migration aplicada ao banco
- [ ] Seeds executados

### Rotas de Configuração
- [ ] Sistema Geral migrado
- [ ] Segurança migrado
- [ ] Backup migrado
- [ ] Email migrado
- [ ] API migrado
- [ ] RFID migrado
- [ ] Performance migrado
- [ ] Alertas migrado

### Notificações
- [ ] Templates de email criados
- [ ] Helper de notificação implementado
- [ ] Notificações de usuário
- [ ] Notificações de configuração
- [ ] Histórico real de notificações

### Logs
- [ ] Leitor de logs implementado
- [ ] Rota de logs atualizada
- [ ] Filtros implementados
- [ ] Download de logs

### Backup
- [ ] Backup de banco implementado
- [ ] Backup de arquivos implementado
- [ ] Agendamento configurado
- [ ] Restauração implementada
- [ ] Notificações de backup

### Testes
- [ ] Testes unitários de SystemConfig
- [ ] Testes de persistência
- [ ] Testes de notificações
- [ ] Testes de backup/restore
- [ ] Testes end-to-end

---

## 🚀 Como Executar

### Passo 1: Aplicar Fundação (AGORA)

```bash
# Terminal 1: Parar servidor se estiver rodando
Ctrl+C

# Terminal 2: Aplicar migration
cd "C:\Users\Oezios Normando\Documents\tireminderapp"
flask db upgrade

# Terminal 3: Executar seeds
flask shell
```

No shell do Flask:
```python
from app.services.system_config_service import SystemConfigService
SystemConfigService.seed_default_configs()
exit()
```

### Passo 2: Testar Fundação

```bash
# Iniciar servidor
python run.py

# Acessar e testar:
# http://192.168.1.86:5000/configuracoes/sistema/geral
```

### Passo 3: Continuar Implementação

Após validar que a fundação funciona, continuar com as fases 2-5.

---

## 📈 Métricas de Sucesso

### Antes
- ❌ 0% configurações persistem
- ❌ 0 notificações enviadas
- ❌ Logs simulados
- ❌ Backup não funcional

### Depois
- ✅ 100% configurações persistem
- ✅ Notificações em todas as ações
- ✅ Logs reais com filtros
- ✅ Backup/restore funcional

---

## 🔍 Testes de Validação

### Teste 1: Persistência
```
1. Alterar configuração em /sistema/geral
2. Reiniciar servidor
3. Verificar se configuração manteve
✅ SUCESSO: Valor mantido após reinício
```

### Teste 2: Notificações
```
1. Alterar qualquer configuração
2. Verificar email recebido
3. Verificar notificação flash
✅ SUCESSO: Notificações enviadas
```

### Teste 3: Logs
```
1. Acessar /sistema/logs
2. Verificar logs reais aparecem
3. Testar filtros
✅ SUCESSO: Logs reais exibidos
```

### Teste 4: Backup
```
1. Executar backup manualmente
2. Verificar arquivo criado
3. Restaurar backup
4. Verificar dados restaurados
✅ SUCESSO: Backup/restore funcional
```

---

## 📞 Próximos Passos Imediatos

**AGORA** (5 minutos):
1. Executar Passo 1 (Migration e Seeds)
2. Testar acesso ao sistema
3. Verificar se tabela foi criada

**DEPOIS** (quando aprovado):
1. Implementar Fase 2 (Rotas)
2. Implementar Fase 3 (Notificações)
3. Implementar Fase 4 (Logs)
4. Implementar Fase 5 (Backup)

---

## 💡 Observações Importantes

1. **Backup antes de tudo**: Faça backup do banco de dados antes de aplicar migrations
2. **Teste em desenvolvimento**: Teste todas as mudanças localmente antes de produção
3. **Rollback disponível**: A migration inclui downgrade se necessário
4. **Zero downtime**: Sistema continua funcionando durante implementação

---

**Arquiteto**: Sistema TI OSN  
**Contato**: Disponível para dúvidas  
**Status**: ✅ PRONTO PARA EXECUÇÃO
