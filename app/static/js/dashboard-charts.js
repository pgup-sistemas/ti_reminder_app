/**
 * Dashboard Charts Module
 * Handles all chart initialization and data management for the dashboard
 */

class DashboardCharts {
    constructor() {
        this.charts = new Map();
        this.initialized = false;
    }

    /**
     * Initialize all dashboard charts
     */
    init() {
        if (this.initialized) return;

        this.initEvolutionChart();
        this.initSectorChart();
        this.initialized = true;
    }

    /**
     * Initialize evolution chart (line chart)
     */
    initEvolutionChart() {
        const canvas = document.getElementById('chartEvolution');
        if (!canvas) return;

        // Get data from global variables (set by template)
        const labels = window.dashboardChartData?.evolution?.labels || [];
        const datasets = [
            {
                label: 'Tarefas',
                data: window.dashboardChartData?.evolution?.tarefas || [],
                borderColor: '#007bff',
                backgroundColor: 'rgba(0, 123, 255, 0.1)',
                tension: 0.1,
                fill: true
            },
            {
                label: 'Lembretes',
                data: window.dashboardChartData?.evolution?.lembretes || [],
                borderColor: '#ffc107',
                backgroundColor: 'rgba(255, 193, 7, 0.1)',
                tension: 0.1,
                fill: true
            },
            {
                label: 'Chamados',
                data: window.dashboardChartData?.evolution?.chamados || [],
                borderColor: '#17a2b8',
                backgroundColor: 'rgba(23, 162, 184, 0.1)',
                tension: 0.1,
                fill: true
            },
            {
                label: 'Equipamentos',
                data: window.dashboardChartData?.evolution?.equipamentos || [],
                borderColor: '#6f42c1',
                backgroundColor: 'rgba(111, 66, 193, 0.1)',
                tension: 0.1,
                fill: true
            }
        ];

        const chart = new Chart(canvas, {
            type: 'line',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
                    }
                },
                scales: {
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0
                        }
                    }
                },
                interaction: {
                    intersect: false,
                    mode: 'index'
                }
            }
        });

        this.charts.set('evolution', chart);
    }

    /**
     * Initialize sector distribution chart (bar chart)
     */
    initSectorChart() {
        const canvas = document.getElementById('chartSector');
        if (!canvas) return;

        // Get data from global variables
        const labels = window.dashboardChartData?.sectors?.labels || [];
        const datasets = [
            {
                label: 'Tarefas',
                data: window.dashboardChartData?.sectors?.tarefas || [],
                backgroundColor: '#007bff'
            },
            {
                label: 'Lembretes',
                data: window.dashboardChartData?.sectors?.lembretes || [],
                backgroundColor: '#ffc107'
            },
            {
                label: 'Chamados',
                data: window.dashboardChartData?.sectors?.chamados || [],
                backgroundColor: '#17a2b8'
            },
            {
                label: 'Equipamentos',
                data: window.dashboardChartData?.sectors?.equipamentos || [],
                backgroundColor: '#6f42c1'
            }
        ];

        const chart = new Chart(canvas, {
            type: 'bar',
            data: {
                labels: labels,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    legend: {
                        position: 'bottom'
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

        this.charts.set('sector', chart);
    }

    /**
     * Update chart data dynamically
     * @param {string} chartName - Name of the chart to update
     * @param {Object} newData - New data to update
     */
    updateChart(chartName, newData) {
        const chart = this.charts.get(chartName);
        if (!chart) return;

        if (newData.labels) chart.data.labels = newData.labels;
        if (newData.datasets) chart.data.datasets = newData.datasets;

        chart.update();
    }

    /**
     * Destroy all charts (cleanup)
     */
    destroy() {
        this.charts.forEach(chart => chart.destroy());
        this.charts.clear();
        this.initialized = false;
    }

    /**
     * Resize all charts (responsive)
     */
    resize() {
        this.charts.forEach(chart => chart.resize());
    }
}

// Global instance
window.DashboardCharts = new DashboardCharts();

// Auto-initialize when DOM is ready
document.addEventListener('DOMContentLoaded', function() {
    // Only initialize if we're on the dashboard page
    if (document.getElementById('chartEvolution') || document.getElementById('chartSector')) {
        window.DashboardCharts.init();
    }
});

// Handle window resize
window.addEventListener('resize', function() {
    if (window.DashboardCharts) {
        window.DashboardCharts.resize();
    }
});