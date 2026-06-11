// Shared UI primitives: formatters, badges, toasts, confirm dialog, modal.

// ─── Formatters ─────────────────────────────────────────

export function esc(s) {
    if (s == null) return '';
    return String(s).replace(/[&<>"']/g, c => (
        { '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]
    ));
}

export function fmtDate(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    if (isNaN(d)) return iso;
    return d.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' });
}

export function fmtDateTime(iso) {
    if (!iso) return '—';
    const d = new Date(iso);
    if (isNaN(d)) return iso;
    return d.toLocaleDateString('es-ES', { day: '2-digit', month: '2-digit', year: 'numeric' })
        + ' ' + d.toLocaleTimeString('es-ES', { hour: '2-digit', minute: '2-digit' });
}

export function fmtMoney(val) {
    if (val == null) return '—';
    return Number(val).toFixed(2) + ' €';
}

export function humanize(s) {
    return (s || '').replace(/_/g, ' ');
}

// ─── Badges ─────────────────────────────────────────────

const STATUS_COLORS = {
    'Pagado': 'bg-green-100 text-green-700', 'Completada': 'bg-green-100 text-green-700',
    'Cerrado': 'bg-gray-100 text-gray-600', 'Cerrada': 'bg-gray-100 text-gray-600',
    'Resuelta': 'bg-green-100 text-green-700', 'Activo': 'bg-green-100 text-green-700',
    'Pendiente': 'bg-yellow-100 text-yellow-700',
    'Impagado': 'bg-red-100 text-red-700', 'Devuelto': 'bg-red-100 text-red-700',
    'Escalada': 'bg-amber-100 text-amber-700', 'Abandonada': 'bg-gray-100 text-gray-600',
    'Abierta': 'bg-blue-100 text-blue-700', 'Abierto': 'bg-blue-100 text-blue-700',
    'En_progreso': 'bg-amber-100 text-amber-700', 'En_proceso': 'bg-amber-100 text-amber-700',
    'Notificado': 'bg-orange-100 text-orange-700', 'Ejecutado': 'bg-red-100 text-red-700',
    'Suspendido': 'bg-orange-100 text-orange-700', 'Baja': 'bg-gray-100 text-gray-600',
    'Averia': 'bg-red-100 text-red-700', 'Fuga': 'bg-blue-100 text-blue-700',
    'Corte_programado': 'bg-amber-100 text-amber-700', 'Corte_impago': 'bg-red-100 text-red-700',
};

export function badge(status) {
    if (!status) return '<span class="text-gray-400">—</span>';
    const cls = STATUS_COLORS[status] || 'bg-gray-100 text-gray-600';
    return `<span class="badge ${cls}">${esc(humanize(status))}</span>`;
}

// ─── Toasts ─────────────────────────────────────────────

export function toast(message, type = 'success') {
    const root = document.getElementById('toast-root');
    const el = document.createElement('div');
    el.className = `toast toast-${type}`;
    el.textContent = message;
    root.appendChild(el);
    setTimeout(() => {
        el.style.transition = 'opacity 0.3s, transform 0.3s';
        el.style.opacity = '0';
        el.style.transform = 'translateX(20px)';
        setTimeout(() => el.remove(), 300);
    }, type === 'error' ? 5000 : 3000);
}

// ─── Modal ──────────────────────────────────────────────

let activeModal = null;

export function closeModal() {
    if (activeModal) { activeModal.remove(); activeModal = null; }
}

/**
 * Open a modal. `contentBuilder(box, close)` populates the modal box.
 * Returns the overlay element.
 */
export function openModal(contentBuilder, { wide = false } = {}) {
    closeModal();
    const overlay = document.createElement('div');
    overlay.className = 'modal-overlay';
    const box = document.createElement('div');
    box.className = 'modal-box' + (wide ? ' modal-wide' : '');
    overlay.appendChild(box);
    overlay.addEventListener('mousedown', e => { if (e.target === overlay) closeModal(); });
    document.addEventListener('keydown', function onKey(e) {
        if (e.key === 'Escape') { closeModal(); document.removeEventListener('keydown', onKey); }
    });
    document.getElementById('modal-root').appendChild(overlay);
    activeModal = overlay;
    contentBuilder(box, closeModal);
    return overlay;
}

/** Confirmation dialog. Returns a Promise<boolean>. */
export function confirmDialog({ title = 'Confirmar', message = '', danger = true, okLabel = 'Confirmar' }) {
    return new Promise(resolve => {
        openModal((box, close) => {
            box.innerHTML = `
                <div class="p-6">
                    <h3 class="text-lg font-semibold text-gray-800">${esc(title)}</h3>
                    <p class="mt-2 text-sm text-gray-600">${esc(message)}</p>
                    <div class="mt-6 flex justify-end gap-2">
                        <button class="btn btn-secondary" data-act="cancel">Cancelar</button>
                        <button class="btn ${danger ? 'btn-danger' : 'btn-primary'}" data-act="ok">${esc(okLabel)}</button>
                    </div>
                </div>`;
            box.querySelector('[data-act="cancel"]').onclick = () => { close(); resolve(false); };
            box.querySelector('[data-act="ok"]').onclick = () => { close(); resolve(true); };
        });
    });
}

// ─── Misc helpers ───────────────────────────────────────

export function sectionHeader(title, actionsHtml = '') {
    return `<div class="flex items-center justify-between flex-wrap gap-3 mb-1">
        <h2 class="text-xl font-bold text-gray-800">${esc(title)}</h2>
        <div class="flex items-center gap-2">${actionsHtml}</div>
    </div>`;
}

export function kpiCard(label, value, color = 'text-eyd-800') {
    return `<div class="card p-5">
        <p class="kpi-label">${esc(label)}</p>
        <p class="kpi-value ${color}">${value}</p>
    </div>`;
}

export function emptyRow(cols, msg = 'Sin registros.') {
    return `<tr><td colspan="${cols}" class="px-4 py-8 text-center text-gray-400 text-sm">${esc(msg)}</td></tr>`;
}

// ─── Label builders (for FK dropdowns / display) ────────

export function addrLabel(d) {
    if (!d) return '—';
    let s = d.calle || '';
    if (d.numero) s += ' ' + d.numero;
    const extras = [d.portal && 'P' + d.portal, d.planta && d.planta, d.letra].filter(Boolean).join(' ');
    if (extras) s += ' ' + extras;
    if (d.municipio) s += ', ' + d.municipio;
    return s.trim() || '—';
}

export function contratoLabel(c) {
    const who = (c.nombre || c.apellidos) ? ` — ${c.nombre || ''} ${c.apellidos || ''}`.trimEnd() : '';
    return `${c.numero_contrato}${who}`;
}

export function abonadoLabel(a) {
    return `${a.nombre} ${a.apellidos} (${a.nif})`;
}
