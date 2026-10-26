// GET filtering keeps Django authoritative and preserves URLs/back navigation.
document.querySelectorAll('[data-auto-filters]').forEach(form => {
    const program = form.querySelector('[data-program-select]');
    const major = form.querySelector('[data-major-select]');
    const syncMajor = () => {
        const available = Array.from(major.options).filter(option => option.dataset.program === program.value);
        Array.from(major.options).forEach(option => {
            if (!option.value) return;
            option.hidden = option.dataset.program !== program.value;
            option.disabled = option.hidden;
        });
        major.disabled = !available.length;
        if (major.disabled || major.selectedOptions[0]?.disabled) major.value = '';
    };
    syncMajor();
    let timer;
    const submit = () => { clearTimeout(timer); form.requestSubmit(); };
    form.querySelectorAll('select').forEach(select => select.addEventListener('change', () => {
        if (select === program) { major.value = ''; syncMajor(); }
        submit();
    }));
    form.querySelector('[type="search"]')?.addEventListener('input', () => {
        clearTimeout(timer); timer = setTimeout(submit, 300);
    });
});
document.addEventListener('click', event => {
    document.querySelectorAll('.inventory-actions-menu[open]').forEach(menu => {
        if (!menu.contains(event.target)) menu.open = false;
    });
});
document.addEventListener('keydown', event => {
    if (event.key === 'Escape') document.querySelectorAll('.inventory-actions-menu[open]').forEach(menu => {
        menu.open = false; menu.querySelector('summary')?.focus();
    });
});
