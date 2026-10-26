document.addEventListener('DOMContentLoaded', () => {
    const canManageOrders = document.body.dataset.canManageOrders === 'true';
    const searchInput = document.getElementById('ordersSearchInput');
    const statusFilter = document.getElementById('ordersStatusFilter');
    const fulfillmentFilter = document.getElementById('ordersFulfillmentFilter');
    const paymentFilter = document.getElementById('ordersPaymentFilter');
    const datePresetFilter = document.getElementById('ordersDatePresetFilter');
    const customDateRange = document.getElementById('ordersCustomDateRange');
    const dateFromInput = document.getElementById('ordersDateFrom');
    const dateToInput = document.getElementById('ordersDateTo');
    const tableBody = document.getElementById('ordersTableBody');
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

    const filtersForm = document.getElementById('ordersFilters');
    const programFilter = document.getElementById('ordersProgramFilter');
    const majorFilter = document.getElementById('ordersMajorFilter');
    const pickupConfirmedCheck = document.getElementById('buyerPickupConfirmedCheck');
    const stepDetailButton = document.getElementById('btnModalStepOrder');
    const cancelDetailButton = document.getElementById('btnModalCancelOrder');
    const deliveryDetailButton = document.getElementById('btnModalDelivery');
    let selectedRow = null;
    let actionPending = false;
    let detailTrigger = null;
    detailModalEl?.addEventListener('hidden.bs.modal', () => {
        if (!completeModalEl?.classList.contains('show') && !cancelModalEl?.classList.contains('show')) {
            detailTrigger?.focus({preventScroll: true});
        }
    });


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
        return Number.isFinite(amount) ? new Intl.NumberFormat('en-PH', {style: 'currency', currency: 'PHP'}).format(amount) : 'Not recorded';
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

    function renderStatusBadge(status, method = '') {
        const labels = {
            pending: 'Pending',
            processing: 'Processing',
            ready_for_pickup: 'Ready for Pickup',
            completed: 'Completed',
            cancelled: 'Cancelled',
        };
        const label = status === 'ready_for_pickup' && method === 'seller_delivery' ? 'Ready for Seller Delivery' : labels[status] || 'Not recorded';
        const key = labels[status] ? status : 'unknown';
        return `<span class="status-pill status-${key}">${label}</span>`;
    }

    function finishOrderAction(message) {
        try {
            window.sessionStorage.setItem('campushubOrderSuccessMessage', message);
            window.sessionStorage.setItem('campushubOrdersScrollY', String(window.scrollY));
        } catch (_) { showActionToast(message); }
        window.setTimeout(() => window.location.reload(), 800);
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

        if (!Array.isArray(items)) return;
        items.forEach(item => {
            const tr = document.createElement('tr');
            const values = [item.product_name, item.variant, item.sku || 'Not recorded',
                item.quantity ?? 'Not recorded', formatCurrency(item.unit_price), formatCurrency(item.subtotal)];
            values.forEach((value, index) => {
                const cell = document.createElement('td');
                cell.textContent = value;
                if (index === 3) cell.className = 'text-center';
                if (index >= 4) cell.className = 'text-end';
                tr.appendChild(cell);
            });
            orderItemsTableBody.appendChild(tr);
        });
    }

    function openOrderDetail(row) {
        if (!row || !detailModal) return;
        selectedRow = row;

        const buyerName = row.dataset.buyerName || 'Unknown customer';
        const currentStatus = row.dataset.orderStatus || 'pending';
        const currentPayment = row.dataset.paymentStatus || 'unpaid';
        const delivery = row.dataset.fulfillmentMethod === 'seller_delivery';
        const delivered = Boolean(row.dataset.deliveredAt);
        setText('orderDetailFulfillment', row.dataset.fulfillmentLabel);
        setText('orderDetailFulfillmentProgress', row.dataset.fulfillmentProgress);
        setText('orderDetailDestination', delivery ? row.dataset.deliveryDestination : 'Not applicable');
        const dateLabel = value => value ? new Date(value).toLocaleString('en-PH') : 'Not recorded';
        setText('orderDetailDeliveryStarted', delivery ? dateLabel(row.dataset.deliveryStartedAt) : 'Not applicable');
        setText('orderDetailDelivered', delivery ? dateLabel(row.dataset.deliveredAt) : 'Not applicable');
        document.querySelectorAll('.order-payment-method').forEach(el => { el.textContent = delivery ? 'Cash — recorded separately from delivery' : 'Cash on Pickup'; });

        setText('orderDetailCode', row.dataset.orderCode);
        setText('orderDetailDate', row.dataset.createdAt);

        const statusBadgeContainer = document.getElementById('orderDetailStatusBadge');
        if (statusBadgeContainer) {
            statusBadgeContainer.innerHTML = renderStatusBadge(currentStatus, row.dataset.fulfillmentMethod);
        }

        setText('orderDetailCustomer', buyerName);
        setText('orderDetailEmail', row.dataset.buyerEmail || 'None provided');
        setText('orderDetailPhone', row.dataset.buyerPhone || 'None provided');
        setText('orderDetailSeller', row.dataset.sellerName || 'Campus Seller');
        setText('orderDetailSellerMessage', row.dataset.messageToSeller || 'None');
        setText('orderDetailBuyerProgram', row.dataset.buyerProgram);
        setText('orderDetailBuyerMajor', row.dataset.buyerMajor || 'Not applicable / not recorded');
        setText('orderDetailSellerProgram', row.dataset.sellerProgram);
        setText('orderDetailSellerMajor', row.dataset.sellerMajor || 'Not applicable / not recorded');
        setText('orderDetailSubtotal', formatCurrency(row.dataset.itemsSubtotal));
        setText('orderDetailPickedUpAt', delivery ? 'Not applicable' : row.dataset.pickedUpAt || 'Not recorded');
        setText('orderDetailPickupStatus', delivery ? 'Not applicable' : row.dataset.pickedUpAt ? 'Picked up' : currentStatus === 'cancelled' ? 'Cancelled' : 'Pickup not recorded');
        const infoPayment = document.getElementById('orderDetailInfoPayment');
        if (infoPayment) infoPayment.innerHTML = renderPaymentBadge(currentPayment);
        stepDetailButton.hidden = !canManageOrders || !['pending', 'processing'].includes(currentStatus);
        stepDetailButton.textContent = currentStatus === 'pending' ? 'Start Processing' : delivery ? 'Mark Ready for Seller Delivery' : 'Mark Ready for Pickup';
        stepDetailButton.dataset.nextStatus = currentStatus === 'pending' ? 'processing' : 'ready_for_pickup';
        cancelDetailButton.hidden = !canManageOrders || delivered || ['completed', 'cancelled'].includes(currentStatus);
        deliveryDetailButton.hidden = !canManageOrders || !delivery || currentStatus !== 'ready_for_pickup' || delivered;
        deliveryDetailButton.textContent = row.dataset.deliveryStartedAt ? 'Confirm Delivered' : 'Start Seller Delivery';
        deliveryDetailButton.dataset.action = row.dataset.deliveryStartedAt ? 'delivered' : 'start_delivery';

        renderOrderItems(row);

        setText('orderDetailTotalQty', `${row.dataset.quantity} ${row.dataset.quantity === '1' ? 'pc' : 'pcs'}`);
        setText('orderDetailAmount', formatCurrency(row.dataset.totalPrice));

        setText('orderDetailPickupLocation', delivery ? 'Not applicable' : row.dataset.pickupLocation || 'Not recorded');
        setText('orderDetailPickupSchedule', delivery ? 'Not applicable' : row.dataset.pickupScheduledAt || 'Not recorded');

        const paymentStatusContainer = document.getElementById('orderDetailPaymentStatus');
        if (paymentStatusContainer) {
            paymentStatusContainer.innerHTML = renderPaymentBadge(currentPayment);
        }

        const isPaid = currentPayment === 'paid';
        setText('orderDetailAmountPaid', isPaid ? formatCurrency(row.dataset.totalPrice) : '₱ 0.00');
        setText('orderDetailPaidAt', row.dataset.paidAt || (isPaid ? 'Timestamp not recorded' : 'Not paid yet'));
        setText('orderDetailRecordedBy', row.dataset.paymentEncodedBy || (isPaid ? 'Not recorded' : 'Pending payment'));
        setText('orderDetailOR', row.dataset.receiptNo || 'Not recorded');

        if (detailReceiptInput) {
            detailReceiptInput.value = row.dataset.receiptNo || '';
            detailReceiptInput.disabled = !canManageOrders || !isPaid;
            document.getElementById('orderORInputContainer').hidden = !canManageOrders || !isPaid;
            detailSaveButton.hidden = !canManageOrders || !isPaid;
        }

        if (btnModalCompleteOrder) {
            btnModalCompleteOrder.style.display = canManageOrders && currentStatus === 'ready_for_pickup' && (!delivery || delivered) ? 'inline-block' : 'none';
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
        if (cashReceivedCheck) cashReceivedCheck.checked = false;
        const delivery = row.dataset.fulfillmentMethod === 'seller_delivery';
        setText('fulfillmentConfirmationLabel', delivery ? 'Seller delivery has been recorded' : 'Buyer has collected the order');
        setText('completePaymentMethod', delivery ? 'Cash' : 'Cash on Pickup');
        setText('completeFulfillmentDescription', delivery ? 'Delivery is already recorded. Explicitly confirm payment before completing this order.' : 'Confirm that the buyer has collected the order and payment was received.');
        if (pickupConfirmedCheck) pickupConfirmedCheck.checked = false;
        if (btnConfirmCompleteOrder) {
            btnConfirmCompleteOrder.disabled = true;
        }
        if (completeAlert) {
            completeAlert.style.display = 'none';
            completeAlert.textContent = '';
        }

        switchFromDetails(completeModal);
    }

    function switchFromDetails(nextModal) {
        if (detailModalEl?.classList.contains('show')) {
            detailModalEl.addEventListener('hidden.bs.modal', () => nextModal.show(), {once: true});
            detailModal.hide();
        } else nextModal.show();
    }

    function syncCompleteButton() {
        if (btnConfirmCompleteOrder) {
            btnConfirmCompleteOrder.disabled = actionPending || !(cashReceivedCheck?.checked && pickupConfirmedCheck?.checked);
        }
    }
    cashReceivedCheck?.addEventListener('change', syncCompleteButton);
    pickupConfirmedCheck?.addEventListener('change', syncCompleteButton);

    btnConfirmCompleteOrder?.addEventListener('click', async () => {
        if (actionPending || !selectedRow || !cashReceivedCheck.checked || !pickupConfirmedCheck.checked) return;

        actionPending = true;
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
                    pickup_confirmed: true,
                    official_receipt_no: selectedRow.dataset.receiptNo || '',
                }),
            });

            const result = await window.CampusHubActions.json(response, 'Unable to confirm the order update. Reload the record before retrying.');
            if (!result.order) throw new Error('The order update was not confirmed. Reload before retrying.');
            if (!response.ok) throw new Error(result.error || 'Failed to complete the order.');

            completeModal.hide();
            finishOrderAction('Order completed and payment confirmed.');
        } catch (error) {
            actionPending = false;
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
        switchFromDetails(cancelModal);
    }

    btnConfirmCancelOrder?.addEventListener('click', async () => {
        if (actionPending || !selectedRow) return;
        const reason = cancelReasonInput ? cancelReasonInput.value.trim() : '';
        if (!reason) {
            if (cancelAlert) {
                cancelAlert.textContent = 'Please enter a cancellation reason.';
                cancelAlert.style.display = 'block';
            }
            return;
        }

        actionPending = true;
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

            const result = await window.CampusHubActions.json(response, 'Unable to confirm the order update. Reload the record before retrying.');
            if (!result.order) throw new Error('The order update was not confirmed. Reload before retrying.');
            if (!response.ok) throw new Error(result.error || 'Failed to cancel order.');

            cancelModal.hide();
            finishOrderAction('Order has been cancelled and stock restored.');
        } catch (error) {
            actionPending = false;
            if (cancelAlert) {
                cancelAlert.textContent = error.message || 'Failed to cancel order.';
                cancelAlert.style.display = 'block';
            }
            btnConfirmCancelOrder.disabled = false;
            btnConfirmCancelOrder.textContent = 'Confirm Cancellation';
        }
    });

    btnModalCompleteOrder?.addEventListener('click', () => {
        if (selectedRow) openCompleteModal(selectedRow);
    });

    detailForm?.addEventListener('submit', async (e) => {
        e.preventDefault();
        if (actionPending || !selectedRow || selectedRow.dataset.paymentStatus !== 'paid') return;

        actionPending = true;
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

            const result = await window.CampusHubActions.json(response, 'Unable to confirm the order update. Reload the record before retrying.');
            if (!result.order) throw new Error('The order update was not confirmed. Reload before retrying.');
            if (!response.ok) throw new Error(result.error || 'Failed to save receipt info.');

            detailModal.hide();
            finishOrderAction('Receipt information saved.');
        } catch (error) {
            actionPending = false;
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

    async function executeStatusStep(row, nextStatus, fulfillmentAction = null) {
        if (actionPending || !row || (!nextStatus && !fulfillmentAction)) return;
        actionPending = true;

        stepDetailButton.disabled = true;
        deliveryDetailButton.disabled = true;
        try {
            const response = await fetch(row.dataset.updateUrl, {
                method: 'POST',
                credentials: 'same-origin',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken': getCsrfToken(),
                },
                body: JSON.stringify(fulfillmentAction ? {fulfillment_action: fulfillmentAction} : { status: nextStatus }),
            });

            const result = await window.CampusHubActions.json(response, 'Unable to confirm the order update. Reload the record before retrying.');
            if (!result.order) throw new Error('The order update was not confirmed. Reload before retrying.');
            if (!response.ok) throw new Error(result.error || `Failed to update status to ${nextStatus}.`);

            finishOrderAction(fulfillmentAction ? 'Seller delivery progress recorded. Payment is unchanged.' : `Order status updated to ${nextStatus.replace(/_/g, ' ')}.`);
        } catch (error) {
            actionPending = false;
            stepDetailButton.disabled = false;
            deliveryDetailButton.disabled = false;
            showActionToast(error.message || 'Failed to update order status.', true);
        }
    }

    tableBody?.addEventListener('click', (e) => {
        const viewBtn = e.target.closest('.view-order-action');
        if (viewBtn) {
            if (viewBtn.matches('a') && (e.ctrlKey || e.metaKey || e.shiftKey || e.altKey)) return;
            e.preventDefault();
            detailTrigger = viewBtn;
            const row = viewBtn.closest('tr');
            if (row) openOrderDetail(row);
            return;
        }

    });

    // Dashboard deep links reuse a row already authorized by the Orders view.
    const requestedOrder = new URLSearchParams(window.location.search).get('order');
    const requestedRow = requestedOrder && [...(tableBody?.querySelectorAll('tr[data-order-id]') || [])]
        .find(row => row.dataset.orderId === requestedOrder);
    if (requestedRow) openOrderDetail(requestedRow);
    stepDetailButton?.addEventListener('click', () => executeStatusStep(selectedRow, stepDetailButton.dataset.nextStatus));
    deliveryDetailButton?.addEventListener('click', () => {
        if (deliveryDetailButton.dataset.action === 'delivered' && !window.confirm('Confirm that the seller personally delivered this order to the customer? This does not record payment.')) return;
        executeStatusStep(selectedRow, null, deliveryDetailButton.dataset.action);
    });
    cancelDetailButton?.addEventListener('click', () => openCancelModal(selectedRow));

    // Filters are GET requests: Django applies scope, pagination and all KPI counts.
    let searchTimer;
    function syncMajorLabel() {
        majorFilter.options[0].textContent = programFilter.value && majorFilter.disabled ? 'Not Applicable' : 'All Majors';
    }
    function submitFilters() {
        window.clearTimeout(searchTimer);
        const custom = datePresetFilter.value === 'custom';
        dateFromInput.required = dateToInput.required = custom;
        if (custom && (!dateFromInput.value || !dateToInput.value)) return;
        dateToInput.setCustomValidity(custom && dateFromInput.value > dateToInput.value ? 'End date must not be before start date.' : '');
        if (filtersForm.reportValidity()) filtersForm.requestSubmit();
    }
    function syncDates() {
        const custom = datePresetFilter.value === 'custom';
        customDateRange.hidden = !custom;
        dateFromInput.disabled = dateToInput.disabled = !custom;
        dateFromInput.required = dateToInput.required = custom;
        if (!custom) {
            dateFromInput.value = dateToInput.value = '';
            dateToInput.setCustomValidity('');
        }
    }
    syncDates();
    syncMajorLabel();
    searchInput?.addEventListener('input', () => {
        window.clearTimeout(searchTimer);
        searchTimer = window.setTimeout(submitFilters, 300);
    });
    filtersForm?.querySelectorAll('select').forEach(control => control.addEventListener('change', () => {
        if (control === programFilter) { majorFilter.value = ''; window.CampusHubAcademic.sync(programFilter, majorFilter); syncMajorLabel(); }
        if (control === datePresetFilter) syncDates();
        submitFilters();
    }));
    [dateFromInput, dateToInput].forEach(control => control?.addEventListener('change', submitFilters));
    statCards.forEach(card => {
        const active = (card.dataset.orderStatFilter || '') === statusFilter.value &&
            (statusFilter.value !== 'ready_for_pickup' || fulfillmentFilter.value === 'pickup');
        card.classList.toggle('is-active', active);
        card.setAttribute('aria-pressed', String(active));
        card.addEventListener('click', () => {
            statusFilter.value = card.dataset.orderStatFilter || '';
            if (statusFilter.value === 'ready_for_pickup') fulfillmentFilter.value = 'pickup';
            submitFilters();
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

});
