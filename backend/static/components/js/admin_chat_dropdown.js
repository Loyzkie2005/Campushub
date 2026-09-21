(function () {
    'use strict';

    const root = document.querySelector('.chat-header-dropdown');
    const list = document.getElementById('chatHeaderList');
    const search = document.getElementById('chatHeaderSearch');
    if (!root || !list || root.dataset.chatBound === 'true') return;
    root.dataset.chatBound = 'true';

    let conversations = [];
    let actorKey = '';
    let query = '';
    let loaded = false;
    let socket = null;
    let reconnectTimer = null;
    let socketUrl = '';
    let socketToken = '';

    function adminTabToken() {
        return window.CampusHubAdminSession?.getTabToken?.()
            || sessionStorage.getItem('campushub_admin_tab_token')
            || new URLSearchParams(window.location.search).get('__at')
            || '';
    }

    function rows(payload) {
        if (Array.isArray(payload)) return payload;
        if (Array.isArray(payload?.conversations)) return payload.conversations;
        if (Array.isArray(payload?.items)) return payload.items;
        return [];
    }

    function other(conversation) {
        return (conversation.participants || []).find(
            (participant) => participant.actor_key !== actorKey
        ) || (conversation.participants || [])[0] || {};
    }

    function displayName(conversation) {
        const participant = other(conversation);
        return participant.display_name || participant.name || conversation.title || 'Conversation';
    }

    function preview(conversation) {
        const last = conversation.last_message;
        return (last && (last.body || last.text)) || 'No messages yet';
    }

    function render() {
        list.innerHTML = '';
        const filtered = conversations.filter((conversation) => {
            const haystack = `${displayName(conversation)} ${preview(conversation)}`.toLowerCase();
            return haystack.includes(query);
        });

        if (!filtered.length) {
            const empty = document.createElement('div');
            empty.className = 'chat-header-empty';
            const label = document.createElement('strong');
            label.textContent = query ? 'No matching messages' : 'No messages';
            empty.appendChild(label);
            list.appendChild(empty);
            return;
        }

        filtered.slice(0, 8).forEach((conversation) => {
            const item = document.createElement('a');
            item.className = `chat-header-item${conversation.unread_count > 0 ? ' is-unseen' : ''}`;
            item.href = `/admin-messages/?conversation=${encodeURIComponent(conversation.id)}`;

            const avatar = document.createElement('span');
            avatar.className = 'chat-header-avatar';
            avatar.textContent = displayName(conversation).trim().charAt(0).toUpperCase() || 'M';

            const copy = document.createElement('span');
            copy.className = 'chat-header-copy';
            const name = document.createElement('strong');
            name.textContent = displayName(conversation);
            const body = document.createElement('small');
            body.textContent = preview(conversation);
            copy.append(name, body);
            item.append(avatar, copy);
            list.appendChild(item);
        });
    }

    function connectSocket(url, token) {
        if (!url || !token) return;
        socketUrl = url;
        socketToken = token;
        if (socket && (socket.readyState === WebSocket.OPEN || socket.readyState === WebSocket.CONNECTING)) {
            return;
        }

        socket = new WebSocket(socketUrl);
        socket.addEventListener('open', () => {
            socket.send(JSON.stringify({ type: 'auth', token: socketToken }));
        });
        socket.addEventListener('message', (event) => {
            let payload;
            try {
                payload = JSON.parse(event.data);
            } catch (_) {
                return;
            }
            if (
                payload.type === 'message.created'
                || payload.type === 'conversation.deleted'
                || payload.type === 'conversation.cleared'
                || payload.type === 'conversation.updated'
            ) {
                load();
            }
        });
        socket.addEventListener('close', () => {
            socket = null;
            window.clearTimeout(reconnectTimer);
            reconnectTimer = window.setTimeout(() => connectSocket(socketUrl, socketToken), 3000);
        });
    }

    async function load() {
        try {
            const headers = { Accept: 'application/json' };
            const tabToken = adminTabToken();
            if (tabToken) headers['X-Admin-Tab-Token'] = tabToken;
            const tokenResponse = await fetch('/api/chat/token/', {
                credentials: 'same-origin',
                headers,
            });
            const contentType = tokenResponse.headers.get('content-type') || '';
            if (!contentType.toLowerCase().includes('application/json')) return;
            const config = await tokenResponse.json();
            if (!tokenResponse.ok || !config.token) return;
            actorKey = config.actor_key;
            connectSocket(config.ws_url, config.token);
            const response = await fetch(
                `${String(config.http_url).replace(/\/+$/, '')}/conversations`,
                {
                    headers: {
                        Accept: 'application/json',
                        Authorization: `Bearer ${config.token}`,
                    },
                }
            );
            if (!response.ok) return;
            conversations = rows(await response.json());
            loaded = true;
            render();
        } catch (_) {
            // Keep the empty state while the chat service is unavailable.
        }
    }

    root.addEventListener('show.bs.dropdown', () => {
        load();
    });
    search?.addEventListener('input', () => {
        query = search.value.trim().toLowerCase();
        render();
    });
    window.addEventListener('focus', () => {
        if (loaded) load();
    });
})();
