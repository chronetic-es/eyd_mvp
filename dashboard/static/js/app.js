// Orchestrator: tabs, refresh, clock, section registry.
import { loadEnums } from './store.js';
import { toast } from './ui.js';

import resumen from './sections/resumen.js';
import abonados from './sections/abonados.js';
import facturacion from './sections/facturacion.js';
import incidencias from './sections/incidencias.js';
import partes from './sections/partes.js';
import llamadas from './sections/llamadas.js';

const sections = { resumen, abonados, facturacion, incidencias, partes, llamadas };
let current = 'resumen';

function rootFor(name) {
    return document.getElementById(`sec-${name}`);
}

async function loadCurrent() {
    const section = sections[current];
    if (!section) return;
    try {
        await section.load(rootFor(current));
    } catch (e) {
        console.error(`Error loading section ${current}:`, e);
        toast('No se pudieron cargar los datos.', 'error');
    }
}

function showTab(name) {
    if (!sections[name]) return;
    current = name;
    document.querySelectorAll('.dash-section').forEach(s => s.classList.add('hidden'));
    rootFor(name).classList.remove('hidden');
    document.querySelectorAll('.tab-btn').forEach(b =>
        b.classList.toggle('active', b.dataset.tab === name));
    loadCurrent();
}

function modalOpen() {
    return document.getElementById('modal-root').childElementCount > 0;
}

function userBusy() {
    const el = document.activeElement;
    return el && ['INPUT', 'SELECT', 'TEXTAREA'].includes(el.tagName);
}

function setupChrome() {
    document.querySelectorAll('.tab-btn').forEach(btn => {
        btn.addEventListener('click', () => showTab(btn.dataset.tab));
    });

    const refreshBtn = document.getElementById('refresh-btn');
    refreshBtn.addEventListener('click', async () => {
        refreshBtn.disabled = true;
        await loadCurrent();
        refreshBtn.disabled = false;
    });

    const clock = document.getElementById('clock');
    const tick = () => {
        clock.textContent = new Date().toLocaleString('es-ES', {
            day: '2-digit', month: '2-digit', year: 'numeric',
            hour: '2-digit', minute: '2-digit', second: '2-digit',
        });
    };
    tick();
    setInterval(tick, 1000);

    // Auto-refresh current section every 30s — but not while a modal is open
    // or the user is interacting with an input.
    setInterval(() => { if (!modalOpen() && !userBusy()) loadCurrent(); }, 30000);
}

async function init() {
    setupChrome();
    await loadEnums();
    showTab('resumen');
}

init();
