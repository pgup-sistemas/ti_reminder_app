# 📚 Guia de Atualização - Documentação MkDocs

## 🎯 Objetivo

Atualizar toda a documentação MkDocs para refletir as novas nomenclaturas profissionais do sistema, mantendo consistência entre interface e documentação.

---

## 📋 Inventário de Arquivos para Atualizar

### 1️⃣ **Arquivo de Configuração Principal**

**Arquivo:** `mkdocs.yml`

#### Mudanças Necessárias:

```yaml
# ❌ ANTES
nav:
  - Início: index.md
  - Guia do Usuário:
    - Lembretes: user-guide/reminders.md
    - Chamados: user-guide/chamados.md
    - Tarefas: user-guide/tasks.md
    - Tutoriais: user-guide/tutorials.md
    - Equipamentos: user-guide/equipment.md
```

```yaml
# ✅ DEPOIS (Cenário Premium)
nav:
  - Início: index.md
  - Guia do Usuário:
    - Notificações Programadas: user-guide/reminders.md
    - Service Desk: user-guide/chamados.md
    - Atividades & Projetos: user-guide/tasks.md
    - Base de Conhecimento: user-guide/tutorials.md
    - Gestão de Ativos: user-guide/equipment.md
```

---

### 2️⃣ **Página Inicial da Documentação**

**Arquivo:** `docs/index.md`

#### Seções para Atualizar:

##### A) Título e Descrição
```markdown
# ❌ ANTES
O **TI OSN System** é uma solução completa e profissional para 
gerenciamento de atividades de TI...

# ✅ DEPOIS
O **TI OSN System** é uma plataforma Enterprise de Gestão de TI 
com módulos integrados para Atividades, Service Desk, Asset Management 
e Business Intelligence...
```

##### B) Links de Navegação
```markdown
# ❌ ANTES
- **[Lembretes](user-guide/reminders.md)** - Criação e gerenciamento de lembretes recorrentes
- **[Chamados](user-guide/chamados.md)** - Abrir, acompanhar e gerenciar chamados de suporte
- **[Tarefas](user-guide/tasks.md)** - Gestão de tarefas pontuais com controle de prazos
- **[Tutoriais](user-guide/tutorials.md)** - Base de conhecimento e tutoriais
- **[Equipamentos](user-guide/equipment.md)** - Solicitação e gestão de equipamentos

# ✅ DEPOIS (Cenário Premium)
- **[Notificações Programadas](user-guide/reminders.md)** - Sistema inteligente de alertas automáticos
- **[Service Desk](user-guide/chamados.md)** - Central ITIL de atendimento e suporte técnico
- **[Atividades & Projetos](user-guide/tasks.md)** - Gestão de workflows e deliverables
- **[Base de Conhecimento](user-guide/tutorials.md)** - Knowledge Management e documentação técnica
- **[Gestão de Ativos](user-guide/equipment.md)** - Asset Management completo com RFID
```

##### C) Seção de Funcionalidades
```markdown
# ❌ ANTES
### 📅 Lembretes e Tarefas
- ✅ **Recorrência Automática**: Diária, quinzenal, mensal, anual
...

### 🎫 Sistema de Chamados
- ✅ **Gestão Completa**: Abertura, acompanhamento, fechamento
...

# ✅ DEPOIS
### 🔔 Notificações Programadas & Automação
- ✅ **Engine de Recorrência**: Padrões diários, quinzenais, mensais e anuais
- ✅ **Inteligência de Alertas**: Sistema anti-spam e priorização automática
- ✅ **Workflows Configuráveis**: Regras personalizadas por tipo
...

### 🎯 Service Desk ITIL Compliant
- ✅ **Gestão de Incidentes**: Ciclo completo de atendimento
- ✅ **SLA Automatizado**: Monitoramento e alertas de prazo
- ✅ **Multi-canal**: Email, portal web e notificações push
...

### 📊 Atividades & Gestão de Projetos
- ✅ **Project Tracking**: Acompanhamento de deliverables
- ✅ **Task Management**: Atribuição e delegação de responsabilidades
- ✅ **Gantt Charts**: Visualização de cronogramas (futuro)
...

### 💼 Asset Management Enterprise
- ✅ **Lifecycle Completo**: Da aquisição ao descarte
- ✅ **RFID Tracking**: Rastreamento automático em tempo real
- ✅ **Manutenção Preventiva**: Calendário e alertas automáticos
...
```

---

### 3️⃣ **Documentos de Usuário**

#### A) **user-guide/reminders.md**

**Mudanças Principais:**

```markdown
# ❌ ANTES
# Gestão de Lembretes

Os lembretes são ferramentas poderosas para organizar tarefas recorrentes...

## 📝 Criando um Lembrete

# ✅ DEPOIS
# Sistema de Notificações Programadas

O módulo de Notificações Programadas é uma engine inteligente de automação 
que garante que atividades críticas nunca sejam esquecidas...

## 📝 Programando uma Nova Notificação
```

**Atualizações de Termos:**
- "Lembrete" → "Notificação Programada"
- "Criar lembrete" → "Programar notificação"
- "Lembretes ativos" → "Notificações ativas"
- "Gestão de lembretes" → "Central de notificações"

---

#### B) **user-guide/chamados.md**

**Mudanças Principais:**

```markdown
# ❌ ANTES
# Sistema de Chamados

O sistema de chamados permite solicitar suporte técnico de forma organizada...

## 📝 Abrindo um Novo Chamado

# ✅ DEPOIS
# Service Desk - Central de Atendimento ITIL

O Service Desk é uma plataforma completa de gerenciamento de incidentes 
e solicitações, alinhada com as melhores práticas ITIL v4...

## 📝 Abrindo uma Nova Solicitação
```

**Atualizações de Termos:**
- "Chamado" → "Solicitação" ou "Ticket"
- "Abrir chamado" → "Criar solicitação"
- "Sistema de chamados" → "Service Desk"
- "Chamados em aberto" → "Solicitações ativas"

---

#### C) **user-guide/tasks.md**

**Mudanças Principais:**

```markdown
# ❌ ANTES
# Gestão de Tarefas

Tarefas são atividades pontuais com prazo definido...

# ✅ DEPOIS
# Atividades & Projetos

O módulo de Atividades & Projetos oferece controle completo sobre 
workflows, deliverables e gestão de tempo...
```

**Atualizações de Termos:**
- "Tarefa" → "Atividade" ou "Entrega"
- "Lista de tarefas" → "Backlog de atividades"
- "Tarefa concluída" → "Entrega finalizada"

---

#### D) **user-guide/tutorials.md**

**Mudanças Principais:**

```markdown
# ❌ ANTES
# Tutoriais e Base de Conhecimento

Tutoriais são guias passo a passo para resolver problemas comuns...

# ✅ DEPOIS
# Base de Conhecimento - Knowledge Management

A Base de Conhecimento é um repositório centralizado de documentação 
técnica, procedimentos e best practices...
```

**Atualizações de Termos:**
- "Tutorial" → "Artigo de conhecimento"
- "Criar tutorial" → "Publicar na base"
- "Buscar tutorial" → "Pesquisar knowledge base"

---

#### E) **user-guide/equipment.md**

**Mudanças Principais:**

```markdown
# ❌ ANTES
# Gestão de Equipamentos

Sistema de solicitação e controle de equipamentos de TI...

# ✅ DEPOIS
# Gestão de Ativos - Asset Management

Plataforma completa de Asset Management com controle do ciclo de vida 
completo de ativos de TI, integrada com RFID e manutenção preventiva...
```

**Atualizações de Termos:**
- "Equipamento" → "Ativo" ou "Recurso"
- "Solicitar equipamento" → "Requisitar ativo"
- "Equipamento disponível" → "Ativo disponível"
- "Devolução" → "Retorno de ativo"

---

### 4️⃣ **Documentos Administrativos**

#### **admin-guide/equipment-admin.md**

```markdown
# ❌ ANTES
# Administração de Equipamentos

# ✅ DEPOIS
# Administração de Ativos - Asset Management Console
```

---

## 🔄 Mapeamento Completo de Termos

### Glossário de Substituições

| Termo Antigo | Termo Novo (Premium) | Contexto |
|--------------|---------------------|----------|
| **Lembrete** | **Notificação Programada** | Singular |
| **Lembretes** | **Notificações Programadas** | Plural |
| **Criar lembrete** | **Programar notificação** | Ação |
| **Gestão de lembretes** | **Central de Notificações** | Módulo |
| **Chamado** | **Solicitação** / **Ticket** | Singular |
| **Chamados** | **Solicitações** / **Tickets** | Plural |
| **Abrir chamado** | **Criar solicitação** | Ação |
| **Sistema de chamados** | **Service Desk** | Módulo |
| **Tarefa** | **Atividade** | Singular |
| **Tarefas** | **Atividades** | Plural |
| **Gestão de tarefas** | **Atividades & Projetos** | Módulo |
| **Tutorial** | **Artigo de Conhecimento** | Singular |
| **Tutoriais** | **Base de Conhecimento** | Módulo |
| **Equipamento** | **Ativo** / **Recurso** | Singular |
| **Equipamentos** | **Ativos** / **Recursos** | Plural |
| **Gestão de equipamentos** | **Gestão de Ativos** / **Asset Management** | Módulo |
| **Dashboard** | **Business Intelligence** | Análises |
| **Painel** | **Workspace** | Visão geral |

---

## 📝 Checklist de Atualização

### Fase 1: Estrutura (mkdocs.yml)
- [ ] Atualizar navegação principal
- [ ] Atualizar site_name e site_description
- [ ] Revisar metadata

### Fase 2: Página Inicial (index.md)
- [ ] Atualizar título e descrição
- [ ] Atualizar links de navegação
- [ ] Atualizar seção de funcionalidades
- [ ] Revisar exemplos de uso
- [ ] Atualizar screenshots (se houver)

### Fase 3: Guias de Usuário
- [ ] **reminders.md** → Notificações Programadas
- [ ] **chamados.md** → Service Desk
- [ ] **tasks.md** → Atividades & Projetos
- [ ] **tutorials.md** → Base de Conhecimento
- [ ] **equipment.md** → Gestão de Ativos
- [ ] **dashboard.md** → Business Intelligence

### Fase 4: Guias Administrativos
- [ ] **admin-guide/equipment-admin.md**
- [ ] **admin-guide/security-admin.md**
- [ ] Outros guias admin

### Fase 5: Guias de Desenvolvedor
- [ ] **dev-guide/security-implementation.md**
- [ ] Atualizar referências de API

### Fase 6: Revisão Final
- [ ] Buscar termos antigos remanescentes
- [ ] Validar links internos
- [ ] Testar navegação
- [ ] Rebuild da documentação
- [ ] Deploy

---

## 🔍 Comando para Buscar Termos Antigos

Use grep para encontrar referências que precisam atualização:

```bash
# Buscar "Lembrete" ou "lembretes"
grep -r "embrete" docs/

# Buscar "Chamado" ou "chamados"
grep -r "hamado" docs/

# Buscar "Tarefa" ou "tarefas"
grep -r "arefa" docs/

# Buscar "Tutorial" ou "tutoriais"
grep -r "utorial" docs/

# Buscar "Equipamento" ou "equipamentos"
grep -r "quipamento" docs/
```

---

## 🎨 Melhorias Adicionais para MkDocs

### 1. Adicionar Badges Profissionais

```markdown
# Service Desk - Central de Atendimento

![ITIL](https://img.shields.io/badge/ITIL-v4-blue)
![SLA](https://img.shields.io/badge/SLA-Monitoring-green)
![24/7](https://img.shields.io/badge/Support-24/7-orange)
```

### 2. Adicionar Admonitions Profissionais

```markdown
!!! enterprise "Enterprise Feature"
    Este recurso está disponível na versão Enterprise do sistema.

!!! itil "ITIL Best Practice"
    Alinhado com as práticas recomendadas ITIL v4.

!!! pro "Recurso Avançado"
    Requer permissões de administrador para configuração.
```

### 3. Atualizar Paleta de Cores (mkdocs.yml)

```yaml
theme:
  name: material  # Upgrade para Material theme
  palette:
    # Modo claro
    - scheme: default
      primary: indigo
      accent: blue
      toggle:
        icon: material/brightness-7
        name: Alternar para modo escuro
    # Modo escuro
    - scheme: slate
      primary: indigo
      accent: blue
      toggle:
        icon: material/brightness-4
        name: Alternar para modo claro
  features:
    - navigation.instant
    - navigation.tracking
    - navigation.tabs
    - navigation.sections
    - navigation.expand
    - search.suggest
    - search.highlight
    - content.code.copy
  font:
    text: Inter
    code: Roboto Mono
```

### 4. Adicionar Custom CSS Profissional

**Criar:** `docs/stylesheets/extra.css`

```css
/* Badges profissionais */
.md-typeset .badge-enterprise {
    background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
    color: white;
    padding: 4px 12px;
    border-radius: 12px;
    font-weight: 600;
    font-size: 0.75rem;
}

/* Cards de funcionalidade */
.feature-card {
    border: 1px solid #e0e0e0;
    border-radius: 8px;
    padding: 20px;
    margin: 10px 0;
    background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
}

/* Ícones maiores para módulos principais */
.module-icon {
    font-size: 2rem;
    margin-right: 10px;
}
```

---

## 🚀 Comandos de Build e Deploy

```bash
# Instalar dependências
pip install mkdocs mkdocs-material

# Servir localmente para preview
mkdocs serve

# Build para produção
mkdocs build

# Deploy (se configurado)
mkdocs gh-deploy
```

---

## 📊 Estimativa de Tempo

| Fase | Tempo Estimado | Prioridade |
|------|----------------|------------|
| **mkdocs.yml** | 30 minutos | 🔥 Alta |
| **index.md** | 1 hora | 🔥 Alta |
| **Guias de Usuário** (5 arquivos) | 3-4 horas | 🔥 Alta |
| **Guias Admin** (6 arquivos) | 2-3 horas | ⚠️ Média |
| **Guias Dev** (1 arquivo) | 1 hora | ⚠️ Média |
| **Melhorias visuais** | 2 horas | ℹ️ Baixa |
| **Testes e validação** | 1 hora | 🔥 Alta |
| **TOTAL** | **10-12 horas** | - |

---

## ✅ Benefícios da Atualização

### Para Usuários:
- ✅ Documentação alinhada com interface
- ✅ Terminologia profissional consistente
- ✅ Facilita onboarding de novos usuários

### Para Vendas:
- ✅ Documentação enterprise-grade
- ✅ Alinhamento com frameworks ITIL/ISO
- ✅ Demonstra maturidade do produto

### Para Suporte:
- ✅ Reduz confusão de nomenclatura
- ✅ Base de conhecimento profissional
- ✅ Facilita treinamentos

---

## 🔗 Integração com Sistema

A documentação MkDocs está integrada ao sistema via:

```python
# Link no rodapé e menu principal
url_for('docs.index')  # Rota para documentação
```

**Certifique-se de que:**
- [ ] Links do sistema para docs estão atualizados
- [ ] Breadcrumbs refletem nova nomenclatura
- [ ] Botão "Ajuda" aponta para documentação atualizada

---

## 📞 Próximos Passos

1. **Decidir cenário** (Premium, Equilibrado ou Conservador)
2. **Aprovar glossário** de substituições
3. **Executar atualizações** seguindo checklist
4. **Testar navegação** completa
5. **Deploy** da documentação atualizada

---

**Status:** ⏳ Pronto para Implementação  
**Impacto:** 🔥 Alto (Alinhamento Sistema-Documentação)  
**Esforço:** ⚡ Médio (10-12 horas)  
**Prioridade:** 📊 Alta (Após atualização do front-end)
