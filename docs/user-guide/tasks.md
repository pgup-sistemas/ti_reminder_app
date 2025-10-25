# Atividades & Projetos

O sistema de atividades permite organizar e acompanhar workflows específicos com datas definidas e responsáveis atribuídos.

## 🎯 Visão Geral

Diferentemente das notificações programadas (que são recorrentes), as atividades são workflows pontuais com:
- ✅ **Data específica** para conclusão
- ✅ **Responsável definido**
- ✅ **Status de conclusão** (pendente/concluída)
- ✅ **Controle por setor**
- ✅ **Filtros avançados**

## 📝 Criando uma Atividade

### Passo a Passo

1. **Acesse o módulo**:
   - Menu principal → **"Atividades & Projetos"**
   - URL: `http://192.168.1.86:5000/tasks`

2. **Clique em "Nova Atividade"**:
   - Formulário será exibido

3. **Preencha os campos**:

    === "Campos Obrigatórios"

        | Campo | Descrição | Exemplo |
        |-------|-----------|---------|
        | **Descrição** | O que precisa ser feito | "Atualizar sistema operacional dos computadores" |
        | **Data** | Prazo para conclusão | Selecione no calendário |
        | **Responsável** | Quem deve executar | Nome da pessoa ou equipe |

    === "Campos Opcionais"

        | Campo | Descrição | Exemplo |
        |-------|-----------|---------|
        | **Setor** | Setor responsável | "TI", "RH", "Financeiro" |
        | **Concluída** | Marcar se já foi finalizada | Checkbox |

4. **Clique em "Adicionar Atividade"** para salvar

## 📊 Visualizando Atividades

### Filtros Disponíveis

<div class="grid cards" markdown>

-   :material-clock-outline:
    **Pendentes**

    ---

    Atividades que ainda precisam ser concluídas

-   :material-clock-check-outline:
    **Concluídas**

    ---

    Atividades já finalizadas

-   :material-clock-alert-outline:
    **Vencidas**

    ---

    Atividades com data anterior a hoje

-   :material-calendar-today:
    **Hoje**

    ---

    Atividades com vencimento hoje

</div>

### Organização Visual

Cada atividade mostra:
- 📝 **Descrição** da atividade
- 📅 **Data de vencimento**
- 👤 **Responsável** pela execução
- 🏢 **Setor** (se definido)
- ✅ **Status** (pendente/concluída)
- ⏰ **Dias restantes** ou **dias em atraso**

## 🎮 Controles de Atividade

### Ações Disponíveis

| Ação | Ícone | Função | Quando Usar |
|------|-------|--------|-------------|
| **✅ Concluir** | Botão verde | Marca como finalizada | Quando atividade foi executada |
| **✏️ Editar** | Botão azul | Modifica informações | Para alterar data ou descrição |
| **🗑️ Excluir** | Botão vermelho | Remove atividade | Apenas administradores |

### Como Usar

1. **Concluir Atividade**:
   - Clique no botão ✅ verde
   - Atividade fica marcada como concluída
   - Move para seção de atividades finalizadas
   - Move para seção de tarefas finalizadas

2. **Editar Tarefa**:
   - Clique no botão ✏️ azul
   - Modifique descrição, data ou responsável
   - Salve as alterações

3. **Excluir Tarefa**:
   - Clique no botão 🗑️ vermelho
   - Confirme a exclusão
   - Tarefa é removida permanentemente

## 📈 Acompanhamento e Relatórios

### Métricas Disponíveis

- 📊 **Total de tarefas** por período
- ✅ **Taxa de conclusão** por responsável
- ⏰ **Tarefas em atraso** por setor
- 📅 **Produtividade** mensal/trimestral

### Exportação de Dados

- **📄 Excel**: Para análise detalhada
- **📋 PDF**: Para relatórios formais
- **🔍 Filtros**: Por período, responsável, setor

## 💡 Dicas e Boas Práticas

### Organização Eficiente

1. **📝 Descrições claras**: Seja específico sobre o que precisa ser feito
2. **📅 Prazos realistas**: Considere tempo necessário para execução
3. **👥 Responsáveis definidos**: Sempre atribua uma pessoa específica
4. **🏷️ Categorização**: Use setores para organização

### Uso Avançado

1. **📊 Acompanhamento proativo**: Monitore tarefas próximas do vencimento
2. **⏰ Alertas preventivos**: Use para evitar atrasos
3. **📈 Análise de padrões**: Identifique gargalos e oportunidades
4. **🤝 Colaboração**: Atribua tarefas para equilibrar carga de trabalho

## 🔍 Busca e Filtros

### Filtros Rápidos

- **📅 Por data**: Hoje, amanhã, semana, mês personalizado
- **👤 Por responsável**: Filtrar tarefas de uma pessoa específica
- **🏢 Por setor**: Ver apenas tarefas do seu setor
- **🔍 Por texto**: Buscar por palavras na descrição

### Busca Avançada

- **Combinação de filtros**: Use múltiplos filtros simultaneamente
- **Ordenação**: Por data, responsável, setor
- **Exportação filtrada**: Exporte apenas dados filtrados

## 🚨 Gerenciamento de Prazos

### Tarefas Vencidas

- ⏰ **Identificação visual**: Cor diferente para tarefas em atraso
- 📊 **Relatórios específicos**: Lista de tarefas vencidas
- 🔔 **Notificações**: Alertas para tarefas em atraso
- 📈 **Acompanhamento**: Métricas de pontualidade

### Estratégias Preventivas

1. **📅 Monitore regularmente** tarefas próximas do vencimento
2. **⏰ Configure lembretes** para datas importantes
3. **👥 Distribua responsabilidades** de forma equilibrada
4. **📊 Analise padrões** de atraso para identificar causas

## 📱 Integração com Dispositivos

### Progressive Web App

- ✅ **Instalação**: Adicione à tela inicial do celular
- ✅ **Notificações push**: Receba alertas no celular
- ✅ **Offline**: Funciona sem conexão com internet
- ✅ **Sincronização**: Dados sincronizados automaticamente

### Acesso Rápido

- 📱 **Atalho na tela inicial**: Acesso com um toque
- 🔄 **Sincronização automática**: Dados sempre atualizados
- 🔔 **Notificações**: Alertas mesmo com app fechado

## 🚨 Solução de Problemas

### Problemas Comuns

**❓ Tarefa não aparece na lista**
- ✅ Verifique os filtros aplicados
- ✅ Confirme se você tem permissão para vê-la
- ✅ Aguarde sincronização (até 5 minutos)

**❓ Não consigo editar tarefa**
- ✅ Verifique se você é o responsável ou administrador
- ✅ Confirme se a tarefa não está concluída
- ✅ Entre em contato com administrador se problema persistir

**❓ Filtros não funcionam**
- ✅ Limpe os filtros e tente novamente
- ✅ Verifique se há tarefas que atendam aos critérios
- ✅ Recarregue a página

## 📚 Recursos Adicionais

- **🎫 Sistema de Chamados**: Para suporte técnico
- **📚 Tutoriais**: Guias específicos sobre tarefas
- **❓ FAQ**: Perguntas frequentes
- **📖 Documentação Técnica**: Recursos avançados

---

<div class="info">
    **Dica**: Use tarefas para atividades pontuais e lembretes para atividades recorrentes. Combine ambos para uma gestão completa das atividades.
</div>