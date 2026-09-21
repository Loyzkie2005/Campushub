document.addEventListener("click", (event) => {
    const closeNotificationMoreMenus = () => {
        document.querySelectorAll(".notification-more-menu.is-open").forEach((menu) => {
            menu.classList.remove("is-open");
        });

        document.querySelectorAll(".notification-more-btn.is-open").forEach((button) => {
            button.classList.remove("is-open");
        });
    };

    const moreButton = event.target.closest("[data-notification-more]");

    if (moreButton) {
        event.stopPropagation();

        const item = moreButton.closest(".notification-menu-item");
        const menu = item?.querySelector(".notification-more-menu");

        document.querySelectorAll(".notification-more-menu.is-open").forEach((openMenu) => {
            if (openMenu !== menu) {
                openMenu.classList.remove("is-open");
            }
        });

        document.querySelectorAll(".notification-more-btn.is-open").forEach((openButton) => {
            if (openButton !== moreButton) {
                openButton.classList.remove("is-open");
            }
        });

        menu?.classList.toggle("is-open");
        moreButton.classList.toggle("is-open");
        return;
    }

    const markSeenButton = event.target.closest("[data-mark-seen]");

    if (markSeenButton) {
        event.stopPropagation();

        const item = markSeenButton.closest(".notification-menu-item");
        const dropdown = markSeenButton.closest(".notification-menu");
        const activeFilter = dropdown?.querySelector("[data-notification-filter].active")?.dataset.notificationFilter;

        item?.classList.remove("is-unseen");
        item?.classList.add("is-seen");
        item?.querySelector(".notification-more-menu")?.classList.remove("is-open");
        item?.querySelector(".notification-more-btn")?.classList.remove("is-open");

        if ((activeFilter === "unseen" || activeFilter === "unread") && item) {
            item.hidden = true;
        }

        return;
    }

    const filterButton = event.target.closest("[data-notification-filter]");

    if (!filterButton) {
        const pageFilterButton = event.target.closest("[data-page-notification-filter]");

        if (pageFilterButton) {
            event.preventDefault();

            const pageList = document.querySelector("[data-page-notification-list]");
            const filterButtons = document.querySelectorAll("[data-page-notification-filter]");
            const notificationItems = pageList?.querySelectorAll(".notification-row") || [];
            const filter = pageFilterButton.dataset.pageNotificationFilter;

            filterButtons.forEach((button) => {
                button.classList.toggle("active", button === pageFilterButton);
            });

            notificationItems.forEach((item) => {
                const category = item.dataset.notificationCategory || "system";
                item.hidden = filter !== "all" && category !== filter;
            });

            return;
        }

        const pageMarkAllButton = event.target.closest("[data-page-mark-all-read]");

        if (pageMarkAllButton) {
            event.preventDefault();
            document.querySelectorAll(".notification-row.is-unseen").forEach((item) => {
                item.classList.remove("is-unseen");
                item.classList.add("is-seen");
            });
            return;
        }

        const pageClearAllButton = event.target.closest("[data-page-clear-all]");

        if (pageClearAllButton) {
            event.preventDefault();
            document.querySelectorAll(".notification-row").forEach((item) => {
                item.hidden = true;
            });
            return;
        }

        const pageFilterToggle = event.target.closest("[data-page-filter-toggle]");

        if (pageFilterToggle) {
            event.preventDefault();
            event.stopPropagation();
            const menu = document.querySelector("[data-page-filter-menu]");
            const isOpen = menu?.classList.toggle("is-open");
            pageFilterToggle.setAttribute("aria-expanded", String(Boolean(isOpen)));
            return;
        }

        const pageCategoryInput = event.target.closest('input[name="pageNotificationCategory"]');

        if (pageCategoryInput) {
            const selected = new Set(
                [...document.querySelectorAll('input[name="pageNotificationCategory"]:checked')].map((input) => input.value)
            );
            document.querySelectorAll(".notification-row").forEach((item) => {
                const category = item.dataset.notificationCategory || "system";
                item.hidden = !selected.has(category);
            });
            return;
        }

        const chatFilterButton = event.target.closest("[data-chat-filter]");

        if (!chatFilterButton) {
            closeNotificationMoreMenus();
            document.querySelector("[data-page-filter-menu]")?.classList.remove("is-open");
            return;
        }

        event.stopPropagation();

        const chatDropdown = chatFilterButton.closest(".chat-header-menu");

        if (!chatDropdown) {
            return;
        }

        const filter = chatFilterButton.dataset.chatFilter;
        const filterButtons = chatDropdown.querySelectorAll("[data-chat-filter]");
        const chatItems = chatDropdown.querySelectorAll(".chat-header-item");

        filterButtons.forEach((button) => {
            button.classList.toggle("active", button === chatFilterButton);
        });

        chatItems.forEach((item) => {
            item.hidden = filter === "unseen" && !item.classList.contains("is-unseen");
        });

        return;
    }

    event.stopPropagation();
    closeNotificationMoreMenus();

    const dropdown = filterButton.closest(".notification-menu");

    if (!dropdown) {
        return;
    }

    const filter = filterButton.dataset.notificationFilter;
    const filterButtons = dropdown.querySelectorAll("[data-notification-filter]");
    const notificationItems = dropdown.querySelectorAll(".notification-menu-item");

    filterButtons.forEach((button) => {
        button.classList.toggle("active", button === filterButton);
    });

    notificationItems.forEach((item) => {
        item.hidden = (filter === "unseen" || filter === "unread") && !item.classList.contains("is-unseen");
    });
});



