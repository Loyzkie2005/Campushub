document.addEventListener('DOMContentLoaded', () => {
    const searchInput = document.getElementById('ordersSearchInput');
    const statusFilter = document.getElementById('ordersStatusFilter');
    const paymentFilter = document.getElementById('ordersPaymentFilter');
    const datePresetFilter = document.getElementById('ordersDatePresetFilter');
    const customDateRange = document.getElementById('ordersCustomDateRange');
    const dateFromInput = document.getElementById('ordersDateFrom');
    const dateToInput = document.getElementById('ordersDateTo');
    const tableBody = document.getElementById('ordersTableBody');
    const showingText = document.getElementById('ordersShowingText');
    const pagination = document.getElementById('ordersPagination');
    const statCards = [...document.querySelectorAll('[data-order-stat-filter]')];

    const detailModalEl = document.getElementById('orderDetailModal');
    const detailModal = detailModalEl && window.bootstrap ? new window.bootstrap.Modal(detailModalEl) : null;
    const completeModalEl = document.getElementById('completeOrderModal');
    const completeModal = completeModalEl && window.bootstrap ? new window.bootstrap.Modal(completeModalEl) : null;
    const cancelModalEl = document.getElementById('cancelOrderModal');
    const cancelModal = cancelModalEl && window.bootstrap ? new window.bootstrap.Modal(cancelModalEl) : null;

    const detailForm = document.getElementById('orderManagementForm');
    const detailReceiptInput = document.getElementById('orderManageReceipt');
    const detailSaveButton = document.getElementById('orderSaveButton');
    const btnModalCompleteOrder = document.getElementById('btnModalCompleteOrder');
    const detailHistoryList = document.getElementById('orderStatusHistory');
    const detailAlertBox = document.getElementById('orderModalAlert');
    const orderItemsTableBody = document.getElementById('orderItemsTableBody');

    const completeAmountDue = document.getElementById('completeOrderAmountDue');
    const cashReceivedCheck = document.getElementById('cashPaymentReceivedCheck');
    const btnConfirmCompleteOrder = document.getElementById('btnConfirmCompleteOrder');
    const completeAlert = document.getElementById('completeOrderAlert');

    const cancelReasonInput = document.getElementById('orderCancelReasonInput');
    const btnConfirmCancelOrder = document.getElementById('btnConfirmCancelOrder');
    const cancelAlert = document.getElementById('cancelOrderAlert');

    const rowsPerPage = 10;
    let currentPage = 1;
    let selectedRow = null;
    let cardFilter = '';

    function getCsrfToken() {
        return document.querySelector('[name="csrfmiddlewaretoken"]')?.value
            || (document.cookie.split('; ').find((row) => row.startsWith('csrftoken=')) || '').split('=')[1]
            || '';
    }

    function parseJson(value, fallback) {
        if (!value) return fallback;
        try {
            return JSON.parse(value);
        } catch (_) {
            return fallback;
        }
    }

    function formatCurrency(value) {
        const amount = Number.parseFloat(value);
        return Number.isNaN(amount) ? '₱ 0.00' : `₱ ${amount.toFixed(2)}`;
    }

    function setText(id, value) {
        const el = document.getElementById(id);
        if (el) el.textContent = value || '—';
    }

    function showActionToast(message, isError = false) {
        const toast = document.getElementById('orderActionToast');
        if (!toast) return;
        toast.textContent = message;
        toast.classList.toggle('is-error', isError);
        toast.classList.add('is-visible');
        window.clearTimeout(showActionToast._timer);
        showActionToast._timer = window.setTimeout(() => {
            toast.classList.remove('is-visible', 'is-error');
        }, 2800);
    }

    function renderStatusBadge(status) {
        const labels = {
            pending: 'Pending',
            processing: 'Processing',
            ready_for_pickup: 'Ready for Pickup',
            completed: 'Completed',
            cancelled: 'Cancelled',
        };
        const label = labels[status] || status;
        return `<span class="status-pill status-${status}">${label}</span>`;
    }

    function renderPaymentBadge(payment) {
        const label = payment === 'paid' ? 'Paid' : 'Unpaid';
        return `<span class="payment-pill payment-${payment}">${label}</span>`;
    }

    function renderHistory(row) {
        if (!detailHistoryList) return;
        detailHistoryList.replaceChildren();
        const history = parseJson(row.dataset.statusHistory, []);

        if (!history.length) {
            const empty = document.createElement('p');
            empty.className = 'order-history-empty';
            empty.textContent = 'No status changes recorded yet.';
            detailHistoryList.appendChild(empty);
            return;
        }

        history.forEach((item) => {
            const entry = document.createElement('div');
            entry.className = 'order-history-entry';
            const marker = document.createElement('span');
            marker.className = 'order-history-marker';
            const content = document.createElement('div');
            const title = document.createElement('strong');
            title.textContent = item.new_status_label || item.new_status || 'Updated';
            const meta = document.createElement('span');
            meta.textContent = `${item.changed_by || 'System'} · ${item.created_at || ''}`;
            content.append(title, meta);
            if (item.notes) {
                const notes = document.createElement('p');
                notes.textContent = item.notes;
                content.appendChild(notes);
            }
            entry.append(marker, content);
            detailHistoryList.appendChild(entry);
        });
    }

    function renderOrderItems(row) {
        if (!orderItemsTableBody) return;
        orderItemsTableBody.replaceChildren();
        const items = parseJson(row.dataset.itemsJson, []);

        if (!Array.isArray(items) || !items.length) {
            const tr = document.createElement('tr');
            tr.innerHTML = `
                <td><strong>${row.dataset.productName || 'Product'}</strong></td>
                <td class="text-muted">${row.dataset.option || 'Standard'}</td>
                <td class="text-center">${row.dataset.quantity || '1'}</td>
                <td class="text-end">${formatCurrency(row.dataset.unitPrice || row.dataset.totalPrice)}</td>
                <td class="text-end fw-bold">${formatCurrency(row.dataset.totalPrice)}</td>
            `;
            orderItemsTableBody.appendChild(tr);
            return;
        }

        items.forEach((item) => {
            const tr = document.createElement('tr');
            const productName = item.product_name || row.dataset.productName || 'Product';
            const variant = item.variant || item.option || 'Standard';
            const qty = item.quantity || 1;
            const unitPrice = formatCurrency(item.unit_price || 0);
            const subtotal = formatCurrency(item.subtotal || (item.quantity * item.unit_price) || 0);

            tr.innerHTML = `
                <td><strong>${productName}</strong></td>
                <td class="text-muted">${variant}</td>
                <td class="text-center">${qty}</td>
                <td class="text-end">${unitPrice}</td>
                <td class="text-end fw-bold">${subtotal}</td>
            `;
            orderItemsTableBody.appendChild(tr);
        });
    }

    function openOrderDetail(row) {
        if (!row || !detailModal) return;
        selectedRow = row;

        const buyerName = row.dataset.buyerName || 'Unknown customer';
        const currentStatus = row.dataset.orderStatus || 'pending';
        const currentPayment = row.dataset.paymentStatus || 'unpaid';

        setText('orderDetailCode', row.dataset.orderCode);
        setText('orderDetailDate', row.dataset.createdAt);

        const statusBadgeContainer = document.getElementById('orderDetailStatusBadge');
        if (statusBadgeContainer) {
            statusBadgeContainer.innerHTML = renderStatusBadge(currentStatus);
        }

        setText('orderDetailCustomer', buyerName);
        setText('orderDetailEmail', row.dataset.buyerEmail || 'None provided');
        setText('orderDetailPhone', row.dataset.buyerPhone || 'None provided');
        setText('orderDetailSeller', row.dataset.sellerName || 'Campus Seller');
        setText('orderDetailSellerMessage', row.dataset.messageToSeller || 'None');

        renderOrderItems(row);

        setText('orderDetailTotalQty', `${row.dataset.quantity || 1} pcs`);
        setText('orderDetailAmount', formatCurrency(row.dataset.totalPrice));

        setText('orderDetailPickupLocation', row.dataset.pickupLocation || 'Cashiering / Selling Counter');
        setText('orderDetailPickupSchedule', row.dataset.pickupScheduledAt || 'Regular campus operating hours');

        const paymentStatusContainer = document.getElementById('orderDetailPaymentStatus');
        if (paymentStatusContainer) {
            paymentStatusContainer.innerHTML = renderPaymentBadge(currentPayment);
        }

        const isPaid = currentPayment === 'paid' || currentStatus === 'completed';
        setText('orderDetailAmountPaid', isPaid ? formatCurrency(row.dataset.totalPrice) : '₱ 0.00');
        setText('orderDetailPaidAt', row.dataset.paidAt || (isPaid ? 'Recorded' : 'Not paid yet'));
        setText('orderDetailRecordedBy', row.dataset.paymentEncodedBy || (isPaid ? 'Authorized Staff' : 'Pending payment'));
        setText('orderDetailOR', row.dataset.receiptNo || 'Not recorded');

        if (detailReceiptInput) {
            detailReceiptInput.value = row.dataset.receiptNo || '';
        }

        if (btnModalCompleteOrder) {
            btnModalCompleteOrder.style.display = currentStatus === 'ready_for_pickup' ? 'inline-block' : 'none';
        }

        if (detailAlertBox) {
            detailAlertBox.hidden = true;
            detailAlertBox.textContent = '';
        }

        renderHistory(row);
        detailModal.show();
    }

    function openCompleteModal(row) {
        if (!row || !completeModal) return;
        selectedRow = row;

        if (completeAmountDue) {
            completeAmountDue.textContent = formatCurrency(row.dataset.totalPrice);
        }
        if (cashReceivedCheck) {
            cashReceivedCheck.checked = false;
        }
        if (btnConfirmCompleteOrder) {
            btnConfirmCompleteOrder.disabled = true;
        }
        if (completeAlert) {
            completeAlert.style.display = 'none';
            completeAlert.textContent = '';
        }

        completeModal.show();
    }

    cashReceivedCheck?.addEventListener('change', () => {
        if (btnConfirmCompleteOrder) {
            btnConfirmCompleteOrder.disabled = !cashReceivedCheck.checked;
        }
    });

    btnConfirmCompleteOrder?.addEventListener('click', async () => {
        if (!selectedRow || !cashReceivedCheck.checked) return;

        btnConfirmCompleteOrder.disabled = true;
        btnConfirmCompleteOrder.textContent = 'Completing...';
        if (completeAlert) completeAlert.style.display = 'none';

        try {
            const response = await fetch(selectedRow.dataset.updateUrl, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify({
                    status: 'completed',
                    payment_status: 'paid',
                    cash_confirmed: true,
                }),
            });

            const result = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(result.error || 'Failed to complete the order.');

            completeModal.hide();
            showActionToast('Order completed and Cash on Pickup payment confirmed.');
            window.sessionStorage.setItem('campushubOrderSuccessMessage', 'Order completed and Cash on Pickup payment confirmed.');
            window.sessionStorage.setItem('campushubOrdersScrollY', String(window.scrollY));
            window.setTimeout(() => window.location.reload(), 800);
        } catch (error) {
            if (completeAlert) {
                completeAlert.textContent = error.message || 'Failed to complete order.';
                completeAlert.style.display = 'block';
            }
            btnConfirmCompleteOrder.disabled = false;
            btnConfirmCompleteOrder.textContent = 'Confirm & Complete';
        }
    });

    function openCancelModal(row) {
        if (!row || !cancelModal) return;
        selectedRow = row;

        if (cancelReasonInput) cancelReasonInput.value = '';
        if (cancelAlert) {
            cancelAlert.style.display = 'none';
            cancelAlert.textContent = '';
        }
        cancelModal.show();
    }

    btnConfirmCancelOrder?.addEventListener('click', async () => {
        if (!selectedRow) return;
        const reason = cancelReasonInput ? cancelReasonInput.value.trim() : '';
        if (!reason) {
            if (cancelAlert) {
                cancelAlert.textContent = 'Please enter a cancellation reason.';
                cancelAlert.style.display = 'block';
            }
            return;
        }

        btnConfirmCancelOrder.disabled = true;
        btnConfirmCancelOrder.textContent = 'Cancelling...';

        try {
            const response = await fetch(selectedRow.dataset.updateUrl, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify({
                    status: 'cancelled',
                    cancellation_reason: reason,
                }),
            });

            const result = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(result.error || 'Failed to cancel order.');

            cancelModal.hide();
            showActionToast('Order has been cancelled and stock restored.');
            window.sessionStorage.setItem('campushubOrderSuccessMessage', 'Order has been cancelled and stock restored.');
            window.sessionStorage.setItem('campushubOrdersScrollY', String(window.scrollY));
            window.setTimeout(() => window.location.reload(), 800);
        } catch (error) {
            if (cancelAlert) {
                cancelAlert.textContent = error.message || 'Failed to cancel order.';
                cancelAlert.style.display = 'block';
            }
            btnConfirmCancelOrder.disabled = false;
            btnConfirmCancelOrder.textContent = 'Confirm Cancellation';
        }
    });

    btnModalCompleteOrder?.addEventListener('click', () => {
        if (detailModal) detailModal.hide();
        if (selectedRow) openCompleteModal(selectedRow);
    });

    detailForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (!selectedRow) return;

        if (detailSaveButton) {
            detailSaveButton.disabled = true;
            detailSaveButton.textContent = 'Saving...';
        }

        try {
            const response = await fetch(selectedRow.dataset.updateUrl, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify({
                    official_receipt_no: detailReceiptInput ? detailReceiptInput.value.trim() : '',
                }),
            });

            const result = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(result.error || 'Failed to save receipt info.');

            detailModal.hide();
            showActionToast('Receipt information saved.');
            window.sessionStorage.setItem('campushubOrderSuccessMessage', 'Receipt information saved.');
            window.sessionStorage.setItem('campushubOrdersScrollY', String(window.scrollY));
            window.setTimeout(() => window.location.reload(), 800);
        } catch (error) {
            if (detailAlertBox) {
                detailAlertBox.textContent = error.message || 'Failed to save receipt info.';
                detailAlertBox.hidden = false;
            }
            if (detailSaveButton) {
                detailSaveButton.disabled = false;
                detailSaveButton.textContent = 'Save Receipt Info';
            }
        }
    });

    async function executeStatusStep(row, nextStatus) {
        if (!row || !nextStatus) return;

        try {
            const response = await fetch(row.dataset.updateUrl, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify({ status: nextStatus }),
            });

            const result = await response.json().catch(() => ({}));
            if (!response.ok) throw new Error(result.error || `Failed to update status to ${nextStatus}.`);

            showActionToast(`Order status updated to ${nextStatus.replace(/_/g, ' ')}.`);
            window.sessionStorage.setItem('campushubOrderSuccessMessage', `Order status updated to ${nextStatus.replace(/_/g, ' ')}.`);
            window.sessionStorage.setItem('campushubOrdersScrollY', String(window.scrollY));
            window.setTimeout(() => window.location.reload(), 800);
        } catch (error) {
            showActionToast(error.message || 'Failed to update order status.', true);
        }
    }

    tableBody?.addEventListener('click', (e) => {
        const viewBtn = e.target.closest('.view-order-action');
        if (viewBtn) {
            const row = viewBtn.closest('tr');
            if (row) openOrderDetail(row);
            return;
        }

        const stepBtn = e.target.closest('.btn-step-action');
        if (stepBtn) {
            const row = stepBtn.closest('tr');
            const nextStatus = stepBtn.dataset.nextStatus;
            if (row && nextStatus) executeStatusStep(row, nextStatus);
            return;
        }

        const completeBtn = e.target.closest('.btn-complete-action');
        if (completeBtn) {
            const row = completeBtn.closest('tr');
            if (row) openCompleteModal(row);
            return;
        }

        const cancelBtn = e.target.closest('.btn-cancel-action');
        if (cancelBtn) {
            const row = cancelBtn.closest('tr');
            if (row) openCancelModal(row);
            return;
        }
    });

    function allRows() {
        return tableBody ? [...tableBody.querySelectorAll('tr[data-order-id]')] : [];
    }

    function rowMatchesDate(row, preset, dateFrom, dateTo) {
        const createdDate = row.dataset.createdDate || '';
        if (!createdDate) return true;

        if (preset === 'custom') {
            const afterStart = !dateFrom || createdDate >= dateFrom;
            const beforeEnd = !dateTo || createdDate <= dateTo;
            return afterStart && beforeEnd;
        }

        if (!preset) return true;

        const rowDate = new Date(`${createdDate}T00:00:00`);
        const today = new Date();
        today.setHours(0, 0, 0, 0);

        if (preset === 'today') {
            return rowDate.getTime() === today.getTime();
        }

        if (preset === '7days') {
            const limit = new Date(today);
            limit.setDate(limit.getDate() - 7);
            return rowDate >= limit;
        }

        if (preset === '30days') {
            const limit = new Date(today);
            limit.setDate(limit.getDate() - 30);
            return rowDate >= limit;
        }

        if (preset === 'month') {
            const currentYearMonth = `${today.getFullYear()}-${String(today.getMonth() + 1).padStart(2, '0')}`;
            return createdDate.startsWith(currentYearMonth);
        }

        return true;
    }

    function filteredRows() {
        const query = searchInput ? searchInput.value.trim().toLowerCase() : '';
        const selectStatus = statusFilter ? statusFilter.value : '';
        const activeStatus = cardFilter || selectStatus;
        const selectPayment = paymentFilter ? paymentFilter.value : '';
        const preset = datePresetFilter ? datePresetFilter.value : '';
        const dateFrom = dateFromInput ? dateFromInput.value : '';
        const dateTo = dateToInput ? dateToInput.value : '';

        return allRows().filter((row) => {
            const textMatches = !query
                || (row.dataset.orderCode && row.dataset.orderCode.toLowerCase().includes(query))
                || (row.dataset.buyerName && row.dataset.buyerName.toLowerCase().includes(query))
                || (row.dataset.buyerEmail && row.dataset.buyerEmail.toLowerCase().includes(query))
                || (row.dataset.productName && row.dataset.productName.toLowerCase().includes(query))
                || (row.dataset.displayItems && row.dataset.displayItems.toLowerCase().includes(query));

            const rowStatus = row.dataset.orderStatus || '';
            const statusMatches = !activeStatus || rowStatus === activeStatus;

            const rowPayment = row.dataset.paymentStatus || '';
            const paymentMatches = !selectPayment || rowPayment === selectPayment;

            const dateMatches = rowMatchesDate(row, preset, dateFrom, dateTo);

            return textMatches && statusMatches && paymentMatches && dateMatches;
        });
    }

    function renderPagination(totalPages) {
        if (!pagination) return;
        pagination.replaceChildren();

        const addButton = (label, page, disabled = false, active = false, isNavigation = false) => {
            const button = document.createElement('button');
            button.type = 'button';
            button.className = `page-btn${isNavigation ? ' page-btn-nav' : ''}${active ? ' is-active' : ''}`;
            button.textContent = label;
            button.disabled = disabled;
            button.addEventListener('click', () => {
                if (page < 1 || page > totalPages || page === currentPage) return;
                currentPage = page;
                updateTable();
            });
            pagination.appendChild(button);
        };

        addButton('‹', currentPage - 1, currentPage === 1, false, true);
        for (let page = 1; page <= totalPages; page += 1) {
            addButton(String(page), page, false, page === currentPage);
        }
        addButton('›', currentPage + 1, currentPage === totalPages, false, true);
    }

    function updateTable() {
        const matched = filteredRows();
        const matchedSet = new Set(matched);
        const totalPages = Math.max(1, Math.ceil(matched.length / rowsPerPage));
        currentPage = Math.min(currentPage, totalPages);
        const start = (currentPage - 1) * rowsPerPage;
        const pageRows = matched.slice(start, start + rowsPerPage);
        const pageSet = new Set(pageRows);

        allRows().forEach((row) => {
            row.hidden = !matchedSet.has(row) || !pageSet.has(row);
        });

        pageRows.forEach((row, index) => {
            const numCell = row.querySelector('.col-num');
            if (numCell) numCell.textContent = String(start + index + 1);
        });

        const emptyState = document.getElementById('ordersEmptyState');
        const tableWrap = document.getElementById('ordersTableWrap');
        const footer = document.getElementById('ordersTableFooter');
        if (emptyState && tableWrap) {
            emptyState.style.display = matched.length === 0 ? 'flex' : 'none';
            tableWrap.style.display = matched.length === 0 ? 'none' : '';
            if (footer) footer.style.display = matched.length === 0 ? 'none' : '';
        }

        if (showingText) {
            showingText.textContent = matched.length
                ? `Showing ${start + 1} to ${Math.min(start + rowsPerPage, matched.length)} of ${matched.length} entries`
                : 'No entries found';
        }
        renderPagination(totalPages);
    }

    function applyFilters() {
        currentPage = 1;
        updateTable();
    }

    [searchInput, statusFilter, paymentFilter, dateFromInput, dateToInput].filter(Boolean).forEach((control) => {
        control.addEventListener(control === searchInput ? 'input' : 'change', () => {
            if (control === statusFilter) {
                cardFilter = '';
                statCards.forEach((card) => card.classList.remove('is-active'));
            }
            applyFilters();
        });
    });

    datePresetFilter?.addEventListener('change', () => {
        const isCustom = datePresetFilter.value === 'custom';
        if (customDateRange) {
            customDateRange.style.display = isCustom ? 'flex' : 'none';
        }
        if (!isCustom) {
            if (dateFromInput) dateFromInput.value = '';
            if (dateToInput) dateToInput.value = '';
        }
        applyFilters();
    });

    statCards.forEach((card) => {
        card.addEventListener('click', () => {
            cardFilter = card.dataset.orderStatFilter || '';
            if (statusFilter) statusFilter.value = cardFilter;
            statCards.forEach((item) => item.classList.toggle('is-active', item === card));
            applyFilters();
            document.getElementById('ordersListSection')?.scrollIntoView({ behavior: 'smooth', block: 'start' });
        });
    });

    const savedScroll = Number.parseInt(window.sessionStorage.getItem('campushubOrdersScrollY') || '', 10);
    if (Number.isFinite(savedScroll)) {
        window.sessionStorage.removeItem('campushubOrdersScrollY');
        window.requestAnimationFrame(() => window.scrollTo({ top: savedScroll, behavior: 'auto' }));
    }
    const savedSuccessMessage = window.sessionStorage.getItem('campushubOrderSuccessMessage');
    if (savedSuccessMessage) {
        window.sessionStorage.removeItem('campushubOrderSuccessMessage');
        showActionToast(savedSuccessMessage);
    }

    updateTable();
});
