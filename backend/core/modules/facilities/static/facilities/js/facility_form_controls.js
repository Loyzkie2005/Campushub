/* Structured controls shared by Add, Edit, and View Facility. */
(() => {
    class FacilityFormControls {
        constructor(root, configuration) {
            this.root = root;
            this.configuration = configuration;
            this.amenities = root.querySelector('#facilityAmenityChoices');
            this.other = root.querySelector('#facilityOtherAmenity');
            this.otherInput = root.querySelector('#facilityOtherAmenityText');
            this.otherField = root.querySelector('#facilityOtherAmenityField');
            this.schedule = root.querySelector('#facilityOperatingHours');
            this.notice = root.querySelector('#facilityScheduleNotice');
            this.minimum = root.querySelector('#facilityMinimumBookingDuration');
            this.type = 'covered_court';
            this.buildSchedule();
            this.other.addEventListener('change', () => this.syncOther());
            this.otherInput.addEventListener('input', () => this.otherInput.setCustomValidity(''));
            this.minimum.addEventListener('change', () => this.minimum.setCustomValidity(''));
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
                const separator = document.createElement('span');
                separator.textContent = 'to';
                times.append(open, separator, close);
                const closed = document.createElement('span');
                closed.className = 'facility-hours-closed';
                closed.textContent = 'Closed';
                row.append(label, times, closed);
                this.schedule.append(row);
                const entry = {day, active, times, open, close, closed};
                active.addEventListener('change', () => {
                    active.setCustomValidity('');
                    this.syncDay(entry);
                });
                [open, close].forEach((field) => field.addEventListener('change', () => {
                    open.setCustomValidity('');
                    close.setCustomValidity('');
                }));
                return entry;
            });
            this.setWorkflow({});
        }

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
        }

        setTime(select, value) {
            // Keep legacy non-quarter-hour times without rounding the booking boundary.
            if (value && !Array.from(select.options).some((option) => option.value === value)) {
                select.add(new Option(value, value));
            }
            select.value = value || '';
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
            this.otherInput.setCustomValidity('');
        }

        setAmenities(selected) {
            const choices = this.type === 'food_analysis' ? this.configuration.services : this.configuration.amenities;
            const values = [...new Set([...choices, ...selected])];
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
            this.other.checked = false;
            this.otherInput.value = '';
            this.syncOther();
        }

        getAmenities() {
            const values = Array.from(this.amenities.querySelectorAll('input:checked'), (input) => input.value);
            if (this.other.checked && this.otherInput.value.trim()) values.push(this.otherInput.value.trim());
            return [...new Set(values)];
        }

        setWorkflow(workflow) {
            const hours = workflow.operating_hours;
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
            if (duration && !Array.from(this.minimum.options).some((option) => option.value === duration)) {
                if (Number.isFinite(Number(duration)) && Number(duration) > 0 && Number(duration) <= 24) {
                    const option = new Option(`${Number(duration) * 60} minutes`, duration);
                    option.dataset.existingDuration = 'true';
                    this.minimum.add(option);
                }
            }
            this.minimum.value = duration;
            this.minimum.setCustomValidity(duration && !this.minimum.value
                ? 'Choose a valid minimum duration or No minimum.' : '');
        }

        getOperatingHours() {
            return Object.fromEntries(this.rows.map((row) => [row.day, row.active.checked
                ? {open: row.open.value, close: row.close.value} : null]));
        }

        syncType(type, config, slots) {
            if (type !== this.type) {
                const selected = this.getAmenities();
                this.type = type;
                this.setAmenities(selected);
            }
            const minimumField = this.minimum.closest('[data-facility-field]');
            minimumField.hidden = !config.fields.includes('minimum_booking_duration') || Boolean(slots?.trim());
            this.minimum.disabled = minimumField.hidden;
            this.rows.forEach((row) => this.syncDay(row));
            this.syncOther();
        }

        validate() {
            if (this.other.checked && !this.otherInput.disabled && !this.otherInput.value.trim()) {
                this.otherInput.setCustomValidity('Specify the other amenity or service.');
                this.otherInput.reportValidity();
                return false;
            }
            if (!this.minimum.disabled && !this.minimum.reportValidity()) return false;
            if (this.schedule.closest('[data-facility-field]').hidden) return true;
            const active = this.rows.filter((row) => row.active.checked);
            if (!active.length) {
                const checkbox = this.rows[0].active;
                checkbox.setCustomValidity('Select at least one operating day.');
                checkbox.reportValidity();
                return false;
            }
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
