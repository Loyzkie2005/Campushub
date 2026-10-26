/* Existing Facility values remain authoritative; this class controls disclosure. */
(() => {
    class FacilityRentalControls {
        constructor(root, configuration, fields) {
            this.root = root; this.configuration = configuration; this.fields = fields;
            this.customType = root.querySelector('#facilityCustomType');
            this.minimum = root.querySelector('#facilityCapacityMin');
            this.formType = root.querySelector('#facilityBookingFormType');
            this.formDisplay = root.querySelector('#facilityBookingFormDisplay');
            this.base = root.querySelector('#facilityBaseDuration');
            this.extra = root.querySelector('#facilityAdditionalHourRate');
            this.notes = root.querySelector('#facilityPricingNotes');
            this.partner = root.querySelector('#facilityPartnerRate');
            this.occupancy = root.querySelector('#facilityPartnerOccupancy');
            this.deposit = root.querySelector('#facilityDepositApplicable');
            this.depositType = root.querySelector('#facilityDepositType');
            this.depositValue = root.querySelector('#facilityDepositValue');
            this.fees = root.querySelector('#facilityAdditionalFees');
            this.discounts = root.querySelector('#facilityDiscountRules');
            this.rules = {requires_approval: root.querySelector('#facilityRequiresApproval'),
                requires_pre_use_inspection: root.querySelector('#facilityPreInspection'),
                requires_post_use_inspection: root.querySelector('#facilityPostInspection'), damage_deposit_applicable: this.deposit};
            this.populate(this.formType, configuration.booking_form_types, 'Select booking form');
            this.deposit.addEventListener('change', () => this.sync());
            this.depositType.addEventListener('change', () => this.sync());
            fields.priceType.addEventListener('change', () => this.sync());
            this.partner.addEventListener('input', () => this.sync());
            root.querySelector('#facilityAddFee').addEventListener('click', () => this.addFee());
            root.querySelector('#facilityAddDiscount').addEventListener('click', () => this.addDiscount());
            root.addEventListener('input', event => event.target.setCustomValidity?.(''));
            root.addEventListener('change', event => event.target.setCustomValidity?.(''));
        }

        populate(select, labels, placeholder = null) {
            select.replaceChildren(...(placeholder ? [new Option(placeholder, '')] : []), ...Object.entries(labels).map(([value, label]) => new Option(label, value)));
        }

        configure(type, config, {preserve = true} = {}) {
            const previousMode = this.fields.mode.value;
            const legacyDirect = preserve && previousMode === 'direct';
            this.physical = !document.body.classList.contains('service-catalog')
                && !['food_analysis', 'training_kitchen', 'lease_space'].includes(type) && !legacyDirect;
            const modes = this.physical ? Object.fromEntries(['slot','room','daily','custom'].map(key => [key,this.configuration.booking_mode_labels[key]])) : {[config.booking_mode]: this.configuration.booking_mode_labels[config.booking_mode]};
            // Preserve legacy direct service records without offering that mode for new ones.
            if (legacyDirect) modes.direct = 'Service Request';
            this.populate(this.fields.mode, modes, this.physical ? 'Select booking mode' : null);
            const suggestedMode = type && type !== 'other' ? config.booking_mode : '';
            this.fields.mode.value = preserve && previousMode in modes ? previousMode : (this.physical ? suggestedMode : config.booking_mode);
            this.fields.mode.disabled = !this.physical;
            const previousPrice = this.fields.priceType.value;
            const prices = this.physical ? this.configuration.pricing_methods : Object.fromEntries(config.price_types.map(key => [key, this.configuration.price_type_labels[key]]));
            this.populate(this.fields.priceType, prices, this.physical ? 'Select pricing method' : null);
            this.fields.priceType.value = preserve && previousPrice in prices ? previousPrice : (this.physical ? '' : config.default_price_type);
            this.fields.priceType.required = this.physical;
            if (!preserve && this.physical) {
                this.formType.value = this.configuration.booking_form_defaults[type] || '';
                this.rules.requires_approval.checked = true;
                this.rules.requires_pre_use_inspection.checked = !!this.configuration.booking_form_defaults[type];
                this.rules.requires_post_use_inspection.checked = !!this.configuration.booking_form_defaults[type];
            }
            this.sync();
            if (!this.physical) return config;
            const room = this.fields.mode.value === 'room';
            return {...config, fields: ['capacity', 'rate', 'operating_hours', 'amenities',
                ...(room ? ['rooms_units','room_type','capacity_per_room','check_in_time','check_out_time'] : this.fields.mode.value === 'slot' ? ['minimum_booking_duration'] : [])], required: !this.fields.priceType.value || this.fields.priceType.value === 'custom' ? [] : ['rate']};
        }

        disclose(name, visible, required = false) {
            const wrap = this.root.querySelector(`[data-rental-field="${name}"]`);
            if (!wrap) return;
            wrap.hidden = !visible;
            wrap.querySelectorAll('input, select, textarea, button').forEach(field => {field.disabled = !visible; field.required = visible && required;});
        }

        sync() {
            const method = this.fields.priceType.value;
            const customVisible = this.fields.type.value === 'other';
            this.customType.closest('[data-custom-type-field]').hidden = !customVisible;
            this.customType.disabled = !customVisible;
            this.customType.required = customVisible;
            if (!customVisible) this.customType.value = '';
            ['rules','form_type','fees','discounts','capacity_min'].forEach(name => this.disclose(name, this.physical));
            this.disclose('form_type', this.physical, true);
            this.syncBookingForm();
            this.disclose('base_duration', this.physical && method === 'base_hour', true);
            this.disclose('additional_hour_rate', this.physical && method === 'base_hour', true);
            this.disclose('pricing_notes', this.physical && method === 'custom', true);
            this.disclose('partner_rate', this.physical && method === 'person_night');
            this.disclose('partner_occupancy', this.physical && method === 'person_night' && this.partner.value.trim() !== '', true);
            this.disclose('deposit_type', this.physical && this.deposit.checked, true);
            this.disclose('deposit_value', this.physical && this.deposit.checked, true);
            this.depositValue.max = this.depositType.value === 'percentage' ? '100' : '99999999.99';
            this.root.querySelector('#facilityDepositHelp').textContent = this.depositType.value === 'percentage' ? 'Percentage of the applicable rental/base fee.' : 'Fixed amount in Philippine Peso.';
            this.root.querySelector('#facilityRoomsNotice').hidden = !this.physical || this.fields.mode.value !== 'room';
            if (this.physical) {
                const wrap = this.fields.rate.closest('[data-facility-field]');
                wrap.hidden = !method || method === 'custom'; this.fields.rate.disabled = wrap.hidden;
                this.fields.rate.required = !wrap.hidden;
                this.root.querySelector('#facilityRateLabel').textContent = (({hour:'Hourly Rate',base_hour:'Base Rate',day:'Daily Rate',person:'Rate Per Person',person_night:'Standard / Individual Rate',night:'Rate Per Night',session:'Fixed Rate'})[method] || 'Rate') + ' *';
            }
            for (const row of this.fees.children) this.syncFee(row);
            for (const row of this.discounts.children) this.syncDiscount(row);
        }

        syncBookingForm() {
            const category = this.fields.type.value;
            const assigned = this.configuration.booking_form_defaults[category];
            const explicit = this.physical && category === 'other';
            if (assigned) this.formType.value = assigned;
            this.formType.hidden = !explicit;
            this.formType.disabled = !explicit;
            this.formType.required = explicit;
            this.formDisplay.hidden = explicit;
            this.formDisplay.textContent = assigned
                ? this.configuration.booking_form_types[assigned] : 'Select Facility Category first.';
            this.root.querySelector('#facilityBookingFormLabel').htmlFor = explicit ? this.formType.id : this.formDisplay.id;
            this.root.querySelector('#facilityBookingFormHelp').textContent = explicit
                ? 'Select the existing booking form that applies to this Other category.'
                : 'Automatically assigned based on Facility Category.';
        }

        setWorkflow(workflow, {mode = 'slot', physical = true} = {}) {
            this.customType.value = typeof workflow.custom_facility_type === 'string' ? workflow.custom_facility_type : '';
            this.minimum.value = workflow.capacity_min ?? '';
            for (const [key, field] of Object.entries(this.rules)) field.checked = workflow[key] ?? (key === 'requires_approval');
            this.formType.value = this.configuration.booking_form_defaults[this.fields.type.value] || workflow.booking_form_type || '';
            this.base.value = workflow.pricing?.base_duration ?? '';
            this.extra.value = workflow.pricing?.additional_hour_rate ?? '';
            this.notes.value = workflow.pricing?.notes ?? '';
            this.partner.value = workflow.pricing?.partner_rate ?? '';
            this.occupancy.value = workflow.pricing?.partner_occupancy_required ?? '';
            this.depositType.value = workflow.damage_deposit?.type || '';
            this.depositValue.value = workflow.damage_deposit?.value ?? '';
            this.fees.replaceChildren();
            for (const fee of workflow.additional_fees || []) this.addFee(fee);
            this.discounts.replaceChildren();
            for (const rule of workflow.discount_rules || []) this.addDiscount(rule);
            this.physical = physical; this.sync();
        }

        addFee(fee = {}) {
            if (this.fees.children.length >= 30) return;
            const row = document.createElement('div'); row.className = 'facility-fee-row';
            const name = document.createElement('input'); name.className = 'form-control'; name.placeholder = 'Enter fee name'; name.maxLength = 150; name.value = fee.name || ''; name.dataset.feeField = 'name';
            const amount = document.createElement('input'); amount.className = 'form-control'; amount.type = 'number'; amount.min = '0'; amount.step = '0.01'; amount.placeholder = 'Amount (₱)'; amount.value = fee.amount ?? ''; amount.dataset.feeField = 'amount';
            const unit = document.createElement('select'); unit.className = 'form-select'; this.populate(unit, this.configuration.fee_units, 'Select basis');
            if (fee.unit === 'unit') unit.add(new Option('Per Item','unit'));
            unit.value = fee.unit || ''; unit.dataset.feeField = 'unit';
            for (const [field, label] of [[name,'Fee Name *'],[amount,'Fee Amount (₱) *'],[unit,'Charging Basis *']]) {
                field.required = true; const wrap = document.createElement('label'); const text = document.createElement('span'); text.className = 'form-label'; text.textContent = label; wrap.append(text,field); row.append(wrap);
            }
            const active = document.createElement('label'); active.className = 'facility-check'; const checkbox = document.createElement('input'); checkbox.type = 'checkbox'; checkbox.checked = fee.active ?? true; checkbox.dataset.feeField = 'active'; active.append(checkbox,document.createTextNode('Active'));
            const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'facility-fee-action'; remove.textContent = 'Remove'; remove.addEventListener('click', () => row.remove());
            const custom = document.createElement('label'); custom.className = 'facility-fee-custom';
            const caption = document.createElement('span'); caption.className = 'form-label'; caption.textContent = 'Custom Charging Basis *';
            const detail = document.createElement('input'); detail.className = 'form-control'; detail.dataset.feeField = 'custom_basis'; detail.maxLength = 200; detail.placeholder = 'Describe the charging basis'; detail.value = fee.custom_basis || '';
            custom.append(caption,detail); row.append(active,remove,custom); this.fees.append(row);
            unit.addEventListener('change', () => this.syncFee(row)); this.syncFee(row);
        }

        syncFee(row) {
            row.querySelectorAll('[data-fee-field]').forEach(field => field.required = this.physical && field.type !== 'checkbox');
            const detail = row.querySelector('[data-fee-field="custom_basis"]');
            const custom = this.physical && row.querySelector('[data-fee-field="unit"]').value === 'custom';
            detail.closest('label').hidden = !custom; detail.disabled = !custom; detail.required = custom;
            if (!custom) detail.value = '';
        }

        addDiscount(rule = {}) {
            if (this.discounts.children.length >= 30) return;
            const row = document.createElement('div'); row.className = 'facility-discount-row';
            for (const [key, label, choices] of [
                ['eligible_client_type','Eligible Client Type',this.configuration.discount_clients],
                ['discount_type','Discount Type',this.configuration.discount_types],
                ['discount_value','Discount Value',null],
                ['applies_to','Applies To',this.configuration.discount_scopes],
            ]) {
                const field = document.createElement(choices ? 'select' : 'input');
                field.className = choices ? 'form-select' : 'form-control'; field.dataset.discountField = key;
                if (choices) this.populate(field, choices, 'Select');
                else { field.type = 'number'; field.min = '0'; field.step = '0.01'; field.placeholder = 'Enter value'; }
                field.value = rule[key] ?? ''; field.required = true;
                const wrap = document.createElement('label'); const text = document.createElement('span'); text.className = 'form-label'; text.textContent = label;
                wrap.append(text, field); row.append(wrap);
                field.addEventListener('change', () => this.syncDiscount(row));
            }
            const active = document.createElement('label'); active.className = 'facility-check';
            const checkbox = document.createElement('input'); checkbox.type = 'checkbox'; checkbox.checked = rule.active ?? true; checkbox.dataset.discountField = 'active';
            active.append(checkbox,document.createTextNode('Active'));
            const remove = document.createElement('button'); remove.type = 'button'; remove.className = 'facility-fee-action'; remove.textContent = 'Remove'; remove.addEventListener('click', () => row.remove());
            const custom = document.createElement('label'); custom.className = 'facility-discount-custom';
            const text = document.createElement('span'); text.className = 'form-label'; text.textContent = 'Custom Discount Scope *';
            const detail = document.createElement('input'); detail.className = 'form-control'; detail.maxLength = 200; detail.placeholder = 'Describe what part of the rental the discount applies to'; detail.dataset.discountField = 'custom_scope'; detail.value = rule.custom_scope || '';
            custom.append(text,detail); row.append(active,remove,custom); this.discounts.append(row); this.syncDiscount(row);
        }

        syncDiscount(row) {
            const find = key => row.querySelector(`[data-discount-field="${key}"]`);
            row.querySelectorAll('[data-discount-field]').forEach(field => field.required = this.physical && field.type !== 'checkbox');
            const value = find('discount_value'); value.max = find('discount_type').value === 'percentage' ? '100' : '99999999.99';
            const scope = find('applies_to');
            const selected = scope.value;
            const choices = this.configuration.discount_scopes_by_method[this.fields.priceType.value] || {};
            this.populate(scope, choices, 'Select');
            if (selected && !(selected in choices)) {
                const invalid = new Option(`${this.configuration.discount_scopes[selected] || selected} — unavailable for this pricing method`, selected); invalid.disabled = true; scope.add(invalid);
            }
            scope.value = selected;
            const partnerOption = [...scope.options].find(option => option.value === 'partner_rate');
            if (partnerOption) partnerOption.disabled = this.partner.value.trim() === '';
            scope.setCustomValidity(scope.selectedOptions[0]?.disabled ? 'Select a scope supported by the pricing method and configured rate.' : '');
            const detail = find('custom_scope'); const custom = scope.value === 'custom' && this.physical;
            detail.closest('label').hidden = !custom; detail.disabled = !custom; detail.required = custom;
            if (!custom) detail.value = '';
        }

        getWorkflow() {
            if (!this.physical) return {};
            const result = Object.fromEntries(Object.entries(this.rules).map(([key, field]) => [key,field.checked]));
            result.booking_form_type = this.formType.value;
            result.capacity_min = this.minimum.value;
            if (this.fields.priceType.value === 'base_hour') result.pricing = {base_duration:this.base.value,additional_hour_rate:this.extra.value};
            else if (this.fields.priceType.value === 'person_night' && this.partner.value.trim() !== '') result.pricing = {partner_rate:this.partner.value,partner_occupancy_required:this.occupancy.value};
            else if (this.fields.priceType.value === 'custom') result.pricing = {notes:this.notes.value.trim()};
            else result.pricing = {};
            result.damage_deposit = this.deposit.checked ? {type:this.depositType.value,value:this.depositValue.value} : {};
            result.additional_fees = [...this.fees.children].map(row => Object.fromEntries([...row.querySelectorAll('[data-fee-field]')].filter(field => !field.disabled).map(field => [field.dataset.feeField,field.type === 'checkbox' ? field.checked : field.value.trim()])));
            result.discount_rules = [...this.discounts.children].map(row => Object.fromEntries([...row.querySelectorAll('[data-discount-field]')].filter(field => !field.disabled).map(field => [field.dataset.discountField,field.type === 'checkbox' ? field.checked : field.value.trim()])));
            return result;
        }

        validate() {
            if (!this.customType.disabled && !this.customType.value.trim()) this.customType.setCustomValidity(`${this.physical ? 'Specify Facility Category' : 'Specify Facility Type'} is required when Other is selected.`);
            if (this.physical && this.minimum.value && Number(this.minimum.value) > Number(this.fields.capacity.value)) this.minimum.setCustomValidity('Minimum capacity must not exceed maximum capacity.');
            return [...this.root.querySelectorAll('input, select, textarea')].filter(field => !field.disabled && !field.closest('[hidden]')).every(field => field.reportValidity());
        }
    }
    window.FacilityRentalControls = FacilityRentalControls;
})();
