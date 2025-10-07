# Gestão de Equipamentos

Solicite equipamentos de TI, acompanhe aprovações e gerencie devoluções de forma organizada e rastreável.

## 🎯 Visão Geral

O módulo de equipamentos oferece controle completo do ciclo de vida dos equipamentos de TI:
- ✅ **Solicitação** de novos equipamentos
- ✅ **Aprovação** por equipe de TI
- ✅ **Entrega** e controle de recebimento
- ✅ **Devolução** e baixa do equipamento
- ✅ **Rastreamento** completo de movimentações

## 📝 Solicitando Equipamentos

### Passo a Passo

1. **Acesse o módulo**:
   - Menu principal → **"Equipamentos"**
   - Clique em **"Nova Solicitação"**
   - URL: `http://192.168.1.86:5000/equipment/new`

2. **Preencha o formulário**:

    === "Dados do Equipamento"

        | Campo | Obrigatório | Descrição | Exemplo |
        |-------|-------------|-----------|---------|
        | **Descrição** | ✅ | O que está solicitando | "Notebook Dell Latitude para desenvolvimento" |
        | **Tipo** | ❌ | Categoria do equipamento | "Notebook", "Monitor", "Impressora" |
        | **Patrimônio** | ❌ | Número do patrimônio (se conhecido) | "TI-2024-001" |
        | **Motivo** | ✅ | Justificativa da solicitação | "Substituição de equipamento com defeito" |

    === "Dados de Entrega"

        | Campo | Obrigatório | Descrição | Exemplo |
        |-------|-------------|-----------|---------|
        | **Setor/Destino** | ✅ | Onde o equipamento será usado | "Setor de Desenvolvimento" |
        | **Data de entrega** | ❌ | Quando precisa receber | Selecione no calendário |
        | **Observações** | ❌ | Informações adicionais | "Urgente para projeto X" |

3. **Envio da solicitação**:
   - Sistema registra automaticamente
   - Equipe de TI é notificada
   - Você recebe confirmação

## 🔄 Fluxo de Aprovação

### Status das Solicitações

<div class="grid cards" markdown>

-   :material-clock-outline:
    **Solicitado**

    ---

    Aguardando análise e aprovação da equipe de TI

-   :material-check-circle-outline:
    **Aprovado**

    ---

    Solicitação aprovada, aguardando entrega

-   :material-package-variant-closed:
    **Entregue**

    ---

    Equipamento entregue ao solicitante

-   :material-package-variant:
    **Devolvido**

    ---

    Equipamento devolvido ao setor de TI

-   :material-close-circle-outline:
    **Negado**

    ---

    Solicitação não aprovada

</div>

### Processo de Aprovação

1. **📝 Análise inicial** pela equipe de TI
2. **✅ Aprovação** ou **❌ Negação** da solicitação
3. **📋 Preenchimento de dados técnicos** (patrimônio, especificações)
4. **📦 Entrega física** do equipamento
5. **✅ Confirmação de recebimento** pelo solicitante

## 📊 Acompanhamento

### Visualizando Solicitações

1. **Lista de equipamentos**:
   - Veja todas as suas solicitações
   - Filtros por status
   - Ordenação por data

2. **Detalhes da solicitação**:
   - Informações completas
   - Histórico de movimentações
   - Dados técnicos do equipamento

### Notificações

- 📧 **E-mail de aprovação** quando solicitação é aprovada
- 📧 **E-mail de entrega** quando equipamento é entregue
- 📧 **Lembretes** para devolução (quando aplicável)

## 🖥️ Dados Técnicos

### Informações Cadastradas

Após aprovação, equipe de TI preenche:

- 🔢 **Número do patrimônio**
- 💻 **Modelo e especificações**
- 📅 **Data de entrega**
- 👤 **Quem recebeu**
- 📋 **Status de conferência**
- 📝 **Observações técnicas**

### Controle de Qualidade

- ✅ **Conferência física** antes da entrega
- ✅ **Testes funcionais** quando necessário
- ✅ **Registro fotográfico** (em desenvolvimento)
- ✅ **Documentação** de entrega

## ♻️ Processo de Devolução

### Quando Devolver

- 🔄 **Equipamento com defeito** para manutenção
- 📦 **Substituição** por modelo mais novo
- 👥 **Transferência** para outro setor
- 🚪 **Término de contrato** ou demissão
- 🔄 **Fim de projeto** ou necessidade

### Como Devolver

1. **Abra um chamado** explicando motivo da devolução
2. **Aguarde instruções** da equipe de TI
3. **Entregue fisicamente** o equipamento
4. **Assine termo de devolução** (quando aplicável)
5. **Sistema registra** devolução automaticamente

## 📋 Tipos de Equipamento

### Categorias Comuns

<div class="grid cards" markdown>

-   :material-laptop:
    **Notebooks**

    ---

    Computadores portáteis para trabalho remoto e mobilidade

-   :material-monitor:
    **Monitores**

    ---

    Telas para estações de trabalho e apresentações

-   :material-keyboard:
    **Periféricos**

    ---

    Teclados, mouses, webcams e outros acessórios

-   :material-printer:
    **Impressoras**

    ---

    Equipamentos para impressão e digitalização

-   :material-cellphone-cog:
    **Dispositivos Móveis**

    ---

    Tablets e smartphones corporativos

-   :material-router-wireless:
    **Equipamentos de Rede**

    ---

    Roteadores, switches e acessórios de conectividade

</div>

## 📈 Relatórios e Métricas

### Dados Disponíveis

- 📊 **Equipamentos por setor**
- 📈 **Tempo médio de aprovação**
- 🔄 **Taxa de devolução**
- 💻 **Tipos mais solicitados**
- 📅 **Sazonalidade** de solicitações

### Exportação

- 📄 **Excel**: Para análise detalhada
- 📋 **PDF**: Para relatórios gerenciais
- 🔍 **Filtros aplicados**: Exporte dados filtrados

## 💡 Boas Práticas

### Ao Solicitar

1. **📝 Seja específico** sobre necessidades técnicas
2. **⏰ Defina prazos realistas** para entrega
3. **🔗 Justifique adequadamente** a solicitação
4. **📞 Mantenha contato** para acompanhamento

### Durante Uso

1. **💻 Cuide do equipamento** adequadamente
2. **🔒 Mantenha segurança** (antivírus, backups)
3. **📞 Reporte problemas** imediatamente
4. **📋 Mantenha documentação** atualizada

### Na Devolução

1. **💾 Faça backup** de dados pessoais
2. **🧹 Limpe dados** corporativos
3. **🔧 Restaure configurações** originais
4. **📦 Embale adequadamente** para transporte

## 🚨 Solução de Problemas

### Problemas Comuns

**❓ Solicitação não aparece**
- ✅ Verifique se foi enviada corretamente
- ✅ Aguarde processamento (até 5 minutos)
- ✅ Entre em contato com TI se não aparecer

**❓ Status não atualiza**
- ✅ Aguarde processamento da equipe de TI
- ✅ Verifique se há comentários na solicitação
- ✅ Entre em contato se demora muito

**❓ Não consigo editar**
- ✅ Apenas solicitações "Solicitadas" podem ser editadas
- ✅ Entre em contato com TI para alterações
- ✅ Abra novo chamado se necessário

**❓ Perdi equipamento**
- ✅ Abra chamado imediatamente explicando situação
- ✅ Forneça detalhes sobre quando foi perdido
- ✅ Siga procedimentos de segurança da empresa

## 📚 Recursos Adicionais

- **🎫 Sistema de Chamados**: Para problemas com equipamentos
- **📚 Tutoriais**: Guias sobre uso de equipamentos
- **❓ FAQ**: Perguntas sobre processos de solicitação
- **📖 Políticas Corporativas**: Regulamentos sobre uso de equipamentos

---

<div class="info">
    **Dica**: Mantenha seus equipamentos sempre atualizados e seguros. Em caso de dúvidas sobre uso ou manutenção, consulte os tutoriais disponíveis ou abra um chamado para suporte técnico.
</div>