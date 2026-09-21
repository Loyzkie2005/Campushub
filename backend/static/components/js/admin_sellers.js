document.addEventListener("DOMContentLoaded", function () {
    document.querySelectorAll(".js-reject-seller").forEach(function (form) {
        form.addEventListener("submit", function (event) {
            const reason = window.prompt("Enter the reason for rejecting this seller request:");
            if (!reason || !reason.trim()) {
                event.preventDefault();
                return;
            }
            form.querySelector("[name='rejection_reason']").value = reason.trim();
        });
    });
});
