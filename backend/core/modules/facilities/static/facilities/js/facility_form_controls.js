/* Structured controls shared by Add, Edit, and View Facility. */
(() => {
    // Shared display controls only; each form keeps its own validation and payload.
    const operatingScheduleUi = {
        timeSelect(label) {
            const select = document.createElement('select');
            select.className = 'form-select';
            select.setAttribute('aria-label', label);
            select.add(new Option('Select time', ''));
            for (let minutes = 0; minutes < 24 * 60; minutes += 15) {
                const hour = Math.floor(minutes / 60);
                const minute = String(minutes % 60).padStart(2, '0');
                const value = `${String(hour).padStart(2, '0')}:${minute}`;
                select.add(new Option(`${hour % 12 || 12}:${minute} ${hour < 12 ? 'AM' : 'PM'}`, value));
            }
            return select;
        },
        setTime(select, value) {
            // Preserve saved boundaries exactly, including non-quarter-hour times.
            if (value && !Array.from(select.options).some(option => option.value === value)) {
                const [hour, minute] = value.split(':').map(Number);
                const label = Number.isInteger(hour) && Number.isInteger(minute)
                    ? `${hour % 12 || 12}:${String(minute).padStart(2, '0')} ${hour < 12 ? 'AM' : 'PM'}` : value;
                select.add(new Option(label, value));
            }
            select.value = value || '';
        },
    };
    window.CampusHubOperatingSchedule = operatingScheduleUi;

    class FacilityFormControls {
        constructor(root, configuration) {
            this.root = root;
            this.configuration = configuration;
            this.physical = !document.body.classList.contains('service-catalog');
            this.customFeature = '';
            this.amenities = root.querySelector('#facilityAmenityChoices');
            this.other = root.querySelector('#facilityOtherAmenity');
            this.otherInput = root.querySelector('#facilityOtherAmenityText');
            this.otherField = root.querySelector('#facilityOtherAmenityField');
            this.schedule = root.querySelector('#facilityOperatingHours');
            this.notice = root.querySelector('#facilityScheduleNotice');
            this.minimum = root.querySelector('#facilityMinimumBookingDuration');
            this.customMinimum = root.querySelector('#facilityCustomDuration');
            this.type = 'covered_court';
            this.buildSchedule();
            this.other.addEventListener('change', () => this.syncOther());
            this.otherInput.addEventListener('input', () => this.otherInput.setCustomValidity(''));
            this.minimum.addEventListener('change', () => {this.minimum.setCustomValidity(''); this.syncMinimum();});
            this.setAmenities([]);
        }

        buildSchedule() {
            this.rows = this.configuration.weekdays.map((day) => {
                const row = document.createElement('div');
                row.className = 'facility-hours-row';
                const label = document.createElement('label');
                label.className = 'facility-check';
                const active = document.createElement('input');
                active.type = 'checkbox';
                active.id = `facilityDay-${day}`;
                const dayName = day[0].toUpperCase() + day.slice(1);
                label.append(active, document.createTextNode(dayName));
                const times = document.createElement('div');
                times.className = 'facility-hours-times';
                const open = this.timeSelect(`${dayName} opening time`);
                const close = this.timeSelect(`${dayName} closing time`);
                for (const [field, caption] of [[open, 'Opening Time'], [close, 'Closing Time']]) {
                    const timeLabel = document.createElement('label'); timeLabel.className = 'facility-hours-time-label';
                    const text = document.createElement('span'); text.textContent = caption;
                    timeLabel.append(text, field); times.append(timeLabel);
                }
                const closed = document.createElement('span');
                closed.className = 'facility-hours-closed';
                closed.textContent = 'Closed';
                row.append(label, times, closed);
                this.schedule.append(row);
                const entry = {day, active, times, open, close, closed};
                active.addEventListener('change', () => {
                    this.scheduleDirty = true;
                    active.setCustomValidity('');
                    this.syncDay(entry);
                });
                [open, close].forEach((field) => field.addEventListener('change', () => {
                    this.scheduleDirty = true;
                    open.setCustomValidity('');
                    close.setCustomValidity('');
                }));
                return entry;
            });
            this.setWorkflow({});
        }

        timeSelect(label) {
            return operatingScheduleUi.timeSelect(label);
        }

        setTime(select, value) {
            operatingScheduleUi.setTime(select, value);
        }

        syncDay(row) {
            const visible = !this.schedule.closest('[data-facility-field]').hidden;
            row.times.hidden = !row.active.checked;
            row.closed.hidden = row.active.checked;
            for (const field of [row.open, row.close]) {
                field.disabled = !visible || !row.active.checked;
                field.required = visible && row.active.checked;
            }
        }

        syncOther() {
            const visible = !this.amenities.closest('[data-facility-field]').hidden;
            this.otherField.hidden = !this.other.checked;
            this.otherInput.disabled = !visible || !this.other.checked;
            this.otherInput.required = visible && this.other.checked;
            if (!this.other.checked) { this.otherInput.value = ''; this.customFeature = ''; }
            this.otherInput.setCustomValidity('');
        }

        setAmenities(selected) {
            const choices = this.type === 'food_analysis' ? this.configuration.services : this.physical ? this.configuration.amenities : this.configuration.service_amenities;
            const custom = this.physical ? this.customFeature : '';
            const values = [...new Set([...choices, ...selected])].filter(value => value !== custom && value !== 'Other');
            this.amenities.replaceChildren();
            for (const value of values) {
                const label = document.createElement('label');
                label.className = 'facility-check';
                const checkbox = document.createElement('input');
                checkbox.type = 'checkbox';
                checkbox.value = value;
                checkbox.checked = selected.includes(value);
                label.append(checkbox, document.createTextNode(value));
                this.amenities.append(label);
            }
            this.other.checked = Boolean(custom);
            this.otherInput.value = custom;
            this.syncOther();
        }

        getAmenities() {
            const values = Array.from(this.amenities.querySelectorAll('input:checked'), (input) => input.value);
            if (this.other.checked && this.otherInput.value.trim()) values.push(this.otherInput.value.trim());
            return [...new Set(values)];
        }

        getFeatureWorkflow() {
            return this.physical ? {other_feature: this.other.checked ? this.otherInput.value.trim() : null} : {};
        }

        setWorkflow(workflow) {
            this.customFeature = this.physical && typeof workflow.other_feature === 'string' ? workflow.other_feature : '';
            this.other.checked = Boolean(this.customFeature); this.otherInput.value = this.customFeature; this.syncOther();
            const hours = workflow.operating_hours;
            this.originalHours = hours;
            this.scheduleDirty = false;
            this.notice.hidden = !hours || typeof hours === 'object';
            this.notice.textContent = this.notice.hidden ? '' : `Review the existing operating hours: ${hours}`;
            for (const row of this.rows || []) {
                const period = hours && typeof hours === 'object' ? hours[row.day] : null;
                row.active.checked = Boolean(period);
                this.setTime(row.open, period?.open);
                this.setTime(row.close, period?.close);
                row.active.setCustomValidity('');
                row.open.setCustomValidity('');
                row.close.setCustomValidity('');
                this.syncDay(row);
            }
            const duration = String(workflow.minimum_booking_duration || '');
            this.minimum.querySelectorAll('[data-existing-duration]').forEach((option) => option.remove());
            const normalized = duration ? String(Number(duration)) : '';
            const predefined = [...this.minimum.options].some(option => option.value === normalized);
            this.minimum.value = predefined ? normalized : 'custom';
            this.customMinimum.value = !predefined && Number.isFinite(Number(duration)) ? Math.round(Number(duration) * 60) : '';
            this.minimum.setCustomValidity('');
            this.syncMinimum();
        }

        syncMinimum() {
            const active = !this.minimum.disabled && this.minimum.value === 'custom';
            this.customMinimum.closest('#facilityCustomDurationField').hidden = !active;
            this.customMinimum.disabled = !active; this.customMinimum.required = active;
            if (this.minimum.value !== 'custom') this.customMinimum.value = '';
        }

        getMinimumDuration() {
            return this.minimum.value === 'custom' ? `${this.customMinimum.value} minutes` : this.minimum.value;
        }

        getOperatingHours() {
            if (typeof this.originalHours === 'string' && !this.scheduleDirty) return this.originalHours;
            return Object.fromEntries(this.rows.map((row) => [row.day, row.active.checked
                ? {open: row.open.value, close: row.close.value} : null]));
        }

        syncType(type, config, slots) {
            if (type !== this.type) {
                const selected = this.getAmenities();
                const otherChecked = this.other.checked, otherText = this.otherInput.value;
                this.customFeature = this.physical && otherChecked ? otherText : '';
                this.type = type;
                this.setAmenities(selected);
                this.other.checked = otherChecked; this.otherInput.value = otherText;
            }
            const minimumField = this.minimum.closest('[data-facility-field]');
            minimumField.hidden = !config.fields.includes('minimum_booking_duration') || Boolean(slots?.trim());
            this.minimum.disabled = minimumField.hidden;
            this.syncMinimum();
            this.rows.forEach((row) => this.syncDay(row));
            this.syncOther();
        }

        validate() {
            if (this.other.checked && !this.otherInput.disabled && !this.otherInput.value.trim()) {
                this.otherInput.setCustomValidity(this.physical ? 'Specify Other Feature is required.' : 'Specify the other amenity or service.');
                this.otherInput.reportValidity();
                return false;
            }
            if (!this.minimum.disabled && !this.minimum.reportValidity()) return false;
            if (!this.customMinimum.disabled && !this.customMinimum.reportValidity()) return false;
            if (this.schedule.closest('[data-facility-field]').hidden) return true;
            const active = this.rows.filter((row) => row.active.checked);
            if (!active.length) return true; // Closed/unconfigured; never invent an operating schedule.
            this.rows[0].active.setCustomValidity('');
            for (const row of active) {
                row.close.setCustomValidity(row.open.value && row.close.value && row.close.value <= row.open.value
                    ? 'Closing time must be after opening time.' : '');
                if (!row.open.reportValidity() || !row.close.reportValidity()) return false;
            }
            return true;
        }
    }
    window.FacilityFormControls = FacilityFormControls;
})();
