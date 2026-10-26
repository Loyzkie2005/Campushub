/* Component drafts are previews of API inventory. Django revalidates every save. */
document.addEventListener('DOMContentLoaded', () => {
    const byId = id => document.getElementById(id);
    const esc = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const money = cents => `₱${(cents / 100).toLocaleString('en-PH', {minimumFractionDigits:2, maximumFractionDigits:2})}`;
    const cents = value => Math.round(Number(value || 0) * 100);
    const enabled = () => Boolean(byId('productTypeBundle')?.checked);
    const selectedOwner = () => byId('productOwner')?.value || ownerId || document.querySelector('meta[name="current-user-id"]')?.content || '';
    let drafts = [], catalog = [], loading = false, catalogReady = false, requestVersion = 0, ownerId = '';
    const message = text => { byId('bundleComponentsMessage').textContent = text; };

    function info(product, selections) {
        if (!product) return {available:0, price:0, pools:[]};
        const groups = product.customization_options || [];
        const tracked = groups.some(group => group.options.some(option => Object.prototype.hasOwnProperty.call(option, 'stock')));
        let price = cents(product.price);
        const pools = [];
        for (const choice of selections) {
            const group = groups.find(g => g.name === choice.group);
            const option = group?.options.find(o => o.name === choice.option);
            if (!option) return {available:0, price:0, pools:[], valid:false};
            price += cents(option.extra_price);
            const expired = option.expiry_date && option.expiry_date < new Date().toLocaleDateString('en-CA');
            if (Object.prototype.hasOwnProperty.call(option, 'stock')) pools.push({key: `${product.id}:${group.name}:${option.name}`, stock:expired ? 0 : Number(option.stock || 0)});
        }
        if (groups.some(g => g.required !== false && !selections.some(s => s.group === g.name))) return {available:0, price, pools:[], valid:false};
        if (tracked && !pools.length) return {available:0, price, pools:[], valid:false};
        if (!tracked) pools.push({key:`${product.id}`, stock:Number(product.stock || 0)});
        return {price, pools, available:pools.length ? Math.min(...pools.map(pool => pool.stock)) : 0};
    }

    function draftInfo(draft) {
        return info(catalog.find(p => Number(p.id) === draft.product_id), draft.selections);
    }

    function totals() {
        let regular = 0;
        const pools = new Map();
        let valid = drafts.length > 0;
        drafts.forEach(draft => {
            const item = draftInfo(draft);
            regular += item.price * draft.required_quantity;
            valid &&= item.available > 0 && Number.isInteger(draft.required_quantity) && draft.required_quantity > 0;
            item.pools.forEach(pool => {
                const current = pools.get(pool.key) || {...pool, required:0};
                current.required += draft.required_quantity;
                pools.set(pool.key, current);
            });
        });
        const available = valid && pools.size ? Math.min(...[...pools.values()].map(pool => Math.floor(pool.stock / pool.required))) : 0;
        const known = catalogReady && drafts.every(draft => catalog.some(product => Number(product.id) === draft.product_id) && draftInfo(draft).valid !== false);
        return {regular, savings:regular - cents(byId('productPrice')?.value), available, known};
    }

    function paintTotals() {
        const sum = totals();
        byId('bundleRegularPrice').textContent = drafts.length && !loading && sum.known ? money(sum.regular) : '—';
        byId('bundleSavings').textContent = drafts.length && !loading && sum.known ? money(sum.savings) : '—';
        byId('bundleAvailable').textContent = !drafts.length || loading ? '—' : sum.known ? String(sum.available) : 'Unavailable';
    }

    function render() {
        byId('bundleComponentsBody').innerHTML = drafts.map((draft, index) => {
            const product = catalog.find(p => Number(p.id) === draft.product_id);
            const item = draftInfo(draft);
            const known = product && item.valid !== false;
            const unknown = loading ? 'Loading…' : 'Unavailable';
            return `<tr><td><strong>${esc(product?.name || draft.product_name)}</strong><small>${esc(draft.selections.map(s => `${s.group}: ${s.option}`).join(' · '))}</small></td><td>${known ? money(item.price) : unknown}<small data-component-subtotal>${known ? money(item.price * draft.required_quantity) + ' total' : '—'}</small></td><td>${known ? item.available : unknown}</td><td><input type="number" class="form-control bundle-required-input" min="1" step="1" value="${draft.required_quantity}" data-component-index="${index}" aria-label="Required Quantity for ${esc(product?.name || draft.product_name)}"> </td><td><button type="button" class="product-suggest-link" data-remove-component="${index}" aria-label="Remove ${esc(product?.name || draft.product_name)}">×</button></td></tr>`;
        }).join('') || '<tr><td colspan="5">No products selected.</td></tr>';
        paintTotals();
    }

    function syncType() {
        byId('bundleComponentsSection').hidden = !enabled();
        byId('singleProductVariantsSection').hidden = enabled();
        byId('productNameLabel').innerHTML = `${enabled() ? 'Bundle Name' : 'Product Name'} <span class="required-asterisk">*</span>`;
        if (enabled()) byId('productPriceLabel').innerHTML = 'Bundle Price (₱) <span class="required-asterisk">*</span>';
        render();
    }

    function selectionChoices(row) {
        return [...row.querySelectorAll('[data-group]')].flatMap(select => [...select.selectedOptions]
            .filter(option => option.value).map(option => ({group:select.dataset.group, option:option.value})));
    }

    function updateChoice(row) {
        const product = catalog.find(p => Number(p.id) === Number(row.dataset.choiceId));
        const item = info(product, selectionChoices(row));
        row.querySelector('[data-choice-price]').textContent = money(item.price);
        row.querySelector('[data-choice-stock]').textContent = item.available;
        row.querySelector('[data-add-component]').disabled = item.available < 1;
    }

    function renderChoices() {
        const search = byId('bundleProductSearch').value.trim().toLowerCase();
        const products = catalog.filter(p => p.name.toLowerCase().includes(search));
        byId('bundleSelectionBody').innerHTML = products.map(product => {
            const variants = (product.customization_options || []).map(group => {
                const options = group.options.map(option => `<option value="${esc(option.name)}" ${Object.prototype.hasOwnProperty.call(option, 'stock') && Number(option.stock) <= 0 ? 'disabled' : ''}>${esc(option.name)}</option>`).join('');
                return `<label class="bundle-variant-label">${esc(group.name)}<select class="form-select form-select-sm" data-group="${esc(group.name)}" ${group.selection === 'multiple' ? 'multiple' : ''} aria-label="${esc(product.name)} ${esc(group.name)}"><option value="">${group.required !== false ? 'Select variant' : 'None'}</option>${options}</select></label>`;
            }).join('');
            return `<tr data-choice-id="${product.id}"><td><strong>${esc(product.name)}</strong>${variants}</td><td data-choice-price></td><td data-choice-stock></td><td><input type="number" class="form-control bundle-required-input" data-choice-quantity min="1" step="1" value="1" aria-label="Required Quantity for ${esc(product.name)}"></td><td><button type="button" class="product-suggest-link" data-add-component>Add</button></td></tr>`;
        }).join('');
        byId('bundleSelectionMessage').textContent = products.length ? 'Approved, active products from this owner only.' : 'No available approved products for this owner.';
        byId('bundleSelectionBody').querySelectorAll('tr').forEach(updateChoice);
    }

    async function fetchCatalog() {
        const version = ++requestVersion;
        const owner = selectedOwner();
        if (!owner) { message('Select a product owner first.'); return false; }
        loading = true;
        catalogReady = false;
        catalog = [];
        byId('bundleSelectionMessage').textContent = 'Loading products…';
        byId('bundleSelectionBody').innerHTML = '';
        byId('bundleSelectionRetry').hidden = true;
        render();
        try {
            const response = await fetch(`/api/marketplace/products/?bundle_owner_id=${encodeURIComponent(owner)}`, {credentials:'same-origin', headers:{Accept:'application/json'}});
            const data = await response.json();
            if (version !== requestVersion) return false;
            if (!response.ok || response.redirected || !Array.isArray(data.products)) throw new Error(data.error || 'Unable to load products.');
            catalog = data.products;
            catalogReady = true;
            ownerId = owner;
            loading = false;
            renderChoices(); render();
            message('Availability and prices are calculated from the selected components.');
            return true;
        } catch (error) {
            if (version !== requestVersion) return false;
            loading = false;
            byId('bundleSelectionMessage').textContent = error.message || 'Unable to load products.';
            byId('bundleSelectionRetry').hidden = false;
            message('Unable to refresh component inventory. Open Add Products and retry.');
            render();
            return false;
        }
    }

    byId('addBundleProducts')?.addEventListener('click', () => {
        if (byId('productOwner') && !byId('productOwner').reportValidity()) return;
        bootstrap.Modal.getOrCreateInstance(byId('bundleProductModal')).show();
        fetchCatalog();
    });
    byId('bundleSelectionRetry')?.addEventListener('click', fetchCatalog);
    byId('bundleProductSearch')?.addEventListener('input', renderChoices);
    byId('bundleSelectionBody')?.addEventListener('change', event => updateChoice(event.target.closest('tr')));
    byId('bundleSelectionBody')?.addEventListener('click', event => {
        if (!event.target.closest('[data-add-component]')) return;
        const row = event.target.closest('tr');
        const product = catalog.find(p => Number(p.id) === Number(row.dataset.choiceId));
        const selections = selectionChoices(row);
        const quantity = Number(row.querySelector('[data-choice-quantity]').value);
        const available = info(product, selections).available;
        const key = JSON.stringify(selections);
        if (!Number.isInteger(quantity) || quantity < 1 || quantity > available) { byId('bundleSelectionMessage').textContent = 'Enter a whole required quantity within available stock.'; return; }
        if (drafts.some(d => d.product_id === Number(product.id) && JSON.stringify(d.selections) === key)) { byId('bundleSelectionMessage').textContent = 'This component is already selected. Change its required quantity in the form.'; return; }
        drafts.push({product_id:Number(product.id), product_name:product.name, selections, required_quantity:quantity});
        render();
        byId('bundleSelectionMessage').textContent = `${product.name} added.`;
    });
    byId('bundleComponentsBody')?.addEventListener('click', event => {
        const button = event.target.closest('[data-remove-component]');
        if (button) { drafts.splice(Number(button.dataset.removeComponent), 1); render(); }
    });
    byId('bundleComponentsBody')?.addEventListener('input', event => {
        if (!event.target.matches('[data-component-index]')) return;
        const draft = drafts[Number(event.target.dataset.componentIndex)];
        draft.required_quantity = Number(event.target.value);
        const known = catalog.some(product => Number(product.id) === draft.product_id) && draftInfo(draft).valid !== false;
        event.target.closest('tr').querySelector('[data-component-subtotal]').textContent = known ? `${money(draftInfo(draft).price * draft.required_quantity)} total` : '—';
        paintTotals();
    });
    byId('productPrice')?.addEventListener('input', render);
    byId('productOwner')?.addEventListener('change', () => {
        if (byId('productOwner').value !== ownerId) { drafts = []; catalog = []; ++requestVersion; loading = false; render(); message('Select approved products from this owner.'); }
    });
    document.querySelectorAll('input[name="productType"]').forEach(input => input.addEventListener('change', syncType));
    byId('bundleProductModal')?.addEventListener('shown.bs.modal', () => byId('bundleProductSearch').focus());

    window.CampusHubBundles = {
        enabled, syncType,
        reset() { drafts = []; catalog = []; ownerId = ''; loading = false; catalogReady = false; ++requestVersion; syncType(); message('Select approved products from the same owner.'); },
        load(product) { ownerId = String(product.seller_id || ''); drafts = (product.bundle?.components || []).map(row => ({product_id:row.product_id, product_name:row.product_name, required_quantity:row.required_quantity, selections:row.selections || []})); syncType(); if (enabled()) fetchCatalog(); },
        payload() { return drafts.map(({product_id, selections, required_quantity}) => ({product_id, selections, required_quantity})); },
        validate() {
            let error = loading ? 'Wait for component inventory to finish loading.' : !drafts.length ? 'Add at least one bundle component.' : !totals().known ? 'Refresh component inventory using Add Products before saving.' : totals().available < 1 ? 'Selected components cannot make one bundle. Check stock and required quantities.' : '';
            message(error || 'Component inventory will be verified again when saving.');
            return !error;
        },
        availability() { return totals().available; },
    };
});
