# Plano de Implementação - Controle de Equipamentos TI

## 📋 Visão Geral
Implementação de funcionalidade para controle de equipamentos solicitados para o setor de TI, permitindo solicitação, aprovação, entrega e devolução de equipamentos.

## 🎯 Objetivos
- Registrar solicitações de equipamentos
- Acompanhar status das solicitações
- Permitir aprovação/recusa pelo setor de TI
- Controlar entrega e devolução de equipamentos
- Gerar relatórios de movimentação

## 📊 Campos do Modelo

### Campos Principais (Solicitados)
- ✅ **Descrição** - Descrição detalhada do equipamento
- ✅ **Patrimônio** - Número do patrimônio do equipamento
- ✅ **Data de entrega** - Data prevista/real da entrega
- ✅ **Solicitante** - Usuário que solicitou o equipamento
- ✅ **Data de devolução** - Data de devolução do equipamento
- ✅ **Conferência** - Status de conferência do equipamento
- ✅ **Observação** - Observações adicionais
- ✅ **Quem recebeu** - Usuário que recebeu o equipamento

### Campos Adicionais Essenciais
- **Status** - (Solicitado, Aprovado, Entregue, Devolvido, Negado)
- **Data da solicitação** - Data automática da solicitação
- **Quem aprovou** - Usuário TI que aprovou a solicitação
- **Data de aprovação** - Data em que foi aprovado
- **Tipo de equipamento** - Categoria (notebook, monitor, etc.)
- **Setor/Destino** - Para onde o equipamento vai
- **Motivo da solicitação** - Justificativa da solicitação

## 🚀 Plano de Implementação Detalhado

### Fase 1: Modelo de Dados
1. **Criar modelo `EquipmentRequest`** em `app/models.py`
   - Definir todos os campos necessários
   - Configurar relacionamentos com User
   - Adicionar métodos auxiliares

2. **Criar migration** para a nova tabela
   - Gerar migration com Alembic
   - Configurar constraints e índices

3. **Executar migration** para criar a tabela no banco
   - Aplicar migration no banco de dados

### Fase 2: Rotas e Controllers
4. **Criar rotas** em `app/routes.py`:
   - `GET /equipment/list` - Listar solicitações
   - `GET /equipment/new` - Formulário nova solicitação
   - `POST /equipment/create` - Criar solicitação
   - `GET /equipment/<id>` - Detalhes da solicitação
   - `GET /equipment/<id>/edit` - Editar solicitação
   - `POST /equipment/<id>/update` - Atualizar solicitação
   - `POST /equipment/<id>/approve` - Aprovar (TI)
   - `POST /equipment/<id>/reject` - Recusar (TI)
   - `POST /equipment/<id>/deliver` - Marcar como entregue
   - `POST /equipment/<id>/return` - Marcar como devolvido

### Fase 3: Templates
5. **Criar templates**:
   - `equipment_list.html` - Listagem de solicitações
   - `equipment_form.html` - Formulário de solicitação
   - `equipment_detail.html` - Detalhes da solicitação
   - `equipment_admin.html` - Painel administrativo TI

### Fase 4: Menu e Navegação
6. **Adicionar item no menu** "Equipamentos"
   - Incluir no template base.html
   - Configurar ícone e link

7. **Configurar permissões** (usuário comum vs TI)
   - Usuário comum: solicitar e ver próprias solicitações
   - TI/Admin: ver todas, aprovar, entregar, devolver

### Fase 5: Funcionalidades Avançadas
8. **Relatórios** (opcional)
   - Relatório de solicitações por período
   - Relatório de equipamentos entregues
   - Relatório de devoluções

9. **Notificações** (opcional)
   - Notificar TI sobre novas solicitações
   - Notificar usuário sobre mudanças de status

10. **Filtros e busca** (opcional)
    - Filtrar por status, data, tipo de equipamento
    - Busca por patrimônio, solicitante

## 🔧 Estrutura do Banco de Dados

### Tabela: equipment_requests
```sql
CREATE TABLE equipment_requests (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    description TEXT NOT NULL,
    patrimony VARCHAR(50),
    delivery_date DATE,
    requester_id INTEGER NOT NULL,
    return_date DATE,
    conference_status VARCHAR(20),
    observations TEXT,
    received_by_id INTEGER,
    status VARCHAR(20) DEFAULT 'Solicitado',
    request_date DATETIME DEFAULT CURRENT_TIMESTAMP,
    approved_by_id INTEGER,
    approval_date DATETIME,
    equipment_type VARCHAR(50),
    destination_sector VARCHAR(100),
    request_reason TEXT,
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    FOREIGN KEY (requester_id) REFERENCES users (id),
    FOREIGN KEY (received_by_id) REFERENCES users (id),
    FOREIGN KEY (approved_by_id) REFERENCES users (id)
);
```

## 📱 Fluxo de Usuário

### Para Usuário Comum:
1. Acessar "Equipamentos" no menu
2. Clicar em "Nova Solicitação"
3. Preencher formulário com dados do equipamento
4. Enviar solicitação
5. Acompanhar status na listagem

### Para TI/Admin:
1. Acessar "Equipamentos" no menu
2. Ver todas as solicitações pendentes
3. Aprovar ou recusar solicitações
4. Marcar como entregue quando equipamento for entregue
5. Marcar como devolvido quando equipamento for devolvido

## 🎨 Interface Sugerida

### Listagem de Equipamentos:
- Tabela com colunas: Patrimônio, Descrição, Solicitante, Status, Data Solicitação, Ações
- Filtros por status, data, tipo
- Botões de ação conforme permissão

### Formulário de Solicitação:
- Campos organizados em seções
- Validação de campos obrigatórios
- Preview da solicitação antes de enviar

### Detalhes da Solicitação:
- Informações completas da solicitação
- Histórico de mudanças de status
- Botões de ação conforme permissão

## ⚡ Próximos Passos

1. **Implementar Fase 1** - Modelo de dados
2. **Testar migration** - Verificar criação da tabela
3. **Implementar Fase 2** - Rotas básicas
4. **Implementar Fase 3** - Templates principais
5. **Testar funcionalidade** - Verificar fluxo completo
6. **Implementar Fase 4** - Menu e permissões
7. **Implementar Fase 5** - Funcionalidades avançadas (opcional)

## 📝 Notas de Desenvolvimento

- Manter consistência com padrões existentes do projeto
- Reutilizar componentes já implementados (forms, alerts, etc.)
- Seguir padrões de segurança já estabelecidos
- Documentar novas funcionalidades
- Testar em diferentes cenários de uso

---

**Status:** 📋 Planejado  
**Prioridade:** 🔥 Alta  
**Estimativa:** 2-3 semanas  
**Responsável:** Equipe de Desenvolvimento 