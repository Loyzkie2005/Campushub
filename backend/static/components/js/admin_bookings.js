(function () {
    'use strict';

    const TYPE_META = {
        class: { label: 'Class / Academic Schedule', badge: 'Class Schedule' },
        official: {label: 'Official Campus Use', badge: 'Official Use'},
        hold: {label: 'Administrative Hold / Unavailable', badge: 'Administrative Hold'},
        other: {label: 'Other Schedule', badge: 'Other'},
        blocked: {label: 'Unavailable', badge: 'Unavailable'},
        reservation: { label: 'Reservation', badge: 'Reservation' },
        maintenance: { label: 'Maintenance', badge: 'Maintenance' },
        assessment: { label: 'Assessment', badge: 'Assessment' },
    };

    const monthNames = [
        'January', 'February', 'March', 'April', 'May', 'June',
        'July', 'August', 'September', 'October', 'November', 'December',
    ];
    const weekdayShort = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

    const allBookingsBody = document.getElementById('bkAllBookingsBody');
    const bookingSearch = document.getElementById('bkBookingSearch');
    const bookingStatusFilter = document.getElementById('bkStatusFilter');
    const bookingFacilityFilter = document.getElementById('bkFacilityFilter');
    const bookingRecordFilter = document.getElementById('bkRecordFilter');
    const toastEl = document.getElementById('bkToast');

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

    const bookingRows = loadBookingRequests();
    const kpiGrid=document.getElementById('bkBookingKpis');
    let selectedKpi=kpiGrid?.dataset.filter || '', loadedKpi=selectedKpi, loadedStatus=bookingStatusFilter?.value || 'all', loadedRecord=bookingRecordFilter?.value || 'current';
    function selectKpi(key) {
        selectedKpi=key;
        kpiGrid?.querySelectorAll('[data-booking-kpi]').forEach(button=>button.setAttribute('aria-pressed',String(button.dataset.bookingKpi===key)));
    }
    kpiGrid?.addEventListener('click',event=>{
        const card=event.target.closest('[data-booking-kpi]');if(!card) return;
        clearTimeout(filterTimer);selectKpi(card.dataset.bookingKpi);
        if(bookingStatusFilter) bookingStatusFilter.value=selectedKpi==='pending'?'pending':'all';
        loadBookingPage(1);
    });
    let bookingPage=Number(document.getElementById('bkPageSummary')?.dataset.page) || 1,
        bookingPages=Number(document.getElementById('bkPageSummary')?.dataset.pages) || 1, listRevision=0, filterTimer;
    function renderBookingPagination(data) {
        const summary=document.getElementById('bkPageSummary'), numbers=document.getElementById('bkPageNumbers');
        if(!summary || !numbers) return;
        const total=Number(data.total) || 0;
        summary.textContent=`Showing ${data.start_index} to ${data.end_index} of ${total} booking request${total===1?'':'s'}`;
        const pages=[...new Set([1,bookingPage-1,bookingPage,bookingPage+1,bookingPages])]
            .filter(page=>page>=1 && page<=bookingPages).sort((a,b)=>a-b);
        numbers.replaceChildren();
        pages.forEach((page,index)=>{
            if(index && page-pages[index-1]>1){
                const gap=document.createElement('span');gap.textContent='…';gap.setAttribute('aria-hidden','true');numbers.append(gap);
            }
            const button=document.createElement('button');button.type='button';button.className='bk-page-button';
            button.dataset.bookingPage=String(page);button.textContent=String(page);button.setAttribute('aria-label',`Page ${page}`);
            if(page===bookingPage) button.setAttribute('aria-current','page');
            numbers.append(button);
        });
        document.getElementById('bkPreviousPage').disabled=!data.has_previous;
        document.getElementById('bkNextPage').disabled=!data.has_next;
    }
    const initialSummary=document.getElementById('bkPageSummary');
    if(initialSummary) renderBookingPagination({total:initialSummary.dataset.total,
        start_index:Number(initialSummary.dataset.start)||0,end_index:Number(initialSummary.dataset.end)||0,
        has_previous:bookingPage>1,has_next:bookingPage<bookingPages});
    document.getElementById('bkPageNumbers')?.addEventListener('click',event=>{
        const button=event.target.closest('[data-booking-page]');
        if(button && Number(button.dataset.bookingPage)!==bookingPage) loadBookingPage(Number(button.dataset.bookingPage));
    });
    async function loadBookingPage(page=1) {
        const revision=++listRevision;
        const params=new URLSearchParams({page:String(page),q:bookingSearch?.value || '',status:bookingStatusFilter?.value || 'all',facility:bookingFacilityFilter?.value || 'all',kpi:selectedKpi,record_status:bookingRecordFilter?.value || 'current'});
        kpiGrid?.setAttribute('aria-busy','true');
        try {
            const response=await fetch('/api/bookings/?'+params,{credentials:'same-origin'}),data=await response.json();
            if(!response.ok) throw new Error(data.error || 'Unable to load bookings.');
            if(revision!==listRevision) return;
            const keys=['total','pending','upcoming','unpaid'];
            if(kpiGrid && !keys.every(key=>Number.isInteger(data.kpis?.[key]) && data.kpis[key]>=0)) throw new Error('Unable to load booking totals. Please try again.');
            keys.forEach(key=>{const node=kpiGrid?.querySelector(`[data-booking-count="${key}"]`);if(node) node.textContent=String(data.kpis[key]);});
            loadedKpi=selectedKpi;loadedStatus=bookingStatusFilter?.value || 'all';loadedRecord=bookingRecordFilter?.value || 'current';
            bookingRows.splice(0,bookingRows.length,...data.bookings);bookingPage=data.page;bookingPages=data.pages;
            renderAllBookings(); renderBookingPagination(data);
        } catch(error){if(revision===listRevision){selectKpi(loadedKpi);if(bookingStatusFilter) bookingStatusFilter.value=loadedStatus;if(bookingRecordFilter) bookingRecordFilter.value=loadedRecord;showToast(error.message,true);}}
        finally {if(revision===listRevision) kpiGrid?.setAttribute('aria-busy','false');}
    }
    document.getElementById('bkPreviousPage')?.addEventListener('click',()=>loadBookingPage(Math.max(1,bookingPage-1)));
    document.getElementById('bkNextPage')?.addEventListener('click',()=>loadBookingPage(Math.min(bookingPages,bookingPage+1)));
    function pad(n) {
        return String(n).padStart(2, '0');
    }

    function parseDateKey(key) {
        const [y, m, d] = String(key || '').split('-').map(Number);
        if (!y || !m || !d) return null;
        return new Date(y, m - 1, d);
    }

    function formatBookingTimeRange(start, end) {
        const time=value=>{
            if(!value) return '';
            const [hour,minute]=String(value).split(':').map(Number);
            if(!Number.isInteger(hour) || hour<0 || hour>23 || !Number.isInteger(minute) || minute<0 || minute>59) return '';
            return `${hour%12 || 12}:${String(minute).padStart(2,'0')} ${hour<12?'AM':'PM'}`;
        };
        return [time(start),time(end)].filter(Boolean).join(' – ');
    }
    // Transaction tabs share this display helper; stored/API times stay HH:MM.
    window.CampusHubBookings = {formatTimeRange:formatBookingTimeRange, notify:showToast, openModal, closeModal};

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

    function openModal(modal) {
        if (!modal) return;
        modal._previousFocus = document.activeElement;
        modal.classList.add('is-open');
        modal.setAttribute('aria-hidden', 'false');
        document.body.classList.add('modal-open');
        document.documentElement.style.overflow = 'hidden';
        const dialog = modal.querySelector('.bk-modal-dialog');
        dialog?.setAttribute('tabindex', '-1');
        dialog?.focus();
    }

    function closeModal(modal) {
        if (!modal) return;
        modal.classList.remove('is-open');
        modal.setAttribute('aria-hidden', 'true');
        if (!document.querySelector('.bk-modal.is-open')) {
            document.body.classList.remove('modal-open');
            document.documentElement.style.overflow = '';
        }
        modal._previousFocus?.focus();
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
                    <td>${escapeHtml(formatLongDate(event.date) + (event.end_date ? ' - ' + formatLongDate(event.end_date) : ''))}</td>
                    <td>${escapeHtml(formatBookingTimeRange(event.start, event.end) || (event.end_date ? 'Check-in → Check-out' : '—'))}</td>
                    <td class="bk-table-amount">${escapeHtml(formatCurrency(event.total_amount))}</td>
                    <td><span class="bk-table-payment is-${paymentClass}">${escapeHtml(paymentStatus === 'paid' ? 'Paid' : 'Unpaid')}</span></td>
                    <td><span class="bk-table-status is-${statusClass}">${escapeHtml(event.status_label || (status === 'pending' ? 'Pending Approval' : status))}</span></td>
                    <td>${escapeHtml(formatSubmittedDate(event.created_at))}</td>
                    <td class="bk-table-actions">
                        <button type="button" class="bk-view-booking" data-more-index="${sourceIndex}" aria-label="More actions for booking ${escapeHtml(event.id)}" aria-expanded="false"><svg viewBox="0 0 24 24" fill="currentColor" aria-hidden="true"><circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/></svg></button>
                    </td>
                </tr>`;
        }).join('');
    }

    function openBookingDetails(booking, action=null) {
        if (!booking?.id) return;
        const params=new URLSearchParams();
        const tabs={payment_details:'Payment',job_order:'JobOrder',job_order_details:'JobOrder',booking_slip:'BookingForm',documents:'BookingForm',activity:'Activity'};
        if(['inspection_pre','inspection_post'].includes(action)) {
            params.set('tab','Inspection');params.set('action','inspection');params.set('kind',action.endsWith('_pre')?'pre':'post');
        }
        else if(['inspection_details','pre_inspection_details','post_inspection_details'].includes(action)) params.set('tab','Inspection');
        else if (tabs[action]) params.set('tab',tabs[action]);
        else if (action) params.set('action',action);
        const target=`/admin-bookings/${encodeURIComponent(booking.id)}/`+(params.size?'?'+params:'');
        window.location.assign(window.CampusHubAdminSession?.urlWithToken?.(target) || target);
    }

    document.addEventListener('campushub:reservation-created', (event) => {
        if (!event.detail?.id || !allBookingsBody) return;
        const index=bookingRows.findIndex(row=>row.id===event.detail.id);
        if(index>=0) bookingRows[index]=event.detail;else bookingRows.unshift(event.detail);
        if(bookingRows.length>20) bookingRows.splice(20);
        renderAllBookings();
        loadBookingPage(bookingPage);
    });
    document.addEventListener('campushub:booking-details', (event) => {
        openBookingDetails({id:event.detail});
    });

    if (allBookingsBody) {
        allBookingsBody.addEventListener('click', (event) => {
            const more=event.target.closest('[data-more-index]');
            if(more){showMoreActions(more,bookingRows[Number(more.dataset.moreIndex)]);return;}
        });
    }

    [bookingSearch, bookingStatusFilter, bookingFacilityFilter, bookingRecordFilter].forEach((control) => {
        if (!control) return;
        control.addEventListener(control === bookingSearch ? 'input' : 'change',()=>{
            if(control===bookingStatusFilter) selectKpi('');
            clearTimeout(filterTimer);filterTimer=setTimeout(()=>loadBookingPage(1),control===bookingSearch?250:0);
        });
    });

    function showMoreActions(trigger,booking) {
        const menu=document.getElementById('bkMoreMenu');
        const labels={view:'View Booking',approve:'Approve',reject:'Reject',cancel:'Cancel Booking',edit:'Edit',complete:'Complete Booking',
            payment:'Record Payment',payment_details:'Payment Details',job_order:'Job Order',
            job_order_details:'Job Order',booking_slip:'Booking Slip',documents:'Documents',activity:'Activity',
            archive:'Archive Booking',restore:'Restore Booking',inspection_details:'Inspection'};
        const actions=booking.actions || [], terminal=['rejected','cancelled'].includes(booking.status);
        const inspectionShortcuts=booking.inspection_shortcuts || [];
        inspectionShortcuts.forEach(item=>labels[item.action]=item.label);
        const items=['view'];
        if(booking.status==='cancelled') {
            items.push('booking_slip','payment_details','activity');
            if(booking.has_job_order) items.push('job_order_details');
            if(!inspectionShortcuts.length) items.push('inspection_details');
            items.push(...actions.filter(action=>['archive','restore'].includes(action)));
        }
        else if(terminal) items.push('activity');
        else {
            items.push(...actions.filter(action=>['approve','reject','edit','cancel','complete'].includes(action)));
            if(booking.status==='approved' && booking.payment_status!=='paid' && actions.includes('payment')) items.push('payment');
            if(booking.payment_status==='paid' || booking.status==='completed') items.push('payment_details');
            if(booking.status!=='pending') {
                if(actions.includes('job_order')) items.push('job_order');
                else if(booking.has_job_order) items.push('job_order_details');
            }
            if(booking.payment_status==='paid' || booking.status==='completed') items.push('booking_slip');
            if(booking.status==='completed') items.push('activity');
        }
        document.querySelectorAll('[data-more-index]').forEach(n=>n.setAttribute('aria-expanded','false'));
        items.push(...inspectionShortcuts.map(item=>item.action));
        const order=['view','booking_slip','job_order','job_order_details','payment_details','payment',
            'inspection_details','pre_inspection_details','post_inspection_details','inspection_pre','inspection_post',
            'approve','reject','edit','complete','documents','activity','cancel','archive','restore'];
        items.sort((a,b)=>order.indexOf(a)-order.indexOf(b));
        menu.innerHTML=items.map(action=>`${['cancel','archive','restore'].includes(action)?'<hr role="separator">':''}<button type="button" data-menu-action="${escapeHtml(action)}" data-menu-booking="${escapeHtml(booking.id)}">${escapeHtml(labels[action])}</button>`).join('');
        menu.hidden=false;const bounds=trigger.getBoundingClientRect();
        menu.style.left=Math.max(8,Math.min(document.documentElement.clientWidth-menu.offsetWidth-8,bounds.right-menu.offsetWidth))+'px';
        menu.style.top=Math.max(8,Math.min(document.documentElement.clientHeight-menu.offsetHeight-8,bounds.bottom+4))+'px';
        trigger.setAttribute('aria-expanded','true');menu._trigger=trigger;menu.querySelector('button')?.focus();
    }
    document.getElementById('bkMoreMenu')?.addEventListener('click',event=>{
        const button=event.target.closest('[data-menu-action]');if(!button) return;
        const menu=document.getElementById('bkMoreMenu');menu.hidden=true;menu._trigger?.setAttribute('aria-expanded','false');
        const booking=bookingRows.find(row=>row.id===button.dataset.menuBooking);
        openBookingDetails(booking,button.dataset.menuAction==='view'?null:button.dataset.menuAction);
    });
    document.addEventListener('click',event=>{if(!event.target.closest('#bkMoreMenu,[data-more-index]')) {const menu=document.getElementById('bkMoreMenu');if(menu){menu.hidden=true;menu._trigger?.setAttribute('aria-expanded','false');}}});
    document.addEventListener('keydown',event=>{const menu=document.getElementById('bkMoreMenu');if(event.key==='Escape' && menu && !menu.hidden){menu.hidden=true;menu._trigger?.setAttribute('aria-expanded','false');menu._trigger?.focus();}});

    document.querySelectorAll('[data-bk-close]').forEach((button) => {
        button.addEventListener('click', () => closeModal(button.closest('.bk-modal')));
    });

    renderAllBookings();
})();
