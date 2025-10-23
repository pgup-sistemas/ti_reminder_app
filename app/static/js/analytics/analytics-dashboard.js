/**
 * Analytics Dashboard
 * Gerencia gráficos e métricas do dashboard analítico
 */

class AnalyticsDashboard {
    constructor() {
        this.charts = {};
        this.refreshInterval = null;
        this.init();
    }
    
    async init() {
        console.log('Inicializando Analytics Dashboard...');
        await this.loadKPIs();
        await this.loadChartData();
        this.setupRefresh();
    }
    
    /**
     * Carrega KPIs principais
     */
    async loadKPIs() {
        try {
            const response = await fetch('/api/analytics/dashboard-kpis');
            
            if (!response.ok) {
                throw new Error('Erro ao carregar KPIs');
            }
            
            const data = await response.json();
            this.updateKPIs(data);
        } catch (error) {
            console.error('Erro ao carregar KPIs:', error);
            this.showError('Erro ao carregar métricas');
        }
    }
    
    /**
     * Atualiza os cards de KPI
     */
    updateKPIs(data) {
        // Chamados abertos
        const chamadosEl = document.getElementById('kpi-chamados-abertos');
        if (chamadosEl) {
            chamadosEl.textContent = data.chamados_abertos || 0;
        }
        
        // Chamados do mês
        const mesEl = document.getElementById('kpi-chamados-mes');
        if (mesEl) {
            mesEl.textContent = data.chamados_mes || 0;
        }
        
        // Variação
        const variacaoEl = document.getElementById('kpi-variacao');
        if (variacaoEl && data.variacao_percentual !== undefined) {
            const variacao = data.variacao_percentual;
            const icon = variacao >= 0 ? 'fa-arrow-up' : 'fa-arrow-down';
            const color = variacao >= 0 ? 'text-success' : 'text-danger';
            
            variacaoEl.className = color + ' small';
            variacaoEl.innerHTML = `<i class="fas ${icon}"></i> ${Math.abs(variacao).toFixed(1)}%`;
        }
        
        // SLA
        const slaEl = document.getElementById('kpi-sla');
        if (slaEl) {
            slaEl.textContent = (data.sla_taxa || 0) + '%';
        }
        
        // Satisfação
        const satisfacaoEl = document.getElementById('kpi-satisfacao');
        if (satisfacaoEl) {
            satisfacaoEl.textContent = (data.satisfacao_media || 0) + '/5';
        }
        
        // Lembretes ativos
        const lembretesEl = document.getElementById('kpi-lembretes-ativos');
        if (lembretesEl) {
            lembretesEl.textContent = data.lembretes_ativos || 0;
        }
        
        // Lembretes vencidos
        const vencidosEl = document.getElementById('kpi-lembretes-vencidos');
        if (vencidosEl) {
            vencidosEl.textContent = data.lembretes_vencidos || 0;
        }
        
        // Equipamentos
        const equipamentosEl = document.getElementById('kpi-equipamentos-uso');
        if (equipamentosEl) {
            equipamentosEl.textContent = data.equipamentos_uso || 0;
        }
    }
    
    /**
     * Carrega dados dos gráficos
     */
    async loadChartData() {
        try {
            // Calcular período (últimos 30 dias)
            const endDate = new Date();
            const startDate = new Date();
            startDate.setDate(startDate.getDate() - 30);
            
            const params = new URLSearchParams({
                start: startDate.toISOString().split('T')[0],
                end: endDate.toISOString().split('T')[0]
            });
            
            // Chamados por período
            const chamadosResponse = await fetch(`/api/analytics/chamados-periodo?${params}`);
            const chamadosData = await chamadosResponse.json();
            this.createLineChart('chart-chamados-periodo', chamadosData);
            
            // Chamados por prioridade
            const prioridadeResponse = await fetch(`/api/analytics/chamados-prioridade?${params}`);
            const prioridadeData = await prioridadeResponse.json();
            this.createPieChart('chart-prioridade', prioridadeData);
            
            // Performance por técnico
            const performanceResponse = await fetch(`/api/analytics/performance-tecnico?${params}`);
            const performanceData = await performanceResponse.json();
            this.createBarChart('chart-performance', performanceData);
            
            // Chamados por setor
            const setorResponse = await fetch(`/api/analytics/chamados-setor?${params}`);
            const setorData = await setorResponse.json();
            this.createHorizontalBarChart('chart-setor', setorData);
            
        } catch (error) {
            console.error('Erro ao carregar dados dos gráficos:', error);
            this.showError('Erro ao carregar gráficos');
        }
    }
    
    /**
     * Cria gráfico de linha (evolução temporal)
     */
    createLineChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Destruir gráfico existente
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.map(d => this.formatDate(d.periodo)),
                datasets: [{
                    label: 'Chamados',
                    data: data.map(d => d.total),
                    borderColor: '#008BCD',
                    backgroundColor: 'rgba(0, 139, 205, 0.1)',
                    borderWidth: 2,
                    tension: 0.4,
                    fill: true
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        titleFont: {
                            size: 14
                        },
                        bodyFont: {
                            size: 13
                        }
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Cria gráfico de pizza
     */
    createPieChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        const colors = {
            'Baixa': '#28a745',
            'Media': '#ffc107',
            'Média': '#ffc107',
            'Alta': '#fd7e14',
            'Critica': '#dc3545',
            'Crítica': '#dc3545'
        };
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(d => d.prioridade),
                datasets: [{
                    data: data.map(d => d.total),
                    backgroundColor: data.map(d => colors[d.prioridade] || '#6c757d'),
                    borderWidth: 2,
                    borderColor: '#fff'
                }]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'bottom',
                        labels: {
                            padding: 15,
                            font: {
                                size: 12
                            }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Cria gráfico de barras verticais
     */
    createBarChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.tecnico),
                datasets: [
                    {
                        label: 'Total Chamados',
                        data: data.map(d => d.total),
                        backgroundColor: '#008BCD',
                        borderColor: '#006a9e',
                        borderWidth: 1
                    },
                    {
                        label: 'SLA Cumprido (%)',
                        data: data.map(d => d.sla_taxa),
                        backgroundColor: '#28a745',
                        borderColor: '#1e7e34',
                        borderWidth: 1
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        position: 'top'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true
                    }
                }
            }
        });
    }
    
    /**
     * Cria gráfico de barras horizontais
     */
    createHorizontalBarChart(canvasId, data) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: data.map(d => d.setor),
                datasets: [{
                    label: 'Chamados',
                    data: data.map(d => d.total),
                    backgroundColor: '#008BCD',
                    borderColor: '#006a9e',
                    borderWidth: 1
                }]
            },
            options: {
                indexAxis: 'y',
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: false
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Formata data para exibição
     */
    formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
    }
    
    /**
     * Configura atualização automática
     */
    setupRefresh() {
        // Atualizar KPIs a cada 5 minutos
        this.refreshInterval = setInterval(() => {
            this.loadKPIs();
        }, 5 * 60 * 1000);
    }
    
    /**
     * Mostra mensagem de erro
     */
    showError(message) {
        console.error(message);
        // Integrar com sistema de toast se disponível
        if (window.components && window.components.toast) {
            window.components.toast('error', 'Erro', message);
        }
    }
    
    /**
     * Limpa recursos
     */
    destroy() {
        // Limpar interval
        if (this.refreshInterval) {
            clearInterval(this.refreshInterval);
        }
        
        // Destruir gráficos
        Object.values(this.charts).forEach(chart => {
            if (chart) chart.destroy();
        });
        
        this.charts = {};
    }
}

// Inicializar quando página carregar
document.addEventListener('DOMContentLoaded', () => {
    // Verificar se Chart.js está disponível
    if (typeof Chart === 'undefined') {
        console.error('Chart.js não está carregado!');
        return;
    }
    
    // Inicializar dashboard
    window.analyticsDashboard = new AnalyticsDashboard();
});
