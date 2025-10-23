# ⚡ PLANO DE AÇÃO IMEDIATO - TI OSN SYSTEM

## 🎯 OBJETIVO
Aumentar o valor comercial do sistema de **R$ 20.000 para R$ 50.000+** em 12 semanas

---

## 📊 RESUMO DA ANÁLISE

### Status Atual: **82/100 pontos**

#### ✅ O QUE ESTÁ BOM
- Arquitetura sólida e bem estruturada
- 8+ módulos funcionais (Lembretes, Chamados, Tutoriais, Equipamentos)
- Segurança implementada (CSRF, Rate Limiting, Talisman)
- PWA funcional com Service Worker
- Documentação completa
- Testes automatizados (22 testes passando)
- Pronto para produção em pequenas empresas

#### ⚠️ O QUE PRECISA MELHORAR (Oportunidades de Alto Valor)
1. **Analytics e Relatórios** - Básicos → Profissionais (+35% valor)
2. **Gestão de Ativos (ITAM)** - Inexistente → Completo (+50% valor)
3. **Integrações** - Nenhuma → Active Directory, M365 (+45% valor)
4. **UI/UX** - Funcional → Moderna (+20% valor)
5. **API REST** - Interna → Pública documentada (+20% valor)

### Potencial de Crescimento: **+170% em valor**

---

## 🚀 ESTRATÉGIA RECOMENDADA: "VITÓRIAS RÁPIDAS"

### FASE 1: MÊS 1 (Semanas 1-4)
**Foco:** Demonstrar valor imediatamente

```
SEMANA 1-2: Dashboard Analytics Profissional
├─ Setup Chart.js ou ApexCharts
├─ 8 gráficos interativos principais
├─ KPIs em cards destacados
└─ Filtros e drill-down

RESULTADO: +35% em valor percebido
INVESTIMENTO: R$ 12.000
```

```
SEMANA 3-4: ITAM Básico (Gestão de Ativos)
├─ Inventário de equipamentos
├─ Controle de licenças
├─ QR Codes para rastreamento
└─ Alertas de vencimento

RESULTADO: +50% em valor percebido (ROI mensurável!)
INVESTIMENTO: R$ 12.000
```

**TOTAL MÊS 1:**
- Investimento: R$ 24.000
- Valor agregado: +85%
- Novo valor: R$ 37.000+
- **ROI em 3-4 meses**

---

## 📋 CHECKLIST DE IMPLEMENTAÇÃO - SEMANA 1

### DIA 1: Setup e Planejamento 🔧

#### Manhã (4h)
- [ ] **Criar branch de desenvolvimento**
  ```bash
  git checkout -b feature/analytics-dashboard
  ```

- [ ] **Instalar dependências**
  ```bash
  # Backend
  pip install pandas numpy

  # Frontend - Adicionar ao base.html
  <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.0"></script>
  # OU
  <script src="https://cdn.jsdelivr.net/npm/apexcharts"></script>
  ```

- [ ] **Criar estrutura de diretórios**
  ```bash
  mkdir -p app/services/analytics
  mkdir -p app/static/js/analytics
  mkdir -p app/templates/analytics
  ```

#### Tarde (4h)
- [ ] **Definir métricas principais** (documentar)
  - Total de chamados por período
  - Taxa de resolução de SLA
  - Tempo médio de resposta
  - Satisfação do usuário
  - Chamados por categoria
  - Performance por técnico
  - Custos com licenças
  - Equipamentos em uso

- [ ] **Criar modelos de dados** (se necessário)
  ```python
  # app/models.py - Adicionar se não existir
  class Metric(db.Model):
      id = db.Column(db.Integer, primary_key=True)
      metric_type = db.Column(db.String(50))
      metric_value = db.Column(db.Float)
      date = db.Column(db.Date)
      metadata = db.Column(db.JSON)
  ```

---

### DIA 2-3: Backend Analytics 🔙

#### Criar Service Layer
```python
# app/services/analytics/analytics_service.py
from datetime import datetime, timedelta
from app.models import Chamado, User, Reminder, EquipmentLoan
from sqlalchemy import func

class AnalyticsService:
    
    @staticmethod
    def get_chamados_por_periodo(start_date, end_date, group_by='day'):
        """Retorna chamados agrupados por período"""
        query = db.session.query(
            func.date_trunc(group_by, Chamado.data_abertura).label('periodo'),
            func.count(Chamado.id).label('total')
        ).filter(
            Chamado.data_abertura.between(start_date, end_date)
        ).group_by('periodo').order_by('periodo')
        
        return [{'periodo': r.periodo, 'total': r.total} for r in query.all()]
    
    @staticmethod
    def get_sla_compliance(start_date, end_date):
        """Retorna taxa de cumprimento de SLA"""
        total = Chamado.query.filter(
            Chamado.data_abertura.between(start_date, end_date)
        ).count()
        
        cumpridos = Chamado.query.filter(
            Chamado.data_abertura.between(start_date, end_date),
            Chamado.sla_cumprido == True
        ).count()
        
        return {
            'total': total,
            'cumpridos': cumpridos,
            'taxa': (cumpridos / total * 100) if total > 0 else 0
        }
    
    @staticmethod
    def get_performance_por_tecnico(start_date, end_date):
        """Performance de cada técnico"""
        query = db.session.query(
            User.username,
            func.count(Chamado.id).label('total_chamados'),
            func.avg(Chamado.tempo_resposta_horas).label('tempo_medio'),
            func.sum(
                func.cast(Chamado.sla_cumprido == True, db.Integer)
            ).label('sla_cumprido')
        ).join(
            Chamado, Chamado.responsavel_ti_id == User.id
        ).filter(
            Chamado.data_abertura.between(start_date, end_date)
        ).group_by(User.id).all()
        
        return [
            {
                'tecnico': r.username,
                'total': r.total_chamados,
                'tempo_medio': round(r.tempo_medio, 2),
                'sla_taxa': (r.sla_cumprido / r.total_chamados * 100)
            }
            for r in query
        ]
    
    @staticmethod
    def get_dashboard_kpis():
        """KPIs principais para dashboard"""
        hoje = datetime.now().date()
        mes_atual = hoje.replace(day=1)
        mes_anterior = (mes_atual - timedelta(days=1)).replace(day=1)
        
        # Chamados abertos
        chamados_abertos = Chamado.query.filter(
            Chamado.status.in_(['Aberto', 'Em Andamento'])
        ).count()
        
        # Chamados do mês
        chamados_mes = Chamado.query.filter(
            Chamado.data_abertura >= mes_atual
        ).count()
        
        # Chamados mês anterior
        chamados_mes_ant = Chamado.query.filter(
            Chamado.data_abertura >= mes_anterior,
            Chamado.data_abertura < mes_atual
        ).count()
        
        # Variação percentual
        variacao = 0
        if chamados_mes_ant > 0:
            variacao = ((chamados_mes - chamados_mes_ant) / chamados_mes_ant) * 100
        
        # SLA do mês
        sla_data = AnalyticsService.get_sla_compliance(mes_atual, hoje)
        
        # Satisfação média
        satisfacao = db.session.query(
            func.avg(Chamado.satisfaction_rating)
        ).filter(
            Chamado.satisfaction_date >= mes_atual
        ).scalar() or 0
        
        return {
            'chamados_abertos': chamados_abertos,
            'chamados_mes': chamados_mes,
            'variacao_percentual': round(variacao, 1),
            'sla_taxa': round(sla_data['taxa'], 1),
            'satisfacao_media': round(satisfacao, 1)
        }
```

#### Criar Endpoints API
```python
# app/routes.py - Adicionar rotas
@bp.route('/api/analytics/dashboard-kpis')
@login_required
def api_dashboard_kpis():
    """KPIs principais"""
    if not current_user.is_admin and not current_user.is_ti:
        return jsonify({'error': 'Sem permissão'}), 403
    
    kpis = AnalyticsService.get_dashboard_kpis()
    return jsonify(kpis)

@bp.route('/api/analytics/chamados-periodo')
@login_required
def api_chamados_periodo():
    """Chamados por período"""
    start = request.args.get('start', (datetime.now() - timedelta(days=30)).date())
    end = request.args.get('end', datetime.now().date())
    group_by = request.args.get('group_by', 'day')
    
    data = AnalyticsService.get_chamados_por_periodo(start, end, group_by)
    return jsonify(data)

@bp.route('/api/analytics/performance-tecnico')
@login_required
def api_performance_tecnico():
    """Performance por técnico"""
    if not current_user.is_admin and not current_user.is_ti:
        return jsonify({'error': 'Sem permissão'}), 403
    
    start = request.args.get('start', (datetime.now() - timedelta(days=30)).date())
    end = request.args.get('end', datetime.now().date())
    
    data = AnalyticsService.get_performance_por_tecnico(start, end)
    return jsonify(data)
```

---

### DIA 4-5: Frontend Analytics 🎨

#### Criar Página de Analytics
```html
<!-- app/templates/analytics_dashboard.html -->
{% extends "base.html" %}

{% block content %}
<div class="container-fluid py-4">
    <!-- KPI Cards -->
    <div class="row g-3 mb-4">
        <div class="col-md-3">
            <div class="card border-0 shadow-sm">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <p class="text-muted mb-1 small">Chamados Abertos</p>
                            <h3 class="mb-0" id="kpi-chamados-abertos">-</h3>
                        </div>
                        <div class="text-primary">
                            <i class="fas fa-ticket-alt fa-2x"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-3">
            <div class="card border-0 shadow-sm">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <p class="text-muted mb-1 small">Chamados do Mês</p>
                            <h3 class="mb-0" id="kpi-chamados-mes">-</h3>
                            <small id="kpi-variacao" class="text-success">
                                <i class="fas fa-arrow-up"></i> 0%
                            </small>
                        </div>
                        <div class="text-success">
                            <i class="fas fa-chart-line fa-2x"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-3">
            <div class="card border-0 shadow-sm">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <p class="text-muted mb-1 small">Taxa de SLA</p>
                            <h3 class="mb-0" id="kpi-sla">-</h3>
                        </div>
                        <div class="text-warning">
                            <i class="fas fa-clock fa-2x"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="col-md-3">
            <div class="card border-0 shadow-sm">
                <div class="card-body">
                    <div class="d-flex justify-content-between align-items-center">
                        <div>
                            <p class="text-muted mb-1 small">Satisfação</p>
                            <h3 class="mb-0" id="kpi-satisfacao">-</h3>
                        </div>
                        <div class="text-info">
                            <i class="fas fa-smile fa-2x"></i>
                        </div>
                    </div>
                </div>
            </div>
        </div>
    </div>
    
    <!-- Gráficos -->
    <div class="row g-3">
        <div class="col-md-8">
            <div class="card border-0 shadow-sm">
                <div class="card-header bg-white">
                    <h5 class="mb-0">Evolução de Chamados</h5>
                </div>
                <div class="card-body">
                    <canvas id="chart-chamados-periodo" height="80"></canvas>
                </div>
            </div>
        </div>
        
        <div class="col-md-4">
            <div class="card border-0 shadow-sm">
                <div class="card-header bg-white">
                    <h5 class="mb-0">Por Prioridade</h5>
                </div>
                <div class="card-body">
                    <canvas id="chart-prioridade"></canvas>
                </div>
            </div>
        </div>
        
        <div class="col-md-12">
            <div class="card border-0 shadow-sm">
                <div class="card-header bg-white">
                    <h5 class="mb-0">Performance por Técnico</h5>
                </div>
                <div class="card-body">
                    <canvas id="chart-performance" height="60"></canvas>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block extra_js %}
<script src="{{ url_for('static', filename='js/analytics-dashboard.js') }}"></script>
{% endblock %}
```

#### JavaScript para Gráficos
```javascript
// app/static/js/analytics-dashboard.js
class AnalyticsDashboard {
    constructor() {
        this.charts = {};
        this.init();
    }
    
    async init() {
        await this.loadKPIs();
        await this.loadChartData();
    }
    
    async loadKPIs() {
        const response = await fetch('/api/analytics/dashboard-kpis');
        const data = await response.json();
        
        document.getElementById('kpi-chamados-abertos').textContent = data.chamados_abertos;
        document.getElementById('kpi-chamados-mes').textContent = data.chamados_mes;
        document.getElementById('kpi-sla').textContent = data.sla_taxa + '%';
        document.getElementById('kpi-satisfacao').textContent = data.satisfacao_media + '/5';
        
        const variacaoEl = document.getElementById('kpi-variacao');
        const variacao = data.variacao_percentual;
        const icon = variacao >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';
        const color = variacao >= 0 ? 'text-success' : 'text-danger';
        
        variacaoEl.className = color;
        variacaoEl.innerHTML = `<i class="fas ${icon}"></i> ${Math.abs(variacao)}%`;
    }
    
    async loadChartData() {
        // Chamados por período
        const chamadosData = await fetch('/api/analytics/chamados-periodo').then(r => r.json());
        this.createLineChart('chart-chamados-periodo', chamadosData);
        
        // Performance por técnico
        const performanceData = await fetch('/api/analytics/performance-tecnico').then(r => r.json());
        this.createBarChart('chart-performance', performanceData);
    }
    
    createLineChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => d.periodo),
                datasets: [{
                    label: 'Chamados',
                    data: data.map(d => d.total),
                    borderColor: '#008BCD',
                    backgroundColor: 'rgba(0, 139, 205, 0.1)',
                    tension: 0.4
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                }
            }
        });
    }
    
    createBarChart(canvasId, data) {
        const ctx = document.getElementById(canvasId);
        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.tecnico),
                datasets: [{
                    label: 'Total Chamados',
                    data: data.map(d => d.total),
                    backgroundColor: '#008BCD'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true
            }
        });
    }
}

// Inicializar quando página carregar
document.addEventListener('DOMContentLoaded', () => {
    new AnalyticsDashboard();
});
```

---

## 🎯 META PARA FINAL DA SEMANA 1

- [ ] ✅ Dashboard analytics funcional
- [ ] ✅ 4 KPI cards atualizando em tempo real
- [ ] ✅ 3 gráficos interativos básicos
- [ ] ✅ Código limpo e documentado
- [ ] ✅ Testes das novas rotas API

---

## 📞 PRÓXIMAS AÇÕES

### Segunda-feira (Dia 1)
1. [ ] Revisar este plano com a equipe
2. [ ] Definir quem será responsável
3. [ ] Criar branch de desenvolvimento
4. [ ] Instalar dependências

### Terça a Sexta (Dias 2-5)
1. [ ] Seguir checklist dia a dia
2. [ ] Commits frequentes
3. [ ] Testes contínuos
4. [ ] Code review diário

### Sexta-feira (Demo)
1. [ ] Apresentar analytics funcionando
2. [ ] Coletar feedback
3. [ ] Planejar semana 2

---

## 💡 DICAS IMPORTANTES

### ✅ FAZER
- Commits pequenos e frequentes
- Testar cada funcionalidade antes de avançar
- Documentar decisões técnicas
- Pedir ajuda quando necessário
- Celebrar pequenas vitórias

### ❌ NÃO FAZER
- Tentar fazer tudo de uma vez
- Pular testes
- Ignorar code review
- Adicionar features não planejadas (scope creep)
- Fazer deploy direto em produção

---

## 📈 TRACKING DE PROGRESSO

Atualizar diariamente:

```
[ ] Dia 1: Setup e planejamento
[ ] Dia 2: Backend analytics (50%)
[ ] Dia 3: Backend analytics (100%)
[ ] Dia 4: Frontend dashboard (50%)
[ ] Dia 5: Frontend dashboard (100%)
[ ] Dia 6-7: Testes e refinamentos
```

---

## 🎯 SUCESSO = 

- Dashboard analytics funcional
- KPIs atualizando em tempo real
- 3-5 gráficos interativos
- Código testado e documentado
- **+35% em valor percebido**

Após completar a Semana 1, o sistema já terá um diferencial competitivo claro!

---

**Questões? Dúvidas? Bloqueios?**

Consulte:
- `ANALISE_COMERCIAL_2025.md` - Análise completa
- `ROADMAP_COMERCIAL_2025.md` - Visão de longo prazo
- `FRONTEND_STANDARDS.md` - Padrões de UI
- `README.md` - Documentação do sistema

**VAMOS COMEÇAR! 🚀**
