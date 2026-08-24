import { getWeekNumber, yAxisConfig, doughnutTooltipConfig } from './chartsConfig.js';
import { ApiService } from './apiService.js';

document.addEventListener("DOMContentLoaded", function() {
    
    // === 0. POBLAR SELECTORES DE SEMANAS ===
    const fechaActual = new Date();
    const semanaActual = getWeekNumber(fechaActual);
    const selectoresSemanas = document.querySelectorAll('.selector-semana-comun');
    
    selectoresSemanas.forEach(selector => {
        for (let i = 0; i < 12; i++) {
            let numeroSemana = semanaActual - i;
            if (numeroSemana <= 0) numeroSemana = 52 + numeroSemana; 
            const option = document.createElement('option');
            option.value = numeroSemana;
            option.text = `Semana S${numeroSemana}`;
            if (i === 0) option.selected = true;
            selector.appendChild(option);
        }
    });

    // === 1. INICIALIZACIÓN DE GRÁFICAS ===
    const chartCocina = new Chart(document.getElementById('graficaCocina').getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'],
            datasets: [{
                label: 'Platos Cocinados',
                data: [0, 0, 0, 0, 0, 0, 0],
                backgroundColor: 'rgba(247, 127, 0, 0.65)',
                borderColor: 'rgba(247, 127, 0, 1)',
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, scales: { y: yAxisConfig } }
    });

    const chartBarra = new Chart(document.getElementById('graficaBarra').getContext('2d'), {
        type: 'bar',
        data: {
            labels: ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo'],
            datasets: [{
                label: 'Bebidas Servidas',
                data: [0, 0, 0, 0, 0, 0, 0],
                backgroundColor: 'rgba(54, 162, 235, 0.65)',
                borderColor: 'rgba(54, 162, 235, 1)',
                borderWidth: 1,
                borderRadius: 5
            }]
        },
        options: { responsive: true, maintainAspectRatio: false, scales: { y: yAxisConfig } }
    });

    const chartPago = new Chart(document.getElementById('graficaMetodosPago').getContext('2d'), {
        type: 'doughnut',
        data: { labels: [], datasets: [{ data: [], backgroundColor: ['rgba(46, 196, 182, 0.7)', 'rgba(203, 243, 240, 0.7)', 'rgba(241, 91, 181, 0.7)'], borderWidth: 1 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' }, tooltip: doughnutTooltipConfig } }
    });

    const chartSedes = new Chart(document.getElementById('graficaSedes').getContext('2d'), {
        type: 'doughnut',
        data: { labels: [], datasets: [{ data: [], backgroundColor: ['rgba(141, 153, 174, 0.7)', 'rgba(239, 35, 60, 0.7)', 'rgba(255, 190, 11, 0.7)'], borderWidth: 1 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { position: 'bottom' }, tooltip: doughnutTooltipConfig } }
    });

    const chartLineas = new Chart(document.getElementById('graficaLinealHistorico').getContext('2d'), {
        type: 'line',
        data: { labels: [], datasets: [{ label: 'Ingresos por Ventas ($ COP)', data: [], borderColor: 'rgba(75, 192, 192, 1)', backgroundColor: 'rgba(75, 192, 192, 0.15)', fill: true, tension: 0.35 }] },
        options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { callback: v => '$' + v.toLocaleString('es-CO') } } } }
    });

    const chartMargen = new Chart(document.getElementById('graficaMargenGanancia').getContext('2d'), {
        type: 'bar',
        data: { labels: [], datasets: [{ label: 'Ventas Totales ($)', data: [], backgroundColor: 'rgba(54, 162, 235, 0.7)' }, { label: 'Costo Teórico ($)', data: [], backgroundColor: 'rgba(239, 35, 60, 0.7)' }] },
        options: { responsive: true, maintainAspectRatio: false, scales: { y: { beginAtZero: true, ticks: { callback: v => '$' + v.toLocaleString('es-CO') } } } }
    });

    const chartHoras = new Chart(document.getElementById('graficaHorasPico').getContext('2d'), {
        type: 'bar',
        data: { labels: [], datasets: [{ label: 'Cantidad de Pedidos', data: [], backgroundColor: 'rgba(255, 190, 11, 0.75)' }] },
        options: { responsive: true, maintainAspectRatio: false, scales: { y: yAxisConfig } }
    });

    // === 2. FUNCIONES DE CARGA DE DATOS ===
    function cargarDatosCocina() {
        const pId = document.getElementById('selectorCocina').value;
        const sId = document.getElementById('semanaCocina').value;
        if (!pId || !sId) return;
        ApiService.fetchVentasProductoSemana(pId, sId).then(data => {
            chartCocina.data.labels = data.labels;
            chartCocina.data.datasets[0].data = data.valores;
            chartCocina.update();
        });
    }

    function cargarDatosBarra() {
        const pId = document.getElementById('selectorBarra').value;
        const sId = document.getElementById('semanaBarra').value;
        if (!pId || !sId) return;
        ApiService.fetchVentasProductoSemana(pId, sId).then(data => {
            chartBarra.data.labels = data.labels;
            chartBarra.data.datasets[0].data = data.valores;
            chartBarra.update();
        });
    }

    function cargarDonasActualizadas(tipo, valor) {
        ApiService.fetchDonas(tipo, valor).then(data => {
            chartPago.data.labels = data.pagos.labels;
            chartPago.data.datasets[0].data = data.pagos.valores;
            chartPago.update();

            chartSedes.data.labels = data.sedes.labels;
            chartSedes.data.datasets[0].data = data.sedes.valores;
            chartSedes.update();
        });
    }

    // === 3. LISTENERS EN EL DOM ===
    document.getElementById('selectorCocina').addEventListener('change', cargarDatosCocina);
    document.getElementById('semanaCocina').addEventListener('change', cargarDatosCocina);
    document.getElementById('selectorBarra').addEventListener('change', cargarDatosBarra);
    document.getElementById('semanaBarra').addEventListener('change', cargarDatosBarra);

    const tipoFiltroDona = document.getElementById('tipoFiltroDona');
    const valorFiltroDona = document.getElementById('valorFiltroDona');

    tipoFiltroDona.addEventListener('change', function() {
        const seleccion = this.value;
        valorFiltroDona.innerHTML = '';
        
        if (seleccion === 'todos') {
            valorFiltroDona.disabled = true;
            const option = document.createElement('option');
            option.value = ""; option.text = "Todo el histórico";
            valorFiltroDona.appendChild(option);
            cargarDonasActualizadas("", "");
            return;
        }

        valorFiltroDona.disabled = false;
        if (seleccion === 'semana') {
            for (let i = 0; i < 12; i++) {
                let numSem = semanaActual - i;
                if (numSem <= 0) numSem = 52 + numSem;
                const opt = document.createElement('option');
                opt.value = numSem; opt.text = `Semana S${numSem}`;
                valorFiltroDona.appendChild(opt);
            }
        } else if (seleccion === 'trimestre') {
            [{val:1, text:"Q1"}, {val:2, text:"Q2"}, {val:3, text:"Q3"}, {val:4, text:"Q4"}].forEach(q => {
                const opt = document.createElement('option');
                opt.value = q.val; opt.text = q.text;
                if (q.val === Math.ceil((new Date().getMonth() + 1) / 3)) opt.selected = true;
                valorFiltroDona.appendChild(opt);
            });
        } else if (seleccion === 'semestre') {
            [{val:1, text:"1er Semestre"}, {val:2, text:"2do Semestre"}].forEach(s => {
                const opt = document.createElement('option');
                opt.value = s.val; opt.text = s.text;
                if (s.val === (new Date().getMonth() + 1 <= 6 ? 1 : 2)) opt.selected = true;
                valorFiltroDona.appendChild(opt);
            });
        }
        cargarDonasActualizadas(seleccion, valorFiltroDona.value);
    });

    valorFiltroDona.addEventListener('change', function() {
        cargarDonasActualizadas(tipoFiltroDona.value, this.value);
    });

    // === 4. EJECUCIÓN INICIAL ===
    ApiService.fetchHistoricoSemanal().then(data => {
        chartLineas.data.labels = data.labels;
        chartLineas.data.datasets[0].data = data.valores;
        chartLineas.update();
    });

    ApiService.fetchMargenGanancia().then(data => {
        chartMargen.data.labels = data.labels;
        chartMargen.data.datasets[0].data = data.ingresos;
        chartMargen.data.datasets[1].data = data.costos;
        chartMargen.update();
    });

    ApiService.fetchHorasPico().then(data => {
        chartHoras.data.labels = data.labels;
        chartHoras.data.datasets[0].data = data.valores;
        chartHoras.update();
    });

    cargarDatosCocina();
    cargarDatosBarra();
    cargarDonasActualizadas("", "");
});