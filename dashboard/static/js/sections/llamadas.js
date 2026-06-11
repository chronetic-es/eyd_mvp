// Llamadas — registry with edit/delete + search.
import { api } from '../api.js';
import { store } from '../store.js';
import { openForm } from '../forms.js';
import {
    sectionHeader, badge, fmtDateTime, esc, emptyRow,
    toast, confirmDialog,
} from '../ui.js';

let rootEl = null;
let searchTerm = '';

async function reload() {
    const url = '/api/llamadas' + (searchTerm ? `?search=${encodeURIComponent(searchTerm)}` : '');
    const { llamadas } = await api.get(url);

    const rows = llamadas.length ? llamadas.map(c => `
        <tr>
            <td class="whitespace-nowrap text-gray-500">${fmtDateTime(c.fecha_inicio)}</td>
            <td class="font-mono text-xs">${esc(c.telefono)}</td>
            <td>${c.nombre ? esc(c.nombre + ' ' + c.apellidos) : '<span class="text-gray-400">Desconocido</span>'}</td>
            <td>${badge(c.motivo_detectado)}</td>
            <td>${badge(c.estado)}</td>
            <td>${c.human_handoff ? '<span class="badge bg-red-100 text-red-700">Si</span>' : '<span class="text-gray-400 text-xs">No</span>'}</td>
            <td class="text-xs text-gray-500 max-w-xs truncate" title="${esc(c.resumen_ia || '')}">${esc(c.resumen_ia || '—')}</td>
            <td class="text-right whitespace-nowrap">
                <button class="btn btn-ghost btn-sm" data-edit="${c.id}">Editar</button>
                <button class="btn btn-ghost btn-sm text-red-500" data-del="${c.id}">Borrar</button>
            </td>
        </tr>`).join('') : emptyRow(8, 'No hay llamadas registradas.');

    rootEl.querySelector('#ll-tbody').innerHTML = rows;
    bindRowActions(llamadas);
}

function bindRowActions(llamadas) {
    rootEl.querySelectorAll('[data-edit]').forEach(b => {
        b.onclick = () => editLlamada(llamadas.find(x => x.id == b.dataset.edit));
    });
    rootEl.querySelectorAll('[data-del]').forEach(b => {
        b.onclick = () => deleteLlamada(b.dataset.del);
    });
}

async function editLlamada(c) {
    const values = await openForm({
        title: `Editar llamada #${c.id}`,
        fields: [
            { name: 'telefono', label: 'Telefono', type: 'text', value: c.telefono, required: true },
            { name: 'motivo_detectado', label: 'Motivo', type: 'select', value: c.motivo_detectado, options: store.enums.motivo_llamada || [] },
            { name: 'estado', label: 'Estado', type: 'select', value: c.estado, required: true, options: store.enums.estado_llamada || [] },
            { name: 'human_handoff', label: 'Transferida a humano', type: 'checkbox', value: c.human_handoff },
            { name: 'resumen_ia', label: 'Resumen', type: 'textarea', value: c.resumen_ia, col: 'full' },
        ],
    });
    if (!values) return;
    try {
        await api.put(`/api/llamadas/${c.id}`, values);
        toast('Llamada actualizada.');
        reload();
    } catch (e) { toast(e.message, 'error'); }
}

async function deleteLlamada(id) {
    const ok = await confirmDialog({ title: 'Borrar llamada', message: '¿Seguro que quieres borrar este registro de llamada?' });
    if (!ok) return;
    try {
        await api.del(`/api/llamadas/${id}`);
        toast('Llamada borrada.');
        reload();
    } catch (e) { toast(e.message, 'error'); }
}

async function load(root) {
    rootEl = root;
    root.innerHTML = `
        ${sectionHeader('Registro de Llamadas', `
            <input id="ll-search" type="search" placeholder="Buscar telefono, nombre, resumen…"
                   class="field-input !w-64" value="${esc(searchTerm)}">
        `)}
        <div class="card overflow-hidden">
            <div class="overflow-x-auto">
                <table class="data-table">
                    <thead><tr>
                        <th>Fecha</th><th>Telefono</th><th>Abonado</th><th>Motivo</th>
                        <th>Estado</th><th>Handoff</th><th>Resumen</th><th class="text-right">Acciones</th>
                    </tr></thead>
                    <tbody id="ll-tbody"></tbody>
                </table>
            </div>
        </div>`;

    const search = root.querySelector('#ll-search');
    let t;
    search.oninput = () => {
        clearTimeout(t);
        t = setTimeout(() => { searchTerm = search.value.trim(); reload(); }, 300);
    };

    await reload();
}

export default { load };
