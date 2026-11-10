// Keep the existing asset/event entry point; rankings now use a native table.
document.addEventListener('DOMContentLoaded', () => {
    const card = document.getElementById('topSellingProductsCard');
    const table = document.getElementById('topSellingProductsTable');
    if (!card || !table) return;
    const body = card.querySelector('[data-products-rows]');
    const content = card.querySelector('[data-products-content]');
    const empty = card.querySelector('[data-products-empty]');
    const error = card.querySelector('[data-products-error]');
    const live = card.querySelector('[data-products-live]');
    const placeholder = document.getElementById('topProductPlaceholder');
    const numbers = new Intl.NumberFormat('en-PH');

    function loadImage(image) {
        // Reuse the existing authenticated image endpoint and tab-session convention.
        const source = new URL(image.dataset.topProductImage, location.origin);
        const token = window.CampusHubAdminSession?.getTabToken() || new URL(location.href).searchParams.get('__at');
        if (source.origin === location.origin && token) source.searchParams.set('__at', token);
        image.addEventListener('error', () => { image.hidden = true; }, {once: true});
        image.src = source.href;
        image.hidden = false;
    }

    function render(products) {
        const rows = products.slice(0, 5).map((product, index) => {
            const row = document.createElement('tr');
            const rank = document.createElement('td');
            rank.className = 'top-product-rank';
            rank.textContent = `#${index + 1}`;
            const label = document.createElement('th');
            label.scope = 'row';
            const cell = document.createElement('div');
            cell.className = 'top-product-cell';
            const thumb = document.createElement('span');
            thumb.className = 'top-product-thumb';
            thumb.setAttribute('aria-hidden', 'true');
            thumb.append(placeholder.content.cloneNode(true));
            if (product.image_url) {
                const image = document.createElement('img');
                image.alt = '';
                image.width = image.height = 38;
                image.loading = 'lazy';
                image.decoding = 'async';
                image.dataset.topProductImage = product.image_url;
                loadImage(image);
                thumb.append(image);
            }
            const name = document.createElement('span');
            name.className = 'top-product-name';
            name.textContent = name.title = product.product_name;
            name.tabIndex = 0;
            cell.append(thumb, name);
            label.append(cell);
            const units = document.createElement('td');
            units.className = 'top-product-units';
            units.textContent = numbers.format(product.units_sold);
            row.append(rank, label, units);
            return row;
        });
        body.replaceChildren(...rows);
        content.hidden = !rows.length;
        empty.hidden = Boolean(rows.length);
        error.hidden = true;
        live.textContent = `Top-selling products updated. ${rows.length} product${rows.length === 1 ? '' : 's'}.`;
    }

    card.querySelectorAll('[data-top-product-image]').forEach(loadImage);
    document.addEventListener('campushub:dashboard-data', event => render(event.detail.marketplace.top_products));
    document.addEventListener('campushub:dashboard-load-error', () => {
        content.hidden = empty.hidden = true;
        live.textContent = '';
        error.hidden = false;
    });
});
