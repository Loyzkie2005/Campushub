document.addEventListener('DOMContentLoaded', () => {
    const feedback = document.getElementById('dashboardOrderFeedback');
    let pending = false;

    function announce(message) {
        feedback.textContent = message;
        feedback.hidden = false;
    }

    // Delegation also handles Super Admin rows rebuilt after reporting-filter requests.
    document.addEventListener('click', async (event) => {
        const trigger = event.target.closest('[data-dashboard-order-details]');
        if (!trigger || event.ctrlKey || event.metaKey || event.shiftKey || event.altKey || event.button !== 0) return;
        if (!window.CampusHubOrders || !window.bootstrap) return; // Keep the existing Orders link fallback.
        event.preventDefault();
        if (pending || document.querySelector('#orderDetailModal.show, #completeOrderModal.show, #cancelOrderModal.show')) return;
        pending = true;
        trigger.setAttribute('aria-busy', 'true');
        announce('Loading order details…');
        const controller = new AbortController();
        const timeout = window.setTimeout(() => controller.abort(), 15000);
        try {
            const target = new URL(trigger.href, window.location.origin);
            if (target.origin !== window.location.origin || target.pathname !== '/admin-orders/' || !/^\d{1,18}$/.test(target.searchParams.get('order') || '')) {
                throw new Error('Unable to load order details. Please use View All Orders.');
            }
            const token = window.CampusHubAdminSession?.getTabToken() || new URL(window.location.href).searchParams.get('__at');
            target.searchParams.set('format', 'dashboard-order');
            if (token) target.searchParams.set('__at', token);
            const response = await fetch(target.href, {
                credentials: 'same-origin',
                cache: 'no-store',
                signal: controller.signal,
                headers: token ? {'X-Admin-Tab-Token': token} : {},
            });
            if (!response.ok || response.redirected || !response.headers.get('content-type')?.includes('text/html')) {
                throw new Error('Unable to load this order. Check your access or reload the dashboard and try again.');
            }
            const parsed = new DOMParser().parseFromString(await response.text(), 'text/html');
            const rows = parsed.querySelectorAll('[data-dashboard-order-fragment] tr[data-order-id]');
            if (rows.length !== 1 || rows[0].dataset.orderId !== target.searchParams.get('order')) {
                throw new Error('Unable to load this order. Reload the dashboard and try again.');
            }
            // The canonical controller reads escaped data attributes, never executes returned scripts.
            window.CampusHubOrders.openSelectedRow(rows[0], trigger);
            feedback.hidden = true;
        } catch (error) {
            announce(error.name === 'AbortError' ? 'Loading order details timed out. Please try again.' : error.message || 'Unable to load order details. Please try again.');
            trigger.focus({preventScroll: true});
        } finally {
            window.clearTimeout(timeout);
            pending = false;
            trigger.removeAttribute('aria-busy');
        }
    });
});
