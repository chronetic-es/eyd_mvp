// Resumen — global KPIs + charts.
import { api } from '../api.js';
import { kpiCard, fmtMoney, humanize } from '../ui.js';

let charts = {};

function destroyCharts() {
    Object.values(charts).forEach(c => c && c.destroy());
    charts = {};
}

async function load(root) {
    const [summary, motives, timeline, billing] = await Promise.all([
        api.get('/api/summary'),
        api.get('/api/calls/motives'),
        api.get('/api/calls/timeline'),
        api.get('/api/billing/summary'),
    ]);

    root.innerHTML = `
        <div class="grid grid-cols-2 lg:grid-cols-4 gap-4">
            ${kpiCard('Abonados', summary.abonados, 'text-eyd-800')}
            ${kpiCard('Contratos activos', summary.contratos_activos, 'text-cyan-600')}
            ${kpiCard('Incidencias activas', summary.incidencias_activas, 'text-red-600')}
            ${kpiCard('Partes abiertos', summary.partes_abiertos, 'text-amber-600')}
            ${kpiCard('Llamadas (7d)', summary.llamadas_7d, 'text-eyd-800')}
            ${kpiCard('Recibos impagados', summary.recibos_impagados, 'text-red-600')}
            ${kpiCard('Deuda activa', fmtMoney(summary.deuda_activa), 'text-orange-600')}
        </div>

        <div class="grid grid-cols-1 lg:grid-cols-3 gap-5">
            <div class="card p-5">
                <h3 class="text-sm font-semibold text-gray-700 mb-3">Motivos de llamada</h3>
                <div class="flex justify-center"><canvas id="rs-motives" style="max-height:220px"></canvas></div>
            </div>
            <div class="card p-5">
                <h3 class="text-sm font-semibold text-gray-700 mb-3">Estado de recibos</h3>
                <div class="flex justify-center"><canvas id="rs-billing" style="max-height:220px"></canvas></div>
            </div>
            <div class="card p-5">
                <h3 class="text-sm font-semibold text-gray-700 mb-3">Llamadas por dia (30d)</h3>
                <canvas id="rs-timeline" style="max-height:220px"></canvas>
            </div>
        </div>`;

    destroyCharts();

    const palette = ['#1e40af', '#0891b2', '#d97706', '#dc2626', '#16a34a', '#7c3aed'];
    charts.motives = new Chart(document.getElementById('rs-motives'), {
        type: 'doughnut',
        data: {
            labels: motives.motives.map(m => humanize(m.motive || 'Otro')),
            datasets: [{ data: motives.motives.map(m => m.count), backgroundColor: palette, borderWidth: 0 }],
        },
        options: { responsive: true, plugins: { legend: { position: 'bottom', labels: { padding: 14, usePointStyle: true } } } },
    });

    const billColors = { 'Pagado': '#16a34a', 'Pendiente': '#d97706', 'Impagado': '#dc2626', 'Devuelto': '#ea580c' };
    charts.billing = new Chart(document.getElementById('rs-billing'), {
        type: 'doughnut',
        data: {
            labels: billing.by_status.map(s => s.status),
            datasets: [{ data: billing.by_status.map(s => s.count), backgroundColor: billing.by_status.map(s => billColors[s.status] || '#6b7280'), borderWidth: 0 }],
        },
        options: { responsive: true, plugins: { legend: { position: 'bottom', labels: { padding: 14, usePointStyle: true } } } },
    });

    charts.timeline = new Chart(document.getElementById('rs-timeline'), {
        type: 'bar',
        data: {
            labels: timeline.timeline.map(t => { const d = new Date(t.date); return d.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit' }); }),
            datasets: [{ label: 'Llamadas', data: timeline.timeline.map(t => t.count), backgroundColor: '#1e40af', borderRadius: 4 }],
        },
        options: { responsive: true, plugins: { legend: { display: false } }, scales: { y: { beginAtZero: true, ticks: { stepSize: 1 } } } },
    });
}

export default { load };
