// A major belongs to one program; labels come from Django master records.
window.CampusHubAcademic = {
    sync(program, major) {
        if (!program || !major) return;
        let available = 0;
        Array.from(major.options).forEach(option => {
            if (!option.value) return;
            option.hidden = option.dataset.program !== program.value;
            option.disabled = option.hidden;
            if (!option.hidden) available += 1;
        });
        major.disabled = available === 0;
        major.required = available > 0 && major.dataset.required === 'true';
        if (major.disabled || major.selectedOptions[0]?.disabled) major.value = '';
    }
};
document.querySelectorAll('[data-academic-pair]').forEach(pair => {
    const program = pair.querySelector('[data-program-select]');
    const major = pair.querySelector('[data-major-select]');
    window.CampusHubAcademic.sync(program, major);
    program?.addEventListener('change', () => window.CampusHubAcademic.sync(program, major));
});
