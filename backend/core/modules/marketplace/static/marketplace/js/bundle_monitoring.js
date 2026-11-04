document.addEventListener('error', event => {
    const image = event.target;
    if (image.matches?.('.bundle-product-photo img')) {
        image.hidden = true;
        const fallback = image.parentElement.querySelector('.bundle-photo-placeholder');
        if (fallback) fallback.hidden = false;
    }
}, true);
document.addEventListener('submit', event => {
    const form = event.target;
    if (!form.matches('.bm-action-form')) return;
    if (form.hasAttribute('aria-busy')) { event.preventDefault(); return; }
    if (form.dataset.confirm && !window.confirm(form.dataset.confirm)) { event.preventDefault(); return; }
    window.CampusHubActions.lock(form, form.dataset.confirm ? 'Highlighting…' : 'Processing…');
});
window.addEventListener('pageshow', () => {
    document.querySelectorAll('.bm-action-form').forEach(form => window.CampusHubActions.unlock(form));
    updateMajors();
});
function updateMajors() {
    const program = document.querySelector('.bm-filters select[name="program"]');
    const major = document.querySelector('.bm-filters select[name="major"]');
    if (!program || !major) return;
    let applicable = false;
    [...major.options].forEach(option => {
        if (!option.value) return;
        option.hidden = Boolean(program.value) && option.dataset.program !== program.value;
        option.disabled = option.hidden;
        if (!option.hidden) applicable = true;
    });
    major.closest('[data-major-filter]').hidden = !applicable;
    major.disabled = !applicable;
    if (major.selectedOptions[0]?.hidden || !applicable) major.value = '';
}
document.addEventListener('change', event => {
    if (event.target.matches('.bm-filters select[name="program"]')) updateMajors();
});

// The same authorized POST powers both the modal and the normal detail form.
(() => {
    const modal = document.getElementById('bundleSendModal');
    const form = modal?.querySelector('[data-bundle-send-form]');
    if (!form) return;
    const confirm = form.querySelector('[data-send-confirm]');
    const cancel = form.querySelector('[data-send-cancel]');
    const error = form.querySelector('[data-send-error]');
    const slide = document.querySelector('[data-suggestion-id]');
    let busy = false;
    let sent = false;
    modal.addEventListener('hide.bs.modal', event => { if (busy) event.preventDefault(); });
    modal.addEventListener('hidden.bs.modal', () => {
        error.hidden = true;
        error.textContent = '';
        if (sent) {
            const status = slide.querySelector('[data-suggestion-status]');
            status.tabIndex = -1;
            status.focus({preventScroll: true});
        }
    });
    form.addEventListener('submit', async event => {
        event.preventDefault();
        if (busy || sent) return;
        busy = true;
        form.setAttribute('aria-busy', 'true');
        confirm.disabled = cancel.disabled = true;
        confirm.textContent = 'Sending\u2026';
        error.hidden = true;
        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 30000);
        try {
            const response = await fetch(form.action, {method: 'POST', body: new FormData(form),
                credentials: 'same-origin', signal: controller.signal,
                headers: {Accept: 'application/json', 'X-Requested-With': 'XMLHttpRequest'}});
            const payload = response.headers.get('Content-Type')?.includes('application/json') ? await response.json() : null;
            if (response.redirected || !response.ok) throw new Error(payload?.error ||
                (response.status === 403 ? 'Sending is not authorized or your session has expired. Reload and try again.' : 'Unable to send this suggestion. Please try again.'));
            if (payload?.sent !== true || Number(payload.id) !== Number(slide.dataset.suggestionId) || typeof payload.status !== 'string' || !payload.status.trim()) {
                throw new Error('Sending was not confirmed. Reload to check the suggestion before trying again.');
            }
            sent = true;
            slide.querySelector('[data-suggestion-status]').textContent = payload.status;
            slide.querySelector('[data-bundle-send]').hidden = true;
            const feedback = slide.querySelector('[data-send-feedback]');
            feedback.textContent = 'Suggestion sent to the seller workspace.';
            feedback.hidden = false;
        } catch (failure) {
            error.textContent = failure.name === 'AbortError' ? 'Sending could not be confirmed in time. Reload to check its status or retry; a recorded send will not be duplicated.' :
                failure instanceof TypeError ? 'Connection interrupted. Please retry; a recorded send will not be duplicated.' : failure.message;
            error.hidden = false;
        } finally {
            busy = false;
            window.clearTimeout(timeout);
            form.removeAttribute('aria-busy');
            confirm.disabled = sent;
            cancel.disabled = false;
            confirm.textContent = 'Confirm Send';
            if (sent) window.bootstrap.Modal.getInstance(modal)?.hide();
        }
    });
})();

// The normal authorized detail page remains the no-JavaScript fallback.
(() => {
    const drawer = document.getElementById('bundleDetailsDrawer');
    const body = document.getElementById('bundleDetailsBody');
    if (!drawer || !body) return;
    const subtitle = document.getElementById('bundleDetailsSubtitle');
    let opener = null;
    let activeRequest = null;
    let viewport = {left: 0, top: 0};

    drawer.addEventListener('hidden.bs.offcanvas', () => {
        activeRequest?.abort();
        activeRequest = null;
        body.replaceChildren();
        body.removeAttribute('aria-busy');
        subtitle.textContent = '';
        if (opener?.isConnected) opener.focus({preventScroll: true});
        window.scrollTo({...viewport, behavior: 'instant'});
    });

    document.addEventListener('click', async event => {
        const trigger = event.target.closest('a[data-bundle-detail]');
        if (!trigger || event.button !== 0 || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey) return;
        if (!window.bootstrap?.Offcanvas) return;
        const target = new URL(trigger.href, window.location.href);
        if (target.origin !== window.location.origin) return;
        event.preventDefault();
        opener = trigger;
        viewport = {left: window.scrollX, top: window.scrollY};
        activeRequest?.abort();
        const controller = new AbortController();
        activeRequest = controller;
        const loading = document.createElement('p');
        loading.className = 'bm-drawer-loading';
        loading.setAttribute('role', 'status');
        loading.textContent = 'Loading recorded recommendation details…';
        body.replaceChildren(loading);
        body.setAttribute('aria-busy', 'true');
        subtitle.textContent = 'Saved recommendation information';
        window.bootstrap.Offcanvas.getOrCreateInstance(drawer).show(trigger);
        target.searchParams.set('format', 'drawer');
        try {
            const response = await fetch(target, {credentials: 'same-origin', signal: controller.signal,
                headers: {'X-Requested-With': 'XMLHttpRequest', Accept: 'text/html'}});
            if (response.redirected || !response.ok) {
                throw new Error(response.status === 403 ? 'Access to these details is not authorized.' :
                    response.status === 404 ? 'This recommendation is no longer available in your scope.' :
                    'Unable to load recorded details. Open the full detail page or try again.');
            }
            const markup = await response.text();
            const content = new DOMParser().parseFromString(markup, 'text/html').querySelector('[data-bundle-record]');
            if (!content) throw new Error('Unable to load recorded details. Open the full detail page or try again.');
            if (controller.signal.aborted || activeRequest !== controller) return;
            body.replaceChildren(document.importNode(content, true));
            subtitle.textContent = `Suggestion #${content.dataset.bundleRecord}`;
            const status = document.createElement('p');
            status.className = 'visually-hidden';
            status.setAttribute('role', 'status');
            status.textContent = 'Recorded recommendation details loaded.';
            body.prepend(status);
        } catch (error) {
            if (controller.signal.aborted || activeRequest !== controller) return;
            const failure = document.createElement('div');
            failure.className = 'bm-drawer-error';
            failure.setAttribute('role', 'alert');
            const message = document.createElement('p');
            message.textContent = error instanceof TypeError ? 'Unable to load recorded details. Check your connection or open the full detail page.' : error.message;
            const fallback = document.createElement('a');
            fallback.href = trigger.href;
            fallback.textContent = 'Open full detail page';
            failure.append(message, fallback);
            body.replaceChildren(failure);
        } finally {
            if (activeRequest === controller) body.removeAttribute('aria-busy');
        }
    });
})();
