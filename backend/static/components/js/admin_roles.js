(function () {
    "use strict";

    document.addEventListener("DOMContentLoaded", function () {
        const page = document.querySelector(".roles-page");
        const dataNode = document.getElementById("rolesData");
        if (!page || !dataNode) return;

        let roles = [];
        try {
            roles = JSON.parse(dataNode.textContent || "[]");
        } catch (_error) {
            roles = [];
        }

        const rolesById = new Map(roles.map(function (role) {
            return [String(role.id), role];
        }));
        const toast = document.getElementById("rolesToast");
        const filterForm = document.getElementById("rolesFilterForm");
        const panel = document.getElementById("rolePermissionPanel");
        const layout = document.getElementById("rolesRbacLayout");
        const panelForm = document.getElementById("permissionPanelForm");
        const panelRoleId = document.getElementById("permissionPanelRoleId");
        const panelPermissions = Array.from(document.querySelectorAll(".js-panel-permission"));
        const panelSave = document.getElementById("permissionPanelSaveButton");
        const panelCancel = document.getElementById("permissionPanelCancelButton");
        const panelClose = document.getElementById("permissionPanelCloseButton");
        const panelNote = document.getElementById("permissionPanelNote");
        const roleFormNode = document.getElementById("roleFormModal");
        const viewUsersNode = document.getElementById("viewRoleModal");
        const deleteRoleNode = document.getElementById("deleteRoleModal");
        const roleFormModal = bootstrap.Modal.getOrCreateInstance(roleFormNode);
        const viewUsersModal = bootstrap.Modal.getOrCreateInstance(viewUsersNode);
        const deleteRoleModal = bootstrap.Modal.getOrCreateInstance(deleteRoleNode);
        const roleForm = document.getElementById("roleForm");
        const roleIdInput = document.getElementById("roleIdInput");
        const roleNameInput = document.getElementById("roleNameInput");
        const roleDescInput = document.getElementById("roleDescInput");
        const roleTypeInput = document.getElementById("roleTypeInput");
        const roleActiveInput = document.getElementById("roleActiveInput");
        const assignedUsersInput = document.getElementById("assignedUsersInput");
        const assignedUsersHelp = document.getElementById("assignedUsersHelp");
        const systemRoleNote = document.getElementById("systemRoleNote");
        const saveRoleButton = document.getElementById("saveRoleButton");
        let selectedRole = null;
        let panelMode = "view";
        let savedPermissionSignature = "";
        let formRole = null;
        let formMode = "add";
        let formPermissionCodenames = [];
        let deleteRoleId = "";
        let filterTimer = 0;

        function showToast(message, type) {
            toast.textContent = message;
            toast.className = "campushub-toast is-visible " + (type === "error" ? "is-error" : "is-success");
            window.clearTimeout(showToast.timer);
            showToast.timer = window.setTimeout(function () {
                toast.classList.remove("is-visible");
            }, 3200);
        }

        function roleById(roleId) {
            return rolesById.get(String(roleId));
        }

        function isSuperAdmin(role) {
            return Boolean(role && String(role.role_name || "").toLowerCase() === "super admin");
        }

        function isRestrictedSystemPermission(input) {
            const roleName = String(selectedRole?.role_name || "").trim().toLowerCase();
            if (roleName === "marketplace admin" || roleName === "facilities admin") {
                return ["can_export_marketplace_data", "can_export_facility_data", "can_system_backup", "can_restore_system_backup"].includes(input.value);
            }
            return false;
        }

        function permissionSignature(values) {
            return Array.from(values || []).map(String).sort().join("|");
        }

        function selectedPermissionValues() {
            return panelPermissions.filter(function (input) {
                return input.checked;
            }).map(function (input) {
                return input.value;
            });
        }

        function setActiveModule(moduleKey) {
            document.querySelectorAll(".permission-module-button").forEach(function (button) {
                const active = button.dataset.module === moduleKey;
                button.classList.toggle("is-active", active);
                button.setAttribute("aria-pressed", active ? "true" : "false");
            });
            document.querySelectorAll(".permission-list-group").forEach(function (group) {
                group.hidden = group.dataset.permissionGroup !== moduleKey;
            });
        }

        function syncPanelState() {
            const selected = selectedPermissionValues();
            const locked = panelMode === "view" || isSuperAdmin(selectedRole);
            panelPermissions.forEach(function (input) {
                input.disabled = locked || isRestrictedSystemPermission(input);
            });
            document.getElementById("permissionPanelCount").textContent =
                selected.length + " permission" + (selected.length === 1 ? "" : "s") + " allowed";
            panelSave.disabled = locked || permissionSignature(selected) === savedPermissionSignature;
        }

        function openPanel(role, mode) {
            selectedRole = role;
            panelMode = mode;
            panel.hidden = false;
            layout.classList.add("is-panel-open");
            document.querySelectorAll("[data-role-row]").forEach(function (row) {
                row.classList.toggle("is-selected", row.dataset.roleRow === String(role.id));
            });
            panelRoleId.value = role.id;
            document.getElementById("permissionPanelMode").textContent =
                mode === "edit" ? "Edit Permissions" : "View Permissions";
            document.getElementById("permissionPanelTitle").textContent = role.display_name || role.role_name;
            const panelDescription = document.getElementById("permissionPanelDescription");
            const roleDescription = (role.description || "").trim();
            const isSeededBuiltInDescription = /^Built-in CampusHub .+ role\.$/i.test(roleDescription);
            const visibleDescription = isSeededBuiltInDescription
                ? ""
                : (roleDescription || role.permission_summary || "");
            panelDescription.textContent = visibleDescription;
            panelDescription.hidden = !visibleDescription;

            const selected = new Set(role.assigned_permissions || []);
            panelPermissions.forEach(function (input) {
                const restricted = isRestrictedSystemPermission(input);
                const row = input.closest(".permission-list-row");
                row.hidden = restricted;
                row.style.display = restricted ? "none" : "";
                input.checked = !restricted && (isSuperAdmin(role) || selected.has(input.value));
            });
            savedPermissionSignature = permissionSignature(selectedPermissionValues());

            panelClose.hidden = mode === "edit";
            panelCancel.hidden = mode !== "edit";
            panelSave.hidden = mode !== "edit" || isSuperAdmin(role);
            panelNote.hidden = !isSuperAdmin(role);
            panelNote.textContent = isSuperAdmin(role)
                ? "Super Admin is a protected system role and always retains full CampusHub access."
                : "";
            const firstModule = document.querySelector(".permission-module-button");
            if (firstModule) setActiveModule(firstModule.dataset.module);
            syncPanelState();
            panel.scrollIntoView({behavior: "smooth", block: "nearest"});
        }

        function closePanel() {
            panel.hidden = true;
            layout.classList.remove("is-panel-open");
            document.querySelectorAll("[data-role-row]").forEach(function (row) {
                row.classList.remove("is-selected");
            });
            selectedRole = null;
            panelRoleId.value = "";
        }

        function updateRoleRow(role) {
            const row = document.querySelector('[data-role-row="' + role.id + '"]');
            if (!row) return;
            const permissionSet = row.querySelector(".permission-set-label");
            const userCount = row.querySelector(".role-user-count");
            const status = row.querySelector(".role-status-badge");
            if (permissionSet) permissionSet.textContent = role.permission_summary;
            if (userCount) userCount.textContent = String(role.user_count || 0);
            if (status) {
                status.textContent = role.status_label;
                status.classList.toggle("is-active", Boolean(role.is_active));
                status.classList.toggle("is-inactive", !role.is_active);
            }
        }

        async function postForm(url, body) {
            const response = await fetch(url, {
                method: "POST",
                body: body,
                credentials: "same-origin",
                headers: {"X-Requested-With": "XMLHttpRequest", "Accept": "application/json"}
            });
            const data = await response.json().catch(function () { return {}; });
            if (!response.ok || !data.success) {
                throw new Error(data.message || "The request could not be completed.");
            }
            return data;
        }

        function resetRoleForm() {
            roleForm.reset();
            formRole = null;
            formMode = "add";
            formPermissionCodenames = [];
            roleIdInput.value = "";
            roleNameInput.readOnly = false;
            roleTypeInput.value = "Custom Role";
            roleActiveInput.disabled = false;
            roleActiveInput.checked = true;
            systemRoleNote.hidden = true;
            document.getElementById("roleFormTitle").textContent = "Add Custom Role";
            saveRoleButton.textContent = "Save Role";
            saveRoleButton.disabled = false;
            Array.from(assignedUsersInput.options).forEach(function (option) {
                option.selected = false;
                option.disabled = true;
            });
            assignedUsersHelp.textContent =
                "Create the role first, assign permissions with the pencil action, then assign administrators.";
        }

        function configureAssignedUsers(role, duplicate) {
            const assignedIds = new Set(
                duplicate || !role ? [] : (role.role_users || []).map(function (user) {
                    return String(user.id);
                })
            );
            const targetName = duplicate || !role ? "" : role.role_name;
            const inactive = !roleActiveInput.checked;
            Array.from(assignedUsersInput.options).forEach(function (option) {
                const alreadyAssigned = assignedIds.has(option.value);
                option.selected = alreadyAssigned;
                option.disabled = (
                    (inactive && !alreadyAssigned)
                    || (targetName === "Marketplace Admin" && !option.dataset.department && !alreadyAssigned)
                );
            });
            assignedUsersHelp.textContent = targetName === "Marketplace Admin"
                ? "New Marketplace Admin assignments require a department."
                : "Use Ctrl or Command to select multiple administrator accounts.";
        }

        function populateRoleForm(role, duplicate) {
            resetRoleForm();
            formRole = duplicate ? null : role;
            formMode = duplicate ? "duplicate" : "edit";
            formPermissionCodenames = Array.from(role.assigned_permissions || []);
            roleIdInput.value = duplicate ? "" : role.id;
            roleNameInput.value = duplicate ? role.role_name + " Copy" : role.role_name;
            roleDescInput.value = role.description || "";
            roleTypeInput.value = duplicate ? "Custom Role" : role.role_type;
            roleActiveInput.checked = duplicate ? true : Boolean(role.is_active);
            if (!duplicate && role.is_protected) {
                roleNameInput.readOnly = true;
                roleActiveInput.disabled = true;
                systemRoleNote.hidden = false;
            }
            configureAssignedUsers(role, duplicate);
            document.getElementById("roleFormTitle").textContent =
                duplicate ? "Duplicate Role" : "Edit Role Details";
            saveRoleButton.textContent = duplicate ? "Create Role" : "Save Changes";
            roleFormModal.show();
        }

        function renderAssignedUsers(role) {
            document.getElementById("viewRoleTitle").textContent = role.role_name;
            const users = document.getElementById("viewAssignedUsers");
            users.replaceChildren();
            const roleUsers = role.role_users || [];
            document.getElementById("viewRoleUserCount").textContent =
                roleUsers.length + " assigned user" + (roleUsers.length === 1 ? "" : "s");
            if (!roleUsers.length) {
                const empty = document.createElement("span");
                empty.className = "role-view-empty";
                empty.textContent = "No administrator accounts are assigned to this role.";
                users.appendChild(empty);
            } else {
                roleUsers.forEach(function (user) {
                    const item = document.createElement("div");
                    item.className = "role-view-user";
                    const avatar = document.createElement("span");
                    avatar.className = "role-view-avatar";
                    avatar.textContent = user.initials || "U";
                    const text = document.createElement("span");
                    const name = document.createElement("strong");
                    name.textContent = user.full_name || user.username;
                    const detail = document.createElement("small");
                    detail.textContent = user.email || user.username;
                    text.append(name, detail);
                    const status = document.createElement("em");
                    status.className = user.is_active ? "is-active" : "is-inactive";
                    status.textContent = user.is_active ? "Active" : "Inactive";
                    item.append(avatar, text, status);
                    users.appendChild(item);
                });
            }
            viewUsersModal.show();
        }

        document.getElementById("addRoleButton").addEventListener("click", function () {
            resetRoleForm();
            roleFormModal.show();
        });

        document.querySelectorAll(".js-auto-filter").forEach(function (select) {
            select.addEventListener("change", function () { filterForm.submit(); });
        });
        const searchInput = filterForm.querySelector('input[name="q"]');
        searchInput.addEventListener("input", function () {
            window.clearTimeout(filterTimer);
            filterTimer = window.setTimeout(function () { filterForm.submit(); }, 450);
        });

        document.querySelectorAll(".permission-module-button").forEach(function (button) {
            button.addEventListener("click", function () {
                setActiveModule(button.dataset.module);
            });
        });
        panelPermissions.forEach(function (input) {
            input.addEventListener("change", syncPanelState);
        });
        document.querySelectorAll(".js-close-role-panel, .js-cancel-role-panel").forEach(function (button) {
            button.addEventListener("click", closePanel);
        });

        document.addEventListener("keydown", function (event) {
            if (event.key === "Escape" && !panel.hidden) closePanel();
        });

        document.addEventListener("click", function (event) {
            const panelButton = event.target.closest(".js-open-role-panel");
            if (panelButton) {
                const role = roleById(panelButton.dataset.roleId);
                if (role) openPanel(role, panelButton.dataset.mode || "view");
                return;
            }
            const usersButton = event.target.closest(".js-view-assigned-users");
            if (usersButton) {
                const role = roleById(usersButton.dataset.roleId);
                if (role) renderAssignedUsers(role);
                return;
            }
            const detailsButton = event.target.closest(".js-edit-role-details");
            if (detailsButton) {
                const role = roleById(detailsButton.dataset.roleId);
                if (role && !role.is_protected) populateRoleForm(role, false);
                return;
            }
            const duplicateButton = event.target.closest(".js-duplicate-role");
            if (duplicateButton) {
                const role = roleById(duplicateButton.dataset.roleId);
                if (role && !role.is_protected) populateRoleForm(role, true);
                return;
            }
            const statusButton = event.target.closest(".js-role-status");
            if (statusButton) {
                const role = roleById(statusButton.dataset.roleId);
                if (!role || role.is_protected) return;
                const action = statusButton.dataset.action;
                if (!window.confirm((action === "activate" ? "Activate" : "Deactivate") + ' the role "' + role.role_name + '"?')) return;
                const body = new FormData();
                body.append("csrfmiddlewaretoken", roleForm.querySelector('[name="csrfmiddlewaretoken"]').value);
                body.append("role_id", role.id);
                body.append("action", action);
                postForm(page.dataset.statusUrl, body)
                    .then(function (data) {
                        showToast(data.message, "success");
                        window.setTimeout(function () { window.location.reload(); }, 450);
                    })
                    .catch(function (error) { showToast(error.message, "error"); });
                return;
            }
            const deleteButton = event.target.closest(".js-delete-role");
            if (deleteButton) {
                const role = roleById(deleteButton.dataset.roleId);
                if (!role || role.is_protected) return;
                deleteRoleId = String(role.id);
                document.getElementById("deleteRoleName").textContent = role.role_name;
                deleteRoleModal.show();
            }
        });

        panelForm.addEventListener("submit", async function (event) {
            event.preventDefault();
            if (!selectedRole || panelMode !== "edit" || isSuperAdmin(selectedRole)) return;
            const originalText = panelSave.textContent;
            panelSave.disabled = true;
            panelSave.textContent = "Saving...";
            try {
                const data = await postForm(page.dataset.permissionsUrl, new FormData(panelForm));
                Object.assign(selectedRole, data.role);
                rolesById.set(String(selectedRole.id), selectedRole);
                updateRoleRow(selectedRole);
                savedPermissionSignature = permissionSignature(selectedRole.assigned_permissions || []);
                syncPanelState();
                showToast(data.message, "success");
            } catch (error) {
                showToast(error.message, "error");
                syncPanelState();
            } finally {
                panelSave.textContent = originalText;
            }
        });

        roleActiveInput.addEventListener("change", function () {
            if (formMode !== "add") configureAssignedUsers(formRole, formMode === "duplicate");
        });

        roleForm.addEventListener("submit", async function (event) {
            event.preventDefault();
            saveRoleButton.disabled = true;
            const originalText = saveRoleButton.textContent;
            saveRoleButton.textContent = "Saving...";
            try {
                const body = new FormData(roleForm);
                formPermissionCodenames.forEach(function (codename) {
                    body.append("permissions", codename);
                });
                if (roleActiveInput.disabled && roleActiveInput.checked) body.set("is_active", "on");
                const data = await postForm(page.dataset.saveUrl, body);
                roleFormModal.hide();
                showToast(data.message, "success");
                window.setTimeout(function () { window.location.reload(); }, 450);
            } catch (error) {
                showToast(error.message, "error");
                saveRoleButton.disabled = false;
                saveRoleButton.textContent = originalText;
            }
        });

        document.getElementById("confirmDeleteRole").addEventListener("click", async function () {
            if (!deleteRoleId) return;
            const button = this;
            button.disabled = true;
            button.textContent = "Deleting...";
            const body = new FormData();
            body.append("csrfmiddlewaretoken", roleForm.querySelector('[name="csrfmiddlewaretoken"]').value);
            body.append("role_id", deleteRoleId);
            try {
                const data = await postForm(page.dataset.deleteUrl, body);
                deleteRoleModal.hide();
                showToast(data.message, "success");
                window.setTimeout(function () { window.location.reload(); }, 450);
            } catch (error) {
                showToast(error.message, "error");
                button.disabled = false;
                button.textContent = "Delete Role";
            }
        });

        roleFormNode.addEventListener("hidden.bs.modal", resetRoleForm);
        deleteRoleNode.addEventListener("hidden.bs.modal", function () {
            deleteRoleId = "";
            const button = document.getElementById("confirmDeleteRole");
            button.disabled = false;
            button.textContent = "Delete Role";
        });
    });
})();
