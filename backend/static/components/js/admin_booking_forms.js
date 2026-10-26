(function () {
    'use strict';
    const el = (id) => document.getElementById(id);
    const value = (id) => el(id)?.value || '';
    const timeLabel = text => window.CampusHubBookings?.formatTimeRange(text) || text;
    const escape = (text) => String(text ?? '').replace(/[&<>"']/g, (c) => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const peso = (number) => new Intl.NumberFormat('en-PH', {style:'currency', currency:'PHP'}).format(Number(number));
    let selectedFacility = null, clientRows = [], quote = null, revision = 0, optionsRevision = 0, searchRevision = 0, editingReservation = null;
    function closedOperatingDayMessage() {
        const day = value('bkResDate');
        if (!day || !selectedFacility) return '';
        const weekday = new Intl.DateTimeFormat('en-US', {weekday:'long', timeZone:'UTC'})
            .format(new Date(day + 'T12:00:00Z')).toLowerCase();
        return selectedFacility.closed_operating_day_messages?.[weekday] || '';
    }
    async function api(url, data, signal) {
        const response = await fetch(url, {credentials:'same-origin', signal, ...(data ? {method:'POST',
            headers:{'Content-Type':'application/json','X-CSRFToken':document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''}, body:JSON.stringify(data)} : {})});
        const result = await response.json().catch(() => ({}));
        if (!response.ok) {const error=new Error(result.error || 'Unable to load this information. Try again.'); error.available=result.available; throw error;}
        return result;
    }
    function show(id) {
        const modal = el(id);
        if (!modal) return;
        modal._previousFocus = document.activeElement;
        modal.classList.add('is-open'); modal.setAttribute('aria-hidden','false'); document.body.classList.add('modal-open');
        document.documentElement.style.overflow = 'hidden';
        modal.querySelector('.bk-modal-dialog').focus();
    }
    document.addEventListener('keydown', (event) => {
        const modal = document.querySelector('.bk-modal.is-open');
        if (!modal) return;
        if (event.key === 'Escape') {modal.querySelector('[data-bk-close]')?.click(); return;}
        if (event.key !== 'Tab') return;
        const controls = [...modal.querySelectorAll('button,input,select,textarea,a[href]')].filter((node) => !node.disabled && node.getClientRects().length);
        const first = controls[0], last = controls[controls.length - 1];
        if (event.shiftKey && (document.activeElement === first || document.activeElement === modal.querySelector('.bk-modal-dialog'))) {event.preventDefault(); last?.focus();}
        else if (!event.shiftKey && document.activeElement === last) {event.preventDefault(); first?.focus();}
    });
    function disclose(id, shown, required = false) {
        const group = el(id);
        if (!group) return;
        group.hidden = !shown;
        group.querySelectorAll('input,select,textarea').forEach((input) => {input.disabled = !shown; input.required = shown && required;});
    }
    let checkTimer, checkAbort, saving = false;
    function invalidate() {
        revision += 1; quote = null; clearTimeout(checkTimer); checkAbort?.abort();
        if (el('bkSaveReservation')) el('bkSaveReservation').disabled = true;
        if (el('bkCostSummary')) el('bkCostSummary').hidden = true;
        if (!el('bkQuoteResult')) return;
        el('bkQuoteResult').textContent = 'Complete the reservation schedule to check availability automatically.';
        if (!saving) checkTimer = setTimeout(checkAutomatically,300);
    }
    function addressControl() {
        const chosen = ['existing','walkin'].includes(value('bkClientMode'));
        const required = chosen && selectedFacility?.workflow_config?.requires_client_address === true;
        disclose('bkAddressField',required || value('bkClientMode') === 'walkin',required);
        el('bkAddressLabel').textContent = required ? 'Address *' : 'Address';
    }
    function clientMode() {
        const existing = value('bkClientMode') === 'existing';
        const chosen = existing || value('bkClientMode') === 'walkin';
        ++searchRevision; clearTimeout(searchTimer); clientRows = []; el('bkClientOptions').replaceChildren();
        el('bkClientHelp').textContent = 'Select a matching CampusHub user.';
        el('bkClientTypeField').classList.toggle('bk-field-wide',!existing);
        disclose('bkClientFields',chosen);
        el('bkResName').required = chosen; el('bkResContact').required = chosen;
        disclose('bkClientLookup', existing); el('bkClientSearch').required = existing;
        el('bkResName').readOnly = existing;
        el('bkNameLabel').textContent = existing ? 'Full Name' : 'Full Name *';
        el('bkResName').placeholder = existing ? 'Filled after selecting a CampusHub user' : "Enter client's full name";
        ['bkResName','bkClientSelect','bkClientSearch','bkResOrganization','bkResContact','bkResEmail','bkResAddress'].forEach(id=>el(id).value='');
        addressControl(); invalidate();
    }
    el('bkClientMode')?.addEventListener('change', clientMode);
    const clientLabel = row => `${row.name} - ${row.identifier}`;
    function selectClient(row) {
        el('bkClientSelect').value = String(row.id);
        el('bkResName').value = row.name; el('bkResEmail').value = row.email;
        el('bkResContact').value = row.contact_number; el('bkResOrganization').value = row.organization || '';
        el('bkClientHelp').textContent = 'Client selected. Stored details have been filled in.';
        invalidate();
    }
    let searchTimer;
    el('bkClientSearch')?.addEventListener('input', () => {
        const number = ++searchRevision;
        clearTimeout(searchTimer);
        const chosen = clientRows.find(row=>clientLabel(row) === value('bkClientSearch'));
        if (chosen) {selectClient(chosen); return;}
        if (value('bkClientSelect')) ['bkResOrganization','bkResContact','bkResEmail'].forEach(id=>el(id).value='');
        el('bkClientSelect').value = ''; el('bkResName').value = ''; el('bkClientOptions').replaceChildren(); invalidate();
        if (value('bkClientSearch').trim().length < 2) {el('bkClientHelp').textContent='Enter at least two characters to search.'; return;}
        el('bkClientHelp').textContent = 'Searching clients...';
        searchTimer = setTimeout(async () => {
            try {
                const result = await api('/api/bookings/clients/?q=' + encodeURIComponent(value('bkClientSearch')));
                if (number !== searchRevision) return;
                clientRows = result.clients;
                el('bkClientOptions').innerHTML = clientRows.map(row=>`<option value="${escape(clientLabel(row))}"></option>`).join('');
                el('bkClientHelp').textContent = clientRows.length ? 'Select a matching user from the suggestions.' : 'No matching clients. Try another name, ID or email.';
            } catch (error) {if (number === searchRevision) el('bkClientHelp').textContent = error.message;}
        }, 300);
    });
    el('bkOpenReservationBtn')?.addEventListener('click', () => {
        if (editingReservation) {
            el('bkReservationForm').reset(); selectedFacility=null; clientMode();
            ['bkSlotFields','bkStayFields','bkGuestFields','bkDiscountField','bkDiscountReasonField'].forEach(id=>disclose(id,false));
            el('bkFeeFields').replaceChildren(); el('bkFormLabel').textContent='';
            el('bkScheduleHint').hidden=false;el('bkScheduleHint').textContent='Select a facility to load its reservation fields.';
        }
        editingReservation=null; el('bkResFacility').disabled=false;
        el('bkReservationTitle').textContent='Add Reservation'; el('bkSaveReservation').textContent='Save Reservation';
        show('bkReservationModal'); invalidate();
    });
    async function loadFacility() {
        const number = ++optionsRevision;
        selectedFacility = null; invalidate(); disclose('bkSlotFields',false); disclose('bkStayFields',false); disclose('bkGuestFields',false);
        ['bkResDate','bkResStart','bkResEnd','bkCheckIn','bkCheckOut','bkRoom'].forEach(id=>el(id).value='');
        el('bkFeeFields').replaceChildren(); disclose('bkDiscountField',false); disclose('bkDiscountReasonField',false);
        el('bkFormLabel').textContent = '';
        el('bkScheduleHint').hidden = false; el('bkScheduleHint').textContent = 'Select a facility to load its reservation fields.';
        el('bkAttendeesLabel').textContent = 'Number of Participants *'; el('bkAttendees').placeholder = 'Enter number of participants';
        el('bkPurposeLabel').textContent = 'Purpose *'; el('bkResPurpose').placeholder = 'Enter reservation purpose';
        addressControl();
        if (!value('bkResFacility')) return;
        el('bkFormLabel').textContent = 'Loading facility configuration…';
        try {
            const result = await api(`/api/bookings/facilities/${encodeURIComponent(value('bkResFacility'))}/options/`);
            if (number !== optionsRevision) return;
            selectedFacility = result.facility;
            el('bkSharedRate').checked = false; el('bkResStart').readOnly = false; el('bkResEnd').readOnly = false;
            const config = selectedFacility.workflow_config || {}, room = selectedFacility.booking_mode === 'room';
            const forms = {rental:'Facilities and Spaces Rental Booking Slip', accommodation:'Room Accommodation Booking Slip', general:'Custom / General Booking Form'};
            el('bkFormLabel').textContent = `${selectedFacility.booking_form_label || forms[config.booking_form_type] || 'Facility Booking Form'} · ${selectedFacility.price_label}${room && config.check_in_time ? ' · Check-in ' + timeLabel(config.check_in_time) : ''}${room && config.check_out_time ? ' · Check-out ' + timeLabel(config.check_out_time) : ''}`;
            disclose('bkSlotFields', selectedFacility.booking_mode === 'slot',true); disclose('bkStayFields',room,true); disclose('bkGuestFields',room);
            disclose('bkRoomField',room && selectedFacility.rooms.length > 0,true);
            disclose('bkCheckInTimeField',room && !!config.check_in_time); disclose('bkCheckOutTimeField',room && !!config.check_out_time);
            el('bkCheckInTime').value=timeLabel(config.check_in_time || ''); el('bkCheckOutTime').value=timeLabel(config.check_out_time || '');
            el('bkScheduleHint').hidden = ['slot','room'].includes(selectedFacility.booking_mode) && (!room || selectedFacility.rooms.length > 0);
            el('bkScheduleHint').textContent = room ? 'No rooms/units are configured. Contact Facilities Admin before reserving a stay.' : 'This booking mode needs a configured request process.';
            disclose('bkSharedField', room && selectedFacility.price_type === 'person_night' && config.pricing?.partner_rate != null);
            el('bkSharedRate').required = false;
            el('bkAttendeesLabel').textContent = room ? 'Number of Guests *' : 'Number of Participants *';
            el('bkAttendees').placeholder = room ? 'Enter number of guests' : 'Enter number of participants';
            el('bkPurposeLabel').textContent = room ? 'Purpose of Stay *' : 'Purpose *';
            el('bkResPurpose').placeholder = room ? 'Enter purpose of stay' : 'Enter reservation purpose';
            addressControl();
            el('bkRoom').innerHTML = '<option value="">Select configured room/unit</option>' + selectedFacility.rooms.map((item) => `<option value="${escape(item.id)}" ${item.status !== 'available' ? 'disabled' : ''}>${escape(item.name)}${item.capacity ? ' · ' + item.capacity + ' guests' : ''}</option>`).join('');
            const rules = (config.discount_rules || []).map((rule,index) => ({...rule,index})).filter((rule) => rule.active);
            disclose('bkDiscountField',rules.length > 0);
            el('bkDiscount').innerHTML = '<option value="">No discount</option>' + rules.map((rule) => `<option value="${rule.index}">${escape(rule.eligible_client_type.replaceAll('_',' '))} · ${escape(rule.discount_value)}${rule.discount_type === 'percentage' ? '%' : ' PHP'}</option>`).join('');
            el('bkFeeFields').innerHTML = (config.additional_fees || []).map((fee,index) => fee.active && ['item','unit'].includes(fee.unit) ? `<label class="bk-field"><span>${escape(fee.name)} quantity</span><input data-fee-index="${index}" type="number" min="0" step="1" value="0"></label>` : '').join('');
            disclose('bkSlotChoiceField',false); await loadSlots(); invalidate();
        } catch (error) {if (number === optionsRevision) el('bkQuoteResult').textContent = error.message;}
    }
    el('bkResFacility')?.addEventListener('change',loadFacility);
    async function loadSlots() {
        if (!selectedFacility || selectedFacility.booking_mode !== 'slot' || !selectedFacility.slots || !value('bkResDate')) return;
        const id = selectedFacility.id, day = value('bkResDate');
        el('bkResStart').value=''; el('bkResEnd').value=''; invalidate();
        el('bkSlotChoice').disabled=true;
        try {
            const result = await api(`/api/mobile/facilities/${encodeURIComponent(id)}/availability/?date=${encodeURIComponent(day)}${editingReservation ? '&booking_id=' + encodeURIComponent(editingReservation.booking.id) : ''}`);
            if (selectedFacility?.id !== id || value('bkResDate') !== day) return;
            disclose('bkSlotChoiceField',true); el('bkSlotChoice').required = true;
            el('bkSlotChoice').innerHTML = '<option value="">Select time slot</option>' + result.slots.map((slot) => `<option value="${escape(slot.start + '|' + slot.end)}" ${slot.status !== 'available' ? 'disabled' : ''}>${escape(slot.label)} · ${escape(slot.status)}</option>`).join('');
            el('bkResStart').readOnly = true; el('bkResEnd').readOnly = true;
            invalidate();
            if (!result.slots.some(slot=>slot.status==='available')) el('bkQuoteResult').textContent='Unavailable \u2014 ' +
                (closedOperatingDayMessage() || 'no configured time slots are available on this date.');
        } catch (error) {el('bkQuoteResult').textContent = error.message;}
    }
    el('bkResDate')?.addEventListener('change', loadSlots);
    el('bkSlotChoice')?.addEventListener('change', () => {const [start,end] = value('bkSlotChoice').split('|'); el('bkResStart').value = start || ''; el('bkResEnd').value = end || ''; invalidate();});
    function verificationControls() {
        const chosen=!!value('bkDiscount');
        disclose('bkDiscountReasonField',chosen);
        el('bkVerificationMethod').required=chosen;
        disclose('bkVerificationOtherField',chosen && value('bkVerificationMethod')==='Other',true);
    }
    ['bkDiscount','bkVerificationMethod'].forEach(id=>el(id)?.addEventListener('change',verificationControls));
    function reservationData() {
        const discounted=!!value('bkDiscount'),method=discounted?value('bkVerificationMethod'):'', notes=discounted?value('bkVerificationNotes'):'';
        return {type:'reservation', booking_id:editingReservation?.booking.id || '', client_type:value('bkClientMode'), facility_id:value('bkResFacility'), client_id:value('bkClientMode') === 'existing' ? value('bkClientSelect') : '',
            full_name:value('bkResName'), contact_number:value('bkResContact'), email:value('bkResEmail'), organization:value('bkResOrganization'),
            purpose:value('bkResPurpose'), notes:value('bkResNotes'), address:value('bkResAddress'), date:value('bkResDate'), start:value('bkResStart'), end:value('bkResEnd'),
            check_in_date:value('bkCheckIn'), check_out_date:value('bkCheckOut'), room_id:value('bkRoom'), attendees:value('bkAttendees'),
            adults:value('bkAdults'), children:value('bkChildren'), shared_rate:el('bkSharedRate')?.checked === true,
            discount_index:value('bkDiscount'), discount_reason:(method==='Other' ? value('bkVerificationOther') : method) + (notes ? ': ' + notes : ''),
            verification_method:method, verification_other:method==='Other' ? value('bkVerificationOther') : '', verification_notes:notes,
            fee_quantities:Object.fromEntries([...document.querySelectorAll('[data-fee-index]')].map((input) => [input.dataset.feeIndex,input.value]))};
    }
    function scheduleComplete() {
        if (!selectedFacility) return false;
        if (selectedFacility.booking_mode === 'room') return !!(value('bkCheckIn') && value('bkCheckOut') && value('bkRoom'));
        return selectedFacility.booking_mode === 'slot' && !!(value('bkResDate') && value('bkResStart') && value('bkResEnd'));
    }
    function requiredFieldsComplete() {
        return el('bkReservationForm').checkValidity() && (value('bkClientMode') !== 'existing' || !!value('bkClientSelect'));
    }
    function scheduleLabel() {
        const date = key=>new Date(key + 'T00:00:00').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
        if (selectedFacility.booking_mode === 'room') return `${date(value('bkCheckIn'))} - ${date(value('bkCheckOut'))}`;
        const time = text=>new Date('2000-01-01T' + text).toLocaleTimeString('en-US',{hour:'numeric',minute:'2-digit'});
        return `${date(value('bkResDate'))} - ${time(value('bkResStart'))} - ${time(value('bkResEnd'))}`;
    }
    async function checkAutomatically() {
        if (saving || !scheduleComplete()) return;
        const number = revision, complete = requiredFieldsComplete();
        checkAbort = new AbortController();
        el('bkQuoteResult').textContent='Checking availability and pricing...';
        try {
            const result = await api('/api/bookings/preview/',{...reservationData(),availability_only:!complete},checkAbort.signal);
            if (number !== revision || saving) return;
            if (result.available !== true) throw new Error('Unable to confirm availability. Try changing the schedule.');
            el('bkQuoteResult').innerHTML=`<strong>Available</strong><span>${escape(scheduleLabel())}</span>${!complete ? '<span>Complete the client and booking information to calculate the amount due.</span>' : ''}`;
            if (!complete || !result.quote) return;
            quote=result.quote;
            const rows=[['Base Rental',quote.base_amount],['Discount',quote.discount_amount],['Additional Fees',quote.fee_amount],['Rental Total',quote.rental_total],['Damage Deposit',quote.deposit_amount],['Amount Due',quote.total_amount]];
            el('bkCostValues').innerHTML=rows.map(([label,amount])=>`<div><dt>${label}</dt><dd>${peso(amount)}</dd></div>`).join('');
            el('bkCostSummary').hidden=false; el('bkSaveReservation').disabled=false;
        } catch (error) {
            if (number !== revision || error.name==='AbortError') return;
            if (error.available !== true && error.message === closedOperatingDayMessage()) {
                el('bkQuoteResult').textContent='Unavailable \u2014 ' + error.message;
                return;
            }
            el('bkQuoteResult').innerHTML=`<strong>${error.available === true ? 'Available' : 'Unavailable'}</strong><span>${error.available === true ? escape(scheduleLabel()) + '</span><span>Complete pricing / booking information: ' : ''}${escape(error.message)}</span>`;
        }
    }
    ['input','change'].forEach(type=>el('bkReservationForm')?.addEventListener(type,invalidate));
    el('bkReservationForm')?.addEventListener('submit',async (event) => {
        event.preventDefault(); if (!quote || saving || !requiredFieldsComplete()) return;
        const data={...reservationData(),quoted_amount:quote.total_amount};
        saving=true; clearTimeout(checkTimer); checkAbort?.abort(); el('bkSaveReservation').disabled=true;
        el('bkQuoteResult').textContent='Saving reservation...';
        try {
            const result=await api(editingReservation ? `/api/bookings/${encodeURIComponent(editingReservation.booking.id)}/update/` : '/api/bookings/create/',{...data,...(editingReservation?{action:'edit'}:{})});
            const saved=result.event || result.booking;
            document.dispatchEvent(new CustomEvent('campushub:reservation-created',{detail:saved}));
            el('bkReservationModal').querySelector('[data-bk-close]').click();
            el('bkReservationSuccess').hidden=false; el('bkViewSavedBooking').dataset.bookingId=saved.id;
            el('bkReservationSuccess').querySelector('span').textContent=editingReservation?'Reservation updated successfully.':'Reservation created successfully.';
            window.CampusHubBookings.notify(editingReservation?'Reservation updated successfully.':'Reservation created successfully.');
            el('bkViewSavedBooking').focus();
            el('bkReservationForm').reset(); selectedFacility=null; editingReservation=null; el('bkResFacility').disabled=false; ++optionsRevision; ++searchRevision; clearTimeout(searchTimer);
            disclose('bkSlotFields',false); disclose('bkStayFields',false); disclose('bkGuestFields',false); disclose('bkDiscountField',false); disclose('bkDiscountReasonField',false);
            el('bkFeeFields').replaceChildren(); el('bkFormLabel').textContent=''; clientRows=[]; el('bkClientOptions').replaceChildren();
            el('bkScheduleHint').hidden=false; el('bkScheduleHint').textContent='Select a facility to load its reservation fields.';
            clientMode();
        } catch (error) {invalidate(); el('bkQuoteResult').textContent=error.message; el('bkQuoteResult').focus();}
        finally {saving=false;}
    });
    document.addEventListener('campushub:edit-reservation',async event=>{
        editingReservation=event.detail; const {booking,details}=editingReservation;
        el('bkReservationForm').reset();
        el('bkResFacility').value=booking.facility_id;
        el('bkReservationTitle').textContent='Edit Reservation'; el('bkSaveReservation').textContent='Save Changes';
        show('bkReservationModal'); await loadFacility();
        if (!selectedFacility) return;
        el('bkResFacility').disabled=true;
        el('bkClientMode').value=details.client_id?'existing':'walkin'; clientMode();
        const fields={bkResName:details.full_name || booking.reserved_by,bkClientSelect:details.client_id,bkResContact:details.contact_number,
            bkResOrganization:details.organization,bkResEmail:details.email,bkResAddress:details.address,bkResNotes:details.notes,
            bkResPurpose:details.purpose || booking.purpose,bkAttendees:details.attendees,bkAdults:details.adults,bkChildren:details.children,
            bkResDate:booking.date,bkCheckIn:booking.date,bkCheckOut:booking.end_date,bkRoom:details.room_id,bkDiscount:details.discount_index,
            bkVerificationMethod:details.verification_method,bkVerificationOther:details.verification_other,bkVerificationNotes:details.verification_notes};
        Object.entries(fields).forEach(([id, val])=>el(id).value=val ?? '');
        if(details.client_id){el('bkClientSearch').value=details.full_name || booking.reserved_by;el('bkClientHelp').textContent='Existing client retained. Search to select a different account.';}
        await loadSlots(); el('bkResStart').value=booking.start; el('bkResEnd').value=booking.end;
        if(!el('bkSlotChoiceField').hidden) el('bkSlotChoice').value=booking.start+'|'+booking.end;
        el('bkSharedRate').checked=details.shared_rate===true;
        document.querySelectorAll('[data-fee-index]').forEach(input=>input.value=details.fee_quantities?.[input.dataset.feeIndex] || 0);
        verificationControls(); invalidate();
    });
    el('bkViewSavedBooking')?.addEventListener('click',()=>document.dispatchEvent(new CustomEvent('campushub:booking-details',{detail:value('bkViewSavedBooking') || el('bkViewSavedBooking').dataset.bookingId})));
    function scheduleControls() {
        disclose('bkOtherTypeField',value('bkUploadType') === 'other',true);
        disclose('bkBlockStartField',!el('bkAllDay').checked,true); disclose('bkBlockEndField',!el('bkAllDay').checked,true);
        el('bkWeekdays').hidden = value('bkRepeat') !== 'weekly';
    }
    function resetSchedule() {
        el('bkUploadForm').reset();
        el('bkBlockId').value = ''; el('bkUploadFacility').disabled = false;
        el('bkSavedAttachment').textContent = ''; el('bkScheduleResult').textContent = '';
        el('bkScheduleSummary').replaceChildren(); el('bkScheduleSummary').hidden = true;
        el('bkUploadForm').querySelector('[type=submit]').disabled = false;
        scheduleControls();
    }
    function refreshSchedule(message) {
        el('bkUploadModal').querySelector('[data-bk-close]').click();
        document.dispatchEvent(new CustomEvent('campushub:calendar-refresh'));
        window.CampusHubBookings.notify(message);
    }
    ['bkUploadType','bkAllDay','bkRepeat'].forEach(id => el(id)?.addEventListener('change',scheduleControls));
    el('bkOpenUploadBtn')?.addEventListener('click', () => {resetSchedule(); show('bkUploadModal');});
    function editBlock(row) {
        const config = row.schedule || {};
        el('bkBlockId').value = row.id; el('bkUploadFacility').value = row.facility_id; el('bkUploadFacility').disabled = true;
        el('bkUploadType').value = row.type; el('bkUploadDate').value = row.first_date || row.date; el('bkUploadUntil').value = config.until || row.date;
        el('bkUploadStart').value = row.start; el('bkUploadEnd').value = row.end;
        el('bkUploadDesc').value = config.title || row.purpose; el('bkOtherType').value = config.other_type || '';
        el('bkRepeat').value = config.repeat || 'none'; el('bkAllDay').checked = !!config.all_day;
        el('bkWeekdays').querySelectorAll('input').forEach(input => input.checked = (config.weekdays || []).includes(Number(input.value)));
        el('bkSavedAttachment').textContent = row.attachment_name ? 'Saved attachment: ' + row.attachment_name : '';
        const summary = el('bkScheduleSummary'); summary.hidden = false;
        summary.innerHTML = `<h4 class="bk-form-section-title">Editing Schedule</h4><div class="bk-block-row"><div><strong>${escape(row.facility)}</strong><span>${escape(config.title || row.purpose)}</span><span>${escape(row.first_date || row.date)}${config.until && config.until !== (row.first_date || row.date) ? ' / '+escape(config.until) : ''} &middot; ${escape(row.status_label || row.status)}</span></div>${row.status === 'approved' || row.status === 'pending' ? '<button type="button" class="bk-btn-ghost" id="bkCancelSchedule">Cancel Schedule</button>' : ''}</div>`;
        el('bkCancelSchedule')?.addEventListener('click', async event => {
            if (!confirm('Cancel this facility schedule? Its history will be kept.')) return;
            const button = event.currentTarget; button.disabled = true;
            try {
                await api(`/api/facility-schedules/${encodeURIComponent(row.id)}/update/`, {action:'cancel'});
                refreshSchedule('Facility schedule cancelled successfully.');
            } catch (error) {el('bkScheduleResult').textContent=error.message; button.disabled=false;}
        });
        el('bkUploadImage').value = ''; scheduleControls(); el('bkUploadDesc').focus();
    }
    document.addEventListener('campushub:calendar-schedule', event => {
        if (!el('bkUploadForm')) return;
        resetSchedule(); show('bkUploadModal');
        const {row, date, facility} = event.detail;
        if (row) editBlock(row);
        else {el('bkUploadDate').value=date; el('bkUploadUntil').value=date;
            el('bkUploadFacility').value=facility || ''; el('bkUploadFacility').focus();}
    });
    el('bkUploadForm')?.addEventListener('submit',async (event) => {
        event.preventDefault(); const button = event.target.querySelector('[type=submit]'); button.disabled = true;
        el('bkScheduleResult').textContent = 'Checking conflicts and saving…';
        try {
            const data = {facility_id:value('bkUploadFacility'),type:value('bkUploadType'),date:value('bkUploadDate'),until:value('bkUploadUntil'),
                start:value('bkUploadStart'),end:value('bkUploadEnd'),purpose:value('bkUploadDesc'),other_type:value('bkOtherType'),
                repeat:value('bkRepeat'),all_day:el('bkAllDay').checked,
                weekdays:[...el('bkWeekdays').querySelectorAll('input:checked')].map((input) => Number(input.value))};
            const file = el('bkUploadImage').files[0];
            if (file) {
                if (file.size > 1024 * 1024) throw new Error('Attachment must be no larger than 1 MB.');
                const encoded = await new Promise((resolve,reject) => {const reader = new FileReader(); reader.onload = () => resolve(reader.result.split(',')[1]); reader.onerror = reject; reader.readAsDataURL(file);});
                data.attachment = {name:file.name,type:file.type,data:encoded};
            }
            await api(value('bkBlockId') ? `/api/facility-schedules/${encodeURIComponent(value('bkBlockId'))}/update/` : '/api/bookings/create/',data);
            refreshSchedule('Facility schedule saved successfully.');
        } catch (error) {el('bkScheduleResult').textContent = error.message || 'Unable to save this schedule. Try again.';}
        finally {button.disabled = false;}
    });
    if (el('bkClientMode')) clientMode();
    if (el('bkUploadForm')) scheduleControls();
    // Dashboard links reuse the existing, permission-rendered form triggers.
    const dashboardAction = new URLSearchParams(location.search).get('action');
    if (dashboardAction === 'add-reservation') el('bkOpenReservationBtn')?.click();
    else if (dashboardAction === 'upload-schedule') el('bkOpenUploadBtn')?.click();
})();
