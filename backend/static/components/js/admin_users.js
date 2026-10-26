document.addEventListener('DOMContentLoaded', () => {
    const rows = JSON.parse(document.getElementById('usersData').textContent);
    const byRef = Object.fromEntries(rows.map(user => [user.ref, user]));
    // Keep menus outside the scrolling table so the last rows are not clipped.
    document.querySelectorAll('.user-actions .dropdown').forEach(container => {
        const toggle = container.querySelector('[data-bs-toggle="dropdown"]'), menu = container.querySelector('.dropdown-menu');
        container.addEventListener('show.bs.dropdown', () => {
            // Bootstrap's delegated keyboard lookup assumes menu/toggle siblings.
            // A floating menu uses our local keyboard handler instead.
            menu.classList.remove('dropdown-menu'); menu.classList.add('user-action-menu-floating');
            document.body.append(menu);
        });
        container.addEventListener('hidden.bs.dropdown', () => {
            menu.classList.remove('user-action-menu-floating'); menu.classList.add('dropdown-menu'); container.append(menu);
        });
        menu.addEventListener('keydown', event => {
            if (!['ArrowDown', 'ArrowUp', 'Escape', 'Home', 'End'].includes(event.key)) return;
            event.preventDefault(); event.stopPropagation();
            if (event.key === 'Escape') { bootstrap.Dropdown.getInstance(toggle)?.hide(); toggle.focus(); return; }
            const items = [...menu.querySelectorAll('.dropdown-item')].filter(item => !item.disabled);
            const current = items.indexOf(document.activeElement);
            const next = event.key === 'Home' ? 0 : event.key === 'End' ? items.length - 1 : Math.max(0, Math.min(items.length - 1, current + (event.key === 'ArrowDown' ? 1 : -1)));
            items[next]?.focus();
        });
        container.closest('.users-table-scroll').addEventListener('scroll', () => bootstrap.Dropdown.getInstance(toggle)?.hide());
    });
    const filters = document.getElementById('userFilters');
    let timer;
    function syncFilterMajor() {
        const major = filters.elements.major;
        window.CampusHubAcademic.sync(filters.elements.department, major);
        document.getElementById('majorFilterGroup').hidden = major.disabled;
    }
    function submitFilters() { clearTimeout(timer); filters.requestSubmit(); }
    filters.addEventListener('submit', () => clearTimeout(timer));
    filters.querySelectorAll('select').forEach(select => select.addEventListener('change', () => { syncFilterMajor(); submitFilters(); }));
    filters.elements.q.addEventListener('input', () => { clearTimeout(timer); timer = setTimeout(submitFilters, 350); });
    document.querySelectorAll('.sort-button').forEach(button => button.addEventListener('click', () => {
        filters.elements.dir.value = filters.elements.sort.value === button.dataset.sort && filters.elements.dir.value === 'asc' ? 'desc' : 'asc';
        filters.elements.sort.value = button.dataset.sort; submitFilters();
    }));
    syncFilterMajor();

    const form = document.getElementById('userForm');
    function formatDate(value) {
        return value ? new Intl.DateTimeFormat('en-US', {timeZone:'Asia/Manila', month:'short', day:'numeric', year:'numeric', hour:'numeric', minute:'2-digit'}).format(new Date(value)) : '—';
    }
    function appendField(parent, label, value) {
        const row = document.createElement('div'), dt = document.createElement('dt'), dd = document.createElement('dd');
        dt.textContent = label; dd.textContent = value || '—'; row.append(dt, dd); parent.append(row);
    }
    if (form) {
    const role = form.elements.role, program = form.elements.department, major = form.elements.major;
    const editor = bootstrap.Modal.getOrCreateInstance(document.getElementById('userEditor'));
    let editing = null;
    function syncAcademic() {
        const global = form.elements.account_type.value === 'admin' && ['super admin', 'facilities admin'].includes(role.value.toLowerCase());
        const meaningful = !global && form.elements.account_type.value !== 'guest';
        const legacy = editing && !editing.department_id;
        const required = role.value.toLowerCase() === 'marketplace admin' || (form.elements.account_type.value === 'student' && !legacy);
        document.getElementById('departmentGroup').hidden = !meaningful;
        program.disabled = !meaningful; program.required = meaningful && required;
        if (!meaningful) { program.value = ''; major.value = ''; }
        window.CampusHubAcademic.sync(program, major);
        document.getElementById('majorGroup').hidden = !meaningful || major.disabled;
        major.required = meaningful && !major.disabled;
        document.getElementById('programRequired').hidden = !program.required;
        document.getElementById('legacyAcademicNotice').hidden = !(meaningful && legacy && !program.value);
    }
    function roleOptions() {
        const admin = form.elements.account_type.value === 'admin';
        Array.from(role.options).forEach(option => {
            const unavailable = (option.dataset.admin === 'true') !== admin || (!editing && !['super admin', 'facilities admin', 'marketplace admin'].includes(option.value.toLowerCase()));
            option.hidden = unavailable; option.disabled = unavailable;
        });
        if (!role.selectedOptions.length || role.selectedOptions[0].disabled) role.value = Array.from(role.options).find(option => !option.disabled)?.value || '';
    }
    function resetEditor() {
        editing = null; form.reset();
        [form.elements.password, form.elements.confirm_password].forEach(input => {input.disabled = false; input.closest('.col-12').hidden = false;}); form.elements.account_ref.value = ''; form.elements.account_type.value = 'admin';
        form.querySelectorAll('input[type="text"], input:not([type])').forEach(input => input.value = '');
        form.querySelectorAll('[data-password-toggle]').forEach(button => {
            document.getElementById(button.dataset.passwordToggle).type = 'password'; button.textContent = 'Show'; button.setAttribute('aria-pressed', 'false');
        });
        document.getElementById('userEditorTitle').textContent = 'Add Administrator';
        document.getElementById('userEditorSubtitle').textContent = 'Create a new administrator account and assign the appropriate system role.';
        document.getElementById('saveUserButton').textContent = 'Create Admin';
        document.getElementById('saveUserButton').disabled = false;
        form.elements.password.required = true; form.elements.confirm_password.required = true;
        document.querySelectorAll('.password-required').forEach(node => node.hidden = false);
        roleOptions(); syncAcademic(); validatePasswordUI();
    }
    document.querySelector('[data-mode="add"]')?.addEventListener('click', resetEditor);
    role.addEventListener('change', syncAcademic); program.addEventListener('change', syncAcademic);
    document.querySelectorAll('.edit-user').forEach(button => button.addEventListener('click', () => {
        const user = byRef[button.dataset.userRef]; if (!user?.can_manage) return;
        resetEditor(); editing = user;
        form.elements.account_ref.value = user.ref; form.elements.account_type.value = user.account_type;
        ['first_name', 'last_name', 'username', 'email', 'contact_number'].forEach(name => form.elements[name].value = user[name] || '');
        roleOptions(); role.value = user.role;
        program.value = user.department_id || ''; window.CampusHubAcademic.sync(program, major); major.value = user.major_id || '';
        form.elements.is_active.checked = user.status === 'active';
        [form.elements.password, form.elements.confirm_password].forEach(input => {input.required = false; input.disabled = true; input.closest('.col-12').hidden = true;});
        document.querySelectorAll('.password-required').forEach(node => node.hidden = true);
        document.getElementById('userEditorTitle').textContent = 'Edit User';
        document.getElementById('userEditorSubtitle').textContent = 'Update account details and system access.';
        document.getElementById('saveUserButton').textContent = 'Save Changes'; syncAcademic(); editor.show();
    }));

    const password = form.elements.password, confirmation = form.elements.confirm_password;
    function validatePasswordUI() {
        const value = password.value, rules = {length:value.length>=8, case:/[A-Z]/.test(value)&&/[a-z]/.test(value), number:/\d/.test(value), special:/[^A-Za-z0-9\s]/.test(value), spaces:!!value&&!/\s/.test(value)};
        document.getElementById('passwordRules').hidden = !value;
        Object.entries(rules).forEach(([name,valid]) => document.querySelector(`[data-rule="${name}"]`).classList.toggle('valid',valid));
        const mismatch = confirmation.value && password.value !== confirmation.value;
        confirmation.setCustomValidity(mismatch ? 'Passwords do not match.' : ''); document.getElementById('passwordMatch').textContent = mismatch ? 'Passwords do not match.' : '';
    }
    password.addEventListener('input',validatePasswordUI); confirmation.addEventListener('input',validatePasswordUI);
    form.addEventListener('submit',event => { validatePasswordUI(); if (!form.checkValidity()) {event.preventDefault(); form.reportValidity(); return;} document.getElementById('saveUserButton').disabled = true; document.getElementById('saveUserButton').textContent = 'Saving…'; });
    resetEditor();
    }
    const viewerElement = document.getElementById('userViewer');
    const viewer = bootstrap.Offcanvas.getOrCreateInstance(viewerElement);
    let viewReturnFocus = null;
    viewerElement.addEventListener('hidden.bs.offcanvas', () => {
        if (viewReturnFocus) {
            viewReturnFocus.focus();
            viewReturnFocus = null;
        }
    });

    document.querySelectorAll('.view-user').forEach(button => button.addEventListener('click', () => {
        const user = byRef[button.dataset.userRef]; if (!user) return;
        viewReturnFocus = button;
        document.getElementById('viewInitials').textContent = user.initials;
        document.getElementById('viewFullName').textContent = user.full_name;
        document.getElementById('viewEmail').textContent = user.email;

        // Visual badges
        const badgesContainer = document.getElementById('viewBadges');
        if (badgesContainer) {
            badgesContainer.replaceChildren();
            const typePill = document.createElement('span');
            typePill.className = `type-badge type-${user.account_type}`;
            typePill.textContent = user.account_type_label;
            const statusPill = document.createElement('span');
            statusPill.className = `status-badge status-${user.status}`;
            statusPill.innerHTML = `<i></i>${user.status_label}`;
            badgesContainer.append(typePill, statusPill);
            if (user.account_type !== 'admin' && user.seller_access && user.seller_access !== 'not_applied') {
                const sellerPill = document.createElement('span');
                sellerPill.className = `seller-badge seller-${user.seller_access}`;
                sellerPill.textContent = user.seller_access_label;
                badgesContainer.append(sellerPill);
            }
        }

        // Section 1: Account Information
        const accountList = document.getElementById('accountInfoList');
        if (accountList) {
            accountList.replaceChildren();
            const accountFields = [
                ['Full Name', user.full_name],
                ['Email', user.email],
                [user.account_type === 'guest' ? 'Username' : 'Username / School ID', user.username],
                ['Account Type', user.account_type_label],
                ['Assigned Role', user.role],
                ['Account Status', user.status_label],
                ['Date Registered', formatDate(user.date_joined)],
                ['Last Login', user.last_login ? formatDate(user.last_login) : 'Never']
            ];
            accountFields.forEach(([l, v]) => appendField(accountList, l, v));
        }

        // Section 2: Academic Information
        const academicList = document.getElementById('academicInfoList');
        if (academicList) {
            academicList.replaceChildren();
            const isStudent = user.account_type === 'student';
            const isFaculty = user.account_type === 'faculty';
            const isAcademic = isStudent || isFaculty || (user.department_id && user.account_type !== 'guest');

            const studentIdVal = user.student_id ? user.student_id : (isStudent ? 'Not recorded' : 'Not applicable');
            const programVal = (user.program && user.program !== '—') ? user.program : (isAcademic ? 'Not recorded' : 'Not applicable');
            const majorVal = user.major ? user.major : (user.program === 'BTLED' ? 'Unassigned' : (isAcademic ? 'Not recorded' : 'Not applicable'));
            const yearLevelVal = user.year_level ? user.year_level : (isStudent ? (user.year_section || 'Not recorded') : 'Not applicable');
            const sectionVal = user.section ? user.section : (isStudent ? 'Not recorded' : 'Not applicable');

            const academicFields = [
                ['Student ID', studentIdVal],
                ['Program', programVal],
                ['Major', majorVal],
                ['Year Level', yearLevelVal],
                ['Section', sectionVal]
            ];
            academicFields.forEach(([l, v]) => appendField(academicList, l, v));
        }

        // Section 3: Seller Information
        const sellerList = document.getElementById('sellerInfoList');
        if (sellerList) {
            sellerList.replaceChildren();
            const isSellerCandidate = user.account_type !== 'admin';
            const sellerAccessVal = isSellerCandidate ? user.seller_access_label : 'Not applicable';
            const appStatusVal = isSellerCandidate ? ((user.seller_application && user.seller_application !== '—') ? user.seller_application : 'Not submitted') : 'Not applicable';
            const approvalDateVal = user.seller_approved_at ? formatDate(user.seller_approved_at) : (user.seller_access === 'approved' ? 'Not recorded' : 'Not applicable');

            const sellerFields = [
                ['Seller Access Status', sellerAccessVal],
                ['Application Status', appStatusVal],
                ['Seller Approval Date', approvalDateVal]
            ];
            if (user.seller_applied_at) {
                sellerFields.push(['Application Date', formatDate(user.seller_applied_at)]);
            }
            if (user.seller_product_type) {
                sellerFields.push(['Product Line', user.seller_product_type]);
            }
            sellerFields.forEach(([l, v]) => appendField(sellerList, l, v));
        }

        // Section 4: Additional Information
        const additionalList = document.getElementById('additionalInfoList');
        if (additionalList) {
            additionalList.replaceChildren();
            const additionalFields = [
                ['Contact Number', user.contact_number || 'Not recorded'],
                ['Email Verification', user.email_verification_label || (user.email_verified ? 'Verified' : 'Email not verified')]
            ];
            if (user.scope) {
                const scopeLabel = user.scope === 'All Modules' ? 'System Scope' : 'Facility Scope';
                additionalFields.push([scopeLabel, user.scope]);
            } else if (user.is_administrator) {
                additionalFields.push(['Scope', 'Administrator Access']);
            }
            if (user.is_administrator && user.recovery_method) {
                additionalFields.push(['Recovery Method', user.recovery_method]);
            }
            additionalFields.forEach(([l, v]) => appendField(additionalList, l, v));
        }

        // Section 5: Recent Activity
        const activity = document.getElementById('userActivityList');
        if (activity) {
            activity.replaceChildren();
            if (!user.activities.length) {
                const item = document.createElement('li');
                item.textContent = 'No recent activity available.';
                activity.append(item);
            }
            user.activities.forEach(event => {
                const li = document.createElement('li'), small = document.createElement('small');
                li.textContent = event.activity;
                small.textContent = formatDate(event.date);
                li.append(small);
                activity.append(li);
            });
        }
        const activityLink = document.getElementById('viewAllUserActivity');
        if (activityLink) {
            activityLink.hidden = !user.activity_url;
            if (user.activity_url) activityLink.href = user.activity_url;
            else activityLink.removeAttribute('href');
        }

        viewer.show();
    }));
    document.querySelectorAll('.account-action').forEach(button => button.addEventListener('click', () => {
        if (!confirm(`Confirm ${button.dataset.action === 'activate' ? 'reactivation' : 'deactivation'} of this account? History will be preserved.`)) return;
        const quick = document.getElementById('quickActionForm'); quick.elements.account_ref.value = button.dataset.ref; quick.elements.action.value = button.dataset.action; quick.requestSubmit();
    }));
    const recoveryModal = document.getElementById('accountRecoveryModal');
    let recoveryReturnFocus;
    recoveryModal.addEventListener('hidden.bs.modal', () => recoveryReturnFocus?.focus());
    document.querySelectorAll('.assist-recovery').forEach(button => {
        // Capture before the dropdown menu is moved outside the table.
        const returnFocus = button.closest('tr')?.querySelector('.more-action');
        button.addEventListener('click', () => {
            const user = byRef[button.dataset.ref]; if (!user?.can_assist_recovery || user.is_administrator) return;
            recoveryReturnFocus = returnFocus;
            const details = document.getElementById('recoveryAccountDetails'); details.replaceChildren();
            appendField(details, 'User', user.full_name); appendField(details, 'Username / School ID', user.username);
            if (user.program_major && user.program_major !== '\u2014') appendField(details, 'Program / Major', user.program_major);
            const methods = document.getElementById('recoveryMethods'); methods.replaceChildren();
            appendField(methods, 'Email', `${user.masked_email || 'Not recorded'} \u00b7 ${user.email_verified ? 'Verified' : 'Not Verified'}`);
            appendField(methods, 'SMS', `${user.masked_phone} \u00b7 ${user.sms_verified ? 'Verified' : 'Not Verified'}`);
            const verified = Boolean(user.email_verified || (user.sms_recovery_available && user.sms_verified));
            const notice = document.getElementById('recoveryNotice');
            notice.textContent = verified ? 'Use a verified recovery method to continue.' : 'No verified recovery method is currently available for this account.';
            notice.classList.toggle('recovery-notice', !verified);
            document.getElementById('recoveryReferral').hidden = verified || !user.recovery_referral;
            bootstrap.Modal.getOrCreateInstance(recoveryModal).show();
        });
    });
    document.querySelectorAll('.seller-access').forEach(button => button.addEventListener('click', () => {
        const modal = document.getElementById('sellerAccessModal');
        modal.querySelector('.modal-account-ref').value = button.dataset.ref; modal.querySelector('.modal-user-name').textContent = button.dataset.name;
        const restore = button.dataset.status === 'suspended';
        document.getElementById('sellerStatus').value = restore ? 'approved' : 'suspended';
        document.getElementById('restoreSellerFlag').value = restore ? '1' : '';
        document.getElementById('sellerAccessTitle').textContent = restore ? 'Restore Seller Access' : 'Suspend Seller Access';
        document.getElementById('sellerAccessMessage').textContent = restore ? 'Restore this user’s approved marketplace access?' : 'Suspend this user’s marketplace access?';
        bootstrap.Modal.getOrCreateInstance(modal).show();
    }));
    document.querySelectorAll('.users-modal input[type="password"]').forEach(input => {
        const wrapper = document.createElement('div'), toggle = document.createElement('button'); wrapper.className = 'users-password-field'; input.before(wrapper); wrapper.append(input);
        toggle.type = 'button'; toggle.dataset.passwordToggle = input.id; toggle.textContent = 'Show'; toggle.setAttribute('aria-label', `Show or hide ${input.name.replaceAll('_',' ')}`); toggle.setAttribute('aria-pressed','false');
        toggle.addEventListener('click', () => { const show = input.type === 'password'; input.type = show ? 'text' : 'password'; toggle.textContent = show ? 'Hide' : 'Show'; toggle.setAttribute('aria-pressed', String(show)); }); wrapper.append(toggle);
    });
    document.querySelectorAll('.campushub-toast').forEach(toast => setTimeout(() => toast.classList.remove('show'),5000));
});
