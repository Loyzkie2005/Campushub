/* Staged role information -> permissions -> administrator assignment. */
(function () {
    "use strict";
    document.addEventListener("DOMContentLoaded", function () {
        const page = document.querySelector(".roles-page");
        if (!page) return;
        const byId = new Map(JSON.parse(document.getElementById("rolesData").textContent).map(role => [role.id, role]));
        const $ = id => document.getElementById(id);
        const panel = $("rolePermissionPanel"), form = $("permissionPanelForm");
        const checks = Array.from(document.querySelectorAll(".js-panel-permission"));
        const save = $("permissionPanelSaveButton"), assign = $("permissionPanelAssignButton");
        const infoForm = $("roleForm"), assignmentForm = $("assignAdminForm");
        const infoModal = bootstrap.Modal.getOrCreateInstance($("roleFormModal"));
        const assignmentModal = bootstrap.Modal.getOrCreateInstance($("assignAdminModal"));
        const usersModal = bootstrap.Modal.getOrCreateInstance($("viewRoleModal"));
        let current = null, mode = "view", saved = "", opener = null, timer = 0;
        const historyModal = bootstrap.Modal.getOrCreateInstance($("roleHistoryModal"));
        const statusModal = bootstrap.Modal.getOrCreateInstance($("roleStatusModal"));
        const roleTriggers = new Map();
        const permissionDependencies = JSON.parse($("permissionDependenciesData").textContent);
        let modalOpener = null, statusRole = null, statusAction = "", historyRole = null, historyPage = 1, historyRequest = 0;
        document.querySelectorAll('.role-row-actions.dropdown').forEach(container => {
            const toggle = container.querySelector('.role-more-toggle'), menu = container.querySelector('.role-more-menu');
            roleTriggers.set(toggle.dataset.roleId, toggle);
            container.addEventListener('show.bs.dropdown', () => {
                // Match the Users menu: Popper positions outside the scroll container.
                menu.classList.remove('dropdown-menu'); menu.classList.add('is-floating'); document.body.append(menu);
            });
            container.addEventListener('hidden.bs.dropdown', () => {
                menu.classList.remove('is-floating'); menu.classList.add('dropdown-menu'); container.append(menu);
            });
            menu.addEventListener('keydown', event => {
                if (!['ArrowDown', 'ArrowUp', 'Home', 'End', 'Escape'].includes(event.key)) return;
                event.preventDefault(); event.stopPropagation();
                if (event.key === 'Escape') { bootstrap.Dropdown.getInstance(toggle)?.hide(); toggle.focus(); return; }
                const items = [...menu.querySelectorAll('.dropdown-item')].filter(item => !item.disabled && !item.closest('li').hidden);
                const currentIndex = items.indexOf(document.activeElement);
                const next = event.key === 'Home' ? 0 : event.key === 'End' ? items.length - 1 : Math.max(0, Math.min(items.length - 1, currentIndex + (event.key === 'ArrowDown' ? 1 : -1)));
                items[next]?.focus();
            });
            container.closest('.roles-table-wrap').addEventListener('scroll', () => bootstrap.Dropdown.getInstance(toggle)?.hide());
        });
        ['roleFormModal', 'assignAdminModal', 'viewRoleModal', 'roleStatusModal', 'roleHistoryModal'].forEach(id => {
            $(id).addEventListener('hidden.bs.modal', () => modalOpener?.focus());
        });
        $("roleHistoryModal").addEventListener('hidden.bs.modal', () => { historyRequest += 1; });
        const outside = new Map();
        function isolatePanel() {
            let node = panel;
            while (node.parentElement && node !== document.body) {
                for (const sibling of node.parentElement.children) {
                    if (sibling !== node && !sibling.dataset.adminAlertRegion) { outside.set(sibling, sibling.inert); sibling.inert = true; }
                }
                node = node.parentElement;
            }
        }
        const signature = values => [...values].sort().join("|");
        const selected = () => checks.filter(c => c.checked).map(c => c.value);
        function toast(message, type='info') {
            window.CampusHubAlerts?.show(message,{type});
            if (!panel.hidden) {
                $("permissionPanelFeedback").textContent = message;
                $("permissionPanelFeedback").hidden = false;
                return;
            }
            if (window.CampusHubAlerts) return;
            const node = $("rolesToast"); node.textContent = message;
            node.classList.add("is-visible"); clearTimeout(timer);
            timer = setTimeout(() => node.classList.remove("is-visible"), 4500);
        }
        function error(id, message = "") { $(id).textContent = message; $(id).hidden = !message; }
        async function post(url, data) {
            const result = await fetch(url, {method: "POST", body: data, credentials: "same-origin", headers: {"X-Requested-With": "XMLHttpRequest"}});
            let payload;
            try { payload = await result.json(); } catch (_) { throw new Error("Unable to save. Your session may have expired; refresh and try again."); }
            if (!result.ok || !payload.success) throw new Error(payload.message || "Unable to save. Try again.");
            return payload;
        }
        function remember(role) {
            byId.set(role.id, role);
            const row = Array.from(document.querySelectorAll("[data-role-row]")).find(r => r.dataset.roleRow === role.id);
            if (!row) return;
            row.querySelector(".role-table-name").textContent = role.display_name;
            row.querySelector(".role-user-count").textContent = role.assignment_applicable ? role.user_count : "\u2014";
            row.querySelector(".permission-set-label").textContent = role.permission_summary;
            const status = row.querySelector(".role-status-badge"); status.textContent = role.status_label;
            status.classList.toggle("is-active", role.is_active); status.classList.toggle("is-inactive", !role.is_active);
            const date = row.querySelector(".role-last-updated"); date.textContent = role.updated_date;
            const time = document.createElement("small"); time.textContent = role.updated_time; date.append(time);
            const assignment = row.querySelector(".js-assign-admins"); if (assignment) assignment.closest("li").hidden = !role.can_assign;
            const statusButton = row.querySelector(".js-role-status");
            if (statusButton) { statusButton.dataset.action = role.is_active ? "deactivate" : "activate"; statusButton.textContent = role.is_active ? "Deactivate Role" : "Reactivate Role"; }
        }
        function activateModule(key) {
            document.querySelectorAll(".permission-module-button").forEach(b => { b.classList.toggle("is-active", b.dataset.module === key); b.setAttribute("aria-pressed", String(b.dataset.module === key)); });
            document.querySelectorAll("[data-permission-group]").forEach(g => { g.hidden = g.dataset.permissionGroup !== key; });
        }
        function sync() {
            const editable = mode === "edit" && !current.is_readonly;
            const required = new Set();
            if (editable) {
                checks.filter(c => c.checked).forEach(c => {
                    (permissionDependencies[c.value] || []).forEach(code => {
                        if (current.allowed_permission_codes.includes(code)) required.add(code);
                    });
                });
            }
            checks.forEach(c => {
                const available = current.allowed_permission_codes.includes(c.value);
                if (required.has(c.value)) c.checked = true;
                c.disabled = !editable || !available || required.has(c.value);
                c.closest(".permission-list-row").querySelector(".permission-dependency-note").hidden = !required.has(c.value);
                c.closest(".permission-list-row").classList.toggle("is-outside-scope", !available);
                c.parentElement.querySelector(".permission-readonly-state").textContent = c.checked ? "\u2713 Allowed" : "\u2014";
            });
            panel.classList.toggle("is-readonly", !editable);
            save.hidden = !editable; save.disabled = saved === signature(selected());
            $("permissionPanelCancelButton").hidden = !editable;
            $("permissionPanelCloseButton").hidden = editable;
            assign.hidden = mode !== "edit" || !current.can_assign;
            assign.disabled = saved !== signature(selected());
            const count = selected().length;
            $("permissionPanelCount").textContent = current.role_name.toLowerCase() === "super admin" ? `All ${count} permissions enabled` : `${count} permissions allowed`;
        }
        function closePanel(restore = true) {
            panel.hidden = true; document.body.classList.remove("role-panel-open");
            outside.forEach((value, node) => { node.inert = value; }); outside.clear();
            if (restore && opener?.isConnected) opener.focus();
        }
        function openPanel(role, requestedMode, focus = true, trigger = null) {
            if (!role) return;
            current = role; mode = role.is_readonly ? "view" : requestedMode;
            $("permissionPanelFeedback").hidden = true;
            if (focus) opener = trigger || document.activeElement;
            $("permissionPanelRoleId").value = role.id;
            $("permissionPanelTitle").textContent = role.display_name;
            $("permissionPanelMode").textContent = mode === "edit" ? "Configure Permissions \u00b7 Step 2" : "View Permissions";
            $("permissionPanelDescription").textContent = `${role.is_readonly ? "Protected System Role" : role.role_type} \u00b7 ${role.permission_summary}`;
            checks.forEach(c => { c.checked = role.assigned_permissions.includes(c.value); });
            saved = signature(selected()); $("permissionPanelNote").hidden = role.role_name.toLowerCase() !== "super admin";
            activateModule(document.querySelector(".permission-module-button")?.dataset.module);
            if (panel.hidden) isolatePanel();
            panel.hidden = false; document.body.classList.add("role-panel-open"); sync(); panel.focus();
        }
        function openAssignment(role) {
            if (!role?.can_assign) { toast("Configure permissions and activate this role before assigning administrators."); return; }
            modalOpener = roleTriggers.get(role.id) || opener;
            closePanel(false); assignmentForm.reset(); error("assignmentError");
            $("assignRoleId").value = role.id; $("assignRoleName").textContent = `${role.display_name} \u00b7 Step 3`;
            const members = new Set(role.role_users.map(u => String(u.id)));
            assignmentForm.querySelectorAll("[name=assigned_users]").forEach(c => { c.checked = members.has(c.value); c.disabled = c.dataset.active !== "true" && !c.checked; });
            assignmentModal.show();
        }
        function openInfo(role = null, trigger = null) {
            if (role?.is_protected) return;
            modalOpener = trigger || $("addRoleButton");
            infoForm.reset(); error("roleFormError");
            $("roleFormTitle").textContent = role ? "Edit Role Information" : "Add Custom Role";
            $("roleIdInput").value = role?.id || ""; $("roleNameInput").value = role?.role_name || "";
            $("roleDescInput").value = role?.description || ""; $("roleActiveInput").checked = role ? role.is_active : true;
            infoModal.show();
        }
        async function loadHistory(role, pageNumber = 1) {
            const sequence = ++historyRequest; historyRole = role; historyPage = pageNumber;
            $("roleHistoryList").replaceChildren(); $("roleHistoryState").textContent = "Loading permission history...";
            $("roleHistoryRetry").hidden = true; $("roleHistoryPagination").hidden = true;
            const url = new URL(window.location.href);
            url.searchParams.set('history_role', role.id); url.searchParams.set('history_page', pageNumber);
            try {
                const response = await fetch(url.href, {credentials: 'same-origin', headers: {'X-Requested-With': 'XMLHttpRequest'}});
                if (!response.ok || response.redirected || !(response.headers.get('content-type') || '').includes('application/json')) throw new Error();
                const payload = await response.json();
                if (!Array.isArray(payload.events) || payload.role !== role.id) throw new Error();
                if (sequence !== historyRequest) return;
                $("roleHistoryState").textContent = payload.total ? `${payload.total} recorded role event${payload.total === 1 ? '' : 's'}` : 'No permission history recorded for this role.';
                payload.events.forEach(event => {
                    const row = document.createElement('li'), title = document.createElement('strong'), date = document.createElement('time'), detail = document.createElement('p');
                    title.textContent = event.event; date.textContent = event.date; detail.textContent = event.activity;
                    row.append(title, date, detail); $("roleHistoryList").append(row);
                });
                historyPage = payload.page;
                $("roleHistoryPage").textContent = `Page ${payload.page} of ${payload.pages}`;
                $("roleHistoryPrevious").disabled = !payload.has_previous; $("roleHistoryNext").disabled = !payload.has_next;
                $("roleHistoryPagination").hidden = payload.pages <= 1;
            } catch (_) {
                if (sequence !== historyRequest) return;
                $("roleHistoryState").textContent = 'Unable to load permission history. Refresh if your session has expired.';
                $("roleHistoryRetry").hidden = false;
            }
        }
        $("roleHistoryPrevious").addEventListener('click', () => loadHistory(historyRole, historyPage - 1));
        $("roleHistoryNext").addEventListener('click', () => loadHistory(historyRole, historyPage + 1));
        $("roleHistoryRetry").addEventListener('click', () => loadHistory(historyRole, historyPage));
        $("roleStatusForm").addEventListener('submit', async event => {
            event.preventDefault(); if (!statusRole || statusRole.is_protected) return;
            const button = $("roleStatusConfirm"); if (button.disabled) return;
            button.disabled = true; button.textContent = 'Saving...'; error('roleStatusError');
            const data = new FormData(form); data.set('role_id', statusRole.id); data.set('action', statusAction);
            try { const payload=await post(page.dataset.statusUrl, data); window.CampusHubAlerts?.remember(payload.message); window.location.reload(); }
            catch (e) { error('roleStatusError', e.message); button.disabled = false; button.textContent = statusAction === 'deactivate' ? 'Deactivate Role' : 'Reactivate Role'; }
        });
        $("addRoleButton").addEventListener("click", () => openInfo());
        document.addEventListener("click", async event => {
            const button = event.target.closest("button"); if (!button) return;
            const role = byId.get(button.dataset.roleId), trigger = roleTriggers.get(button.dataset.roleId);
            if (button.matches('.role-more-menu .dropdown-item')) bootstrap.Dropdown.getInstance(trigger)?.hide();
            if (button.matches(".js-open-role-panel")) openPanel(role, button.dataset.mode, true, trigger);
            if (button.matches(".js-close-role-panel")) closePanel();
            if (button.matches(".js-cancel-role-panel")) closePanel();
            if (button.matches(".permission-module-button")) activateModule(button.dataset.module);
            if (button.matches(".js-edit-role-details")) openInfo(role, trigger);
            if (button.matches(".js-assign-admins")) openAssignment(role);
            if (button === assign) openAssignment(current);
            if (button.matches(".js-view-assigned-users")) {
                modalOpener = trigger;
                $("viewRoleTitle").textContent = `${role.display_name} \u00b7 Assigned Administrators`;
                $("viewRoleUserCount").textContent = `${role.user_count} assigned administrator${role.user_count === 1 ? "" : "s"}`;
                const list = $("viewAssignedUsers"); list.replaceChildren();
                role.role_users.forEach(u => {
                    const row = document.createElement("p"), name = document.createElement("strong"), detail = document.createElement("small"), status = document.createElement("small");
                    name.textContent = u.full_name; detail.textContent = u.username;
                    row.append(name, detail);
                    if (u.program_major && u.program_major !== '\u2014') { const program = document.createElement('small'); program.textContent = `Program / Major: ${u.program_major}`; row.append(program); }
                    status.textContent = `Account Status: ${u.account_status}`; row.append(status); list.append(row);
                });
                if (!role.user_count) list.textContent = "No administrators assigned.";
                usersModal.show();
            }
            if (button.matches('.js-view-role-history') && role && !role.is_readonly) {
                modalOpener = trigger; $("roleHistoryName").textContent = role.display_name;
                historyModal.show(); loadHistory(role);
            }
            if (button.matches('.js-role-status') && role && !role.is_protected) {
                modalOpener = trigger; statusRole = role; statusAction = button.dataset.action;
                const deactivating = statusAction === 'deactivate';
                $("roleStatusTitle").textContent = deactivating ? 'Deactivate Role?' : 'Reactivate Role?';
                $("roleStatusName").textContent = role.display_name;
                $("roleStatusMessage").textContent = deactivating ? 'This role will no longer be available for new administrator assignments.' : 'This role will be available for administrator assignments once its permissions are configured.';
                $("roleStatusImpact").textContent = deactivating ? "Assigned administrators also lose this role's permissions until reactivated. Assignment and activity history will be preserved." : 'Existing assignments, configured permissions and activity history will be preserved.';
                $("roleStatusConfirm").disabled = false; $("roleStatusConfirm").textContent = deactivating ? 'Deactivate Role' : 'Reactivate Role';
                error('roleStatusError'); statusModal.show();
            }
        });
        checks.forEach(c => c.addEventListener("change", sync));
        form.addEventListener("submit", async event => {
            event.preventDefault(); if (mode !== "edit" || current.is_readonly || save.disabled) return;
            save.disabled = true; save.textContent = "Saving..."; const data = new FormData(form); data.delete("permissions"); selected().forEach(c => data.append("permissions", c));
            try { const payload = await post(page.dataset.permissionsUrl, data); remember(payload.role); openPanel(payload.role, "edit", false); toast(payload.message,'success'); }
            catch (e) { toast(e.message,'error'); sync(); }
            finally { save.textContent = "Save Changes"; }
        });
        infoForm.addEventListener("submit", async event => {
            event.preventDefault(); const button = $("saveRoleButton"); button.disabled = true; button.textContent = "Saving..."; error("roleFormError");
            const creating = !$("roleIdInput").value;
            try {
                const payload = await post(page.dataset.saveUrl, new FormData(infoForm));
                window.CampusHubAlerts?.remember(payload.message);
                if (creating) { const url = new URL(window.location.href); url.search = ""; const token = new URL(window.location.href).searchParams.get("__at"); if (token) url.searchParams.set("__at", token); url.searchParams.set("configure", payload.role.id); window.location.assign(url.href); }
                else window.location.reload();
            } catch (e) { error("roleFormError", e.message); button.disabled = false; button.textContent = "Save Role"; }
        });
        assignmentForm.addEventListener("submit", async event => {
            event.preventDefault(); const button = assignmentForm.querySelector("[type=submit]"); button.disabled = true; button.textContent = "Saving..."; error("assignmentError");
            try { const payload=await post(page.dataset.saveUrl, new FormData(assignmentForm)); window.CampusHubAlerts?.remember(payload.message); window.location.reload(); }
            catch (e) { error("assignmentError", e.message); button.disabled = false; button.textContent = "Save Assignments"; }
        });
        const filters = $("rolesFilterForm"); let filterTimer;
        filters.querySelectorAll("select").forEach(s => s.addEventListener("change", () => filters.requestSubmit()));
        const search = filters.querySelector("[name=q]"); search.addEventListener("input", () => { clearTimeout(filterTimer); filterTimer = setTimeout(() => filters.requestSubmit(), 500); });
        filters.addEventListener("submit", () => clearTimeout(filterTimer));
        document.addEventListener("keydown", event => {
            if (panel.hidden) return;
            if (event.key === "Escape") { event.preventDefault(); closePanel(); }
            if (event.key === "Tab") {
                const visible = [...panel.querySelectorAll("button:not([disabled]),input:not([disabled])")].filter(n => n.getClientRects().length && !n.hidden);
                const first = visible[0], last = visible[visible.length - 1];
                if (event.shiftKey && (document.activeElement === first || document.activeElement === panel)) { event.preventDefault(); last?.focus(); }
                else if (!event.shiftKey && (document.activeElement === last || document.activeElement === panel)) { event.preventDefault(); first?.focus(); }
            }
        });
        $("roleFormModal").addEventListener("shown.bs.modal", () => $("roleNameInput").focus());
        const configured = JSON.parse($("configureRoleData").textContent);
        if (configured && !configured.is_readonly) { remember(configured); openPanel(configured, "edit"); }
    });
})();
