// Partes de trabajo — CRUD with status filter. numero_parte auto-generated server-side.
import { api } from '../api.js';
import { store } from '../store.js';
import { openForm } from '../forms.js';
import {
    sectionHeader, badge, fmtDate, esc, emptyRow, humanize,
    toast, confirmDialog, addrLabel,
} from '../ui.js';

let rootEl = null;
let filterEstado = '';

async function fkOptions() {
    const [dirs, incs] = await Promise.all([
        api.get('/api/direcciones'),
        api.get('/api/incidencias'),
    ]);
    return {
        direcciones: dirs.direcciones.map(d => ({ value: d.id, label: addrLabel(d) })),
        incidencias: incs.incidents.map(i => ({ value: i.id, label: `#${i.id} ${humanize(i.tipo)} (${fmtDate(i.fecha_inicio)})` })),
    };
}

async function reload() {
    const url = '/api/partes' + (filterEstado ? `?estado=${encodeURIComponent(filterEstado)}` : '');
    const { partes } = await api.get(url);

    const rows = partes.length ? partes.map(p => {
        const dir = p.calle ? esc(addrLabel(p)) : '—';
        const inc = p.incident_type ? `${badge(p.incident_type)} <span class="text-xs text-gray-400">#${p.incidencia_id}</span>` : '—';
        return `<tr>
            <td class="font-mono text-xs font-medium">${esc(p.numero_parte)}</td>
            <td>${badge(p.estado)}</td>
            <td class="text-gray-500">${fmtDate(p.fecha)}</td>
            <td class="text-sm">${dir}</td>
            <td>${inc}</td>
            <td class="text-xs text-gray-500 max-w-xs truncate" title="${esc(p.descripcion || '')}">${esc(p.descripcion || '—')}</td>
            <td class="text-right whitespace-nowrap">
                ${p.estado !== 'Cerrado' ? `<button class="btn btn-ghost btn-sm" data-close="${p.id}">Cerrar</button>` : ''}
                <button class="btn btn-ghost btn-sm" data-edit="${p.id}">Editar</button>
                <button class="btn btn-ghost btn-sm text-red-500" data-del="${p.id}">Borrar</button>
            </td>
        </tr>`;
    }).join('') : emptyRow(7, 'No hay partes de trabajo.');

    rootEl.querySelector('#pt-tbody').innerHTML = rows;

    rootEl.querySelectorAll('[data-edit]').forEach(b => b.onclick = () => openParteForm(partes.find(x => x.id == b.dataset.edit)));
    rootEl.querySelectorAll('[data-close]').forEach(b => b.onclick = () => quickClose(b.dataset.close));
    rootEl.querySelectorAll('[data-del]').forEach(b => b.onclick = () => deleteParte(b.dataset.del));
}

async function openParteForm(p = null) {
    const fk = await fkOptions();
    const values = await openForm({
        title: p ? `Editar ${p.numero_parte}` : 'Nuevo parte de trabajo',
        submitLabel: p ? 'Guardar' : 'Crear',
        fields: [
            { name: 'descripcion', label: 'Descripcion', type: 'textarea', value: p?.descripcion, required: true, col: 'full' },
            { name: 'estado', label: 'Estado', type: 'select', value: p?.estado || 'Abierto', required: true, options: store.enums.estado_parte || [] },
            { name: 'fecha', label: 'Fecha', type: 'date', value: p?.fecha },
            { name: 'direccion_suministro_id', label: 'Direccion', type: 'select', value: p?.direccion_suministro_id, options: fk.direcciones },
            { name: 'incidencia_id', label: 'Incidencia', type: 'select', value: p?.incidencia_id, options: fk.incidencias },
        ],
    });
    if (!values) return;
    try {
        if (p) await api.put(`/api/partes/${p.id}`, values);
        else await api.post('/api/partes', values);
        toast(p ? 'Parte actualizado.' : 'Parte creado.');
        reload();
    } catch (e) { toast(e.message, 'error'); }
}

async function quickClose(id) {
    try {
        await api.put(`/api/partes/${id}`, { estado: 'Cerrado' });
        toast('Parte cerrado.');
        reload();
    } catch (e) { toast(e.message, 'error'); }
}

async function deleteParte(id) {
    const ok = await confirmDialog({ title: 'Borrar parte', message: '¿Seguro que quieres borrar este parte de trabajo?' });
    if (!ok) return;
    try {
        await api.del(`/api/partes/${id}`);
        toast('Parte borrado.');
        reload();
    } catch (e) { toast(e.message, 'error'); }
}

async function load(root) {
    rootEl = root;
    const estados = store.enums.estado_parte || [];
    root.innerHTML = `
        ${sectionHeader('Partes de Trabajo', `
            <select id="pt-filter" class="field-input !w-40">
                <option value="">Todos los estados</option>
                ${estados.map(e => `<option value="${e}" ${e === filterEstado ? 'selected' : ''}>${esc(humanize(e))}</option>`).join('')}
            </select>
            <button id="pt-new" class="btn btn-primary">+ Nuevo parte</button>
        `)}
        <div class="card overflow-hidden">
            <div class="overflow-x-auto">
                <table class="data-table">
                    <thead><tr>
                        <th>N. Parte</th><th>Estado</th><th>Fecha</th><th>Direccion</th>
                        <th>Incidencia</th><th>Descripcion</th><th class="text-right">Acciones</th>
                    </tr></thead>
                    <tbody id="pt-tbody"></tbody>
                </table>
            </div>
        </div>`;

    root.querySelector('#pt-filter').onchange = (e) => { filterEstado = e.target.value; reload(); };
    root.querySelector('#pt-new').onclick = () => openParteForm();

    await reload();
}

export default { load };
