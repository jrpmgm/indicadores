// ================================
// graficos.js (versión rediseñada)
// ================================

// Paleta de colores elegante
const baseColors = [
    '#4CAF50', '#42A5F5', '#FF9800',
    '#E91E63', '#9C27B0', '#00ACC1',
    '#8BC34A', '#F44336', '#3F51B5'
];

// Fuente y tipografía base
const baseFont = {
    family: "'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif",
    size: 14,
    weight: '500'
};

// Opciones generales para todos los gráficos
function getChartOptions(horizontal = false) {
    const baseOptions = {
        responsive: true,
        maintainAspectRatio: false,
        animation: {
            duration: 600,
            easing: 'easeOutQuart'
        },
        plugins: {
            legend: {
                labels: {
                    color: '#333',
                    font: baseFont
                }
            },
            tooltip: {
                backgroundColor: '#fff',
                titleColor: '#333',
                bodyColor: '#555',
                borderColor: '#ddd',
                borderWidth: 1,
                padding: 10,
                displayColors: false
            }
        },
        scales: {
            x: {
                grid: { display: false },
                ticks: { color: '#555', font: baseFont }
            },
            y: {
                beginAtZero: true,
                grid: { color: 'rgba(0,0,0,0.05)', lineWidth: 3 },
                ticks: { color: '#0a0a0aff', font: baseFont }
            }
        }
    };

    // Clona baseOptions y ajusta si es horizontal
    return Object.assign({}, baseOptions, {
        indexAxis: horizontal ? 'y' : 'x'
    });
}


/* const chartOptions = {
    responsive: true,
    animation: {
        duration: 600,
        easing: 'easeOutQuart'
    },
    plugins: {
        legend: {
            display: true,
            labels: {
                color: "#2c3e50",  // texto oscuro elegante
                font: {
                    size: 14,
                    weight: "600"
                }
            }
        },
        tooltip: {
            mode: 'index',
            intersect: false,
            backgroundColor: "rgba(44, 62, 80, 0.85)", // gris oscuro elegante
            titleColor: "#fff",
            bodyColor: "#ecf0f1",
            borderColor: "#95a5a6",
            borderWidth: 1
        }
    },
    scales: {
        y: {
            beginAtZero: true,
            ticks: {
                color: "#34495e",
                font: {
                    size: 13,
                    weight: "500"
                }
            },
            grid: {
                display: true,
                color: "rgba(117, 115, 115, 0.58)", // gris suave
                lineWidth: 1            // 🔹 más grueso
            }
        },
        x: {
            ticks: {
                color: "#34495e",
                font: {
                    size: 13,
                    weight: "500"
                }
            },
            grid: {
                display: false,
                color: "rgba(0,0,0,0.05)", // aún más suave
                lineWidth: 2               // 🔹 más grueso
            }
        }
    }
}; */

/**
 * Calcula el color de contraste (negro o blanco) en función de un fondo
 */
function getContrastColor(hexColor) {
    if (!hexColor) return '#000';
    const c = hexColor.substring(1);
    const rgb = parseInt(c, 16);
    const r = (rgb >> 16) & 0xff;
    const g = (rgb >> 8) & 0xff;
    const b = (rgb >> 0) & 0xff;
    const luma = 0.299 * r + 0.587 * g + 0.114 * b;
    return luma > 186 ? '#333' : '#fff';
}

/**
 * Genera colores dinámicos para gráficos tipo pie/doughnut/polarArea
 */
function generarColores(cantidad) {
    const colores = [];
    for (let i = 0; i < cantidad; i++) {
        colores.push(baseColors[i % baseColors.length]);
    }
    return colores;
}

/**
 * Función principal para graficar ventas
 */
function graficarSales(canvasId, data, typegra, agrouptype) {
    
    if (Chart.getChart(canvasId)){
        Chart.getChart(canvasId).destroy();
    }

    if (!Array.isArray(data)) {
        console.error("Error: 'data' no es un array válido.", data);
        return null;
    }
    const ctx = document.getElementById(canvasId).getContext('2d');

    /* const labels = agrouptype === 'Mensual'
        ? data.map(d => d.month_name)
        : data.map(d => String(d.year));
    const valores = data.map(d => {
        const subtotal = parseFloat(d.subtotal);
        return isNaN(subtotal) ? 0 : subtotal;
    });
    
    const valoresAdd  = data.map(d => {
        const adicional = parseFloat(d.periodoanterior);
        return isNaN(adicional) ? 0 : adicional;
    }); */

    const labels = data.map(d => d.periodo);
    const valores = data.map(d => parseFloat(d.subtotal || 0));
    const valoresAdd = data.map(d => parseFloat(d.periodoanterior || 0));

    let chartConfig = {};
    switch (typegra) {
        case 'bar':
        case 'barH':
        case 'line':
            chartConfig = {
                type: typegra === 'barH' ? 'bar' : typegra,
                data: {
                    labels: labels,
                    datasets: [{
                            label: 'Ventas Año Actual',
                            data: valores,
                            backgroundColor: typegra === 'bar' ? 'rgba(125, 189, 241, 1)' : 'rgb(66,165,245)',
                            borderColor: '#2196F3',
                            borderWidth: 1,
                            borderRadius: typegra === 'bar' ? 6 : 0,
                            tension: typegra === 'line' ? 0.4 : 0,
                            fill: typegra === 'line' ? false : true
                        },
                        {
                            label: 'Ventas Año Anterior',
                            data: valoresAdd,
                            backgroundColor: typegra === 'bar' ? 'rgba(247, 192, 111, 1)' : 'rgb(255,152,0)',
                            borderColor: '#FF9800',
                            borderWidth: 1,
                            borderRadius: typegra === 'bar' ? 6 : 0,
                            tension: typegra === 'line' ? 0.4 : 0,
                            fill: typegra === 'line' ? false : true
                        }
                    ]
                },
                options: typegra === 'barH'? getChartOptions(true) : getChartOptions(false)
            };
            break;

        case 'pie':
        case 'doughnut':
        case 'polarArea':
            chartConfig = {
                type: typegra,
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Totales',
                        data: valores,
                        backgroundColor: generarColores(valores.length),
                        borderColor: '#fff',
                        borderWidth: 2
                    }]
                },
                options: {
                    ...getChartOptions(false),
                    plugins: {
                        /* ...chartOptions.plugins, */
                        legend: { display: false },
                        datalabels: {
                            color: function (ctx) {
                                const bgColor = ctx.chart.data.datasets[0].backgroundColor[ctx.dataIndex];
                                return getContrastColor(bgColor);
                            },
                            font: { weight: 'bold', size: 12 },
                            formatter: (value, context) => context.chart.data.labels[context.dataIndex]
                        }
                    }
                },
                plugins: typeof ChartDataLabels !== 'undefined' ? [ChartDataLabels] : []
            };
            break;

        default:
            console.warn(`Tipo de gráfico no reconocido: ${typegra}, usando 'bar'.`);
            chartConfig = {
                type: 'bar',
                data: {
                    labels: labels,
                    datasets: [{
                        label: 'Total Facturado',
                        data: valores,
                        backgroundColor: baseColors,
                        borderRadius: 6,
                        borderWidth: 1
                    }]
                },
                options: getChartOptions(false)
            };
            break;
    }

    return new Chart(ctx, chartConfig);
}
