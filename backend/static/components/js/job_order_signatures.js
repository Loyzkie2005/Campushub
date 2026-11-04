/* One capture component for the booking tab and the authenticated mobile Job Order. */
(() => {
    'use strict';
    const node = (tag, text, className) => {
        const element = document.createElement(tag);
        if (text) element.textContent = text;
        if (className) element.className = className;
        return element;
    };
    async function post(endpoint, body) {
        const response = await fetch(endpoint, {method: 'POST', credentials: 'same-origin',
            headers: {'Content-Type': 'application/json',
                'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''},
            body: JSON.stringify(body)});
        const result = await response.json().catch(() => ({}));
        if (!response.ok || response.redirected || !response.headers.get('Content-Type')?.startsWith('application/json')) {
            throw new Error(result.error || 'Unable to save the signature. Reload the Job Order to check its current status.');
        }
        return result;
    }
    function mount(host, config, refresh) {
        if (!host || !config) return;
        // The official DOCX-derived preview owns names, dates and signature images.
        // This toolbar supplies only the current actor's permitted action and capture errors.
        const toolbar = node('div', '', 'beu-signature-toolbar');
        const actions = node('div', '', 'beu-signature-controls');
        const message = node('p', '', 'beu-signature-message');
        message.setAttribute('role', 'status');
        toolbar.append(actions);
        host.replaceChildren(toolbar, message);
        host.hidden = !config.sections.some(section => !section.signed && section.can_sign);
        for (const section of config.sections) {
            if (!section.signed && section.can_sign) {
                actions.append(node('span', section.role, 'beu-signature-designation'));
                const button = node('button', 'Sign Job Order'); button.type = 'button';
                button.addEventListener('click', () => open(section, button)); actions.append(button);
            }
        }
        async function open(section, trigger) {
            if (!window.SignaturePad) {message.textContent = 'Signature pad unavailable. Reload this page.'; return;}
            const dialog = node('dialog', '', 'beu-signature-dialog');
            const title = node('h2', 'Sign Job Order'); title.id = 'beuSignatureDialogTitle';
            dialog.setAttribute('aria-labelledby', title.id);
            const help = node('p', `Sign as ${section.name} (${section.role}). Draw your own signature below.`);
            const canvas = node('canvas'); canvas.setAttribute('aria-label', 'Draw your signature using a mouse or touch');
            const error = node('p'); error.setAttribute('role', 'alert');
            const preview = node('img'); preview.alt = 'Your signature preview'; preview.hidden = true;
            const actions = node('div', '', 'beu-signature-actions');
            const clear = node('button', 'Clear Signature'); clear.type = 'button';
            const cancel = node('button', 'Cancel'); cancel.type = 'button';
            const confirm = node('button', 'Confirm & Sign', 'beu-signature-confirm'); confirm.type = 'button';
            actions.append(clear, cancel, confirm);
            dialog.append(title, help, canvas, preview,
                node('p', 'Confirming records your signature on this document revision in your assigned capacity.'), error, actions);
            document.body.append(dialog); dialog.showModal(); cancel.focus();
            let pad, width = 0, pending = true, challenge;
            const enable = value => {pending = !value; clear.disabled = cancel.disabled = confirm.disabled = !value;};
            enable(false);
            const resize = () => {
                const next = canvas.clientWidth;
                if (!next || next === width) return;
                const points = pad?.toData() || [];
                const previous = width; width = next;
                const ratio = Math.min(window.devicePixelRatio || 1, 2);
                canvas.width = Math.round(next * ratio); canvas.height = Math.round(180 * ratio);
                canvas.getContext('2d').scale(ratio, ratio);
                if (pad) {
                    const scale = previous ? Math.min(1, next / previous) : 1;
                    pad.fromData(points.map(group => ({...group,
                        points: group.points.map(point => ({...point, x: point.x * scale, y: point.y * scale}))})));
                    if (!pad.isEmpty()) {preview.src = pad.toDataURL('image/png'); preview.hidden = false;}
                }
            };
            resize();
            pad = new window.SignaturePad(canvas, {penColor: '#1A1851', backgroundColor: '#FFFFFF'});
            pad.off();
            const observer = new ResizeObserver(resize); observer.observe(canvas);
            pad.addEventListener('endStroke', () => {preview.src = pad.toDataURL('image/png'); preview.hidden = false;});
            clear.addEventListener('click', () => {pad.clear(); preview.hidden = true; error.textContent = '';});
            cancel.addEventListener('click', () => {if (!pending) dialog.close();});
            dialog.addEventListener('cancel', event => {if (pending) event.preventDefault();});
            dialog.addEventListener('close', () => {observer.disconnect(); pad.off(); dialog.remove();
                if (trigger.isConnected) trigger.focus();}, {once: true});
            try {
                challenge = await post(config.endpoint, {intent: 'prepare', section: section.section});
                enable(true); pad.on();
            } catch (failure) {error.textContent = failure.message; cancel.disabled = false; pending = false; return;}
            confirm.addEventListener('click', async () => {
                if (pending) return;
                if (pad.isEmpty()) {error.textContent = 'Draw your signature before confirming.'; return;}
                enable(false); pad.off(); dialog.setAttribute('aria-busy', 'true'); error.textContent = 'Saving signature...';
                try {
                    await post(config.endpoint, {intent: 'sign', section: section.section,
                        challenge: challenge.challenge, signature: pad.toDataURL('image/png')});
                    dialog.close(); await refresh();
                } catch (failure) {
                    error.textContent = failure.message; enable(true); pad.on(); dialog.removeAttribute('aria-busy');
                }
            });
        }
    }
    window.CampusHubJobOrderSignatures = {mount};
    document.addEventListener('DOMContentLoaded', () => {
        const data = document.getElementById('beuStandaloneSigningData');
        if (data) mount(document.getElementById('beuStandaloneSignatures'), JSON.parse(data.textContent), () => location.reload());
    });
})();
