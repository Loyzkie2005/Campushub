/* One protected live result feeds the recommendation panels; no CSV fallback or writes. */
document.addEventListener('DOMContentLoaded', () => {
    const seed = document.getElementById('bundleSuggestionsData');
    if (!seed) return;
    const byId = id => document.getElementById(id);
    const suggestedPanel = byId('bundleSuggestions');
    const panels = {suggested: suggestedPanel?.hasAttribute('data-monitor-preview') ? null : suggestedPanel, frequent: byId('frequentlyBoughtTogether'), cross_sell: byId('crossSellSuggestions')};
    const titles = {suggested: 'Suggested Product Bundles', frequent: 'Frequently Bought Together', cross_sell: 'Cross-Sell Suggestions'};
    const emptyText = {suggested: 'No bundle suggestions available yet.', frequent: 'No frequently bought together products yet.',
        cross_sell: 'No cross-sell suggestions available yet.'};
    const errorText = {suggested: 'Unable to load bundle suggestions.', frequent: 'Unable to load frequently bought together products.',
        cross_sell: 'Unable to load cross-sell suggestions.'};
    const allDialog = byId('bundleAllDialog'), reviewDialog = byId('bundleReviewDialog');
    let data = JSON.parse(seed.textContent), mode = 'frequent', page = 1, busy = false;
    const isLiveResult = result => result?.source === 'live' &&
        Array.isArray(result.rows) && Array.isArray(result.frequent_results) && Array.isArray(result.directional_rows) && result.read_only === true;
    if (!isLiveResult(data)) data = {...data, source: 'live', rows: [], frequent_results: [], directional_rows: [], error: true};
    const limit = data.dashboard_limit || 3, pageSize = data.page_size || 8;
    const node = (tag, text = '', className = '') => {
        const element = document.createElement(tag);
        element.textContent = text; element.className = className; return element;
    };
    const button = (text, className, handler) => {
        const control = node('button', text, className); control.type = 'button';
        control.addEventListener('click', handler); return control;
    };
    const rowsFor = kind => kind === 'suggested' ? data.rows : kind === 'cross_sell' ? data.directional_rows : data.frequent_results;
    function photo(product) {
        const wrap = node('span', '', 'bundle-product-photo');
        const fallback = node('span', '', 'bundle-photo-placeholder');
        fallback.setAttribute('role', 'img'); fallback.setAttribute('aria-label', `No image available for ${product.name}`);
        fallback.append(byId('bundlePhotoPlaceholder').content.cloneNode(true));
        if (product.image_url) {
            const image = node('img'); image.src = product.image_url; image.alt = product.name;
            image.width = 52; image.height = 52; image.loading = 'lazy'; image.decoding = 'async';
            fallback.hidden = true; wrap.append(image);
        }
        wrap.append(fallback); return wrap;
    }
    function pair(row, kind) {
        const directional = kind === 'cross_sell';
        const suggested = kind === 'suggested';
        const card = node('article', '', `bundle-pair${directional ? ' bundle-pair--cross-sell' : ''}${suggested ? ' bundle-pair--suggested' : ''}`); card.dataset.pairId = row.id;
        const images = node('div', '', 'bundle-pair-images'), plus = node('span', directional ? '\u2192' : '+', 'bundle-pair-plus');
        plus.setAttribute('aria-hidden', 'true'); images.append(photo(row.products[0]), plus, photo(row.products[1]));
        const names = node('h3');
        if (suggested) names.textContent = `${row.product_a} + ${row.product_b}`;
        else {
            names.append(node('span', row.product_a));
            names.append(node('span', directional ? 'Recommended with' : 'and',
                directional ? 'bundle-relation-label' : 'visually-hidden'));
            names.append(node('span', row.product_b));
        }
        card.append(images, names, node('p', `Seller: ${row.seller}`, 'bundle-pair-seller'));
        if (suggested) {
            const footer = node('div', '', 'bundle-pair-footer'), control = node('button', 'View', 'bundle-review-button');
            control.type = 'button'; control.dataset.bundleReview = row.id;
            control.setAttribute('aria-label', `View ${row.product_a} and ${row.product_b}`);
            footer.append(control); card.append(footer);
        }
        return card;
    }
    function review(row) {
        if (!reviewDialog) return;
        const products = byId('bundleReviewProducts'); products.replaceChildren();
        row.products.forEach((product, index) => {
            const card = node('article', '', 'bundle-product-card');
            card.append(node('span', index === 0 ? 'Product A' : 'Product B'), photo(product), node('h3', product.name));
            products.append(card);
        });
        byId('bundleReviewCombination').textContent = `Suggested Bundle: ${row.product_a} + ${row.product_b}`;
        byId('bundleReviewSeller').textContent = `Seller: ${row.seller}`;
        reviewDialog.showModal();
    }
    function renderPanels() {
        Object.entries(panels).forEach(([kind, panel]) => {
            if (!panel) return;
            const list = panel.querySelector('[data-bundle-list]'); list.replaceChildren();
            const rows = rowsFor(kind).slice(0, limit);
            if (data.error || !rows.length) {
                list.append(node('p', data.error ? errorText[kind] : emptyText[kind], 'bundle-empty'));
                if (kind === 'suggested' && !data.error) list.append(node('p',
                    'Suggestions will appear after sufficient completed marketplace transactions are recorded.', 'bundle-empty-detail'));
                if (data.error) list.append(button('Retry', 'bundle-review-button', load));
            } else rows.forEach(row => list.append(pair(row, kind)));
            panel.querySelector('[data-bundle-view-all]').hidden = data.error || rowsFor(kind).length <= limit;
        });
    }
    function renderAll() {
        const rows = rowsFor(mode), totalPages = Math.max(1, Math.ceil(rows.length / pageSize));
        page = Math.min(page, totalPages);
        byId('bundleAllTitle').textContent = titles[mode];
        const list = byId('bundleAllRows'); list.replaceChildren();
        rows.slice((page - 1) * pageSize, page * pageSize).forEach(row => list.append(pair(row, mode)));
        const nav = byId('bundleAllPagination'); nav.replaceChildren();
        if (totalPages <= 1) return;
        const go = number => { page = number; renderAll(); allDialog.querySelector('.bundle-review-body').scrollTop = 0;
            nav.querySelector('[aria-current="page"]').focus(); };
        const previous = button('\u2039', '', () => go(page - 1)); previous.setAttribute('aria-label', 'Previous product pair page');
        previous.disabled = page === 1; nav.append(previous);
        const start = Math.max(1, Math.min(page - 2, totalPages - 4));
        for (let number = start; number <= Math.min(totalPages, start + 4); number++) {
            const control = button(String(number), '', () => go(number)); control.setAttribute('aria-label', `Product pair page ${number}`);
            if (number === page) control.setAttribute('aria-current', 'page'); nav.append(control);
        }
        const next = button('\u203a', '', () => go(page + 1)); next.setAttribute('aria-label', 'Next product pair page');
        next.disabled = page === totalPages; nav.append(next);
    }
    async function load() {
        if (busy) return;
        busy = true;
        Object.values(panels).filter(Boolean).forEach(panel => {
            panel.setAttribute('aria-busy', 'true');
            panel.querySelector('[data-bundle-list]').replaceChildren(node('p', 'Loading results\u2026', 'bundle-empty'));
            panel.querySelector('[data-bundle-view-all]').hidden = true;
        });
        const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 15000);
        try {
            const response = await fetch(`${data.endpoint}?source=live`, {credentials: 'same-origin',
                headers: {'Accept': 'application/json'}, signal: controller.signal});
            if (!response.ok) throw Error('Recommendations unavailable');
            const result = await response.json();
            if (!isLiveResult(result)) throw Error('Invalid result');
            data = result;
        } catch (_) {
            data = {...data, rows: [], frequent_results: [], directional_rows: [], error: true};
        } finally {
            clearTimeout(timer); busy = false; renderPanels();
            Object.values(panels).filter(Boolean).forEach(panel => panel.removeAttribute('aria-busy'));
        }
    }
    document.addEventListener('click', event => {
        const control = event.target.closest('[data-bundle-review],[data-bundle-view-all],[data-bundle-close]');
        if (!control || busy) return;
        if (control.hasAttribute('data-bundle-close')) control.closest('dialog').close();
        else if (control.hasAttribute('data-bundle-view-all')) {
            mode = control.dataset.bundleViewAll;
            if (!panels[mode]) return;
            page = 1; renderAll(); allDialog.showModal();
        } else if (panels.suggested) {
            const row = data.rows.find(item => item.id === control.dataset.bundleReview);
            if (row) review(row);
        }
    });
    // Retain the existing placeholder when a supplied image fails to load.
    document.addEventListener('error', event => {
        if (event.target.matches?.('.bundle-product-photo img')) {
            event.target.hidden = true;
            event.target.parentElement.querySelector('.bundle-photo-placeholder').hidden = false;
        }
    }, true);
    if (data.error) renderPanels(); // Server-rendered valid/empty results remain usable without JS.
});

/* Delegated controls also work after the Super Admin dashboard replaces its fragment. */
(() => {
    const selected = new Map();
    const selectedTabs = new Map();
    const selector = '[data-demo-bundle-carousel]';
    function selectTab(card, source, focus = false) {
        selectedTabs.set(card.getAttribute('aria-labelledby'), source);
        card.querySelectorAll('[data-bundle-tab]').forEach(tab => {
            const active = tab.dataset.bundleTab === source;
            tab.setAttribute('aria-selected', String(active));
            tab.tabIndex = active ? 0 : -1;
            if (active && focus) tab.focus();
        });
        card.querySelectorAll('[data-bundle-source]').forEach(panel => {
            panel.hidden = panel.dataset.bundleSource !== source;
        });
        const label = card.querySelector('[data-bundle-demo-label]');
        if (label) label.hidden = source !== 'synthetic';
    }
    function show(root, index, announce = false) {
        const slides = [...root.querySelectorAll('[data-demo-slide]')];
        if (!slides.length) return;
        index = Math.max(0, Math.min(slides.length - 1, index));
        slides.forEach((slide, position) => { slide.hidden = position !== index; });
        root.dataset.demoIndex = String(index);
        selected.set(root.getAttribute('aria-labelledby'), slides[index].dataset.demoId);
        root.querySelectorAll('[data-demo-go]').forEach((dot, position) => {
            dot.setAttribute('aria-current', position === index ? 'true' : 'false');
        });
        const previous = root.querySelector('[data-demo-step="-1"]');
        const next = root.querySelector('[data-demo-step="1"]');
        if (previous) previous.disabled = index === 0;
        if (next) next.disabled = index === slides.length - 1;
        if (announce) {
            const status = root.querySelector('[data-demo-announcement]');
            if (status) status.textContent = slides[index].textContent.trim().replace(/\s+/g, ' ');
        }
    }
    function fallback(image) {
        if (!image.matches?.('.bundle-product-photo img') || !image.closest(selector)) return;
        image.hidden = true;
        const placeholder = image.parentElement.querySelector('.bundle-photo-placeholder');
        if (placeholder) placeholder.hidden = false;
    }
    function initialize() {
        document.querySelectorAll(selector).forEach(root => {
            const slides = [...root.querySelectorAll('[data-demo-slide]')];
            const wanted = selected.get(root.getAttribute('aria-labelledby'));
            show(root, Math.max(0, slides.findIndex(slide => slide.dataset.demoId === wanted)));
            const controls = root.querySelector('[data-demo-controls]');
            if (controls) controls.hidden = slides.length < 2;
            root.querySelectorAll('.bundle-product-photo img').forEach(image => {
                if (image.complete && !image.naturalWidth) fallback(image);
            });
        });
        document.querySelectorAll('[data-bundle-tabs]').forEach(card => {
            selectTab(card, selectedTabs.get(card.getAttribute('aria-labelledby')) || 'synthetic');
            card.querySelector('[data-bundle-tablist]').hidden = false;
        });
    }
    document.addEventListener('click', event => {
        const tab = event.target.closest?.('[data-bundle-tab]');
        if (tab) {
            selectTab(tab.closest('[data-bundle-tabs]'), tab.dataset.bundleTab);
            return;
        }
        const button = event.target.closest?.('[data-demo-step], [data-demo-go]');
        const root = button?.closest(selector);
        if (!root || button.disabled) return;
        const index = button.hasAttribute('data-demo-go') ? Number(button.dataset.demoGo)
            : Number(root.dataset.demoIndex || 0) + Number(button.dataset.demoStep);
        show(root, index, true);
        if (button.disabled && document.activeElement === button) {
            root.querySelector('[data-demo-go][aria-current="true"]')?.focus();
        }
    });
    document.addEventListener('keydown', event => {
        const tab = event.target.closest?.('[data-bundle-tab]');
        if (tab && ['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) {
            event.preventDefault();
            const source = event.key === 'Home' ? 'synthetic' : event.key === 'End' ? 'live'
                : tab.dataset.bundleTab === 'synthetic' ? 'live' : 'synthetic';
            selectTab(tab.closest('[data-bundle-tabs]'), source, true);
            return;
        }
        const root = event.target.closest?.(selector);
        if (!root || !['ArrowLeft', 'ArrowRight', 'Home', 'End'].includes(event.key)) return;
        const slides = root.querySelectorAll('[data-demo-slide]');
        if (!slides.length) return;
        event.preventDefault();
        const index = Number(root.dataset.demoIndex || 0);
        show(root, event.key === 'Home' ? 0 : event.key === 'End' ? slides.length - 1
            : index + (event.key === 'ArrowRight' ? 1 : -1), true);
        root.querySelector('[data-demo-go][aria-current="true"]')?.focus();
    });
    document.addEventListener('error', event => fallback(event.target), true);
    document.addEventListener('campushub:dashboard-data', initialize);
    if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initialize);
    else initialize();
})();
