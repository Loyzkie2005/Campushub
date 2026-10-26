/* Owner UI only. The existing Django code service authorizes every step. */
(() => {
    const root = document.getElementById('ownerRecovery');
    if (!root) return;
    const identify = document.getElementById('ownerIdentify'), verify = document.getElementById('ownerVerify');
    const password = document.getElementById('ownerPassword'), complete = document.getElementById('ownerComplete');
    const heading = document.getElementById('recoveryHeading'), notice = document.getElementById('ownerNotice');
    const boxes = [...verify.querySelectorAll('.code-boxes input')], resend = document.getElementById('ownerResend');
    let email = '', purpose = 'password', grant = '', busy = false, cooldown = 0, timer;
    const masked = value => { const [local, domain] = value.split('@'); return `${local.slice(0, 2)}***@${domain}`; };
    const message = value => { notice.textContent = value; notice.focus(); };
    const show = (form, title) => {
        [identify, verify, password, complete].forEach(element => { element.hidden = element !== form; });
        heading.textContent = title;
        notice.textContent = '';
        form.querySelector('input, select')?.focus();
    };
    const updateButtons = () => {
        root.setAttribute('aria-busy', String(busy));
        root.querySelectorAll('button').forEach(button => { button.disabled = busy; });
        resend.disabled = busy || cooldown > 0;
        resend.textContent = cooldown > 0 ? `Resend Code (${cooldown}s)` : 'Resend Code';
    };
    const startCooldown = seconds => {
        clearInterval(timer); cooldown = seconds; updateButtons();
        timer = setInterval(() => { cooldown = Math.max(0, cooldown - 1); updateButtons(); if (!cooldown) clearInterval(timer); }, 1000);
    };
    async function post(url, payload) {
        const response = await fetch(url, { method: 'POST', credentials: 'omit',
            headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' }, body: JSON.stringify(payload) });
        if (!(response.headers.get('content-type') || '').includes('application/json')) throw new Error('Unable to continue recovery. Please try again.');
        const result = await response.json();
        if (!response.ok) throw new Error(result.error || 'Unable to continue recovery.');
        return result;
    }
    async function run(action) {
        if (busy) return;
        busy = true; updateButtons(); notice.textContent = 'Please wait...';
        try { await action(); } catch (error) { message(error.message || 'Unable to continue recovery. Please try again.'); }
        finally { busy = false; updateButtons(); }
    }
    const clearCode = () => boxes.forEach(box => { box.value = ''; });
    const identifyAccount = () => {
        if (!identify.reportValidity()) return false;
        email = document.getElementById('ownerEmail').value.trim().toLowerCase();
        purpose = document.getElementById('ownerPurpose').value; grant = '';
        return true;
    };
    const openCode = () => {
        clearCode(); document.getElementById('ownerMaskedEmail').textContent = masked(email);
        show(verify, 'Verify Your Account');
    };
    identify.addEventListener('submit', event => {
        event.preventDefault(); if (!identifyAccount()) return;
        run(async () => { const result = await post(root.dataset.sendUrl, { email, purpose });
            openCode(); startCooldown(result.resend_after || 60); message(result.message); });
    });
    document.getElementById('ownerExistingCode').addEventListener('click', () => { if (identifyAccount()) openCode(); });
    resend.addEventListener('click', () => {
        if (cooldown > 0) return;
        run(async () => { const result = await post(root.dataset.sendUrl, { email, purpose });
            grant = ''; clearCode(); startCooldown(result.resend_after || 60); message(result.message); boxes[0].focus(); });
    });
    document.getElementById('ownerChange').addEventListener('click', () => { grant = ''; clearCode(); show(identify, 'Account Recovery'); });
    boxes.forEach((box, index) => {
        box.addEventListener('input', () => {
            const digits = box.value.replace(/[^0-9]/g, '');
            if (digits.length > 1) {
                const start = digits.length === 6 ? 0 : index;
                [...digits].forEach((digit, offset) => { if (boxes[start + offset]) boxes[start + offset].value = digit; });
                boxes[Math.min(5, start + digits.length)].focus();
            } else { box.value = digits; if (digits && index < 5) boxes[index + 1].focus(); }
        });
        box.addEventListener('keydown', event => {
            if (event.key === 'Backspace' && !box.value && index > 0) { event.preventDefault(); boxes[index - 1].value = ''; boxes[index - 1].focus(); }
        });
    });
    verify.addEventListener('submit', event => {
        event.preventDefault();
        const code = boxes.map(box => box.value).join('');
        if (!/^[0-9]{6}$/.test(code)) { message('Enter the 6-digit verification code.'); return; }
        run(async () => {
            const result = await post(root.dataset.verifyUrl, { email, purpose, code }); clearCode();
            if (purpose === 'password') {
                if (!result.recovery_grant) throw new Error('Unable to continue recovery. Request a new code.');
                grant = result.recovery_grant; show(password, 'Create New Password');
            } else {
                show(complete, purpose === 'username' ? 'Username Recovered' : 'Email Verified');
                document.getElementById('ownerCompletedMessage').textContent = result.message;
                const username = document.getElementById('ownerUsername');
                username.hidden = purpose !== 'username'; username.textContent = purpose === 'username' ? `Username / School ID: ${result.username}` : '';
            }
        });
    });
    password.addEventListener('submit', event => {
        event.preventDefault();
        const value = document.getElementById('ownerNewPassword').value, confirmation = document.getElementById('ownerConfirmPassword').value;
        if (!grant || !password.reportValidity()) return;
        if (value !== confirmation) { message('Passwords do not match.'); return; }
        run(async () => { await post(root.dataset.confirmUrl, { email, recovery_grant: grant, new_password: value, confirm_password: confirmation });
            grant = ''; password.reset(); show(complete, 'Password Updated Successfully');
            document.getElementById('ownerCompletedMessage').textContent = 'Your password has been changed.'; });
    });
    root.querySelectorAll('.password-visibility').forEach(button => button.addEventListener('click', () => {
        const input = document.getElementById(button.dataset.input), visible = input.type === 'password';
        input.type = visible ? 'text' : 'password'; button.setAttribute('aria-pressed', String(visible));
        button.textContent = `${visible ? 'Hide' : 'Show'} ${button.dataset.input === 'ownerNewPassword' ? 'new password' : 'confirmation'}`;
    }));
})();
