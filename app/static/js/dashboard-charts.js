/**
 * Dashboard Charts Module
 * Handles all chart initialization and data management for the dashboard
 */

class DashboardCharts {
    constructor() {
        this.charts = new Map();
        this.initialized = false;
        this.setupThemeListener();
    }

    /**
     * Get theme-aware color palette from CSS variables
     */
    getThemePalette() {
        const root = getComputedStyle(document.documentElement);
        const isDark = document.documentElement.getAttribute('data-theme') === 'dark';
        
        return {
            primary: root.getPropertyValue('--primary-500').trim() || '#007bff',
            warning: root.getPropertyValue('--warning').trim() || '#ffc107',
            info: root.getPropertyValue('--info').trim() || '#17a2b8',
            secondary: isDark ? '#8b5cf6' : '#6f42c1',
            textColor: root.getPropertyValue('--text-primary').trim() || (isDark ? '#f8f9fa' : '#212529'),
            gridColor: root.getPropertyValue('--border-color').trim() || (isDark ? '#495057' : '#dee2e6'),
        };
    }

    /**
     * Setup theme change listener
     */
    setupThemeListener() {
        document.addEventListener('themeChanged', (e) => {
            this.updateChartsTheme();
        });
    }

    /**
     * Update all charts to match current theme
     */
    updateChartsTheme() {
        const palette = this.getThemePalette();
        
        this.charts.forEach((chart, name) => {
            // Update datasets colors
            chart.data.datasets.forEach((dataset, index) => {
                const colors = [palette.primary, palette.warning, palette.info, palette.secondary];
                const baseColor = colors[index % colors.length];
                
                if (chart.config.type === 'line') {
                    dataset.borderColor = baseColor;
                    dataset.backgroundColor = this.hexToRgba(baseColor, 0.1);
                } else {
                    dataset.backgroundColor = baseColor;
                }
            });

            // Update grid and text colors
            if (chart.options.scales) {
                const axisColor = palette.textColor;
                const gridColor = palette.gridColor;
                
                Object.keys(chart.options.scales).forEach(axis => {
                    if (chart.options.scales[axis].ticks) {
                        chart.options.scales[axis].ticks.color = axisColor;
                    }
                    if (chart.options.scales[axis].grid) {
                        chart.options.scales[axis].grid.color = gridColor;
                    }
                });
            }

            // Update legend colors
            if (chart.options.plugins?.legend?.labels) {
                chart.options.plugins.legend.labels.color = palette.textColor;
            }

            chart.update('none');
        });
    }

    /**
     * Convert hex color to rgba
     */
    hexToRgba(hex, alpha = 1) {
        hex = hex.replace('#', '');
        const r = parseInt(hex.substring(0, 2), 16);
        const g = parseInt(hex.substring(2, 4), 16);
        const b = parseInt(hex.substring(4, 6), 16);
        return `rgba(${r}, ${g}, ${b}, ${alpha})`;
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

        const palette = this.getThemePalette();
        const colors = [palette.primary, palette.warning, palette.info, palette.secondary];

        // Get data from global variables (set by template)
        const labels = window.dashboardChartData?.evolution?.labels || [];
        const datasets = [
            {
                label: 'Tarefas',
                data: window.dashboardChartData?.evolution?.tarefas || [],
                borderColor: colors[0],
                backgroundColor: this.hexToRgba(colors[0], 0.1),
                tension: 0.1,
                fill: true
            },
            {
                label: 'Lembretes',
                data: window.dashboardChartData?.evolution?.lembretes || [],
                borderColor: colors[1],
                backgroundColor: this.hexToRgba(colors[1], 0.1),
                tension: 0.1,
                fill: true
            },
            {
                label: 'Chamados',
                data: window.dashboardChartData?.evolution?.chamados || [],
                borderColor: colors[2],
                backgroundColor: this.hexToRgba(colors[2], 0.1),
                tension: 0.1,
                fill: true
            },
            {
                label: 'Equipamentos',
                data: window.dashboardChartData?.evolution?.equipamentos || [],
                borderColor: colors[3],
                backgroundColor: this.hexToRgba(colors[3], 0.1),
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
                        position: 'bottom',
                        labels: {
                            color: palette.textColor
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: palette.textColor
                        },
                        grid: {
                            color: palette.gridColor
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                            color: palette.textColor
                        },
                        grid: {
                            color: palette.gridColor
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

        const palette = this.getThemePalette();
        const colors = [palette.primary, palette.warning, palette.info, palette.secondary];

        // Get data from global variables
        const labels = window.dashboardChartData?.sectors?.labels || [];
        const datasets = [
            {
                label: 'Tarefas',
                data: window.dashboardChartData?.sectors?.tarefas || [],
                backgroundColor: colors[0]
            },
            {
                label: 'Lembretes',
                data: window.dashboardChartData?.sectors?.lembretes || [],
                backgroundColor: colors[1]
            },
            {
                label: 'Chamados',
                data: window.dashboardChartData?.sectors?.chamados || [],
                backgroundColor: colors[2]
            },
            {
                label: 'Equipamentos',
                data: window.dashboardChartData?.sectors?.equipamentos || [],
                backgroundColor: colors[3]
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
                        position: 'bottom',
                        labels: {
                            color: palette.textColor
                        }
                    }
                },
                scales: {
                    x: {
                        ticks: {
                            color: palette.textColor
                        },
                        grid: {
                            color: palette.gridColor
                        }
                    },
                    y: {
                        beginAtZero: true,
                        ticks: {
                            precision: 0,
                            color: palette.textColor
                        },
                        grid: {
                            color: palette.gridColor
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