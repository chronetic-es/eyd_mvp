// Shared reference data (ENUM values) loaded once at startup.
import { api } from './api.js';

export const store = { enums: {} };

export async function loadEnums() {
    try {
        store.enums = await api.get('/api/meta/enums');
    } catch {
        store.enums = {};
    }
}
