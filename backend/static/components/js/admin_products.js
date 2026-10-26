/** Keep http(s) URLs and base64 data URLs (uploaded images). */
function normalizeProductImageUrl(url) {
    const value = (url || '').trim();
    if (!value) return '';
    if (/^https?:\/\//i.test(value)) return value;
    if (/^data:image\//i.test(value)) return value;
    if (value.startsWith('/')) return value;
    return '';
}

function parseProductImagesJson(raw) {
    const value = (raw || '').trim();
    if (!value) return [];
    try {
        const parsed = JSON.parse(value);
        if (Array.isArray(parsed)) return parsed.filter(Boolean);
    } catch (_) {
        /* ignore */
    }
    try {
        const parsed = JSON.parse(value.replace(/\\u0022/g, '"'));
        if (Array.isArray(parsed)) return parsed.filter(Boolean);
    } catch (_) {
        /* ignore */
    }
    return [];
}

function parseProductImages(rawImages, fallbackUrl) {
    if (Array.isArray(rawImages) && rawImages.length) {
        return rawImages.filter(Boolean);
    }
    if (typeof rawImages === 'string') {
        const parsed = parseProductImagesJson(rawImages);
        if (parsed.length) return parsed;
    }
    const fallback = (fallbackUrl || '').trim();
    if (!fallback) return [];
    if (fallback.startsWith('[')) {
        return parseProductImagesJson(fallback);
    }
    return [fallback];
}

function productGalleryImageSrc(productId, index) {
    if (productId) {
        const path = `/api/products/${encodeURIComponent(productId)}/image/?index=${encodeURIComponent(index)}`;
        const session = window.CampusHubAdminSession;
        if (session?.urlWithToken) return session.urlWithToken(path);
        // An img cannot use the tab-auth fetch header; authorize only this
        // same-origin image endpoint through the established tab query token.
        const token = new URLSearchParams(window.location.search).get('__at');
        return token ? `${path}&__at=${encodeURIComponent(token)}` : path;
    }
    return '';
}

function resolveProductGalleryUrls(productId, rawImages, fallbackUrl) {
    const list = parseProductImages(rawImages, fallbackUrl);
    if (!list.length) return [];
    if (productId) {
        return list.map((_, index) => productGalleryImageSrc(productId, index));
    }
    return list.map((url) => normalizeProductImageUrl(url) || url).filter(Boolean);
}

async function fetchProductByIdFromServer(productId) {
    if (!productId) return null;
    try {
        const response = await fetch(`/api/marketplace/products/?product_id=${encodeURIComponent(productId)}`, {
            credentials: 'same-origin',
            headers: { Accept: 'application/json' },
        });
        if (!response.ok) return null;
        const data = await response.json();
        return (data.products || []).find((item) => String(item.id) === String(productId)) || null;
    } catch (_) {
        return null;
    }
}

async function fetchProductImagesFromServer(productId) {
    const product = await fetchProductByIdFromServer(productId);
    if (!product) return [];
    return parseProductImages(product.images, product.image_url);
}

function parseJsonDataset(raw) {
    const value = (raw || '').trim();
    if (!value) return null;
    try {
        return JSON.parse(value);
    } catch (_) {
        /* ignore */
    }
    try {
        return JSON.parse(value.replace(/\\u0022/g, '"'));
    } catch (_) {
        /* ignore */
    }
    return null;
}

function parseCustomizationOptions(raw) {
    const parsed = parseJsonDataset(raw);
    return Array.isArray(parsed) ? parsed : [];
}

function normalizeStatus(status) {
    return String(status || 'pending').trim().toLowerCase();
}

function getOptionNamesForGallery(customizationOptions) {
    const names = [];
    const groups = Array.isArray(customizationOptions) ? customizationOptions : [];
    groups.forEach((group) => {
        (group?.options || []).forEach((option) => {
            const name = (option?.name || '').trim();
            if (name) names.push(name);
        });
    });
    return names;
}

function getRowVariantGalleryUrls(row) {
    const productId = row?.dataset?.productId || '';
    const imageList = parseProductImagesJson(row?.dataset?.productImages || '');
    const fallback = row?.dataset?.productImageUrl || '';
    const urls = resolveProductGalleryUrls(productId, imageList, fallback);
    if (urls.length > 1) return urls;

    const variantNames = getOptionNamesForGallery(
        parseCustomizationOptions(row?.dataset?.customizationOptions || '')
    );
    if (productId && variantNames.length > 1) {
        return variantNames.map((_, index) => productGalleryImageSrc(productId, index));
    }
    return urls;
}

function getVariantNameForRowIndex(row, index) {
    const names = getOptionNamesForGallery(
        parseCustomizationOptions(row?.dataset?.customizationOptions || '')
    );
    return names[index] || '';
}

function escapeHtml(value) {
    return String(value ?? '')
        .replace(/&/g, '&amp;')
        .replace(/</g, '&lt;')
        .replace(/>/g, '&gt;')
        .replace(/"/g, '&quot;');
}

document.addEventListener('DOMContentLoaded', function () {
    const STORAGE_KEY = 'campushub_test_products';

    const PERISHABLE_CATEGORIES = new Set([
        'Rice Meals', 'Snacks', 'Desserts', 'Beverages', 'Combo Meals', 'Breakfast',
    ]);
    const LOW_STOCK_THRESHOLD = parseInt(
        document.querySelector('meta[name="low-stock-threshold"]')?.content || '5',
        10
    );
    const EXPIRY_WARNING_DAYS = parseInt(
        document.querySelector('meta[name="expiry-warning-days"]')?.content || '7',
        10
    );
    const INVENTORY_LABELS = {
        in_stock: 'In Stock',
        low_stock: 'Low Stock',
        out_of_stock: 'Out of Stock',
        partially_available: 'Partially Available',
        expiring_soon: 'Expiring Soon',
        expired: 'Expired',
    };
    const INVENTORY_PRIORITY = [
        'expired',
        'out_of_stock',
        'expiring_soon',
        'low_stock',
        'partially_available',
        'in_stock',
    ];

    const uploadInput = document.getElementById('productImageUpload');
    const uploadDropzone = document.getElementById('productImageDropzone');
    const uploadFileName = document.getElementById('productImageFileName');
    const productSaveToast = document.getElementById('productSaveToast');
    const saveProductButton = document.getElementById('saveProductButton');
    const addProductButton = document.getElementById('addProductButton');
    const productsSearchInput = document.getElementById('productsSearchInput');
    const productsTableBody = document.getElementById('productsTableBody');
    const productsListSection = document.getElementById('productsListSection');
    const productLoadingSection = document.getElementById('productLoadingSection');
    const productFormSection = document.getElementById('productFormSection');
    const productFormHeader = document.getElementById('productFormHeader');
    const productFormTitle = document.getElementById('productFormTitle');
    const statsGrid = document.getElementById('productStatsGrid');
    const currentUserDisplayName = document.querySelector('meta[name="current-user"]')?.content || '';
    const isSuperuser = document.querySelector('meta[name="is-superuser"]')?.content === 'true';
    const canManageProducts = document.querySelector('meta[name="can-manage-products"]')?.content === 'true';
    const canApproveProducts = document.querySelector('meta[name="can-approve-products"]')?.content === 'true';
    const productDescriptionField = document.getElementById('productDescription');

    if (productDescriptionField) {
        productDescriptionField.addEventListener('input', updateDescriptionCount);
    }

    let editingProductRow = null;
    let editingProductId = null;
    let pendingProductDecisionRow = null;
    let pendingProductDecision = '';
    const tableImageCycles = new WeakMap();

    function setProductImageFallback(image, failed) {
        image.hidden = failed;
        const fallback = image.parentElement?.querySelector('.product-table-image-empty');
        if (fallback) fallback.hidden = !failed;
    }
    productsTableBody?.addEventListener('error', (event) => {
        if (event.target.matches?.('img.product-table-image')) setProductImageFallback(event.target, true);
    }, true);
    productsTableBody?.addEventListener('load', (event) => {
        if (event.target.matches?.('img.product-table-image')) setProductImageFallback(event.target, false);
    }, true);

    function stopProductTableImageCycle(row) {
        const state = tableImageCycles.get(row);
        if (!state) return;
        if (state.timer) window.clearInterval(state.timer);
        if (state.cell && state.onEnter) state.cell.removeEventListener('mouseenter', state.onEnter);
        if (state.cell && state.onLeave) state.cell.removeEventListener('mouseleave', state.onLeave);
        tableImageCycles.delete(row);
    }

    function initProductTableImageCycle(row) {
        if (!row) return;
        stopProductTableImageCycle(row);

        const img = row.querySelector('.product-table-image:not(.product-table-image-empty)');
        const cell = row.querySelector('.product-name-cell');
        if (!img || !cell) return;

        const urls = getRowVariantGalleryUrls(row);
        img.referrerPolicy = 'no-referrer';
        if (urls[0] && img.getAttribute('src') !== urls[0]) img.src = urls[0];
        if (img.complete && !img.naturalWidth) setProductImageFallback(img, true);
        if (urls.length <= 1) return;

        const productName = cell.querySelector('strong')?.textContent?.trim() || img.alt || 'Product';
        const state = {
            idx: 0,
            timer: null,
            urls,
            cell,
            onEnter: null,
            onLeave: null,
        };

        function showIndex(nextIdx) {
            state.idx = ((nextIdx % urls.length) + urls.length) % urls.length;
            img.src = urls[state.idx];
            const variantName = getVariantNameForRowIndex(row, state.idx);
            img.alt = variantName ? `${productName} — ${variantName}` : productName;
            img.title = variantName || productName;
        }

        function startTimer(interval) {
            if (state.timer) window.clearInterval(state.timer);
            state.timer = window.setInterval(() => showIndex(state.idx + 1), interval);
        }

        state.onEnter = () => startTimer(1200);
        state.onLeave = () => {
            showIndex(0);
            startTimer(2800);
        };

        cell.addEventListener('mouseenter', state.onEnter);
        cell.addEventListener('mouseleave', state.onLeave);
        showIndex(0);
        startTimer(2800);
        tableImageCycles.set(row, state);
    }

    function initAllProductTableImageCycles() {
        if (!productsTableBody) return;
        productsTableBody.querySelectorAll('tr[data-product-id]').forEach(initProductTableImageCycle);
    }

    // â”€â”€ localStorage helpers â”€â”€
    function loadTestProducts() {
        try { return JSON.parse(localStorage.getItem(STORAGE_KEY)) || []; }
        catch { return []; }
    }

    function saveTestProducts(products) {
        try {
            localStorage.setItem(STORAGE_KEY, JSON.stringify(products));
        } catch (_) {}
    }

    function generateId() {
        return `test_${Date.now()}_${Math.random().toString(36).slice(2, 7)}`;
    }

    // â”€â”€ HTML helpers â”€â”€
    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, (c) =>
            ({ '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;' }[c]));
    }

    function normalizeStatus(status) {
        return String(status || 'pending').trim().toLowerCase();
    }

    function formatStatus(status) {
        const s = normalizeStatus(status);
        return s.split('-').map((part) => part.charAt(0).toUpperCase() + part.slice(1)).join(' ');
    }

    function isPerishableCategory(category) {
        return PERISHABLE_CATEGORIES.has(String(category || '').trim());
    }

    function formatIsoDate(date) {
        const year = date.getFullYear();
        const month = String(date.getMonth() + 1).padStart(2, '0');
        const day = String(date.getDate()).padStart(2, '0');
        return `${year}-${month}-${day}`;
    }

    function suggestedExpiryDate() {
        const date = new Date();
        date.setHours(0, 0, 0, 0);
        date.setDate(date.getDate() + EXPIRY_WARNING_DAYS);
        return formatIsoDate(date);
    }

    function computeInventoryStatus(stockValue, expiryValue, category, threshold = LOW_STOCK_THRESHOLD) {
        const stock = Number.isFinite(stockValue) ? stockValue : parseInt(String(stockValue || '0'), 10) || 0;
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        if (isPerishableCategory(category) && expiryValue) {
            const expiry = new Date(`${expiryValue}T00:00:00`);
            if (!Number.isNaN(expiry.getTime()) && expiry < today) {
                return 'expired';
            }
        }
        if (stock <= 0) return 'out_of_stock';
        if (stock <= threshold) return 'low_stock';
        if (isPerishableCategory(category) && expiryValue) {
            const expiry = new Date(`${expiryValue}T00:00:00`);
            if (!Number.isNaN(expiry.getTime())) {
                const daysLeft = Math.ceil((expiry - today) / 86400000);
                if (daysLeft <= EXPIRY_WARNING_DAYS) return 'expiring_soon';
            }
        }
        return 'in_stock';
    }

    function flattenCustomizationInventory(groups) {
        const items = [];
        (groups || []).forEach((group) => {
            (group.options || []).forEach((opt) => {
                if (!opt || typeof opt !== 'object' || !('stock' in opt)) return;
                items.push({
                    stock: parseInt(opt.stock, 10) || 0,
                    expiry_date: opt.expiry_date || '',
                    low_stock_threshold: opt.low_stock_threshold ?? LOW_STOCK_THRESHOLD,
                });
            });
        });
        return items;
    }

    function worstInventoryStatus(statuses) {
        for (const status of INVENTORY_PRIORITY) {
            if (statuses.includes(status)) return status;
        }
        return 'in_stock';
    }

    function computeAvailabilityFromOptions(items, category) {
        if (!items.length) return 'in_stock';

        const statuses = items.map((item) =>
            computeInventoryStatus(item.stock, item.expiry_date, category, item.low_stock_threshold)
        );
        const stocks = items.map((item) => item.stock);

        if (stocks.every((stock) => stock <= 0)) return 'out_of_stock';

        if (stocks.some((stock) => stock <= 0) && stocks.some((stock) => stock > 0)) {
            const worst = worstInventoryStatus(statuses.filter((status, index) => stocks[index] > 0));
            if (['in_stock', 'low_stock', 'expiring_soon'].includes(worst)) {
                return 'partially_available';
            }
            return worst;
        }

        return worstInventoryStatus(statuses);
    }

    function customizationHasStockTracking(options) {
        return (options || []).some((group) =>
            (group?.options || []).some((opt) => opt && typeof opt === 'object' && 'stock' in opt)
        );
    }

    function hasCustomizationOptions(product = {}) {
        return (product.customization_options || []).some(
            (group) => (group?.options || []).some((opt) => opt && typeof opt === 'object')
        );
    }

    function hasVariantInventory(product = {}) {
        if (!customizationHasStockTracking(product.customization_options)) return false;
        return flattenCustomizationInventory(product.customization_options).length > 0;
    }

    function computeProductAvailability(product = {}) {
        const category = product.category || '';
        const options = product.customization_options || [];
        if (product.customization_enabled && hasCustomizationOptions(product)) {
            if (customizationHasStockTracking(options)) {
                return computeAvailabilityFromOptions(
                    flattenCustomizationInventory(options),
                    category
                );
            }
            return 'in_stock';
        }
        if (hasVariantInventory(product)) {
            return computeAvailabilityFromOptions(
                flattenCustomizationInventory(options),
                category
            );
        }
        return computeInventoryStatus(product.stock, product.expiry_date, category, product.low_stock_threshold ?? LOW_STOCK_THRESHOLD);
    }

    function deriveStockFromCustomization(customizationData, fallbackStock) {
        const items = flattenCustomizationInventory(customizationData.customization_options);
        if (items.length) {
            return items.reduce((sum, item) => sum + (parseInt(item.stock, 10) || 0), 0);
        }
        return parseInt(fallbackStock, 10) || 0;
    }

    function deriveExpiryFromCustomization(customizationData, category, fallbackExpiry) {
        if (!isPerishableCategory(category)) return '';
        const items = flattenCustomizationInventory(customizationData.customization_options);
        if (items.length) {
            const dates = items.map((item) => item.expiry_date).filter(Boolean);
            if (!dates.length) return '';
            return dates.sort()[0];
        }
        return fallbackExpiry || '';
    }

    function computeTotalStock(product = {}) {
        const options = product.customization_options || [];
        if (customizationHasStockTracking(options)) {
            const items = flattenCustomizationInventory(options);
            return items.reduce((sum, item) => sum + Math.max(0, parseInt(item.stock, 10) || 0), 0);
        }
        // Options without tracked stock do not create available units.
        return Math.max(0, parseInt(product.stock, 10) || 0);
    }

    function inventoryStatusLabel(status) {
        return INVENTORY_LABELS[status] || 'In Stock';
    }

    function renderInventoryPill(status) {
        const safeStatus = escapeHtml(status || 'in_stock');
        return `<span class="inventory-pill inventory-${safeStatus}">${escapeHtml(inventoryStatusLabel(status))}</span>`;
    }

    function countProductVariants(product = {}) {
        if (hasVariantInventory(product)) return flattenCustomizationInventory(product.customization_options).length;
        const serverCount = parseInt(product.variant_count, 10);
        if (Number.isFinite(serverCount) && serverCount >= 0) return serverCount;
        return flattenCustomizationInventory(product.customization_options || []).length;
    }

    function formatProductPriceDisplay(product = {}) {
        if (product.price_display) return String(product.price_display);
        const basePrice = Number.parseFloat(product.price) || 0;
        if (!product.customization_enabled) {
            return `\u20B1${basePrice.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        }

        let minimumExtra = 0;
        let maximumExtra = 0;
        (product.customization_options || []).forEach((group) => {
            const extras = (group?.options || [])
                .map((option) => Math.max(0, Number.parseFloat(option?.extra_price) || 0));
            if (!extras.length) return;
            if (group.required) minimumExtra += Math.min(...extras);
            maximumExtra += group.selection === 'multiple'
                ? extras.reduce((sum, value) => sum + value, 0)
                : Math.max(...extras);
        });

        const format = (value) => `\u20B1${value.toLocaleString('en-PH', { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        const minimum = basePrice + minimumExtra;
        const maximum = basePrice + maximumExtra;
        return minimum === maximum ? format(minimum) : `${format(minimum)} \u2013 ${format(maximum)}`;
    }

    function renderStatusPill(status) {
        const s = normalizeStatus(status);
        const icons = {
            pending: '<svg class="status-icon" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>',
            rejected: '<svg class="status-icon" aria-hidden="true" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="2" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m9.75 9.75 4.5 4.5m0-4.5-4.5 4.5M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>'
        };
        return `<span class="status-pill status-${escapeHtml(s)}">${icons[s] || ''}<span>${escapeHtml(formatStatus(s))}</span></span>`;
    }

    function renderInventoryPill(status) {
        const s = (status || 'in_stock').toLowerCase();
        let label = 'In Stock';
        if (s === 'low_stock') label = 'Low Stock';
        else if (s === 'out_of_stock') label = 'Out of Stock';
        return `<span class="inventory-pill inventory-${escapeHtml(s)}">${escapeHtml(label)}</span>`;
    }

    function computeProductQuantityStatus(product) {
        const stock = computeTotalStock(product);
        if (stock <= 0) return 'out_of_stock';
        if (product.product_type === 'bundle') return 'in_stock';
        if (hasVariantInventory(product)) {
            return flattenCustomizationInventory(product.customization_options).some(item =>
                item.stock > 0 && item.stock <= item.low_stock_threshold) ? 'low_stock' : 'in_stock';
        }
        return computeInventoryStatus(stock, '', '', product.low_stock_threshold ?? LOW_STOCK_THRESHOLD);
    }

    function renderInventorySummary(totalStock, variantCount, product = {}) {
        const safeStock = Math.max(0, parseInt(totalStock, 10) || 0);
        if (product.product_type === 'bundle') return `<div class="inventory-summary-clean"><span class="inventory-number">${safeStock} bundle${safeStock === 1 ? '' : 's'} available</span><span class="inventory-threshold">Derived from components</span></div>`;
        // Use the parent quantity, not approval or the worst individual variant.
        const quantityState = computeProductQuantityStatus({ ...product, stock: safeStock });
        const secondary = [];
        const variants = Math.max(0, parseInt(variantCount, 10) || 0);
        if (variants > 0) secondary.push(`<span class="inventory-variant-sub">${variants} variant${variants === 1 ? '' : 's'}</span>`);
        const lowVariants = hasVariantInventory(product) ? flattenCustomizationInventory(product.customization_options).filter(item => item.stock > 0 && item.stock <= item.low_stock_threshold).length : 0;
        if (quantityState === 'low_stock') secondary.push(`<span class="inventory-warning low-stock"><span class="inventory-warning-dot" aria-hidden="true"></span>${lowVariants ? `${lowVariants} variant${lowVariants === 1 ? '' : 's'} Low Stock` : 'Low Stock'}</span>`);
        else if (quantityState === 'out_of_stock') secondary.push('<span class="inventory-warning out-of-stock"><span class="inventory-warning-dot" aria-hidden="true"></span>Out of Stock</span>');
        return `<div class="inventory-summary-clean">
            <span class="inventory-number">${safeStock} ${safeStock === 1 ? 'pc' : 'pcs'}</span>
            ${hasVariantInventory(product) ? '' : `<span class="inventory-threshold">Threshold: ${escapeHtml(String(product.low_stock_threshold ?? LOW_STOCK_THRESHOLD))}</span>`}
            ${secondary.length ? `<span class="inventory-secondary${variants ? ' inventory-secondary--variants' : ''}">${secondary.join(variants ? '' : '<span aria-hidden="true">&middot;</span>')}</span>` : ''}
        </div>`;
    }

    function formatExpiryDisplay(expiryValue) {
        if (!expiryValue) return '<span class="expiry-empty">â€”</span>';
        const date = new Date(`${expiryValue}T00:00:00`);
        if (Number.isNaN(date.getTime())) return '<span class="expiry-empty">â€”</span>';
        const label = date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
        return `<strong>${escapeHtml(label)}</strong>`;
    }

    let activeInventoryFilter = '';
    let activeStatFilter = '';

    function updateStatCardActiveState() {
        const grid = document.getElementById('productStatsGrid');
        if (grid) {
            grid.dataset.activeFilter = activeStatFilter || activeInventoryFilter || '';
        }
        document.querySelectorAll('#productStatsGrid [data-stat-filter]').forEach((card) => {
            const key = card.dataset.statFilter || '';
            // Total ("all") is never highlighted — only Pending / Approved / Low Stock
            const isActive = key !== 'all' && Boolean(activeStatFilter) && activeStatFilter === key;
            card.classList.toggle('is-active', isActive);
            card.setAttribute('aria-pressed', String(isActive));
        });
    }

    function setInventoryFilter(value = '') {
        activeInventoryFilter = value || '';
        const isActive = activeInventoryFilter === 'low_stock';

        if (isActive) {
            activeStatFilter = 'low_stock';
        } else if (activeStatFilter === 'low_stock') {
            activeStatFilter = '';
        }

        updateStatCardActiveState();
        applyInlineFilters();
    }

    function applyStatCardFilter(filterKey = '') {
        const statusFilterEl = document.getElementById('productsStatusFilter');
        const key = filterKey || 'all';

        // Total clears filters and does not stay active.
        // Pending / Approved / Low Stock toggle on/off.
        let nextKey = '';
        if (key === 'all') {
            nextKey = '';
        } else if (activeStatFilter === key) {
            nextKey = '';
        } else {
            nextKey = key;
        }

        activeStatFilter = nextKey;
        activeInventoryFilter = nextKey === 'low_stock' ? 'low_stock' : '';
        window.__chProductStatFilter = nextKey;

        if (statusFilterEl) {
            statusFilterEl.value = (nextKey === 'pending' || nextKey === 'approved') ? nextKey : '';
        }

        // Force-clear other card active states before applying the new one
        document.querySelectorAll('#productStatsGrid [data-stat-filter]').forEach((card) => {
            card.classList.remove('is-active');
            card.setAttribute('aria-pressed', 'false');
        });
        updateStatCardActiveState();
        applyInlineFilters();
        if (typeof window.__chSyncProductEmptyState === 'function') {
            window.__chSyncProductEmptyState();
        }

        // Scroll Products List into view (header scrolls with page — no sticky offset)
        if (nextKey === 'pending' || nextKey === 'low_stock' || nextKey === 'approved') {
            scrollProductsListIntoView();
        }
    }

    function getScrollParent(el) {
        let node = el && el.parentElement;
        while (node && node !== document.body) {
            const style = window.getComputedStyle(node);
            const overflowY = style.overflowY;
            if ((overflowY === 'auto' || overflowY === 'scroll') && node.scrollHeight > node.clientHeight) {
                return node;
            }
            node = node.parentElement;
        }
        return document.scrollingElement || document.documentElement;
    }

    function scrollProductsListIntoView() {
        const listSection = document.getElementById('productsListSection');
        if (!listSection) return;

        const run = () => {
            const scrollParent = getScrollParent(listSection);
            const sectionRect = listSection.getBoundingClientRect();
            const gap = 12;

            if (scrollParent === document.scrollingElement || scrollParent === document.documentElement || scrollParent === document.body) {
                const top = window.scrollY + sectionRect.top - gap;
                window.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
                return;
            }

            const parentRect = scrollParent.getBoundingClientRect();
            const top = scrollParent.scrollTop + (sectionRect.top - parentRect.top) - gap;
            scrollParent.scrollTo({ top: Math.max(0, top), behavior: 'smooth' });
        };

        requestAnimationFrame(() => {
            requestAnimationFrame(run);
            setTimeout(run, 80);
        });
    }

    function automationHeaderIcon(status) {
        if (status === 'out_of_stock' || status === 'expired') {
            return `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"/></svg>`;
        }
        if (status === 'low_stock' || status === 'expiring_soon') {
            return `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"/></svg>`;
        }
        return `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z"/></svg>`;
    }

    function automationNoteIcon(type) {
        if (type === 'danger' || type === 'caution') {
            return `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 9v3.75m-9.303 3.376c-.866 1.5.217 3.374 1.948 3.374h14.71c1.73 0 2.813-1.874 1.948-3.374L13.949 3.378c-.866-1.5-3.032-1.5-3.898 0L2.697 16.126ZM12 15.75h.007v.008H12v-.008Z"/></svg>`;
        }
        return `<svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="m11.25 11.25.041-.02a.75.75 0 0 1 1.063.852l-.708 2.836a.75.75 0 0 0 1.063.853l.041-.021M21 12a9 9 0 1 1-18 0 9 9 0 0 1 18 0Zm-9-3.75h.008v.008H12V8.25Z"/></svg>`;
    }

    function automationMessageType(message) {
        const text = String(message || '').toLowerCase();
        if (text.includes('out of stock') || text.includes('in the past') || text.includes('hidden from')) {
            return 'danger';
        }
        if (text.includes('low stock') || text.includes('expires in') || text.includes('fifo priority')) {
            return 'caution';
        }
        return 'note';
    }

    function renderAutomationMessage(message) {
        const type = automationMessageType(message);
        return `
            <li class="product-inventory-note product-inventory-note-${type}">
                <span class="product-inventory-note-icon" aria-hidden="true">${automationNoteIcon(type)}</span>
                <span>${escapeHtml(message)}</span>
            </li>`;
    }

    function updateProductFormAutomation() {
        const expiryField = document.getElementById('productExpiryDate');
        const expiryWrap = document.getElementById('productExpiryFieldWrap');
        const categoryInput = document.getElementById('productCategoryInput');
        const category = categoryInput ? categoryInput.value : '';
        const perishable = isPerishableCategory(category);
        if (expiryWrap) {
            // Always show expiry date field
        }
    }

    function bindProductFormAutomation() {
        const categoryField = document.getElementById('productCategory');
        const stockField = document.getElementById('productStock');
        const expiryField = document.getElementById('productExpiryDate');
        const suggestBtn = document.getElementById('productSuggestExpiryBtn');

        [categoryField, stockField, expiryField].forEach((field) => {
            field?.addEventListener('input', updateProductFormAutomation);
            field?.addEventListener('change', updateProductFormAutomation);
        });

        if (suggestBtn && expiryField) {
            suggestBtn.addEventListener('click', () => {
                expiryField.value = suggestedExpiryDate();
                updateProductFormAutomation();
            });
        }

        updateProductFormAutomation();
    }

    bindProductFormAutomation();

    const PRODUCT_CATEGORIES = [
        'Rice Meals', 'Snacks', 'Desserts', 'Beverages', 'Combo Meals', 'Breakfast',
        'School Supplies', 'Electronics', 'Clothing', 'Accessories',
        'Personal Care', 'Services', 'Stationery', 'Books',
        'Home & Living', 'Sports', 'Others'
    ];

    function getSelectedCategory() {
        const hiddenValue = document.getElementById('productCategory')?.value?.trim() || '';
        if (hiddenValue) return hiddenValue;

        const inputValue = document.getElementById('productCategoryInput')?.value?.trim() || '';
        if (!inputValue) return '';

        const exact = PRODUCT_CATEGORIES.find(
            (category) => category.toLowerCase() === inputValue.toLowerCase()
        );
        return exact || inputValue;
    }

    function syncCategoryFields() {
        const hiddenField = document.getElementById('productCategory');
        const inputField = document.getElementById('productCategoryInput');
        if (!hiddenField || !inputField) return;

        const resolved = getSelectedCategory();
        if (resolved) {
            hiddenField.value = resolved;
            inputField.value = resolved;
        }
    }

    function notifyCategoryChanged() {
        syncCategoryFields();
        updateProductFormAutomation();
        updateCustomizationPanelVisibility();
    }

    function setCategoryValue(category) {
        const hiddenField = document.getElementById('productCategory');
        const inputField = document.getElementById('productCategoryInput');
        if (hiddenField) hiddenField.value = category || '';
        if (inputField) inputField.value = category || '';
    }

    // ── Category Searchable Combobox ──
    (function initCategoryCombobox() {
        const input = document.getElementById('productCategoryInput');
        const hidden = document.getElementById('productCategory');
        const dropdown = document.getElementById('categoryDropdown');
        if (!input || !dropdown || !hidden) return;

        function renderDropdown(filter) {
            const matches = (window.LocalAutocomplete && filter)
                ? window.LocalAutocomplete.suggest(PRODUCT_CATEGORIES, filter, 12)
                : (filter
                    ? PRODUCT_CATEGORIES.filter((c) => c.toLowerCase().includes(String(filter).toLowerCase()))
                    : PRODUCT_CATEGORIES);

            if (!matches.length) {
                dropdown.innerHTML = '<div class="category-dropdown-empty">No matching category</div>';
            } else {
                dropdown.innerHTML = matches.map(c =>
                    `<button type="button" class="category-dropdown-item" data-value="${c}">${c}</button>`
                ).join('');
            }
        }

        function open() {
            renderDropdown(input.value);
            dropdown.classList.add('is-open');
        }

        function close() {
            dropdown.classList.remove('is-open');
        }

        function select(value) {
            input.value = value;
            hidden.value = value;
            close();
            notifyCategoryChanged();
        }

        input.addEventListener('focus', () => {
            input.select();
            open();
        });
        input.addEventListener('input', () => {
            hidden.value = input.value.trim();
            renderDropdown(input.value);
            dropdown.classList.add('is-open');
            updateCustomizationPanelVisibility();
        });

        input.addEventListener('blur', () => {
            setTimeout(() => {
                const typed = input.value.trim();
                if (typed) {
                    const exact = PRODUCT_CATEGORIES.find(
                        (category) => category.toLowerCase() === typed.toLowerCase()
                    );
                    hidden.value = exact || typed;
                    if (exact) input.value = exact;
                } else {
                    hidden.value = '';
                }
                updateCustomizationPanelVisibility();
            }, 200);
        });

        dropdown.addEventListener('click', (e) => {
            const item = e.target.closest('.category-dropdown-item');
            if (item) select(item.dataset.value);
        });

        document.addEventListener('click', (e) => {
            if (!e.target.closest('#categoryCombobox')) close();
        });

        input.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') close();
            if (e.key === 'Enter') {
                e.preventDefault();
                const first = dropdown.querySelector('.category-dropdown-item');
                if (first) select(first.dataset.value);
            }
        });
    })();

    // ── Product Name local autocomplete (no API) ──
    (function initProductNameAutocomplete() {
        const input = document.getElementById('productName');
        const dropdown = document.getElementById('productNameDropdown');
        const wrap = document.getElementById('productNameCombobox');
        if (!input || !dropdown || !wrap) return;

        const samples = (window.LocalAutocomplete && window.LocalAutocomplete.PRODUCT_NAME_SAMPLES)
            || [];

        function renderDropdown(filter) {
            if (!window.LocalAutocomplete || !samples.length) {
                dropdown.innerHTML = '';
                dropdown.classList.remove('is-open');
                return;
            }
            const q = String(filter || '').trim();
            if (!q) {
                dropdown.innerHTML = '';
                dropdown.classList.remove('is-open');
                return;
            }
            const matches = window.LocalAutocomplete.suggest(samples, q, 8);
            if (!matches.length) {
                dropdown.innerHTML = '<div class="category-dropdown-empty">No matching name</div>';
            } else {
                dropdown.innerHTML = matches.map((name) =>
                    `<button type="button" class="category-dropdown-item" data-value="${name}">${name}</button>`
                ).join('');
            }
            dropdown.classList.add('is-open');
        }

        function close() {
            dropdown.classList.remove('is-open');
        }

        function select(value) {
            input.value = value;
            close();
            input.dispatchEvent(new Event('input', { bubbles: true }));
        }

        input.addEventListener('input', () => renderDropdown(input.value));
        input.addEventListener('focus', () => {
            if (input.value.trim()) renderDropdown(input.value);
        });
        dropdown.addEventListener('click', (e) => {
            const item = e.target.closest('.category-dropdown-item');
            if (item) select(item.dataset.value);
        });
        document.addEventListener('click', (e) => {
            if (!e.target.closest('#productNameCombobox')) close();
        });
        input.addEventListener('keydown', (e) => {
            if (e.key === 'Escape') close();
            if (e.key === 'Enter') {
                const first = dropdown.querySelector('.category-dropdown-item');
                if (first && dropdown.classList.contains('is-open')) {
                    e.preventDefault();
                    select(first.dataset.value);
                }
            }
        });
    })();

    const FOOD_CATEGORIES = [
        'Rice Meals', 'Snacks', 'Desserts', 'Beverages', 'Combo Meals', 'Breakfast',
    ];

    function isFoodCategory(category) {
        return FOOD_CATEGORIES.includes((category || '').trim());
    }

    function appendCustomizationGroup(group = {}) {
        const groupsRoot = document.getElementById('productCustomizationGroups');
        if (!groupsRoot) return null;
        const element = createCustomizationGroupElement(group);
        groupsRoot.appendChild(element);
        updateCustomizationPanelVisibility();
        return element;
    }

    function setOptionRowImage(row, imageUrl) {
        if (!row) return;
        const preview = row.querySelector('.customization-option-image-preview');
        const placeholder = row.querySelector('.customization-option-image-placeholder');
        const url = normalizeProductImageUrl(imageUrl) || String(imageUrl || '').trim();
        if (url) {
            row.dataset.optionImage = url;
            if (preview) {
                preview.src = url;
                preview.hidden = false;
            }
            if (placeholder) placeholder.hidden = true;
        } else {
            delete row.dataset.optionImage;
            if (preview) {
                preview.removeAttribute('src');
                preview.hidden = true;
            }
            if (placeholder) placeholder.hidden = false;
        }
    }

    function bindOptionImageInput(row) {
        const input = row?.querySelector('.customization-option-image-input');
        if (!input || input.dataset.bound === '1') return;
        input.dataset.bound = '1';
        input.addEventListener('change', () => {
            const file = input.files && input.files[0];
            if (!file || !validProductImageFile(file)) { input.value = ''; return; }
            const reader = new FileReader();
            reader.onerror = () => showProductSaveToast('Unable to read variant image. Please choose it again.', 'error');
            reader.onload = (e) => setOptionRowImage(row, e.target.result);
            reader.readAsDataURL(file);
        });
    }

    function collectVariantOptionImages() {
        const groupsRoot = document.getElementById('productCustomizationGroups');
        if (!groupsRoot) return [];
        const images = [];
        groupsRoot.querySelectorAll('.customization-option-row').forEach((row) => {
            const name = row.querySelector('.customization-option-name')?.value.trim() || '';
            if (!name) return;
            const image = row.dataset.optionImage || '';
            if (image) images.push(image);
        });
        return images;
    }

    function applyImagesToVariantOptions(images = []) {
        const groupsRoot = document.getElementById('productCustomizationGroups');
        if (!groupsRoot) return;
        const list = Array.isArray(images) ? images.filter(Boolean) : [];
        const rows = Array.from(groupsRoot.querySelectorAll('.customization-option-row'));
        if (list.length !== rows.length) return; // A sparse gallery cannot identify a missing option image.
        rows.forEach((row, index) => {
            if (row.dataset.imageManaged === '1' || row.dataset.optionImage) return;
            setOptionRowImage(row, list[index] || '');
        });
    }

    function createCustomizationGroupElement(group = {}) {
        const template = document.getElementById('variantGroupTemplate');
        const wrap = template.content.firstElementChild.cloneNode(true);

        const nameInput = wrap.querySelector('.customization-group-name');
        if (nameInput && group.name) nameInput.value = group.name;

        const selectionSelect = wrap.querySelector('.customization-group-selection');
        if (selectionSelect && group.selection === 'multiple') selectionSelect.value = 'multiple';

        const requiredSelect = wrap.querySelector('.customization-group-required');
        if (requiredSelect) requiredSelect.value = group.required === false ? 'no' : 'yes';

        const optionsList = wrap.querySelector('.customization-options-list');
        const optionTemplate = document.getElementById('variantOptionTemplate');
        const defaultOptions = [
            { name: '', stock: '0', extra_price: '0' },
        ];
        const options = Array.isArray(group.options) && group.options.length
            ? group.options
            : defaultOptions;
        options.forEach((option) => {
            const row = optionTemplate.content.firstElementChild.cloneNode(true);
            row.dataset.existingOption = option.name ? '1' : '0';
            row.dataset.imageManaged = Object.prototype.hasOwnProperty.call(option, 'image') ? '1' : '0';
            const nameField = row.querySelector('.customization-option-name');
            const stockField = row.querySelector('.customization-option-stock');
            const thresholdField = row.querySelector('.customization-option-threshold');
            const expiryField = row.querySelector('.customization-option-expiry');
            const priceField = row.querySelector('.customization-option-price');
            if (nameField && option.name) nameField.value = option.name;
            if (stockField) stockField.value = option.name && option.stock == null ? '' : (option.stock ?? '0');
            if (thresholdField) thresholdField.value = option.low_stock_threshold ?? LOW_STOCK_THRESHOLD;
            if (expiryField && option.expiry_date) expiryField.value = option.expiry_date;
            row.dataset.priceOffset = option.extra_price ?? '0';
            if (priceField) priceField.value = (Number(document.getElementById('productPrice')?.value || 0) + Number(option.extra_price || 0)).toFixed(2);
            setOptionRowImage(row, option.image || '');
            updateVariantState(row);
            bindOptionImageInput(row);
            optionsList.appendChild(row);
        });

        return wrap;
    }

    function updateVariantState(row) {
        const stockField = row.querySelector('.customization-option-stock');
        const thresholdField = row.querySelector('.customization-option-threshold');
        const stock = stockField?.value;
        const threshold = thresholdField?.value;
        const stateEl = row.querySelector('.customization-option-state');
        if (!stateEl) return;
        const initial = !editingProductId || row.dataset.existingOption !== '1';
        const ready = Boolean(row.querySelector('.customization-option-name')?.value.trim())
            && stock !== '' && threshold !== '' && stockField?.validity.valid && thresholdField?.validity.valid
            && Number.isInteger(Number(stock)) && Number(stock) >= 0 && Number(stock) <= 2147483647
            && Number.isInteger(Number(threshold)) && Number(threshold) >= 0 && Number(threshold) <= 2147483647
            && (!initial || Number(threshold) < Number(stock) || (Number(stock) === 0 && Number(threshold) === 0));
        const state = ready ? computeInventoryStatus(stock, '', '', Number(threshold)) : '';
        stateEl.textContent = state ? ({ in_stock: 'In Stock', low_stock: 'Low Stock', out_of_stock: 'Out of Stock' }[state] || '') : 'Enter valid option details';
        stateEl.className = `customization-option-state pd-inventory-state pd-inventory-state--${state}`;
    }

    function renumberVariationGroups() {
        const groupsRoot = document.getElementById('productCustomizationGroups');
        if (!groupsRoot) return;
        groupsRoot.querySelectorAll('.customization-group').forEach((group, i) => {
            const title = group.querySelector('.variant-group-title');
            if (title) title.textContent = `Variation Group #${i + 1}`;
        });
        toggleStockExpiryFields();
    }

    function toggleStockExpiryFields() {
        const groupsRoot = document.getElementById('productCustomizationGroups');
        const hasVariants = groupsRoot && groupsRoot.querySelectorAll('.customization-group').length > 0;
        const priceLabel = document.getElementById('productPriceLabel');
        if (priceLabel) priceLabel.innerHTML = `${hasVariants ? 'Base Price' : 'Price'} (₱) <span class="required-asterisk">*</span>`;
        const isBundle = document.getElementById('productTypeBundle')?.checked;
        const priceHelper = document.getElementById('variantPriceHelper');
        if (priceHelper) priceHelper.hidden = !hasVariants || isBundle;
        const stockWrap = document.getElementById('productStockFieldWrap');
        const thresholdWrap = document.getElementById('productThresholdFieldWrap');
        const expiryWrap = document.getElementById('productExpiryFieldWrap');
        if (stockWrap) stockWrap.style.display = hasVariants || isBundle ? 'none' : '';
        if (thresholdWrap) thresholdWrap.style.display = hasVariants || isBundle ? 'none' : '';
        const stockInput = document.getElementById('productStock');
        const thresholdInput = document.getElementById('productLowStockThreshold');
        [stockInput, thresholdInput].forEach(input => {
            if (input) {
                input.required = !hasVariants && !isBundle;
                input.disabled = Boolean(hasVariants || isBundle);
            }
        });
        if (expiryWrap) expiryWrap.style.display = hasVariants || isBundle ? 'none' : '';
        window.CampusHubBundles?.syncType();
        // Product Images (section 1) always stays visible
        const imagesSection = document.getElementById('productImagesSection');
        if (imagesSection) imagesSection.style.display = '';
        const topRow = document.querySelector('.create-product-row-top');
        if (topRow) topRow.classList.remove('has-variants-only');
    }

    function validateThresholdForm(customizationData) {
        const groups = document.getElementById('productCustomizationGroups');
        const rows = [...(groups?.querySelectorAll('.customization-option-row') || [])];
        const hasGroups = Boolean(groups?.querySelector('.customization-group'));
        if (hasGroups && !customizationData.customization_enabled) {
            showProductSaveToast('Enter a variation group name and at least one option, or remove the empty group.', 'error');
            return false;
        }
        const inputs = hasGroups ? rows.filter(row => row.querySelector('.customization-option-name')?.value.trim()).map(row => ({
            stock: row.querySelector('.customization-option-stock'),
            threshold: row.querySelector('.customization-option-threshold'),
            initial: !editingProductId || row.dataset.existingOption !== '1',
        })) : [{ stock: document.getElementById('productStock'),
                 threshold: document.getElementById('productLowStockThreshold'), initial: !editingProductId }];
        for (const { stock, threshold, initial } of inputs) {
            stock.required = true;
            threshold.setCustomValidity('');
            if (!stock.reportValidity() || !threshold.reportValidity()) return false;
            const stockValue = Number(stock.value), thresholdValue = Number(threshold.value);
            if (!Number.isInteger(thresholdValue) || thresholdValue < 0) {
                threshold.setCustomValidity('Low Stock Threshold must be a whole number of 0 or greater.');
            } else if (initial && thresholdValue >= stockValue && !(stockValue === 0 && thresholdValue === 0)) {
                threshold.setCustomValidity('Low Stock Threshold must be lower than the initial stock quantity.');
            }
            if (!threshold.checkValidity()) {
                document.getElementById('productThresholdError').textContent = threshold.validationMessage;
                threshold.reportValidity();
                return false;
            }
        }
        for (const row of rows.filter(row => row.querySelector('.customization-option-name')?.value.trim())) {
            const price = row.querySelector('.customization-option-price');
            price.setCustomValidity(Number(price.value) < Number(document.getElementById('productPrice').value || 0) ? 'Variant Price must be at least the base price. Set the base price to the lowest variant price.' : '');
            if (!price.reportValidity()) return false;
        }
        document.getElementById('productThresholdError').textContent = '';
        return true;
    }

    document.addEventListener('input', event => {
        if (event.target.matches('#productStock, #productLowStockThreshold, .customization-option-stock, .customization-option-threshold')) {
            document.querySelectorAll('#productLowStockThreshold, .customization-option-threshold').forEach(input => input.setCustomValidity(''));
            document.getElementById('productThresholdError').textContent = '';
        }
        const row = event.target.closest('.customization-option-row');
        if (row) {
            updateVariantState(row);
            if (event.target.matches('.customization-option-price')) {
                event.target.setCustomValidity('');
                row.dataset.priceOffset = String(Number(event.target.value) - Number(document.getElementById('productPrice').value || 0));
            }
        }
        if (event.target.id === 'productPrice') document.querySelectorAll('.customization-option-row').forEach(row => {
            const price = row.querySelector('.customization-option-price');
            price.value = (Number(event.target.value || 0) + Number(row.dataset.priceOffset || 0)).toFixed(2);
            price.setCustomValidity('');
        });
    });
    document.querySelectorAll('input[name="productType"]').forEach(input => input.addEventListener('change', toggleStockExpiryFields));

    function updateCustomizationPanelVisibility() {
        syncCategoryFields();
        toggleStockExpiryFields();
    }

    function readCustomizationFromForm() {
        const groupsRoot = document.getElementById('productCustomizationGroups');
        if (!groupsRoot) {
            return { customization_enabled: false, customization_options: [] };
        }

        const groups = [];
        groupsRoot.querySelectorAll('.customization-group').forEach((groupEl) => {
            const name = groupEl.querySelector('.customization-group-name')?.value.trim() || '';
            const selection = groupEl.querySelector('.customization-group-selection')?.value || 'single';
            const options = [];
            groupEl.querySelectorAll('.customization-option-row').forEach((row) => {
                const optionName = row.querySelector('.customization-option-name')?.value.trim() || '';
                const optionStock = row.querySelector('.customization-option-stock')?.value || '0';
                const optionThreshold = row.querySelector('.customization-option-threshold')?.value;
                const optionExpiry = row.querySelector('.customization-option-expiry')?.value || '';
                const extraPrice = (Number(row.querySelector('.customization-option-price')?.value || 0) - Number(document.getElementById('productPrice').value || 0)).toFixed(2);
                if (optionName) {
                    options.push({ name: optionName, stock: optionStock, low_stock_threshold: optionThreshold, expiry_date: optionExpiry, extra_price: extraPrice, image: row.dataset.optionImage || '' });
                }
            });
            if (name && options.length) {
                const requiredEl = groupEl.querySelector('.customization-group-required');
                const required = requiredEl ? requiredEl.value === 'yes' : true;
                groups.push({ name, selection, required, options });
            }
        });

        return {
            customization_enabled: groups.length > 0,
            customization_options: groups,
        };
    }

    function loadCustomizationToForm(product = {}) {
        const groupsRoot = document.getElementById('productCustomizationGroups');
        if (!groupsRoot) return;

        const groups = Array.isArray(product.customization_options) ? product.customization_options : [];

        groupsRoot.innerHTML = '';
        if (groups.length) {
            groups.forEach((group) => groupsRoot.appendChild(createCustomizationGroupElement(group)));
        }
        renumberVariationGroups();
        updateCustomizationPanelVisibility();
        const productImages = Array.isArray(product.images) ? product.images : [];
        if (groups.length && productImages.length) {
            applyImagesToVariantOptions(productImages);
        }
    }

    function resetCustomizationForm() {
        const groupsRoot = document.getElementById('productCustomizationGroups');
        if (groupsRoot) groupsRoot.innerHTML = '';
        updateCustomizationPanelVisibility();
    }

    (function initProductCustomizationEditor() {
        const groupsRoot = document.getElementById('productCustomizationGroups');
        const addGroupBtn = document.getElementById('addCustomizationGroupBtn');
        const categoryInput = document.getElementById('productCategoryInput');
        if (!groupsRoot || !addGroupBtn) return;

        addGroupBtn.addEventListener('click', () => {
            appendCustomizationGroup({
                name: '',
                selection: 'single',
                options: [
                    { name: '', stock: '0', extra_price: '0' },
                ],
            });
            renumberVariationGroups();
        });

        groupsRoot.addEventListener('click', (event) => {
            const target = event.target;
            if (!(target instanceof Element)) return;

            const addOptionBtn = target.closest('.customization-add-option-btn');
            if (addOptionBtn) {
                const optionTemplate = document.getElementById('variantOptionTemplate');
                const row = optionTemplate.content.firstElementChild.cloneNode(true);
                row.dataset.priceOffset = '0';
                row.querySelector('.customization-option-price').value = Number(document.getElementById('productPrice')?.value || 0).toFixed(2);
                updateVariantState(row);
                bindOptionImageInput(row);
                addOptionBtn.closest('.customization-group')
                    ?.querySelector('.customization-options-list')
                    ?.appendChild(row);
                return;
            }

            const removeOptionBtn = target.closest('.customization-option-remove');
            if (removeOptionBtn) {
                removeOptionBtn.closest('.customization-option-row')?.remove();
                return;
            }

            const removeGroupBtn = target.closest('.customization-group-remove');
            if (removeGroupBtn) {
                removeGroupBtn.closest('.customization-group')?.remove();
                renumberVariationGroups();
            }
        });

        categoryInput?.addEventListener('change', updateCustomizationPanelVisibility);
        categoryInput?.addEventListener('input', updateCustomizationPanelVisibility);
        updateCustomizationPanelVisibility();
    })();

    // â”€â”€ Upload â”€â”€
    const PRODUCT_IMAGE_SLOT_MAX = 6;
    let productImageSlots = Array(PRODUCT_IMAGE_SLOT_MAX).fill(null);
    let pendingProductImageSlotIndex = null;

    function renderProductImageSlots() {
        const grid = document.getElementById('productImageSlots');
        if (!grid) return;
        grid.querySelectorAll('.product-image-slot').forEach((slotEl, index) => {
            const emptyEl = slotEl.querySelector('.product-image-slot-empty');
            const previewEl = slotEl.querySelector('.product-image-slot-preview');
            const removeBtn = slotEl.querySelector('.product-image-slot-remove');
            const processingEl = slotEl.querySelector('.product-image-slot-processing');
            const data = productImageSlots[index];
            slotEl.setAttribute('aria-busy', String(Boolean(data?.isProcessing)));
            slotEl.setAttribute('role', data ? 'group' : 'button');
            slotEl.tabIndex = data ? -1 : 0;
            let primary = slotEl.querySelector('.product-image-primary');
            if (!primary) {
                primary = document.createElement('button'); primary.type = 'button'; primary.className = 'product-image-primary'; slotEl.append(primary);
            }
            primary.hidden = !data?.src || Boolean(data?.isProcessing);
            const isPrimary = index === productImageSlots.findIndex(item => item?.src);
            primary.disabled = isPrimary || productImageSlots.some(item => item?.isProcessing);
            primary.textContent = isPrimary ? 'Primary' : 'Make primary';
            if (previewEl) previewEl.alt = `Product image ${index + 1}`;

            if (data?.isProcessing) {
                slotEl.classList.add('is-processing');
                slotEl.classList.remove('is-filled');
                if (processingEl) processingEl.hidden = false;
                if (emptyEl) emptyEl.hidden = true;
                if (previewEl) previewEl.hidden = true;
                if (removeBtn) removeBtn.hidden = false;
            } else if (data?.src) {
                slotEl.classList.remove('is-processing');
                slotEl.classList.add('is-filled');
                if (processingEl) processingEl.hidden = true;
                if (previewEl) {
                    previewEl.src = data.src;
                    previewEl.hidden = false;
                }
                if (emptyEl) emptyEl.hidden = true;
                if (removeBtn) removeBtn.hidden = false;
            } else {
                slotEl.classList.remove('is-processing', 'is-filled');
                if (processingEl) processingEl.hidden = true;
                if (previewEl) {
                    previewEl.removeAttribute('src');
                    previewEl.hidden = true;
                }
                if (emptyEl) emptyEl.hidden = false;
                if (removeBtn) removeBtn.hidden = true;
            }
        });
        const count = productImageSlots.filter((slot) => slot && (slot.src || slot.isProcessing)).length;
        if (uploadDropzone) {
            uploadDropzone.classList.toggle('has-file', count > 0);
        }
        if (uploadFileName) {
            uploadFileName.textContent = count
                ? (count === 1 ? '1 image selected' : `${count} images selected`)
                : 'No file selected';
        }
    }

    function setProductImageSlotsFromSources(sources = []) {
        productImageSlots = Array(PRODUCT_IMAGE_SLOT_MAX).fill(null);
        sources
            .filter(Boolean)
            .slice(0, PRODUCT_IMAGE_SLOT_MAX)
            .forEach((src, index) => {
                productImageSlots[index] = { src, file: null };
            });
        renderProductImageSlots();
    }

    function removeImageBackground(dataUrl, callback, tolerance = 38) {
        if (!dataUrl || typeof dataUrl !== 'string' || !dataUrl.startsWith('data:image/')) {
            callback(dataUrl);
            return;
        }
        const img = new Image();
        img.onload = () => {
            try {
                const canvas = document.createElement('canvas');
                const w = img.naturalWidth || img.width;
                const h = img.naturalHeight || img.height;
                if (!w || !h) {
                    callback(dataUrl);
                    return;
                }
                canvas.width = w;
                canvas.height = h;
                const ctx = canvas.getContext('2d', { willReadFrequently: true });
                ctx.drawImage(img, 0, 0);

                const imgData = ctx.getImageData(0, 0, w, h);
                const data = imgData.data;

                const cornerIndices = [
                    0,
                    Math.max(0, (w - 1) * 4),
                    Math.max(0, ((h - 1) * w) * 4),
                    Math.max(0, ((h - 1) * w + (w - 1)) * 4)
                ];

                let bgR = 0, bgG = 0, bgB = 0, sampleCount = 0;
                for (const idx of cornerIndices) {
                    if (data[idx + 3] > 20) {
                        bgR += data[idx];
                        bgG += data[idx + 1];
                        bgB += data[idx + 2];
                        sampleCount++;
                    }
                }

                if (sampleCount === 0) {
                    callback(dataUrl);
                    return;
                }

                bgR = Math.round(bgR / sampleCount);
                bgG = Math.round(bgG / sampleCount);
                bgB = Math.round(bgB / sampleCount);

                const colorDist = (r1, g1, b1, r2, g2, b2) => {
                    return Math.hypot(r1 - r2, g1 - g2, b1 - b2);
                };

                const visited = new Uint8Array(w * h);
                const queue = new Int32Array(w * h);
                let head = 0;
                let tail = 0;

                const isBgPixel = (x, y) => {
                    const idx = (y * w + x) * 4;
                    if (data[idx + 3] === 0) return true;
                    const dist = colorDist(data[idx], data[idx + 1], data[idx + 2], bgR, bgG, bgB);
                    return dist <= tolerance;
                };

                for (let x = 0; x < w; x++) {
                    if (isBgPixel(x, 0)) {
                        visited[x] = 1;
                        queue[tail++] = x;
                    }
                    const bIdx = (h - 1) * w + x;
                    if (isBgPixel(x, h - 1)) {
                        visited[bIdx] = 1;
                        queue[tail++] = bIdx;
                    }
                }
                for (let y = 1; y < h - 1; y++) {
                    const lIdx = y * w;
                    if (isBgPixel(0, y)) {
                        visited[lIdx] = 1;
                        queue[tail++] = lIdx;
                    }
                    const rIdx = y * w + (w - 1);
                    if (isBgPixel(w - 1, y)) {
                        visited[rIdx] = 1;
                        queue[tail++] = rIdx;
                    }
                }

                while (head < tail) {
                    const curr = queue[head++];
                    const cx = curr % w;
                    const cy = Math.floor(curr / w);

                    const neighbors = [
                        cx > 0 ? curr - 1 : -1,
                        cx < w - 1 ? curr + 1 : -1,
                        cy > 0 ? curr - w : -1,
                        cy < h - 1 ? curr + w : -1
                    ];

                    for (let i = 0; i < 4; i++) {
                        const n = neighbors[i];
                        if (n !== -1 && !visited[n]) {
                            const nx = n % w;
                            const ny = Math.floor(n / w);
                            if (isBgPixel(nx, ny)) {
                                visited[n] = 1;
                                queue[tail++] = n;
                            }
                        }
                    }
                }

                if (tail === 0) {
                    callback(dataUrl);
                    return;
                }

                for (let i = 0; i < visited.length; i++) {
                    if (visited[i]) {
                        data[i * 4 + 3] = 0;
                    }
                }

                const maxFadeDist = tolerance * 1.4;
                for (let i = 0; i < visited.length; i++) {
                    if (!visited[i]) {
                        const x = i % w;
                        const y = Math.floor(i / w);
                        let isEdge = false;
                        if (x > 0 && visited[i - 1]) isEdge = true;
                        else if (x < w - 1 && visited[i + 1]) isEdge = true;
                        else if (y > 0 && visited[i - w]) isEdge = true;
                        else if (y < h - 1 && visited[i + w]) isEdge = true;

                        if (isEdge) {
                            const idx = i * 4;
                            const dist = colorDist(data[idx], data[idx + 1], data[idx + 2], bgR, bgG, bgB);
                            if (dist < maxFadeDist) {
                                const alphaFactor = Math.max(0.1, Math.min(1.0, dist / maxFadeDist));
                                data[idx + 3] = Math.round(data[idx + 3] * alphaFactor);
                            }
                        }
                    }
                }

                ctx.putImageData(imgData, 0, 0);
                callback(canvas.toDataURL('image/png'));
            } catch (err) {
                console.warn('Auto background removal fallback:', err);
                callback(dataUrl);
            }
        };
        img.onerror = () => callback(dataUrl);
        img.src = dataUrl;
    }

    async function requestServerAiBgRemoval(dataUrl) {
        const controller = new AbortController(), timer = setTimeout(() => controller.abort(), 20000);
        try {
            const response = await fetch('/api/products/remove-bg/', {
                signal: controller.signal,
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfCookie(),
                },
                body: JSON.stringify({ image_data: dataUrl }),
            });
            const result = await response.json().catch(() => ({}));
            if (response.ok && result.success && result.image_data) {
                return result.image_data;
            }
            if (result.error) {
                console.warn('Server AI background removal:', result.error);
            }
        } catch (err) {
            console.warn('Server AI background removal error, falling back:', err);
        }
        finally { clearTimeout(timer); }
        return null;
    }

    function processUploadedImageSource(rawSource, callback) {
        const autoRemove = document.getElementById('autoRemoveBgToggle')?.checked ?? true;
        if (!autoRemove) {
            callback(rawSource);
            return;
        }
        requestServerAiBgRemoval(rawSource).then((aiResult) => {
            if (aiResult) {
                callback(aiResult);
            } else {
                showProductSaveToast('Auto Remove BG is unavailable. The original image was kept.', 'error');
                callback(rawSource);
            }
        });
    }

    function validProductImageFile(file) {
        if (!['image/jpeg', 'image/png', 'image/webp', 'image/gif'].includes(file.type) || !file.size || file.size > 5 * 1024 * 1024) {
            showProductSaveToast('Choose JPEG, PNG, WebP or GIF images, up to 5 MB each.', 'error');
            return false;
        }
        return true;
    }
    function addProductImageFileToSlot(file, slotIndex) {
        if (!file || slotIndex < 0 || slotIndex >= PRODUCT_IMAGE_SLOT_MAX || !validProductImageFile(file)) return;
        const previous = productImageSlots[slotIndex];
        const slot = { src: '', file, isProcessing: true };
        productImageSlots[slotIndex] = slot;
        renderProductImageSlots();
        const failed = () => {
            if (productImageSlots[slotIndex] !== slot) return;
            productImageSlots[slotIndex] = previous;
            renderProductImageSlots();
            showProductSaveToast('Unable to read this image. Choose a supported image smaller than 20 megapixels.', 'error');
        };
        const reader = new FileReader();
        reader.onerror = failed;
        reader.onload = event => {
            const image = new Image();
            image.onerror = failed;
            image.onload = () => {
                if (image.naturalWidth * image.naturalHeight > 20000000) { failed(); return; }
                if (productImageSlots[slotIndex] !== slot) return;
                processUploadedImageSource(event.target.result, processedSrc => {
                    if (productImageSlots[slotIndex] !== slot) return; // Removed or replaced uploads cannot reappear.
                    slot.src = processedSrc; slot.isProcessing = false;
                    renderProductImageSlots();
                });
            };
            image.src = event.target.result;
        };
        reader.readAsDataURL(file);
    }
    function addProductImageFiles(files) {
        if (!files || !files.length) return;
        for (const file of files) {
            const index = productImageSlots.findIndex(slot => !slot);
            if (index === -1) { showProductSaveToast('Maximum 6 gallery images allowed.', 'error'); break; }
            addProductImageFileToSlot(file, index);
        }
    }

    function removeProductImageSlot(index) {
        if (index < 0 || index >= PRODUCT_IMAGE_SLOT_MAX) return;
        productImageSlots[index] = null;
        renderProductImageSlots();
    }

    function getProductImageSlotSources() {
        return productImageSlots.filter(Boolean).map((slot) => slot.src);
    }

    function clearProductImageSlots() {
        productImageSlots = Array(PRODUCT_IMAGE_SLOT_MAX).fill(null);
        renderProductImageSlots();
    }

    function updateFileName() {
        if (!uploadInput || !uploadDropzone) return;
        if (!uploadInput.files.length) {
            if (!productImageSlots.filter(Boolean).length) {
            uploadDropzone.classList.remove('is-loading', 'has-file');
            if (uploadFileName) uploadFileName.textContent = 'No file selected';
        }
            pendingProductImageSlotIndex = null;
            return;
        }
        if (pendingProductImageSlotIndex !== null) {
            addProductImageFileToSlot(uploadInput.files[0], pendingProductImageSlotIndex);
            pendingProductImageSlotIndex = null;
        } else {
            addProductImageFiles(uploadInput.files);
        }
        uploadInput.value = '';
        uploadDropzone.classList.remove('has-file');
        uploadDropzone.classList.add('is-loading');
        setTimeout(() => {
            uploadDropzone.classList.remove('is-loading');
            renderProductImageSlots();
        }, 400);
    }

    if (uploadInput && uploadDropzone) {
        uploadInput.addEventListener('change', updateFileName);
        uploadDropzone.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                pendingProductImageSlotIndex = null;
                uploadInput.click();
            }
        });
        uploadDropzone.addEventListener('click', (event) => {
            if (event.target instanceof Element && event.target.closest('.product-image-slots')) return;
            pendingProductImageSlotIndex = null;
        });
        ['dragenter', 'dragover'].forEach(ev => {
            uploadDropzone.addEventListener(ev, e => { e.preventDefault(); uploadDropzone.classList.add('is-dragover'); });
        });
        ['dragleave', 'dragend', 'drop'].forEach(ev => {
            uploadDropzone.addEventListener(ev, e => { e.preventDefault(); uploadDropzone.classList.remove('is-dragover'); });
        });
        uploadDropzone.addEventListener('drop', e => {
            if (e.dataTransfer.files.length) {
                addProductImageFiles(e.dataTransfer.files);
                uploadDropzone.classList.add('is-loading');
                setTimeout(() => uploadDropzone.classList.remove('is-loading'), 400);
            }
        });
    }

    const productImageSlotsGrid = document.getElementById('productImageSlots');
    if (productImageSlotsGrid && uploadInput) {
        productImageSlotsGrid.addEventListener('click', (event) => {
            const target = event.target;
            if (!(target instanceof Element)) return;
            const primary = target.closest('.product-image-primary');
            if (primary) {
                event.stopPropagation();
                const index = Number(primary.closest('.product-image-slot').dataset.slotIndex);
                if (productImageSlots[index]?.src) { const [image] = productImageSlots.splice(index, 1); productImageSlots.unshift(image); renderProductImageSlots(); }
                return;
            }
            const removeBtn = target.closest('.product-image-slot-remove');
            if (removeBtn) {
                event.stopPropagation();
                const slotEl = removeBtn.closest('.product-image-slot');
                const index = Number(slotEl?.dataset.slotIndex);
                if (!Number.isNaN(index)) removeProductImageSlot(index);
                return;
            }
            const slotEl = target.closest('.product-image-slot');
            if (!slotEl || slotEl.classList.contains('is-filled') || slotEl.classList.contains('is-processing')) return;
            const index = Number(slotEl.dataset.slotIndex);
            pendingProductImageSlotIndex = Number.isNaN(index) ? null : index;
            uploadInput.click();
        });
        productImageSlotsGrid.addEventListener('keydown', (event) => {
            if (event.key !== 'Enter' && event.key !== ' ') return;
            const slotEl = event.target.closest('.product-image-slot');
            if (!slotEl || slotEl.classList.contains('is-filled') || slotEl.classList.contains('is-processing')) return;
            event.preventDefault();
            const index = Number(slotEl.dataset.slotIndex);
            pendingProductImageSlotIndex = Number.isNaN(index) ? null : index;
            uploadInput.click();
        });
    }

    renderProductImageSlots();

    // ——— Render row ———
    function productImageSrc(imageUrl) {
        const value = (imageUrl || '').trim();
        if (!value) return '';
        if (/^https?:\/\//i.test(value) || /^data:image\//i.test(value) || value.startsWith('/')) {
            return value;
        }
        return value;
    }

    function renderProductActionsCell(status, isArchived = false) {
        const button = (kind, label, path) => `<button type="button" class="btn-user-action btn-${kind}-product" title="${kind === 'view' ? 'View Details' : `${label} Product`}" aria-label="${kind === 'view' ? 'View Details' : `${label} product`}"><svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" stroke-width="1.8" width="16" height="16"><path stroke-linecap="round" stroke-linejoin="round" d="${path}"/></svg></button>`;
        const view = button('view', 'View', 'M2 12s4-7 10-7 10 7 10 7-4 7-10 7S2 12 2 12Zm7 0a3 3 0 1 0 6 0 3 3 0 0 0-6 0');
        const listing = canManageProducts ? (isArchived ? button('restore', 'Restore', 'M4 10a8 8 0 1 1 1 8M4 3v7h7') : button('archive', 'Archive', 'M4 7h16v13H4V7Zm-1-4h18v4H3V3Zm6 8h6')) : '';
        const review = normalizeStatus(status) === 'pending' && canApproveProducts && !isArchived
            ? button('approve', 'Approve', 'm5 12 4 4L19 6') + button('reject', 'Reject', 'm6 6 12 12M18 6 6 18') : '';
        return `<td class="col-action"><div class="action-row">${view}${review}${listing}</div></td>`;
    }

    function renderProductRow(row, product) {
        if (!row || !product) return;
        const pId = product.id || '';
        const ns = normalizeStatus(product.approval_status || product.product_status || 'pending');
        const invStatus = product.inventory_status || 'in_stock';
        const formattedPrice = typeof product.price === 'number'
            ? product.price.toFixed(2)
            : String(product.price || '0.00');
        const displayId = product.sku || '';

        // Product images
        const storedImages = Array.isArray(product.images) && product.images.length
            ? product.images
            : (product.image_url ? [product.image_url] : []);
        const primaryImage = storedImages[0] || product.image_url || '';
        const imgHtml = primaryImage
            ? `<img src="${escapeHtml(pId ? productGalleryImageSrc(pId, 0) : primaryImage)}" alt="${escapeHtml(product.name || '')}" class="product-table-image" referrerpolicy="no-referrer">
               <span class="product-table-image product-table-image-empty" hidden>${escapeHtml((product.name || 'P').charAt(0).toUpperCase())}</span>`
            : `<span class="product-table-image product-table-image-empty">${escapeHtml((product.name || 'P').charAt(0).toUpperCase())}</span>`;

        row.dataset.productId = String(pId);
        row.dataset.productStatus = ns;
        row.dataset.productDescription = product.description || '';
        row.dataset.productImageUrl = primaryImage;
        row.dataset.productImages = JSON.stringify(storedImages);
        row.dataset.productExpiry = product.expiry_date || '';
        row.dataset.inventoryStatus = invStatus;
        row.dataset.productStock = String(Math.max(0, computeTotalStock(product)));
        row.dataset.productType = product.product_type || 'single';
        row.dataset.bundle = JSON.stringify(product.bundle || {});
        row.dataset.productTags = JSON.stringify(product.tags || []);
        row.dataset.departmentId = product.program_id || product.department_id || '';
        row.dataset.majorId = product.major_id || '';
        row.dataset.programLabel = product.program || '';
        row.dataset.majorLabel = product.major || '';
        row.dataset.programMajor = product.program_major || '';
        row.dataset.sku = product.sku || '';
        row.dataset.lowStockThreshold = product.product_type === 'bundle' || hasVariantInventory(product) ? '' : String(product.low_stock_threshold ?? LOW_STOCK_THRESHOLD);
        row.dataset.variantCount = String(countProductVariants(product));
        const lowStockItems = hasVariantInventory(product)
            ? flattenCustomizationInventory(product.customization_options)
            : [{ stock: computeTotalStock(product), expiry_date: product.expiry_date }];
        row.dataset.hasLowStock = product.product_type !== 'bundle' && lowStockItems.some((item) =>
            computeInventoryStatus(item.stock, item.expiry_date, product.category, item.low_stock_threshold ?? product.low_stock_threshold ?? LOW_STOCK_THRESHOLD) === 'low_stock') ? '1' : '0';
        row.dataset.productCategory = product.category || '';
        row.dataset.customizationEnabled = product.customization_enabled ? '1' : '0';
        row.dataset.customizationOptions = JSON.stringify(product.customization_options || []);
        row.dataset.sellerId = product.seller_id || '';
        row.dataset.sellerDepartment = product.department || '';
        row.dataset.productBasePrice = product.price || '';
        row.dataset.productSubmittedAt = product.submitted_at || '';
        row.dataset.productUpdatedAt = product.updated_at || '';

        const submittedAt = product.submitted_at || 'Just now';

        row.innerHTML = `
            <td class="col-num"></td>
            <td class="col-product-name">
                <div class="product-name-cell">
                    ${imgHtml}
                    <div class="product-name-meta">
                        <strong title="${escapeHtml(product.name || '')}">${escapeHtml(product.name || '')}</strong>
                        ${displayId ? `<span class="product-id-label">${escapeHtml(displayId)}</span>` : ''}
                    </div>
                </div>
            </td>
            <td class="col-seller"><strong>${escapeHtml(product.seller || currentUserDisplayName)}</strong><span>${escapeHtml(product.program_major || 'Unassigned (legacy record)')}</span></td>
            <td>${escapeHtml(product.category || 'Uncategorized')}</td>
            <td class="col-price">&#8369; ${escapeHtml(formattedPrice)}</td>
            <td class="col-inventory">
                ${renderInventorySummary(computeTotalStock(product), countProductVariants(product), product)}
            </td>
            <td class="col-status">
                ${renderStatusPill(ns)}
            </td>
            <td class="col-date">
                <strong>${escapeHtml(submittedAt)}</strong>
            </td>
            ${renderProductActionsCell(ns, Boolean(product.is_archived))}
        `;

        initProductTableImageCycle(row);
    }

    function upsertLocalProduct(product) {
        try {
            const products = loadTestProducts().filter((p) => String(p.id) !== String(product.id));
            products.push(product);
            saveTestProducts(products);
        } catch (_) {}
    }

    function applyImageToRow(row, imageUrl, imageList) {
        const url = productImageSrc(imageUrl);
        const productId = row.dataset.productId || '';
        const storedImages = parseProductImages(imageList, url);
        row.dataset.productImageUrl = url;
        row.dataset.productImages = JSON.stringify(storedImages);
        const cell = row.querySelector('.product-name-cell');
        if (!cell) return;
        const name = cell.querySelector('strong')?.textContent?.trim() || '';
        const thumbSrc = productId && storedImages.length
            ? productGalleryImageSrc(productId, 0)
            : url;
        const imgHtml = thumbSrc
            ? `<img src="${escapeHtml(thumbSrc)}" alt="${escapeHtml(name)}" class="product-table-image" loading="lazy" referrerpolicy="no-referrer"><span class="product-table-image product-table-image-empty" hidden>${escapeHtml((name || 'P').charAt(0).toUpperCase())}</span>`
            : `<span class="product-table-image product-table-image-empty">${escapeHtml((name || 'P').charAt(0).toUpperCase())}</span>`;
        cell.innerHTML = `${imgHtml}<div class="product-name-meta"><strong title="${escapeHtml(name)}">${escapeHtml(name)}</strong></div>`;
        initProductTableImageCycle(row);
    }

    async function hydrateProductImagesFromServer() {
        if (!productsTableBody) return;
        try {
            const response = await fetch('/api/marketplace/products/', {
                credentials: 'same-origin',
                headers: { Accept: 'application/json' },
            });
            if (!response.ok) return;
            const data = await response.json();
            const products = data.products || [];
            products.forEach((product) => {
                const row = productsTableBody.querySelector(`tr[data-product-id="${product.id}"]`);
                if (!row) return;
                const imageList = parseProductImages(product.images, product.image_url);
                if (!imageList.length) return;
                applyImageToRow(
                    row,
                    `/api/products/${product.id}/image/`,
                    imageList
                );
                upsertLocalProduct({
                    id: product.id,
                    image_url: product.image_url,
                    images: imageList,
                    name: product.name,
                });
            });
            initAllProductTableImageCycles();
        } catch (_) {
            /* ignore */
        }
    }

    function loadTestProductsIntoTable() {
        const products = loadTestProducts();
        if (!products.length || !productsTableBody) return;
        const emptyRow = productsTableBody.querySelector('.empty-products-row');
        if (emptyRow) emptyRow.remove();
        products.forEach((product) => {
            const existing = productsTableBody.querySelector(`tr[data-product-id="${product.id}"]`);
            if (existing) {
                if (product.image_url || product.images?.length) {
                    applyImageToRow(
                        existing,
                        product.id ? `/api/products/${product.id}/image/` : product.image_url,
                        product.images
                    );
                }
                return;
            }
            const row = document.createElement('tr');
            renderProductRow(row, product);
            productsTableBody.appendChild(row);
        });
    }

    // loadTestProductsIntoTable();
    initAllProductTableImageCycles();
    hydrateProductImagesFromServer();

    // â”€â”€ Toast â”€â”€
    function showProductSaveToast(message = 'Product saved.', type = 'success') {
        if (!productSaveToast) return;
        productSaveToast.textContent = message;
        productSaveToast.classList.toggle('is-error', type === 'error');
        productSaveToast.classList.add('show');
        window.clearTimeout(productSaveToast.hideTimer);
        productSaveToast.hideTimer = window.setTimeout(() => {
            productSaveToast.classList.remove('show', 'is-error');
        }, 2400);
    }

    // â”€â”€ Renumber rows â”€â”€
    function renumberRows() {
        if (!productsTableBody) return;
        const rows = productsTableBody.querySelectorAll('tr:not(.empty-products-row)');
        rows.forEach((row, i) => {
            const numCell = row.querySelector('td.col-num') || row.firstElementChild;
            if (numCell && numCell.classList.contains('col-num')) {
                numCell.textContent = i + 1;
            } else if (row.firstElementChild && row.children.length >= 8) {
                row.firstElementChild.textContent = i + 1;
            }
        });
    }

    // â”€â”€ Form helpers â”€â”€
    function updateDescriptionCount() {
        const desc = document.getElementById('productDescription');
        const countEl = document.getElementById('productDescriptionCount');
        if (!desc || !countEl) return;
        const max = Number(desc.getAttribute('maxlength')) || 1000;
        countEl.textContent = `${desc.value.length} / ${max} characters`;
    }

    document.getElementById('productOwner')?.addEventListener('change', event => {
        const owner = event.target.selectedOptions[0];
        if (!owner?.dataset.program) return;
        const program = document.getElementById('productDepartment');
        const major = document.getElementById('productMajor');
        program.value = owner.dataset.program;
        window.CampusHubAcademic?.sync(program, major);
        major.value = owner.dataset.major || '';
    });

    function setDepartmentValue(departmentName) {
        const deptField = document.getElementById('productDepartment');
        if (!deptField) return;
        const target = String(departmentName || '').trim().toLowerCase();
        if (!target) {
            deptField.value = '';
            return;
        }
        const match = Array.from(deptField.options).find(
            (opt) => opt.textContent.trim().toLowerCase() === target
        );
        deptField.value = match ? match.value : '';
    }

    function setSaveProductButtonLabel(text) {
        if (!saveProductButton) return;
        const labelEl = saveProductButton.querySelector('.save-btn-label');
        if (labelEl) labelEl.textContent = text;
        else saveProductButton.textContent = text;
    }

    function syncProductFormMode(isEdit) {
        const subtitle = document.getElementById('productFormSubtitle');
        if (isEdit) {
            if (productFormTitle) productFormTitle.textContent = 'Edit Product';
            if (subtitle) {
                subtitle.textContent = 'Update the product information and save your changes.';
            }
            setSaveProductButtonLabel('Save Changes');
        } else {
            if (productFormTitle) productFormTitle.textContent = 'Add Product';
            if (subtitle) {
                subtitle.textContent = 'Enter product details to add a new product.';
            }
            setSaveProductButtonLabel('Add Product');
        }
    }

    function resetProductForm() {
        const feedback = document.getElementById('productFormError');
        if (feedback) { feedback.hidden = true; feedback.textContent = ''; }
        document.querySelectorAll('#productFormSection [aria-invalid]').forEach(field => field.removeAttribute('aria-invalid'));
        editingProductRow = null;
        editingProductId = null;
        syncProductFormMode(false);
        document.getElementById('productTypeSingle').checked = true;
        const owner = document.getElementById('productOwner');
        if (owner) owner.value = '';
        document.getElementById('productName').value = '';
        document.getElementById('productPrice').value = '';
        setCategoryValue('');
        document.getElementById('productStock').value = '';
        document.getElementById('productLowStockThreshold').value = LOW_STOCK_THRESHOLD;
        document.getElementById('productLowStockThreshold').setCustomValidity('');
        document.getElementById('productThresholdError').textContent = '';
        document.getElementById('productExpiryDate').value = '';
        document.getElementById('productStatus').value = 'approved';
        document.getElementById('productDescription').value = '';
        const tagsField = document.getElementById('productTags');
        if (tagsField) tagsField.value = '';
        const deptField = document.getElementById('productDepartment');
        if (deptField) {
            const defaultOpt = Array.from(deptField.options).find((opt) => opt.defaultSelected);
            deptField.value = defaultOpt ? defaultOpt.value : '';
        }
        document.getElementById('productMajor').value = '';
        window.CampusHubAcademic?.sync(deptField, document.getElementById('productMajor'));
        updateDescriptionCount();
        resetCustomizationForm();
        window.CampusHubBundles?.reset();
        clearProductImageSlots();
        if (uploadInput) uploadInput.value = '';
        if (uploadDropzone) uploadDropzone.classList.remove('is-loading', 'has-file');
        const autoRemoveToggle = document.getElementById('autoRemoveBgToggle');
        if (autoRemoveToggle) autoRemoveToggle.checked = true;
        updateProductFormAutomation();
    }

    function hideProductDetailsSection() {
        document.getElementById('productDetailsSection')?.classList.add('d-none');
    }

    function showProductForm() {
        hideProductDetailsSection();
        productsListSection.classList.add('d-none');
        if (productLoadingSection) productLoadingSection.classList.add('d-none');
        if (productFormHeader) productFormHeader.classList.remove('d-none');
        productFormSection.classList.remove('d-none');
        if (statsGrid) statsGrid.classList.add('d-none');
        updateCustomizationPanelVisibility();
        window.scrollTo({ top: 0, behavior: 'smooth' });
    }

    function showProductLoading(callback) {
        hideProductDetailsSection();
        productsListSection.classList.add('d-none');
        if (productFormHeader) productFormHeader.classList.add('d-none');
        productFormSection.classList.add('d-none');
        if (productLoadingSection) productLoadingSection.classList.remove('d-none');
        if (statsGrid) statsGrid.classList.add('d-none');
        window.scrollTo({ top: 0, behavior: 'smooth' });
        window.setTimeout(callback, 520);
    }

    function showProductsList() {
        hideProductDetailsSection();
        if (productLoadingSection) productLoadingSection.classList.add('d-none');
        if (productFormHeader) productFormHeader.classList.add('d-none');
        productFormSection.classList.add('d-none');
        productsListSection.classList.remove('d-none');
        if (statsGrid) statsGrid.classList.remove('d-none');
    }

    function getProductFromRow(row) {
        const cells = row.children;
        const productCell = cells[1];
        const nameEl = productCell.querySelector('strong');
        const image = productCell.querySelector('img');
        const customization_options = parseCustomizationOptions(row.dataset.customizationOptions || '');
        const product = {
            id: row.dataset.productId || '',
            product_type: row.dataset.productType || 'single',
            bundle: parseJsonDataset(row.dataset.bundle || '{}') || {},
            tags: parseCustomizationOptions(row.dataset.productTags || '[]'),
            department_id: row.dataset.departmentId || '',
            program_id: row.dataset.departmentId || '', major_id: row.dataset.majorId || '',
            program: row.dataset.programLabel || '', major: row.dataset.majorLabel || '',
            program_major: row.dataset.programMajor || '', sku: row.dataset.sku || '',
            seller_id: row.dataset.sellerId || '',
            image_url: row.dataset.productImageUrl || (image ? image.getAttribute('src') : ''),
            name: nameEl ? nameEl.textContent.trim() : '',
            seller: cells[2]?.querySelector('strong')?.textContent.trim() || cells[2]?.textContent.trim() || '',
            category: row.dataset.productCategory || (cells[3] ? cells[3].textContent.trim() : ''),
            department: row.dataset.sellerDepartment || '',
            price: row.dataset.productBasePrice || '',
            stock: row.dataset.productStock || '0',
            low_stock_threshold: row.dataset.lowStockThreshold === '' ? null : Number(row.dataset.lowStockThreshold ?? LOW_STOCK_THRESHOLD),
            expiry_date: row.dataset.productExpiry || '',
            inventory_status: row.dataset.inventoryStatus || '',
            product_status: row.dataset.productStatus || '',
            approval_status: row.dataset.productStatus || '',
            submitted_at: row.dataset.productSubmittedAt || '',
            updated_at: row.dataset.productUpdatedAt || '',
            is_archived: row.dataset.isArchived === '1' || row.dataset.isArchived === 'true',
            description: row.dataset.productDescription || '',
            images: parseProductImagesJson(row.dataset.productImages || ''),
            customization_enabled: row.dataset.customizationEnabled === '1',
            customization_options,
            variant_count: row.dataset.variantCount || flattenCustomizationInventory(customization_options).length,
        };
        product.stock = String(computeTotalStock(product));
        return product;
    }

    function openEditProductForm(row) {
        const product = getProductFromRow(row);
        document.getElementById(product.product_type === 'bundle' ? 'productTypeBundle' : 'productTypeSingle').checked = true;
        const owner = document.getElementById('productOwner');
        if (owner && product.seller_id) {
            if (!Array.from(owner.options).some(option => option.value === String(product.seller_id))) {
                owner.add(new Option(product.seller, String(product.seller_id)));
            }
            owner.value = String(product.seller_id);
        }
        editingProductRow = row;
        editingProductId = product.id;
        syncProductFormMode(true);
        document.getElementById('productName').value = product.name;
        document.getElementById('productPrice').value = product.price;
        setCategoryValue(product.category);
        document.getElementById('productStock').value = product.stock;
        document.getElementById('productLowStockThreshold').value = product.low_stock_threshold ?? LOW_STOCK_THRESHOLD;
        document.getElementById('productLowStockThreshold').setCustomValidity('');
        document.getElementById('productThresholdError').textContent = '';
        document.getElementById('productExpiryDate').value = product.expiry_date || '';
        document.getElementById('productStatus').value = normalizeStatus(product.product_status || 'pending');
        document.getElementById('productDescription').value = product.description === 'No description' ? '' : product.description;
        const tagsField = document.getElementById('productTags');
        if (tagsField) tagsField.value = Array.isArray(product.tags) ? product.tags.join(', ') : '';
        setDepartmentValue(product.department || '');
        document.getElementById('productDepartment').value = product.program_id || product.department_id || '';
        window.CampusHubAcademic?.sync(document.getElementById('productDepartment'), document.getElementById('productMajor'));
        document.getElementById('productMajor').value = product.major_id || '';
        updateDescriptionCount();
        loadCustomizationToForm(product);
        const existingImages = Array.isArray(product.images) && product.images.length
            ? product.images
            : parseProductImagesJson(row.dataset.productImages || '');
        setProductImageSlotsFromSources(existingImages);
        if (uploadInput) uploadInput.value = '';
        if (uploadDropzone) uploadDropzone.classList.remove('is-loading', 'has-file');
        updateProductFormAutomation();
        window.CampusHubBundles?.load(product);
        showProductForm();
    }

    if (addProductButton) {
        addProductButton.addEventListener('click', () => {
            resetProductForm();
            showProductLoading(showProductForm);
        });
        if (new URLSearchParams(window.location.search).get('action') === 'add') {
            resetProductForm();
            showProductLoading(showProductForm);
        }
    }

    const backToProductsButton = document.getElementById('backToProductsButton');
    if (backToProductsButton) {
        backToProductsButton.addEventListener('click', () => {
            resetProductForm();
            showProductsList();
        });
    }

    const cancelProductFormButton = document.getElementById('cancelProductFormButton');
    if (cancelProductFormButton) {
        cancelProductFormButton.addEventListener('click', () => {
            resetProductForm();
            showProductsList();
        });
    }

    if (saveProductButton) {
        saveProductButton.addEventListener('click', () => {
            if (saveProductButton.disabled) return;
            const feedback = document.getElementById('productFormError');
            if (feedback) { feedback.hidden = true; feedback.textContent = ''; }
            document.querySelectorAll('#productFormSection [aria-invalid]').forEach(field => field.removeAttribute('aria-invalid'));
            const invalid = [...document.querySelectorAll('#productFormSection input, #productFormSection select, #productFormSection textarea')].find(field => !field.disabled && !field.checkValidity());
            if (invalid) { invalid.reportValidity(); invalid.focus(); return; }
            const bundleMode = document.getElementById('productTypeBundle').checked;
            if (bundleMode && !window.CampusHubBundles.validate()) return;
            const owner = document.getElementById('productOwner');
            if (owner && !owner.reportValidity()) return;
            const name = document.getElementById('productName').value.trim();
            const price = document.getElementById('productPrice').value;
            const category = getSelectedCategory() || document.getElementById('productCategory')?.value?.trim() || '';
            const stock = document.getElementById('productStock').value || 0;
            const expiryDate = document.getElementById('productExpiryDate')?.value || '';
            const selectedStatus = document.getElementById('productStatus')?.value || 'approved';
            // In admin add product form: auto-approve new listings, remove pending!
            // When editing an existing product, retain its status.
            let productStatus;
            if (editingProductId) {
                productStatus = selectedStatus;
            } else {
                productStatus = 'approved';
            }
            const statusField = document.getElementById('productStatus');
            if (statusField && !editingProductId) {
                statusField.value = 'approved';
            }
            const description = document.getElementById('productDescription').value.trim();
            const customizationData = bundleMode ? {customization_enabled:false, customization_options:[]} : readCustomizationFromForm();
            if (!bundleMode && !validateThresholdForm(customizationData)) return;
            const threshold = bundleMode || customizationData.customization_enabled ? null : Number(document.getElementById('productLowStockThreshold').value);
            const derivedStock = bundleMode ? window.CampusHubBundles.availability() : deriveStockFromCustomization(customizationData, stock);
            const derivedExpiry = bundleMode ? '' : deriveExpiryFromCustomization(customizationData, category, expiryDate);
            const inventoryStatus = computeProductAvailability({
                category,
                stock: derivedStock,
                low_stock_threshold: threshold,
                expiry_date: derivedExpiry,
                customization_enabled: customizationData.customization_enabled,
                customization_options: customizationData.customization_options,
            });

            const programField = document.getElementById('productDepartment');
            const majorField = document.getElementById('productMajor');
            if (!programField.value || (!majorField.disabled && !majorField.value)) {
                showProductSaveToast('Select a program and its major when applicable.', 'error');
                (!programField.value ? programField : majorField).focus();
                return;
            }
            if (!name || !price || !category || category === 'Select food category') {
                showProductSaveToast('Please enter product name, price, and category.', 'error');
                return;
            }

            if (isPerishableCategory(category) && derivedExpiry) {
                const expiry = new Date(`${derivedExpiry}T00:00:00`);
                const today = new Date();
                today.setHours(0, 0, 0, 0);
                if (expiry < today && !window.confirm('This expiry date is in the past. Save anyway?')) {
                    return;
                }
            }

            const isProcessingBgRemoval = productImageSlots.some((slot) => slot && !slot.src && slot.file);
            if (isProcessingBgRemoval) {
                showProductSaveToast('Still processing image background. Please wait a moment...', 'error');
                return;
            }

            // Show spinner
            saveProductButton.classList.add('is-saving');
            saveProductButton.disabled = true;
            const labelEl = saveProductButton.querySelector('.save-btn-label');
            if (labelEl) labelEl.textContent = editingProductId ? 'Updating...' : 'Saving...';

            const existingProduct = editingProductRow ? getProductFromRow(editingProductRow) : {};

            async function saveProductToServer(productData) {
                const payload = {
                    id: /^\d+$/.test(String(productData.id || '')) ? productData.id : null,
                    seller_id: productData.seller_id || null,
                    name: productData.name,
                    price: productData.price,
                    category: productData.category,
                    stock: bundleMode ? 0 : productData.stock,
                    low_stock_threshold: productData.low_stock_threshold,
                    product_type: bundleMode ? 'bundle' : 'single',
                    bundle_components: bundleMode ? window.CampusHubBundles.payload() : [],
                    department_id: document.getElementById('productDepartment').value || null,
                    major_id: document.getElementById('productMajor').value || null,
                    tags: document.getElementById('productTags').value,
                    expiry_date: productData.expiry_date || null,
                    description: productData.description,
                    image_url: productData.images ? '' : normalizeProductImageUrl(productData.image_url || ''),
                    images: productData.images || null,
                    customization_enabled: productData.customization_enabled,
                    customization_options: productData.customization_options,
                    approval_status: editingProductId ? (productData.approval_status || productData.product_status || 'approved') : 'approved',
                    product_status: editingProductId ? (productData.product_status || productData.approval_status || 'approved') : 'approved',
                };

                const response = await fetch('/api/products/admin/save/', {
                    method: 'POST',
                    credentials: 'same-origin',
                    headers: {
                        'Content-Type': 'application/json',
                        'Accept': 'application/json',
                        'X-CSRFToken': getCsrfCookie()
                    },
                    body: JSON.stringify(payload)
                });

                if (response.redirected) {
                    throw new Error('Session expired. Please reload and log in again.');
                }

                const data = await window.CampusHubActions.json(response, 'Unable to confirm the update. Reload the record before retrying.');
                if (!response.ok || !data.product) {
                    throw new Error(data.error || 'Could not save product.');
                }
                return data.product;
            }

            async function finalizeSave(imageUrl) {
                const isMultiple = Array.isArray(imageUrl);
                const ownerSelect = document.getElementById('productOwner');
                const productData = {
                    id: editingProductId || generateId(),
                    seller_id: ownerSelect ? ownerSelect.value : null,
                    name, price, category,
                    department: existingProduct.department || '',
                    stock: derivedStock,
                    low_stock_threshold: threshold,
                    expiry_date: isPerishableCategory(category) ? derivedExpiry : '',
                    inventory_status: inventoryStatus,
                    description,
                    product_status: editingProductId ? normalizeStatus(productStatus || 'approved') : 'approved',
                    image_url: isMultiple ? imageUrl[0] || '' : imageUrl,
                    images: isMultiple ? imageUrl : null,
                    seller: existingProduct.seller || currentUserDisplayName,
                    approval_status: editingProductId ? normalizeStatus(productStatus || 'approved') : 'approved',
                    customization_enabled: customizationData.customization_enabled,
                    customization_options: customizationData.customization_options,
                    submitted_at: existingProduct.submitted_at || new Date().toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' })
                };

                try {
                    const savedProduct = await saveProductToServer(productData);
                    productData.id = savedProduct.id;
                    productData.seller_id = savedProduct.seller_id;
                    productData.seller = savedProduct.seller || productData.seller;
                    productData.department = savedProduct.department || productData.department;
                    productData.approval_status = savedProduct.approval_status || 'approved';
                    productData.product_status = productData.approval_status;
                    productData.inventory_status = savedProduct.inventory_status || inventoryStatus;
                    productData.expiry_date = savedProduct.expiry_date || productData.expiry_date;
                    productData.submitted_at = savedProduct.submitted_at || productData.submitted_at;
                    productData.updated_at = savedProduct.updated_at;
                    productData.low_stock_threshold = savedProduct.low_stock_threshold;
                    productData.stock = savedProduct.stock;
                    productData.product_type = savedProduct.product_type;
                    productData.bundle = savedProduct.bundle;
                    productData.tags = savedProduct.tags;
                    productData.department_id = savedProduct.department_id;
                    productData.image_url = savedProduct.image_url || productData.image_url;
                    productData.images = savedProduct.images
                        || productData.images
                        || (productData.image_url ? [productData.image_url] : []);
                    productData.customization_enabled = savedProduct.customization_enabled || false;
                    productData.customization_options = savedProduct.customization_options || [];
                    // Keep the saved SKU/Program/Major, not just the old form fields.
                    Object.assign(productData, savedProduct);

                    upsertLocalProduct(productData);

                    try {
                        if (editingProductRow) {
                            renderProductRow(editingProductRow, productData);
                            showProductSaveToast('Product updated.');
                        } else {
                            const emptyRow = productsTableBody?.querySelector('.empty-products-row');
                            if (emptyRow) emptyRow.remove();
                            // Show table, hide empty state
                            const tableWrap = document.getElementById('productsTableWrap');
                            const emptyState = document.getElementById('productsEmptyState');
                            const tableFooter = document.getElementById('productsTableFooter');
                            if (tableWrap) tableWrap.style.display = '';
                            if (emptyState) emptyState.style.display = 'none';
                            if (tableFooter) tableFooter.style.display = '';
                            const row = document.createElement('tr');
                            renderProductRow(row, productData);
                            productsTableBody?.prepend(row);
                            showProductSaveToast(
                                productData.approval_status === 'pending'
                                    ? 'Product saved as Pending Approval.'
                                    : 'Product saved.'
                            );
                        }

                        renumberRows();
                        const showingText = document.getElementById('productsShowingText');
                        if (showingText && productsTableBody) {
                            const rowCount = productsTableBody.querySelectorAll('tr:not(.empty-products-row)').length;
                            showingText.textContent = `Showing 1 to ${Math.min(10, rowCount)} of ${rowCount} entries`;
                        }
                    } catch (domErr) {
                        console.warn('Non-fatal error rendering saved product in table:', domErr);
                        showProductSaveToast('Product saved.');
                    }

                    resetProductForm();
                    showProductsList();
                    window.dispatchEvent(new Event('products-table-changed'));
                } catch (error) {
                    console.error('Save product failed:', error);
                    const feedback = document.getElementById('productFormError');
                    if (feedback) { feedback.textContent = error.message || 'Could not save product.'; feedback.hidden = false; }
                    const fieldId = {name:'productName',category:'productCategory',description:'productDescription',price:'productPrice',stock:'productStock',low_stock_threshold:'productLowStockThreshold',seller_id:'productOwner',images:'productImageUpload',customization_options:'productCustomizationGroups'}[error.field];
                    const field = fieldId && document.getElementById(fieldId);
                    if (field) { field.setAttribute('aria-invalid', 'true'); if (field.type !== 'file') field.focus(); }

                    showProductSaveToast(error.message || 'Could not save product.', 'error');
                } finally {
                    saveProductButton.classList.remove('is-saving');
                    saveProductButton.disabled = false;
                    setSaveProductButtonLabel(editingProductId ? 'Save Changes' : 'Add Product');
                }
            }

            const spinnerStart = Date.now();
            const MIN_SPINNER = 900;

            function finalizeSaveWithDelay(imageUrl) {
                const elapsed = Date.now() - spinnerStart;
                const remaining = Math.max(0, MIN_SPINNER - elapsed);
                setTimeout(() => {
                    finalizeSave(imageUrl).catch((err) => {
                        console.error('Unhandled finalizeSave error:', err);
                        saveProductButton.classList.remove('is-saving');
                        saveProductButton.disabled = false;
                        setSaveProductButtonLabel(editingProductId ? 'Save Changes' : 'Add Product');
                    });
                }, remaining);
            }

            // Keep both product gallery images and per-variant option images.
            const uploadedImages = getProductImageSlotSources().filter(Boolean); // Variant photos stay on their exact options, outside the gallery.
            finalizeSaveWithDelay(uploadedImages);
        });
    }

    function productNameFromRow(row) {
        return row?.querySelector('.product-name-meta strong')?.textContent.trim()
            || row?.children[1]?.textContent.trim()
            || 'this product';
    }

    function getCsrfCookie() {
        return document.cookie
            .split(';')
            .map((cookie) => cookie.trim())
            .find((cookie) => cookie.startsWith('csrftoken='))
            ?.split('=')[1] || '';
    }

    function syncProductStatsFromRows() {
        // These are the complete, server-authorized records, including archived
        // rows. Visible filters/pagination must not redefine the summary totals.
        const rows = [...productsTableBody.querySelectorAll('tr[data-product-id]')];
        const counts = {
            totalStatCard: rows.length,
            pendingStatCard: rows.filter(row => row.dataset.productStatus === 'pending').length,
            approvedStatCard: rows.filter(row => row.dataset.productStatus === 'approved').length,
            lowStockStatCard: rows.filter(row => row.dataset.hasLowStock === '1' && !['1','true'].includes(row.dataset.isArchived)).length,
        };
        Object.entries(counts).forEach(([id, count]) => {
            const value = document.querySelector(`#${id} strong`);
            if (value) value.textContent = String(count);
        });
    }
    window.addEventListener('products-table-changed', syncProductStatsFromRows);

    function openProductDecision(row, action) {
        if (!row || !['approve', 'reject'].includes(action)) return;
        pendingProductDecisionRow = row;
        pendingProductDecision = action;
        const isReject = action === 'reject';
        const title = document.getElementById('productDecisionModalLabel');
        const message = document.getElementById('productDecisionMessage');
        const name = document.getElementById('productDecisionName');
        const reasonGroup = document.getElementById('productDecisionReasonGroup');
        const reason = document.getElementById('productDecisionReason');
        const confirmButton = document.getElementById('confirmProductDecisionButton');
        if (title) title.textContent = isReject ? 'Reject Product' : 'Approve Product';
        if (message) message.textContent = isReject
            ? 'Provide a reason so the seller can correct the listing.'
            : 'Approve this listing and make it available in the marketplace?';
        if (name) name.textContent = productNameFromRow(row);
        if (reasonGroup) reasonGroup.classList.toggle('d-none', !isReject);
        if (reason) reason.value = '';
        if (confirmButton) {
            confirmButton.textContent = isReject ? 'Reject' : 'Approve';
            confirmButton.classList.toggle('is-reject', isReject);
        }
        const modal = document.getElementById('productDecisionModal');
        if (modal && window.bootstrap?.Modal) {
            window.bootstrap.Modal.getOrCreateInstance(modal).show();
        }
    }

    function openProductArchiveModal(row) {
        if (!row) return;
        window.__chPendingArchiveProductRow = row;
        const name = document.getElementById('archiveProductName');
        if (name) name.textContent = productNameFromRow(row);
        const modal = document.getElementById('archiveProductModal');
        if (modal && window.bootstrap?.Modal) {
            window.bootstrap.Modal.getOrCreateInstance(modal).show();
        }
    }
    window.openProductArchiveModal = openProductArchiveModal;

    function openProductRestoreModal(row) {
        if (!row) return;
        window.__chPendingRestoreProductRow = row;
        const name = document.getElementById('restoreProductName');
        if (name) name.textContent = productNameFromRow(row);
        const modal = document.getElementById('restoreProductModal');
        if (modal && window.bootstrap?.Modal) {
            window.bootstrap.Modal.getOrCreateInstance(modal).show();
        }
    }
    window.openProductRestoreModal = openProductRestoreModal;

    if (productsTableBody) {
        productsTableBody.addEventListener('click', (event) => {
            const viewButton = event.target.closest('.btn-view-product, .view-product-action');
            if (viewButton) {
                event.preventDefault();
                event.stopPropagation();
                const row = viewButton.closest('tr');
                if (row && typeof window.openProductDetailsView === 'function') {
                    window.openProductDetailsView(row);
                }
                return;
            }
            const editButton = event.target.closest('.btn-edit-product, .edit-product-action');
            if (editButton) {
                openEditProductForm(editButton.closest('tr'));
                return;
            }
            const approveButton = event.target.closest('.btn-approve-product');
            if (approveButton) {
                openProductDecision(approveButton.closest('tr'), 'approve');
                return;
            }
            const rejectButton = event.target.closest('.btn-reject-product');
            if (rejectButton) {
                openProductDecision(rejectButton.closest('tr'), 'reject');
                return;
            }
            const archiveButton = event.target.closest('.btn-archive-product, .btn-delete-product, .delete-product-action');
            if (archiveButton) {
                event.preventDefault();
                event.stopPropagation();
                const row = archiveButton.closest('tr');
                if (row) openProductArchiveModal(row);
                return;
            }
            const restoreButton = event.target.closest('.btn-restore-product');
            if (restoreButton) {
                event.preventDefault();
                event.stopPropagation();
                const row = restoreButton.closest('tr');
                if (row) openProductRestoreModal(row);
                return;
            }
        });
    }

    document.getElementById('confirmProductDecisionButton')?.addEventListener('click', async (event) => {
        const row = pendingProductDecisionRow;
        const action = pendingProductDecision;
        const productId = row?.dataset.productId;
        const button = event.currentTarget;
        const reason = document.getElementById('productDecisionReason')?.value.trim() || '';
        if (!row || !productId || !['approve', 'reject'].includes(action)) return;
        if (action === 'reject' && !reason) {
            document.getElementById('productDecisionReason')?.focus();
            showProductSaveToast('Enter a rejection reason.', 'error');
            return;
        }

        const originalLabel = button.textContent;
        button.disabled = true;
        button.textContent = 'Saving...';
        try {
            const body = new FormData();
            if (action === 'reject') body.append('rejection_reason', reason);
            const response = await fetch(`/api/marketplace/products/${encodeURIComponent(productId)}/${action}/`, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    Accept: 'application/json',
                    'X-CSRFToken': getCsrfCookie(),
                    'X-Requested-With': 'XMLHttpRequest',
                },
                body,
            });
            const data = await window.CampusHubActions.json(response, 'Unable to confirm the update. Reload the record before retrying.');
            if (data.ok !== true) throw new Error('The product decision was not confirmed. Reload before retrying.');

            const nextStatus = action === 'approve' ? 'approved' : 'rejected';
            row.dataset.productStatus = nextStatus;
            const statusCell = row.querySelector('.col-status');
            if (statusCell) statusCell.innerHTML = renderStatusPill(nextStatus);
            const actionCell = row.querySelector('.col-action');
            if (actionCell) actionCell.outerHTML = renderProductActionsCell(nextStatus);

            const modal = document.getElementById('productDecisionModal');
            if (modal && window.bootstrap?.Modal) window.bootstrap.Modal.getOrCreateInstance(modal).hide();
            pendingProductDecisionRow = null;
            pendingProductDecision = '';
            applyInlineFilters();
            window.dispatchEvent(new Event('products-table-changed'));
            showProductSaveToast(`Product ${nextStatus}.`);
        } catch (error) {
            showProductSaveToast(error.message || `Could not ${action} product.`, 'error');
        } finally {
            button.disabled = false;
            button.textContent = originalLabel;
        }
    });

    // â”€â”€ Filter â”€â”€
    const filterBtn = document.getElementById('productsFilterBtn');
    const filterDropdown = document.getElementById('productsFilterDropdown');
    const filterBadge = document.getElementById('productsFilterBadge');
    const filterClearBtn = document.getElementById('filterClearBtn');

    function applyFilters() {
        const searchQuery = productsSearchInput ? productsSearchInput.value.trim().toLowerCase() : '';
        const checkedStatuses = [...document.querySelectorAll('input[name="filterStatus"]:checked')].map(i => i.value.toLowerCase());
        const checkedCategories = [...document.querySelectorAll('input[name="filterCategory"]:checked')].map(i => i.value.toLowerCase());

        const activeCount = checkedStatuses.length + checkedCategories.length;
        if (filterBadge) {
            filterBadge.textContent = activeCount;
            filterBadge.classList.toggle('hidden', activeCount === 0);
        }

        const labelEl = filterBtn ? filterBtn.querySelector('.filter-label-text') : null;
        if (labelEl) {
            const allSelected = [
                ...[...document.querySelectorAll('input[name="filterStatus"]:checked')].map(i => i.value),
                ...[...document.querySelectorAll('input[name="filterCategory"]:checked')].map(i => i.value)
            ];
            labelEl.textContent = allSelected.length === 0 ? 'Filter'
                : allSelected.length === 1 ? allSelected[0]
                : `${allSelected[0]} +${allSelected.length - 1}`;
        }

        if (!productsTableBody) return;
        productsTableBody.querySelectorAll('tr:not(.empty-products-row):not(.filter-empty-row)').forEach((row) => {
            const text = row.textContent.toLowerCase();
            const rowStatus = row.children[5]?.textContent.trim().toLowerCase() || '';
            const rowCategory = row.children[2]?.textContent.trim().toLowerCase() || '';
            const matchesSearch = !searchQuery || text.includes(searchQuery);
            const matchesStatus = checkedStatuses.length === 0 || checkedStatuses.includes(rowStatus);
            const matchesCategory = checkedCategories.length === 0 || checkedCategories.some(c => rowCategory.includes(c));
            row.style.display = matchesSearch && matchesStatus && matchesCategory ? '' : 'none';
        });
    }

    if (filterBtn && filterDropdown) {
        filterBtn.addEventListener('click', (e) => {
            e.stopPropagation();
            const isOpen = filterDropdown.classList.toggle('is-open');
            filterBtn.classList.toggle('is-open', isOpen);
            filterBtn.setAttribute('aria-expanded', String(isOpen));
        });
        document.addEventListener('click', (e) => {
            if (!filterDropdown.contains(e.target) && e.target !== filterBtn) {
                filterDropdown.classList.remove('is-open');
                filterBtn.classList.remove('is-open');
                filterBtn.setAttribute('aria-expanded', 'false');
            }
        });
        filterDropdown.querySelectorAll('input[type="checkbox"]').forEach(cb => {
            cb.addEventListener('change', applyFilters);
        });
    }

    if (filterClearBtn) {
        filterClearBtn.addEventListener('click', () => {
            document.querySelectorAll('input[name="filterStatus"], input[name="filterCategory"]').forEach(cb => cb.checked = false);
            applyFilters();
        });
    }

    if (productsSearchInput && productsTableBody) {
        // Search has one debounced handler below.
    }

    // â”€â”€ Inline status/category filter selects â”€â”€
    const statusFilter = document.getElementById('productsStatusFilter');
    const archiveFilter = document.getElementById('productsArchiveFilter');
    const categoryFilter = document.getElementById('productsCategoryFilter');
    const departmentFilter = document.getElementById('productsDepartmentFilter');

    const majorFilter = document.getElementById('productsMajorFilter');
    function applyInlineFilters() {
        const search = productsSearchInput?.value.trim().toLowerCase() || '';
        const status = statusFilter?.value || '';
        const listing = archiveFilter?.value ?? 'active';
        const category = categoryFilter?.value || '';
        const program = departmentFilter?.value || '';
        const major = majorFilter?.disabled ? '' : (majorFilter?.value || '');
        productsTableBody?.querySelectorAll('tr[data-product-id]').forEach(row => {
            const archived = ['1','true'].includes(row.dataset.isArchived);
            const searchable = [row.querySelector('.product-name-meta strong')?.textContent, row.querySelector('.col-seller strong')?.textContent, row.dataset.sku].join(' ').toLowerCase();
            const matches = (!search || searchable.includes(search)) && (!status || row.dataset.productStatus === status)
                && (!listing || (listing === 'archived' ? archived : !archived))
                && (!category || row.dataset.productCategory === category)
                && (!program || row.dataset.departmentId === program) && (!major || row.dataset.majorId === major)
                && (!activeInventoryFilter || row.dataset.inventoryStatus === activeInventoryFilter || (activeInventoryFilter === 'low_stock' && row.dataset.hasLowStock === '1'));
            row.style.display = matches ? '' : 'none';
        });
        const url = new URL(window.location.href);
        const values = {search, status, listing_status: listing, program, major, category, inventory_status: activeInventoryFilter};
        Object.entries(values).forEach(([key,value]) => value ? url.searchParams.set(key,value) : url.searchParams.delete(key));
        url.searchParams.delete('page');
        window.history.replaceState(null, '', url);
        window.__chSyncProductEmptyState?.();
    }

    document.querySelectorAll('#productStatsGrid [data-stat-filter]').forEach((card) => {
        const activate = () => applyStatCardFilter(card.dataset.statFilter || 'all');
        card.addEventListener('click', activate);
        card.addEventListener('keydown', (event) => {
            if (event.key === 'Enter' || event.key === ' ') {
                event.preventDefault();
                activate();
            }
        });
    });

    const clearInventoryFilterBtn = document.getElementById('clearInventoryFilterBtn');
    if (clearInventoryFilterBtn) {
        clearInventoryFilterBtn.addEventListener('click', () => {
            activeStatFilter = '';
            setInventoryFilter('');
        });
    }

    if (statusFilter) {
        statusFilter.addEventListener('change', () => {
            const value = (statusFilter.value || '').toLowerCase();
            if (value === 'pending' || value === 'approved') {
                activeStatFilter = value;
                activeInventoryFilter = '';
                window.__chProductStatFilter = value;
            } else {
                if (activeStatFilter === 'pending' || activeStatFilter === 'approved') {
                    activeStatFilter = '';
                }
                window.__chProductStatFilter = activeInventoryFilter || '';
            }
            updateStatCardActiveState();
            applyInlineFilters();
            if (typeof window.__chSyncProductEmptyState === 'function') {
                window.__chSyncProductEmptyState();
            }
        });
    }
        if (archiveFilter) {
        archiveFilter.addEventListener('change', () => {
            applyInlineFilters();
            if (typeof window.__chSyncProductEmptyState === 'function') {
                window.__chSyncProductEmptyState();
            }
        });
    }
    if (categoryFilter) categoryFilter.addEventListener('change', applyInlineFilters);
    if (departmentFilter) departmentFilter.addEventListener('change', applyInlineFilters);
    let searchTimer;
    productsSearchInput?.addEventListener('input', () => { clearTimeout(searchTimer); searchTimer = setTimeout(() => { applyInlineFilters(); window.dispatchEvent(new Event('products-table-changed')); }, 300); });
    majorFilter?.addEventListener('change', applyInlineFilters);
    document.getElementById('productsClearFilters')?.addEventListener('click', () => {
        clearTimeout(searchTimer);
        [productsSearchInput,statusFilter,archiveFilter,departmentFilter,majorFilter,categoryFilter].forEach(field => { if (field) field.value = ''; });
        activeInventoryFilter = ''; activeStatFilter = '';
        window.CampusHubAcademic?.sync(departmentFilter, majorFilter);
        updateStatCardActiveState(); applyInlineFilters();
        window.dispatchEvent(new Event('products-table-changed'));
    });

    // Operational dashboard shortcuts open the existing inline filters.
    const shortcutParams = new URLSearchParams(window.location.search);
    [[productsSearchInput,'search'],[statusFilter,'status'],[archiveFilter,'listing_status'],[departmentFilter,'program'],[categoryFilter,'category']].forEach(([field,key]) => { if (field && shortcutParams.has(key)) field.value = shortcutParams.get(key); });
    window.CampusHubAcademic?.sync(departmentFilter, majorFilter);
    if (majorFilter && !majorFilter.disabled) majorFilter.value = shortcutParams.get('major') || '';
    applyInlineFilters();
    const shortcutInventory = shortcutParams.get('inventory_status');
    const shortcutStatus = shortcutParams.get('status');
    if (['low_stock', 'out_of_stock'].includes(shortcutInventory)) {
        setInventoryFilter(shortcutInventory);
    } else if (statusFilter && ['pending', 'approved', 'rejected'].includes(shortcutStatus)) {
        statusFilter.value = shortcutStatus;
        statusFilter.classList.add('is-active');
        activeStatFilter = ['pending', 'approved'].includes(shortcutStatus) ? shortcutStatus : '';
        updateStatCardActiveState();
        applyInlineFilters();
    }

    // === Active state classes for search bar and filters (navy blue) ===
    if (productsSearchInput) {
        productsSearchInput.addEventListener('focus', () => {
            const container = productsSearchInput.closest('.products-search');
            if (container) container.classList.add('is-focused');
        });
        productsSearchInput.addEventListener('blur', () => {
            const container = productsSearchInput.closest('.products-search');
            if (container) container.classList.remove('is-focused');
        });
    }
    if (statusFilter) {
        statusFilter.addEventListener('change', () => {
            statusFilter.classList.toggle('is-active', !!statusFilter.value);
        });
    }
    if (categoryFilter) {
        categoryFilter.addEventListener('change', () => {
            categoryFilter.classList.toggle('is-active', !!categoryFilter.value);
        });
    }

    function clearStatFilters() {
        activeStatFilter = '';
        activeInventoryFilter = '';
        window.__chProductStatFilter = '';
        const statusFilterEl = document.getElementById('productsStatusFilter');
        const categoryFilterEl = document.getElementById('productsCategoryFilter');
        const searchInput = document.getElementById('productsSearchInput');
                if (statusFilterEl) {
            statusFilterEl.value = '';
            statusFilterEl.classList.remove('is-active');
        }
        if (categoryFilterEl) {
            categoryFilterEl.value = '';
            categoryFilterEl.classList.remove('is-active');
        }
        if (searchInput) {
            searchInput.value = '';
            const searchContainer = searchInput.closest('.products-search');
            if (searchContainer) searchContainer.classList.remove('is-focused');
        }
        updateStatCardActiveState();
        applyInlineFilters();
        if (typeof window.__chSyncProductEmptyState === 'function') {
            window.__chSyncProductEmptyState();
        }
    }

    window.CampusHubAdminProducts = {
        getProductFromRow,
        renderProductActionsCell,
        applyInlineFilters,
        computeProductAvailability,
        computeTotalStock,
        countProductVariants,
        renderInventorySummary,
        showProductSaveToast,
        computeInventoryStatus,
        computeProductQuantityStatus,
        deriveExpiryFromCustomization,
        inventoryStatusLabel,
        INVENTORY_LABELS,
        isPerishableCategory,
        customizationHasStockTracking,
        hasCustomizationOptions,
        openEditProductForm,
        clearStatFilters,
        applyStatCardFilter,
        getActiveStatFilter: () => activeStatFilter,
        getActiveInventoryFilter: () => activeInventoryFilter,
    };
});


// â”€â”€ Functional Pagination â”€â”€
function initializeProductPagination() {
    const tbody = document.getElementById('productsTableBody');
    const showingText = document.getElementById('productsShowingText');
    const paginationContainer = document.getElementById('productsPagination');
    if (!tbody || !paginationContainer) return;

    let currentPage = 1;
    const rowsPerPage = 10;

    function getVisibleRows() {
        return [...tbody.querySelectorAll('tr:not(.empty-products-row)')].filter(
            (row) => row.style.display !== 'none'
        );
    }

    function getFilterEmptyCopy() {
        // Prefer the explicit key set by card clicks — avoids stale "pending" messages
        const key = window.__chProductStatFilter
            || window.CampusHubAdminProducts?.getActiveStatFilter?.()
            || document.getElementById('productStatsGrid')?.dataset.activeFilter
            || '';

        if (key === 'approved') {
            return { title: 'No approved products', hint: '', icon: 'default' };
        }
        if (key === 'pending') {
            return { title: 'No pending listings', hint: '', icon: 'default' };
        }
        if (key === 'low_stock') {
            return { title: 'No low stock alerts', hint: '', icon: 'default' };
        }

        const statusValue = (document.getElementById('productsStatusFilter')?.value || '').toLowerCase();
        if (statusValue === 'approved') {
            return { title: 'No approved products', hint: '', icon: 'default' };
        }
        if (statusValue === 'pending') {
            return { title: 'No pending listings', hint: '', icon: 'default' };
        }
        if (statusValue === 'rejected') {
            return { title: 'No rejected listings', hint: '', icon: 'default' };
        }

        const search = (document.getElementById('productsSearchInput')?.value || '').trim();
        const category = document.getElementById('productsCategoryFilter')?.value || '';
        if (search || category || statusValue) {
            return { title: '', hint: '', icon: 'default' };
        }
        return { title: 'No Products Found', hint: '', icon: 'default' };
    }

    function setEmptyStateIcon() {
        const iconWrap = document.getElementById('productsEmptyStateIcon');
        if (!iconWrap) return;
        iconWrap.className = 'products-empty-state-icon';
        iconWrap.style.display = 'flex';
        // Neutral package icon only (no caution / warning triangle)
        iconWrap.innerHTML = `
            <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.7" stroke="currentColor" width="22" height="22" aria-hidden="true">
                <path stroke-linecap="round" stroke-linejoin="round" d="M20.25 7.5l-.625 10.632a2.25 2.25 0 0 1-2.247 2.118H6.622a2.25 2.25 0 0 1-2.247-2.118L3.75 7.5m8.25 3v6.75m0 0-3-3m3 3 3-3M3.375 7.5h17.25c.621 0 1.125-.504 1.125-1.125v-1.5c0-.621-.504-1.125-1.125-1.125H3.375c-.621 0-1.125.504-1.125 1.125v1.5c0 .621.504 1.125 1.125 1.125Z"/>
            </svg>`;
    }

    function syncProductEmptyState() {
        const allProductRows = [...tbody.querySelectorAll('tr:not(.empty-products-row):not(.filter-empty-row)')];
        const visibleCount = allProductRows.filter((row) => row.style.display !== 'none').length;
        const tableFooter = document.getElementById('productsTableFooter');
        const tableWrap = document.getElementById('productsTableWrap');
        const emptyState = document.getElementById('productsEmptyState');
        const emptyTitle = document.getElementById('productsEmptyStateTitle');
        const emptyHint = document.getElementById('productsEmptyStateHint');

        if (visibleCount === 0) {
            const copy = getFilterEmptyCopy();
            setEmptyStateIcon();
            if (tableFooter) tableFooter.style.display = 'none';
            if (tableWrap) tableWrap.style.display = 'none';
            if (emptyState) {
                emptyState.classList.remove('d-none');
                emptyState.classList.add('is-visible');
            }
            if (emptyTitle) {
                emptyTitle.textContent = copy.title || '';
                emptyTitle.classList.toggle('d-none', !copy.title);
            }
            if (emptyHint) {
                emptyHint.textContent = '';
                emptyHint.classList.add('d-none');
            }
            return false;
        }

        if (tableFooter) tableFooter.style.display = '';
        if (tableWrap) tableWrap.style.display = '';
        if (emptyState) {
            emptyState.classList.add('d-none');
            emptyState.classList.remove('is-visible');
        }
        return true;
    }
    window.__chSyncProductEmptyState = syncProductEmptyState;

    function renderPagination() {
        tbody.querySelectorAll('tr.filter-empty-row').forEach((row) => row.remove());

        const allProductRows = [...tbody.querySelectorAll('tr:not(.empty-products-row):not(.filter-empty-row)')];
        const visibleForPage = allProductRows.filter((row) => row.style.display !== 'none');
        const totalRows = visibleForPage.length;
        const totalPages = Math.max(1, Math.ceil(totalRows / rowsPerPage));
        if (currentPage > totalPages) currentPage = totalPages;

        const startIdx = (currentPage - 1) * rowsPerPage;
        const endIdx = Math.min(startIdx + rowsPerPage, totalRows);

        allProductRows.forEach((row) => {
            row.hidden = true;
        });
        visibleForPage.forEach((row, i) => {
            row.hidden = i < startIdx || i >= endIdx;
        });

        if (showingText) {
            if (totalRows === 0) {
                showingText.textContent = 'No entries';
            } else if (totalPages <= 1) {
                showingText.textContent = totalRows === 1
                    ? 'Showing 1 of 1 entry'
                    : `Showing all ${totalRows} entries`;
            } else {
                showingText.textContent = `Showing ${startIdx + 1} to ${endIdx} of ${totalRows} entries`;
            }
        }

        const hasRows = syncProductEmptyState();
        if (!hasRows) {
            paginationContainer.innerHTML = '';
            paginationContainer.style.display = 'none';
            return;
        }
        paginationContainer.style.display = '';

        let html = '';
        html += `<button type="button" class="page-btn page-btn-nav" data-page="prev" aria-label="Previous page" ${currentPage === 1 ? 'disabled' : ''}>&lsaquo;</button>`;

        for (let p = 1; p <= totalPages; p++) {
            if (totalPages <= 7 || p <= 3 || p > totalPages - 2 || Math.abs(p - currentPage) <= 1) {
                html += `<button type="button" class="page-btn ${p === currentPage ? 'is-active' : ''}" data-page="${p}" aria-label="Page ${p}" ${p === currentPage ? 'aria-current="page"' : ''}>${p}</button>`;
            } else if (p === 4 && currentPage > 5) {
                html += '<span class="page-ellipsis">...</span>';
            } else if (p === totalPages - 2 && currentPage < totalPages - 4) {
                html += '<span class="page-ellipsis">...</span>';
            }
        }

        html += `<button type="button" class="page-btn page-btn-nav" data-page="next" aria-label="Next page" ${currentPage === totalPages ? 'disabled' : ''}>&rsaquo;</button>`;
        paginationContainer.innerHTML = html;
    }

    paginationContainer.addEventListener('click', (e) => {
        const btn = e.target.closest('[data-page]');
        if (!btn || btn.disabled) return;
        const val = btn.dataset.page;
        if (val === 'prev') currentPage--;
        else if (val === 'next') currentPage++;
        else currentPage = parseInt(val, 10);
        renderPagination();
    });

    window.addEventListener('products-table-changed', () => {
        currentPage = 1;
        renderPagination();
    });

    const emptyClearBtn = document.getElementById('productsEmptyClearFilterBtn');
    if (emptyClearBtn) {
        emptyClearBtn.addEventListener('click', () => {
            window.CampusHubAdminProducts?.clearStatFilters?.();
        });
    }

    // Re-render pagination when rows are added/removed or filter visibility changes
    let paginationRefreshTimer = null;
    let isRenderingPagination = false;
    const observer = new MutationObserver(() => {
        if (isRenderingPagination) return;
        clearTimeout(paginationRefreshTimer);
        paginationRefreshTimer = setTimeout(() => {
            currentPage = 1;
            isRenderingPagination = true;
            try {
                renderPagination();
            } finally {
                // Allow observer again after style writes settle
                setTimeout(() => {
                    isRenderingPagination = false;
                }, 0);
            }
        }, 30);
    });
    observer.observe(tbody, { childList: true, subtree: true, attributes: true, attributeFilter: ['style', 'class'] });

    isRenderingPagination = true;
    try {
        renderPagination();
    } finally {
        setTimeout(() => {
            isRenderingPagination = false;
        }, 0);
    }
}
if (document.readyState === 'loading') document.addEventListener('DOMContentLoaded', initializeProductPagination, {once:true});
else initializeProductPagination();


// ── Product Details Section (eye icon) ──
(function () {
    const section = document.getElementById('productDetailsSection');
    const listSection = document.getElementById('productsListSection');
    const formSection = document.getElementById('productFormSection');
    const loadingSection = document.getElementById('productLoadingSection');
    const statsGrid = document.getElementById('productStatsGrid');
    if (!section) return;
    // Details actions reuse the list's helpers after DOM initialization.
    const renderProductActionsCell = (...args) => window.CampusHubAdminProducts.renderProductActionsCell(...args);
    const applyInlineFilters = () => window.CampusHubAdminProducts.applyInlineFilters();
    const showProductSaveToast = (...args) => window.CampusHubAdminProducts.showProductSaveToast(...args);

    const mainImage = document.getElementById('pdMainImage');
    const counter = document.getElementById('pdImageCounter');
    const optionLabel = document.getElementById('pdImageOptionName');
    const prevBtn = document.getElementById('pdPrevImg');
    const nextBtn = document.getElementById('pdNextImg');
    const thumbnails = document.getElementById('pdThumbnails');
    const thumbPrev = document.getElementById('pdThumbPrev');
    const thumbNext = document.getElementById('pdThumbNext');

    let images = [];
    let optionNames = [];
    let variantGalleryItems = [];
    let activeProduct = null;
    let currentIdx = 0;
    let activeProductId = '';
    let activeDetailsRow = null;

    function formatPdDate(value) {
        if (!value) return '—';
        const raw = String(value).trim();
        if (!raw) return '—';
        const iso = raw.includes('T') ? raw : `${raw}T12:00:00`;
        const date = new Date(iso);
        if (Number.isNaN(date.getTime())) return raw;
        return date.toLocaleDateString(undefined, { month: 'short', day: 'numeric', year: 'numeric' });
    }

    function formatPdDateTime(value) {
        if (!value) return '—';
        const raw = String(value).trim();
        if (!raw) return '—';
        // A date without a time must not acquire an invented noon timestamp.
        if (!raw.includes('T')) return formatPdDate(raw);
        const date = new Date(raw);
        if (Number.isNaN(date.getTime())) return raw;
        const locale = 'en-US';
        const timeZone = 'Asia/Manila';
        const day = date.toLocaleDateString(locale, { timeZone, month: 'short', day: 'numeric', year: 'numeric' });
        const time = date.toLocaleTimeString(locale, { timeZone, hour: 'numeric', minute: '2-digit' });
        return `${day} · ${time}`;
    }

    function formatMoney(value) {
        const num = parseFloat(value) || 0;
        return `₱ ${num.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
    }

    function capitalizeStatus(status) {
        const s = String(status || '').trim();
        if (!s) return '—';
        return s.charAt(0).toUpperCase() + s.slice(1);
    }

    function buildVariantRows(product, helpers) {
        const category = product.category || '';
        const inventoryStatus = helpers.computeProductAvailability?.(product) || product.inventory_status || 'in_stock';
        const labels = helpers.INVENTORY_LABELS || {};
        const rows = [];
        const groups = Array.isArray(product.customization_options) ? product.customization_options : [];
        const tracksStock = helpers.customizationHasStockTracking?.(product.customization_options);

        groups.forEach((group) => {
            const groupName = (group?.name || 'Variation').trim();
            (group?.options || []).forEach((opt) => {
                const hasStock = opt && typeof opt === 'object' && 'stock' in opt;
                const stock = hasStock ? (parseInt(opt.stock, 10) || 0) : null;
                const expiry = opt?.expiry_date || '';
                const extra = parseFloat(opt?.extra_price || 0) || 0;
                const status = stock === null
                    ? inventoryStatus
                    : (helpers.computeInventoryStatus?.(stock, expiry, category, opt.low_stock_threshold ?? helpers.LOW_STOCK_THRESHOLD) || 'in_stock');
                rows.push({
                    groupName,
                    optionName: (opt?.name || 'Option').trim(),
                    extraPrice: extra,
                    imageUrl: opt?.image || '',
                    stock,
                    expiry,
                    status,
                    statusLabel: labels[status] || status,
                    stockUnset: stock === null,
                });
            });
        });

        if (!rows.length) {
            const stock = parseInt(product.stock, 10) || 0;
            const expiry = product.expiry_date || '';
            const status = helpers.computeInventoryStatus?.(stock, expiry, category, product.low_stock_threshold ?? helpers.LOW_STOCK_THRESHOLD) || inventoryStatus;
            rows.push({
                groupName: '—',
                optionName: product.name || 'Base product',
                extraPrice: 0,
                stock,
                status,
                statusLabel: labels[status] || status,
                stockUnset: false,
            });
        } else if (!tracksStock) {
            const stock = parseInt(product.stock, 10) || 0;
            rows.forEach((row) => {
                row.stock = null;
                row.stockUnset = true;
            });
        }

        return rows;
    }

    function buildVariantGalleryItems(product, helpers) {
        const rows = buildVariantRows(product, helpers);
        const basePrice = parseFloat(product.price) || 0;
        const productUpdated = product.updated_at || product.submitted_at || '';
        const fallbackStatus = helpers.computeProductAvailability?.(product) || product.inventory_status || 'in_stock';

        if (!rows.length) {
            return [{
                optionName: '',
                groupName: '',
                displayName: product.name || '',
                price: basePrice,
                inventoryStatus: fallbackStatus,
                updatedAt: productUpdated,
                stock: parseInt(product.stock, 10) || 0,
                expiry: product.expiry_date || '',
            }];
        }

        return rows.map((row) => {
            const inventoryStatus = row.stockUnset || row.stock === null
                ? fallbackStatus
                : row.status;
            const displayName = row.optionName && row.optionName !== (product.name || 'Base product')
                ? `${product.name || ''} — ${row.optionName}`
                : (product.name || '');
            return {
                optionName: row.optionName,
                groupName: row.groupName,
                imageUrl: row.imageUrl,
                displayName,
                price: basePrice + (row.extraPrice || 0),
                inventoryStatus,
                updatedAt: productUpdated,
                stock: row.stock,
                expiry: row.expiry || '',
            };
        });
    }

    function getVariantItemForIndex(idx) {
        if (!variantGalleryItems.length) return null;
        if (variantGalleryItems.some(item => item.imageUrl)) {
            const rawImage = parseProductImages(activeProduct?.images, activeProduct?.image_url)[idx];
            const match = variantGalleryItems.find(item => item.imageUrl === rawImage);
            // A product photo without a variant association must keep the base label.
            return match || { displayName: activeProduct?.name || '', optionName: '', price: parseFloat(activeProduct?.price) || 0 };
        }
        return variantGalleryItems[idx] ?? variantGalleryItems[idx % variantGalleryItems.length];
    }

    function updateHeroVariantDisplay(idx) {
        if (!activeProduct) return;
        const item = getVariantItemForIndex(idx);
        if (!item) return;

        const nameEl = document.getElementById('pdName');
        if (nameEl) nameEl.textContent = item.displayName || activeProduct.name || '';

        const metaEl = document.getElementById('pdMeta');
        const productId = activeProduct.id || '';
        if (metaEl) {
            metaEl.textContent = activeProduct.product_code || `PRD-${String(productId).padStart(4, '0')}`;
        }

        const priceEl = document.getElementById('pdPrice');
        if (priceEl) {
            priceEl.textContent = `₱ ${item.price.toLocaleString(undefined, { minimumFractionDigits: 2, maximumFractionDigits: 2 })}`;
        }

        const updatedEl = document.getElementById('pdUpdated');
        if (updatedEl) {
            updatedEl.textContent = formatPdDateTime(activeProduct.updated_at);
        }

        updateOptionLabel();
    }

    function populateVariationsTable(product, helpers) {
        const section = document.getElementById('pdVariantInventorySection');
        const tbody = document.getElementById('pdVariationsTableBody');
        if (!tbody) return;
        const countEl = document.getElementById('pdVariantInventoryCount');
        const groups = Array.isArray(product.customization_options) ? product.customization_options : [];
        const hasVariants = groups.some((group) => Array.isArray(group?.options) && group.options.length > 0);

        section?.classList.toggle('d-none', !hasVariants);
        if (!hasVariants) {
            tbody.innerHTML = '';
            if (countEl) countEl.textContent = '0 variants';
            return;
        }

        const rows = buildVariantRows(product, helpers);
        if (!rows.length) {
            tbody.innerHTML = '<tr><td colspan="6" class="pd-empty-cell"></td></tr>';
            return;
        }

        if (countEl) {
            countEl.textContent = `${rows.length} variant${rows.length === 1 ? '' : 's'}`;
        }
        const basePrice = parseFloat(product.price) || 0;
        tbody.innerHTML = rows.map((row) => {
            const stockLabel = row.stockUnset ? 'Not set' : String(row.stock);
            const expiryLabel = row.expiry ? formatPdDate(row.expiry) : 'None';
            const statusClass = String(row.status || 'in_stock').replace(/[^a-z_]/g, '');
            return `<tr>
                <td>${escapeHtml(row.groupName)}</td>
                <td class="pd-variant-name">${escapeHtml(row.optionName)}</td>
                <td class="pd-variant-price">${escapeHtml(formatMoney(basePrice + row.extraPrice))}</td>
                <td class="pd-variant-stock">${escapeHtml(stockLabel)}</td>
                <td>${escapeHtml(expiryLabel)}</td>
                <td><span class="inventory-pill inventory-${statusClass}">${escapeHtml(row.statusLabel)}</span></td>
            </tr>`;
        }).join('');
    }

    function getStockUnit(category) {
        const cat = String(category || '').toLowerCase();
        if (cat.includes('beverage') || cat.includes('drink') || cat.includes('milk')) return 'cups';
        if (cat.includes('snack') || cat.includes('food') || cat.includes('meal')) return 'pcs';
        return 'units';
    }

    function setInventoryKpiDisplay(id, amount) {
        const el = document.getElementById(id);
        if (!el) return;
        const val = Number(amount) || 0;
        el.innerHTML = `${val} <span class="pd-inventory-unit">${val === 1 ? 'pc' : 'pcs'}</span>`;
    }

    function populateInventoryHistory(product, failed = false) {
        const tbody = document.getElementById('pdInventoryHistoryBody');
        if (!tbody) return;
        const historyWrap = tbody.closest(".pd-inventory-history-wrap");
        const showHistory = product.can_view_stock_movements !== false;
        if (historyWrap) {
            historyWrap.hidden = !showHistory;
            if (historyWrap.previousElementSibling) historyWrap.previousElementSibling.hidden = !showHistory;
        }
        if (!showHistory) return;
        if (!Array.isArray(product.stock_movements)) {
            tbody.innerHTML = failed
                ? '<tr><td colspan="7">Unable to load recorded stock movements. Reopen this product to retry.</td></tr>'
                : '<tr><td colspan="7">Loading recorded stock movements…</td></tr>';
            return;
        }
        tbody.innerHTML = product.stock_movements.length ? product.stock_movements.map(event => `<tr>
            <td>${escapeHtml(formatPdDateTime(event.date))}<small>${escapeHtml(event.sku)}</small></td>
            <td>${escapeHtml(event.kind)}<small>${escapeHtml(event.balance)}</small></td>
            <td>${event.quantity > 0 ? '+' : ''}${Number(event.quantity)}</td>
            <td>${event.before ?? '—'}</td><td>${event.after ?? '—'}</td>
            <td>${escapeHtml(event.reference)}</td><td>${escapeHtml(event.actor)}</td></tr>`).join('')
            : '<tr><td colspan="7">No recorded stock movements.</td></tr>';
    }

    function populateInventoryKpis(product, failed = false) {
        const inventory = product.inventory;
        const skuEl = document.getElementById('pdInventorySku');
        if (skuEl) skuEl.textContent = inventory?.variant_thresholds?.length ? 'Per variant' : (inventory?.sku || product.sku || 'Unavailable');
        const feedback = document.getElementById('pdInventoryFeedback');
        const summaryEl = document.getElementById('pdInventorySummary');
        const headingEl = document.getElementById('pdInventoryHeading');
        const bundleMode = product.product_type === 'bundle';
        document.getElementById('pdMenuUpdateStock')?.classList.toggle('d-none', bundleMode);
        if (bundleMode && inventory) {
            summaryEl?.classList.add('d-none');
            if (headingEl) headingEl.textContent = 'Bundle Inventory';
            const componentEl = document.getElementById('pdVariantThresholds');
            componentEl?.classList.remove('d-none');
            if (componentEl) componentEl.innerHTML = `<p><strong>Derived Availability: ${inventory.available} bundle${inventory.available === 1 ? '' : 's'}</strong></p><table class="table table-sm"><thead><tr><th>Component / Variant</th><th>Required Quantity</th><th>Available Stock</th></tr></thead><tbody>${inventory.components.map(row => `<tr><th>${escapeHtml(row.product_name)}<small class="d-block">${escapeHtml(row.variant)}</small></th><td>${row.required_quantity}</td><td>${row.available}</td></tr>`).join('')}</tbody></table>`;
            const statusEl = document.getElementById('pdInventoryStatus');
            if (statusEl) { statusEl.textContent = inventory.status_label; statusEl.className = `pd-inventory-state pd-inventory-state--${inventory.status}`; }
            if (feedback) feedback.hidden = true;
            return;
        }
        if (!inventory) {
            const tracksVariants = (product.customization_options || []).some(group => (group.options || []).some(option => Object.prototype.hasOwnProperty.call(option, 'stock')));
            if (summaryEl) summaryEl.classList.toggle('d-none', tracksVariants || bundleMode);
            if (headingEl) headingEl.textContent = bundleMode ? 'Bundle Inventory' : tracksVariants ? 'Variant Inventory' : 'Inventory Information';
            const variantEl = document.getElementById('pdVariantThresholds');
            if (variantEl) { variantEl.classList.add('d-none'); variantEl.textContent = ''; }
            ['pdKpiTotal', 'pdKpiReserved', 'pdKpiAvailable', 'pdKpiThreshold',
                'pdKpiStatus', 'pdInventoryStatus'].forEach(id => {
                const el = document.getElementById(id);
                if (!el) return;
                el.textContent = failed ? 'Unavailable' : 'Loading…';
                if (id === 'pdKpiStatus' || id === 'pdInventoryStatus') el.className = 'pd-inventory-state';
            });
            if (feedback) {
                feedback.hidden = false;
                feedback.textContent = failed ? 'Unable to load inventory. Reopen this product to retry.' : 'Loading inventory…';
            }
            return;
        }
        // Django supplies the snapshot; saved stock has already had holds deducted.
        setInventoryKpiDisplay('pdKpiTotal', inventory.on_hand);
        setInventoryKpiDisplay('pdKpiReserved', inventory.reserved);
        setInventoryKpiDisplay('pdKpiAvailable', inventory.available);
        const variantThresholds = inventory.variant_thresholds || [];
        if (summaryEl) summaryEl.classList.toggle('d-none', variantThresholds.length > 0);
        if (headingEl) headingEl.textContent = variantThresholds.length ? 'Variant Inventory' : 'Inventory Information';
        if (variantThresholds.length) document.getElementById('pdKpiThreshold').textContent = 'Per variant';
        else setInventoryKpiDisplay('pdKpiThreshold', inventory.low_stock_threshold);
        const variantEl = document.getElementById('pdVariantThresholds');
        if (variantEl) {
            variantEl.classList.toggle('d-none', !variantThresholds.length);
            variantEl.innerHTML = variantThresholds.length ? `<table class="table table-sm mb-3"><thead><tr><th scope="col">Variant</th><th scope="col">SKU</th><th scope="col">On Hand</th><th scope="col">Reserved</th><th scope="col">Available</th><th scope="col">Threshold</th><th scope="col">Status</th></tr></thead><tbody>${variantThresholds.map(item =>
                `<tr><th scope="row">${escapeHtml([item.group, item.name].filter(Boolean).join(' · '))}</th><td>${escapeHtml(item.sku || 'Unavailable')}</td><td>${item.on_hand}</td><td>${item.reserved}</td><td>${item.available} ${item.available === 1 ? 'pc' : 'pcs'}</td><td>${item.threshold} ${item.threshold === 1 ? 'pc' : 'pcs'}</td><td><span class="pd-inventory-state pd-inventory-state--${escapeHtml(item.status)}">${escapeHtml(item.status_label)}</span></td></tr>`).join('')}</tbody></table>` : '';
        }
        ['pdInventoryStatus', 'pdKpiStatus'].forEach(id => {
            const el = document.getElementById(id);
            if (!el) return;
            el.textContent = inventory.status_label;
            el.className = `pd-inventory-state pd-inventory-state--${inventory.status}`;
        });
        if (feedback) {
            feedback.hidden = true;
            feedback.textContent = '';
        }
    }


    function formatOrderRef(orderId) {
        return `ORD-${String(orderId || '').padStart(6, '0')}`;
    }

    function buildActivityLogEntries(product, orders = []) {
        const entries = [];
        const created = product.submitted_at || product.created_at;
        const updated = product.updated_at;
        const seller = product.seller || 'Seller';
        const unit = getStockUnit(product.category);
        const productOrders = (orders || [])
            .filter((o) => String(o.product_id) === String(product.id))
            .sort((a, b) => new Date(a.created_at) - new Date(b.created_at));

        const totalStock = parseInt(product.stock, 10) || 0;
        const totalDeducted = productOrders.reduce((sum, o) => sum + (parseInt(o.quantity, 10) || 1), 0);
        // Current stock cannot establish historic initial/restock quantities.

        if (created) {
            entries.push({
                date: created,
                action: 'Product Created',
                by: seller,
                details: 'New product added',
            });
        }

        if (updated && created && String(updated) !== String(created)) {
            entries.push({
                date: updated,
                action: 'Product Updated',
                by: seller,
                details: 'Product details updated',
            });
        }

        productOrders.forEach((order) => {
            const qty = parseInt(order.quantity, 10) || 1;
            entries.push({
                date: order.created_at,
                action: product.product_type === 'bundle' ? 'Bundle Ordered' : 'Stock Deducted',
                by: 'System',
                details: product.product_type === 'bundle' ? `Reserved components for ${qty} bundle${qty === 1 ? '' : 's'} (Order ${formatOrderRef(order.id)})` : `Deducted ${qty} ${unit} (Order ${formatOrderRef(order.id)})`,
            });
        });

        if (product.approved_at && product.approval_status === 'approved') {
            entries.push({
                date: product.approved_at,
                action: 'Status Changed',
                by: product.approved_by || 'Admin',
                details: 'Product approved for marketplace',
            });
        }

        return entries.sort((a, b) => new Date(b.date) - new Date(a.date));
    }

    function populateActivityLog(product, orders = []) {
        const tbody = document.getElementById('pdActivityLogBody');
        if (!tbody) return;

        const entries = buildActivityLogEntries(product, orders);
        if (!entries.length) {
            tbody.innerHTML = '';
            return;
        }

        tbody.innerHTML = entries.map((row) => `
            <tr>
                <td class="col-datetime">${escapeHtml(formatPdDateTime(row.date))}</td>
                <td class="col-action">${escapeHtml(row.action)}</td>
                <td class="col-by" title="${escapeHtml(row.by)}">${escapeHtml(row.by)}</td>
                <td class="col-details">${escapeHtml(row.details)}</td>
            </tr>`).join('');
    }

    function buildProductTags(product) {
        const tags = new Set();
        const name = (product.name || '').trim();
        const category = (product.category || '').trim();
        if (name) tags.add(name);
        if (category) tags.add(category);
        const extras = {
            Beverages: ['Cold', 'Sweet'],
            Snacks: ['Quick Bite'],
            Desserts: ['Sweet'],
            'Rice Meals': ['Hot', 'Meal'],
            Breakfast: ['Morning'],
        };
        (extras[category] || ['Campus']).forEach((t) => tags.add(t));
        return [...tags].slice(0, 5);
    }

    function populateProductTags(product) {
        const container = document.getElementById('pdTags');
        if (!container) return;
        const tags = buildProductTags(product);
        container.innerHTML = tags.map((tag) => `<span class="pd-tag">${escapeHtml(tag)}</span>`).join('');
    }

    function populateOrdersTable(orders, productId) {
        const tbody = document.getElementById('pdOrdersTableBody');
        if (!tbody) return;

        const productOrders = (orders || [])
            .filter((o) => String(o.product_id) === String(productId))
            .sort((a, b) => new Date(b.created_at) - new Date(a.created_at))
            .slice(0, 10);

        if (!productOrders.length) {
            tbody.innerHTML = '';
            return;
        }

        tbody.innerHTML = productOrders.map((order) => {
            const statusClass = `pd-order-status pd-order-status--${escapeHtml(order.status || 'pending')}`;
            const variant = String(order.option || order.customization?.summary || 'Standard').trim() || 'Standard';
            return `<tr>
                <td>ORD-${String(order.id).padStart(4, '0')}</td>
                <td class="col-date text-nowrap">${escapeHtml(formatPdDate(order.created_at))}</td>
                <td>${escapeHtml(order.buyer_name || '—')}</td>
                <td class="col-variant" title="${escapeHtml(variant)}">${escapeHtml(variant)}</td>
                <td class="col-qty">${order.quantity || 1}</td>
                <td class="col-amount">${escapeHtml(formatMoney(order.total_price))}</td>
                <td class="col-status"><span class="${statusClass}">${escapeHtml(capitalizeStatus(order.status))}</span></td>
            </tr>`;
        }).join('');
    }

    function populateSalesFromOrders(orders, productId, variantRows) {
        const productOrders = (orders || []).filter(o => String(o.product_id) === String(productId) && o.status === 'completed' && o.payment_status === 'paid');
        let totalSold = 0;
        let totalRevenue = 0;
        const variantCounts = {};

        productOrders.forEach((order) => {
            const qty = parseInt(order.quantity, 10) || 1;
            totalSold += qty;
            totalRevenue += parseFloat(order.total_price) || 0;
            const key = (order.option || order.customization?.summary || 'Standard').trim();
            variantCounts[key] = (variantCounts[key] || 0) + qty;
        });

        const set = (id, val) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val;
        };

        set('pdSalesSold', String(totalSold));
        set('pdSalesRevenue', formatMoney(totalRevenue));
        set('pdSalesOrders', String(productOrders.length));

        const best = Object.entries(variantCounts).sort((a, b) => b[1] - a[1])[0];
        const bestEl = document.getElementById('pdBestVariation');
        if (bestEl) {
            bestEl.textContent = best
                ? `Best selling: ${best[0]} (${best[1]} sold)`
                : '';
        }
    }

    async function fetchOrdersFromServer() {
        try {
            const response = await fetch('/api/orders/', {
                credentials: 'same-origin',
                headers: { Accept: 'application/json' },
            });
            if (!response.ok) return [];
            const data = await response.json();
            return data.orders || [];
        } catch (_) {
            return [];
        }
    }

    function populateProductDetails(product) {
        const helpers = window.CampusHubAdminProducts || {};
        const inventoryStatus = helpers.computeProductAvailability?.(product) || product.inventory_status || 'in_stock';
        const status = product.approval_status || product.product_status || 'pending';
        const department = product.department || 'Not Assigned';
        const dateStr = product.submitted_at || '';
        const updatedStr = product.updated_at || '';
        const isPending = normalizeStatus(status) === 'pending';
        const isArchived = Boolean(
            product.is_archived === true ||
            product.is_archived === '1' ||
            product.is_archived === 'true' ||
            (activeDetailsRow && (activeDetailsRow.dataset.isArchived === '1' || activeDetailsRow.dataset.isArchived === 'true'))
        );
        const description = (product.description || '').trim() || '—';

        const canEdit = document.querySelector('meta[name="can-manage-products"]')?.content === 'true';
        document.getElementById('pdEditBtn')?.classList.toggle('d-none', !canEdit);
        document.getElementById('pdMenuArchiveProduct')?.classList.toggle('d-none', isArchived || !canEdit);
        document.getElementById('pdRestoreBtn')?.classList.toggle('d-none', !isArchived);
        document.getElementById('pdMenuRestoreProduct')?.classList.toggle('d-none', !isArchived);

        activeProduct = { ...product, inventory_status: inventoryStatus };
        variantGalleryItems = buildVariantGalleryItems(activeProduct, helpers);
        optionNames = variantGalleryItems.map((item) => item.optionName).filter(Boolean);

        const fields = {
            pdMeta: product.product_code || `PRD-${String(product.id || '').padStart(4, '0')}`,
            pdCategory: product.category || '—',
            pdSeller: product.seller || '—',
            pdDeptHero: product.program || 'Unassigned (legacy record)',
            pdMajorHero: product.major || '—',
            pdCreatedAt: formatPdDateTime(dateStr),
            pdDescription: description,
            pdDept: department,
            pdCat2: product.category || '—',
            pdCreatedBy: product.seller || '—',
            pdCreatedDate: formatPdDate(dateStr),
        };

        Object.entries(fields).forEach(([id, val]) => {
            const el = document.getElementById(id);
            if (el) el.textContent = val;
        });

        const updatedEl = document.getElementById('pdUpdated');
        if (updatedEl) updatedEl.textContent = formatPdDateTime(updatedStr);

        const statusEl = document.getElementById('pdStatusText');
        if (statusEl) {
            statusEl.textContent = capitalizeStatus(status);
            statusEl.className = `pd-active-badge status-${status}`;
        }
        const listingEl = document.getElementById('pdListingStatus');
        if (listingEl) listingEl.textContent = isArchived ? 'Archived' : 'Active';

        populateProductTags(product);
        populateInventoryKpis(product);
        populateVariationsTable(product, helpers);
        populateInventoryHistory(product);
        populateActivityLog(product);
        updateHeroVariantDisplay(currentIdx);
    }

    async function loadOrdersAndSales(product) {
        const orders = await fetchOrdersFromServer();
        if (section.classList.contains('d-none') || activeProductId !== String(product.id)) return;
        const helpers = window.CampusHubAdminProducts || {};
        const variantRows = buildVariantRows(product, helpers);
        populateInventoryHistory(product, orders);
        populateOrdersTable(orders, product.id);
        populateSalesFromOrders(orders, product.id, variantRows);
        populateActivityLog(product, orders);
    }

    function updateOptionLabel() {
        if (!optionLabel) return;
        const item = getVariantItemForIndex(currentIdx);
        const name = item ? (item.optionName || '') : (optionNames[currentIdx] || '');
        if (name) {
            optionLabel.textContent = name;
            optionLabel.hidden = false;
        } else {
            optionLabel.textContent = '';
            optionLabel.hidden = true;
        }
    }

    function renderDetailsGallery() {
        if (mainImage) {
            mainImage.referrerPolicy = 'no-referrer';
            mainImage.src = images[currentIdx] || images[0] || '';
            mainImage.style.display = images.length ? '' : 'none';
        }
        if (counter) counter.textContent = images.length ? `${currentIdx + 1}/${images.length}` : '';
        if (prevBtn) prevBtn.style.display = images.length > 1 ? 'inline-flex' : 'none';
        if (nextBtn) nextBtn.style.display = images.length > 1 ? 'inline-flex' : 'none';

        if (thumbnails) {
            thumbnails.innerHTML = '';
            images.forEach((url, i) => {
                const thumb = document.createElement('img');
                thumb.referrerPolicy = 'no-referrer';
                thumb.src = url;
                thumb.alt = '';
                thumb.className = i === currentIdx ? 'is-active' : '';
                thumb.addEventListener('click', () => showImage(i));
                thumbnails.appendChild(thumb);
            });
        }

        updateHeroVariantDisplay(currentIdx);
        updateThumbNavState();
    }

    function updateThumbNavState() {
        const multi = images.length > 1;
        [thumbPrev, thumbNext].forEach((btn) => {
            if (!btn) return;
            btn.disabled = !multi;
            btn.style.visibility = multi ? 'visible' : 'hidden';
        });
    }

    function showImage(idx) {
        if (!images.length) return;
        currentIdx = ((idx % images.length) + images.length) % images.length;
        renderDetailsGallery();
    }

    if (prevBtn) prevBtn.addEventListener('click', () => showImage((currentIdx - 1 + images.length) % images.length));
    if (nextBtn) nextBtn.addEventListener('click', () => showImage(currentIdx + 1));
    if (thumbPrev) thumbPrev.addEventListener('click', () => showImage((currentIdx - 1 + images.length) % images.length));
    if (thumbNext) thumbNext.addEventListener('click', () => showImage(currentIdx + 1));

    const backBtn = document.getElementById('pdBackBtn');
    if (backBtn) backBtn.addEventListener('click', () => {
        section.classList.add('d-none');
        if (listSection) listSection.classList.remove('d-none');
        if (statsGrid) statsGrid.classList.remove('d-none');
        activeDetailsRow = null;
    });

    function openEditFromDetails() {
        if (!activeDetailsRow) return;
        section.classList.add('d-none');
        const productId = activeDetailsRow.dataset.productId;
        const helpers = window.CampusHubAdminProducts || {};
        const openForm = (product) => {
            if (product && product.customization_options) {
                activeDetailsRow.dataset.customizationOptions = JSON.stringify(product.customization_options);
                activeDetailsRow.dataset.customizationEnabled = product.customization_enabled ? '1' : '0';
            }
            helpers.openEditProductForm?.(activeDetailsRow);
        };
        if (productId) {
            fetchProductByIdFromServer(productId).then((serverProduct) => {
                openForm(serverProduct);
            }).catch(() => openForm(null));
            return;
        }
        openForm(null);
    }

    function getCsrfToken() {
        return document.cookie
            .split(';')
            .map((c) => c.trim())
            .find((c) => c.startsWith('csrftoken='))
            ?.split('=')[1] || '';
    }

    function openUpdateStockFromDetails() {
        if (!activeDetailsRow) return;
        const helpers = window.CampusHubAdminProducts || {};
        const product = helpers.getProductFromRow?.(activeDetailsRow) || {};
        const nameEl = document.getElementById('updateStockProductName');
        const currentEl = document.getElementById('updateStockCurrent');
        const inputEl = document.getElementById('updateStockInput');
        const hintEl = document.getElementById('updateStockHint');
        const currentStock = parseInt(product.stock, 10) || 0;
        const variantSelect = document.getElementById('updateStockVariant');
        const variantWrap = document.getElementById('updateStockVariantWrap');
        const variants = [];
        (product.customization_options || []).forEach((group, groupIndex) => (group.options || []).forEach((option, optionIndex) => {
            if (Object.prototype.hasOwnProperty.call(option, 'stock')) variants.push({ key: `${groupIndex}:${optionIndex}`, name: `${group.name} · ${option.name}`, stock: option.stock });
        }));
        if (variantWrap) variantWrap.hidden = !variants.length;
        if (variantSelect) {
            variantSelect.innerHTML = variants.map(item => `<option value="${item.key}" data-stock="${item.stock}">${escapeHtml(item.name)}</option>`).join('');
            variantSelect.onchange = () => {
                const stock = variantSelect.selectedOptions[0]?.dataset.stock || '0';
                if (currentEl) currentEl.textContent = stock;
                if (inputEl) inputEl.value = stock;
            };
        }

        if (nameEl) nameEl.textContent = product.name || 'Selected product';
        if (currentEl) currentEl.textContent = String(currentStock);
        if (inputEl) inputEl.value = String(currentStock);
        if (variants.length) variantSelect?.onchange();
        if (hintEl) {
            hintEl.textContent = variants.length
                ? 'Updates only the selected variant’s available quantity. Existing reservations and threshold are retained.'
                : 'This updates stock only — it does not open the full edit form.';
        }

        const modalEl = document.getElementById('updateStockModal');
        if (modalEl && window.bootstrap?.Modal) {
            window.bootstrap.Modal.getOrCreateInstance(modalEl).show();
            setTimeout(() => inputEl?.focus(), 200);
        }
    }

    function openArchiveFromDetails() {
        if (!activeDetailsRow) return;
        window.openProductArchiveModal?.(activeDetailsRow);
    }

    function openRestoreFromDetails() {
        if (!activeDetailsRow) return;
        window.openProductRestoreModal?.(activeDetailsRow);
    }

    document.getElementById('pdEditBtn')?.addEventListener('click', openEditFromDetails);
    document.getElementById('pdRestoreBtn')?.addEventListener('click', openRestoreFromDetails);
    document.getElementById('pdMenuUpdateStock')?.addEventListener('click', openUpdateStockFromDetails);
    document.getElementById('pdMenuArchiveProduct')?.addEventListener('click', openArchiveFromDetails);
    document.getElementById('pdMenuRestoreProduct')?.addEventListener('click', openRestoreFromDetails);

    document.getElementById('confirmUpdateStockButton')?.addEventListener('click', async () => {
        if (!activeDetailsRow) return;
        const productId = activeDetailsRow.dataset.productId;
        const inputEl = document.getElementById('updateStockInput');
        const btn = document.getElementById('confirmUpdateStockButton');
        const stock = parseInt(inputEl?.value, 10);
        if (!productId || Number.isNaN(stock) || stock < 0) {
            alert('Enter a valid stock quantity (0 or more).');
            return;
        }

        const originalLabel = btn?.textContent || 'Save Stock';
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Saving…';
        }
        try {
            const response = await fetch(`/api/products/admin/${encodeURIComponent(productId)}/stock/`, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    Accept: 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify({ stock, variant_key: document.getElementById('updateStockVariantWrap')?.hidden ? null : document.getElementById('updateStockVariant')?.value }),
            });
            const data = await window.CampusHubActions.json(response, 'Unable to confirm the update. Reload the record before retrying.');
            if (!data.product) throw new Error('The update was not confirmed. Reload the record before retrying.');

            activeDetailsRow.dataset.productStock = String(stock);
            // The stock endpoint returns canonical remaining/variant quantities.
            const saved = data.product;
            const helpers = window.CampusHubAdminProducts;
            const inventoryCell = activeDetailsRow.querySelector('.col-inventory');
            if (saved && helpers && inventoryCell) {
                const available = helpers.computeTotalStock(saved);
                const variants = helpers.countProductVariants(saved);
                inventoryCell.innerHTML = helpers.renderInventorySummary(available, variants, saved);
                activeDetailsRow.dataset.lowStockThreshold = saved.low_stock_threshold == null ? '' : String(saved.low_stock_threshold);
                activeDetailsRow.dataset.productStock = String(available);
                activeDetailsRow.dataset.variantCount = String(variants);
                activeDetailsRow.dataset.customizationOptions = JSON.stringify(saved.customization_options || []);
                activeDetailsRow.dataset.inventoryStatus = saved.inventory_status;
            }
            const stockCell = activeDetailsRow.querySelector('.col-stock strong, [data-stock-display]');
            if (stockCell) stockCell.textContent = String(stock);
            if (saved && activeProduct) {
                activeProduct = { ...activeProduct, ...saved };
                populateInventoryKpis(activeProduct, true);
                activeDetailsRow.dataset.productUpdatedAt = saved.updated_at || '';
                const updatedEl = document.getElementById('pdUpdated');
                if (updatedEl) updatedEl.textContent = formatPdDateTime(saved.updated_at);
            }

            const modalEl = document.getElementById('updateStockModal');
            if (modalEl && window.bootstrap?.Modal) {
                window.bootstrap.Modal.getOrCreateInstance(modalEl).hide();
            }
            helpers?.showProductSaveToast('Stock updated.');
        } catch (error) {
            showProductSaveToast(error.message || 'Failed to update stock', 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = originalLabel;
            }
        }
    });

    document.getElementById('confirmArchiveProductButton')?.addEventListener('click', async () => {
        const targetRow = window.__chPendingArchiveProductRow || activeDetailsRow;
        if (!targetRow) return;
        const productId = targetRow.dataset.productId;
        const previousStatus = targetRow.dataset.productStatus || '';
        const btn = document.getElementById('confirmArchiveProductButton');
        if (!productId) return;

        const originalLabel = btn?.textContent || 'Archive';
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Archiving…';
        }
        try {
            const response = await fetch(`/api/products/admin/${encodeURIComponent(productId)}/archive/`, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    Accept: 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
            });
            const data = await window.CampusHubActions.json(response, 'Unable to confirm the update. Reload the record before retrying.');
            if (String(data.id) !== String(productId)) throw new Error('The update was not confirmed. Reload the record before retrying.');

            const modalEl = document.getElementById('archiveProductModal');
            if (modalEl && window.bootstrap?.Modal) {
                window.bootstrap.Modal.getOrCreateInstance(modalEl).hide();
            }

            targetRow.dataset.isArchived = '1';
            const actionCell = targetRow.querySelector('td.col-action');
            if (actionCell) {
                actionCell.outerHTML = renderProductActionsCell(previousStatus, true);
            }

            window.__chPendingArchiveProductRow = null;

            // Archive changes listing visibility, not record/approval counts.

            applyInlineFilters();
            window.dispatchEvent(new Event('products-table-changed'));

            if (targetRow === activeDetailsRow && activeProduct) {
                activeProduct.is_archived = true;
                populateProductDetails(activeProduct);
            }

            showProductSaveToast('Product archived.');
        } catch (error) {
            showProductSaveToast(error.message || 'Failed to archive product', 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = originalLabel;
            }
        }
    });

    document.getElementById('archiveProductModal')?.addEventListener('hidden.bs.modal', () => {
        window.__chPendingArchiveProductRow = null;
    });

    document.getElementById('confirmRestoreProductButton')?.addEventListener('click', async () => {
        const targetRow = window.__chPendingRestoreProductRow || activeDetailsRow;
        if (!targetRow) return;
        const productId = targetRow.dataset.productId;
        const previousStatus = targetRow.dataset.productStatus || '';
        const btn = document.getElementById('confirmRestoreProductButton');
        if (!productId) return;

        const originalLabel = btn?.textContent || 'Restore';
        if (btn) {
            btn.disabled = true;
            btn.textContent = 'Restoring…';
        }
        try {
            const response = await fetch(`/api/products/admin/${encodeURIComponent(productId)}/restore/`, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    Accept: 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
            });
            const data = await window.CampusHubActions.json(response, 'Unable to confirm the update. Reload the record before retrying.');
            if (String(data.id) !== String(productId)) throw new Error('The update was not confirmed. Reload the record before retrying.');

            const modalEl = document.getElementById('restoreProductModal');
            if (modalEl && window.bootstrap?.Modal) {
                window.bootstrap.Modal.getOrCreateInstance(modalEl).hide();
            }

            targetRow.dataset.isArchived = '0';
            const actionCell = targetRow.querySelector('td.col-action');
            if (actionCell) {
                actionCell.outerHTML = renderProductActionsCell(previousStatus, false);
            }

            window.__chPendingRestoreProductRow = null;

            // Restore keeps the same record/approval counts.

            applyInlineFilters();
            window.dispatchEvent(new Event('products-table-changed'));

            if (targetRow === activeDetailsRow && activeProduct) {
                activeProduct.is_archived = false;
                populateProductDetails(activeProduct);
            }

            showProductSaveToast('Product restored successfully.');
        } catch (error) {
            showProductSaveToast(error.message || 'Failed to restore product', 'error');
        } finally {
            if (btn) {
                btn.disabled = false;
                btn.textContent = originalLabel;
            }
        }
    });

    document.getElementById('restoreProductModal')?.addEventListener('hidden.bs.modal', () => {
        window.__chPendingRestoreProductRow = null;
    });

    document.getElementById('pdViewAllOrders')?.addEventListener('click', () => {
        window.location.href = '/admin-orders/';
    });
    document.getElementById('pdViewAllActivity')?.addEventListener('click', () => {
        const wrap = document.querySelector('.pd-activity-wrap');
        if (wrap) wrap.style.maxHeight = 'none';
    });

    async function syncDetailsFromServer(productId, row, fallbackUrl) {
        const product = await fetchProductByIdFromServer(productId);
        if (section.classList.contains('d-none') || activeProductId !== String(productId)) return;
        if (!product || !product.inventory) {
            populateInventoryKpis({}, true);
            populateInventoryHistory({}, true);
            return;
        }

        const helpers = window.CampusHubAdminProducts || {};
        const merged = {
            ...helpers.getProductFromRow?.(row),
            ...product,
            department: product.department || row.dataset.sellerDepartment || helpers.getProductFromRow?.(row)?.department || '',
            customization_options: product.customization_options || [],
            approval_status: product.approval_status,
            product_status: product.approval_status,
        };

        populateProductDetails(merged);
        const serverImages = parseProductImages(product.images, product.image_url);
        if (serverImages.length) {
            images = resolveProductGalleryUrls(productId, serverImages, fallbackUrl);
            currentIdx = Math.min(currentIdx, images.length - 1);
            renderDetailsGallery();
        }
        loadOrdersAndSales(merged);
    }

    window.openProductDetailsView = function openProductDetailsView(row) {
        const helpers = window.CampusHubAdminProducts;
        if (!helpers?.getProductFromRow) return;

        activeDetailsRow = row;
        const product = helpers.getProductFromRow(row);
        const imageUrl = product.image_url;
        const imagesRaw = row.dataset.productImages || '';
        const productId = product.id || '';
        activeProductId = productId;

        const storedImages = parseProductImagesJson(imagesRaw);
        images = resolveProductGalleryUrls(productId, storedImages, imageUrl);
        currentIdx = 0;
        variantGalleryItems = buildVariantGalleryItems(product, helpers);
        optionNames = variantGalleryItems.map((item) => item.optionName).filter(Boolean);

        populateProductDetails(product);
        renderDetailsGallery();

        const ordersBody = document.getElementById('pdOrdersTableBody');
        if (ordersBody) {
            ordersBody.innerHTML = '<tr><td colspan="7" class="pd-empty-cell"></td></tr>';
        }

        if (listSection) listSection.classList.add('d-none');
        if (formSection) formSection.classList.add('d-none');
        if (loadingSection) loadingSection.classList.add('d-none');
        if (statsGrid) statsGrid.classList.add('d-none');
        section.classList.remove('d-none');
        window.scrollTo({ top: 0, behavior: 'smooth' });

        loadOrdersAndSales(product);
        syncDetailsFromServer(productId, row, imageUrl);
    };

    // Dashboard leaders link to the existing details view, including archived
    // products with historical sales. Keep the list and edit workflows intact.
    document.addEventListener('DOMContentLoaded', () => {
        const id = new URL(window.location.href).searchParams.get('product_id');
        if (!id || !/^\d+$/.test(id)) return;
        const row = document.querySelector(`tr[data-product-id="${id}"]`);
        if (row) window.openProductDetailsView(row);
    });
})();
