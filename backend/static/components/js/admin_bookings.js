(function () {
    'use strict';

    const TYPE_META = {
        class: { label: 'Class Schedule', badge: 'Class Schedule' },
        reservation: { label: 'Reservation', badge: 'Reservation' },
        maintenance: { label: 'Maintenance', badge: 'Maintenance' },
        assessment: { label: 'Assessment', badge: 'Assessment' },
    };

    const monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December',
    ];
    const weekdayShort = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

    const grid = document.getElementById('bkCalendarGrid');
    const monthLabel = document.getElementById('bkMonthLabel');
    const upcomingList = document.getElementById('bkUpcomingList');
    const allBookingsBody = document.getElementById('bkAllBookingsBody');
    const bookingSearch = document.getElementById('bkBookingSearch');
    const bookingStatusFilter = document.getElementById('bkStatusFilter');
    const bookingFacilityFilter = document.getElementById('bkFacilityFilter');
    const bookingDetailsModal = document.getElementById('bkBookingDetailsModal');
    const bookingDetailsId = document.getElementById('bkBookingDetailsId');
    const bookingDetailsContent = document.getElementById('bkBookingDetailsContent');
    const bookingDetailsPurpose = document.getElementById('bkBookingDetailsPurpose');
    const prevBtn = document.getElementById('bkPrevMonth');
    const nextBtn = document.getElementById('bkNextMonth');
    const toastEl = document.getElementById('bkToast');

    function getCookie(name) {
        const match = document.cookie
            .split(';')
            .map((c) => c.trim())
            .find((c) => c.startsWith(`${name}=`));
        return match ? decodeURIComponent(match.split('=').slice(1).join('=')) : '';
    }

    function getCsrfToken() {
        const input = document.querySelector('[name=csrfmiddlewaretoken]');
        return (input && input.value) || getCookie('csrftoken') || '';
    }

    function loadEvents() {
        const el = document.getElementById('bkCalendarEvents');
        if (!el) return [];
        try {
            const data = JSON.parse(el.textContent || '[]');
            return Array.isArray(data) ? data : [];
        } catch (err) {
            return [];
        }
    }

    function loadBookingRequests() {
        const el = document.getElementById('bkBookingRequests');
        if (!el) return [];
        try {
            const data = JSON.parse(el.textContent || '[]');
            return Array.isArray(data) ? data : [];
        } catch (err) {
            return [];
        }
    }

    const events = loadEvents();
    const bookingRows = loadBookingRequests();
    const today = new Date();
    let viewYear = today.getFullYear();
    let viewMonth = today.getMonth();
    let upcomingFilter = 'all';

    function pad(n) {
        return String(n).padStart(2, '0');
    }

    function toDateKey(year, monthIndex, day) {
        return `${year}-${pad(monthIndex + 1)}-${pad(day)}`;
    }

    function parseDateKey(key) {
        const [y, m, d] = String(key || '').split('-').map(Number);
        if (!y || !m || !d) return null;
        return new Date(y, m - 1, d);
    }

    function formatTimeRange(start, end) {
        if (!start && !end) return '';
        const clean = (t) => String(t || '').slice(0, 5);
        if (start && end) return `${clean(start)} - ${clean(end)}`;
        return clean(start || end);
    }

    function formatLongDate(key) {
        const dt = parseDateKey(key);
        if (!dt) return key;
        const mon = monthNames[dt.getMonth()].slice(0, 3);
        return `${mon} ${pad(dt.getDate())}, ${dt.getFullYear()} (${weekdayShort[dt.getDay()]})`;
    }

    function formatSubmittedDate(value) {
        const dt = new Date(value);
        if (!value || Number.isNaN(dt.getTime())) return '-';
        return dt.toLocaleString('en-US', {
            month: 'short',
            day: '2-digit',
            year: 'numeric',
            hour: 'numeric',
            minute: '2-digit',
        });
    }

    function formatCurrency(value) {
        const amount = Number(value || 0);
        const formatted = Number.isFinite(amount)
            ? amount.toLocaleString('en-US', { minimumFractionDigits: 2, maximumFractionDigits: 2 })
            : '0.00';
        return `\u20B1${formatted}`;
    }

    function eventsForDate(dateKey) {
        return events
            .filter((ev) => ev.date === dateKey)
            .sort((a, b) => String(a.start || '').localeCompare(String(b.start || '')));
    }

    function escapeHtml(value) {
        return String(value ?? '').replace(/[&<>"']/g, (char) => ({
            '&': '&amp;',
            '<': '&lt;',
            '>': '&gt;',
            '"': '&quot;',
            "'": '&#39;',
        }[char]));
    }

    function showToast(message, isError) {
        if (!toastEl) return;
        toastEl.textContent = message;
        toastEl.classList.toggle('is-error', !!isError);
        toastEl.classList.add('is-show');
        clearTimeout(showToast._timer);
        showToast._timer = setTimeout(() => toastEl.classList.remove('is-show'), 2600);
    }

    function timeToMinutes(value) {
        const [h, m] = String(value || '').split(':').map(Number);
        if (Number.isNaN(h) || Number.isNaN(m)) return null;
        return h * 60 + m;
    }

    function addEvent(event) {
        events.push(event);
        events.sort((a, b) => {
            const byDate = String(a.date).localeCompare(String(b.date));
            if (byDate !== 0) return byDate;
            return String(a.start || '').localeCompare(String(b.start || ''));
        });
        const dt = parseDateKey(event.date);
        if (dt) {
            viewYear = dt.getFullYear();
            viewMonth = dt.getMonth();
        }
        renderCalendar();
    }

    async function createBooking(payload) {
        const response = await fetch('/api/bookings/create/', {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCsrfToken(),
            },
            credentials: 'same-origin',
            body: JSON.stringify(payload),
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.error || 'Could not save booking.');
        }
        return data.event;
    }

    function openModal(modal) {
        if (!modal) return;
        modal.classList.add('is-open');
        modal.setAttribute('aria-hidden', 'false');
        document.body.classList.add('modal-open');
    }

    function closeModal(modal) {
        if (!modal) return;
        modal.classList.remove('is-open');
        modal.setAttribute('aria-hidden', 'true');
        if (!document.querySelector('.bk-modal.is-open')) {
            document.body.classList.remove('modal-open');
        }
    }

    function setSubmitBusy(form, busy, label) {
        const btn = form?.querySelector('button[type="submit"]');
        if (!btn) return;
        btn.disabled = !!busy;
        if (label) btn.textContent = label;
    }

    function renderCalendar() {
        if (!grid || !monthLabel) {
            renderUpcoming();
            renderAllBookings();
            return;
        }
        monthLabel.textContent = `${monthNames[viewMonth]} ${viewYear}`;
        grid.querySelectorAll('.bk-day').forEach((node) => node.remove());

        const firstDay = new Date(viewYear, viewMonth, 1).getDay();
        const daysInMonth = new Date(viewYear, viewMonth + 1, 0).getDate();
        const daysInPrev = new Date(viewYear, viewMonth, 0).getDate();
        const isCurrentMonth = today.getFullYear() === viewYear && today.getMonth() === viewMonth;

        for (let i = firstDay - 1; i >= 0; i -= 1) {
            const day = daysInPrev - i;
            const cell = document.createElement('div');
            cell.className = 'bk-day is-muted';
            cell.innerHTML = `<span class="bk-day-num">${day}</span>`;
            grid.appendChild(cell);
        }

        for (let day = 1; day <= daysInMonth; day += 1) {
            const dateKey = toDateKey(viewYear, viewMonth, day);
            const dayEvents = eventsForDate(dateKey);
            const cell = document.createElement('div');
            cell.className = 'bk-day' + (isCurrentMonth && day === today.getDate() ? ' is-today' : '');
            cell.dataset.date = dateKey;

            let html = `<span class="bk-day-num">${day}</span>`;
            const visible = dayEvents.slice(0, 2);
            visible.forEach((ev) => {
                const type = TYPE_META[ev.type] ? ev.type : 'reservation';
                const meta = TYPE_META[type];
                const time = formatTimeRange(ev.start, ev.end);
                html += `
                    <div class="bk-event bk-event-${type}" title="${escapeHtml(meta.label)}">
                        <strong>• ${escapeHtml(meta.label)}</strong>
                        <span>${escapeHtml(ev.facility || 'Facility')}</span>
                        ${time ? `<span>${escapeHtml(time)}</span>` : ''}
                    </div>`;
            });
            if (dayEvents.length > 2) {
                html += `<div class="bk-event-more">+${dayEvents.length - 2} more</div>`;
            }
            cell.innerHTML = html;
            grid.appendChild(cell);
        }

        const total = firstDay + daysInMonth;
        const trailing = (7 - (total % 7)) % 7;
        for (let i = 1; i <= trailing; i += 1) {
            const cell = document.createElement('div');
            cell.className = 'bk-day is-muted';
            cell.innerHTML = `<span class="bk-day-num">${i}</span>`;
            grid.appendChild(cell);
        }

        renderUpcoming();
        renderAllBookings();
    }

    function renderUpcoming() {
        if (!upcomingList) return;
        const upcomingCard = document.querySelector('.bk-upcoming-card');

        const todayKey = toDateKey(today.getFullYear(), today.getMonth(), today.getDate());
        const upcoming = events
            .filter((ev) => ev.date >= todayKey)
            .filter((ev) => upcomingFilter === 'all' || ev.type === upcomingFilter)
            .sort((a, b) => {
                const byDate = String(a.date).localeCompare(String(b.date));
                if (byDate !== 0) return byDate;
                return String(a.start || '').localeCompare(String(b.start || ''));
            })
            .slice(0, 6);

        if (upcomingCard) {
            upcomingCard.classList.toggle('is-filled', upcoming.length > 0);
            upcomingCard.classList.toggle('is-empty', upcoming.length === 0);
        }

        if (!upcoming.length) {
            upcomingList.innerHTML = '<li class="bk-upcoming-empty">No upcoming facility bookings yet.</li>';
            return;
        }

        upcomingList.innerHTML = upcoming.map((ev, index) => {
            const type = TYPE_META[ev.type] ? ev.type : 'reservation';
            const meta = TYPE_META[type];
            const time = formatTimeRange(ev.start, ev.end);
            const reservedBy = ev.reserved_by
                ? `<span>
                    <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M15.75 6a3.75 3.75 0 1 1-7.5 0 3.75 3.75 0 0 1 7.5 0ZM4.501 20.118a7.5 7.5 0 0 1 14.998 0A17.933 17.933 0 0 1 12 21.75c-2.676 0-5.216-.584-7.499-1.632Z" /></svg>
                    Reserved by ${escapeHtml(ev.reserved_by)}
                   </span>`
                : '';

            return `
                <li class="bk-upcoming-item">
                    <span class="bk-upcoming-num is-${type}">${index + 1}</span>
                    <div class="bk-upcoming-body">
                        <span class="bk-upcoming-badge is-${type}">${escapeHtml(meta.badge)}</span>
                        <strong>${escapeHtml(ev.facility || 'Facility')}</strong>
                        <div class="bk-upcoming-meta">
                            <span>
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M6.75 3v2.25M17.25 3v2.25M3 8.25h18M4.5 5.25h15A1.5 1.5 0 0 1 21 6.75v12A1.5 1.5 0 0 1 19.5 20.25h-15A1.5 1.5 0 0 1 3 18.75v-12A1.5 1.5 0 0 1 4.5 5.25z" /></svg>
                                ${escapeHtml(formatLongDate(ev.date))}
                            </span>
                            ${time ? `<span>
                                <svg xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke-width="1.8" stroke="currentColor"><path stroke-linecap="round" stroke-linejoin="round" d="M12 6v6h4.5m4.5 0a9 9 0 1 1-18 0 9 9 0 0 1 18 0Z" /></svg>
                                ${escapeHtml(time)}
                            </span>` : ''}
                            ${reservedBy}
                        </div>
                    </div>
                </li>`;
        }).join('');
    }

    function renderAllBookings() {
        if (!allBookingsBody) return;

        const searchTerm = String(bookingSearch?.value || '').trim().toLowerCase();
        const selectedStatus = bookingStatusFilter?.value || 'all';
        const selectedFacility = bookingFacilityFilter?.value || 'all';
        const rows = bookingRows.filter((booking) => {
            const matchesSearch = !searchTerm || [
                booking.id,
                booking.reserved_by,
                booking.facility,
                booking.room,
            ].some((value) => String(value || '').toLowerCase().includes(searchTerm));
            const matchesStatus = selectedStatus === 'all'
                || String(booking.status || '').toLowerCase() === selectedStatus;
            const matchesFacility = selectedFacility === 'all'
                || String(booking.facility_id || '') === selectedFacility;
            return matchesSearch && matchesStatus && matchesFacility;
        });

        const setCount = (id, value) => {
            const node = document.getElementById(id);
            if (node) node.textContent = String(value);
        };
        setCount('bkTotalRequests', bookingRows.length);
        setCount('bkPendingRequests', bookingRows.filter((item) => item.status === 'pending').length);
        setCount('bkApprovedRequests', bookingRows.filter((item) => item.status === 'approved').length);
        setCount('bkRejectedRequests', bookingRows.filter((item) => item.status === 'rejected').length);

        if (!rows.length) {
            allBookingsBody.innerHTML = '<tr><td colspan="11" class="bk-table-empty">No booking requests found.</td></tr>';
            return;
        }

        allBookingsBody.innerHTML = rows.map((event) => {
            const status = String(event.status || 'pending');
            const statusClass = status.toLowerCase().replace(/[^a-z]+/g, '-');
            const paymentStatus = String(event.payment_status || 'unpaid');
            const paymentClass = paymentStatus.toLowerCase().replace(/[^a-z]+/g, '-');
            const sourceIndex = bookingRows.indexOf(event);
            return `
                <tr>
                    <td class="bk-booking-id">${escapeHtml(event.id || '-')}</td>
                    <td>${escapeHtml(event.reserved_by || '-')}</td>
                    <td>${escapeHtml(event.facility || 'Facility')}</td>
                    <td>${escapeHtml(event.room || '-')}</td>
                    <td>${escapeHtml(formatLongDate(event.date))}</td>
                    <td>${escapeHtml(formatTimeRange(event.start, event.end) || '-')}</td>
                    <td class="bk-table-amount">${escapeHtml(formatCurrency(event.total_amount))}</td>
                    <td><span class="bk-table-payment is-${paymentClass}">${escapeHtml(paymentStatus)}</span></td>
                    <td><span class="bk-table-status is-${statusClass}">${escapeHtml(status)}</span></td>
                    <td>${escapeHtml(formatSubmittedDate(event.created_at))}</td>
                    <td class="bk-table-actions">
                        <button type="button" class="bk-view-booking" data-booking-index="${sourceIndex}" aria-label="View booking ${escapeHtml(event.id || '')}" title="View details">
                            <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="M2.5 12s3.5-6 9.5-6 9.5 6 9.5 6-3.5 6-9.5 6-9.5-6-9.5-6Z"/><circle cx="12" cy="12" r="2.5"/></svg>
                        </button>
                    </td>
                </tr>`;
        }).join('');
    }

    function openBookingDetails(booking) {
        if (!booking || !bookingDetailsModal || !bookingDetailsContent) return;
        const type = TYPE_META[booking.type] ? TYPE_META[booking.type].label : 'Reservation';
        const detailRows = [
            ['Requester', booking.reserved_by || '-'],
            ['Facility', booking.facility || '-'],
            ['Room / Unit', booking.room || '-'],
            ['Schedule Type', type],
            ['Date', formatLongDate(booking.date)],
            ['Time', formatTimeRange(booking.start, booking.end) || '-'],
            ['Total Cost', formatCurrency(booking.total_amount)],
            ['Payment Status', booking.payment_status || 'unpaid'],
            ['Booking Status', booking.status || 'pending'],
            ['Date Submitted', formatSubmittedDate(booking.created_at)],
        ];

        if (bookingDetailsId) bookingDetailsId.textContent = booking.id || '';
        bookingDetailsContent.innerHTML = detailRows.map(([label, value]) => `
            <div>
                <dt>${escapeHtml(label)}</dt>
                <dd>${escapeHtml(value)}</dd>
            </div>`).join('');
        if (bookingDetailsPurpose) {
            bookingDetailsPurpose.textContent = booking.purpose || 'No purpose provided.';
        }
        openModal(bookingDetailsModal);
    }

    if (allBookingsBody) {
        allBookingsBody.addEventListener('click', (event) => {
            const button = event.target.closest('.bk-view-booking');
            if (!button) return;
            openBookingDetails(bookingRows[Number(button.dataset.bookingIndex)]);
        });
    }

    [bookingSearch, bookingStatusFilter, bookingFacilityFilter].forEach((control) => {
        if (!control) return;
        control.addEventListener(control === bookingSearch ? 'input' : 'change', renderAllBookings);
    });

    if (prevBtn) {
        prevBtn.addEventListener('click', () => {
            viewMonth -= 1;
            if (viewMonth < 0) {
                viewMonth = 11;
                viewYear -= 1;
            }
            renderCalendar();
        });
    }

    if (nextBtn) {
        nextBtn.addEventListener('click', () => {
            viewMonth += 1;
            if (viewMonth > 11) {
                viewMonth = 0;
                viewYear += 1;
            }
            renderCalendar();
        });
    }

    const uploadModal = document.getElementById('bkUploadModal');
    const reservationModal = document.getElementById('bkReservationModal');
    const openUploadBtn = document.getElementById('bkOpenUploadBtn');
    const openReservationBtn = document.getElementById('bkOpenReservationBtn');
    const uploadForm = document.getElementById('bkUploadForm');
    const reservationForm = document.getElementById('bkReservationForm');
    const uploadImage = document.getElementById('bkUploadImage');
    const uploadImageName = document.getElementById('bkUploadImageName');
    const uploadDropzone = document.getElementById('bkUploadDropzone');

    function resetUploadDropzone() {
        if (uploadImageName) uploadImageName.textContent = 'No file selected';
        uploadDropzone?.classList.remove('has-file', 'is-dragover', 'is-loading');
        if (uploadImage) uploadImage.value = '';
    }

    if (openUploadBtn) openUploadBtn.addEventListener('click', () => openModal(uploadModal));
    if (openReservationBtn) openReservationBtn.addEventListener('click', () => openModal(reservationModal));

    document.querySelectorAll('[data-bk-close]').forEach((btn) => {
        btn.addEventListener('click', () => {
            closeModal(btn.closest('.bk-modal'));
        });
    });

    if (uploadDropzone && uploadImage) {
        ['dragenter', 'dragover'].forEach((type) => {
            uploadDropzone.addEventListener(type, (event) => {
                event.preventDefault();
                uploadDropzone.classList.add('is-dragover');
            });
        });
        ['dragleave', 'drop'].forEach((type) => {
            uploadDropzone.addEventListener(type, (event) => {
                event.preventDefault();
                uploadDropzone.classList.remove('is-dragover');
            });
        });
        uploadDropzone.addEventListener('drop', (event) => {
            const file = event.dataTransfer?.files?.[0];
            if (!file || !file.type.startsWith('image/')) return;
            const dt = new DataTransfer();
            dt.items.add(file);
            uploadImage.files = dt.files;
            uploadImage.dispatchEvent(new Event('change'));
        });
    }

    if (uploadImage && uploadImageName) {
        uploadImage.addEventListener('change', () => {
            const file = uploadImage.files && uploadImage.files[0];
            if (file) {
                uploadImageName.textContent = file.name;
                uploadDropzone?.classList.add('has-file');
            } else {
                resetUploadDropzone();
            }
        });
    }

    if (uploadForm) {
        uploadForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const facilityId = document.getElementById('bkUploadFacility')?.value || '';
            const type = document.getElementById('bkUploadType')?.value || 'class';
            const date = document.getElementById('bkUploadDate')?.value || '';
            const start = document.getElementById('bkUploadStart')?.value || '';
            const end = document.getElementById('bkUploadEnd')?.value || '';
            const description = document.getElementById('bkUploadDesc')?.value || '';

            if (!facilityId || !date || !start || !end) {
                showToast('Please complete the schedule details.', true);
                return;
            }
            if ((timeToMinutes(start) ?? 0) >= (timeToMinutes(end) ?? 0)) {
                showToast('End time must be later than start time.', true);
                return;
            }

            setSubmitBusy(uploadForm, true, 'Saving...');
            try {
                const saved = await createBooking({
                    facility_id: facilityId,
                    type,
                    date,
                    start,
                    end,
                    purpose: description,
                });
                addEvent(saved);
                uploadForm.reset();
                resetUploadDropzone();
                closeModal(uploadModal);
                showToast('Schedule saved to facility calendar.');
            } catch (err) {
                showToast(err.message || 'Could not save schedule.', true);
            } finally {
                setSubmitBusy(uploadForm, false, 'Confirm');
            }
        });
    }

    if (reservationForm) {
        reservationForm.addEventListener('submit', async (event) => {
            event.preventDefault();
            const facilityId = document.getElementById('bkResFacility')?.value || '';
            const reservedBy = document.getElementById('bkResBy')?.value || '';
            const date = document.getElementById('bkResDate')?.value || '';
            const start = document.getElementById('bkResStart')?.value || '';
            const end = document.getElementById('bkResEnd')?.value || '';
            const purpose = document.getElementById('bkResPurpose')?.value || '';

            if (!facilityId || !reservedBy || !date || !start || !end) {
                showToast('Please complete the reservation details.', true);
                return;
            }
            if ((timeToMinutes(start) ?? 0) >= (timeToMinutes(end) ?? 0)) {
                showToast('End time must be later than start time.', true);
                return;
            }

            setSubmitBusy(reservationForm, true, 'Saving...');
            try {
                const saved = await createBooking({
                    facility_id: facilityId,
                    type: 'reservation',
                    date,
                    start,
                    end,
                    purpose,
                    reserved_by: reservedBy,
                });
                addEvent(saved);
                reservationForm.reset();
                closeModal(reservationModal);
                showToast('Reservation saved.');
            } catch (err) {
                showToast(err.message || 'Could not save reservation.', true);
            } finally {
                setSubmitBusy(reservationForm, false, 'Save Reservation');
            }
        });
    }

    document.querySelectorAll('.bk-upcoming-filter').forEach((button) => {
        button.addEventListener('click', () => {
            upcomingFilter = button.dataset.filter || 'all';

            document.querySelectorAll('.bk-upcoming-filter').forEach((item) => {
                const isActive = item === button;
                item.classList.toggle('is-active', isActive);
                item.setAttribute('aria-pressed', String(isActive));
            });

            renderUpcoming();
        });
    });

    renderCalendar();
})();
