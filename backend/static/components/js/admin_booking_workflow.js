/* Full-page booking tabs and small action dialogs reuse existing endpoints/data. */
(function () {
    'use strict';
    const el=id=>document.getElementById(id);
    const page=el('bkBookingDetailPage');
    if(!page) return;
    const actionModal=el('bkBookingActionModal');
    const escape=value=>String(value??'').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const money=value=>new Intl.NumberFormat('en-PH',{style:'currency',currency:'PHP'}).format(Number(value || 0));
    const date=(value,options={})=>value ? new Date(value).toLocaleString('en-US',{timeZone:'Asia/Manila',...options}) : 'Not recorded';
    const localDateTime=(value=new Date())=>{
        const parts=Object.fromEntries(new Intl.DateTimeFormat('en-CA',{timeZone:'Asia/Manila',year:'numeric',month:'2-digit',
            day:'2-digit',hour:'2-digit',minute:'2-digit',hourCycle:'h23'}).formatToParts(new Date(value)).map(p=>[p.type,p.value]));
        return `${parts.year}-${parts.month}-${parts.day}T${parts.hour}:${parts.minute}`;
    };
    const titles={approve:'Approve Booking',reject:'Reject Booking',cancel:'Cancel Booking',edit:'Edit Booking',
        complete:'Complete Booking',payment:'Record Payment',job_order:'Edit Job Order',
        inspection:'Record Inspection',assign_personnel:'Assign Personnel In-Charge',document:'Add Document',
        archive:'Archive Booking',restore:'Restore Booking'};
    let current=null, loadRevision=0, busy=false, openBookingId=null, reservationReturnTab='Overview';
    async function api(path, data) {
        const response=await fetch(path,{credentials:'same-origin',...(data ? {method:'POST',headers:{'Content-Type':'application/json',
            'X-CSRFToken':document.querySelector('[name=csrfmiddlewaretoken]')?.value || ''},body:JSON.stringify(data)} : {})});
        const result=await response.json();
        if (!response.ok) throw new Error(result.error || 'Unable to load this booking.');
        return result;
    }
    function closeEditor() {
        if(actionModal.classList.contains('is-open')) window.CampusHubBookings.closeModal(actionModal);
        el('bkActionEditor').replaceChildren(); el('bkTransactionEditor').replaceChildren();
        el('bkTransactionEditor').hidden=true;
    }
    function tab(name) {
        if(!el('bkTab'+name)) name='Overview';
        closeEditor();
        document.querySelectorAll('[data-bk-tab]').forEach(button=>{const active=button.dataset.bkTab===name;
            button.setAttribute('aria-selected',String(active));button.tabIndex=active?0:-1;el('bkPanel'+button.dataset.bkTab).hidden=!active;});
        if(name==='JobOrder') window.CampusHubJobOrder.load(el('bkPanelJobOrder').querySelector('[data-job-preview]'));
    }
    document.querySelectorAll('[data-bk-tab]').forEach(button=>{
        button.addEventListener('click',()=>{if(!busy) tab(button.dataset.bkTab);});
        button.addEventListener('keydown',event=>{
            if(busy) return;
            const buttons=[...document.querySelectorAll('[data-bk-tab]')].filter(n=>!n.hidden);
            const index=buttons.indexOf(button);
            const next=event.key==='ArrowRight' ? buttons[(index+1)%buttons.length] : event.key==='ArrowLeft' ? buttons[(index+buttons.length-1)%buttons.length] : event.key==='Home'?buttons[0]:event.key==='End'?buttons.at(-1):null;
            if(next){event.preventDefault();tab(next.dataset.bkTab);next.focus();}
        });
    });
    function dl(values,className='bk-details-grid') {
        return `<dl class="${className}">${values.map(([k,v])=>`<div><dt>${escape(k)}</dt><dd>${escape(v ?? 'Not recorded')}</dd></div>`).join('')}</dl>`;
    }
    function actionButton(action,label,kind='') {
        return current.booking.actions.includes(action) ? `<button type="button" class="bk-btn-ghost" data-transaction-action="${action}" data-kind="${kind}">${escape(label || titles[action])}</button>` : '';
    }
    function documentLinks(doc) {
        return `<a class="bk-btn-ghost" href="${escape(doc.url)}" target="_blank" rel="noopener">View / Print ${escape(doc.title)}</a>${doc.pdf_url ? ` <a class="bk-btn-ghost" href="${escape(doc.pdf_url)}">Export PDF</a>` : ''}`;
    }
    const paymentStatusLabel=value=>({paid:'Paid',unpaid:'Unpaid',failed:'Failed'})[value] || 'Not recorded';
    const paymentBadge=value=>`<span class="bk-payment-status${value==='paid'?' is-paid':value==='unpaid'?' is-unpaid':''}">${escape(paymentStatusLabel(value))}</span>`;
    const paymentDate=value=>date(value,{year:'numeric',month:'short',day:'numeric',hour:'numeric',minute:'2-digit',hour12:true});
    function paymentValue(value,fallback='Not recorded') {
        const saved=String(value ?? '').trim();
        return !saved || ['null','nonetype','-'].includes(saved.toLowerCase())?fallback:saved;
    }
    function paymentRecordTable(fields) {
        return `<div class="bk-payment-record"><table class="bk-payment-record-table" aria-labelledby="bkPaymentRecordTitle"><thead><tr><th scope="col">Payment Detail</th><th scope="col">Information</th></tr></thead><tbody>${fields.map(([label,value])=>`<tr><th scope="row">${escape(label)}</th><td>${escape(value)}</td></tr>`).join('')}</tbody></table></div>`;
    }
    function receiptLinks(file) {
        const name=file.name || file.title;
        return `<div class="bk-payment-receipt"><p>${escape(name)}</p><div class="bk-transaction-actions">${file.view_url?`<a class="bk-btn-ghost" href="${escape(file.view_url)}" target="_blank" rel="noopener" aria-label="View receipt ${escape(name)}">View Receipt</a>`:''}<a class="bk-btn-ghost" href="${escape(file.url)}" download aria-label="Download receipt ${escape(name)}">Download Receipt</a></div></div>`;
    }
    function renderPayment(paymentId) {
        const {booking:b,payments,documents}=current;
        const selected=payments.find(p=>p.id===paymentId) || payments[0];
        const history=payments.length>1;
        const fields=selected?[
            ['Official Receipt No.',paymentValue(selected.official_receipt_no)],
            ['Payment Method',paymentValue(selected.method)],['Date Paid',paymentDate(selected.paid_at)],
            ['Recorded / Verified By',paymentValue(selected.by?.name)],['Notes',paymentValue(selected.notes,'None')]]:[];
        const receipts=[...(selected?.receipt_attachment?[selected.receipt_attachment]:[]),
            ...documents.filter(doc=>doc.section==='Payment' && !payments.some(p=>p.receipt_attachment?.url===doc.url))];
        const recordContext=selected && (history || selected.status!=='paid')?
            `<div class="bk-payment-record-context"><span>Payment Status ${paymentBadge(selected.status)}</span><span>Recorded Amount <strong>${escape(money(selected.amount))}</strong></span></div>`:'';
        const action=actionButton('payment');
        el('bkPanelPayment').innerHTML=`<section class="bk-payment-section" aria-labelledby="bkPaymentSummaryTitle"><h2 id="bkPaymentSummaryTitle">Payment Summary</h2><dl class="bk-details-grid bk-payment-summary"><div><dt>Original Amount Due</dt><dd>${escape(money(b.total_amount))}</dd></div><div><dt>Amount Paid</dt><dd>${escape(money(b.paid_amount))}</dd></div><div><dt>Remaining Balance</dt><dd>${escape(money(b.amount_due))}</dd></div><div><dt>Payment Status</dt><dd>${paymentBadge(b.payment_status)}</dd></div></dl></section>`+
            `<section class="bk-payment-section" id="bkPaymentRecordDetails" aria-labelledby="bkPaymentRecordTitle"><h2 id="bkPaymentRecordTitle">Payment Record Details</h2>${recordContext}${selected?paymentRecordTable(fields):'<p class="bk-payment-empty">No payment recorded.</p>'}</section>`+
            (history?`<section class="bk-payment-section" aria-labelledby="bkPaymentHistoryTitle"><h2 id="bkPaymentHistoryTitle">Payment History</h2><div class="bk-activity-scroll" role="region" aria-label="Payment history" tabindex="0"><table class="bk-activity-table bk-payment-history"><thead><tr><th scope="col">Date Paid</th><th scope="col">Official Receipt No.</th><th scope="col">Payment Method</th><th scope="col">Amount Paid</th><th scope="col">Recorded / Verified By</th><th scope="col">Payment Status</th></tr></thead><tbody>${payments.map(p=>`<tr class="${p.id===selected.id?'is-selected':''}"><td>${escape(paymentDate(p.paid_at))}</td><td><button type="button" data-payment-record="${escape(p.id)}" aria-controls="bkPaymentRecordDetails" aria-pressed="${p.id===selected.id}" aria-label="View payment record ${escape(p.official_receipt_no || p.id)}">${escape(paymentValue(p.official_receipt_no))}</button></td><td>${escape(paymentValue(p.method))}</td><td>${escape(money(p.amount))}</td><td>${escape(paymentValue(p.by?.name))}</td><td>${paymentBadge(p.status)}</td></tr>`).join('')}</tbody></table></div></section>`:'')+
            `<section class="bk-payment-section" aria-labelledby="bkPaymentReceiptTitle"><h2 id="bkPaymentReceiptTitle">Receipt Attachment</h2>${receipts.length?receipts.map(receiptLinks).join(''):'<p class="bk-payment-empty">No receipt attachment uploaded.</p>'}</section>`+
            (action?`<section class="bk-payment-section" aria-labelledby="bkPaymentActionsTitle"><h2 id="bkPaymentActionsTitle">Payment Actions</h2><div class="bk-transaction-actions">${action.replace('bk-btn-ghost','bk-btn-primary')}</div></section>`:'');
    }
    function scheduleLabel(booking) {
        const day=value=>value?date(value+'T00:00:00+08:00',{year:'numeric',month:'short',day:'numeric'}):'Not recorded';
        return day(booking.date)+(booking.end_date?' \u2013 '+day(booking.end_date):'');
    }
    function reservationTime(booking,details) {
        const start=booking.start || details.check_in_time, end=booking.end || details.check_out_time;
        return start && end?window.CampusHubBookings.formatTimeRange(start,end):'Not recorded';
    }
    function completionChecklist(checks) {
        return `<ul class="bk-completion-checks">${checks.map(check=>`<li class="${check.satisfied?'is-satisfied':check.blocking===false?'is-warning':'is-outstanding'}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true">${check.satisfied?'<path d="m5 12 4 4L19 6"/>':check.blocking===false?'<path d="m12 3 10 18H2L12 3zM12 9v5m0 3v1"/>':'<circle cx="12" cy="12" r="8"/>'}</svg><span>${escape(check.satisfied?check.label:check.pending_label || check.message)}</span></li>`).join('')}</ul>`;
    }
    function renderOverview() {
        const {booking:b,details:d,completion}=current, quote=b.quote || {};
        const section=(id,title,content)=>`<section class="bk-overview-section" aria-labelledby="${id}"><h2 id="${id}">${title}</h2>${content}</section>`;
        const info=[['Booking ID',b.id],['Requester',b.reserved_by],['Facility',b.facility]];
        if(d.room_id) info.push(['Room / Unit',b.room]);
        info.push(['Booking Source',b.source],['Date / Stay',scheduleLabel(b)],['Time',reservationTime(b,d)],
            ['Participants / Guests',d.attendees ?? quote.guests ?? 'Not recorded']);
        info.push(['Record Status',b.is_archived?'Archived':'Current']);
        if(quote.nights) info.push(['Nights',quote.nights]);
        info.push(['Purpose',d.purpose || b.purpose || 'Not recorded']);
        const pricing=[['Base Rental','base_amount'],['Discount','discount_amount'],['Additional Fees','fee_amount'],
            ['Damage Deposit','deposit_amount'],['Rental Total','rental_total']].map(([label,key])=>[label,
                quote[key]==null?'Not recorded':money(key==='discount_amount' && Number(quote[key])>0?-Number(quote[key]):quote[key])]);
        // Rental subtotal excludes the deposit in the existing backend quote.
        if(quote.rental_total==null || Number(quote.rental_total)!==Number(b.total_amount)) pricing.push(['Total Amount Due',money(b.total_amount)]);
        pricing.push(['Amount Paid',money(b.paid_amount)],['Remaining Balance',money(b.amount_due)]);
        const approval=[['Submitted',paymentDate(b.created_at)]];
        if(b.approved_at || b.approved_by) approval.push(['Approved By',b.approved_by || 'Not recorded'],['Approved At',paymentDate(b.approved_at)]);
        else if(b.status!=='rejected') approval.push(['Approval',b.status==='pending'?'Awaiting approval':'No approval recorded.']);
        if(b.status==='rejected' && d.reject) approval.push(['Rejected By',d.reject.by?.name || 'Not recorded'],
            ['Rejected At',paymentDate(d.reject.at)],['Reason',d.reject.reason || 'Not recorded']);
        const savedNotes=paymentValue(d.notes,'');
        const notes=!savedNotes || savedNotes.toLowerCase()==='not recorded'?'No notes provided.':savedNotes;
        let completionContent='';
        if(b.status==='completed') {
            completionContent=`<p>Booking completed${d.completion?.at?' on '+escape(paymentDate(d.completion.at)):'.'}</p>`+
                (d.completion?.by?.name?`<p>Completed by ${escape(d.completion.by.name)}</p>`:'');
        } else if(['cancelled','rejected'].includes(b.status)) {
            completionContent=`<p>This booking is ${escape(b.status)}.</p>`;
        } else {
            const more=current.booking.actions.includes('cancel')?`<details class="bk-overview-more"><summary>More Actions <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" aria-hidden="true"><path d="m6 9 6 6 6-6"/></svg></summary><div>${actionButton('cancel').replace('bk-btn-ghost','bk-btn-ghost bk-cancel-booking')}</div></details>`:'';
            const ordinary=['approve','reject','edit'].map(key=>actionButton(key)).join('');
            const complete=completion?.can_manage?`<button type="button" class="bk-btn-primary" data-transaction-action="complete"${b.actions.includes('complete')?'':' disabled aria-describedby="bkCompletionReason"'}>Complete Booking</button>`:'';
            completionContent=(completion?completionChecklist(completion.checks):'')+
                (completion?`<p class="bk-completion-state" role="status">${completion.eligible?'Ready for completion':completion.remaining_count!=null?`${completion.remaining_count} requirement${completion.remaining_count===1?'':'s'} remaining`:''}</p>`:'')+
                (completion && !completion.eligible?`<p id="bkCompletionReason">${escape(completion.reason)}</p>`:'')+
                (more || ordinary || complete?`<div class="bk-overview-actions"><div class="bk-transaction-actions">${more}${ordinary}</div>${complete}</div>`:'');
        }
        const cancellation=b.status==='cancelled'?section('bkOverviewCancellationTitle','Cancellation Information',
            dl([['Reason',paymentValue(d.cancel?.reason)],['Cancelled By',paymentValue(d.cancel?.by?.name)],
                ['Cancelled At',paymentDate(d.cancel?.at)]])+`<p>Cancelled bookings are read-only.</p><div class="bk-transaction-actions">${actionButton(b.is_archived?'restore':'archive')}</div>`):'';
        el('bkPanelOverview').innerHTML=section('bkOverviewInformationTitle','Booking Information',dl(info,'bk-details-grid bk-overview-info'))+cancellation+
            section('bkOverviewPricingTitle','Pricing Summary',(b.pricing_method_label?`<p class="bk-overview-method">Pricing Method: <strong>${escape(b.pricing_method_label)}</strong></p>`:'')+dl(pricing,'bk-overview-pricing'))+
            section('bkOverviewApprovalTitle','Approval Information',dl(approval,'bk-details-grid'))+
            section('bkOverviewNotesTitle','Notes',`<p class="bk-overview-notes">${escape(notes)}</p>`)+
            (b.status==='cancelled'?'':section('bkOverviewCompletionTitle','Completion Readiness',completionContent));
    }
    function renderInspections() {
        const {details:d,rules,documents}=current;
        const kinds=['pre','post'];
        const assigned=d.assigned_personnel;
        const assignment=`<div class="bk-inspection-assignment"><div><span>Personnel In-Charge</span><strong>${escape(assigned?.name || 'Not assigned')}</strong></div>${actionButton('assign_personnel',assigned?'Change Personnel':'Assign Personnel')}</div>`;
        el('bkPanelInspection').innerHTML=assignment+kinds.map(kind=>{
            const record=d.inspections?.[kind], post=kind==='post';
            const title=`${post?'Post':'Pre'}-Use Inspection`;
            const allowed=current.inspection_actions?.includes(kind);
            const recordLabel=`Record ${post?'Post':'Pre'}-Use Inspection`;
            const action=allowed?actionButton('inspection',record?'Edit Inspection':recordLabel,kind):
                !record && current.booking.actions.includes('assign_personnel')?`<button type="button" class="bk-btn-ghost" disabled title="Not available for the current booking stage">${recordLabel}</button>`:'';
            const missedPre=!post && current.completion?.checks.some(check=>check.key==='pre_inspection' && !check.blocking && !check.satisfied);
            const availability=current.booking.status!=='approved'?'Inspection recording is unavailable for this booking status.':
                !rules[`requires_${kind}_use_inspection`] && !(post && current.completion?.requires_issue_confirmation)?'Not required for this booking.':
                !current.booking.actions.includes('assign_personnel')?'Only authorized facilities personnel can record this inspection.':
                allowed?'Ready to record.':post?'Available after scheduled facility use ends.':'Unavailable for the current booking stage.';
            if(!record) return `<section class="bk-inspection-section"><header class="bk-inspection-heading"><h2>${title}</h2>${action}</header>${current.booking.status==='cancelled'?'<p>No inspection recorded.</p>':`<p>Status: <strong>Not Recorded</strong></p><p>${missedPre?'Pre-use inspection was not recorded.':availability}</p>`}</section>`;
            const fields=[['Status','Recorded'],['Inspector',record.inspector?.name || 'Not recorded'],
                ['Inspection Date & Time',paymentDate(record.inspected_at)],[`Facility Condition ${post?'After':'Before'} Use`,current.inspection_conditions?.[kind]?.label || record.condition || 'Not recorded']];
            if(post) fields.push(['Damage Found',current.inspection_damage===true?'Yes':current.inspection_damage===false?'No':'Not recorded']);
            else fields.push(['Existing Damage / Issues',paymentValue(record.existing_damage,'None')]);
            if(post && current.inspection_damage===true) fields.push(['Damage Description',paymentValue(record.damage_found)]);
            fields.push(['Remarks',paymentValue(record.remarks,'None')]);
            const extra=[['Recorded By',record.recorded_by?.name || 'Not recorded'],['Created At',paymentDate(record.created_at)],['Updated At',paymentDate(record.at)]];
            for(const [label,key] of [['Previously recorded cleanliness','cleanliness'],['Previously recorded missing items','missing_items'],['Previously recorded overtime','overtime']]) {
                if(record[key]) extra.push([label,record[key]]);
            }
            if(post && (record.deposit_decision || current.completion?.requires_issue_confirmation)) extra.push(
                ['Damage / Deposit Decision',record.deposit_decision || 'Not recorded'],['Resolution Confirmed',record.issues_resolved_confirmed===true?'Yes':'Not confirmed']);
            const links=documents.filter(doc=>doc.section==='Inspection' && doc.kind===kind).map(doc=>`<div class="bk-transaction-record bk-transaction-actions">${documentLinks(doc)}</div>`).join('');
            return `<section class="bk-inspection-section"><header class="bk-inspection-heading"><h2>${title}</h2>${action}</header>${dl(fields,'bk-details-grid bk-inspection-summary')}<details class="bk-inspection-details"><summary>View Details</summary>${dl(extra)}${links}</details></section>`;
        }).join('');
    }
    function render() {
        window.CampusHubJobOrder.dispose();
        const {booking:b,details:d,documents,rules,activity}=current;
        el('bkTransactionMessage').textContent='';
        el('bkBookingDetailsId').textContent=b.id;
        el('bkDetailBookingStatus').textContent=b.status_label;
        el('bkDetailBookingStatus').classList.toggle('bk-cancelled-status',b.status==='cancelled');
        el('bkDetailPaymentStatus').textContent=b.payment_status==='paid'?'Paid':'Unpaid';
        renderOverview();
        const files=(section,kind)=>documents.filter(doc=>doc.section===section && (!kind || doc.kind===kind));
        const links=docs=>docs.map(doc=>`<div class="bk-transaction-record">${documentLinks(doc)}</div>`).join('');
        const formDocs=files('BookingForm');
        const officialDoc=formDocs.find(doc=>!doc.url.includes('/attachments/'));
        el('bkPanelBookingForm').innerHTML=`<h2>Booking Slip</h2><p>${escape(b.booking_form_label || b.quote?.form_label || 'Booking Slip')}</p><p>Slip Status: Generated<br>Generated from Booking: ${escape(b.id)}</p>`+
            (officialDoc?`<div class="bk-form-toolbar">${actionButton('edit','Edit Booking Slip')}<button class="bk-slip-print" type="button" data-bk-print-slip${current.booking_form_html?'':' disabled'}><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M7 8V3h10v5M7 17H4V9h16v8h-3M7 14h10v7H7z"/><path d="M17 11h.01"/></svg>Print</button><a href="${escape(officialDoc.pdf_url)}"><svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="1.8" stroke-linecap="round" stroke-linejoin="round" aria-hidden="true"><path d="M12 3v12m-4-4 4 4 4-4M5 17v4h14v-4"/></svg>Export PDF</a></div>`:'')+
            (current.booking_form_html || '<p>Booking slip preview unavailable. Open the printable slip or refresh this page.</p>');
        renderPayment();
        const jobDoc=files('JobOrder').find(doc=>doc.pdf_url);
        el('bkPanelJobOrder').innerHTML=current.job_order_document?
            `<header class="beu-job-panel-heading"><div><h2>Job Order</h2><p>USTP Oroquieta Business Enterprise Unit<br>JOB ORDER Request</p><p>Job Order Status: <strong>${escape(current.job_order_status)}</strong></p><p>Generated from Booking: <strong>${escape(b.id)}</strong></p></div><div class="beu-job-panel-actions">${actionButton('job_order','Edit Job Order')}<button type="button" class="bk-btn-primary" data-bk-print-job data-job-print disabled>Print</button>${jobDoc?window.CampusHubJobOrder.exportMenu(jobDoc.pdf_url,current.job_order_document.docx_url):''}</div></header><div class="beu-job-preview" data-job-preview data-pdf-url="${escape(current.job_order_document.pdf_url)}"></div>`:
            '<h2>Job Order</h2><p>Job Order is available after booking approval.</p>';
        window.CampusHubJobOrder.prepare(el('bkPanelJobOrder').querySelector('[data-job-preview]'));
        renderInspections();
        const labels={booking_archived:'Booking Archived',booking_restored:'Booking Restored',booking_created:'Reservation Created',booking_auto_approved:'Booking Approved (automatic)',booking_approved:'Booking Approved',
            facility_payment_recorded:'Payment Recorded',booking_reserved:'Booking Reserved / Confirmed',job_order_created:'Job Order Created',job_order_updated:'Job Order Updated',
            pre_use_inspection_completed:'Pre-Use Inspection Recorded',post_use_inspection_completed:'Post-Use Inspection Recorded',pre_use_inspection_updated:'Pre-Use Inspection Updated',post_use_inspection_updated:'Post-Use Inspection Updated',booking_personnel_assigned:'Personnel Assigned',booking_damage_recorded:'Damage Issue Recorded',booking_resolution_completed:'Damage / Deposit Resolution Completed',booking_completed:'Booking Completed',booking_cancelled:'Booking Cancelled',booking_rejected:'Booking Rejected'};
        el('bkPanelActivity').innerHTML=activity.length?`<div class="bk-activity-scroll" role="region" aria-label="Booking activity" tabindex="0"><table class="bk-activity-table"><thead><tr><th>Action</th><th>Actor</th><th>Role</th><th>Date / Time</th><th>Result</th></tr></thead><tbody>${activity.map(a=>`<tr><td>${escape(labels[a.code] || a.action)}</td><td>${escape(a.by)}</td><td>${escape(a.role || 'User')}</td><td>${escape(date(a.at))}</td><td>${escape(a.result)}</td></tr>`).join('')}</tbody></table></div>`:'<p>No recorded activity for this booking.</p>';
    }
    function destination(action) {
        return ({payment_details:'Payment',job_order_details:'JobOrder',booking_slip:'BookingForm',documents:'BookingForm',activity:'Activity'})[action];
    }
    async function load(id, nextAction) {
        const revision=++loadRevision; current=null;openBookingId=id;
        el('bkTransactionMessage').textContent='Loading booking information...';page.setAttribute('aria-busy','true');
        document.querySelectorAll('[data-bk-tab]').forEach(button=>button.disabled=true);
        try {
            const response=await api(`/api/bookings/${encodeURIComponent(id)}/`);
            if(revision!==loadRevision) return;
            current=response;render();
            tab(destination(nextAction) || nextAction || 'Overview');
            return true;
        } catch(error) {
            if(revision===loadRevision){el('bkTransactionMessage').textContent=error.message;
                const retry=document.createElement('button');retry.type='button';retry.className='bk-btn-ghost';retry.textContent='Retry';retry.addEventListener('click',()=>load(id,nextAction));el('bkTransactionMessage').append(' ',retry);}
            return false;
        } finally {if(revision===loadRevision){page.removeAttribute('aria-busy');document.querySelectorAll('[data-bk-tab]').forEach(button=>button.disabled=!current);}}
    }
    function field(label,name,value='',options={}) {
        const tag=options.textarea?'textarea':'input';
        const attrs=`name="${name}" ${options.required?'required':''} ${options.readonly?'readonly':''} ${options.type==='number'?`min="${options.min ?? 0}" step="0.01"`:''}`;
        return `<label class="bk-field ${options.wide?'bk-field-wide':''}"><span>${escape(label)}${options.required?' *':''}</span>${tag==='textarea'?`<textarea ${attrs} maxlength="${options.maxLength || 2000}" rows="2">${escape(value)}</textarea>`:`<input ${attrs} type="${options.type || 'text'}" ${options.type==='file'?'accept=".pdf,.png,.jpg,.jpeg,.webp"':`value="${escape(value)}" maxlength="2000"`}>`}</label>`;
    }
    function editor(action,kind='pre') {
        if(!current || busy || !Object.hasOwn(titles,action) || !current.booking.actions.includes(action)) return;
        if(action==='edit'){
            reservationReturnTab=el('bkTabBookingForm').getAttribute('aria-selected')==='true'?'BookingForm':'Overview';
            document.dispatchEvent(new CustomEvent('campushub:edit-reservation',{detail:current}));return;
        }
        tab(({payment:'Payment',job_order:'JobOrder',inspection:'Inspection',document:'BookingForm'})[action] || 'Overview');
        const {booking:b,details:d}=current;
        let content='';
        if(action==='approve') content=`<p class="bk-field-wide">Confirm ${escape(titles[action].toLowerCase())} for ${escape(b.id)}. The server will validate its current state.</p>`;
        if(['archive','restore'].includes(action)) content=`<p class="bk-field-wide">${action==='archive'?'Move this booking to archived records?':'Restore this booking to current records?'} Its booking status will remain Cancelled. Payments, documents and history will be preserved.</p>`;
        if(action==='complete') content=`<div class="bk-field-wide">${dl([['Booking',b.id],['Facility',b.facility],['Schedule',scheduleLabel(b)],['Time / Stay',reservationTime(b,d)]])}${completionChecklist(current.completion?.checks || [])}</div>`+
            (current.completion?.requires_issue_confirmation?'<label class="bk-field-wide bk-completion-confirm"><input type="checkbox" name="issues_resolved_confirmed" required><span>I confirm that damage, deposit and additional charge issues are resolved.</span></label>':'')+
            '<p class="bk-field-wide">Completing this booking will change the booking status to Completed.</p>';
        if(['reject','cancel'].includes(action)) content=field('Reason','reason','',{required:true,textarea:true,wide:true});
        if(action==='cancel' && Number(b.paid_amount)>0) content+='<p class="bk-field-wide bk-form-hint">Recorded payments will be kept. Handle any refund separately.</p>';
        if(action==='payment') {
            const quote=d.quote || b.quote || {};
            const breakdown=[['Base Rental / Accommodation','base_amount'],['Discount','discount_amount'],['Additional Fees','fee_amount'],
                ['Rental / Accommodation Total','rental_total'],['Damage Deposit','deposit_amount']].filter(([,key])=>quote[key]!=null).map(([label,key])=>[label,money(quote[key])]);
            content='<p class="bk-field-wide bk-form-hint">Record the Official Receipt issued by the Cashiering / authorized collecting office. CampusHub does not issue Official Receipts. Date Paid uses Philippine time (Asia/Manila).</p>'+
                (breakdown.length?`<div class="bk-field-wide">${dl(breakdown)}</div>`:'')+
                field('Payment Method','payment_method','Cash',{readonly:true,required:true})+field('Original Amount Due','original_amount_due',b.total_amount,{readonly:true})+
                field('Amount Due','amount_due',b.amount_due,{readonly:true})+
                field('Amount Paid','amount_paid',b.amount_due,{type:'number',min:0.01,required:true})+field('Official Receipt No.','official_receipt_no','',{required:true})+
                field('Date Paid','paid_at',localDateTime(),{type:'datetime-local',required:true})+
                field('Recorded / Verified By','payment_recorder',current.recording_user?.name || 'Not recorded',{readonly:true})+
                field('Notes','notes','',{textarea:true})+field('Receipt Attachment (PDF/image, up to 1 MB)','attachment','',{type:'file',wide:true});
        }
        if(action==='job_order') {
            const job=d.job_order || {}, config=current.job_order_form;
            const selected=Array.isArray(job.service_types)?job.service_types:config.service_choices.includes(job.service_requested)?[job.service_requested]:[];
            const other=Array.isArray(job.service_types)?job.service_other || '':selected.length?'':job.service_requested || '';
            const jobLocal=value=>value?(/(?:Z|[+-]\d{2}:\d{2})$/.test(value)?localDateTime(value):value.slice(0,16)):'';
            content=field('Job Order Request No.','number',job.number || '')+
                field('Date','job_date',job.date || localDateTime().slice(0,10),{readonly:true})+
                '<p class="bk-field-wide bk-form-hint">Complete the draft fields. Client information and the reservation are filled from the saved booking.</p>'+
                `<label class="bk-field"><span>Gender Preference</span><select name="gender_preference"><option value="">Select gender preference (optional)</option>${config.gender_choices.map(value=>`<option ${job.gender_preference===value?'selected':''}>${escape(value)}</option>`).join('')}${job.gender_preference&&!config.gender_choices.includes(job.gender_preference)?`<option selected>${escape(job.gender_preference)}</option>`:''}</select></label>`+
                `<fieldset class="beu-service-options"><legend>Job or Service Requested *</legend><div>${config.service_choices.map(value=>`<label><input type="checkbox" name="service_types" value="${escape(value)}" ${selected.includes(value)?'checked':''}>${escape(value)}</label>`).join('')}</div></fieldset>`+
                field('Other service (if applicable)','service_other',other,{wide:true})+
                field('Turnaround Time','turnaround_time',job.turnaround_time || '',{wide:true})+
                field('Details / Specifics','specifics',job.specifics || '',{textarea:true,wide:true,maxLength:12000})+
                field('Item (s)','items',job.items || '',{textarea:true,wide:true,maxLength:12000})+
                field('Date and Time Product / Specimen Received at USTP ORO BEU (Philippine time)','received_at',jobLocal(job.received_at),{type:'datetime-local'})+
                field('Date and Time Job or Service Required (Philippine time)','required_at',jobLocal(job.required_at),{type:'datetime-local'});
        }
        if(action==='inspection') {
            const record=d.inspections?.[kind] || {};
            if(!current.inspection_actions?.includes(kind)) {el('bkTransactionMessage').textContent='This inspection is not available for the current booking stage.';return;}
            const defaultInspector=current.inspection_defaults?.[kind];
            const condition=current.inspection_conditions?.[kind] || {value:'',other:''};
            content=`<input type="hidden" name="kind" value="${escape(kind)}"><label class="bk-field"><span>Inspector *</span><select name="inspector_id" required><option value="">Select authorized personnel</option>${current.staff.map(s=>`<option value="${s.id}" ${String(defaultInspector)===String(s.id)?'selected':''}>${escape(s.name)}</option>`).join('')}</select></label>`+
                field('Inspection Date & Time (Philippine time)','inspected_at',localDateTime(record.inspected_at || new Date()),{type:'datetime-local',required:true})+
                `<label class="bk-field bk-field-wide"><span>Facility Condition ${kind==='pre'?'Before':'After'} Use *</span><select name="condition" required><option value="">Select facility condition</option>${current.inspection_condition_choices.map(choice=>`<option value="${escape(choice)}" ${condition.value===choice?'selected':''}>${escape(choice)}</option>`).join('')}</select></label>`+
                `<div class="bk-field-wide" data-inspection-other${condition.value==='Other'?'':' hidden'}>${field('Specify Condition','condition_other',condition.other,{required:condition.value==='Other',wide:true})}</div>`;
            if(kind==='pre') content+=field('Existing Damage / Issues','existing_damage',record.existing_damage || '',{textarea:true,wide:true});
            else content+=`<fieldset class="bk-inspection-damage-choice bk-field-wide"><legend>Damage Found? *</legend>${[['false','No'],['true','Yes']].map(([value,label])=>`<label><input type="radio" name="has_damage" value="${value}" required ${current.inspection_damage===true && value==='true' || current.inspection_damage===false && value==='false'?'checked':''}>${label}</label>`).join('')}</fieldset><div class="bk-field-wide" data-inspection-damage${current.inspection_damage===true?'':' hidden'}>${field('Damage Description','damage_found',record.damage_found || '',{textarea:true,required:current.inspection_damage===true,wide:true})}</div>`;
            content+=field('Remarks','remarks',record.remarks || '',{textarea:true,wide:true});
            if(kind==='post') content+='<div class="bk-field-wide bk-inspection-resolution" data-inspection-resolution>'+field('Damage / Deposit Decision (if applicable)','deposit_decision',record.deposit_decision || '',{wide:true})+
                `<label class="bk-field-wide bk-completion-confirm"><input type="checkbox" name="issues_resolved_confirmed" ${record.issues_resolved_confirmed===true?'checked':''}><span>I confirm that any recorded damage, deposit and additional charge issues are resolved.</span></label>`+
                '<p class="bk-field-wide bk-form-hint">Confirm resolution only after the applicable issues are settled. This does not record a cash refund.</p></div>';
            content+=field('Supporting Photo / Report (up to 1 MB)','attachment','',{type:'file',wide:true});
        }
        if(action==='assign_personnel') content=`<label class="bk-field bk-field-wide"><span>Personnel In-Charge *</span><select name="personnel_id" required><option value="">Select authorized personnel</option>${current.staff.map(person=>`<option value="${person.id}" ${String(d.assigned_personnel?.id)===String(person.id)?'selected':''}>${escape(person.name)}</option>`).join('')}</select></label>`;
        if(action==='document') content=field('Document Title','title','',{required:true})+field('Supporting Document (PDF/image, up to 1 MB)','attachment','',{type:'file',required:true});
        const small=action!=='document';
        const host=el(small?'bkActionEditor':'bkTransactionEditor');host.hidden=false;
        host.dataset.action=action;
        const submitLabel=({archive:'Archive Booking',restore:'Restore Booking',payment:'Confirm Payment',complete:'Complete Booking',inspection:'Save Inspection'})[action] || 'Save';
        host.innerHTML=`${small?'':`<h3>${escape(titles[action])}</h3>`}<form id="bkTransactionForm" class="bk-admin-form-grid">${content}<p class="bk-field-wide" id="bkTransactionError" role="alert"></p><div class="bk-field-wide bk-transaction-actions"><button type="button" class="bk-btn-ghost" id="bkCancelTransaction">Cancel</button><button type="submit" class="bk-btn-primary">${escape(submitLabel)}</button></div></form>`;
        if(action==='inspection') {
            const updateOther=()=>{
                const other=host.querySelector('[name=condition]').value==='Other';
                host.querySelector('[data-inspection-other]').hidden=!other;
                const input=host.querySelector('[name=condition_other]');input.disabled=!other;input.required=other;
                input.previousElementSibling.textContent=other?'Specify Condition *':'Specify Condition';
            };
            host.querySelector('[name=condition]').addEventListener('change',updateOther);updateOther();
        }
        if(action==='inspection' && kind==='post') {
            const updateDamage=()=>{
                const damage=host.querySelector('[name=has_damage]:checked')?.value==='true';
                host.querySelector('[data-inspection-damage]').hidden=!damage;
                host.querySelector('[name=damage_found]').required=damage;
                host.querySelector('[name=damage_found]').disabled=!damage;
                host.querySelector('[name=damage_found]').previousElementSibling.textContent=damage?'Damage Description *':'Damage Description';
                const needsResolution=damage || current.completion?.requires_issue_confirmation;
                const resolution=host.querySelector('[data-inspection-resolution]');
                resolution.hidden=!needsResolution;
                resolution.querySelectorAll('input').forEach(input=>input.disabled=!needsResolution);
            };
            host.querySelectorAll('[name=has_damage]').forEach(input=>input.addEventListener('change',updateDamage));updateDamage();
        }
        el('bkCancelTransaction').addEventListener('click',closeEditor);
        if(small){actionModal.dataset.action=action;el('bkBookingActionTitle').textContent=action==='inspection'?`${d.inspections?.[kind]?'Edit':'Record'} ${kind==='pre'?'Pre':'Post'}-Use Inspection`:titles[action];window.CampusHubBookings.openModal(actionModal);}
        else host.scrollIntoView({block:'nearest'});
        host.querySelector('input:not([type=hidden]),textarea,select,button')?.focus();
        el('bkTransactionForm').addEventListener('submit',event=>submit(event,action));
    }
    function readFile(file) {
        if(file.size>1024*1024) return Promise.reject(new Error('Choose a PDF/image up to 1 MB.'));
        return new Promise((resolve,reject)=>{const reader=new FileReader();reader.onload=()=>resolve({name:file.name,type:file.type,data:reader.result.split(',')[1]});reader.onerror=()=>reject(new Error('Unable to read the attachment.'));reader.readAsDataURL(file);});
    }
    async function submit(event,action) {
        event.preventDefault();if(busy || !current) return;
        const form=event.target, bookingId=current.booking.id;
        if(!form.checkValidity()) {form.reportValidity();return;}
        busy=true; form.querySelectorAll('button').forEach(n=>n.disabled=true);
        try {
            const data={action};
            for(const [key,val] of new FormData(form).entries()) if(!(val instanceof File)) data[key]=val;
            if(action==='job_order') data.service_types=new FormData(form).getAll('service_types');
            if(action==='inspection' && data.kind==='post') data.has_damage=form.querySelector('[name=has_damage]:checked')?.value==='true';
            if(action==='inspection') {
                const original=current.details.inspections?.[data.kind]?.inspected_at;
                if(original && localDateTime(original)===data.inspected_at) data.inspected_at=original;
            }
            if(action==='complete' || action==='inspection') data.issues_resolved_confirmed=form.querySelector('[name=issues_resolved_confirmed]')?.checked || false;
            const file=form.querySelector('[name=attachment]')?.files[0];if(file) data.attachment=await readFile(file);
            const result=await api(`/api/bookings/${encodeURIComponent(bookingId)}/update/`,data);
            document.dispatchEvent(new CustomEvent('campushub:reservation-created',{detail:result.booking}));
            const messages={archive:'Booking archived successfully.',restore:'Booking restored successfully.',approve:'Booking approved successfully.',reject:'Booking rejected successfully.',cancel:'Booking cancelled successfully.',
                complete:'Booking completed successfully.',payment:'Payment recorded successfully.',inspection:'Inspection saved successfully.',assign_personnel:'Personnel assignment saved successfully.',document:'Document added successfully.',job_order:'Job Order saved successfully.'};
            if(result.changed===false) messages[action]='No changes to save.';
            window.CampusHubBookings.notify(messages[action] || 'Booking updated successfully.');
            if(openBookingId===bookingId){closeEditor();
                const refreshed=await load(bookingId,action==='payment'?'payment_details':action==='job_order'?'job_order_details':['inspection','assign_personnel'].includes(action)?'Inspection':action==='document'?'BookingForm':'Overview');
                if(refreshed) {
                    el('bkTransactionMessage').textContent=messages[action] || 'Booking updated successfully.';
                    if(action==='job_order') el('bkPanelJobOrder').querySelector('[data-transaction-action=job_order]')?.focus();
                    if(['archive','restore'].includes(action)) el('bkPanelOverview').querySelector(`[data-transaction-action=${action==='archive'?'restore':'archive'}]`)?.focus();
                    if(action==='complete'){const heading=el('bkOverviewCompletionTitle');heading.tabIndex=-1;heading.focus();}
                    if(action==='inspection') el('bkPanelInspection').querySelector(`[data-transaction-action=inspection][data-kind=${form.querySelector('[name=kind]').value}]`)?.focus();
                    if(action==='assign_personnel') el('bkPanelInspection').querySelector('[data-transaction-action=assign_personnel]')?.focus();
                }}
        } catch(error) {(el('bkTransactionError') || el('bkTransactionMessage')).textContent=error.message;}
        finally {busy=false;form.querySelectorAll('button').forEach(n=>n.disabled=false);}
    }
    page.addEventListener('click',event=>{
        if(event.target.closest('.bk-overview-more [data-transaction-action]')) {
            const menu=event.target.closest('details');menu.open=false;menu.querySelector('summary').focus();
        }
        const paymentRecord=event.target.closest('[data-payment-record]');
        if(paymentRecord && !busy) {
            const id=paymentRecord.dataset.paymentRecord;renderPayment(id);
            [...el('bkPanelPayment').querySelectorAll('[data-payment-record]')].find(button=>button.dataset.paymentRecord===id)?.focus();return;
        }
        if(event.target.closest('[data-bk-print-slip]')){if(!busy && current?.booking_form_html) window.print();return;}
        if(event.target.closest('[data-bk-print-job]')){if(!busy) window.CampusHubJobOrder.print(el('bkPanelJobOrder').querySelector('[data-job-preview]'));return;}
        const button=event.target.closest('[data-transaction-action]');if(button) editor(button.dataset.transactionAction,button.dataset.kind);
    });
    actionModal.addEventListener('keydown',event=>{
        if(!actionModal.classList.contains('is-open') || !['job_order','complete','cancel','inspection','assign_personnel','archive','restore'].includes(el('bkActionEditor').dataset.action)) return;
        if(event.key==='Escape' && !busy){event.preventDefault();closeEditor();return;}
        if(event.key!=='Tab') return;
        const controls=[...actionModal.querySelectorAll('button,input,select,textarea,a[href]')]
            .filter(control=>!control.disabled && control.offsetParent!==null);
        const first=controls[0], last=controls.at(-1);
        if(event.shiftKey && document.activeElement===first){event.preventDefault();last?.focus();}
        else if(!event.shiftKey && document.activeElement===last){event.preventDefault();first?.focus();}
    });
    document.addEventListener('click',event=>{
        document.querySelectorAll('.bk-overview-more[open]').forEach(menu=>{if(!menu.contains(event.target)) menu.open=false;});
    });
    page.addEventListener('keydown',event=>{
        const menu=event.target.closest('.bk-overview-more[open]');
        if(event.key==='Escape' && menu){event.preventDefault();menu.open=false;menu.querySelector('summary').focus();}
    });
    document.addEventListener('campushub:reservation-created',async event=>{
        if(!busy && event.detail?.id===page.dataset.bookingId) {
            const target=reservationReturnTab;reservationReturnTab='Overview';
            if(await load(event.detail.id,target)) {
                if(target==='BookingForm') el('bkPanelBookingForm').querySelector('[data-transaction-action=edit]')?.focus();
            }
        }
    });
    try {
        current=JSON.parse(el('bkBookingDetailData').textContent);openBookingId=current.booking.id;render();
        const params=new URLSearchParams(location.search);tab(params.get('tab') || 'Overview');
        const action=params.get('action');
        if(action){if(current.booking.actions.includes(action)) editor(action,params.get('kind'));else el('bkTransactionMessage').textContent='This action is not permitted for the current booking state.';}
    } catch(error) {el('bkTransactionMessage').textContent='Unable to load booking details.';load(page.dataset.bookingId);}
})();
