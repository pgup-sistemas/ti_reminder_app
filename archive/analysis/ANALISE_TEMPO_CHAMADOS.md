# 📊 Análise: Tempo de Duração dos Chamados

## 🔍 Situação Atual

### ✅ O que JÁ existe

| Campo/Funcionalidade | Status | Localização |
|---------------------|--------|-------------|
| `data_abertura` | ✅ Existe | `models.py` - Quando chamado foi criado |
| `data_fechamento` | ✅ Existe | `models.py` - Quando chamado foi fechado |
| `data_ultima_atualizacao` | ✅ Existe | `models.py` - Última modificação |
| `tempo_resposta_horas` | ✅ Existe | `models.py` - Tempo até primeira resposta |
| `tempo_restante_sla` | ✅ Existe | `models.py` - Property calculada |
| **Display na lista** | ❌ **NÃO EXISTE** | `listar_chamados.html` - **FALTA** |

### ❌ O que FALTA

**Na lista de chamados (`/chamados`) NÃO mostra:**

1. **Tempo decorrido** desde a abertura (para chamados abertos)
2. **Duração total** até o fechamento (para chamados fechados)
3. **Indicador visual** de "há quanto tempo está aberto"
4. **Métrica de performance** (rápido, normal, lento)

---

## 📋 Informações Exibidas Atualmente

### Template: `listar_chamados.html`

**Colunas da tabela desktop:**
| Coluna | Dado Exibido |
|--------|-------------|
| ID | Número do chamado |
| Título | Nome do chamado |
| Status | Badge (Aberto, Em Andamento, Resolvido, Fechado) |
| Prioridade | Badge (Baixa, Média, Alta, Crítica) |
| **SLA** | Status + Prazo SLA ✅ |
| Solicitante | Nome do usuário |
| Setor | Nome do setor |
| **Abertura** | Data/hora de criação ✅ |
| Ações | Botões (Ver, Editar) |

### 🎯 O que está faltando: **DURAÇÃO/TEMPO DECORRIDO**

---

## 💡 Proposta de Melhoria Visual

### 1. **Nova Coluna: "Duração"** 

**Localização:** Entre "Abertura" e "Ações"

**Conteúdo:**
- **Chamados Abertos/Em Andamento:** 
  - Tempo decorrido desde abertura
  - Ex: "2h 30m" | "3 dias" | "1 semana"
  - Cor dinâmica baseada no tempo

- **Chamados Fechados:**
  - Duração total até fechamento
  - Ex: "Resolvido em 4h 20m" | "Fechado em 2 dias"

### 2. **Indicadores Visuais**

#### Para Chamados Abertos:

```
🟢 Verde:  < 24h aberto
🟡 Amarelo: 24h - 72h aberto
🟠 Laranja: 3-7 dias aberto
🔴 Vermelho: > 7 dias aberto
```

#### Para Chamados Fechados:

```
⚡ Rápido:  < 4h para resolver
✅ Normal:   4h - 24h para resolver
📊 Lento:    > 24h para resolver
```

### 3. **Formato de Exibição**

#### Chamados Abertos (exemplo):
```
┌─────────────────────────────────────┐
│ Aberto há                           │
│ ⏰ 2h 30m                    🟢     │
└─────────────────────────────────────┘
```

#### Chamados Fechados (exemplo):
```
┌─────────────────────────────────────┐
│ Resolvido em                        │
│ ✅ 4h 20m                    ⚡     │
└─────────────────────────────────────┘
```

---

## 🔧 Implementação Técnica

### 1. **Adicionar Properties no Modelo** (`models.py`)

```python
@property
def tempo_aberto(self):
    """
    Retorna o tempo que o chamado está/esteve aberto.
    Para chamados abertos: tempo desde abertura até agora
    Para chamados fechados: tempo desde abertura até fechamento
    """
    if self.data_fechamento:
        # Chamado fechado: calcular duração total
        diferenca = self.data_fechamento - self.data_abertura
    else:
        # Chamado aberto: calcular tempo desde abertura
        agora = get_current_time_for_db()
        diferenca = agora - self.data_abertura
    
    return diferenca

@property
def tempo_aberto_formatado(self):
    """Retorna tempo aberto em formato legível"""
    delta = self.tempo_aberto
    
    dias = delta.days
    horas = delta.seconds // 3600
    minutos = (delta.seconds % 3600) // 60
    
    if dias > 0:
        if dias == 1:
            return f"{dias} dia"
        elif dias < 7:
            return f"{dias} dias"
        elif dias < 30:
            semanas = dias // 7
            return f"{semanas} semana{'s' if semanas > 1 else ''}"
        else:
            meses = dias // 30
            return f"{meses} m{'eses' if meses > 1 else 'ês'}"
    elif horas > 0:
        return f"{horas}h {minutos}m"
    else:
        return f"{minutos}m"

@property
def indicador_tempo(self):
    """
    Retorna indicador visual baseado no tempo aberto.
    Para chamados abertos: cor baseada em urgência
    Para chamados fechados: performance (rápido/normal/lento)
    """
    delta = self.tempo_aberto
    horas_totais = delta.total_seconds() / 3600
    
    if self.status == 'Fechado':
        # Indicadores para chamados fechados (performance)
        if horas_totais < 4:
            return {'classe': 'success', 'icone': 'bolt', 'texto': 'Rápido'}
        elif horas_totais < 24:
            return {'classe': 'info', 'icone': 'check', 'texto': 'Normal'}
        else:
            return {'classe': 'secondary', 'icone': 'chart-line', 'texto': 'Lento'}
    else:
        # Indicadores para chamados abertos (urgência por tempo)
        if horas_totais < 24:
            return {'classe': 'success', 'icone': 'clock', 'texto': 'Recente'}
        elif horas_totais < 72:
            return {'classe': 'warning', 'icone': 'clock', 'texto': 'Atenção'}
        elif horas_totais < 168:  # 7 dias
            return {'classe': 'orange', 'icone': 'exclamation-triangle', 'texto': 'Antigo'}
        else:
            return {'classe': 'danger', 'icone': 'exclamation-circle', 'texto': 'Crítico'}
```

### 2. **Modificar Template** (`listar_chamados.html`)

#### Desktop View - Adicionar nova coluna:

```html
<!-- ANTES: Linha 171-172 -->
<th><i class="fas fa-calendar-alt me-2 text-muted"></i>Abertura</th>
<th class="text-center pe-3"><i class="fas fa-cogs me-2 text-muted"></i>Ações</th>

<!-- DEPOIS: Adicionar coluna Duração -->
<th><i class="fas fa-calendar-alt me-2 text-muted"></i>Abertura</th>
<th class="text-center"><i class="fas fa-hourglass-half me-2 text-muted"></i>Duração</th>
<th class="text-center pe-3"><i class="fas fa-cogs me-2 text-muted"></i>Ações</th>
```

#### Linha de dados - Adicionar célula:

```html
<!-- ANTES: Linha 237-239 -->
<td>
    <small class="text-muted">{{ chamado.data_abertura|local_datetime }}</small>
</td>
<td class="text-center pe-3">

<!-- DEPOIS: -->
<td>
    <small class="text-muted">{{ chamado.data_abertura|local_datetime }}</small>
</td>
<td class="text-center">
    {% set indicador = chamado.indicador_tempo %}
    <div class="d-flex flex-column align-items-center">
        <span class="badge bg-{{ indicador.classe }} bg-opacity-10 text-{{ indicador.classe }} border border-{{ indicador.classe }} border-opacity-25 d-inline-flex align-items-center gap-1 mb-1">
            <i class="fas fa-{{ indicador.icone }}"></i>
            {{ chamado.tempo_aberto_formatado }}
        </span>
        <small class="text-muted" style="font-size: 0.7rem;">
            {% if chamado.status == 'Fechado' %}
                {{ indicador.texto }}
            {% else %}
                Aberto há
            {% endif %}
        </small>
    </div>
</td>
<td class="text-center pe-3">
```

#### Mobile View - Adicionar informação:

```html
<!-- DEPOIS da linha 328 (após SLA) -->
<div class="col-6">
    <small class="text-muted d-block">Duração</small>
    {% set indicador = chamado.indicador_tempo %}
    <span class="badge bg-{{ indicador.classe }}">
        <i class="fas fa-{{ indicador.icone }}"></i> 
        {{ chamado.tempo_aberto_formatado }}
    </span>
    <br>
    <small class="text-muted" style="font-size: 0.7rem;">{{ indicador.texto }}</small>
</div>
```

---

## 🎨 Mockup Visual

### Desktop - Tabela Expandida:

```
┌──────┬──────────────┬──────────┬────────────┬─────────┬─────────────┬────────┬──────────────┬────────────┬────────┐
│  ID  │   Título     │  Status  │ Prioridade │   SLA   │ Solicitante │ Setor  │   Abertura   │  Duração   │ Ações  │
├──────┼──────────────┼──────────┼────────────┼─────────┼─────────────┼────────┼──────────────┼────────────┼────────┤
│ #123 │ Impressora   │ 🟢 Aberto│ 🔴 Crítica │ ⏰ 2h   │ João Silva  │ TI     │ 29/10 10:00  │ ⏰ 2h 30m  │ 👁️ ✏️ │
│      │ quebrada     │          │            │ restam  │             │        │              │ 🟢 Recente │        │
├──────┼──────────────┼──────────┼────────────┼─────────┼─────────────┼────────┼──────────────┼────────────┼────────┤
│ #122 │ Email não    │ 🟡 Em    │ 🟡 Média   │ ✅ OK   │ Maria Costa │ Admin  │ 28/10 14:20  │ 📅 1 dia   │ 👁️    │
│      │ funciona     │ Andamento│            │         │             │        │              │ 🟡 Atenção │        │
├──────┼──────────────┼──────────┼────────────┼─────────┼─────────────┼────────┼──────────────┼────────────┼────────┤
│ #121 │ Problema     │ ⚫ Fechado│ 🔵 Baixa   │ ✅ Cump │ Pedro Lima  │ Vendas │ 25/10 09:00  │ ✅ 4h 20m  │ 👁️    │
│      │ rede         │          │            │         │             │        │              │ ⚡ Rápido  │        │
└──────┴──────────────┴──────────┴────────────┴─────────┴─────────────┴────────┴──────────────┴────────────┴────────┘
```

### Mobile - Card Expandido:

```
┌────────────────────────────────────────────┐
│ 🎫 #123 - Impressora quebrada             │
│                            🟢 Aberto       │
│                            🔴 Crítica      │
├────────────────────────────────────────────┤
│ Solicitante: João Silva                    │
│ Setor: TI                                  │
├────────────────────────────────────────────┤
│ Abertura: 29/10/25 10:00                   │
│ SLA: ⏰ 2h restam                          │
├────────────────────────────────────────────┤
│ Duração:                                   │
│ ⏰ 2h 30m 🟢                                │
│ (Recente)                                  │
├────────────────────────────────────────────┤
│ [👁️ Visualizar] [✏️ Editar]               │
└────────────────────────────────────────────┘
```

---

## 📊 Benefícios da Melhoria

### Para Usuários:
✅ Visualização instantânea do tempo de espera  
✅ Entendimento rápido se chamado está "parado"  
✅ Priorização visual de quais chamados precisam atenção  

### Para Administradores/TI:
✅ Identificação rápida de chamados antigos  
✅ Métricas de performance visíveis  
✅ Dashboard visual de eficiência  

### Para Gestão:
✅ KPI visual de tempo de resolução  
✅ Identificação de gargalos  
✅ Análise de performance da equipe  

---

## 🎯 Indicadores de Performance

### Classificação por Tempo (Chamados Fechados):

| Classificação | Tempo de Resolução | Badge | Cor |
|---------------|-------------------|-------|-----|
| ⚡ **Rápido** | < 4 horas | `success` | Verde |
| ✅ **Normal** | 4h - 24h | `info` | Azul |
| 📊 **Lento** | > 24 horas | `secondary` | Cinza |

### Alertas por Tempo (Chamados Abertos):

| Status | Tempo Aberto | Badge | Cor | Ação Sugerida |
|--------|-------------|-------|-----|---------------|
| 🟢 **Recente** | < 24h | `success` | Verde | Monitorar |
| 🟡 **Atenção** | 24h - 72h | `warning` | Amarelo | Priorizar |
| 🟠 **Antigo** | 3-7 dias | `orange` | Laranja | Urgente |
| 🔴 **Crítico** | > 7 dias | `danger` | Vermelho | Ação Imediata |

---

## 📈 Métricas Adicionais (Futuro)

Com esta implementação, futuramente podemos adicionar:

1. **Dashboard de Performance:**
   - Tempo médio de resolução por setor
   - Tempo médio de resolução por prioridade
   - Gráfico de evolução temporal

2. **Relatórios:**
   - Chamados mais antigos (> 7 dias)
   - Chamados resolvidos rapidamente (< 4h)
   - Comparativo mensal de performance

3. **Alertas Automáticos:**
   - Email quando chamado passa de 72h aberto
   - Notificação quando SLA próximo de vencer
   - Alerta de chamado "abandonado" (> 7 dias)

---

## 🚀 Implementação Recomendada

### Fase 1: Backend (models.py)
- ✅ Adicionar properties `tempo_aberto`
- ✅ Adicionar property `tempo_aberto_formatado`
- ✅ Adicionar property `indicador_tempo`

### Fase 2: Frontend (listar_chamados.html)
- ✅ Adicionar coluna "Duração" na tabela desktop
- ✅ Adicionar informação de duração nos cards mobile
- ✅ Aplicar badges coloridos baseados em indicadores

### Fase 3: Testes
- ✅ Testar com chamados recentes (< 24h)
- ✅ Testar com chamados antigos (> 7 dias)
- ✅ Testar com chamados fechados
- ✅ Validar formatação de tempo

### Fase 4: Refinamentos (Opcional)
- 🔄 Adicionar tooltip com data exata
- 🔄 Ordenação por duração
- 🔄 Filtro por tempo de duração
- 🔄 Gráfico de distribuição de tempos

---

## 📝 Estimativa de Desenvolvimento

| Tarefa | Tempo Estimado | Complexidade |
|--------|---------------|--------------|
| Adicionar properties no modelo | 15 min | Baixa |
| Modificar template desktop | 20 min | Baixa |
| Modificar template mobile | 15 min | Baixa |
| Testes e ajustes | 20 min | Baixa |
| **TOTAL** | **~70 min** | **Baixa** |

---

## ✅ Conclusão

**Status Atual:** ❌ Sistema NÃO mostra tempo de duração dos chamados na lista  
**Proposta:** ✅ Adicionar coluna "Duração" com indicadores visuais inteligentes  
**Benefício:** 📈 Melhora significativa na UX e visibilidade de métricas  
**Complexidade:** 🟢 Baixa - Implementação simples e direta  
**Impacto:** 🔥 ALTO - Informação crítica para gestão de chamados  

**Recomendação:** **IMPLEMENTAR** esta melhoria visual!
