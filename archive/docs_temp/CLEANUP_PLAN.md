# 🧹 Plano de Limpeza do Projeto - TI Reminder App

## 📊 Análise da Situação Atual

### Problemas Identificados

1. **Scripts na Raiz (23 arquivos Python)**
   - Migração de BD obsoletos ou já executados
   - Scripts de verificação/debug temporários
   - Duplicação de funcionalidades

2. **Scripts em /scripts (15 arquivos)**
   - Scripts de refatoração já executados
   - Scripts de otimização pontuais
   - Alguns scripts úteis a manter

3. **Documentação Excessiva (48 arquivos .md)**
   - Relatórios de desenvolvimento temporários
   - Documentação duplicada
   - Análises pontuais de problemas já resolvidos

---

## 🗂️ Categorização dos Scripts

### ✅ MANTER - Scripts Úteis

#### Na Raiz:
- `config.py` - Configuração principal ✓
- `run.py` - Execução da aplicação ✓
- `wsgi.py` - Deploy em produção ✓
- `init_db.py` - Inicialização do banco ✓

#### Em /scripts:
- `db_manager.py` - Gerenciamento centralizado de BD ✓
- `deploy.py` - Script de deploy ✓
- `health_check.py` - Verificação de saúde do sistema ✓
- `production_readiness_check.py` - Verificação de produção ✓
- `run_tests.py` - Execução de testes ✓

---

### 🗑️ REMOVER - Scripts Obsoletos

#### Scripts de Refatoração (JÁ EXECUTADOS):
```
scripts/
  ├── final_flash_cleanup.py          # Refatoração de flash() concluída
  ├── update_flash_calls.py           # Refatoração de flash() concluída
  ├── update_flash_advanced.py        # Refatoração de flash() concluída
  ├── update_alert_calls.py           # Refatoração de alert() concluída
  └── validate_refactoring.py         # Validação já executada
```

#### Scripts de Migração Específica (JÁ EXECUTADOS):
```
raiz/
  ├── add_columns.py                  # Migração específica antiga
  ├── add_satisfaction_fields.py      # Migração específica antiga
  ├── apply_equipment_migration.py    # Migração específica antiga
  ├── apply_migration.py              # Substituído por db_manager.py
  ├── direct_migration.py             # Migração específica antiga
  ├── fix_certification_columns.py    # Migração específica antiga
  ├── fix_reservation_datetime.py     # Migração específica antiga
  ├── run_migration.py                # Substituído por db_manager.py
  └── run_migration_manual.py         # Substituído por db_manager.py
```

#### Scripts de Debug/Teste Temporários:
```
raiz/
  ├── check_db_direct.py              # Debug temporário
  ├── check_loans.py                  # Debug temporário
  ├── check_migration.py              # Substituído por db_manager.py
  ├── check_reservations.py           # Debug temporário
  ├── check_tables.py                 # Debug temporário
  ├── check_user_table.py             # Debug temporário
  ├── test_db_connection.py           # Substituído por db_manager.py
  ├── test_equipment_routes.py        # Testes devem estar em /tests
  └── test_notification.py            # Testes devem estar em /tests
```

#### Scripts de Utilidades Temporárias:
```
raiz/
  ├── create_test_data.py             # Útil mover para /scripts
  ├── optimize_performance.py         # Otimização já aplicada
  ├── config_production.py            # Consolidado em config.py
  └── system_config_model.py          # Documentação conceitual

scripts/
  ├── cleanup_legacy.py               # Usar uma vez e remover
  ├── code_splitting.py               # Otimização não utilizada
  ├── minify_assets.py                # Não está em uso
  └── optimize_images.py              # Não está em uso
```

---

### 📝 DOCUMENTAÇÃO - Organizar

#### REMOVER - Relatórios Temporários (31 arquivos):
```
ANALISE_SISTEMA_NOTIFICACOES.md
CALENDAR_FIX_REPORT.md
COMO_FUNCIONA_SOLICITACAO_NOTIFICACOES.md
CORRECOES_FINAIS.md
DASHBOARD_ANALYSIS.md
DASHBOARD_UNIFORMIZATION_COMPLETE.md
DEBUG_RESERVATIONS.md
DIFERENCA_NOTIFICACOES.md
EQUIPMENT_AUDIT_REPORT.md
EQUIPMENT_FIX_DATABASE.md
EQUIPMENT_IMPROVEMENTS.md
EQUIPMENT_PENDING_APPROVALS_FIX.md
EQUIPMENT_RESERVATIONS_FIXED.md
EQUIPMENT_ROUTES_STATUS.md
EQUIPMENT_SCHEDULE_FEATURE.md
EXPORTACAO_PDF_CHAMADOS.md
FRONTEND_AJUSTADO.md
INSTRUCOES_TESTE_DEBUG.md
LIMPAR_CACHE.md
MENU_REORGANIZATION_ANALYSIS.md
MENU_UPDATE_DOCUMENTATION.md
MIGRATION_OLD_TO_NEW_CALENDAR.md
MIGRATION_SUMMARY.md
PLANO_ACAO_NOTIFICACOES.md
REFACTORED_RESERVATION_CALENDAR.md
REFACTORING_COMPLETE_REPORT.md
REFACTORING_SUMMARY.txt
RELATORIO_SISTEMA_ANTIGO.md
SISTEMA_EQUIPAMENTOS_V2_LIMPO.md
SISTEMA_FUNCIONANDO.md
SISTEMA_NOTIFICACOES_IMPLEMENTADO.md
SISTEMA_V2_ATIVADO.md
SISTEMA_V2_PRONTO.md
SOLUCAO_FINAL_CALENDARIO.md
TESTE_CALENDARIO.md
```

#### MANTER - Documentação Útil:
```
README.md                           # Principal ✓
DEPLOYMENT_GUIDE.md                 # Útil ✓
PRODUCTION_READINESS_GUIDE.md       # Útil ✓
QUICK_START.md                      # Útil ✓
TESTING_GUIDE.md                    # Útil ✓
COMPONENTS_GUIDE.md                 # Útil ✓
FRONTEND_STANDARDS.md               # Útil ✓
REFACTORING_GUIDE.md               # Útil ✓
REMINDER_IMPROVEMENTS.md            # Referência útil ✓
PERFORMANCE_OPTIMIZATION.md         # Referência útil ✓
ROTEIRO_TESTES_NOTIFICACOES.md     # Útil para testes ✓
```

---

## 🎯 Estratégia de Limpeza

### Fase 1: Criar Estrutura de Backup

```bash
# Criar pastas de arquivo
mkdir -p archive/migrations_old
mkdir -p archive/debug_scripts
mkdir -p archive/refactoring_scripts
mkdir -p archive/docs_temp
```

### Fase 2: Mover Scripts Obsoletos

```bash
# Migrações antigas
mv add_columns.py archive/migrations_old/
mv add_satisfaction_fields.py archive/migrations_old/
mv apply_equipment_migration.py archive/migrations_old/
mv apply_migration.py archive/migrations_old/
mv direct_migration.py archive/migrations_old/
mv fix_certification_columns.py archive/migrations_old/
mv fix_reservation_datetime.py archive/migrations_old/
mv run_migration.py archive/migrations_old/
mv run_migration_manual.py archive/migrations_old/

# Debug/Teste temporários
mv check_*.py archive/debug_scripts/
mv test_db_connection.py archive/debug_scripts/
mv test_equipment_routes.py archive/debug_scripts/
mv test_notification.py archive/debug_scripts/

# Scripts de refatoração
mv scripts/final_flash_cleanup.py archive/refactoring_scripts/
mv scripts/update_flash_calls.py archive/refactoring_scripts/
mv scripts/update_flash_advanced.py archive/refactoring_scripts/
mv scripts/update_alert_calls.py archive/refactoring_scripts/
mv scripts/validate_refactoring.py archive/refactoring_scripts/

# Outros obsoletos
mv optimize_performance.py archive/
mv config_production.py archive/
mv system_config_model.py archive/
mv scripts/code_splitting.py archive/
mv scripts/minify_assets.py archive/
mv scripts/optimize_images.py archive/
mv scripts/cleanup_legacy.py archive/
```

### Fase 3: Organizar Documentação

```bash
# Mover documentação temporária
mv *_FIX_*.md archive/docs_temp/
mv *_ANALYSIS.md archive/docs_temp/
mv *_COMPLETE*.md archive/docs_temp/
mv *_SUMMARY*.md archive/docs_temp/
mv SISTEMA_*.md archive/docs_temp/
mv DEBUG_*.md archive/docs_temp/
mv INSTRUCOES_*.md archive/docs_temp/
mv CORRECOES_*.md archive/docs_temp/
mv LIMPAR_*.md archive/docs_temp/
mv TESTE_*.md archive/docs_temp/
mv PLANO_*.md archive/docs_temp/
mv COMO_*.md archive/docs_temp/
mv DIFERENCA_*.md archive/docs_temp/
mv EXPORTACAO_*.md archive/docs_temp/
mv FRONTEND_AJUSTADO.md archive/docs_temp/
mv RELATORIO_*.md archive/docs_temp/
mv SOLUCAO_*.md archive/docs_temp/
mv REFACTORED_*.md archive/docs_temp/
mv MIGRATION_*.md archive/docs_temp/
mv MENU_*.md archive/docs_temp/
```

### Fase 4: Consolidar Scripts Úteis

```bash
# Mover create_test_data.py para scripts
mv create_test_data.py scripts/
```

### Fase 5: Limpar Arquivos de Configuração Temporários

```bash
# Remover arquivos temporários
rm -f db_initialized.flag
rm -f pg_version.txt
rm -f .coverage
```

---

## 📋 Resultado Esperado

### Estrutura Final - Raiz:
```
tireminderapp/
├── .env
├── .gitignore
├── config.py              ✓ Config principal
├── init_db.py             ✓ Init BD
├── mkdocs.yml             ✓ Docs
├── pytest.ini             ✓ Testes
├── requirements.txt       ✓ Dependências
├── requirements-docs-full.txt
├── requirements-fixed.txt
├── run.py                 ✓ Executar app
├── runtime.txt            ✓ Python version
├── wsgi.py                ✓ WSGI entry
├── README.md              ✓ Principal
├── DEPLOYMENT_GUIDE.md    ✓
├── PRODUCTION_READINESS_GUIDE.md ✓
├── QUICK_START.md         ✓
├── TESTING_GUIDE.md       ✓
├── COMPONENTS_GUIDE.md    ✓
├── FRONTEND_STANDARDS.md  ✓
├── REFACTORING_GUIDE.md   ✓
├── REMINDER_IMPROVEMENTS.md ✓
├── PERFORMANCE_OPTIMIZATION.md ✓
└── ROTEIRO_TESTES_NOTIFICACOES.md ✓
```

### Estrutura Final - /scripts:
```
scripts/
├── create_test_data.py           ✓ Dados de teste
├── db_manager.py                 ✓ Gerenciar BD
├── deploy.py                     ✓ Deploy
├── health_check.py               ✓ Health check
├── production_readiness_check.py ✓ Prod check
└── run_tests.py                  ✓ Rodar testes
```

### Nova Pasta - /archive:
```
archive/
├── migrations_old/          # Migrações antigas
├── debug_scripts/           # Scripts de debug
├── refactoring_scripts/     # Scripts de refatoração
├── docs_temp/               # Docs temporárias
└── README.md                # Explicação do conteúdo
```

---

## 📊 Estatísticas

### Antes da Limpeza:
- **Scripts na raiz:** 23 arquivos Python
- **Scripts em /scripts:** 15 arquivos
- **Documentação .md:** 48 arquivos
- **Total:** 86+ arquivos

### Depois da Limpeza:
- **Scripts na raiz:** 4 arquivos Python (80% redução)
- **Scripts em /scripts:** 6 arquivos úteis (60% redução)
- **Documentação .md:** 11 arquivos úteis (77% redução)
- **Total:** 21 arquivos principais (75% redução geral)

### Benefícios:
✅ Estrutura mais limpa e organizada
✅ Mais fácil de navegar e entender
✅ Arquivos obsoletos preservados em /archive
✅ Mantém histórico para referência
✅ Facilita onboarding de novos desenvolvedores
✅ Reduz confusão sobre quais scripts usar

---

## ⚠️ Considerações

1. **Backup:** Todos os arquivos serão movidos para `/archive`, não deletados
2. **Git:** Fazer commit antes da limpeza para poder reverter se necessário
3. **Testes:** Executar suite de testes após a limpeza
4. **Documentação:** Criar README.md em `/archive` explicando o conteúdo
5. **Revisão:** Revisar a pasta /archive depois de 3-6 meses e deletar se não for mais necessário

---

## 🚀 Próximos Passos

1. ✅ Revisar este plano
2. ⬜ Fazer commit do estado atual
3. ⬜ Executar script de limpeza automatizado
4. ⬜ Rodar testes para validar
5. ⬜ Atualizar documentação se necessário
6. ⬜ Fazer commit da estrutura limpa
