document.addEventListener('DOMContentLoaded', () => {
    const controls = document.getElementById('dashboardGlobalControls');
    if (!controls) return;
    const root = controls.closest('[data-global-dashboard]');
    const form = document.getElementById('dashboardGlobalFilter');
    const select = document.getElementById('dashboardPeriod');
    const custom = document.getElementById('dashboardCustomRange');
    const start = document.getElementById('dashboardStartDate');
    const end = document.getElementById('dashboardEndDate');
    const dateError = document.getElementById('dashboardDateError');
    const error = document.getElementById('dashboardLoadError');
    const loading = document.getElementById('dashboardLoading');
    const kpiStale = document.getElementById('dashboardKpiStale');
    const refresh = document.getElementById('dashboardRefresh');
    const salesError = document.getElementById('salesOverviewLoadError');
    const salesCard = document.getElementById('sales-overview-card');
    const lowStockCard = root.querySelector('[data-low-stock-card]');
    const lowStockContent = lowStockCard?.querySelector('[data-low-stock-content]');
    const lowStockError = lowStockCard?.querySelector('[data-low-stock-error]');
    const recentOrdersContent = root.querySelector('#recentOrdersSlot .recent-orders-table-wrap');
    const recentOrdersError = root.querySelector('[data-recent-orders-error]');
    // State labels are presentation only; all data still comes from this existing request.
    const regions = [...root.querySelectorAll('[data-executive-dashboard] [data-empty-region]')];
    for (const region of regions) {
        const status = document.createElement('p');
        status.className = 'dashboard-card-loading'; status.setAttribute('role', 'status');
        status.textContent = 'Updating this section…'; region.append(status);
    }
    function regionState(state, chart = null) {
        for (const region of regions) {
            if (chart && region.dataset.emptyRegion !== chart) continue;
            region.dataset.requestState = state;
        }
    }
    let applied = JSON.parse(document.getElementById('dashboardPeriodData').textContent);
    let requested = { ...applied };
    let controller;
    let salesRetryOnly = false;
    let bookingRetryOnly = false;
    let serviceRetryOnly = false;
    const bookingCard = root.querySelector('[data-booking-overview]');
    const serviceCard = root.querySelector('[data-services-overview]');
    const serviceGrouping = document.getElementById('serviceGroupingSelect');
    const money = new Intl.NumberFormat('en-PH', { style: 'currency', currency: 'PHP' });
    // Prefer wrapping between thousands groups, retaining every digit on narrow cards.
    const wrapMoney = (text) => text.replaceAll(',', ',\u200b');
    const revenueKpi = root.querySelector('[data-dashboard-kpi="marketplace_revenue"]');
    if (revenueKpi) revenueKpi.textContent = wrapMoney(revenueKpi.textContent);
    const number = new Intl.NumberFormat('en-PH', { maximumFractionDigits: 0 });
    const timestamp = new Intl.DateTimeFormat('en-PH', { timeZone: 'Asia/Manila', year: 'numeric', month: 'short', day: '2-digit', hour: 'numeric', minute: '2-digit' });
    const categoryCard = document.getElementById('categorySalesCard');
    const categorySvg = categoryCard?.querySelector('.marketplace-category-chart svg');
    const categoryTooltip = categoryCard?.querySelector('[data-category-tooltip]');
    let activeCategorySegment = null;
    function hideCategoryTooltip() {
        if (!categoryTooltip) return;
        categoryTooltip.hidden = true;
        activeCategorySegment?.classList.remove('is-active');
        activeCategorySegment = null;
    }
    function showCategoryTooltip(segment, x, y) {
        if (activeCategorySegment !== segment) {
            activeCategorySegment?.classList.remove('is-active');
            segment.classList.add('is-active');
            activeCategorySegment = segment;
        }
        categoryTooltip.querySelector('[data-category-tooltip-name]').textContent = segment.dataset.categoryName;
        categoryTooltip.querySelector('[data-category-tooltip-sales]').textContent = `Sales: \u20b1${segment.dataset.categorySales}`;
        categoryTooltip.querySelector('[data-category-tooltip-share]').textContent = `Sales share: ${segment.dataset.categoryShare}%`;
        categoryTooltip.hidden = false;
        const cardRect = categoryCard.getBoundingClientRect();
        categoryTooltip.style.left = `${Math.max(12, Math.min(x - cardRect.left + 12, cardRect.width - categoryTooltip.offsetWidth - 12))}px`;
        categoryTooltip.style.top = `${Math.max(12, Math.min(y - cardRect.top + 12, cardRect.height - categoryTooltip.offsetHeight - 12))}px`;
    }
    function categoryAtPointer(event) {
        const rect = categorySvg.getBoundingClientRect();
        if (!rect.width || !rect.height) return null;
        const x = (event.clientX - rect.left) * 240 / rect.width - 120;
        const y = (event.clientY - rect.top) * 240 / rect.height - 120;
        const radius = Math.hypot(x, y);
        if (radius < 69 || radius > 113) return null;
        // Match the rotated ring's angle to backend segment ranges, rather than
        // relying on overlapping dashed SVG circles to identify the category.
        const sharePosition = ((Math.atan2(y, x) * 180 / Math.PI + 90 + 360) % 360) / 3.6;
        const segment = [...categorySvg.querySelectorAll('[data-category-name]')].find((segment) => {
            const start = -Number(segment.dataset.categoryStart);
            return sharePosition >= start && sharePosition < start + Number(segment.dataset.categoryLength);
        });
        // Keep the hovered segment active over its enlarged outer edge.
        return radius <= 107 || segment === activeCategorySegment ? segment : null;
    }
    function inspectCategoryPointer(event) {
        const segment = categoryAtPointer(event);
        if (segment) showCategoryTooltip(segment, event.clientX, event.clientY);
        else hideCategoryTooltip();
    }
    if (categorySvg && categoryTooltip) {
    categorySvg.addEventListener('pointermove', inspectCategoryPointer);
    categorySvg.addEventListener('pointerdown', inspectCategoryPointer);
    categorySvg.addEventListener('pointerleave', (event) => {
        if (event.pointerType !== 'touch' && !categoryTooltip.contains(event.relatedTarget)) hideCategoryTooltip();
    });
    categoryTooltip.addEventListener('pointerleave', hideCategoryTooltip);
    categorySvg.addEventListener('focusin', (event) => {
        const segment = event.target.closest('[data-category-name]');
        if (!segment) return;
        const rect = categorySvg.getBoundingClientRect();
        showCategoryTooltip(segment, rect.left + rect.width / 2, rect.top + rect.height / 2);
    });
    categorySvg.addEventListener('focusout', (event) => {
        if (!categorySvg.contains(event.relatedTarget)) hideCategoryTooltip();
    });
    document.addEventListener('keydown', (event) => { if (event.key === 'Escape') hideCategoryTooltip(); });
    document.addEventListener('pointerdown', (event) => {
        if (!categorySvg.contains(event.target) && !categoryTooltip.contains(event.target)) hideCategoryTooltip();
    });
    window.addEventListener('resize', hideCategoryTooltip);
    }
    function setText(selector, value) {
        const element = root.querySelector(selector);
        if (element) element.textContent = value;
    }
    function loadProductImage(image, imageUrl) {
        const source = new URL(imageUrl, window.location.origin);
        const token = window.CampusHubAdminSession?.getTabToken() || new URL(window.location.href).searchParams.get('__at');
        if (source.origin === window.location.origin && token) source.searchParams.set('__at', token);
        image.addEventListener('error', () => { image.hidden = true; }, { once: true });
        image.src = source.href;
        image.hidden = false;
    }
    root.querySelectorAll('[data-product-image-url]').forEach((image) => loadProductImage(image, image.dataset.productImageUrl));
    function syncConstraints() {
        end.min = start.value;
        start.max = end.value || end.max;
        dateError.hidden = true;
    }
    function updateSecondaryTitles() {
        root.querySelectorAll('[data-dashboard-secondary]').forEach((element) => {
            if (element.scrollWidth > element.clientWidth) element.title = element.textContent;
            else element.removeAttribute('title');
        });
    }
    window.addEventListener('resize', updateSecondaryTitles);
    updateSecondaryTitles();
    document.fonts?.ready.then(updateSecondaryTitles);
    function positionCustomRange() {
        if (custom.hidden) return;
        const viewport = document.documentElement.clientWidth || window.innerWidth;
        const anchor = form.getBoundingClientRect();
        const width = custom.getBoundingClientRect().width;
        // Keep the panel beneath the selector and inside the viewport on narrow screens.
        custom.style.left = `${Math.max(16 - anchor.left, Math.min(0, viewport - 16 - anchor.left - width))}px`;
    }
    window.addEventListener('resize', positionCustomRange);
    function restoreAppliedPeriod() {
        select.value = applied.type;
        start.value = applied.start_date;
        end.value = applied.end_date;
        custom.hidden = true;
        dateError.hidden = true;
    }
    function activePeriod() {
        return root.getAttribute('aria-busy') === 'true' ? requested : applied;
    }
    start.addEventListener('input', syncConstraints);
    end.addEventListener('input', syncConstraints);
    let attentionItems = JSON.parse(document.getElementById('dashboardAttentionData').textContent).items;
    let backupAttention = null;
    const serviceAttention = new Map();
    document.addEventListener('campushub:system-status', (event) => {
        for (const [key, label] of [['database', 'Database'], ['chat_service', 'Chat Service']]) {
            const health = event.detail?.[key]?.status;
            if (health === 'online') serviceAttention.delete(key);
            else if (['degraded', 'unavailable'].includes(health)) serviceAttention.set(key, {
                key: `${key}_issue`, count: 1, label: `${label} ${health === 'degraded' ? 'Degraded' : 'Unavailable'}`,
                action: 'View Status', url: '#dashboardSystemStatus', severity: 'attention',
            });
        }
        const state = event.detail?.backup?.status;
        // Unknown health retains the last verified warning; it is not all-clear.
        if (!['healthy', 'warning', 'failed', 'no_backup_available'].includes(state)) { renderAttention({items: attentionItems}); return; }
        const backupLink = document.querySelector('[data-system-service="backup"] .dashboard-service-action');
        backupAttention = state === 'healthy' || !backupLink ? null : {
            key: 'backup_warning', count: 1, label: 'Backup Warning', action: 'Open Backup',
            url: backupLink.href, severity: 'attention',
        };
        renderAttention({ items: attentionItems });
    });
    function renderAttention(attention) {
        const list = document.getElementById('dashboardAttentionItems');
        if (!list) return;
        attentionItems = attention.items.filter((item) => item.count > 0);
        const items = [...attentionItems, ...serviceAttention.values(), ...(backupAttention ? [backupAttention] : [])];
        const fragment = document.createDocumentFragment();
        for (const item of items) {
            const row = document.createElement('li');
            row.className = 'dashboard-attention-row';
            row.dataset.attentionKey = item.key;
            row.dataset.severity = item.severity;
            const icon = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
            icon.classList.add('dashboard-attention-icon');
            for (const [key, value] of Object.entries({ 'aria-hidden': 'true', viewBox: '0 0 24 24', fill: 'none', stroke: 'currentColor', 'stroke-width': '1.8' })) icon.setAttribute(key, value);
            const path = document.createElementNS(icon.namespaceURI, 'path');
            path.setAttribute('d', 'M12 8v5m0 3h.01M10.3 3.8 2.6 17a2 2 0 0 0 1.7 3h15.4a2 2 0 0 0 1.7-3L13.7 3.8a2 2 0 0 0-3.4 0Z');
            path.setAttribute('stroke-linecap', 'round');
            path.setAttribute('stroke-linejoin', 'round');
            icon.appendChild(path);
            const count = document.createElement('strong');
            count.className = 'dashboard-attention-count';
            count.textContent = number.format(item.count);
            const label = document.createElement('span');
            label.className = 'dashboard-attention-label';
            label.textContent = item.label;
            const action = document.createElement('a');
            action.className = 'dashboard-attention-action';
            const url = new URL(item.url, window.location.origin);
            const token = new URL(window.location.href).searchParams.get('__at');
            if (url.origin === window.location.origin && token) url.searchParams.set('__at', token);
            action.href = url.toString();
            action.setAttribute('aria-label', `${item.action}: ${item.label}`);
            action.append(document.createTextNode(`${item.action} `));
            const arrow = document.createElement('span');
            arrow.setAttribute('aria-hidden', 'true');
            arrow.textContent = '\u2192';
            action.appendChild(arrow);
            row.append(icon, count, label, action);
            fragment.appendChild(row);
        }
        list.replaceChildren(fragment);
        document.getElementById('dashboardAttentionEmpty').hidden = items.length > 0;
    }
    function inventoryLink(url) {
        const target = new URL(url, window.location.origin);
        const token = window.CampusHubAdminSession?.getTabToken() || new URL(window.location.href).searchParams.get('__at');
        if (target.origin === window.location.origin && token) target.searchParams.set('__at', token);
        return target.href;
    }
    function renderLowStock(snapshot) {
        if (!lowStockCard) return;
        const failed = !snapshot || snapshot.state !== 'ready';
        lowStockContent.hidden = failed;
        lowStockError.hidden = !failed;
        if (failed) return;
        lowStockCard.querySelector('[data-low-stock-view-all]').href = inventoryLink(snapshot.view_all_url);
        const rows = document.createDocumentFragment();
        for (const item of snapshot.products) {
            const row = document.createElement('tr');
            const heading = document.createElement('th');
            heading.scope = 'row';
            const link = document.createElement('a');
            link.className = 'low-stock-product-cell';
            link.href = inventoryLink(item.url);
            link.title = `View inventory for ${item.product_name}${item.variant_name ? ` (${item.variant_name})` : ''}`;
            const thumb = document.createElement('span');
            thumb.className = 'inventory-alert-thumb';
            thumb.setAttribute('aria-hidden', 'true');
            if (item.image_url) {
                const image = document.createElement('img');
                image.alt = '';
                image.width = image.height = 36;
                image.loading = 'lazy';
                image.decoding = 'async';
                loadProductImage(image, item.image_url);
                thumb.appendChild(image);
            }
            link.appendChild(thumb);
            const details = document.createElement('span');
            const name = document.createElement('strong');
            name.textContent = item.product_name;
            details.appendChild(name);
            if (item.variant_key) {
                const variant = document.createElement('small');
                variant.textContent = `${item.group_name || 'Option'}: ${item.variant_name || 'Unnamed option'}`;
                details.appendChild(variant);
            }
            link.appendChild(details);
            heading.appendChild(link);
            const available = document.createElement('td');
            available.className = 'text-end low-stock-qty';
            available.textContent = number.format(item.available);
            const threshold = document.createElement('td');
            threshold.className = 'text-end';
            threshold.textContent = item.status === 'out_of_stock' ? 'Out of Stock' : 'Low Stock';
            row.append(heading, available, threshold);
            rows.appendChild(row);
        }
        lowStockCard.querySelector('[data-low-stock-rows]').replaceChildren(rows);
        lowStockCard.querySelector('[data-low-stock-empty]').hidden = snapshot.products.length > 0;
        if (root.querySelector('[data-executive-dashboard]')) lowStockContent.querySelector('table').hidden = !snapshot.products.length;
    }
    function renderRecentOrders(orders) {
        const body = root.querySelector('[data-recent-order-rows]');
        if (!body) return;
        if (!Array.isArray(orders)) throw new Error('Recent orders payload is unavailable');
        const rows = document.createDocumentFragment();
        for (const order of (document.querySelector('[data-executive-dashboard]') ? orders.slice(0, 5) : orders)) {
            const row = document.createElement('tr');
            const cell = (text, className = '') => {
                const element = document.createElement('td');
                element.className = className;
                element.textContent = text;
                return element;
            };
            const items = cell('', 'recent-order-items');
            const product = document.createElement('div');
            product.className = 'recent-order-product';
            if (order.image_url) {
                const image = document.createElement('img');
                image.className = 'recent-order-thumb'; image.alt = ''; image.width = image.height = 38;
                loadProductImage(image, order.image_url);
                product.append(image);
            } else {
                const placeholder = document.createElement('span');
                placeholder.className = 'recent-order-thumb recent-order-thumb--empty';
                placeholder.setAttribute('aria-hidden', 'true'); product.append(placeholder);
            }
            const details = document.createElement('span'); details.className = 'recent-order-item';
            const name = document.createElement('strong'); name.textContent = order.product_name;
            const quantity = document.createElement('small'); quantity.textContent = `${number.format(order.quantity)} unit${order.quantity === 1 ? '' : 's'}`;
            details.append(name, quantity); product.append(details); items.append(product);
            const status = cell('', 'recent-order-status');
            const pill = document.createElement('span');
            pill.className = `status-pill status-${order.status_key}`; pill.textContent = order.status; status.append(pill);
            if (document.querySelector('[data-executive-dashboard]')) {
                const reference = document.createElement('th'); reference.scope = 'row';
                const link = document.createElement('a'); link.textContent = order.code;
                link.className = 'recent-order-link';
                const target = new URL(order.url, location.origin);
                if (target.origin !== location.origin || target.pathname !== '/admin-orders/') throw new Error('Invalid order destination');
                const token = window.CampusHubAdminSession?.getTabToken() || new URL(location.href).searchParams.get('__at');
                if (token) target.searchParams.set('__at', token);
                link.href = target.href; reference.append(link);
                pill.classList.add('recent-orders-status');
                const payment = cell('');
                const paymentLabel = document.createElement('span');
                paymentLabel.className = 'status-pill recent-orders-payment';
                paymentLabel.dataset.paymentStatus = order.payment_key;
                paymentLabel.textContent = order.payment_status;
                payment.append(paymentLabel);
                const action = cell('');
                const detailsLink = link.cloneNode(false);
                detailsLink.className = 'recent-order-details';
                detailsLink.textContent = 'View Details';
                detailsLink.setAttribute('aria-label', `View details for order ${order.code}`);
                action.append(detailsLink);
                row.append(reference, cell(order.date), cell(order.buyer_name, 'recent-orders-person'),
                    cell(order.seller_name || 'Not recorded', 'recent-orders-person'), cell(order.item_count ?? 'Not recorded', 'text-center'),
                    cell(`\u20b1${order.total}`, 'text-end'), status, payment, action);
            } else {
            row.append(cell(order.code, 'recent-order-code'), items, cell(order.buyer_name, 'recent-order-customer'),
                cell(`₱${order.total}`, 'text-end recent-order-amount'), status,
                cell(order.payment_status, 'recent-order-payment'), cell(order.date, 'recent-order-date'));
            }
            rows.append(row);
        }
        body.replaceChildren(rows);
        const empty = root.querySelector('[data-recent-orders-empty]');
        if (empty) empty.hidden = Boolean(orders.length);
        recentOrdersContent.hidden = empty ? !orders.length : false;
        recentOrdersError.hidden = true;
    }

    function renderSalesTrend(payload) {
        const grouping = payload.grouping;
        root.querySelector('.sales-overview__trend-header p').textContent = 'Marketplace revenue over the selected period.';
        const hasSales = payload.marketplace.sales_overview.has_sales;
        root.querySelector('.sales-overview__empty').hidden = hasSales;
        root.querySelector('.sales-overview__canvas').dataset.hasSales = String(hasSales);
        root.querySelector('.sales-overview__legend').hidden = !hasSales;
        root.querySelector('.sales-overview__canvas').hidden = !hasSales;
        document.getElementById('salesOverviewChart').setAttribute('aria-label', `Marketplace revenue by ${grouping} period. Use left and right arrow keys to inspect each period.`);
        root.querySelectorAll('.sales-overview__cta-btn').forEach((detailLink) => {
            const url = new URL(detailLink.href);
            url.searchParams.set('date_from', payload.period.start_date);
            url.searchParams.set('date_to', payload.period.end_date);
            url.searchParams.set('grouping', grouping);
            detailLink.href = url.toString();
        });
    }
    function render(payload) {
        if (kpiStale) kpiStale.hidden = true;
        const marketplace = payload.marketplace;
        renderRecentOrders(payload.operations?.recent_orders);
        renderLowStock(payload.low_stock);
        renderAttention(payload.attention_required);
        for (const [key, metric] of Object.entries(payload.kpis)) {
            setText(`[data-dashboard-kpi="${key}"]`, key === 'marketplace_revenue' ? wrapMoney(money.format(metric.value)) : number.format(metric.value));
            const secondary = root.querySelector(`[data-dashboard-secondary="${key}"]`);
            if (secondary) {
                const recordedFreeSales = key === 'marketplace_revenue' && marketplace.sales_overview.has_sales;
                secondary.textContent = Number(metric.value) === 0 && secondary.dataset.zeroCopy && !recordedFreeSales ? secondary.dataset.zeroCopy : metric.secondary_text;
                secondary.dataset.semanticType = metric.semantic_type;
                secondary.dataset.trendState = metric.trend_state;
                secondary.dataset.direction = metric.direction;
            }
        }
        updateSecondaryTitles();
        for (const group of ['services_overview', 'accounts_overview']) {
            for (const [key, value] of Object.entries(payload[group] || {})) {
                setText(`[data-dashboard-summary="${group}.${key}"]`, value);
            }
        }
        for (const metric of marketplace.sales_overview.metrics) {
            const content = root.querySelector(`.sales-overview__metric[data-metric="${metric.key}"] .sales-overview__metric-content`);
            if (!content) continue;
            content.querySelector('strong').textContent = `${metric.currency ? '₱' : ''}${metric.value}`;
            const comparison = content.querySelector('.dashboard-comparison');
            const isZero = !marketplace.sales_overview.has_sales;
            comparison.textContent = isZero
                ? `No completed ${metric.key === 'sales' ? 'sales' : 'orders'} this period.`
                : metric.comparison_text;
            comparison.dataset.semanticType = isZero ? 'neutral' : metric.semantic_type;
        }
        renderSalesTrend(payload);
        if (root.querySelector('[data-marketplace-products]')) {
        const productHeading = root.querySelector('[data-products-heading]');
        productHeading.replaceChildren(...['Product', 'Units Sold / Sales'].map((label) => {
            const heading = document.createElement('span');
            heading.textContent = label;
            return heading;
        }));
        const products = document.createDocumentFragment();
        for (const product of (document.querySelector('[data-executive-dashboard]') ? marketplace.top_products.slice(0, 3) : marketplace.top_products)) {
            const row = document.createElement('li');
            if (product.image_url) {
                const image = document.createElement('img');
                image.className = 'marketplace-product-image';
                image.alt = '';
                image.width = image.height = 40;
                image.loading = 'lazy';
                image.decoding = 'async';
                loadProductImage(image, product.image_url);
                row.appendChild(image);
            }
            const details = document.createElement('div');
            details.className = 'marketplace-product-details';
            const name = document.createElement('strong');
            const rank = document.createElement('span');
            rank.className = 'marketplace-product-rank';
            rank.setAttribute('aria-hidden', 'true');
            rank.textContent = `${product.rank}.`;
            name.append(rank, document.createTextNode(` ${product.product_name}`));
            const category = document.createElement('span');
            category.textContent = product.category;
            details.append(name, category);
            const units = document.createElement('span');
            units.className = 'marketplace-product-units';
            units.textContent = number.format(product.units_sold);
            units.setAttribute('aria-label', `${number.format(product.units_sold)} ${product.units_sold === 1 ? 'unit' : 'units'} sold`);
            const amount = document.createElement('span');
            amount.className = 'marketplace-product-amount';
            amount.textContent = `\u20b1${product.sales}`;
            amount.setAttribute('aria-label', `Sales amount: ${product.sales} pesos`);
            const stats = document.createElement('div');
            stats.className = 'marketplace-product-stats';
            stats.append(units, amount);
            row.append(details, stats);
            products.appendChild(row);
        }
        root.querySelector('[data-marketplace-products]').replaceChildren(products);
        root.querySelector('[data-products-heading]').hidden = marketplace.top_products.length === 0;
        root.querySelector('[data-products-empty]').hidden = marketplace.top_products.length > 0;
        }
        if (categoryCard) {
        const snapshot = marketplace.product_categories;
        root.querySelector('[data-category-empty]').hidden = snapshot.total > 0;
        root.querySelector('[data-category-content]').hidden = snapshot.total === 0;
        root.querySelector('[data-category-total]').textContent = `\u20b1${snapshot.total_sales}`;
        hideCategoryTooltip();
        const categories = document.createDocumentFragment();
        const segments = document.createDocumentFragment();
        const labels = document.createDocumentFragment();
        const svgNamespace = 'http://www.w3.org/2000/svg';
        for (const category of snapshot.categories) {
            const row = document.createElement('tr');
            const heading = document.createElement('th');
            heading.scope = 'row';
            const line = document.createElement('span');
            line.className = 'marketplace-category-name';
            const dot = document.createElement('i');
            dot.className = 'marketplace-category-dot';
            dot.setAttribute('aria-hidden', 'true');
            dot.style.backgroundColor = category.chart.color;
            const name = document.createElement('span');
            name.textContent = category.name;
            name.title = category.name;
            line.append(dot, name);
            heading.append(line);
            const percent = document.createElement('td');
            percent.className = 'marketplace-category-share';
            percent.textContent = `${category.percentage}%`;
            const amount = document.createElement('td');
            amount.className = 'marketplace-category-sales';
            amount.textContent = `\u20b1${category.sales}`;
            row.append(heading, percent, amount);
            categories.appendChild(row);
            if (category.chart.share > 0) {
                const circle = document.createElementNS(svgNamespace, 'circle');
                for (const [attribute, value] of Object.entries({ cx: 120, cy: 120, r: 88, fill: 'none',
                    stroke: category.chart.color, 'stroke-width': 38, pathLength: 100,
                    'stroke-dasharray': `${category.chart.share} 100`, 'stroke-dashoffset': category.chart.offset,
                    'data-category-name': category.name, 'data-category-sales': category.sales,
                    'data-category-share': category.percentage, 'data-category-start': category.chart.offset,
                    'data-category-length': category.chart.share, tabindex: 0, role: 'img',
                    'aria-label': `${category.name}. Sales: \u20b1${category.sales}. Sales share: ${category.percentage}%.` })) {
                    circle.setAttribute(attribute, value);
                }
                segments.appendChild(circle);
            }
            if (category.chart.share >= 4) {
                const label = document.createElementNS(svgNamespace, 'text');
                for (const [attribute, value] of Object.entries({ x: category.chart.label_x, y: category.chart.label_y,
                    fill: category.chart.label_color, 'text-anchor': 'middle', 'dominant-baseline': 'central' })) {
                    label.setAttribute(attribute, value);
                }
                label.textContent = `${category.percentage}%`;
                labels.appendChild(label);
            }
        }
        root.querySelector('[data-marketplace-categories]').replaceChildren(categories);
        root.querySelector('[data-category-segments]').replaceChildren(segments);
        root.querySelector('[data-category-chart-labels]').replaceChildren(labels);
        }
        setText('#dashboardSelectedRange', `${payload.period.start_date} – ${payload.period.end_date}`);
        const updated = document.getElementById('dashboardUpdatedAt');
        updated.dateTime = payload.last_updated;
        updated.textContent = `Updated ${timestamp.format(new Date(payload.last_updated))}`;
        document.dispatchEvent(new CustomEvent('campushub:dashboard-data', { detail: payload }));
    }
    async function load(period = requested, salesOnly = false, bookingOnly = false, servicesOnly = false) {
        // Grouping changes only the chart; global filters still refresh every card.
        const chartOnly = salesOnly || bookingOnly || servicesOnly;
        if (chartOnly && root.getAttribute('aria-busy') === 'true') return;
        if (!chartOnly) requested = { ...period };
        if (!servicesOnly && serviceCard?.getAttribute('aria-busy') === 'true') {
            serviceGrouping.value = serviceCard.dataset.renderedGrouping || 'daily';
            serviceCard.querySelector('[data-service-chart-live]').textContent = '';
        }
        controller?.abort();
        // A newer chart request may cancel the other chart's request.
        // Release its controls before marking the new request as busy.
        bookingCard?.setAttribute('aria-busy', 'false');
        document.getElementById('bookingGroupingSelect').disabled = false;
        serviceCard?.setAttribute('aria-busy', 'false');
        if (serviceGrouping) serviceGrouping.disabled = false;
        const activeController = new AbortController();
        controller = activeController;
        salesCard.setAttribute('aria-busy', String(salesOnly));
        const regionKey = salesOnly ? 'sales' : bookingOnly ? 'bookings' : servicesOnly ? 'service-trend' : null;
        regionState('loading', regionKey);
        if (!chartOnly) {
            hideCategoryTooltip();
            root.setAttribute('aria-busy', 'true');
            document.dispatchEvent(new CustomEvent('campushub:dashboard-loading'));
            loading.hidden = false;
            error.hidden = true;
            if (lowStockError) lowStockError.hidden = true;
            if (recentOrdersError) recentOrdersError.hidden = true;
            refresh.disabled = true;
            refresh.setAttribute('aria-busy', 'true');
        } else if (salesOnly) {
            salesCard.querySelector('[data-sales-chart-live]').textContent = 'Updating Sales Trend.';
        } else if (servicesOnly) {
            serviceCard?.setAttribute('aria-busy', 'true');
            serviceGrouping.disabled = true;
            serviceCard.querySelector('[data-service-chart-live]').textContent = 'Updating Service Request Trend.';
        } else {
            bookingCard?.setAttribute('aria-busy', 'true');
            document.getElementById('bookingGroupingSelect').disabled = true;
            bookingCard.querySelector('[data-booking-chart-live]').textContent = 'Updating Booking Trend.';
        }
        if (!bookingOnly && !servicesOnly) {
            salesError.hidden = true;
            salesCard.removeAttribute('data-load-failed');
        }
        const url = new URL(controls.dataset.apiUrl, window.location.origin);
        // Preserve tab-specific admin authentication without moving credentials.
        const current = new URL(window.location.href);
        current.searchParams.forEach((value, key) => {
            if (!['period', 'start_date', 'end_date', 'date_from', 'date_to', 'sales_days', 'sales_period', 'date_range', 'facility_days', 'booking_days', 'sales_grouping', 'grouping', 'booking_grouping', 'service_grouping'].includes(key)) url.searchParams.set(key, value);
        });
        url.searchParams.set('period', chartOnly ? 'custom' : period.type);
        if (chartOnly || period.type === 'custom') {
            url.searchParams.set('start_date', period.start_date);
            url.searchParams.set('end_date', period.end_date);
        }
        url.searchParams.set('grouping', document.getElementById('salesGroupingSelect').value);
        url.searchParams.set('booking_grouping', document.getElementById('bookingGroupingSelect').value);
        if (serviceGrouping) url.searchParams.set('service_grouping', serviceGrouping.value);
        try {
            const response = await fetch(url, { headers: { Accept: 'application/json' }, cache: 'no-store', signal: activeController.signal });
            if (!response.ok) throw new Error('Dashboard request failed');
            const payload = await response.json();
            if (controller !== activeController) return;
            regionState('ready', regionKey);
            salesRetryOnly = false;
            bookingRetryOnly = false;
            serviceRetryOnly = false;
            if (servicesOnly) {
                document.dispatchEvent(new CustomEvent('campushub:service-trend-data', {detail: payload}));
                const displayUrl = new URL(window.location.href);
                displayUrl.searchParams.set('service_grouping', payload.executive.services.request_trend.grouping);
                history.replaceState({}, '', displayUrl);
                return;
            }
            if (bookingOnly) {
                document.dispatchEvent(new CustomEvent('campushub:booking-trend-data', { detail: payload }));
                const displayUrl = new URL(window.location.href);
                displayUrl.searchParams.set('booking_grouping', payload.facilities.booking_overview.grouping);
                history.replaceState({}, '', displayUrl);
                return;
            }
            if (salesOnly) {
                renderSalesTrend(payload);
                document.dispatchEvent(new CustomEvent('campushub:sales-trend-data', { detail: payload }));
                const displayUrl = new URL(window.location.href);
                displayUrl.searchParams.set('grouping', payload.grouping);
                history.replaceState({}, '', displayUrl);
                return;
            }
            render(payload);
            applied = payload.period;
            requested = { ...applied };
            select.value = applied.type;
            start.value = applied.start_date;
            end.value = applied.end_date;
            end.max = payload.last_updated.slice(0, 10);
            syncConstraints();
            custom.hidden = true;
            const displayUrl = new URL(window.location.href);
            ['period', 'start_date', 'end_date', 'date_from', 'date_to', 'sales_days', 'sales_period', 'date_range', 'facility_days', 'booking_days', 'sales_grouping', 'grouping', 'booking_grouping', 'service_grouping'].forEach((key) => displayUrl.searchParams.delete(key));
            url.searchParams.forEach((value, key) => displayUrl.searchParams.set(key, value));
            history.replaceState({}, '', displayUrl);
        } catch (exception) {
            if (exception.name !== 'AbortError' && controller === activeController) {
                regionState('error', regionKey);
                if (servicesOnly) {
                    serviceRetryOnly = true;
                    document.dispatchEvent(new CustomEvent('campushub:service-trend-error'));
                    return;
                }
                if (bookingOnly) {
                    bookingRetryOnly = true;
                    document.dispatchEvent(new CustomEvent('campushub:booking-trend-error'));
                    return;
                }
                salesRetryOnly = salesOnly;
                salesError.hidden = false;
                salesCard.setAttribute('data-load-failed', 'true');
                if (salesOnly) salesCard.querySelector('[data-sales-chart-live]').textContent = 'Sales Trend could not be updated. Please retry.';
                else {
                    restoreAppliedPeriod();
                    error.hidden = false;
                    if (kpiStale) kpiStale.hidden = false;
                    if (lowStockContent) lowStockContent.hidden = true;
                    if (lowStockError) lowStockError.hidden = false;
                    if (recentOrdersContent) recentOrdersContent.hidden = true;
                    if (recentOrdersError) recentOrdersError.hidden = false;
                    const ordersEmpty = root.querySelector('[data-recent-orders-empty]');
                    if (ordersEmpty) ordersEmpty.hidden = true;
                    document.dispatchEvent(new CustomEvent('campushub:dashboard-load-error'));
                }
            }
        } finally {
            if (controller === activeController) {
                for (const region of regions) if (region.dataset.requestState === 'loading') region.dataset.requestState = 'ready';
                salesCard.setAttribute('aria-busy', 'false');
                if (servicesOnly) {
                    serviceCard?.setAttribute('aria-busy', 'false');
                    serviceGrouping.disabled = false;
                } else if (bookingOnly) {
                    bookingCard?.setAttribute('aria-busy', 'false');
                    document.getElementById('bookingGroupingSelect').disabled = false;
                } else if (!salesOnly) {
                    root.setAttribute('aria-busy', 'false');
                    loading.hidden = true;
                    refresh.disabled = false;
                    refresh.setAttribute('aria-busy', 'false');
                }
            }
        }
    }
    select.addEventListener('change', () => {
        custom.hidden = select.value !== 'custom';
        if (select.value === 'custom') {
            syncConstraints();
            positionCustomRange();
            start.focus();
        } else load({ type: select.value });
    });
    form.addEventListener('submit', (event) => {
        event.preventDefault();
        if (select.value === 'custom') {
            if (!start.value || !end.value || start.value > end.value || end.value > end.max) {
                dateError.textContent = 'Enter a valid date range with start date on or before end date, ending today or earlier.';
                dateError.hidden = false;
                return;
            }
            load({ type: 'custom', start_date: start.value, end_date: end.value });
        } else load({ type: select.value });
    });
    document.getElementById('dashboardCancelRange').addEventListener('click', () => {
        restoreAppliedPeriod();
        select.focus();
    });
    custom.addEventListener('keydown', (event) => {
        if (event.key === 'Escape') {
            event.preventDefault();
            restoreAppliedPeriod();
            select.focus();
        }
    });
    refresh.addEventListener('click', () => load(applied));
    document.getElementById('dashboardRetry').addEventListener('click', () => load(requested));
    document.getElementById('salesOverviewRetry').addEventListener('click', () => load(salesRetryOnly ? applied : requested, salesRetryOnly));
    document.getElementById('lowStockRetry')?.addEventListener('click', () => load(requested));
    document.getElementById('bookingOverviewRetry')?.addEventListener('click', () => load(bookingRetryOnly ? applied : requested, false, bookingRetryOnly));
    document.getElementById('topProductsRetry')?.addEventListener('click', () => load(requested));
    document.getElementById('recentOrdersRetry')?.addEventListener('click', () => load(requested));
    document.getElementById('salesOverviewFilters').addEventListener('submit', (event) => {
        event.preventDefault();
        load(applied, true);
    });
    document.getElementById('salesGroupingSelect').addEventListener('change', () => {
        load(applied, true);
    });
    document.getElementById('bookingGroupingSelect').addEventListener('change', () => load(applied, false, true));
    serviceGrouping?.addEventListener('change', () => load(applied, false, false, true));
    document.getElementById('serviceTrendRetry')?.addEventListener('click', () => load(serviceRetryOnly ? applied : requested, false, false, serviceRetryOnly));
    document.getElementById('servicesOverviewRetry')?.addEventListener('click', () => load(requested));
});
