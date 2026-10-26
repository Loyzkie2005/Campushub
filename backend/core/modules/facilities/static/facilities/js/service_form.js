/* Service-only disclosure and payloads; images and list actions reuse the catalog. */
(() => {
    'use strict';
    const el = id => document.getElementById(id), value = id => el(id)?.value.trim() || '';
    const escape = input => String(input ?? '').replace(/[&<>"']/g,c=>({'&':'&amp;','<':'&lt;','>':'&gt;','"':'&quot;',"'":'&#39;'}[c]));
    const days = ['monday','tuesday','wednesday','thursday','friday','saturday','sunday'];
    class ServiceFormControls {
        constructor(root, choices) {
            this.root=root; this.choices=choices;
            el('serviceWeeklyHours').innerHTML=days.map(day=>`<div class="facility-hours-row" data-service-day="${day}"><label class="facility-check"><input type="checkbox" data-service-open> ${day[0].toUpperCase()+day.slice(1)}</label><div class="facility-hours-times" data-service-times hidden></div><span class="facility-hours-closed" data-service-day-status>Closed</span></div>`).join('');
            this.root.querySelectorAll('[data-service-day]').forEach(row=>{
                const day=row.dataset.serviceDay, name=day[0].toUpperCase()+day.slice(1);
                for(const [key,caption] of [['start','Opening Time'],['end','Closing Time']]){
                    const label=document.createElement('label');label.className='facility-hours-time-label';
                    const text=document.createElement('span');text.textContent=caption;
                    const select=window.CampusHubOperatingSchedule.timeSelect(`${name} ${caption.toLowerCase()}`);
                    select.setAttribute(`data-service-${key}`,'');label.append(text,select);
                    row.querySelector('[data-service-times]').append(label);
                }
            });
            el('serviceAddAnalysis').addEventListener('click',()=>this.addAnalysis());
            el('serviceAnalysisRows').addEventListener('click',event=>event.target.closest('[data-remove-analysis]')?.closest('.service-analysis-row').remove());
            el('serviceAddAssessmentDate').addEventListener('click',()=>this.addAssessmentDate());
            el('serviceAssessmentDates').addEventListener('click',event=>event.target.closest('[data-remove-date]')?.closest('.service-assessment-date').remove());
            el('serviceLeaseSpaces').addEventListener('change',event=>{if(event.target.matches('[data-space-field=pricing_method]'))this.sync();});
            el('facilityType').addEventListener('change',()=>{
                if(!this.requestChosen)el('serviceRequestType').value={food_analysis:'service',training_kitchen:'assessment',lease_space:'lease'}[value('facilityType')] || '';
                if(!this.outputChosen)el('serviceOutputType').value={food_analysis:'analysis_certificate',training_kitchen:'assessment_result',lease_space:'lease_contract'}[value('facilityType')] || '';
                el('serviceExistingPricing').hidden=true; this.sync();
            });
            el('serviceRequestType').addEventListener('change',()=>this.requestChosen=!!value('serviceRequestType'));
            el('serviceOutputType').addEventListener('change',()=>this.outputChosen=!!value('serviceOutputType'));
            ['facilityPriceType','servicePaymentTiming','serviceOutputType','serviceAvailabilityEnabled','serviceSchedulingMethod'].forEach(id=>el(id).addEventListener('change',()=>this.sync()));
            root.querySelectorAll('[data-service-lease],[data-service-open]').forEach(input=>input.addEventListener('change',()=>this.sync()));
            root.addEventListener('input',event=>event.target.setCustomValidity?.(''));
            root.addEventListener('change',event=>event.target.setCustomValidity?.(''));
            this.reset();
        }
        disclose(name, shown, required=false) {
            const group=this.root.querySelector(`[data-service-disclose="${name}"]`);
            group.hidden=!shown;
            group.querySelectorAll('input,select,textarea,button').forEach(field=>{
                field.disabled=!shown; field.required=shown && required && field.type!=='checkbox' && field.tagName!=='BUTTON';
            });
        }
        sync() {
            const category=value('facilityType'), previous=value('facilityPriceType'), allowed=this.choices.allowed_pricing[category] || [];
            el('facilityPriceType').replaceChildren(new Option('Select pricing method',''),...allowed.map(key=>new Option(this.choices.pricing[key],key)));
            el('facilityPriceType').value=allowed.includes(previous)?previous:'';
            const method=value('facilityPriceType');
            this.disclose('category',category==='other',true);
            this.disclose('timing',value('servicePaymentTiming')==='custom',true);
            this.disclose('output',value('serviceOutputType')==='custom',true);
            this.disclose('customPricing',method==='custom',true);
            this.disclose('rate',!!method && !['analysis','term'].includes(method),method!=='custom');
            this.disclose('termRates',method==='term',true);
            el('serviceRateLabel').textContent={candidate:'Assessment Fee / Candidate *',fixed_monthly:'Fixed Monthly Rental *',monthly:'Monthly Rate *',sqm:'Rate Per sqm / Month *',machine_month:'Rate Per Machine / Month *',fixed:'Fixed Rate *',custom:'Rate / Amount (Optional)'}[method] || 'Rate *';
            this.disclose('analyses',method==='analysis');
            if(method==='analysis') this.root.querySelectorAll('[data-analysis-name],[data-analysis-fee]').forEach(input=>input.required=true);
            this.root.querySelectorAll('[data-service-category]').forEach(group=>{
                const shown=group.dataset.serviceCategory===category;group.hidden=!shown;
                group.querySelectorAll('input,select,textarea').forEach(field=>field.disabled=!shown);
            });
            el('serviceSchedulingMethod').required=category==='training_kitchen';
            if(category!=='training_kitchen')el('serviceSchedulingMethod').value='';
            this.disclose('leaseOther',category==='lease_space' && !!this.root.querySelector('[data-service-lease="other"]:checked'),true);
            el('serviceCategoryHint').hidden=category!=='' && category!=='other';
            el('serviceCategoryHint').textContent=category==='other'?'Configure request, pricing and availability above.':'Select a category to configure this service.';
            el('serviceSpecificHeading').textContent='6. '+({food_analysis:'Food Analysis Configuration',training_kitchen:'BPP NC II Configuration',lease_space:'Lease Configuration'}[category] || 'Service-Specific Configuration');
            const scheduling=value('serviceSchedulingMethod');
            this.disclose('assessmentDates',category==='training_kitchen' && scheduling==='specific_date');
            el('serviceSchedulingHelp').textContent={specific_date:'Configure assessment dates below. These are service schedules, not facility reservations.',admin_assigned:'The client submits a request first. Staff assign the actual schedule later.',none:'Clients submit a request without choosing an appointment or calendar slot.'}[scheduling] || 'Select how assessment schedules are assigned.';
            this.syncLeaseSpaces(category);
            const noAppointment=category==='training_kitchen' && scheduling==='none';
            el('serviceAvailabilityEnabled').disabled=false;
            el('serviceAvailabilityHelp').textContent=noAppointment?'No appointment is required. Optional office hours do not create booking slots.':{food_analysis:'Optional sample submission and processing hours.',training_kitchen:'Optional normal office hours. Client schedules follow the scheduling method above.',lease_space:'Optional application receiving hours, not hourly lease reservations.'}[category] || 'Optional normal operating hours.';
            const enabled=el('serviceAvailabilityEnabled').checked;el('serviceWeeklyHours').hidden=!enabled;
            this.root.querySelectorAll('[data-service-day]').forEach(row=>{
                const checked=row.querySelector('[data-service-open]').checked;
                row.querySelector('[data-service-day-status]').hidden=checked;
                row.querySelector('[data-service-times]').hidden=!checked;
                row.querySelector('[data-service-open]').disabled=!enabled;
                row.querySelectorAll('[data-service-start],[data-service-end]').forEach(field=>{field.disabled=!enabled || !checked;field.required=enabled && checked;});
            });
        }
        addAnalysis(item={}) {
            const row=document.createElement('div');row.className='service-analysis-row';
            row.innerHTML=`<label>Analysis / Test Name *<input class="form-control" data-analysis-name maxlength="150" value="${escape(item.name)}" placeholder="Enter analysis or test name"></label><label>Description<input class="form-control" data-analysis-description maxlength="500" value="${escape(item.description)}" placeholder="Describe this analysis or test"></label><label>Rate / Fee *<input class="form-control" data-analysis-fee type="number" min="0" max="99999999.99" step="0.01" value="${escape(item.fee)}" placeholder="Enter fee"></label><label class="service-check"><input type="checkbox" data-analysis-active ${item.active===false?'':'checked'}>Active</label><button type="button" class="facility-cancel-btn" data-remove-analysis aria-label="Remove analysis/test row">Remove</button>`;
            el('serviceAnalysisRows').append(row);this.sync();
            const label=document.createElement('label');label.textContent='Charging Basis *';
            const select=document.createElement('select');select.className='form-select';select.dataset.analysisBasis='';
            Object.entries(this.choices.charging_bases).forEach(([key,title])=>select.add(new Option(title,key)));
            select.value=item.charging_basis || (Object.keys(item).length?'analysis':'sample');select.required=true;
            select.disabled=value('facilityPriceType')!=='analysis';
            label.append(select);row.insertBefore(label,row.querySelector('.service-check'));
        }
        addAssessmentDate(item={}) {
            const row=document.createElement('div');row.className='service-assessment-date';
            row.innerHTML=`<label>Assessment Date *<input class="form-control" data-assessment-date type="date" required value="${escape(item.date)}"></label>`;
            for(const key of ['start','end']){
                const label=document.createElement('label');label.textContent=key==='start'?'Start Time (Optional)':'End Time (Optional)';
                const select=window.CampusHubOperatingSchedule.timeSelect('Assessment '+key+' time');select.dataset.assessmentTime=key;
                window.CampusHubOperatingSchedule.setTime(select,item[key]);label.append(select);row.append(label);
            }
            const remove=document.createElement('button');remove.type='button';remove.className='facility-cancel-btn';remove.dataset.removeDate='';remove.textContent='Remove';
            row.append(remove);el('serviceAssessmentDates').append(row);this.sync();
        }
        syncLeaseSpaces(category) {
            const selected=[...this.root.querySelectorAll('[data-service-lease]:checked')].map(field=>field.dataset.serviceLease);
            selected.forEach(key=>{
                if(el('serviceLeaseSpaces').querySelector(`[data-lease-config="${key}"]`))return;
                const saved=this.leaseDraft?.[key] || {}, group=document.createElement('section');group.className='service-lease-space';group.dataset.leaseConfig=key;
                const heading=document.createElement('h4');heading.textContent=this.choices.lease_types[key];group.append(heading);
                const grid=document.createElement('div');grid.className='facility-form-grid';group.append(grid);
                for(const [field,title] of Object.entries({location:'Space Location',available_area:'Available Area (sqm)',standard_area:'Standard Area (sqm)',pricing_method:'Pricing Basis',rate:'Rate',regular_term_rate:'Regular Term Rate',midyear_rate:'Midyear Rate',pricing_description:'Pricing / Agreement Details',water_charge:'Water Charge / Month',electricity_arrangement:'Electricity Arrangement',internet_arrangement:'Internet Arrangement',utility_conditions:'Other Utility Conditions'})){
                    const label=document.createElement('label');label.textContent=title;
                    const control=document.createElement(field==='pricing_method'?'select':field==='utility_conditions'?'textarea':'input');control.className=field==='pricing_method'?'form-select':'form-control';control.dataset.spaceField=field;
                    if(field==='pricing_method'){control.add(new Option('Use service pricing',''));this.choices.lease_pricing.forEach(method=>control.add(new Option(this.choices.pricing[method],method)));}
                    else if(['available_area','standard_area','rate','regular_term_rate','midyear_rate','water_charge'].includes(field)){control.type='number';control.min='0';control.step='0.01';control.placeholder='Enter configured amount';}
                    else {control.maxLength=field==='utility_conditions'?1000:250;control.placeholder='Enter '+title.toLowerCase();}
                    control.value=saved[field] ?? '';label.append(control);grid.append(label);
                }
                el('serviceLeaseSpaces').append(group);
            });
            el('serviceLeaseSpaces').querySelectorAll('[data-lease-config]').forEach(group=>{
                const shown=category==='lease_space' && selected.includes(group.dataset.leaseConfig);group.hidden=!shown;
                const method=group.querySelector('[data-space-field=pricing_method]').value;
                group.querySelectorAll('[data-space-field]').forEach(control=>{
                    const key=control.dataset.spaceField;
                    let visible=key==='rate'?!!method && method!=='term':['regular_term_rate','midyear_rate'].includes(key)?method==='term':key==='pricing_description'?method==='custom':true;
                    if(['available_area','standard_area','water_charge'].includes(key) && !control.value){
                        visible=['canteen','stall','other'].includes(group.dataset.leaseConfig) || key!=='water_charge' && (method==='sqm' || value('facilityPriceType')==='sqm');
                    }
                    control.parentElement.hidden=!visible;control.disabled=!shown || !visible;
                    control.required=shown && visible && (['regular_term_rate','midyear_rate','pricing_description'].includes(key) || key==='rate' && method!=='custom');
                });
            });
        }
        leaseDetails() {
            return Object.fromEntries([...el('serviceLeaseSpaces').querySelectorAll('[data-lease-config]')].filter(group=>!group.hidden).map(group=>[
                group.dataset.leaseConfig,Object.fromEntries([...group.querySelectorAll('[data-space-field]')].filter(field=>!field.disabled).map(field=>[field.dataset.spaceField,field.value.trim()]))]));
        }
        rowMenu(resource, manage, viewRequests) {
            const button=(action,label)=>`<li><button type="button" class="dropdown-item" data-facility-row-action="${action}">${label}</button></li>`;
            const items=[button('view','View Service')];
            if(manage && !resource.isArchived)items.push(button('edit','Edit Service'));
            if(viewRequests)items.push(`<li><a class="dropdown-item" href="/admin-service-requests/?service=${encodeURIComponent(resource.id)}">View Service Requests</a></li>`);
            if(manage){
                items.push('<li><hr class="dropdown-divider"></li>');
                if(resource.isArchived)items.push(button('restore','Restore Service'));
                else {
                    if(resource.status!=='available')items.push(button('status_available','Set Active'));
                    if(resource.status==='available')items.push(button('status_unavailable','Set Temporarily Unavailable'));
                    if(resource.status!=='inactive')items.push(button('status_inactive','Set Inactive'));
                    items.push(button('archive','Archive Service'));
                }
            }
            return `<div class="facility-row-actions"><div class="dropdown facility-row-more"><button type="button" class="facility-action-icon" data-bs-toggle="dropdown" data-bs-boundary="viewport" data-bs-config='{"popperConfig":{"strategy":"fixed"}}' aria-expanded="false" aria-label="Service actions"><svg viewBox="0 0 24 24" fill="currentColor" width="18" height="18" aria-hidden="true"><circle cx="12" cy="5" r="1.5"/><circle cx="12" cy="12" r="1.5"/><circle cx="12" cy="19" r="1.5"/></svg></button><ul class="dropdown-menu dropdown-menu-end facility-row-dropdown">${items.join('')}</ul></div></div>`;
        }
        reset() {
            this.requestChosen=false;this.outputChosen=false;this.savedClosedHours=false;
            this.root.querySelectorAll('.service-form-body button').forEach(button=>button.disabled=false);
            this.root.querySelector('.service-form-body').querySelectorAll('input:not([type=file]),select,textarea').forEach(field=>{
                field.setCustomValidity('');if(field.type==='checkbox')field.checked=false;else field.value='';
            });
            this.leaseDraft={};el('serviceLeaseSpaces').replaceChildren();el('serviceAssessmentDates').replaceChildren();
            el('facilityStatus').value='available';
            el('serviceAnalysisRows').replaceChildren();el('serviceExistingPricing').hidden=true;this.sync();
        }
        fill(resource) {
            this.reset();const workflow=resource.workflowConfig || {}, config=workflow.service || {};
            const fields={facilityName:resource.name,facilityType:resource.facilityType,facilityLocation:resource.location,
                facilityStatus:['maintenance','occupied','reserved'].includes(resource.status)?'unavailable':resource.status,
                facilityDescription:resource.description,facilityRequirements:resource.requirements,facilityTermsConditions:resource.termsConditions,
                serviceCustomCategory:resource.customFacilityType || workflow.custom_facility_type,
                serviceRequestType:resource.mode==='direct'?'service':resource.mode,
                servicePaymentTiming:config.payment_timing,serviceCustomTiming:config.custom_payment_timing,
                serviceOutputType:config.output_type ?? '',serviceCustomOutput:config.custom_output_type,
                serviceCustomPricing:config.custom_pricing_description,serviceTurnaround:workflow.turnaround_information,
                serviceAssessmentName:workflow.assessment_service_type,serviceCandidateCapacity:resource.capacity || '',
                serviceSchedulingMethod:config.scheduling_method,serviceOtherLease:config.other_lease_space_type};
            Object.entries(fields).forEach(([id,text])=>el(id).value=text ?? '');
            el('serviceRegularRate').value=config.term_rates?.regular ?? '';el('serviceMidyearRate').value=config.term_rates?.midyear ?? '';
            this.leaseDraft=config.lease_space_details || {};
            this.requestChosen=!!value('serviceRequestType');this.outputChosen=!!value('serviceOutputType');
            const flags={serviceApproval:workflow.requires_approval,
                serviceAvailabilityEnabled:config.availability_enabled || (config.version!==1 && typeof workflow.operating_hours==='object'),
                serviceSampleAcceptance:config.sample_acceptance_required};
            Object.entries(flags).forEach(([id,checked])=>el(id).checked=checked===true);
            this.savedClosedHours=el('serviceAvailabilityEnabled').checked && days.every(day=>workflow.operating_hours?.[day]===null);
            this.sync();el('facilityPriceType').value=resource.priceType;this.sync();
            el('facilityRate').value=resource.priceType==='custom' && !config.custom_amount_set?'':resource.rate;
            (config.pricing_items || []).forEach(item=>this.addAnalysis(item));
            (config.assessment_dates || []).forEach(item=>this.addAssessmentDate(item));
            this.root.querySelectorAll('[data-service-lease]').forEach(input=>input.checked=(config.lease_space_types || []).includes(input.dataset.serviceLease));
            this.root.querySelectorAll('[data-service-day]').forEach(row=>{
                const period=workflow.operating_hours?.[row.dataset.serviceDay];row.querySelector('[data-service-open]').checked=!!period;
                window.CampusHubOperatingSchedule.setTime(row.querySelector('[data-service-start]'),period?.open);
                window.CampusHubOperatingSchedule.setTime(row.querySelector('[data-service-end]'),period?.close);
            });
            if(!this.choices.pricing[resource.priceType]) {
                el('serviceExistingPricing').hidden=false;
                el('serviceExistingPricing').textContent='Choose a pricing method before saving. Existing rate: '+new Intl.NumberFormat('en-PH',{style:'currency',currency:'PHP'}).format(Number(resource.rate || 0));
            }
            this.sync();
        }
        validate() {
            if(value('facilityType')==='training_kitchen' && value('serviceSchedulingMethod')==='specific_date'){
                for(const row of el('serviceAssessmentDates').children){
                    const start=row.querySelector('[data-assessment-time=start]'),end=row.querySelector('[data-assessment-time=end]');
                    start.setCustomValidity('');end.setCustomValidity('');
                    if(!!start.value!==!!end.value || start.value && start.value>=end.value){end.setCustomValidity('Enter both times, with end time after start time.');end.reportValidity();return false;}
                }
            }
            const weekly=el('serviceAvailabilityEnabled');weekly.setCustomValidity('');
            if(weekly.checked) {
                const available=[...this.root.querySelectorAll('[data-service-day]')].filter(row=>row.querySelector('[data-service-open]').checked);
                if(!available.length && !this.savedClosedHours){weekly.setCustomValidity('Select at least one available day, or turn off weekly availability.');weekly.reportValidity();return false;}
                for(const row of available){const start=row.querySelector('[data-service-start]'),end=row.querySelector('[data-service-end]');end.setCustomValidity('');if(start.value && end.value && start.value>=end.value){end.setCustomValidity('End time must be after start time.');end.reportValidity();return false;}}
            }
            const controls=[...this.root.querySelectorAll('.service-form-body input,.service-form-body select,.service-form-body textarea')].filter(field=>!field.disabled);
            for(const field of controls) {if(field.required && field.type!=='checkbox' && !field.value.trim())field.setCustomValidity('Complete this required field.');if(!field.checkValidity()){field.reportValidity();return false;}}
            if(value('facilityPriceType')==='analysis' && !el('serviceAnalysisRows').children.length){el('serviceAddAnalysis').focus();return false;}
            return true;
        }
        payload(images) {
            const category=value('facilityType'), method=value('facilityPriceType');
            const checked=id=>el(id).checked, config={payment_timing:value('servicePaymentTiming'),
                output_type:value('serviceOutputType'),availability_enabled:checked('serviceAvailabilityEnabled')};
            if(config.payment_timing==='custom')config.custom_payment_timing=value('serviceCustomTiming');
            if(config.output_type==='custom')config.custom_output_type=value('serviceCustomOutput');
            if(method==='analysis')config.pricing_items=[...el('serviceAnalysisRows').children].map(row=>({name:row.querySelector('[data-analysis-name]').value.trim(),description:row.querySelector('[data-analysis-description]').value.trim(),fee:row.querySelector('[data-analysis-fee]').value,active:row.querySelector('[data-analysis-active]').checked,charging_basis:row.querySelector('[data-analysis-basis]').value}));
            if(method==='term')config.term_rates={regular:value('serviceRegularRate'),midyear:value('serviceMidyearRate')};
            if(method==='custom')config.custom_pricing_description=value('serviceCustomPricing');
            if(category==='food_analysis')config.sample_acceptance_required=checked('serviceSampleAcceptance');
            if(category==='training_kitchen'){config.scheduling_method=value('serviceSchedulingMethod');if(config.scheduling_method==='specific_date')config.assessment_dates=[...el('serviceAssessmentDates').children].map(row=>({date:row.querySelector('[data-assessment-date]').value,start:row.querySelector('[data-assessment-time=start]').value,end:row.querySelector('[data-assessment-time=end]').value}));}
            if(category==='lease_space'){config.lease_space_types=[...this.root.querySelectorAll('[data-service-lease]:checked')].map(input=>input.dataset.serviceLease);config.lease_space_details=this.leaseDetails();if(config.lease_space_types.includes('other'))config.other_lease_space_type=value('serviceOtherLease');}
            const workflow={service:config,requires_approval:checked('serviceApproval')};
            if(config.availability_enabled)workflow.operating_hours=Object.fromEntries([...this.root.querySelectorAll('[data-service-day]')].map(row=>[row.dataset.serviceDay,row.querySelector('[data-service-open]').checked?{open:row.querySelector('[data-service-start]').value,close:row.querySelector('[data-service-end]').value}:null]));
            if(category==='food_analysis')workflow.turnaround_information=value('serviceTurnaround');
            if(category==='training_kitchen')workflow.assessment_service_type=value('serviceAssessmentName');
            return {catalog_kind:'service',name:value('facilityName'),facility_type:category,custom_facility_type:category==='other'?value('serviceCustomCategory'):'',
                location:value('facilityLocation'),status:value('facilityStatus'),description:value('facilityDescription'),mode:value('serviceRequestType'),price_type:method,
                rate:method==='analysis'?'':value('facilityRate').replaceAll(',',''),capacity:category==='training_kitchen'?value('serviceCandidateCapacity'):0,
                workflow_config:workflow,requirements:value('facilityRequirements'),terms_conditions:value('facilityTermsConditions'),images};
        }
    }
    window.ServiceFormControls=ServiceFormControls;
})();
