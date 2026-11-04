export const ApiService = {
    async fetchVentasProductoSemana(productoId, semanaId) {
        const response = await fetch(`/api/ventas-producto-semana/?producto_id=${productoId}&semana=${semanaId}`);
        return response.json();
    },

    async fetchDonas(tipo, valor) {
        let queryParams = (tipo && valor) ? `?tipo_filtro=${tipo}&valor_filtro=${valor}` : "";
        
        const [pagoRes, sedeRes] = await Promise.all([
            fetch(`/api/ventas-metodos-pago/${queryParams}`),
            fetch(`/api/ventas-por-sede/${queryParams}`)
        ]);
        
        return {
            pagos: await pagoRes.json(),
            sedes: await sedeRes.json()
        };
    },

    async fetchHistoricoSemanal() {
        const response = await fetch('/api/ventas-historico-semanal/');
        return response.json();
    },

    async fetchMargenGanancia() {
        const response = await fetch('/api/margen-ganancia-productos/');
        return response.json();
    },

    async fetchHorasPico() {
        const response = await fetch('/api/horas-pico-ventas/');
        return response.json();
    }
};