/* Shared opt-in feedback helpers. Django remains authoritative for every action. */
(function () {
    'use strict';
    async function json(response, fallback = 'The request could not be completed.') {
        if (response.redirected) throw new Error('Your session may have expired. Reload and sign in before retrying.');
        let data;
        try { data = await response.json(); } catch (_) {
            throw new Error(response.status === 403 ? 'Permission denied or your session has expired. Reload before retrying.' : fallback);
        }
        if (!response.ok || !data || typeof data !== 'object' || data.error) {
            const error = new Error(data?.error || (response.status === 409 ? 'This record has changed. Reload it before retrying.' : fallback));
            error.field = data?.field;
            throw error;
        }
        return data;
    }
    const pending = new WeakMap();
    function lock(form, label = 'Processing…', activeButton = null) {
        if (pending.has(form)) return false;
        const buttons = [...form.querySelectorAll('button')].map(button => ({button, disabled: button.disabled}));
        pending.set(form, buttons); form.setAttribute('aria-busy', 'true');
        buttons.forEach(({button}) => { button.disabled = true; });
        const button = activeButton || form.querySelector('button[type="submit"],button:not([type])');
        if (button) { button.dataset.actionLabel = button.textContent; button.textContent = label; }
        return true;
    }
    function unlock(form) {
        (pending.get(form) || []).forEach(({button, disabled}) => {
            button.disabled = disabled;
            if (button.dataset.actionLabel) { button.textContent = button.dataset.actionLabel; delete button.dataset.actionLabel; }
        });
        pending.delete(form); form.removeAttribute('aria-busy');
    }
    window.CampusHubActions = {json, lock, unlock};
    document.addEventListener('submit', event => {
        const form = event.target;
        if (!form.matches('[data-action-filter]') || event.defaultPrevented) return;
        if (form.hasAttribute('aria-busy')) { event.preventDefault(); return; }
        form.setAttribute('aria-busy', 'true');
        const status = document.createElement('span'); status.dataset.filterProgress = ''; status.setAttribute('role', 'status');
        status.textContent = 'Updating results…'; form.append(status);
    });
    window.addEventListener('pageshow', () => {
        document.querySelectorAll('[data-action-filter]').forEach(form => {
            form.removeAttribute('aria-busy'); form.querySelector('[data-filter-progress]')?.remove();
        });
    });
})();
