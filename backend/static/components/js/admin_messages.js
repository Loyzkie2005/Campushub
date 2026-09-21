(function () {
    'use strict';

    const listEl = document.getElementById('messagesList');
    const bodyEl = document.getElementById('messageChatBody');
    const composer = document.getElementById('messageComposer');
    const input = document.getElementById('messageInput');
    const sendBtn = document.getElementById('messageSendBtn');
    const clearChatBtn = document.getElementById('messageClearChatBtn');
    const searchInput = document.getElementById('messagesSearchInput');
    const composeBtn = document.getElementById('messagesComposeBtn');
    const deleteBtn = document.getElementById('messagesDeleteBtn');
    const conversationHeader = document.getElementById('messageConversationHeader');
    const contactName = document.getElementById('messageContactName');
    const contactAvatar = document.getElementById('messageContactAvatar');
    const connectionStatus = document.getElementById('messageConnectionStatus');
    if (!listEl || !bodyEl || !composer || !input || !sendBtn) return;

    let token = '';
    let actorKey = '';
    let httpUrl = '';
    let wsUrl = '';
    let socket = null;
    let reconnectTimer = null;
    let reconnectAttempt = 0;
    let conversations = [];
    let activeConversation = null;
    let peerLastReadId = 0;
    let pendingLocalId = 0;
    let editMode = false;
    const selectedConversationIds = new Set();
    const activeConversationKey = 'campushub_active_chat_id';

    function adminTabToken() {
        return window.CampusHubAdminSession?.getTabToken?.()
            || sessionStorage.getItem('campushub_admin_tab_token')
            || new URLSearchParams(window.location.search).get('__at')
            || '';
    }

    function djangoHeaders() {
        const headers = { Accept: 'application/json' };
        const tabToken = adminTabToken();
        if (tabToken) headers['X-Admin-Tab-Token'] = tabToken;
        return headers;
    }

    async function responseJson(response, fallbackMessage) {
        const contentType = response.headers.get('content-type') || '';
        if (!contentType.toLowerCase().includes('application/json')) {
            if (response.redirected || response.status === 401 || response.status === 403) {
                throw new Error('Admin session expired. Please sign in again.');
            }
            throw new Error(`${fallbackMessage} (server returned ${response.status}).`);
        }
        return response.json();
    }

    function setConnectionStatus(text, connected) {
        if (!connectionStatus) return;
        connectionStatus.textContent = text;
        connectionStatus.classList.toggle('text-success', Boolean(connected));
        connectionStatus.classList.toggle('text-muted', !connected);
    }

    async function api(path, options) {
        const response = await fetch(`${httpUrl}${path}`, {
            ...(options || {}),
            headers: {
                Accept: 'application/json',
                Authorization: `Bearer ${token}`,
                'Content-Type': 'application/json',
                ...((options && options.headers) || {}),
            },
        });
        const data = await response.json().catch(() => ({}));
        if (!response.ok) {
            throw new Error(data.detail || data.error || `Chat request failed (${response.status})`);
        }
        return data;
    }

    function values(payload, key) {
        if (Array.isArray(payload)) return payload;
        if (payload && Array.isArray(payload[key])) return payload[key];
        if (payload && Array.isArray(payload.items)) return payload.items;
        return [];
    }

    function otherParticipant(conversation) {
        const participants = conversation.participants || [];
        return participants.find((item) => item.actor_key !== actorKey) || participants[0] || null;
    }

    function conversationName(conversation) {
        const other = otherParticipant(conversation);
        return (other && (other.display_name || other.name)) || conversation.title || 'Conversation';
    }

    function conversationPreview(conversation) {
        const last = conversation.last_message;
        if (typeof last === 'string') return last;
        if (last && last.body) return last.body;
        return 'No messages yet';
    }

    function conversationTime(conversation) {
        const raw = (conversation.last_message && conversation.last_message.created_at)
            || conversation.updated_at
            || conversation.created_at;
        if (!raw) return '';
        const date = new Date(raw);
        if (Number.isNaN(date.getTime())) return '';
        return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
    }

    function initialsFromName(name) {
        const parts = String(name || '')
            .trim()
            .split(/\s+/)
            .filter(Boolean);
        if (!parts.length) return 'CH';
        if (parts.length === 1) return parts[0].slice(0, 2).toUpperCase();
        return `${parts[0][0]}${parts[parts.length - 1][0]}`.toUpperCase();
    }

    function renderProfileAvatar(element, name) {
        element.textContent = initialsFromName(name);
        element.removeAttribute('aria-hidden');
        element.setAttribute('aria-label', name || 'Chat profile');
    }

    let typingStopTimer = null;
    let typingActive = false;
    let remoteTypingName = '';

    function typingIndicatorRow() {
        const row = document.createElement('div');
        row.className = 'bubble-row incoming typing-row';
        row.id = 'messageTypingIndicator';
        const line = document.createElement('div');
        line.className = 'message-bubble-line';
        const bubble = document.createElement('div');
        bubble.className = 'message-bubble typing-bubble';
        bubble.setAttribute('aria-label', 'Typing');
        bubble.innerHTML = `
                <span class="typing-dots" aria-hidden="true">
                    <span></span><span></span><span></span>
                </span>`;
        line.appendChild(bubble);
        row.appendChild(line);
        return row;
    }

    function showTypingIndicator(name) {
        remoteTypingName = name || 'Someone';
        let indicator = bodyEl.querySelector('#messageTypingIndicator');
        if (!indicator) {
            bodyEl.querySelector('.messages-chat-empty')?.remove();
            indicator = typingIndicatorRow();
            bodyEl.appendChild(indicator);
        }
        bodyEl.scrollTop = bodyEl.scrollHeight;
        if (connectionStatus && activeConversation) {
            connectionStatus.textContent = `${remoteTypingName} is typing…`;
        }
    }

    function hideTypingIndicator() {
        remoteTypingName = '';
        bodyEl.querySelector('#messageTypingIndicator')?.remove();
        if (connectionStatus && socket?.readyState === WebSocket.OPEN) {
            connectionStatus.textContent = 'Online';
        }
    }

    function emitTyping(isTyping) {
        if (!activeConversation || !socket || socket.readyState !== WebSocket.OPEN) return;
        socket.send(JSON.stringify({
            type: isTyping ? 'typing.start' : 'typing.stop',
            conversation_id: activeConversation.id,
        }));
        typingActive = isTyping;
    }

    function onComposerTyping() {
        if (!activeConversation) return;
        if (input.value.trim()) {
            if (!typingActive) emitTyping(true);
            clearTimeout(typingStopTimer);
            typingStopTimer = setTimeout(() => emitTyping(false), 1600);
        } else if (typingActive) {
            clearTimeout(typingStopTimer);
            emitTyping(false);
        }
    }

    function updateEditControls() {
        composeBtn?.classList.toggle('is-editing', editMode);
        composeBtn?.setAttribute('aria-pressed', String(editMode));
        deleteBtn?.classList.toggle('d-none', !editMode);
        if (deleteBtn) deleteBtn.disabled = selectedConversationIds.size === 0;
    }

    function setEditMode(enabled) {
        editMode = enabled;
        if (!editMode) selectedConversationIds.clear();
        updateEditControls();
        renderConversations();
    }

    function toggleConversationSelection(conversationId) {
        if (selectedConversationIds.has(conversationId)) {
            selectedConversationIds.delete(conversationId);
        } else {
            selectedConversationIds.add(conversationId);
        }
        updateEditControls();
        renderConversations();
    }

    function clearActiveConversation() {
        activeConversation = null;
        sessionStorage.removeItem(activeConversationKey);
        clearTimeout(typingStopTimer);
        if (typingActive) emitTyping(false);
        remoteTypingName = '';
        const url = new URL(window.location.href);
        url.searchParams.delete('conversation');
        window.history.replaceState({}, '', `${url.pathname}${url.search}${url.hash}`);
        conversationHeader?.classList.add('d-none');
        composer.classList.add('d-none');
        input.disabled = true;
        sendBtn.disabled = true;
        bodyEl.innerHTML = '<div class="messages-chat-empty"><strong>No chats</strong></div>';
    }

    function bindSwipeToDelete(wrapper, item) {
        let startX = null;
        let offset = 0;

        item.addEventListener('pointerdown', (event) => {
            if (editMode) return;
            startX = event.clientX;
            offset = 0;
            item.setPointerCapture(event.pointerId);
            item.classList.add('is-swiping');
        });
        item.addEventListener('pointermove', (event) => {
            if (startX === null) return;
            offset = Math.max(-84, Math.min(0, event.clientX - startX));
            if (Math.abs(offset) > 5) {
                item.dataset.suppressClick = 'true';
                item.style.transform = `translateX(${offset}px)`;
            }
        });
        const finish = () => {
            if (startX === null) return;
            const open = offset < -42;
            wrapper.classList.toggle('is-open', open);
            item.style.transform = open ? 'translateX(-84px)' : '';
            item.classList.remove('is-swiping');
            startX = null;
            offset = 0;
        };
        item.addEventListener('pointerup', finish);
        item.addEventListener('pointercancel', finish);
    }

    function renderConversations() {
        const query = String(searchInput?.value || '').trim().toLowerCase();
        const filtered = conversations.filter((conversation) =>
            conversationName(conversation).toLowerCase().includes(query)
            || conversationPreview(conversation).toLowerCase().includes(query)
        );
        listEl.innerHTML = '';

        if (!filtered.length) {
            const empty = document.createElement('div');
            empty.className = 'messages-list-empty';
            const strong = document.createElement('strong');
            strong.textContent = query ? 'No matching chats' : 'No chats';
            empty.appendChild(strong);
            listEl.appendChild(empty);
            return;
        }

        filtered.forEach((conversation) => {
            const name = conversationName(conversation);
            const item = document.createElement('button');
            item.type = 'button';
            const selected = selectedConversationIds.has(conversation.id);
            const hasUnread = Number(conversation.unread_count || 0) > 0;
            item.className = `message-thread${activeConversation?.id === conversation.id ? ' active' : ''}${selected ? ' is-selected' : ''}${hasUnread ? ' has-unread' : ''}`;

            if (editMode) {
                const checkbox = document.createElement('span');
                checkbox.className = 'message-thread-checkbox';
                checkbox.setAttribute('aria-hidden', 'true');
                checkbox.textContent = selected ? '✓' : '';
                item.appendChild(checkbox);
            }

            const avatar = document.createElement('span');
            avatar.className = 'message-thread-avatar';
            renderProfileAvatar(avatar, name);

            const copy = document.createElement('span');
            copy.className = 'message-thread-copy';
            const title = document.createElement('strong');
            title.textContent = name;
            const preview = document.createElement('small');
            preview.textContent = conversationPreview(conversation);
            copy.append(title, preview);

            const meta = document.createElement('span');
            meta.className = 'message-thread-meta';
            const time = document.createElement('span');
            time.textContent = conversationTime(conversation);
            meta.appendChild(time);
            if (Number(conversation.unread_count || 0) > 0) {
                const unreadDot = document.createElement('span');
                unreadDot.className = 'message-thread-unread-dot';
                unreadDot.title = `${conversation.unread_count} unread`;
                meta.appendChild(unreadDot);
            }

            item.append(avatar, copy, meta);
            item.addEventListener('click', () => {
                if (item.dataset.suppressClick === 'true') {
                    item.dataset.suppressClick = 'false';
                    return;
                }
                if (editMode) {
                    toggleConversationSelection(conversation.id);
                    return;
                }
                openConversation(conversation);
            });

            const swipeRow = document.createElement('div');
            swipeRow.className = 'message-thread-swipe';
            const swipeDelete = document.createElement('button');
            swipeDelete.type = 'button';
            swipeDelete.className = 'message-thread-swipe-delete';
            swipeDelete.textContent = 'Delete';
            swipeDelete.addEventListener('click', () =>
                deleteConversations([conversation.id])
            );
            swipeRow.append(swipeDelete, item);
            bindSwipeToDelete(swipeRow, item);
            listEl.appendChild(swipeRow);
        });
    }

    function peerLastReadFromConversation(conversation) {
        const other = otherParticipant(conversation);
        const value = other && other.last_read_message_id;
        return Number(value || 0);
    }

    function deliveryLabelFor(message, isLastOutgoing) {
        if (!isLastOutgoing) return '';
        if (message._localStatus === 'sending' || String(message.id || '').startsWith('local-')) {
            return 'Sending';
        }
        const messageId = Number(message.id || 0);
        if (messageId > 0 && peerLastReadId >= messageId) return 'Seen';
        return 'Delivered';
    }

    function refreshOutgoingDeliveryStatuses() {
        const rows = [...bodyEl.querySelectorAll('.bubble-row.outgoing')];
        rows.forEach((row, index) => {
            const statusEl = row.querySelector('.message-delivery-status');
            if (!statusEl) return;
            const isLast = index === rows.length - 1;
            if (!isLast) {
                statusEl.remove();
                return;
            }
            const messageId = row.dataset.messageId || '';
            const sending = row.dataset.delivery === 'sending' || messageId.startsWith('local-');
            let label = 'Delivered';
            if (sending) label = 'Sending';
            else if (Number(messageId) > 0 && peerLastReadId >= Number(messageId)) label = 'Seen';
            statusEl.textContent = label;
        });
    }

    function messageMinuteKey(message) {
        const date = new Date(message.created_at || Date.now());
        return Number.isNaN(date.getTime())
            ? ''
            : String(Math.floor(date.getTime() / 60000));
    }

    function messageRow(message, options = {}) {
        const outgoing = (message.sender_actor_key || message.sender_key) === actorKey;
        const isLastOutgoing = Boolean(options.isLastOutgoing);
        const showTimestamp = options.showTimestamp !== false;
        const row = document.createElement('div');
        row.className = `bubble-row ${outgoing ? 'outgoing' : 'incoming'}`;
        row.dataset.messageId = String(message.id || '');
        row.dataset.minuteKey = messageMinuteKey(message);
        if (message._localStatus === 'sending') row.dataset.delivery = 'sending';

        const time = document.createElement('small');
        time.className = 'message-time';
        const date = new Date(message.created_at || Date.now());
        time.textContent = date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });

        const line = document.createElement('div');
        line.className = 'message-bubble-line';

        const bubble = document.createElement('div');
        bubble.className = 'message-bubble';
        const text = document.createElement('div');
        text.textContent = message.body || '';
        bubble.appendChild(text);

        line.appendChild(bubble);
        row.appendChild(line);
        if (showTimestamp) row.appendChild(time);

        if (outgoing) {
            const status = document.createElement('small');
            status.className = 'message-delivery-status';
            status.textContent = deliveryLabelFor(message, isLastOutgoing);
            if (!isLastOutgoing) status.hidden = true;
            row.appendChild(status);
        }
        return row;
    }

    function renderMessages(messages) {
        bodyEl.innerHTML = '';
        if (!messages.length) {
            const empty = document.createElement('div');
            empty.className = 'messages-chat-empty';
            const strong = document.createElement('strong');
            strong.textContent = 'No messages yet';
            empty.appendChild(strong);
            bodyEl.appendChild(empty);
            return;
        }
        let lastOutgoingIndex = -1;
        const timestampIndices = new Set();
        const displayedMinutes = new Set();
        messages.forEach((message, index) => {
            const outgoing = (message.sender_actor_key || message.sender_key) === actorKey;
            if (outgoing) lastOutgoingIndex = index;

            const nextMessage = messages[index + 1];
            const senderKey = message.sender_actor_key || message.sender_key;
            const nextSenderKey = nextMessage
                ? (nextMessage.sender_actor_key || nextMessage.sender_key)
                : null;
            const minuteKey = messageMinuteKey(message);
            const nextMinuteKey = nextMessage ? messageMinuteKey(nextMessage) : null;
            const endsSenderGroup = !nextMessage || senderKey !== nextSenderKey;
            const endsMinute = !nextMessage || minuteKey !== nextMinuteKey;

            if ((endsSenderGroup || endsMinute) && !displayedMinutes.has(minuteKey)) {
                timestampIndices.add(index);
                displayedMinutes.add(minuteKey);
            }
        });
        messages.forEach((message, index) => {
            bodyEl.appendChild(messageRow(message, {
                isLastOutgoing: index === lastOutgoingIndex,
                showTimestamp: timestampIndices.has(index),
            }));
        });
        bodyEl.scrollTop = bodyEl.scrollHeight;
    }

    function appendMessage(message) {
        if (!message || activeConversation?.id !== message.conversation_id) return;
        if (message.id && bodyEl.querySelector(`[data-message-id="${message.id}"]`)) {
            refreshOutgoingDeliveryStatuses();
            return;
        }
        // Replace optimistic "Sending" bubble for our own messages.
        const outgoing = (message.sender_actor_key || message.sender_key) === actorKey;
        if (outgoing) {
            const pending = bodyEl.querySelector('.bubble-row.outgoing[data-delivery="sending"]');
            if (pending && (pending.querySelector('.message-bubble')?.textContent || '') === (message.body || '')) {
                pending.remove();
            }
        }
        bodyEl.querySelector('.messages-chat-empty')?.remove();
        const previousRow = bodyEl.querySelector('.bubble-row:last-of-type');
        const previousIsOutgoing = previousRow?.classList.contains('outgoing');
        const sameMinute = previousRow?.dataset.minuteKey === messageMinuteKey(message);
        let showTimestamp = true;
        if (previousRow && sameMinute && previousIsOutgoing === outgoing) {
            previousRow.querySelector('.message-time')?.remove();
        } else if (previousRow && sameMinute) {
            showTimestamp = false;
        }
        bodyEl.querySelectorAll('.message-delivery-status').forEach((el) => {
            el.hidden = true;
        });
        bodyEl.appendChild(messageRow(message, {
            isLastOutgoing: outgoing,
            showTimestamp,
        }));
        refreshOutgoingDeliveryStatuses();
        bodyEl.scrollTop = bodyEl.scrollHeight;
    }

    async function loadConversations() {
        const data = await api('/conversations');
        conversations = values(data, 'conversations');
        renderConversations();
        if (!activeConversation) {
            const requestedId = Number(
                new URLSearchParams(window.location.search).get('conversation')
                || sessionStorage.getItem(activeConversationKey)
            );
            const requested = conversations.find((item) => item.id === requestedId);
            if (requested) {
                await openConversation(requested);
                return;
            }
            clearActiveConversation();
        }
        if (activeConversation) {
            activeConversation = conversations.find((item) => item.id === activeConversation.id)
                || activeConversation;
        }
    }

    async function openConversation(conversation) {
        activeConversation = conversation;
        peerLastReadId = peerLastReadFromConversation(conversation);
        sessionStorage.setItem(activeConversationKey, String(conversation.id));
        const url = new URL(window.location.href);
        url.searchParams.set('conversation', String(conversation.id));
        window.history.replaceState({}, '', `${url.pathname}${url.search}${url.hash}`);
        conversationHeader?.classList.remove('d-none');
        composer.classList.remove('d-none');
        const name = conversationName(conversation);
        if (contactName) contactName.textContent = name;
        if (contactAvatar) renderProfileAvatar(contactAvatar, name);
        hideTypingIndicator();
        input.disabled = false;
        sendBtn.disabled = false;
        renderConversations();
        bodyEl.innerHTML = '<div class="messages-chat-empty"><strong>Loading…</strong></div>';
        try {
            const data = await api(`/conversations/${conversation.id}/messages?limit=100`);
            const messages = values(data, 'messages');
            // Refresh peer read from latest conversation summary if available.
            const latest = conversations.find((item) => item.id === conversation.id) || conversation;
            peerLastReadId = peerLastReadFromConversation(latest);
            renderMessages(messages);
            if (messages.length) {
                const last = messages[messages.length - 1];
                await api(`/conversations/${conversation.id}/read`, {
                    method: 'POST',
                    body: JSON.stringify({ message_id: last.id }),
                }).catch(() => {});
                conversation.unread_count = 0;
                const stored = conversations.find((item) => item.id === conversation.id);
                if (stored) stored.unread_count = 0;
                renderConversations();
            }
        } catch (error) {
            bodyEl.innerHTML = '';
            const empty = document.createElement('div');
            empty.className = 'messages-chat-empty text-danger';
            empty.textContent = error.message;
            bodyEl.appendChild(empty);
        }
    }

    function connectSocket() {
        clearTimeout(reconnectTimer);
        socket = new WebSocket(wsUrl);
        setConnectionStatus('Connecting…', false);

        socket.addEventListener('open', () => {
            socket.send(JSON.stringify({ type: 'auth', token }));
        });
        socket.addEventListener('message', (event) => {
            let payload;
            try {
                payload = JSON.parse(event.data);
            } catch (_) {
                return;
            }
            if (payload.type === 'auth.ok' || payload.type === 'authenticated') {
                reconnectAttempt = 0;
                setConnectionStatus('Online', true);
                return;
            }
            if (payload.type === 'message.created') {
                hideTypingIndicator();
                appendMessage(payload.message);
                loadConversations().catch(() => {});
                return;
            }
            if (payload.type === 'typing.start') {
                if (
                    payload.conversation_id === activeConversation?.id
                    && payload.actor_key !== actorKey
                ) {
                    showTypingIndicator(payload.name || 'Someone');
                }
                return;
            }
            if (payload.type === 'typing.stop') {
                if (
                    payload.conversation_id === activeConversation?.id
                    && payload.actor_key !== actorKey
                ) {
                    hideTypingIndicator();
                }
                return;
            }
            if (payload.type === 'conversation.deleted') {
                if (activeConversation?.id === payload.conversation_id) {
                    clearActiveConversation();
                }
                selectedConversationIds.delete(payload.conversation_id);
                loadConversations().catch(() => {});
                return;
            }
            if (payload.type === 'conversation.cleared') {
                if (activeConversation?.id === payload.conversation_id) {
                    renderMessages([]);
                }
                loadConversations().catch(() => {});
                return;
            }
            if (payload.type === 'conversation.updated') {
                if (payload.read && activeConversation?.id === payload.read.conversation_id) {
                    if (payload.read.actor_key && payload.read.actor_key !== actorKey) {
                        peerLastReadId = Number(payload.read.last_read_message_id || peerLastReadId);
                        refreshOutgoingDeliveryStatuses();
                    }
                }
                loadConversations().then(() => {
                    if (!activeConversation) return;
                    const latest = conversations.find((item) => item.id === activeConversation.id);
                    if (!latest) return;
                    peerLastReadId = Math.max(
                        peerLastReadId,
                        peerLastReadFromConversation(latest),
                    );
                    refreshOutgoingDeliveryStatuses();
                }).catch(() => {});
            }
        });
        socket.addEventListener('close', () => {
            setConnectionStatus('Reconnecting…', false);
            reconnectAttempt += 1;
            const wait = Math.min(1000 * (2 ** reconnectAttempt), 15000);
            reconnectTimer = setTimeout(connectSocket, wait);
        });
        socket.addEventListener('error', () => socket.close());
    }

    async function sendMessage(body) {
        if (!activeConversation || !body) return;
        pendingLocalId += 1;
        const localId = `local-${pendingLocalId}`;
        const optimistic = {
            id: localId,
            conversation_id: activeConversation.id,
            sender_actor_key: actorKey,
            sender_name: 'You',
            body,
            created_at: new Date().toISOString(),
            _localStatus: 'sending',
        };
        appendMessage(optimistic);

        if (socket && socket.readyState === WebSocket.OPEN) {
            socket.send(JSON.stringify({
                type: 'message.send',
                conversation_id: activeConversation.id,
                body,
            }));
            return;
        }
        const message = await api(`/conversations/${activeConversation.id}/messages`, {
            method: 'POST',
            body: JSON.stringify({ body }),
        });
        const pending = bodyEl.querySelector(`[data-message-id="${localId}"]`);
        pending?.remove();
        appendMessage(message.message || message);
        await loadConversations();
    }

    composer.addEventListener('submit', async (event) => {
        event.preventDefault();
        const body = input.value.trim();
        if (!body || !activeConversation) return;
        clearTimeout(typingStopTimer);
        if (typingActive) emitTyping(false);
        input.value = '';
        sendBtn.disabled = true;
        try {
            await sendMessage(body);
        } catch (error) {
            input.value = body;
            setConnectionStatus(error.message, false);
        } finally {
            sendBtn.disabled = false;
            input.focus();
        }
    });

    async function deleteConversations(ids) {
        if (!ids.length) return;
        const label = ids.length === 1 ? 'this chat' : `these ${ids.length} chats`;
        if (!window.confirm(`Delete ${label}? It will return if a new message arrives.`)) return;

        if (deleteBtn) deleteBtn.disabled = true;
        const originalText = deleteBtn?.textContent || 'Delete';
        if (deleteBtn) deleteBtn.textContent = 'Deleting…';
        try {
            for (const conversationId of ids) {
                await api(`/conversations/${conversationId}`, { method: 'DELETE' });
            }
            if (activeConversation && ids.includes(activeConversation.id)) {
                clearActiveConversation();
            }
            selectedConversationIds.clear();
            await loadConversations();
            if (editMode) setEditMode(false);
        } catch (error) {
            setConnectionStatus(error.message, false);
            updateEditControls();
        } finally {
            if (deleteBtn) deleteBtn.textContent = originalText;
        }
    }

    async function deleteSelectedConversations() {
        await deleteConversations([...selectedConversationIds]);
    }

    async function clearActiveChat() {
        if (!activeConversation) return;
        if (!window.confirm('Clear all messages in this chat?')) return;
        clearChatBtn.disabled = true;
        try {
            await api(`/conversations/${activeConversation.id}/messages`, {
                method: 'DELETE',
            });
            renderMessages([]);
            await loadConversations();
        } catch (error) {
            setConnectionStatus(error.message, false);
        } finally {
            clearChatBtn.disabled = false;
        }
    }

    searchInput?.addEventListener('input', renderConversations);
    input?.addEventListener('input', onComposerTyping);
    composeBtn?.addEventListener('click', () => setEditMode(!editMode));
    deleteBtn?.addEventListener('click', deleteSelectedConversations);
    clearChatBtn?.addEventListener('click', clearActiveChat);

    async function init() {
        try {
            const response = await fetch('/api/chat/token/', {
                headers: djangoHeaders(),
                credentials: 'same-origin',
            });
            const config = await responseJson(response, 'Could not authenticate chat');
            if (!response.ok || !config.token) {
                throw new Error(config.error || 'Could not authenticate chat.');
            }
            token = config.token;
            actorKey = config.actor_key;
            httpUrl = String(config.http_url || '').replace(/\/+$/, '');
            wsUrl = config.ws_url;
            await loadConversations();
            connectSocket();
        } catch (error) {
            setConnectionStatus(error.message, false);
            listEl.innerHTML = '';
            const errorEl = document.createElement('div');
            errorEl.className = 'messages-list-empty text-danger';
            errorEl.textContent = error.message;
            listEl.appendChild(errorEl);
        }
    }

    window.addEventListener('beforeunload', () => {
        clearTimeout(reconnectTimer);
        if (socket) socket.close();
    });
    init();
})();
