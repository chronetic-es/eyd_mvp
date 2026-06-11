// Incidencias — cards with affected addresses + work orders; full CRUD,
// link/unlink addresses, quick-close, and generate a work order from an incident.
import { api } from '../api.js';
import { store } from '../store.js';
import { openForm } from '../forms.js';
import {
    sectionHeader, badge, fmtDate, esc, humanize,
    toast, confirmDialog, addrLabel,
} from '../ui.js';

let rootEl = null;
let filterActive = 'all';

async function reload() {
    const { incidents, active_count, total_count } = await api.get('/api/incidencias');
    const filtered = incidents.filter(i =>
        filterActive === 'all' || (filterActive === 'active' ? i.active : !i.active));

    rootEl.querySelector('#inc-stats').innerHTML =
        `<span class="text-red-600 font-semibold">${active_count}</span> activas · ${total_count} totales`;

    const list = rootEl.querySelector('#inc-list');
    if (!filtered.length) {
        list.innerHTML = `<div class="card px-5 py-10 text-center text-gray-400 text-sm">No hay incidencias.</div>`;
        return;
    }

    list.innerHTML = filtered.map(inc => {
        const wrap = inc.active ? 'border-red-200 bg-red-50' : 'border-gray-200 bg-gray-50 opacity-80';
        const statusBadge = inc.active ? badge('Abierta') : badge('Resuelta');
        const addrs = inc.addresses.map(a => `
            <span class="inline-flex items-center gap-1 bg-white border border-gray-200 rounded-full pl-2.5 pr-1 py-0.5 text-xs mr-1 mb-1">
                ${esc(addrLabel(a))}
                <button class="text-gray-400 hover:text-red-500 w-4 h-4 leading-none" data-unlink="${inc.id}:${a.id}" title="Quitar">×</button>
            </span>`).join('') || '<span class="text-xs text-gray-400">Sin direcciones</span>';
        const wos = inc.work_orders.map(w =>
            `<span class="inline-flex items-center gap-1 text-xs mr-2">${esc(w.numero_parte)} ${badge(w.estado)}</span>`
        ).join('') || '<span class="text-xs text-gray-400">Sin partes</span>';
        const finStr = inc.active
            ? (inc.fecha_fin_prevista ? `Est. fin: ${fmtDate(inc.fecha_fin_prevista)} ${inc.hora_fin_prevista || ''}` : 'Sin estimacion')
            : `Resuelta: ${fmtDate(inc.fecha_fin)} ${inc.hora_fin || ''}`;

        return `<div class="rounded-xl border ${wrap} p-5 shadow-sm">
            <div class="flex items-start justify-between flex-wrap gap-2">
                <div class="flex items-center gap-2">
                    ${badge(inc.tipo)} ${statusBadge}
                    <span class="text-xs text-gray-400">#${inc.id}</span>
                </div>
                <span class="text-xs text-gray-500">${fmtDate(inc.fecha_inicio)} ${inc.hora_inicio || ''}</span>
            </div>
            <p class="mt-2 text-sm text-gray-700">${esc(inc.descripcion)}</p>
            <div class="mt-3 text-xs text-gray-500"><strong>${finStr}</strong></div>
            <div class="mt-2"><span class="text-xs text-gray-400 mr-1">Direcciones:</span>${addrs}
                <button class="btn btn-ghost btn-sm" data-addaddr="${inc.id}">+ Añadir</button></div>
            <div class="mt-2"><span class="text-xs text-gray-400 mr-1">Partes:</span>${wos}</div>
            <div class="mt-3 flex flex-wrap gap-2 pt-3 border-t border-black/5">
                ${inc.active ? `<button class="btn btn-secondary btn-sm" data-close="${inc.id}">Cerrar</button>` : ''}
                <button class="btn btn-secondary btn-sm" data-parte="${inc.id}">Generar parte</button>
                <button class="btn btn-secondary btn-sm" data-edit="${inc.id}">Editar</button>
                <button class="btn btn-danger btn-sm" data-del="${inc.id}">Borrar</button>
            </div>
        </div>`;
    }).join('');

    bindActions(filtered);
}

function bindActions(incidents) {
    const find = id => incidents.find(x => x.id == id);
    rootEl.querySelectorAll('[data-edit]').forEach(b => b.onclick = () => openIncForm(find(b.dataset.edit)));
    rootEl.querySelectorAll('[data-del]').forEach(b => b.onclick = () => deleteInc(b.dataset.del));
    rootEl.querySelectorAll('[data-close]').forEach(b => b.onclick = () => quickClose(b.dataset.close));
    rootEl.querySelectorAll('[data-addaddr]').forEach(b => b.onclick = () => addAddress(b.dataset.addaddr));
    rootEl.querySelectorAll('[data-unlink]').forEach(b => b.onclick = () => unlinkAddress(b.dataset.unlink));
    rootEl.querySelectorAll('[data-parte]').forEach(b => b.onclick = () => generateParte(find(b.dataset.parte)));
}

async function openIncForm(inc = null) {
    const values = await openForm({
        title: inc ? `Editar incidencia #${inc.id}` : 'Nueva incidencia',
        submitLabel: inc ? 'Guardar' : 'Crear',
        fields: [
            { name: 'tipo', label: 'Tipo', type: 'select', value: inc?.tipo, required: true, options: store.enums.tipo_incidencia || [] },
            { name: 'descripcion', label: 'Descripcion', type: 'textarea', value: inc?.descripcion, required: true, col: 'full' },
            { name: 'fecha_inicio', label: 'Fecha inicio', type: 'date', value: inc?.fecha_inicio, required: true },
            { name: 'hora_inicio', label: 'Hora inicio', type: 'time', value: inc?.hora_inicio, required: true },
            { name: 'fecha_fin_prevista', label: 'Fecha fin prevista', type: 'date', value: inc?.fecha_fin_prevista },
            { name: 'hora_fin_prevista', label: 'Hora fin prevista', type: 'time', value: inc?.hora_fin_prevista },
            { name: 'fecha_fin', label: 'Fecha fin (real)', type: 'date', value: inc?.fecha_fin },
            { name: 'hora_fin', label: 'Hora fin (real)', type: 'time', value: inc?.hora_fin },
        ],
    });
    if (!values) return;
    try {
        if (inc) await api.put(`/api/incidencias/${inc.id}`, values);
        else await api.post('/api/incidencias', values);
        toast(inc ? 'Incidencia actualizada.' : 'Incidencia creada.');
        reload();
    } catch (e) { toast(e.message, 'error'); }
}

async function quickClose(id) {
    const now = new Date();
    const fecha = now.toISOString().slice(0, 10);
    const hora = now.toTimeString().slice(0, 5);
    try {
        await api.put(`/api/incidencias/${id}`, { fecha_fin: fecha, hora_fin: hora });
        toast('Incidencia cerrada.');
        reload();
    } catch (e) { toast(e.message, 'error'); }
}

async function deleteInc(id) {
    const ok = await confirmDialog({ title: 'Borrar incidencia', message: '¿Seguro? Se desvincularán sus direcciones afectadas.' });
    if (!ok) return;
    try {
        await api.del(`/api/incidencias/${id}`);
        toast('Incidencia borrada.');
        reload();
    } catch (e) { toast(e.message, 'error'); }
}

async function addAddress(incId) {
    const { direcciones } = await api.get('/api/direcciones');
    const values = await openForm({
        title: 'Añadir dirección afectada',
        submitLabel: 'Enlazar',
        fields: [{
            name: 'direccion_suministro_id', label: 'Direccion', type: 'select', required: true,
            options: direcciones.map(d => ({ value: d.id, label: addrLabel(d) })),
        }],
    });
    if (!values) return;
    try {
        await api.post(`/api/incidencias/${incId}/direcciones`, values);
        toast('Dirección enlazada.');
        reload();
    } catch (e) { toast(e.message, 'error'); }
}

async function unlinkAddress(key) {
    const [incId, dirId] = key.split(':');
    try {
        await api.del(`/api/incidencias/${incId}/direcciones/${dirId}`);
        toast('Dirección desvinculada.');
        reload();
    } catch (e) { toast(e.message, 'error'); }
}

async function generateParte(inc) {
    // Pre-fill with the incident and its first affected address, if any.
    const firstAddr = inc.addresses[0]?.id ?? null;
    const values = await openForm({
        title: `Generar parte para incidencia #${inc.id}`,
        submitLabel: 'Crear parte',
        fields: [
            { name: 'descripcion', label: 'Descripcion', type: 'textarea', required: true, col: 'full',
              value: `Actuación por incidencia #${inc.id} (${humanize(inc.tipo)})` },
            { name: 'estado', label: 'Estado', type: 'select', value: 'Abierto', required: true, options: store.enums.estado_parte || [] },
            { name: 'direccion_suministro_id', label: 'Direccion', type: 'select', value: firstAddr,
              options: inc.addresses.map(a => ({ value: a.id, label: addrLabel(a) })) },
        ],
    });
    if (!values) return;
    try {
        await api.post('/api/partes', { ...values, incidencia_id: inc.id });
        toast('Parte de trabajo creado.');
        reload();
    } catch (e) { toast(e.message, 'error'); }
}

async function load(root) {
    rootEl = root;
    root.innerHTML = `
        ${sectionHeader('Incidencias', `
            <select id="inc-filter" class="field-input !w-44">
                <option value="all" ${filterActive === 'all' ? 'selected' : ''}>Todas</option>
                <option value="active" ${filterActive === 'active' ? 'selected' : ''}>Solo activas</option>
                <option value="closed" ${filterActive === 'closed' ? 'selected' : ''}>Solo resueltas</option>
            </select>
            <button id="inc-new" class="btn btn-primary">+ Nueva incidencia</button>
        `)}
        <p id="inc-stats" class="text-sm text-gray-500"></p>
        <div id="inc-list" class="space-y-4"></div>`;

    root.querySelector('#inc-filter').onchange = (e) => { filterActive = e.target.value; reload(); };
    root.querySelector('#inc-new').onclick = () => openIncForm();

    await reload();
}

export default { load };
