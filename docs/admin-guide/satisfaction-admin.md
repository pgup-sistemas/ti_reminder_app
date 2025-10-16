# Administração do Sistema de Satisfação

Guia completo para administradores configurarem e gerenciarem o sistema de avaliação de satisfação dos serviços de TI.

## Configuração do Sistema

### 1. Configurações Gerais

#### Parâmetros de Envio
```python
# Configurações no arquivo config.py
SATISFACTION_SURVEY_DELAY = 24  # Horas após fechamento
SATISFACTION_SURVEY_REMINDER = 72  # Horas para lembrete
SATISFACTION_SURVEY_EXPIRY = 720  # Horas para expirar (30 dias)
```

#### Templates de Email
- **Pesquisa Inicial**: Envio automático
- **Lembrete**: Reenvio para não respondentes
- **Agradecimento**: Confirmação de avaliação

### 2. Gestão de Pesquisas

#### Envio Manual
```python
# API para envio manual
POST /satisfaction/send-survey/{chamado_id}
```

#### Controle de Status
- **Pendente**: Aguardando envio
- **Enviada**: Pesquisa enviada por email
- **Respondida**: Avaliação recebida
- **Expirada**: Prazo esgotado

## Dashboard Administrativo

### Métricas Principais

#### KPIs de Satisfação
- **NPS (Net Promoter Score)**: Calculado automaticamente
- **CSAT (Customer Satisfaction)**: Média das avaliações
- **Taxa de Resposta**: Percentual de avaliações recebidas

#### Distribuição por Estrelas
- **5 estrelas**: Promotores (9-10)
- **4 estrelas**: Neutros (7-8)
- **1-3 estrelas**: Detratores (0-6)

### Análises Avançadas

#### Por Responsável TI
```sql
SELECT
    responsavel_ti_id,
    AVG(satisfaction_rating) as avg_rating,
    COUNT(*) as total_chamados,
    COUNT(satisfaction_rating) as avaliados
FROM chamado
WHERE data_fechamento >= '2024-01-01'
GROUP BY responsavel_ti_id
ORDER BY avg_rating DESC
```

#### Por Tipo de Chamado
- **Incidentes**: Satisfação em resolução
- **Requisições**: Satisfação em atendimento
- **Problemas**: Satisfação em soluções

#### Tendências Temporais
- **Diária**: Variações por dia da semana
- **Semanal**: Padrões semanais
- **Mensal**: Evolução mensal

## Gestão de Feedback

### Análise de Comentários

#### Categorização Automática
- **Positivo**: Elogios e satisfação
- **Negativo**: Reclamações e insatisfação
- **Sugestão**: Ideias de melhoria
- **Neutro**: Comentários informativos

#### Palavras-Chave
- **Temas Comuns**: Velocidade, qualidade, comunicação
- **Alertas**: Palavras que indicam problemas graves
- **Ações**: Sugestões específicas de melhoria

### Respostas Automatizadas

#### Templates por Avaliação
- **5 estrelas**: Agradecimento especial
- **1-2 estrelas**: Pedido de desculpas + contato
- **3-4 estrelas**: Agradecimento + compromisso de melhoria

## Relatórios Executivos

### Relatório de Satisfação

#### Estrutura do Relatório
1. **Sumário Executivo**: Principais métricas
2. **Análise de Tendências**: Evolução temporal
3. **Pontos Fortes**: O que está funcionando bem
4. **Áreas de Melhoria**: Onde focar esforços
5. **Recomendações**: Ações específicas

#### Distribuição Automática
- **Semanal**: Relatório para gestores
- **Mensal**: Relatório executivo completo
- **Trimestral**: Análise estratégica

## Ações Corretivas

### Processo de Melhoria

#### 1. Identificação
- **Análise de Feedback**: Padrões em reclamações
- **Benchmarking**: Comparação com metas
- **Root Cause**: Análise de causas raiz

#### 2. Planejamento
- **Ações Específicas**: Soluções para problemas
- **Responsáveis**: Atribuição de tarefas
- **Prazos**: Cronograma de implementação

#### 3. Implementação
- **Execução**: Aplicação das melhorias
- **Comunicação**: Transparência com usuários
- **Treinamento**: Capacitação da equipe

#### 4. Monitoramento
- **Acompanhamento**: Verificação de eficácia
- **Ajustes**: Correções conforme necessário
- **Relatórios**: Comunicação de resultados

## Configurações Avançadas

### Personalização de Pesquisas

#### Campos Customizados
```json
{
    "custom_fields": [
        {
            "name": "velocidade_atendimento",
            "type": "rating",
            "label": "Velocidade do Atendimento",
            "required": true
        }
    ]
}
```

#### Lógica Condicional
- **Perguntas Seguinte**: Baseadas na resposta anterior
- **Encaminhamento**: Roteamento baseado em feedback

### Integrações

#### CRM/ERP
- **Sincronização**: Dados de clientes
- **Segmentação**: Pesquisas personalizadas
- **Relatórios**: Integração com sistemas externos

#### Ferramentas de Analytics
- **Google Analytics**: Comportamento dos respondentes
- **Power BI**: Dashboards avançados
- **Tableau**: Visualizações interativas

## Monitoramento e Alertas

### Alertas Automáticos

#### Thresholds Configuráveis
```python
ALERT_THRESHOLDS = {
    'satisfaction_drop': 0.1,  # 10% de queda
    'response_rate_low': 0.7,  # 70% de taxa de resposta
    'negative_feedback_spike': 2.0  # Dobro do normal
}
```

#### Canais de Notificação
- **Email**: Alertas para gestores
- **Slack/Teams**: Notificações em tempo real
- **SMS**: Alertas críticos

## Segurança e Privacidade

### Proteção de Dados

#### Anonimização
- **Dados Pessoais**: Remoção automática
- **Auditoria**: Log completo de acessos
- **Retenção**: Política de retenção de dados

#### Compliance
- **LGPD**: Conformidade com leis de privacidade
- **ISO 27001**: Segurança da informação
- **Auditorias**: Verificações regulares

## Suporte e Troubleshooting

### Problemas Comuns

#### Pesquisas Não Enviadas
- **Verificar**: Configuração de email
- **Logs**: Verificar logs do sistema
- **Fila**: Status da fila de emails

#### Avaliações Não Registradas
- **Validação**: Verificar campos obrigatórios
- **Banco**: Status da conexão
- **Cache**: Limpeza de cache

### Suporte Técnico
- **Documentação**: docs/satisfaction-admin.md
- **Equipe de TI**: chamados@empresa.com
- **Fornecedor**: suporte@satisfaction-provider.com