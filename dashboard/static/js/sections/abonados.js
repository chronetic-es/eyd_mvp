// Abonados — search + CRUD, a 360 detail panel (contratos→contadores/recibos/
// expedientes + llamadas), and a direcciones manager.
import { api } from '../api.js';
import { store } from '../store.js';
import { openForm } from '../forms.js';
import {
    sectionHeader, badge, fmtDate, fmtMoney, esc, emptyRow, humanize,
    toast, confirmDialog, openModal, closeModal, addrLabel,
} from '../ui.js';

let rootEl = null;
let searchTerm = '';

// ─── List ───────────────────────────────────────────────

async function reload() {
    const url = '/api/abonados' + (searchTerm ? `?search=${encodeURIComponent(searchTerm)}` : '');
    const { abonados } = await api.get(url);
    const rows = abonados.length ? abonados.map(a => `
        <tr>
            <td class="font-mono text-xs">${esc(a.nif)}</td>
            <td class="font-medium">${esc(a.nombre)} ${esc(a.apellidos)}</td>
            <td class="font-mono text-xs">${esc(a.telefono)}</td>
            <td class="text-center">${a.num_contratos}</td>
            <td class="text-right whitespace-nowrap">
                <button class="btn btn-ghost btn-sm text-eyd-700" data-view="${a.id}">Ver ficha</button>
                <button class="btn btn-ghost btn-sm" data-edit="${a.id}">Editar</button>
                <button class="btn btn-ghost btn-sm text-red-500" data-del="${a.id}">Borrar</button>
            </td>
        </tr>`).join('') : emptyRow(5, 'No hay abonados.');
    rootEl.querySelector('#ab-tbody').innerHTML = rows;
    rootEl.querySelectorAll('[data-view]').forEach(b => b.onclick = () => open360(b.dataset.view));
    rootEl.querySelectorAll('[data-edit]').forEach(b => b.onclick = () => openAbonadoForm(abonados.find(x => x.id == b.dataset.edit)));
    rootEl.querySelectorAll('[data-del]').forEach(b => b.onclick = () => deleteAbonado(b.dataset.del));
}

async function openAbonadoForm(a = null) {
    const values = await openForm({
        title: a ? 'Editar abonado' : 'Nuevo abonado',
        submitLabel: a ? 'Guardar' : 'Crear',
        fields: [
            { name: 'nombre', label: 'Nombre', type: 'text', value: a?.nombre, required: true },
            { name: 'apellidos', label: 'Apellidos', type: 'text', value: a?.apellidos, required: true },
            { name: 'nif', label: 'NIF', type: 'text', value: a?.nif, required: true },
            { name: 'telefono', label: 'Telefono', type: 'text', value: a?.telefono, required: true },
            { name: 'dir_fiscal', label: 'Direccion fiscal', type: 'text', value: a?.dir_fiscal, required: true, col: 'full' },
        ],
        validateFn: (v) => {
            const digits = (v.telefono || '').replace(/\D/g, '');
            if (digits.length < 7) return 'El telefono no parece valido.';
            if ((v.nif || '').length < 8) return 'El NIF debe tener al menos 8 caracteres.';
            return null;
        },
    });
    if (!values) return;
    try {
        if (a) await api.put(`/api/abonados/${a.id}`, values);
        else await api.post('/api/abonados', values);
        toast(a ? 'Abonado actualizado.' : 'Abonado creado.');
        reload();
    } catch (e) { toast(e.message, 'error'); }
}

async function deleteAbonado(id) {
    const ok = await confirmDialog({ title: 'Borrar abonado', message: '¿Seguro? No se podrá si tiene contratos asociados.' });
    if (!ok) return;
    try {
        await api.del(`/api/abonados/${id}`);
        toast('Abonado borrado.');
        reload();
    } catch (e) { toast(e.message, 'error'); }
}

// ─── 360 detail panel ───────────────────────────────────

async function open360(id) {
    let data;
    try { data = await api.get(`/api/abonados/${id}`); }
    catch (e) { toast(e.message, 'error'); return; }

    openModal((box) => {
        const a = data.abonado;
        box.innerHTML = `
            <div class="px-6 py-4 border-b flex items-start justify-between">
                <div>
                    <h3 class="text-lg font-semibold text-gray-800">${esc(a.nombre)} ${esc(a.apellidos)}</h3>
                    <p class="text-xs text-gray-500 mt-0.5">NIF ${esc(a.nif)} · Tel ${esc(a.telefono)}</p>
                    <p class="text-xs text-gray-400">${esc(a.dir_fiscal)}</p>
                </div>
                <button class="btn btn-ghost" data-close>✕</button>
            </div>
            <div class="px-6 py-5 max-h-[70vh] overflow-y-auto space-y-5">
                <div class="flex items-center justify-between">
                    <h4 class="text-sm font-semibold text-gray-700">Contratos (${data.contratos.length})</h4>
                    <button class="btn btn-primary btn-sm" data-newcontrato>+ Nuevo contrato</button>
                </div>
                <div class="space-y-3">${data.contratos.map(contratoCard).join('') || '<p class="text-sm text-gray-400">Sin contratos.</p>'}</div>

                <div>
                    <h4 class="text-sm font-semibold text-gray-700 mb-2">Llamadas (${data.llamadas.length})</h4>
                    ${data.llamadas.length ? `<div class="card overflow-hidden"><table class="data-table"><tbody>
                        ${data.llamadas.map(l => `<tr>
                            <td class="text-gray-500 text-xs">${fmtDate(l.fecha_inicio)}</td>
                            <td>${badge(l.motivo_detectado)}</td>
                            <td>${badge(l.estado)}</td>
                            <td class="text-xs text-gray-500">${esc(l.resumen_ia || '')}</td>
                        </tr>`).join('')}
                    </tbody></table></div>` : '<p class="text-sm text-gray-400">Sin llamadas.</p>'}
                </div>
            </div>`;

        box.querySelector('[data-close]').onclick = closeModal;
        box.querySelector('[data-newcontrato]').onclick = () => contratoForm(id, null);
        box.querySelectorAll('[data-editcontrato]').forEach(b => b.onclick = () => {
            const c = data.contratos.find(x => x.id == b.dataset.editcontrato); contratoForm(id, c);
        });
        box.querySelectorAll('[data-delcontrato]').forEach(b => b.onclick = () => delContrato(id, b.dataset.delcontrato));
        box.querySelectorAll('[data-newcontador]').forEach(b => b.onclick = () => contadorForm(id, b.dataset.newcontador, null));
        box.querySelectorAll('[data-editcontador]').forEach(b => {
            const [cid] = b.dataset.editcontador.split(':');
            b.onclick = () => {
                const contrato = data.contratos.find(x => x.id == cid);
                const cont = contrato.contadores.find(z => z.id == b.dataset.editcontador.split(':')[1]);
                contadorForm(id, cid, cont);
            };
        });
        box.querySelectorAll('[data-delcontador]').forEach(b => b.onclick = () => delContador(id, b.dataset.delcontador));
    }, { wide: true });
}

function contratoCard(c) {
    const contadores = c.contadores.map(ct => `
        <tr>
            <td class="font-mono text-xs">${esc(ct.num_serie)}</td>
            <td class="text-right">${Number(ct.lectura_m3).toFixed(2)} m³</td>
            <td class="text-gray-500 text-xs">${fmtDate(ct.fecha_lectura)}</td>
            <td class="text-right">
                <button class="btn btn-ghost btn-sm" data-editcontador="${c.id}:${ct.id}">✎</button>
                <button class="btn btn-ghost btn-sm text-red-500" data-delcontador="${ct.id}">✕</button>
            </td>
        </tr>`).join('') || emptyRow(4, 'Sin contadores.');

    const recibos = c.recibos.map(r =>
        `<span class="inline-flex items-center gap-1 text-xs mr-1 mb-1">${esc(r.periodo)} ${badge(r.estado)} ${fmtMoney(r.importe)}</span>`
    ).join('') || '<span class="text-xs text-gray-400">Sin recibos</span>';

    const expedientes = c.expedientes.map(e =>
        `<span class="inline-flex items-center gap-1 text-xs mr-1 mb-1">Exp.#${e.id} ${badge(e.estado)} ${fmtMoney(e.importe_deuda)}</span>`
    ).join('') || '<span class="text-xs text-gray-400">Sin expedientes</span>';

    return `<div class="border rounded-xl p-4 bg-gray-50/60">
        <div class="flex items-start justify-between flex-wrap gap-2">
            <div class="flex items-center gap-2">
                <span class="font-mono text-sm font-medium">${esc(c.numero_contrato)}</span>
                ${badge(c.estado)}
            </div>
            <div class="flex gap-1">
                <button class="btn btn-ghost btn-sm" data-editcontrato="${c.id}">Editar</button>
                <button class="btn btn-ghost btn-sm text-red-500" data-delcontrato="${c.id}">Borrar</button>
            </div>
        </div>
        <p class="text-xs text-gray-500 mt-1">${esc(addrLabel(c))} · Alta ${fmtDate(c.fecha_alta)}${c.fecha_baja ? ' · Baja ' + fmtDate(c.fecha_baja) : ''}</p>
        <div class="mt-3">
            <div class="flex items-center justify-between mb-1">
                <span class="text-xs font-semibold text-gray-600">Contadores</span>
                <button class="btn btn-ghost btn-sm" data-newcontador="${c.id}">+ Lectura</button>
            </div>
            <div class="card overflow-hidden"><table class="data-table"><tbody>${contadores}</tbody></table></div>
        </div>
        <div class="mt-2 text-xs"><span class="text-gray-400">Recibos:</span> ${recibos}</div>
        <div class="mt-1 text-xs"><span class="text-gray-400">Expedientes:</span> ${expedientes}</div>
    </div>`;
}

// ─── Nested forms (reopen 360 afterwards) ───────────────

async function direccionOptions() {
    const { direcciones } = await api.get('/api/direcciones');
    return direcciones.map(d => ({ value: d.id, label: addrLabel(d) }));
}

async function contratoForm(abonadoId, c) {
    const dirs = await direccionOptions();
    const values = await openForm({
        title: c ? `Editar contrato ${c.numero_contrato}` : 'Nuevo contrato',
        submitLabel: c ? 'Guardar' : 'Crear',
        fields: [
            { name: 'numero_contrato', label: 'Numero de contrato', type: 'text', value: c?.numero_contrato, required: true, placeholder: 'CTR-2026-010' },
            { name: 'direccion_suministro_id', label: 'Direccion de suministro', type: 'select', value: c?.direccion_id, required: true, options: dirs, col: 'full' },
            { name: 'estado', label: 'Estado', type: 'select', value: c?.estado || 'Activo', required: true, options: store.enums.estado_contrato || [] },
            { name: 'fecha_alta', label: 'Fecha alta', type: 'date', value: c?.fecha_alta, required: true },
            { name: 'fecha_baja', label: 'Fecha baja', type: 'date', value: c?.fecha_baja },
        ],
        validateFn: (v) => (v.fecha_baja && v.fecha_alta && v.fecha_baja < v.fecha_alta)
            ? 'La fecha de baja no puede ser anterior al alta.' : null,
    });
    if (values) {
        try {
            if (c) await api.put(`/api/contratos/${c.id}`, values);
            else await api.post('/api/contratos', { ...values, entidad_id: Number(abonadoId) });
            toast(c ? 'Contrato actualizado.' : 'Contrato creado.');
        } catch (e) { toast(e.message, 'error'); }
    }
    open360(abonadoId);
}

async function delContrato(abonadoId, contratoId) {
    const ok = await confirmDialog({ title: 'Borrar contrato', message: '¿Seguro? No se podrá si tiene recibos, contadores o expedientes.' });
    if (ok) {
        try { await api.del(`/api/contratos/${contratoId}`); toast('Contrato borrado.'); }
        catch (e) { toast(e.message, 'error'); }
    }
    open360(abonadoId);
}

async function contadorForm(abonadoId, contratoId, ct) {
    const values = await openForm({
        title: ct ? 'Editar lectura' : 'Nueva lectura de contador',
        submitLabel: ct ? 'Guardar' : 'Añadir',
        fields: [
            { name: 'num_serie', label: 'N. serie', type: 'text', value: ct?.num_serie, required: true },
            { name: 'lectura_m3', label: 'Lectura (m³)', type: 'number', step: '0.001', value: ct?.lectura_m3 },
            { name: 'fecha_lectura', label: 'Fecha lectura', type: 'date', value: ct?.fecha_lectura, required: true },
            { name: 'fecha_alta', label: 'Fecha alta', type: 'date', value: ct?.fecha_alta, required: true },
            { name: 'fecha_baja', label: 'Fecha baja', type: 'date', value: ct?.fecha_baja },
        ],
    });
    if (values) {
        try {
            if (ct) await api.put(`/api/contadores/${ct.id}`, values);
            else await api.post('/api/contadores', { ...values, contrato_id: Number(contratoId) });
            toast(ct ? 'Lectura actualizada.' : 'Lectura añadida.');
        } catch (e) { toast(e.message, 'error'); }
    }
    open360(abonadoId);
}

async function delContador(abonadoId, contadorId) {
    const ok = await confirmDialog({ title: 'Borrar lectura', message: '¿Borrar esta lectura de contador?' });
    if (ok) {
        try { await api.del(`/api/contadores/${contadorId}`); toast('Lectura borrada.'); }
        catch (e) { toast(e.message, 'error'); }
    }
    open360(abonadoId);
}

// ─── Direcciones manager ────────────────────────────────

async function openDireccionesManager() {
    let data;
    try { data = await api.get('/api/direcciones'); }
    catch (e) { toast(e.message, 'error'); return; }

    openModal((box) => {
        box.innerHTML = `
            <div class="px-6 py-4 border-b flex items-center justify-between">
                <h3 class="text-lg font-semibold text-gray-800">Direcciones de suministro</h3>
                <div class="flex gap-2">
                    <button class="btn btn-primary btn-sm" data-newdir>+ Nueva</button>
                    <button class="btn btn-ghost" data-close>✕</button>
                </div>
            </div>
            <div class="px-6 py-4 max-h-[70vh] overflow-y-auto">
                <div class="card overflow-hidden"><table class="data-table">
                    <thead><tr><th>Direccion</th><th>C.P.</th><th>Municipio</th><th class="text-right">Acciones</th></tr></thead>
                    <tbody>${data.direcciones.length ? data.direcciones.map(d => `
                        <tr>
                            <td>${esc(addrLabel({ ...d, municipio: '' }))}</td>
                            <td class="text-xs">${esc(d.cod_postal)}</td>
                            <td>${esc(d.municipio)}</td>
                            <td class="text-right whitespace-nowrap">
                                <button class="btn btn-ghost btn-sm" data-editdir="${d.id}">Editar</button>
                                <button class="btn btn-ghost btn-sm text-red-500" data-deldir="${d.id}">Borrar</button>
                            </td>
                        </tr>`).join('') : emptyRow(4, 'Sin direcciones.')}
                    </tbody>
                </table></div>
            </div>`;
        box.querySelector('[data-close]').onclick = closeModal;
        box.querySelector('[data-newdir]').onclick = () => direccionForm(null);
        box.querySelectorAll('[data-editdir]').forEach(b => b.onclick = () => direccionForm(data.direcciones.find(x => x.id == b.dataset.editdir)));
        box.querySelectorAll('[data-deldir]').forEach(b => b.onclick = () => delDireccion(b.dataset.deldir));
    }, { wide: true });
}

async function direccionForm(d) {
    const values = await openForm({
        title: d ? 'Editar direccion' : 'Nueva direccion',
        submitLabel: d ? 'Guardar' : 'Crear',
        fields: [
            { name: 'calle', label: 'Calle', type: 'text', value: d?.calle, required: true, col: 'full' },
            { name: 'numero', label: 'Numero', type: 'text', value: d?.numero },
            { name: 'portal', label: 'Portal', type: 'text', value: d?.portal },
            { name: 'planta', label: 'Planta', type: 'text', value: d?.planta },
            { name: 'letra', label: 'Letra', type: 'text', value: d?.letra },
            { name: 'cod_postal', label: 'Codigo postal', type: 'text', value: d?.cod_postal, required: true },
            { name: 'municipio', label: 'Municipio', type: 'text', value: d?.municipio, required: true },
        ],
    });
    if (values) {
        try {
            if (d) await api.put(`/api/direcciones/${d.id}`, values);
            else await api.post('/api/direcciones', values);
            toast(d ? 'Direccion actualizada.' : 'Direccion creada.');
        } catch (e) { toast(e.message, 'error'); }
    }
    openDireccionesManager();
}

async function delDireccion(id) {
    const ok = await confirmDialog({ title: 'Borrar direccion', message: '¿Seguro? No se podrá si está en uso.' });
    if (ok) {
        try { await api.del(`/api/direcciones/${id}`); toast('Direccion borrada.'); }
        catch (e) { toast(e.message, 'error'); }
    }
    openDireccionesManager();
}

// ─── Section entry ──────────────────────────────────────

async function load(root) {
    rootEl = root;
    root.innerHTML = `
        ${sectionHeader('Abonados', `
            <input id="ab-search" type="search" placeholder="Buscar NIF, nombre, telefono…"
                   class="field-input !w-64" value="${esc(searchTerm)}">
            <button id="ab-dirs" class="btn btn-secondary">Direcciones</button>
            <button id="ab-new" class="btn btn-primary">+ Nuevo abonado</button>
        `)}
        <div class="card overflow-hidden">
            <div class="overflow-x-auto">
                <table class="data-table">
                    <thead><tr>
                        <th>NIF</th><th>Nombre</th><th>Telefono</th><th class="text-center">Contratos</th>
                        <th class="text-right">Acciones</th>
                    </tr></thead>
                    <tbody id="ab-tbody"></tbody>
                </table>
            </div>
        </div>`;

    const search = root.querySelector('#ab-search');
    let t;
    search.oninput = () => { clearTimeout(t); t = setTimeout(() => { searchTerm = search.value.trim(); reload(); }, 300); };
    root.querySelector('#ab-new').onclick = () => openAbonadoForm();
    root.querySelector('#ab-dirs').onclick = () => openDireccionesManager();

    await reload();
}

export default { load };
