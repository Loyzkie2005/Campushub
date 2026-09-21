(function () {
    const STORAGE_KEY = 'campushub_facility_bookings';
    const searchInput = document.getElementById('fbSearchInput');
    const filterRoot = document.getElementById('fbFilters');
    const listRoot = document.getElementById('fbFacilityList');
    const noResults = document.getElementById('fbNoResults');
    const bookingModal = document.getElementById('fbBookingModal');
    const detailsModal = document.getElementById('fbDetailsModal');
    const bookingForm = document.getElementById('fbBookingForm');
    const modalPreview = document.getElementById('fbModalPreview');
    const detailsBody = document.getElementById('fbDetailsBody');
    const detailsBookBtn = document.getElementById('fbDetailsBookBtn');
    const confirmBookingBtn = document.getElementById('fbConfirmBooking');
    const myBookingsRoot = document.getElementById('fbMyBookings');
    const toast = document.getElementById('fbToast');

    let activeFilter = 'all';
    let selectedFacility = null;

    function escapeHtml(value) {
        return String(value || '')
            .replace(/&/g, '&amp;')
            .replace(/</g, '&lt;')
            .replace(/>/g, '&gt;')
            .replace(/"/g, '&quot;')
            .replace(/'/g, '&#39;');
    }

    function showToast(message, isError = false) {
        if (!toast) return;
        toast.textContent = message;
        toast.classList.toggle('is-error', isError);
        toast.classList.add('is-visible');
        window.clearTimeout(showToast._timer);
        showToast._timer = window.setTimeout(() => {
            toast.classList.remove('is-visible', 'is-error');
        }, 3200);
    }

    function getCardData(card) {
        return {
            id: card.dataset.facilityId || '',
            name: card.dataset.facilityName || '',
            description: card.dataset.description || '',
            capacity: card.dataset.capacity || '',
            rate: card.dataset.rate || '',
            priceType: card.dataset.priceType || 'hour',
            status: card.dataset.status || 'available',
            imageUrl: card.dataset.imageUrl || '',
            bookingMode: card.dataset.bookingMode || 'room',
        };
    }

    function formatPrice(rate, priceType) {
        const amount = Number(rate || 0);
        const formatted = amount.toLocaleString('en-PH');
        return `\u20b1${formatted} / ${priceType || 'hour'}`;
    }

    function renderPreview(target, facility) {
        if (!target) return;
        const imageHtml = facility.imageUrl
            ? `<img src="${escapeHtml(facility.imageUrl)}" alt="${escapeHtml(facility.name)}">`
            : '';
        target.innerHTML = `
            ${imageHtml}
            <div>
                <h4>${escapeHtml(facility.name)}</h4>
                <p>${escapeHtml(formatPrice(facility.rate, facility.priceType))}</p>
            </div>`;
    }

    function renderDetails(facility) {
        if (!detailsBody) return;
        detailsBody.innerHTML = `
            <div class="fb-modal-preview">
                ${facility.imageUrl ? `<img src="${escapeHtml(facility.imageUrl)}" alt="${escapeHtml(facility.name)}">` : ''}
                <div>
                    <h4>${escapeHtml(facility.name)}</h4>
                    <p>${escapeHtml(formatPrice(facility.rate, facility.priceType))}</p>
                </div>
            </div>
            <div class="fb-meta" style="margin-bottom:12px;">
                <span class="fb-status fb-status-${escapeHtml(facility.status)}">${escapeHtml(facility.status)}</span>
            </div>
            ${facility.capacity ? `<p class="fb-card-desc"><strong>Capacity:</strong> ${escapeHtml(facility.capacity)}</p>` : ''}
            ${facility.description ? `<p class="fb-card-desc">${escapeHtml(facility.description)}</p>` : ''}
            <p class="fb-card-desc"><strong>Booking mode:</strong> ${escapeHtml(facility.bookingMode)}</p>`;
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
        if (!document.querySelector('.fb-modal.is-open')) {
            document.body.classList.remove('modal-open');
        }
    }

    function closeAllModals() {
        [bookingModal, detailsModal].forEach(closeModal);
    }

    function setDefaultBookingDate() {
        const dateInput = document.getElementById('fbBookingDate');
        if (!dateInput) return;
        const today = new Date();
        dateInput.min = today.toISOString().slice(0, 10);
        if (!dateInput.value) {
            dateInput.value = today.toISOString().slice(0, 10);
        }
    }

    function openBookingModal(facility) {
        selectedFacility = facility;
        renderPreview(modalPreview, facility);
        bookingForm?.reset();
        setDefaultBookingDate();
        openModal(bookingModal);
    }

    function openDetailsModal(facility) {
        selectedFacility = facility;
        renderDetails(facility);
        if (detailsBookBtn) {
            detailsBookBtn.disabled = facility.status !== 'available';
        }
        openModal(detailsModal);
    }

    function loadBookings() {
        try {
            return JSON.parse(localStorage.getItem(STORAGE_KEY) || '[]');
        } catch (_) {
            return [];
        }
    }

    function saveBookings(bookings) {
        localStorage.setItem(STORAGE_KEY, JSON.stringify(bookings));
    }

    function renderMyBookings() {
        if (!myBookingsRoot) return;
        const bookings = loadBookings();
        if (!bookings.length) {
            myBookingsRoot.innerHTML = `
                <div class="fb-empty" style="padding:20px;border-style:solid;">
                    <strong>No bookings yet</strong>
                    Tap Book Now on an available facility to get started.
                </div>`;
            return;
        }

        myBookingsRoot.innerHTML = bookings.slice(0, 8).map((booking) => `
            <div class="fb-booking-item">
                <div>
                    <strong>${escapeHtml(booking.facilityName)}</strong>
                    <span>${escapeHtml(booking.purpose || 'Reservation')}</span>
                    <span>${escapeHtml(booking.date)} · ${escapeHtml(booking.startTime)} - ${escapeHtml(booking.endTime)}</span>
                </div>
                <time>${escapeHtml(booking.createdLabel || 'Booked')}</time>
            </div>`).join('');
    }

    function applyFilters() {
        if (!listRoot) return;
        const query = (searchInput?.value || '').trim().toLowerCase();
        let visibleCount = 0;

        listRoot.querySelectorAll('.fb-card').forEach((card) => {
            const name = card.dataset.name || '';
            const status = card.dataset.status || '';
            const matchesSearch = !query || name.includes(query);
            const matchesFilter = activeFilter === 'all' || status === activeFilter;
            const visible = matchesSearch && matchesFilter;
            card.style.display = visible ? '' : 'none';
            if (visible) visibleCount += 1;
        });

        if (noResults) {
            noResults.classList.toggle('d-none', visibleCount > 0 || !listRoot.querySelector('.fb-card'));
        }
    }

    filterRoot?.addEventListener('click', (event) => {
        const chip = event.target.closest('[data-filter]');
        if (!chip) return;
        activeFilter = chip.dataset.filter || 'all';
        filterRoot.querySelectorAll('.fb-filter-chip').forEach((button) => {
            button.classList.toggle('is-active', button === chip);
        });
        applyFilters();
    });

    searchInput?.addEventListener('input', applyFilters);

    listRoot?.addEventListener('click', (event) => {
        const actionButton = event.target.closest('[data-fb-action]');
        if (!actionButton) return;
        const card = actionButton.closest('.fb-card');
        if (!card) return;
        const facility = getCardData(card);
        const action = actionButton.dataset.fbAction;
        if (action === 'book') openBookingModal(facility);
        if (action === 'details') openDetailsModal(facility);
    });

    detailsBookBtn?.addEventListener('click', () => {
        if (!selectedFacility) return;
        closeModal(detailsModal);
        openBookingModal(selectedFacility);
    });

    document.querySelectorAll('[data-fb-close-modal]').forEach((button) => {
        button.addEventListener('click', closeAllModals);
    });

    confirmBookingBtn?.addEventListener('click', () => {
        if (!selectedFacility) return;

        const date = document.getElementById('fbBookingDate')?.value || '';
        const startTime = document.getElementById('fbBookingStart')?.value || '';
        const endTime = document.getElementById('fbBookingEnd')?.value || '';
        const purpose = document.getElementById('fbBookingPurpose')?.value.trim() || '';
        const notes = document.getElementById('fbBookingNotes')?.value.trim() || '';

        if (!date || !startTime || !endTime || !purpose) {
            showToast('Please complete all required booking fields.', true);
            return;
        }

        if (startTime >= endTime) {
            showToast('End time must be later than start time.', true);
            return;
        }

        const bookings = loadBookings();
        bookings.unshift({
            id: `${selectedFacility.id}-${Date.now()}`,
            facilityId: selectedFacility.id,
            facilityName: selectedFacility.name,
            date,
            startTime,
            endTime,
            purpose,
            notes,
            createdLabel: new Date().toLocaleString(),
        });
        saveBookings(bookings);
        renderMyBookings();
        closeModal(bookingModal);
        showToast(`Booking confirmed for ${selectedFacility.name}.`);
    });

    setDefaultBookingDate();
    renderMyBookings();
    applyFilters();
})();
