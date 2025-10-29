# Administração do Sistema RFID

Este guia fornece instruções completas para administradores configurarem e gerenciarem o sistema RFID de rastreamento de equipamentos.

## Configuração Inicial

### 1. Instalação de Leitores RFID

#### Requisitos de Hardware
- **Leitores RFID**: Modelo compatível com protocolo EPC Gen2
- **Antenas**: Alcance mínimo de 3 metros
- **Fonte de Alimentação**: Estável e com backup
- **Conectividade**: Rede Ethernet ou Wi-Fi

#### Posicionamento Estratégico
- **Entradas/Saídas**: Principais pontos de acesso
- **Áreas Críticas**: Servidores, equipamentos valiosos
- **Corredores**: Pontos de passagem obrigatório
- **Estacionamentos**: Controle de veículos

### 2. Configuração de Software

#### Cadastro de Leitores
```python
# Exemplo de configuração via API
POST /rfid/reader/register
{
    "reader_id": "READER_001",
    "location": "Entrada Principal",
    "ip_address": "192.168.1.100",
    "port": 5084,
    "antennas": 4
}
```

#### Definição de Zonas
- **Zona Segura**: Área permitida para o equipamento
- **Zona Restrita**: Área proibida
- **Zona Quarentena**: Equipamentos suspeitos

## Gerenciamento de Equipamentos

### Cadastro de Equipamentos

#### Dados Obrigatórios
- **Descrição**: Identificação clara do equipamento
- **Patrimônio**: Número único da organização
- **Tipo**: Notebook, monitor, servidor, etc.
- **Valor**: Para controle de seguros

#### Vinculação de Tags
1. **Aquisição**: Compra de tags RFID compatíveis
2. **Programação**: Gravação do ID único
3. **Teste**: Verificação de leitura
4. **Instalação**: Fixação no equipamento

### Monitoramento em Tempo Real

#### Dashboard RFID
- **Status dos Leitores**: Online/offline
- **Equipamentos Ativos**: Localização atual
- **Alertas**: Movimentações suspeitas
- **Histórico**: Trajetória completa

#### APIs Disponíveis
```javascript
// Status em tempo real
GET /api/rfid/status

// Localização específica
GET /rfid/location/{equipment_id}

// Histórico de movimentação
GET /rfid/history/{equipment_id}?period=30d
```

## Alertas e Notificações

### Tipos de Alerta

#### Alerta de Perda
- **Gatilho**: Equipamento fora da zona permitida
- **Notificação**: Email + push para responsáveis
- **Ação**: Bloqueio automático de saída

#### Alerta de Movimento Suspeito
- **Gatilho**: Padrões anômalos de movimentação
- **Análise**: Machine learning para detecção
- **Escalação**: Alerta para segurança

### Configuração de Regras

#### Regras de Zona
```json
{
    "equipment_type": "notebook",
    "allowed_zones": ["escritorio", "reuniao"],
    "restricted_zones": ["exterior"],
    "alert_delay": 300
}
```

#### Regras de Horário
- **Horário Comercial**: Movimentação normal
- **Fora do Expediente**: Alerta automático
- **Feriados**: Controle especial

## Relatórios e Analytics

### Relatórios Disponíveis

#### Relatório de Movimentação
- **Período**: Diário, semanal, mensal
- **Métricas**: Distância percorrida, tempo de uso
- **Análise**: Padrões de utilização

#### Relatório de Alertas
- **Frequência**: Número de alertas por período
- **Tipos**: Classificação por gravidade
- **Resolução**: Tempo médio de resposta

### Dashboards Executivos

#### KPIs Principais
- **Taxa de Perdas**: Equipamentos perdidos/total
- **Tempo de Localização**: Média para encontrar equipamentos
- **Alertas Falsos**: Percentual de alertas incorretos

## Manutenção e Suporte

### Manutenção Preventiva

#### Leitores RFID
- **Limpeza**: Antenas livres de poeira
- **Calibração**: Ajuste de sensibilidade
- **Atualização**: Firmware atualizado

#### Tags RFID
- **Inspeção Visual**: Danos físicos
- **Teste de Leitura**: Funcionamento correto
- **Substituição**: Tags danificadas

### Troubleshooting

#### Problemas Comuns

##### Leitor Offline
- **Sintomas**: Equipamentos não detectados
- **Causas**: Problema de rede, energia
- **Solução**: Verificar conectividade e energia

##### Falsos Positivos
- **Sintomas**: Alertas incorretos
- **Causas**: Interferência, configuração inadequada
- **Solução**: Recalibrar sensibilidade

##### Tags Não Lidas
- **Sintomas**: Equipamentos invisíveis
- **Causas**: Tag danificada, orientação incorreta
- **Solução**: Verificar instalação da tag

## Segurança e Compliance

### Controle de Acesso
- **Autenticação**: Apenas administradores autorizados
- **Auditoria**: Log completo de todas as ações
- **Criptografia**: Dados sensíveis protegidos

### Compliance
- **LGPD**: Proteção de dados pessoais
- **ISO 27001**: Segurança da informação
- **Auditorias**: Relatórios para compliance

## Suporte e Contato

Para suporte técnico do sistema RFID, entre em contato com:
- **📧 E-mail**: pageupsistemas@gmail.com
- **<i class="fab fa-github"></i> GitHub**: [ti_reminder_app](https://github.com/pgup-sistemas/ti_reminder_app.git)
- **🎫 Sistema de chamados**: Abra um ticket interno
- **📚 Documentação**: docs/rfid-admin.md