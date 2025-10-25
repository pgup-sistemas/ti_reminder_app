# Tickets & Suporte

O sistema de tickets & suporte permite abrir solicitações de atendimento de forma profissional e acompanhar o andamento até a resolução completa.

## 🎯 Visão Geral

A central de atendimento oferece uma interface completa para:
- ✅ **Solicitar suporte técnico**
- ✅ **Acompanhar andamento** em tempo real
- ✅ **Comunicar com a equipe de TI**
- ✅ **Receber notificações** de atualizações
- ✅ **Consultar histórico** completo

## 📝 Abrindo um Novo Ticket

### Passo a Passo

1. **Acesse o módulo**:
   - Menu principal → **"Tickets & Suporte"**
   - Clique em **"Abrir Novo Ticket"**
   - URL direta: `http://192.168.1.86:5000/chamados/abrir`

2. **Preencha o formulário**:

    === "Informações Básicas"

        | Campo | Obrigatório | Descrição | Dicas |
        |-------|-------------|-----------|-------|
        | **Título** | ✅ | Resumo claro do problema | Seja específico e objetivo |
        | **Descrição** | ✅ | Detalhes completos | Inclua passos para reproduzir |
        | **Prioridade** | ✅ | Nível de urgência | Escolha adequadamente |

    === "Categorias de Prioridade"

        | Prioridade | Quando Usar | Tempo de Resposta | Exemplos |
        |------------|-------------|------------------|----------|
        | **🔴 Crítica** | Sistema fora do ar | Até 2 horas | Servidor caído, rede indisponível |
        | **🟠 Alta** | Funcionalidade importante afetada | Até 4 horas | Sistema lento, erro recorrente |
        | **🟡 Média** | Problema que pode aguardar | Até 24 horas | Funcionalidade secundária |
        | **🔵 Baixa** | Melhorias ou dúvidas | Até 72 horas | Sugestões, treinamentos |

3. **Envio automático**:
   - Sistema envia e-mail para equipe de TI
   - Você recebe confirmação automática
   - Ticket aparece imediatamente na sua lista

## 🔄 Acompanhamento de Tickets

### Status do Ticket

<div class="grid cards" markdown>

-   :material-circle-outline:
    **Aberto**

    ---

    Ticket criado aguardando atendimento da TI

-   :material-progress-clock:
    **Em Andamento**

    ---

    Equipe de TI está trabalhando na solução

-   :material-check-circle-outline:
    **Resolvido**

    ---

    Problema solucionado, aguardando confirmação

-   :material-check-circle:
    **Fechado**

    ---

    Ticket finalizado e arquivado

</div>

### Como Acompanhar

1. **Lista de Chamados**:
   - Veja todos os seus chamados
   - Filtros por status e prioridade
   - Ordenação por data

2. **Detalhes do Chamado**:
   - Clique no chamado para ver informações completas
   - Veja comentários e atualizações
   - Acompanhe o histórico de mudanças

3. **Notificações**:
   - Receba alertas sobre atualizações
   - E-mails automáticos de mudanças de status

## 💬 Sistema de Comentários

### Funcionalidades

- ✅ **Adicionar comentários** com informações adicionais
- ✅ **Comunicar com a TI** diretamente no chamado
- ✅ **Anexar arquivos** (em desenvolvimento)
- ✅ **Histórico completo** de todas as interações
- ✅ **Notificações** de novos comentários

### Boas Práticas

1. **📝 Seja claro e objetivo** nos comentários
2. **🔗 Inclua informações relevantes** sobre o problema
3. **📸 Anexe screenshots** quando possível (em desenvolvimento)
4. **⏰ Atualize o status** se o problema foi resolvido pelo usuário

## 📊 Relatórios e Métricas

### Dados Disponíveis

- 📈 **Tempo de resposta**: Desde abertura até primeira resposta
- ⏱️ **Tempo de solução**: Desde abertura até fechamento
- 📊 **Taxa de resolução**: Percentual de chamados resolvidos
- 🎯 **SLA compliance**: Cumprimento de prazos acordados

### Visualização

- **📊 Dashboard**: Métricas em tempo real
- **📈 Gráficos**: Tendências históricas
- **📋 Exportação**: Relatórios em Excel/PDF
- **🔍 Filtros**: Por período, setor, prioridade

## 🔔 Sistema de Notificações

### Tipos de Notificação

| Evento | Quando Ocorre | Destinatário | Frequência |
|--------|---------------|--------------|------------|
| **📝 Novo chamado** | Imediatamente após abertura | Equipe TI | Imediata |
| **🔄 Atualização de status** | Quando status muda | Solicitante | Por mudança |
| **💬 Novo comentário** | Quando alguém comenta | Todos os envolvidos | Por comentário |
| **⏰ SLA próximo do fim** | Quando prazo está acabando | Responsável TI | Diário |

### Configuração

1. **🔔 Ative no navegador** quando solicitado
2. **📧 Configure e-mail** para notificações importantes
3. **📱 Use o PWA** para notificações push no celular

## 🎯 Níveis de Acesso

### Usuário Comum

- ✅ **Abrir chamados** para si mesmo
- ✅ **Ver chamados** do seu setor
- ✅ **Adicionar comentários**
- ✅ **Receber notificações**

### Equipe de TI

- ✅ **Ver todos os chamados**
- ✅ **Alterar status** e responsável
- ✅ **Adicionar comentários internos**
- ✅ **Gerenciar SLAs**

### Administradores

- ✅ **Todas as funcionalidades** da equipe de TI
- ✅ **Configurar sistema**
- ✅ **Gerenciar usuários**
- ✅ **Relatórios avançados**

## 📋 Boas Práticas

### Ao Abrir um Chamado

1. **📝 Título claro**: Resuma o problema em poucas palavras
2. **🔍 Descrição detalhada**: Inclua passos para reproduzir
3. **📸 Evidências**: Anexe screenshots quando possível
4. **⏰ Prioridade adequada**: Escolha o nível correto de urgência

### Durante o Atendimento

1. **💬 Responda rapidamente** aos comentários da TI
2. **🧪 Teste as soluções** propostas
3. **📝 Forneça feedback** sobre as soluções
4. **✅ Confirme a resolução** quando problema for solucionado

## 🚨 Solução de Problemas

### Problemas Comuns

**❓ Chamado não aparece na lista**
- ✅ Verifique se você tem permissão para vê-lo
- ✅ Use os filtros para localizar
- ✅ Aguarde alguns minutos para sincronização

**❓ Não recebo notificações**
- ✅ Verifique configurações do navegador
- ✅ Confirme se e-mail está correto no perfil
- ✅ Teste notificações na página de configurações

**❓ Status não atualiza**
- ✅ Aguarde processamento do sistema
- ✅ Verifique se há comentários recentes
- ✅ Entre em contato com a TI se problema persistir

## 📚 Recursos Adicionais

- **🎫 Sistema de Chamados**: Para suporte técnico adicional
- **📚 Tutoriais**: Guias sobre funcionalidades específicas
- **❓ FAQ**: Perguntas frequentes sobre chamados
- **📖 Documentação Técnica**: Para administradores e TI

---

<div class="info">
    **Dica**: Mantenha seus chamados atualizados com comentários regulares. Isso ajuda a equipe de TI a entender melhor o problema e fornecer soluções mais eficazes.
</div>