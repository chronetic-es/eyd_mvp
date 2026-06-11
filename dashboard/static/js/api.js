// Thin fetch wrapper with JSON handling and friendly error extraction.

export class ApiError extends Error {
    constructor(message, status) {
        super(message);
        this.status = status;
    }
}

function extractDetail(data, status) {
    if (!data) return `Error ${status}`;
    const d = data.detail;
    if (typeof d === 'string') return d;
    // FastAPI validation errors: list of {loc, msg, ...}
    if (Array.isArray(d)) {
        return d.map(e => {
            const field = Array.isArray(e.loc) ? e.loc[e.loc.length - 1] : '';
            return field ? `${field}: ${e.msg}` : e.msg;
        }).join(' · ');
    }
    return `Error ${status}`;
}

async function request(method, url, body) {
    const opts = { method, headers: {} };
    if (body !== undefined) {
        opts.headers['Content-Type'] = 'application/json';
        opts.body = JSON.stringify(body);
    }
    const res = await fetch(url, opts);
    if (res.status === 204) return null;
    let data = null;
    try { data = await res.json(); } catch { /* no body */ }
    if (!res.ok) {
        throw new ApiError(extractDetail(data, res.status), res.status);
    }
    return data;
}

export const api = {
    get: (url) => request('GET', url),
    post: (url, body) => request('POST', url, body),
    put: (url, body) => request('PUT', url, body),
    del: (url) => request('DELETE', url),
};
