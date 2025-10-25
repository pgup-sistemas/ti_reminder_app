# Notificações Programadas

As notificações programadas são ferramentas profissionais para gerenciar alertas recorrentes e garantir que nenhuma atividade importante seja esquecida.

## 🎯 Visão Geral

O sistema de notificações programadas permite criar alertas automáticos que se repetem em intervalos definidos, com controle inteligente de status e notificações em tempo real.

## 📝 Criando uma Notificação Programada

### Passo a Passo

1. **Acesse o módulo**:
   - Clique em **"Notificações Programadas"** no menu principal
   - Ou acesse diretamente: `http://192.168.1.86:5000/reminders`

2. **Clique em "Nova Notificação"**:
   - Botão localizado no canto superior direito

3. **Preencha o formulário**:

    === "Campos Obrigatórios"

        | Campo | Descrição | Exemplo |
        |-------|-----------|---------|
        | **Nome** | Descrição clara da notificação | "Backup mensal do servidor" |
        | **Tipo** | Categoria para organização | "Manutenção", "Backup", "Auditoria" |
        | **Vencimento** | Data limite para execução | Selecione no calendário |
        | **Responsável** | Quem deve executar a tarefa | "João Silva", "Equipe TI" |

    === "Campos Opcionais"

        | Campo | Descrição | Exemplo |
        |-------|-----------|---------|
        | **Frequência** | Intervalo de recorrência | Diário, Quinzenal, Mensal, Anual |
        | **Setor** | Setor responsável | "TI", "RH", "Financeiro" |
        | **Pausar até** | Data para pausar temporariamente | Data específica |
        | **Data de fim** | Quando a recorrência deve parar | Última ocorrência |

4. **Clique em "Salvar"** para criar a notificação

## 🔄 Recorrência Automática

### Tipos de Frequência

| Frequência | Descrição | Exemplo de Uso |
|------------|-----------|----------------|
| **Diário** | Todo dia útil | Verificação de backups |
| **Quinzenal** | A cada 15 dias | Revisão de equipamentos |
| **Mensal** | Uma vez por mês | Relatórios gerenciais |
| **Anual** | Uma vez por ano | Auditoria completa |

### Como Funciona

1. **Criação Automática**: O sistema cria automaticamente a próxima notificação quando uma é concluída
2. **Controle Inteligente**: Respeita as configurações de pausa e fim de recorrência
3. **Status Visual**: Mostra claramente se está ativo, pausado ou concluído

## 🎮 Controles Disponíveis

### Status das Notificações

<div class="grid cards" markdown>

-   :material-check-circle:
    **Ativo**

    ---

    Notificação ativa e gerando alertas automáticos

-   :material-pause-circle:
    **Pausado**

    ---

    Temporariamente desativado, pode ser reativado

-   :material-check:
    **Concluído**

    ---

    Tarefa realizada, aguarda próxima ocorrência

-   :material-cancel:
    **Cancelado**

    ---

    Permanentemente removido do sistema

</div>

### Ações Rápidas

| Ação | Ícone | Descrição | Atalho |
|------|-------|-----------|--------|
| **Concluir** | ✅ | Marca como realizado | Botão verde |
| **Pausar** | ⏸️ | Pausa temporariamente | Botão amarelo |
| **Reativar** | ▶️ | Volta ao status ativo | Botão azul |
| **Editar** | ✏️ | Modifica informações | Botão azul |
| **Excluir** | 🗑️ | Remove permanentemente | Botão vermelho |

## 🔔 Sistema de Notificações

### Regras Inteligentes

- **🔔 Aparecem**: 7 dias antes do vencimento
- **⏰ Frequência**: Máximo 1x por dia por notificação
- **✅ Param**: Quando concluído ou passa de 7 dias do vencimento
- **🎯 Público**: Apenas o responsável pela notificação

### Como Ativar

1. **Primeira visita**: Clique em "Ativar Agora" na mensagem azul
2. **Configurações**: Permita notificações nas configurações do navegador
3. **Teste**: Clique em "Testar Notificação" para verificar

## 📊 Visualizando Notificações

### Filtros Disponíveis

- **📅 Por Status**: Ativos, Pausados, Concluídos, Cancelados
- **📆 Por Data**: Hoje, Amanhã, Semana, Mês
- **👤 Por Responsável**: Filtrar por pessoa responsável
- **🏢 Por Setor**: Filtrar por setor organizacional
- **🔍 Por Texto**: Busca por nome ou descrição

### Visualização em Lista

Cada notificação mostra:
- ✅ **Nome** e **tipo** da notificação
- 📅 **Data de vencimento**
- 👤 **Responsável** pela execução
- 🏢 **Setor** responsável
- 🔔 **Status** atual
- ⏰ **Próxima ocorrência** (se recorrente)

## 📈 Relatórios e Exportação

### Dados Disponíveis

- 📊 **Lista completa** de notificações
- 📅 **Por período** específico
- 👥 **Por responsável**
- 🏢 **Por setor**
- 📊 **Estatísticas** de conclusão

### Formatos de Exportação

- **📄 Excel**: Para análise detalhada
- **📋 PDF**: Para relatórios formais
- **🖨️ Imprimir**: Visualização otimizada para impressão

## 💡 Dicas e Boas Práticas

### Organização Eficiente

1. **📝 Nomes Descritivos**: Use nomes claros e específicos
2. **🏷️ Categorização**: Utilize tipos para agrupar notificações similares
3. **📅 Prazos Realistas**: Defina datas alcançáveis
4. **👥 Responsabilidades Claras**: Atribua sempre um responsável

### Uso Avançado

1. **🔄 Recorrência Inteligente**: Configure lembretes que se auto-gerenciam
2. **⏸️ Controle Temporário**: Use pausa para períodos específicos
3. **📊 Acompanhamento**: Monitore padrões de conclusão
4. **🔔 Notificações**: Configure para receber alertas importantes

## 🚨 Solução de Problemas

### Problemas Comuns

**❓ Notificação não aparece na lista**
- ✅ Verifique os filtros aplicados
- ✅ Confirme se não está concluída ou cancelada
- ✅ Verifique as permissões de acesso

**❓ Não recebo notificações**
- ✅ Verifique se estão ativadas no navegador
- ✅ Confirme se a notificação está ativa
- ✅ Teste as notificações na página de notificações programadas

**❓ Recorrência não funciona**
- ✅ Verifique se há data de fim configurada
- ✅ Confirme se não está pausado
- ✅ Verifique logs do sistema

## 📚 Recursos Adicionais

- **🎫 Tickets & Suporte**: Para atendimento técnico
- **📚 Base de Conhecimento**: Guias detalhados de uso
- **❓ FAQ**: Perguntas frequentes
- **📖 Documentação Completa**: Guias avançados

---

<div class="info">
    **Dica**: Use notificações programadas para tarefas que se repetem regularmente, como backups, auditorias e revisões periódicas.
</div>