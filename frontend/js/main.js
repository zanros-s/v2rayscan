const apiBase = "/api";
let serverGroupMode = "all"; // all / ungrouped / group:<id>
let serverGroups = [];

function showMessage(elementId, text, success = true) {
    const el = document.getElementById(elementId);
    if (!el) return;
    el.textContent = text;
    el.className = "status-text " + (success ? "success" : "error");
    if (text) {
        setTimeout(() => {
            el.textContent = "";
        }, 4000);
    }
}

function updateProxyFieldsVisibility() {
    const useProxy = document.getElementById("telegram-use-proxy").checked;
    const mode = document.getElementById("telegram-proxy-mode").value;

    const socksRows = document.querySelectorAll(".proxy-socks-row");
    const serverRows = document.querySelectorAll(".proxy-server-row");

    socksRows.forEach(row => {
        row.style.display = useProxy && mode === "socks" ? "flex" : "none";
    });
    serverRows.forEach(row => {
        row.style.display = useProxy && mode === "server" ? "flex" : "none";
    });
}

async function loadSettings() {
    try {
        const res = await fetch(`${apiBase}/settings/`);
        if (!res.ok) return;
        const data = await res.json();

        document.getElementById("telegram-bot-token").value = data.telegram_bot_token || "";
        document.getElementById("telegram-chat-id").value = data.telegram_chat_id || "";
        document.getElementById("check-interval").value = data.check_interval_seconds || 30;
        document.getElementById("notify-on-recover").checked = !!data.notify_on_recover;
        document.getElementById("down-fail-threshold").value = data.down_fail_threshold ?? 3;
        
        document.getElementById("telegram-use-proxy").checked = !!data.telegram_use_proxy;
        document.getElementById("telegram-proxy-mode").value = data.telegram_proxy_mode || "none";

        document.getElementById("telegram-socks-host").value = data.telegram_socks_host || "";
        document.getElementById("telegram-socks-port").value = data.telegram_socks_port || "";
        document.getElementById("telegram-socks-username").value = data.telegram_socks_username || "";
        document.getElementById("telegram-socks-password").value = data.telegram_socks_password || "";
        document.getElementById("telegram-server-id").value = data.telegram_server_id || "";

        updateProxyFieldsVisibility();
    } catch (e) {
        console.error(e);
    }
}

async function saveSettings() {
    const botToken = document.getElementById("telegram-bot-token").value.trim();
    const chatId = document.getElementById("telegram-chat-id").value.trim();
    const interval = parseInt(document.getElementById("check-interval").value, 10) || 30;
    const notifyOnRecover = document.getElementById("notify-on-recover").checked;

    const useProxy = document.getElementById("telegram-use-proxy").checked;
    const proxyMode = document.getElementById("telegram-proxy-mode").value;

    const socksHost = document.getElementById("telegram-socks-host").value.trim();
    const socksPortVal = document.getElementById("telegram-socks-port").value.trim();
    const socksPort = socksPortVal ? parseInt(socksPortVal, 10) : null;
    const socksUser = document.getElementById("telegram-socks-username").value.trim();
    const socksPass = document.getElementById("telegram-socks-password").value;

    const serverIdVal = document.getElementById("telegram-server-id").value.trim();
    const serverId = serverIdVal ? parseInt(serverIdVal, 10) : null;
    const downFailThresholdVal = document
        .getElementById("down-fail-threshold")
        .value
        .trim();

    const downFailThreshold = downFailThresholdVal
        ? parseInt(downFailThresholdVal, 10)
        : 3; 

    try {
        const res = await fetch(`${apiBase}/settings/`, {
            method: "PUT",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                telegram_bot_token: botToken || null,
                telegram_chat_id: chatId || null,
                check_interval_seconds: interval,
                notify_on_recover: notifyOnRecover,
                telegram_use_proxy: useProxy,
                telegram_proxy_mode: proxyMode,
                telegram_socks_host: socksHost || null,
                telegram_socks_port: socksPort,
                telegram_socks_username: socksUser || null,
                telegram_socks_password: socksPass || null,
                telegram_server_id: serverId,
                down_fail_threshold: downFailThreshold,
            })
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            showMessage(
            "settings-status",
            err.detail || t("settings.status.error"),
            false
            );
            return;
        }

        showMessage("settings-status", t("settings.status.ok"), true);
        await loadSettings();
    } catch (e) {
        console.error(e);
        showMessage("settings-status", t("common.error.network"), false);
    }
}

async function addServer() {
    const name = document.getElementById("server-name").value.trim();
    const link = document.getElementById("server-link").value.trim();

    if (!link) {
    showMessage(
        "add-server-status",
        t("addserver.status.error_required"),
        false
    );
    return;
    }

    try {
        const res = await fetch(`${apiBase}/servers/`, {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({
                name: name || null,
                link: link
            })
        });

        if (!res.ok) {
            const err = await res.json().catch(() => ({}));
            showMessage(
            "add-server-status",
            err.detail || t("addserver.status.error"),
            false
            );
            return;
        }

        document.getElementById("server-name").value = "";
        document.getElementById("server-link").value = "";
        showMessage("add-server-status", t("addserver.status.ok"), true);
        await loadServers();
    } catch (e) {
        console.error(e);
        showMessage("add-server-status", t("common.error.network"), false);
    }
}
function buildServerRow(server) {
    const tr = document.createElement("tr");

    const statusText = server.last_status || "-";
    const latencyText =
        server.last_latency_ms != null
            ? `${server.last_latency_ms.toFixed(0)} ms`
            : "-";
    const lastCheckedText = server.last_checked_at
        ? new Date(server.last_checked_at).toLocaleString()
        : "-";

    const statusClass =
        statusText === "UP" ? "up" : statusText === "DOWN" ? "down" : "";

    const groupName = server.group ? server.group.name : t("groups.ungrouped");
    const groupColor = (server.group && server.group.color) || "#4b5563";

    tr.innerHTML = `
        <td>${server.id}</td>
        <td>${server.name}</td>
        <td class="group-cell">
            <span class="color-dot" style="background:${groupColor};display:inline-block;width:8px;height:8px;border-radius:999px;margin-left:4px;"></span>
            ${groupName}
        </td>
        <td>${server.host}:${server.port}</td>
        <td>${server.type}</td>
        <td class="raw-link-cell" title="${server.raw_link || ""}">
            ${server.raw_link || ""}
        </td>
        <td class="status ${statusClass}">
            ${statusText}
        </td>
        <td>${latencyText}</td>
        <td>${lastCheckedText}</td>
        <td class="servers-actions">
            <button data-action="toggle">${t("servers.action.toggle")}</button>
            <button data-action="test">${t("servers.action.test")}</button>
            <button data-action="chart">${t("servers.action.chart")}</button>
            <button data-action="monitor">${t("servers.action.monitor")}</button>
            <button data-action="edit">${t("servers.action.edit")}</button>
            <button data-action="delete" class="danger">${t("servers.action.delete")}</button>
        </td>
    `;


    tr.querySelector('[data-action="toggle"]').onclick = () =>
        toggleServer(server.id);
    tr.querySelector('[data-action="test"]').onclick = () =>
        testServer(server.id);
    tr.querySelector('[data-action="chart"]').onclick = () =>
        showServerChart(server.id, server.name);
    tr.querySelector('[data-action="monitor"]').onclick = () =>
        monitorServer(server.id);
    tr.querySelector('[data-action="edit"]').onclick = () =>
        openEditServerModal(server);
    tr.querySelector('[data-action="delete"]').onclick = () =>
        deleteServer(server.id);

    return tr;
}

async function loadGroups() {
    try {
        const res = await fetch(`${apiBase}/groups/`);
        if (!res.ok) return;
        serverGroups = await res.json();
        renderGroupBar();
        fillEditGroupSelect();
    } catch (e) {
        console.error(e);
    }
}

function renderGroupBar() {
    const bar = document.getElementById("server-groups-bar");
    if (!bar) return;
    bar.innerHTML = "";

   
    const allPill = document.createElement("div");
    allPill.className = "group-pill" + (serverGroupMode === "all" ? " active" : "");
    allPill.textContent = t("groups.all");
    allPill.onclick = () => {
        serverGroupMode = "all";
        renderGroupBar();
        loadServers();
    };
    bar.appendChild(allPill);

    
    const ungroupedPill = document.createElement("div");
    ungroupedPill.className =
        "group-pill" + (serverGroupMode === "ungrouped" ? " active" : "");
    ungroupedPill.textContent = t("groups.ungrouped");
    ungroupedPill.onclick = () => {
        serverGroupMode = "ungrouped";
        renderGroupBar();
        loadServers();
    };
    bar.appendChild(ungroupedPill);

    
    serverGroups.forEach((g) => {
        const pill = document.createElement("div");
        const active = serverGroupMode === `group:${g.id}` ? " active" : "";
        pill.className = "group-pill" + active;

        const color = g.color || "#0ea5e9";

        pill.innerHTML = `
        <span class="color-dot" style="background:${color};"></span>
        <span class="group-name">${g.name}</span>
        <span class="group-count" id="group-count-${g.id}"></span>
        <span class="group-actions">
            <button title="${t("groups.actions.edit")}">✎</button>
            <button title="${t("groups.actions.delete")}">✕</button>
        </span>
        `;

        pill.onclick = (e) => {
            if (e.target.tagName === "BUTTON") return;
            serverGroupMode = `group:${g.id}`;
            renderGroupBar();
            loadServers();
        };

        const [editBtn, delBtn] = pill.querySelectorAll(".group-actions button");
        editBtn.onclick = (e) => {
            e.stopPropagation();
            editGroupPrompt(g);
        };
        delBtn.onclick = (e) => {
            e.stopPropagation();
            deleteGroup(g.id);
        };

        bar.appendChild(pill);
    });
}

async function createGroupPrompt() {
    const name = prompt(t("groups.prompt.new"));
    if (!name) return;
    const color = prompt(t("groups.prompt.color_new")) || null;

    await fetch(`${apiBase}/groups/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, color, sort_order: 0 }),
    });
    loadGroups();
}

async function editGroupPrompt(group) {
    const name = prompt(t("groups.prompt.edit"), group.name);
    if (!name) return;
    const color = prompt(
        t("groups.prompt.color_edit"),
        group.color || "#0ea5e9"
    );

    await fetch(`${apiBase}/groups/${group.id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ name, color }),
    });
    loadGroups();
}

async function deleteGroup(id) {
    if (!confirm(t("groups.confirm.delete"))) return;
    await fetch(`${apiBase}/groups/${id}`, { method: "DELETE" });
    if (serverGroupMode === `group:${id}`) {
        serverGroupMode = "all";
    }
    loadGroups();
    loadServers();
}

function fillEditGroupSelect() {
    const sel = document.getElementById("edit-server-group");
    if (!sel) return;
    sel.innerHTML = `<option value="">بدون گروه</option>`;
    serverGroups.forEach((g) => {
        const opt = document.createElement("option");
        opt.value = g.id;
        opt.textContent = g.name;
        sel.appendChild(opt);
    });
}

async function loadServers() {
    try {
        const res = await fetch(`${apiBase}/servers/`);
        if (!res.ok) return;
        const data = await res.json();

        const tbody = document.querySelector("#servers-table tbody");
        tbody.innerHTML = "";

        let servers = Array.isArray(data) ? data : [];

       
        if (serverGroupMode === "ungrouped") {
            servers = servers.filter((s) => !s.group_id);
        } else if (serverGroupMode.startsWith("group:")) {
            const id = parseInt(serverGroupMode.split(":")[1], 10);
            servers = servers.filter((s) => s.group_id === id);
        }

        
        const counts = {};
        servers.forEach((s) => {
            const gid = s.group_id || "ungrouped";
            counts[gid] = (counts[gid] || 0) + 1;
        });
        serverGroups.forEach((g) => {
            const el = document.getElementById(`group-count-${g.id}`);
            if (el) el.textContent = counts[g.id] ? `(${counts[g.id]})` : "";
        });

        servers.forEach((server) => {
            tbody.appendChild(buildServerRow(server));
        });
    } catch (e) {
        console.error(e);
    }
}


async function monitorServer(id) {
    try {
        const res = await fetch(`${apiBase}/servers/${id}`);
        if (!res.ok) {
            alert(t("monitor.error.fetch_link"));
            return;
        }
        const data = await res.json();

        const liveInput = document.getElementById("live-link");
        if (liveInput) {
            liveInput.value = data.raw_link || "";
        }

        if (window.startLiveMonitor) {
            window.startLiveMonitor();
        } else {
            alert(t("monitor.error.unavailable"));
        }
    } catch (e) {
        console.error(e);
        alert(t("monitor.error.start"));
    }
}
function openEditServerModal(server) {
    const modal = document.getElementById("server-edit-modal");
    if (!modal) return;

    document.getElementById("edit-server-id").value = server.id;
    document.getElementById("edit-server-name").value = server.name || "";
    document.getElementById("edit-server-link").value = server.raw_link || "";
    document.getElementById("edit-server-enabled").checked = !!server.enabled;

    const sel = document.getElementById("edit-server-group");
    if (sel) {
        sel.value = server.group_id || "";
    }

    modal.classList.remove("hidden");
}

function closeEditServerModal() {
    const modal = document.getElementById("server-edit-modal");
    if (!modal) return;
    modal.classList.add("hidden");
}

async function saveEditServerModal(e) {
    e.preventDefault();
    const id = parseInt(
        document.getElementById("edit-server-id").value,
        10
    );
    const name = document.getElementById("edit-server-name").value.trim();
    const link = document
        .getElementById("edit-server-link")
        .value.trim();
    const enabled = document.getElementById(
        "edit-server-enabled"
    ).checked;
    const groupVal =
        document.getElementById("edit-server-group").value || null;
    const group_id = groupVal ? parseInt(groupVal, 10) : null;

    const payload = { name, enabled, group_id };
    if (link) payload.link = link;

    await fetch(`${apiBase}/servers/${id}`, {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify(payload),
    });

    closeEditServerModal();
    loadServers();
}

async function toggleServer(id) {
    try {
        const res = await fetch(`${apiBase}/servers/${id}/toggle`, {
            method: "POST"
        });
        if (!res.ok) {
            alert(t("servers.error.toggle"));
            return;
        }
        await loadServers();
    } catch (e) {
        console.error(e);
        alert(t("common.error.network"));
    }
}

async function deleteServer(id) {
    if (!confirm(t("servers.confirm.delete"))) return;

    try {
        const res = await fetch(`${apiBase}/servers/${id}`, {
            method: "DELETE"
        });
        if (!res.ok) {
            alert(t("servers.error.delete"));
            return;
        }
        await loadServers();
    } catch (e) {
        console.error(e);
        alert(t("common.error.network"));
    }
}

async function testServer(id) {
    try {
        const res = await fetch(`${apiBase}/servers/${id}/test`, {
            method: "POST"
        });
        if (!res.ok) {
            alert(t("servers.error.test"));
            return;
        }
        await loadServers();
    } catch (e) {
        console.error(e);
        alert(t("common.error.network"));
    }
}

document.addEventListener("DOMContentLoaded", () => {
    document
        .getElementById("telegram-use-proxy")
        .addEventListener("change", updateProxyFieldsVisibility);
    document
        .getElementById("telegram-proxy-mode")
        .addEventListener("change", updateProxyFieldsVisibility);

    const addGroupBtn = document.getElementById("add-group-btn");
    if (addGroupBtn) {
        addGroupBtn.addEventListener("click", createGroupPrompt);
    }

    const editForm = document.getElementById("server-edit-form");
    if (editForm) {
        editForm.addEventListener("submit", saveEditServerModal);
    }
    const cancelEdit = document.getElementById("server-edit-cancel");
    if (cancelEdit) {
        cancelEdit.addEventListener("click", closeEditServerModal);
    }

    loadSettings();
    loadGroups();   
    loadServers();
});



