/**
 * Analytics Dashboard
 * Gerencia gráficos e métricas do dashboard analítico
 */

class AnalyticsDashboard {
    constructor() {
        this.charts = {};
        this.refreshInterval = null;
        this.dateRange = {
            start: null,
            end: null
        };
        this.init();
    }
    
    async init() {
        console.log('[Analytics] ========== INICIALIZANDO DASHBOARD ==========');
        try {
            console.log('[Analytics] 1/5 - Inicializando filtros de data...');
            this.initializeDateFilters();
            
            console.log('[Analytics] 2/5 - Configurando event listeners...');
            this.setupEventListeners();
            
            console.log('[Analytics] 3/5 - Carregando KPIs...');
            await this.loadKPIs();
            
            console.log('[Analytics] 4/5 - Carregando gráficos...');
            await this.loadChartData();
            
            console.log('[Analytics] 5/5 - Configurando auto-refresh...');
            this.setupRefresh();
            
            console.log('[Analytics] ========== DASHBOARD INICIALIZADO ==========');
        } catch (error) {
            console.error('[Analytics] ERRO FATAL na inicialização:', error);
        }
    }
    
    /**
     * Configura event listeners
     */
    setupEventListeners() {
        // Botão aplicar filtros
        const btnApplyFilters = document.getElementById('btn-apply-filters');
        if (btnApplyFilters) {
            btnApplyFilters.addEventListener('click', () => this.applyFilters());
        }
        
        // Botão refresh
        const btnRefresh = document.getElementById('btn-refresh');
        if (btnRefresh) {
            btnRefresh.addEventListener('click', () => {
                this.loadKPIs();
                this.loadChartData();
            });
        }
        
        // Select de preset
        const filterPreset = document.getElementById('filter-preset');
        if (filterPreset) {
            filterPreset.addEventListener('change', () => this.applyPreset());
        }
        
        // Exportações
        const btnExportPDF = document.getElementById('btn-export-pdf');
        if (btnExportPDF) {
            btnExportPDF.addEventListener('click', (e) => {
                e.preventDefault();
                this.exportPDF();
            });
        }
        const btnExportExcel = document.getElementById('btn-export-excel');
        if (btnExportExcel) {
            btnExportExcel.addEventListener('click', (e) => {
                e.preventDefault();
                this.exportExcel();
            });
        }
        const btnExportImage = document.getElementById('btn-export-image');
        if (btnExportImage) {
            btnExportImage.addEventListener('click', (e) => {
                e.preventDefault();
                this.exportImage();
            });
        }
        
        console.log('[Analytics] Event listeners configurados!');
    }
    
    /**
     * Inicializa os filtros de data
     */
    initializeDateFilters() {
        const endDate = new Date();
        const startDate = new Date();
        startDate.setDate(startDate.getDate() - 30);
        
        const startInput = document.getElementById('filter-start-date');
        const endInput = document.getElementById('filter-end-date');
        
        if (startInput) {
            startInput.value = this.formatDateInput(startDate);
            this.dateRange.start = startDate;
        }
        
        if (endInput) {
            endInput.value = this.formatDateInput(endDate);
            this.dateRange.end = endDate;
        }
    }
    
    /**
     * Formata data para input type="date"
     */
    formatDateInput(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }
    
    /**
     * Aplica preset de período
     */
    applyPreset() {
        const preset = document.getElementById('filter-preset').value;
        const endDate = new Date();
        let startDate = new Date();
        
        if (preset === 'custom') {
            // Deixa usuário definir
            return;
        }
        
        const days = parseInt(preset);
        startDate.setDate(startDate.getDate() - days);
        
        document.getElementById('filter-start-date').value = this.formatDateInput(startDate);
        document.getElementById('filter-end-date').value = this.formatDateInput(endDate);
        
        this.dateRange.start = startDate;
        this.dateRange.end = endDate;
    }
    
    /**
     * Aplica filtros personalizados
     */
    async applyFilters() {
        const startInput = document.getElementById('filter-start-date');
        const endInput = document.getElementById('filter-end-date');
        
        if (startInput && endInput) {
            this.dateRange.start = new Date(startInput.value);
            this.dateRange.end = new Date(endInput.value);
            
            // Validação
            if (this.dateRange.start > this.dateRange.end) {
                alert('A data inicial não pode ser maior que a data final!');
                return;
            }
            
            // Recarregar gráficos com novo período
            await this.loadChartData();
            
            // Feedback visual
            this.showToast('success', 'Filtros aplicados com sucesso!');
        }
    }
    
    /**
     * Carrega KPIs principais
     */
    async loadKPIs() {
        console.log('[Analytics] Iniciando loadKPIs...');
        try {
            console.log('[Analytics] Fazendo fetch para /api/analytics/dashboard-kpis');
            const response = await fetch('/api/analytics/dashboard-kpis');
            console.log('[Analytics] Response status:', response.status);
            
            if (!response.ok) {
                console.error('[Analytics] Response não OK:', response.status, response.statusText);
                throw new Error(`Erro ao carregar KPIs: ${response.status}`);
            }
            
            const data = await response.json();
            console.log('[Analytics] Dados recebidos:', data);
            this.updateKPIs(data);
            console.log('[Analytics] KPIs atualizados com sucesso!');
        } catch (error) {
            console.error('[Analytics] ERRO ao carregar KPIs:', error);
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
        
        // Tutoriais
        const tutoriaisEl = document.getElementById('kpi-total-tutoriais');
        if (tutoriaisEl) {
            tutoriaisEl.textContent = data.total_tutoriais || 0;
        }
        
        const visualizacoesEl = document.getElementById('kpi-total-visualizacoes');
        if (visualizacoesEl) {
            visualizacoesEl.textContent = data.total_visualizacoes || 0;
        }
        
        // Tarefas
        const tasksConcluidasEl = document.getElementById('kpi-tasks-concluidas');
        if (tasksConcluidasEl) {
            tasksConcluidasEl.textContent = data.tasks_concluidas || 0;
        }
        
        const tasksPendentesEl = document.getElementById('kpi-tasks-pendentes');
        if (tasksPendentesEl) {
            tasksPendentesEl.textContent = data.tasks_pendentes || 0;
        }
    }
    
    /**
     * Carrega dados dos gráficos
     */
    async loadChartData() {
        console.log('[Analytics] Iniciando loadChartData...');
        try {
            // Usar período do filtro ou padrão
            const startDate = this.dateRange.start || new Date(Date.now() - 30 * 24 * 60 * 60 * 1000);
            const endDate = this.dateRange.end || new Date();
            
            const params = new URLSearchParams({
                start: startDate.toISOString().split('T')[0],
                end: endDate.toISOString().split('T')[0]
            });
            console.log('[Analytics] Período:', params.toString());
            
            // Chamados por período
            console.log('[Analytics] Carregando: chamados por período...');
            const chamadosResponse = await fetch(`/api/analytics/chamados-periodo?${params}`);
            const chamadosData = await chamadosResponse.json();
            console.log('[Analytics] Dados período:', chamadosData.length, 'registros');
            this.createLineChart('chart-chamados-periodo', chamadosData);
            
            // Chamados por prioridade
            console.log('[Analytics] Carregando: chamados por prioridade...');
            const prioridadeResponse = await fetch(`/api/analytics/chamados-prioridade?${params}`);
            const prioridadeData = await prioridadeResponse.json();
            console.log('[Analytics] Dados prioridade:', prioridadeData.length, 'registros');
            this.createPieChart('chart-prioridade', prioridadeData);
            
            // Performance por técnico
            console.log('[Analytics] Carregando: performance por técnico...');
            const performanceResponse = await fetch(`/api/analytics/performance-tecnico?${params}`);
            const performanceData = await performanceResponse.json();
            console.log('[Analytics] Dados performance:', performanceData.length, 'registros');
            this.createBarChart('chart-performance', performanceData);
            
            // Chamados por setor
            console.log('[Analytics] Carregando: chamados por setor...');
            const setorResponse = await fetch(`/api/analytics/chamados-setor?${params}`);
            const setorData = await setorResponse.json();
            console.log('[Analytics] Dados setor:', setorData.length, 'registros');
            this.createHorizontalBarChart('chart-setor', setorData);
            
            // Tutoriais por categoria
            console.log('[Analytics] Carregando: tutoriais por categoria...');
            try {
                const tutoriaisCatResponse = await fetch('/api/analytics/tutoriais-categoria');
                if (tutoriaisCatResponse.ok) {
                    const tutoriaisCatData = await tutoriaisCatResponse.json();
                    console.log('[Analytics] Dados tutoriais categoria:', tutoriaisCatData.length, 'registros');
                    if (tutoriaisCatData.length > 0) {
                        this.createPieChart('chart-tutoriais-categoria', tutoriaisCatData, 'categoria');
                    } else {
                        this.showEmptyChart('chart-tutoriais-categoria', 'Nenhum tutorial cadastrado');
                    }
                } else {
                    console.warn('[Analytics] Erro ao carregar tutoriais categoria:', tutoriaisCatResponse.status);
                }
            } catch (e) {
                console.error('[Analytics] Erro tutoriais categoria:', e);
            }
            
            // Tutoriais mais visualizados
            console.log('[Analytics] Carregando: tutoriais mais visualizados...');
            try {
                const tutoriaisTopResponse = await fetch('/api/analytics/tutoriais-mais-visualizados?limit=10');
                if (tutoriaisTopResponse.ok) {
                    const tutoriaisTopData = await tutoriaisTopResponse.json();
                    console.log('[Analytics] Dados tutoriais top:', tutoriaisTopData.length, 'registros');
                    if (tutoriaisTopData.length > 0) {
                        this.createHorizontalBarChart('chart-tutoriais-top', tutoriaisTopData, 'tutoriais');
                    } else {
                        this.showEmptyChart('chart-tutoriais-top', 'Nenhuma visualização registrada');
                    }
                } else {
                    console.warn('[Analytics] Erro ao carregar tutoriais top:', tutoriaisTopResponse.status);
                }
            } catch (e) {
                console.error('[Analytics] Erro tutoriais top:', e);
            }
            
            // Tarefas por período
            console.log('[Analytics] Carregando: tarefas por período...');
            try {
                const tasksResponse = await fetch(`/api/analytics/tasks-periodo?${params}`);
                if (tasksResponse.ok) {
                    const tasksData = await tasksResponse.json();
                    console.log('[Analytics] Dados tarefas:', tasksData.length, 'registros');
                    if (tasksData.length > 0) {
                        this.createTasksLineChart('chart-tasks-periodo', tasksData);
                    } else {
                        this.showEmptyChart('chart-tasks-periodo', 'Nenhuma tarefa no período');
                    }
                } else {
                    console.warn('[Analytics] Erro ao carregar tarefas:', tasksResponse.status);
                }
            } catch (e) {
                console.error('[Analytics] Erro tarefas:', e);
            }
            
            console.log('[Analytics] Todos os gráficos carregados!');
        } catch (error) {
            console.error('[Analytics] ERRO ao carregar dados dos gráficos:', error);
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
    createPieChart(canvasId, data, labelField = 'prioridade') {
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
        
        // Gerar cores aleatórias para categorias não mapeadas
        const generateColor = (index) => {
            const hue = (index * 137.508) % 360; // Golden angle
            return `hsl(${hue}, 70%, 60%)`;
        };
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'doughnut',
            data: {
                labels: data.map(d => d[labelField]),
                datasets: [{
                    data: data.map(d => d.total),
                    backgroundColor: data.map((d, i) => colors[d[labelField]] || generateColor(i)),
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
    createHorizontalBarChart(canvasId, data, type = 'setor') {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        // Configurar labels e dados baseado no tipo
        let labels, values, label;
        if (type === 'tutoriais') {
            labels = data.map(d => d.titulo);
            values = data.map(d => d.visualizacoes);
            label = 'Visualizações';
        } else {
            labels = data.map(d => d.setor);
            values = data.map(d => d.total);
            label = 'Chamados';
        }
        
        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: [{
                    label: label,
                    data: values,
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
                    },
                    tooltip: {
                        backgroundColor: 'rgba(0, 0, 0, 0.8)',
                        padding: 12,
                        callbacks: {
                            title: function(context) {
                                // Truncar títulos longos no tooltip
                                let title = context[0].label;
                                return title.length > 50 ? title.substring(0, 47) + '...' : title;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    },
                    y: {
                        ticks: {
                            callback: function(value, index) {
                                // Truncar labels longos no eixo Y
                                let label = this.getLabelForValue(value);
                                return label.length > 30 ? label.substring(0, 27) + '...' : label;
                            }
                        }
                    }
                }
            }
        });
    }
    
    /**
     * Cria gráfico de linha para tarefas
     */
    createTasksLineChart(canvasId, data) {
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
                datasets: [
                    {
                        label: 'Total',
                        data: data.map(d => d.total),
                        borderColor: '#008BCD',
                        backgroundColor: 'rgba(0, 139, 205, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Concluídas',
                        data: data.map(d => d.concluidas),
                        borderColor: '#28a745',
                        backgroundColor: 'rgba(40, 167, 69, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true
                    },
                    {
                        label: 'Pendentes',
                        data: data.map(d => d.pendentes),
                        borderColor: '#ffc107',
                        backgroundColor: 'rgba(255, 193, 7, 0.1)',
                        borderWidth: 2,
                        tension: 0.4,
                        fill: true
                    }
                ]
            },
            options: {
                responsive: true,
                maintainAspectRatio: true,
                plugins: {
                    legend: {
                        display: true,
                        position: 'top'
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
     * Formata data para exibição
     */
    formatDate(dateString) {
        if (!dateString) return '';
        const date = new Date(dateString);
        return date.toLocaleDateString('pt-BR', { day: '2-digit', month: '2-digit' });
    }
    
    /**
     * Mostra mensagem para gráfico vazio
     */
    showEmptyChart(canvasId, message) {
        const canvas = document.getElementById(canvasId);
        if (!canvas) return;
        
        const ctx = canvas.getContext('2d');
        
        // Destruir gráfico existente
        if (this.charts[canvasId]) {
            this.charts[canvasId].destroy();
        }
        
        // Criar gráfico vazio com mensagem
        this.charts[canvasId] = new Chart(ctx, {
            type: 'bar',
            data: {
                labels: [''],
                datasets: [{
                    label: message,
                    data: [0],
                    backgroundColor: '#e9ecef'
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
                        enabled: false
                    }
                },
                scales: {
                    y: {
                        display: false
                    },
                    x: {
                        display: false
                    }
                }
            }
        });
        
        // Adicionar texto no canvas
        const parent = canvas.parentElement;
        let emptyMsg = parent.querySelector('.empty-chart-message');
        if (!emptyMsg) {
            emptyMsg = document.createElement('div');
            emptyMsg.className = 'empty-chart-message text-center text-muted py-5';
            emptyMsg.innerHTML = `<i class="fas fa-inbox fa-3x mb-3 d-block opacity-25"></i><p>${message}</p>`;
            parent.style.position = 'relative';
            emptyMsg.style.position = 'absolute';
            emptyMsg.style.top = '50%';
            emptyMsg.style.left = '50%';
            emptyMsg.style.transform = 'translate(-50%, -50%)';
            emptyMsg.style.zIndex = '10';
            parent.appendChild(emptyMsg);
        } else {
            emptyMsg.innerHTML = `<i class="fas fa-inbox fa-3x mb-3 d-block opacity-25"></i><p>${message}</p>`;
        }
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
     * Mostra toast de sucesso
     */
    showToast(type, message) {
        if (window.components && window.components.toast) {
            window.components.toast(type, type === 'success' ? 'Sucesso' : 'Aviso', message);
        } else {
            console.log(`${type}: ${message}`);
        }
    }
    
    /**
     * Exporta dashboard como PDF
     */
    async exportPDF() {
        try {
            const startDate = (this.dateRange.start || new Date(Date.now() - 30*24*60*60*1000))
                .toISOString().split('T')[0];
            const endDate = (this.dateRange.end || new Date()).toISOString().split('T')[0];
            const url = `/api/analytics/export/pdf?start=${startDate}&end=${endDate}`;
            window.open(url, '_blank');
        } catch (error) {
            console.error('Erro ao exportar PDF:', error);
            alert('Erro ao exportar PDF. Tente novamente.');
        }
    }
    
    /**
     * Exporta dados como Excel
     */
    async exportExcel() {
        try {
            const startDate = (this.dateRange.start || new Date(Date.now() - 30*24*60*60*1000))
                .toISOString().split('T')[0];
            const endDate = (this.dateRange.end || new Date()).toISOString().split('T')[0];
            const url = `/api/analytics/export/excel?start=${startDate}&end=${endDate}`;
            window.open(url, '_blank');
        } catch (error) {
            console.error('Erro ao exportar Excel:', error);
            alert('Erro ao exportar dados. Tente novamente.');
        }
    }
    
    /**
     * Exporta dashboard como imagem
     */
    async exportImage() {
        try {
            const element = document.getElementById('analytics-content') || document.querySelector('.container-fluid');
            
            if (typeof html2canvas === 'undefined') {
                await this.loadExportLibraries();
            }
            
            const canvas = await html2canvas(element, {
                scale: 2,
                logging: false,
                useCORS: true
            });
            
            canvas.toBlob(blob => {
                const link = document.createElement('a');
                link.href = URL.createObjectURL(blob);
                link.download = `analytics_dashboard_${this.formatDateInput(new Date())}.png`;
                link.click();
                
                this.showToast('success', 'Imagem exportada com sucesso!');
            });
        } catch (error) {
            console.error('Erro ao exportar imagem:', error);
            alert('Erro ao exportar imagem. Tente novamente.');
        }
    }
    
    /**
     * Carrega bibliotecas de exportação dinamicamente
     */
    async loadExportLibraries() {
        return new Promise((resolve, reject) => {
            // html2canvas
            const script1 = document.createElement('script');
            script1.src = 'https://cdnjs.cloudflare.com/ajax/libs/html2canvas/1.4.1/html2canvas.min.js';
            script1.onload = () => {
                // jsPDF
                const script2 = document.createElement('script');
                script2.src = 'https://cdnjs.cloudflare.com/ajax/libs/jspdf/2.5.1/jspdf.umd.min.js';
                script2.onload = () => {
                    window.jsPDF = window.jspdf.jsPDF;
                    resolve();
                };
                script2.onerror = reject;
                document.head.appendChild(script2);
            };
            script1.onerror = reject;
            document.head.appendChild(script1);
        });
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
    console.log('[Analytics] DOM Content Loaded!');
    console.log('[Analytics] Verificando Chart.js...');
    
    // Verificar se Chart.js está disponível
    if (typeof Chart === 'undefined') {
        console.error('[Analytics] ❌ ERRO: Chart.js não está carregado!');
        alert('ERRO: Chart.js não foi carregado. Verifique sua conexão com a internet.');
        return;
    }
    
    console.log('[Analytics] ✅ Chart.js disponível!');
    console.log('[Analytics] Criando instância do AnalyticsDashboard...');
    
    // Inicializar dashboard
    window.analyticsDashboard = new AnalyticsDashboard();
});
