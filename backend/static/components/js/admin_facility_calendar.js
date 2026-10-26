/* Read-only calendar over the same Django bookings and schedule blocks. */
(function () {
    'use strict';
    const el = id => document.getElementById(id), root = el('bkFacilityCalendar');
    if (!root) return;
    const escape = value => String(value ?? '').replace(/[&<>"']/g, c => ({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const labels = {reservation:'Reservation', class:'Class / Academic Schedule', maintenance:'Maintenance',
        official:'Official Campus Use', hold:'Administrative Hold', other:'Other', blocked:'Administrative Hold', assessment:'Other'};
    let data = JSON.parse(el('bkCalendarData').textContent), revision = 0, selected = null;
    let year = Number(data.start.slice(0,4)), month = Number(data.start.slice(5,7))-1;
    const canEdit = root.dataset.canEdit === 'true';
    const dateKey = (y,m,d) => `${y}-${String(m+1).padStart(2,'0')}-${String(d).padStart(2,'0')}`;
    const dateLabel = value => new Date(value+'T12:00:00').toLocaleDateString('en-US',{month:'short',day:'numeric',year:'numeric'});
    const typeLabel = row => row.type === 'reservation' && row.status === 'pending' ? 'Pending Reservation' : labels[row.type] || 'Other';
    const timeLabel = row => {
        if (row.all_day) return 'All Day';
        // Reuse the Bookings display helper; API and stored clocks remain HH:MM.
        const range = window.CampusHubBookings.formatTimeRange(row.start, row.end);
        return row.end_date ? `${dateLabel(row.first_date)} – ${dateLabel(row.end_date)}${range ? ' · '+range : ''}` :
            range || 'Time not recorded';
    };
    const eventClass = row => row.type === 'reservation' && row.status === 'pending' ? 'pending' : row.type;
    const findEvent = key => [...data.events,...data.upcoming].find(row => row.key === key);
    function openDetails(rows) {
        const modal = el('bkCalendarDetails');
        if (!modal.classList.contains('is-open')) modal._previousFocus = document.activeElement;
        selected = rows.length === 1 ? rows[0] : null;
        el('bkCalendarDetailsTitle').textContent = selected ? 'Event Details' : dateLabel(rows[0].date);
        if (!selected) el('bkCalendarDetailsBody').innerHTML = rows.map(row => eventButton(row)).join('');
        else {
            const row = selected, block = row.type !== 'reservation';
            const config = row.schedule || {};
            const recurrence = config.repeat === 'weekly' ? 'Weekly · '+(config.weekdays || []).map(day=>['Mon','Tue','Wed','Thu','Fri','Sat','Sun'][day]).join(', ')+
                ' · Until '+dateLabel(config.until) : 'Does not repeat';
            const fields = [['Event Type',typeLabel(row)],['Facility',row.facility],['Date',dateLabel(row.date)],['Time / Stay',timeLabel(row)]];
            if (block) fields.push(['Title / Description',config.title || row.purpose],['Effective From',dateLabel(row.first_date)],
                ['Recurrence',recurrence],['Status',row.status_label]);
            else fields.push(['Booking ID',row.id],['Requester',row.reserved_by || 'Not recorded'],
                ['Booking Status',row.status_label],['Payment Status',row.payment_status === 'paid' ? 'Paid' : 'Unpaid']);
            if (row.room) fields.push(['Room / Unit',row.room]);
            el('bkCalendarDetailsBody').innerHTML = `<dl class="bk-details-grid">${fields.map(([name,value])=>`<div><dt>${escape(name)}</dt><dd>${escape(value)}</dd></div>`).join('')}</dl>`+
                (row.attachment_url ? `<p><a href="${escape(row.attachment_url)}" target="_blank" rel="noopener">Supporting Attachment: ${escape(row.attachment_name)}</a></p>` : '')+
                `<div class="bk-calendar-detail-actions">${block ? (canEdit ? '<button type="button" class="bk-btn-primary" id="bkCalendarEditSchedule">View / Edit Schedule</button>' : '') :
                    `<a class="bk-btn-primary" href="/admin-bookings/${encodeURIComponent(row.id)}/">View Booking Details</a>`}</div>`;
        }
        modal.classList.add('is-open'); modal.setAttribute('aria-hidden','false');
        document.body.classList.add('modal-open'); document.documentElement.style.overflow='hidden';
        modal.querySelector('.bk-modal-dialog').focus();
    }
    function eventButton(row) {
        return `<button type="button" class="bk-event bk-event-${eventClass(row)}" data-calendar-event="${escape(row.key)}" title="${escape(typeLabel(row)+' · '+row.facility+' · '+timeLabel(row))}">
            <strong>${escape(typeLabel(row))}</strong><span>${escape(row.facility)}</span>${row.room ? `<span>${escape(row.room)}</span>` : ''}
            <span>${escape(timeLabel(row))}</span><span>${escape(row.status_label)}</span></button>`;
    }
    function render() {
        el('bkMonthLabel').textContent = new Date(year,month,1).toLocaleDateString('en-US',{month:'long',year:'numeric'});
        const grid = el('bkCalendarGrid'); grid.querySelectorAll('.bk-day').forEach(node=>node.remove());
        const firstDay = new Date(year,month,1).getDay(), days = new Date(year,month+1,0).getDate();
        const count = Math.ceil((firstDay+days)/7)*7;
        const byDate = new Map();
        data.events.forEach(row=>{if(!byDate.has(row.date)) byDate.set(row.date,[]); byDate.get(row.date).push(row);});
        for (let index=0;index<count;index++) {
            const offset=index-firstDay+1, actual = new Date(year,month,offset), key=dateKey(actual.getFullYear(),actual.getMonth(),actual.getDate());
            const muted=offset<1 || offset>days, rows=byDate.get(key) || [], cell=document.createElement('div');
            cell.className='bk-day'+(muted?' is-muted':'')+(key===data.today?' is-today':''); cell.dataset.date=key;
            cell.innerHTML=`<span class="bk-day-num">${actual.getDate()}</span>`+(muted?'':rows.slice(0,2).map(eventButton).join(''))+
                (!muted && rows.length>2 ? `<button type="button" class="bk-event-more" data-calendar-day="${key}">+${rows.length-2} more</button>` : '')+
                (!muted && !rows.length && canEdit ? `<button type="button" class="bk-day-add" data-calendar-add="${key}" aria-label="Add facility schedule for ${dateLabel(key)}">+</button>` : '');
            grid.append(cell);
        }
        const upcoming = data.upcoming, card=document.querySelector('.bk-upcoming-card');
        card.classList.toggle('is-filled',upcoming.length>0); card.classList.toggle('is-empty',!upcoming.length);
        el('bkUpcomingList').innerHTML = upcoming.length ? upcoming.map(row=>`<li class="bk-upcoming-item"><button type="button" class="bk-calendar-upcoming" data-calendar-event="${escape(row.key)}">
            <span class="bk-upcoming-badge is-${eventClass(row)}">${escape(typeLabel(row))}</span><strong>${escape(row.facility)}${row.room?' · '+escape(row.room):''}</strong>
            <span>${escape(dateLabel(row.date))}</span><span>${escape(timeLabel(row))}</span><span>${escape(row.status_label)}</span></button></li>`).join('') :
            '<li class="bk-upcoming-empty">No upcoming calendar events.</li>';
    }
    async function load() {
        const current=++revision, parameters=new URLSearchParams({start:dateKey(year,month,1),end:dateKey(year,month,new Date(year,month+1,0).getDate()),
            facility:el('bkCalendarFacility').value,type:el('bkCalendarType').value});
        root.setAttribute('aria-busy','true'); el('bkUpcomingList').setAttribute('aria-busy','true');
        el('bkCalendarMessage').textContent='Loading calendar…'; el('bkCalendarRetry').hidden=true;
        // Remove previous results so changed filters cannot leave misleading events visible.
        el('bkCalendarGrid').querySelectorAll('.bk-day').forEach(node=>node.remove()); el('bkUpcomingList').replaceChildren();
        try {
            const response=await fetch('/api/facility-calendar/?'+parameters,{credentials:'same-origin'}), result=await response.json();
            if (!response.ok || !Array.isArray(result.events) || !Array.isArray(result.upcoming)) throw Error(result.error || 'Unable to load calendar events.');
            if (current!==revision) return;
            data=result; render(); el('bkCalendarMessage').textContent='';
        } catch (error) {
            if (current!==revision) return;
            el('bkCalendarMessage').textContent=error.message || 'Unable to load calendar events.'; el('bkCalendarRetry').hidden=false;
            el('bkUpcomingList').innerHTML='<li class="bk-upcoming-empty">Unable to load upcoming calendar events.</li>';
        } finally {if(current===revision){root.setAttribute('aria-busy','false');el('bkUpcomingList').setAttribute('aria-busy','false');}}
    }
    el('bkPrevMonth').addEventListener('click',()=>{const date=new Date(year,month-1,1);year=date.getFullYear();month=date.getMonth();load();});
    el('bkNextMonth').addEventListener('click',()=>{const date=new Date(year,month+1,1);year=date.getFullYear();month=date.getMonth();load();});
    el('bkToday').addEventListener('click',()=>{year=Number(data.today.slice(0,4));month=Number(data.today.slice(5,7))-1;load();});
    ['bkCalendarFacility','bkCalendarType'].forEach(id=>el(id).addEventListener('change',load));
    el('bkCalendarRetry').addEventListener('click',load);
    document.addEventListener('campushub:calendar-refresh',load);
    document.addEventListener('click',event=>{
        const button=event.target.closest('[data-calendar-event],[data-calendar-day],[data-calendar-add],#bkCalendarEditSchedule');
        if (!button || root.getAttribute('aria-busy')==='true') return;
        if (button.dataset.calendarEvent) {const row=findEvent(button.dataset.calendarEvent);if(row)openDetails([row]);}
        else if (button.dataset.calendarDay) openDetails(data.events.filter(row=>row.date===button.dataset.calendarDay));
        else if (canEdit) {
            if(button.id==='bkCalendarEditSchedule') el('bkCalendarDetails').querySelector('[data-bk-close]').click();
            document.dispatchEvent(new CustomEvent('campushub:calendar-schedule',{detail:{row:button.id==='bkCalendarEditSchedule'?selected:null,
                date:button.dataset.calendarAdd, facility:el('bkCalendarFacility').value}}));
        }
    });
    const requestedFacility = new URLSearchParams(location.search).get('facility');
    const facilitySelect = el('bkCalendarFacility');
    if (requestedFacility && Array.from(facilitySelect.options).some(option => option.value === requestedFacility)) {
        facilitySelect.value = requestedFacility;
        load();
    }
    render();
})();
