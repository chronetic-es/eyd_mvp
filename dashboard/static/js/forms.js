// Modal form builder. openForm(config) -> Promise<values|null>.
//
// Field config: { name, label, type, required, value, options, placeholder, step, help, col }
//   type: text | textarea | number | date | time | select | checkbox
//   options (for select): array of strings or {value, label}
//   col: 'full' to span both columns (default: half width)

import { openModal, esc, humanize } from './ui.js';

function renderField(f) {
    const id = `f_${f.name}`;
    const req = f.required ? '<span class="text-red-500">*</span>' : '';
    const span = f.col === 'full' || f.type === 'textarea' ? 'sm:col-span-2' : '';
    let control;

    if (f.type === 'textarea') {
        control = `<textarea id="${id}" name="${f.name}" rows="3" class="field-input"
                    placeholder="${esc(f.placeholder || '')}">${esc(f.value ?? '')}</textarea>`;
    } else if (f.type === 'select') {
        const opts = (f.options || []).map(o => {
            const val = typeof o === 'object' ? o.value : o;
            const lab = typeof o === 'object' ? o.label : humanize(o);
            const sel = String(f.value ?? '') === String(val) ? 'selected' : '';
            return `<option value="${esc(val)}" ${sel}>${esc(lab)}</option>`;
        }).join('');
        const blank = f.required ? '' : `<option value="">— Ninguno —</option>`;
        control = `<select id="${id}" name="${f.name}" class="field-input">${blank}${opts}</select>`;
    } else if (f.type === 'checkbox') {
        const checked = f.value ? 'checked' : '';
        return `<div class="${span} flex items-center gap-2 mt-1">
            <input type="checkbox" id="${id}" name="${f.name}" ${checked} class="w-4 h-4 rounded border-gray-300">
            <label for="${id}" class="text-sm text-gray-700">${esc(f.label)}</label>
        </div>`;
    } else {
        const step = f.type === 'number' && f.step ? `step="${f.step}"` : '';
        control = `<input type="${f.type}" id="${id}" name="${f.name}" ${step}
                    value="${esc(f.value ?? '')}" placeholder="${esc(f.placeholder || '')}" class="field-input">`;
    }

    return `<div class="${span}">
        <label class="field-label" for="${id}">${esc(f.label)} ${req}</label>
        ${control}
        ${f.help ? `<p class="text-[0.7rem] text-gray-400 mt-0.5">${esc(f.help)}</p>` : ''}
        <p class="field-error hidden" data-err="${f.name}"></p>
    </div>`;
}

function collect(fields, box) {
    const values = {};
    for (const f of fields) {
        const el = box.querySelector(`[name="${f.name}"]`);
        if (!el) continue;
        if (f.type === 'checkbox') {
            values[f.name] = el.checked;
        } else if (f.type === 'number') {
            values[f.name] = el.value === '' ? null : Number(el.value);
        } else {
            const v = el.value.trim();
            values[f.name] = v === '' ? null : v;
        }
    }
    return values;
}

function validate(fields, values, box) {
    let ok = true;
    box.querySelectorAll('.field-error').forEach(e => e.classList.add('hidden'));
    for (const f of fields) {
        if (f.required && (values[f.name] == null || values[f.name] === '')) {
            const err = box.querySelector(`[data-err="${f.name}"]`);
            if (err) { err.textContent = 'Campo obligatorio'; err.classList.remove('hidden'); }
            ok = false;
        }
    }
    return ok;
}

/**
 * @param {object} cfg { title, fields, submitLabel, wide, validateFn }
 *   validateFn(values) -> error string | null (custom cross-field validation)
 */
export function openForm({ title, fields, submitLabel = 'Guardar', wide = false, validateFn = null }) {
    return new Promise(resolve => {
        openModal((box, close) => {
            box.innerHTML = `
                <form>
                    <div class="px-6 py-4 border-b">
                        <h3 class="text-lg font-semibold text-gray-800">${esc(title)}</h3>
                    </div>
                    <div class="px-6 py-5 grid grid-cols-1 sm:grid-cols-2 gap-4 max-h-[65vh] overflow-y-auto">
                        ${fields.map(renderField).join('')}
                    </div>
                    <p class="px-6 text-sm text-red-600 hidden" data-form-error></p>
                    <div class="px-6 py-4 border-t flex justify-end gap-2">
                        <button type="button" class="btn btn-secondary" data-act="cancel">Cancelar</button>
                        <button type="submit" class="btn btn-primary">${esc(submitLabel)}</button>
                    </div>
                </form>`;

            const form = box.querySelector('form');
            box.querySelector('[data-act="cancel"]').onclick = () => { close(); resolve(null); };
            form.onsubmit = (e) => {
                e.preventDefault();
                const values = collect(fields, box);
                if (!validate(fields, values, box)) return;
                if (validateFn) {
                    const err = validateFn(values);
                    if (err) {
                        const ef = box.querySelector('[data-form-error]');
                        ef.textContent = err; ef.classList.remove('hidden');
                        return;
                    }
                }
                close();
                resolve(values);
            };
        }, { wide });
    });
}
