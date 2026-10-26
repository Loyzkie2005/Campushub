document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-seller-avatar]').forEach(photo => {
        const fallback = () => { photo.hidden = true; };
        photo.addEventListener('error', fallback);
        if (photo.complete && photo.naturalWidth === 0) fallback();
    });
    // Application Details Drawer initialization (Bootstrap Offcanvas)
    const drawer = document.getElementById('sellerApplicationDrawer');
    if (drawer) {
        const body = document.getElementById('sellerApplicationBody');
        const subtitle = document.getElementById('sellerApplicationSubtitle');
        let opener = null;
        let viewport = {left: 0, top: 0};

        drawer.addEventListener('show.bs.offcanvas', event => {
            const trigger = event.relatedTarget || opener;
            const templateId = trigger?.dataset.sellerApplication || '';
            const content = document.getElementById(templateId);
            if (!(content instanceof HTMLTemplateElement)) {
                event.preventDefault();
                return;
            }
            opener = trigger;
            viewport = {left: window.scrollX, top: window.scrollY};
            if (subtitle) {
                subtitle.textContent = trigger.dataset.applicant ? `Applicant: ${trigger.dataset.applicant}` : '';
            }
            body.replaceChildren(content.content.cloneNode(true));
            body.scrollTop = 0;
        });

        drawer.addEventListener('hidden.bs.offcanvas', () => {
            body.replaceChildren();
            if (subtitle) subtitle.textContent = '';
            // Avoid Bootstrap's default focus return scrolling a low table row.
            if (opener?.isConnected) opener.focus({preventScroll: true});
            window.scrollTo({...viewport, behavior: 'instant'});
        });

        document.querySelectorAll('button[data-seller-application]').forEach(trigger => {
            trigger.addEventListener('click', () => {
                opener = trigger;
                window.bootstrap?.Offcanvas.getOrCreateInstance(drawer).show(trigger);
            });
        });
    }

    // Existing filter debouncing and auto-submit
    const filters = document.querySelector('.seller-filters');
    if (filters) {
        let timer;
        const submit = () => { clearTimeout(timer); filters.requestSubmit(); };
        filters.querySelector('[type="search"]').addEventListener('input', event => {
            clearTimeout(timer);
            if (!event.isComposing) timer = setTimeout(submit, 400);
        });
        filters.querySelector('select').addEventListener('change', submit);
        filters.addEventListener('submit', () => clearTimeout(timer));
        // The submit button remains available when JavaScript is unavailable.
        filters.querySelector('[type="submit"]').hidden = true;
    }

    // Existing review form actions (Approve / Reject / Revision)
    document.querySelectorAll('.seller-actions form').forEach(form => {
        form.addEventListener('submit', async event => {
            event.preventDefault();
            const actions = window.CampusHubActions, group = form.closest('.seller-actions');
            if (group.hasAttribute('aria-busy')) return;
            const reject = form.classList.contains('js-reject-seller'), revision = form.dataset.revision === 'true';
            if (reject) {
                const input = form.querySelector('[name="rejection_reason"]');
                const reason = window.prompt(revision ? 'Enter applicant-visible revision notes:' : 'Enter the applicant-visible rejection reason:', input.value);
                if (reason === null) return;
                input.value = reason.trim();
                if (!input.value) { window.CampusHubAlerts.error('Enter a reason before submitting this review.'); return; }
            }
            const consequence = reject ? (revision ? 'Request changes to this application? Your notes will be visible to the applicant.' : 'Reject this application? Your reason will be visible to the applicant.') : 'Approve this application and enable seller access?';
            if (!window.confirm(consequence)) return;
            const body = new FormData(form);
            if (!actions.lock(group, revision ? 'Submitting…' : reject ? 'Rejecting…' : 'Approving…', event.submitter || form.querySelector('button'))) return;
            try {
                const response = await fetch(form.action, {method: 'POST', credentials: 'same-origin', headers: {'X-Requested-With': 'XMLHttpRequest', Accept: 'application/json'}, body});
                const result = await actions.json(response, 'Unable to record this review. Reload the record before retrying.');
                if (result.ok !== true) throw new Error('The review was not confirmed. Reload the record before retrying.');
                window.CampusHubAlerts.remember(result.message);
                window.location.reload();
            } catch (error) {
                actions.unlock(group);
                window.CampusHubAlerts.error(error.message || 'Unable to record this review. Reload the record before retrying.');
            }
        });
    });
});
