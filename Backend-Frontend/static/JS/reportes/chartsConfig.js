// Funciones de utilidad para fechas
export function getWeekNumber(d) {
    d = new Date(Date.UTC(d.getFullYear(), d.getMonth(), d.getDate()));
    d.setUTCDate(d.getUTCDate() + 4 - (d.getUTCDay() || 7));
    const yearStart = new Date(Date.UTC(d.getUTCFullYear(), 0, 1));
    return Math.ceil((((d - yearStart) / 86400000) + 1) / 7);
}

// Configuraciones compartidas de Chart.js
export const yAxisConfig = {
    beginAtZero: true,
    ticks: { stepSize: 1 }
};

export const doughnutTooltipConfig = {
    callbacks: {
        label: function(context) {
            let label = context.label || '';
            if (label) label += ': ';
            if (context.raw !== null) {
                label += '$' + context.raw.toLocaleString('es-CO');
            }
            return label;
        }
    }
};