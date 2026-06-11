// Facturacion — recibos (with filter + marcar pagado) and expedientes de corte.
import { api } from '../api.js';
import { store } from '../store.js';
import { openForm } from '../forms.js';
import {
    sectionHeader, badge, fmtDate, fmtMoney, esc, emptyRow, humanize,
    toast, confirmDialog, contratoLabel,
} from '../ui.js';

let rootEl = null;
let filterEstado = '';

async function contratoOptions() {
    const { contratos } = await api.get('/api/contratos');
    return contratos.map(c => ({ value: c.id, label: contratoLabel(c) }));
}

async function reciboOptions() {
    const { recibos } = await api.get('/api/recibos');
    return recibos.map(r => ({ value: r.id, label: `${r.numero_contrato} · ${r.periodo} · ${fmtMoney(r.importe)}` }));
}

async function reloadRecibos() {
    const url = '/api/recibos' + (filterEstado ? `?estado=${encodeURIComponent(filterEstado)}` : '');
    const { recibos } = await api.get(url);
    const rows = recibos.length ? recibos.map(r => `
        <tr>
            <td class="font-mono text-xs">${esc(r.numero_contrato)}</td>
            <td>${esc(r.nombre)} ${esc(r.apellidos)}</td>
            <td>${esc(r.periodo)}</td>
            <td class="text-right font-medium">${fmtMoney(r.importe)}</td>
            <td>${badge(r.estado)}</td>
            <td class="text-xs text-gray-500">${esc(humanize(r.forma_pago))}</td>
            <td class="text-gray-500">${fmtDate(r.fecha_vencimiento)}</td>
            <td class="text-right whitespace-nowrap">
                ${r.estado !== 'Pagado' ? `<button class="btn btn-ghost btn-sm text-green-600" data-pay="${r.id}">Marcar pagado</button>` : ''}
                <button class="btn btn-ghost btn-sm" data-edit="${r.id}">Editar</button>
                <button class="btn btn-ghost btn-sm text-red-500" data-del="${r.id}">Borrar</button>
            </td>
        </tr>`).join('') : emptyRow(8, 'No hay recibos.');
    rootEl.querySelector('#rc-tbody').innerHTML = rows;
    rootEl.querySelectorAll('[data-pay]').forEach(b => b.onclick = () => marcarPagado(b.dataset.pay));
    rootEl.querySelectorAll('#rc-tbody [data-edit]').forEach(b => b.onclick = () => openReciboForm(recibos.find(x => x.id == b.dataset.edit)));
    rootEl.querySelectorAll('#rc-tbody [data-del]').forEach(b => b.onclick = () => deleteRecibo(b.dataset.del));
}

async function reloadExpedientes() {
    const { expedientes } = await api.get('/api/expedientes');
    const rows = expedientes.length ? expedientes.map(e => `
        <tr>
            <td class="font-mono text-xs">${esc(e.numero_contrato)}</td>
            <td>${esc(e.nombre)} ${esc(e.apellidos)}</td>
            <td>${badge(e.estado)}</td>
            <td class="text-gray-500">${fmtDate(e.fecha_apertura)}</td>
            <td class="text-gray-500">${fmtDate(e.fecha_corte)}</td>
            <td class="text-right font-medium">${fmtMoney(e.importe_deuda)}</td>
            <td class="text-right whitespace-nowrap">
                <button class="btn btn-ghost btn-sm" data-edit="${e.id}">Editar</button>
                <button class="btn btn-ghost btn-sm text-red-500" data-del="${e.id}">Borrar</button>
            </td>
        </tr>`).join('') : emptyRow(7, 'No hay expedientes.');
    rootEl.querySelector('#ex-tbody').innerHTML = rows;
    rootEl.querySelectorAll('#ex-tbody [data-edit]').forEach(b => b.onclick = () => openExpedienteForm(expedientes.find(x => x.id == b.dataset.edit)));
    rootEl.querySelectorAll('#ex-tbody [data-del]').forEach(b => b.onclick = () => deleteExpediente(b.dataset.del));
}

// ─── Recibos CRUD ───────────────────────────────────────

async function openReciboForm(r = null) {
    const contratos = await contratoOptions();
    const values = await openForm({
        title: r ? `Editar recibo #${r.id}` : 'Nuevo recibo',
        submitLabel: r ? 'Guardar' : 'Crear',
        fields: [
            { name: 'contrato_id', label: 'Contrato', type: 'select', value: r?.contrato_id, required: true, options: contratos },
            { name: 'periodo', label: 'Periodo', type: 'text', value: r?.periodo, required: true, placeholder: '2026-T1' },
            { name: 'importe', label: 'Importe (€)', type: 'number', step: '0.01', value: r?.importe, required: true },
            { name: 'estado', label: 'Estado', type: 'select', value: r?.estado || 'Pendiente', required: true, options: store.enums.estado_recibo || [] },
            { name: 'forma_pago', label: 'Forma de pago', type: 'select', value: r?.forma_pago || 'Domiciliado', required: true, options: store.enums.forma_pago || [] },
            { name: 'fecha_emision', label: 'Fecha emision', type: 'date', value: r?.fecha_emision, required: true },
            { name: 'fecha_vencimiento', label: 'Fecha vencimiento', type: 'date', value: r?.fecha_vencimiento, required: true },
        ],
    });
    if (!values) return;
    try {
        if (r) await api.put(`/api/recibos/${r.id}`, values);
        else await api.post('/api/recibos', values);
        toast(r ? 'Recibo actualizado.' : 'Recibo creado.');
        reloadRecibos();
    } catch (e) { toast(e.message, 'error'); }
}

async function marcarPagado(id) {
    try {
        await api.post(`/api/recibos/${id}/marcar-pagado`);
        toast('Recibo marcado como pagado.');
        reloadRecibos();
    } catch (e) { toast(e.message, 'error'); }
}

async function deleteRecibo(id) {
    const ok = await confirmDialog({ title: 'Borrar recibo', message: '¿Seguro que quieres borrar este recibo?' });
    if (!ok) return;
    try {
        await api.del(`/api/recibos/${id}`);
        toast('Recibo borrado.');
        reloadRecibos();
    } catch (e) { toast(e.message, 'error'); }
}

// ─── Expedientes CRUD ───────────────────────────────────

async function openExpedienteForm(ex = null) {
    const [contratos, recibos] = await Promise.all([contratoOptions(), reciboOptions()]);
    const values = await openForm({
        title: ex ? `Editar expediente #${ex.id}` : 'Nuevo expediente de corte',
        submitLabel: ex ? 'Guardar' : 'Crear',
        fields: [
            { name: 'contrato_id', label: 'Contrato', type: 'select', value: ex?.contrato_id, required: true, options: contratos },
            { name: 'recibo_id', label: 'Recibo asociado', type: 'select', value: ex?.recibo_id, options: recibos },
            { name: 'estado', label: 'Estado', type: 'select', value: ex?.estado || 'Pendiente', required: true, options: store.enums.estado_expediente || [] },
            { name: 'importe_deuda', label: 'Deuda (€)', type: 'number', step: '0.01', value: ex?.importe_deuda },
            { name: 'fecha_apertura', label: 'Fecha apertura', type: 'date', value: ex?.fecha_apertura, required: true },
            { name: 'fecha_corte', label: 'Fecha corte', type: 'date', value: ex?.fecha_corte },
        ],
    });
    if (!values) return;
    try {
        if (ex) await api.put(`/api/expedientes/${ex.id}`, values);
        else await api.post('/api/expedientes', values);
        toast(ex ? 'Expediente actualizado.' : 'Expediente creado.');
        reloadExpedientes();
    } catch (e) { toast(e.message, 'error'); }
}

async function deleteExpediente(id) {
    const ok = await confirmDialog({ title: 'Borrar expediente', message: '¿Seguro que quieres borrar este expediente?' });
    if (!ok) return;
    try {
        await api.del(`/api/expedientes/${id}`);
        toast('Expediente borrado.');
        reloadExpedientes();
    } catch (e) { toast(e.message, 'error'); }
}

async function load(root) {
    rootEl = root;
    const estados = store.enums.estado_recibo || [];
    root.innerHTML = `
        ${sectionHeader('Recibos', `
            <select id="rc-filter" class="field-input !w-40">
                <option value="">Todos los estados</option>
                ${estados.map(e => `<option value="${e}" ${e === filterEstado ? 'selected' : ''}>${esc(humanize(e))}</option>`).join('')}
            </select>
            <button id="rc-new" class="btn btn-primary">+ Nuevo recibo</button>
        `)}
        <div class="card overflow-hidden">
            <div class="overflow-x-auto">
                <table class="data-table">
                    <thead><tr>
                        <th>Contrato</th><th>Abonado</th><th>Periodo</th><th class="text-right">Importe</th>
                        <th>Estado</th><th>Forma pago</th><th>Vencimiento</th><th class="text-right">Acciones</th>
                    </tr></thead>
                    <tbody id="rc-tbody"></tbody>
                </table>
            </div>
        </div>

        <div class="pt-2">
            ${sectionHeader('Expedientes de Corte', `<button id="ex-new" class="btn btn-primary">+ Nuevo expediente</button>`)}
            <div class="card overflow-hidden">
                <div class="overflow-x-auto">
                    <table class="data-table">
                        <thead><tr>
                            <th>Contrato</th><th>Abonado</th><th>Estado</th><th>Apertura</th>
                            <th>Corte</th><th class="text-right">Deuda</th><th class="text-right">Acciones</th>
                        </tr></thead>
                        <tbody id="ex-tbody"></tbody>
                    </table>
                </div>
            </div>
        </div>`;

    root.querySelector('#rc-filter').onchange = (e) => { filterEstado = e.target.value; reloadRecibos(); };
    root.querySelector('#rc-new').onclick = () => openReciboForm();
    root.querySelector('#ex-new').onclick = () => openExpedienteForm();

    await Promise.all([reloadRecibos(), reloadExpedientes()]);
}

export default { load };
