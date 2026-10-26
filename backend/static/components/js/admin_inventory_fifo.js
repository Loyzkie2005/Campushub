// One key per receiving draft: retry a lost response without receiving twice.
document.addEventListener('DOMContentLoaded', () => {
    // Bootstrap handles the backdrop, Escape and focus containment.
    // Initialize independently of receiving: Stock Movements has no receipt form.
    const drawer = document.getElementById('inventoryDetailsDrawer');
    if (drawer) {
        const body = document.getElementById('inventoryDetailsBody');
        let opener = null;
        let viewport = {left: 0, top: 0};
        drawer.addEventListener('show.bs.offcanvas', event => {
            const trigger = event.relatedTarget;
            const content = document.getElementById(trigger?.dataset.inventoryDetail || '');
            if (!(content instanceof HTMLTemplateElement)) { event.preventDefault(); return; }
            opener = trigger;
            viewport = {left: window.scrollX, top: window.scrollY};
            document.getElementById('inventoryDetailsTitle').textContent = trigger.dataset.detailTitle;
            body.replaceChildren(content.content.cloneNode(true));
            body.scrollTop = 0;
        });
        drawer.addEventListener('hidden.bs.offcanvas', () => {
            body.replaceChildren();
            // Avoid Bootstrap's default focus return scrolling a low table row.
            if (opener?.isConnected) opener.focus({preventScroll: true});
            window.scrollTo({...viewport, behavior: 'instant'});
        });
        document.querySelectorAll('button[data-inventory-detail]').forEach(trigger => {
            trigger.addEventListener('click', () => {
                window.bootstrap?.Offcanvas.getOrCreateInstance(drawer).show(trigger);
            });
        });
    }
    const form = document.getElementById('fifoReceiveForm');
    if (!form) return;
    const feedback = document.getElementById('fifoReceiveFeedback');
    let busy = false, previous = '', key = '';
    const storageKey = `campushub.fifo.receiving.${form.dataset.receiver}`;
    try { const draft = JSON.parse(sessionStorage.getItem(storageKey) || 'null'); if (draft) { previous = draft.previous; key = draft.key; } } catch (_) { /* Receiving remains usable when storage is unavailable. */ }
    form.addEventListener('submit', async event => {
        event.preventDefault();
        if (busy || !form.reportValidity()) return;
        const data = new FormData(form), payload = {sku: data.get('sku'), quantity: data.get('quantity'), reference: data.get('reference').trim()};
        const draft = JSON.stringify(payload);
        if (draft !== previous) {
            const bytes = crypto.getRandomValues(new Uint8Array(16));
            bytes[6] = (bytes[6] & 15) | 64; bytes[8] = (bytes[8] & 63) | 128;
            const hex = [...bytes].map(value => value.toString(16).padStart(2, '0')).join('');
            key = `${hex.slice(0,8)}-${hex.slice(8,12)}-${hex.slice(12,16)}-${hex.slice(16,20)}-${hex.slice(20)}`; previous = draft;
        }
        try { sessionStorage.setItem(storageKey, JSON.stringify({previous, key})); } catch (_) { /* Current-page retries still reuse the key. */ }
        busy = true;
        const controls = [...form.querySelectorAll('input, select, button')];
        controls.forEach(input => { input.disabled = true; });
        form.setAttribute('aria-busy', 'true'); feedback.textContent = 'Recording receipt…';
        const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 15000);
        try {
            const response = await fetch(form.action, {method: 'POST', credentials: 'same-origin', signal: controller.signal,
                headers: {'Content-Type': 'application/json', 'X-CSRFToken': data.get('csrfmiddlewaretoken')}, body: JSON.stringify({...payload, key})});
            if (response.redirected || !response.headers.get('Content-Type')?.includes('application/json')) throw new Error('Session expired. Reload and sign in before receiving stock.');
            const result = await response.json();
            if (!response.ok) throw new Error(result.error || 'Unable to record this receipt.');
            try { sessionStorage.removeItem(storageKey); } catch (_) { /* No persisted key to clear. */ }
            feedback.textContent = `${result.message} ${result.batch}`;
            window.setTimeout(() => window.location.reload(), 1000);
        } catch (error) {
            feedback.textContent = error.name === 'AbortError' ? 'The response timed out. Retry the same draft safely; it will not receive stock twice.' : error.message;
            busy = false; controls.forEach(input => { input.disabled = false; }); form.removeAttribute('aria-busy');
        } finally { clearTimeout(timer); }
    });
});
