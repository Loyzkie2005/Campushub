import 'dart:async';

import 'package:flutter/material.dart';

import '../models/chat_conversation.dart';
import '../models/chat_message.dart';
import '../services/chat_service.dart';

String chatInitials(String name) {
  final parts = name
      .trim()
      .split(RegExp(r'\s+'))
      .where((part) => part.isNotEmpty)
      .toList(growable: false);
  if (parts.isEmpty) return 'CH';
  if (parts.length == 1) {
    final value = parts.first;
    return value.substring(0, value.length >= 2 ? 2 : 1).toUpperCase();
  }
  return '${parts.first[0]}${parts.last[0]}'.toUpperCase();
}

class _ChatProfileAvatar extends StatelessWidget {
  const _ChatProfileAvatar({
    required this.name,
    this.size = 52,
    this.fontSize = 16,
    this.borderWidth = 2,
  });

  final String name;
  final double size;
  final double fontSize;
  final double borderWidth;

  @override
  Widget build(BuildContext context) {
    return Container(
      width: size,
      height: size,
      alignment: Alignment.center,
      decoration: BoxDecoration(
        color: MessagesPage.primaryNavy,
        shape: BoxShape.circle,
        border: Border.all(color: Colors.white, width: borderWidth),
        boxShadow: const [BoxShadow(color: Color(0xFFDBE3EF), spreadRadius: 1)],
      ),
      child: Text(
        chatInitials(name),
        style: TextStyle(
          color: Colors.white,
          fontSize: fontSize,
          fontWeight: FontWeight.w800,
          letterSpacing: 0.2,
        ),
      ),
    );
  }
}

class _TypingDots extends StatefulWidget {
  const _TypingDots();

  @override
  State<_TypingDots> createState() => _TypingDotsState();
}

class _TypingDotsState extends State<_TypingDots>
    with SingleTickerProviderStateMixin {
  late final AnimationController _controller;

  @override
  void initState() {
    super.initState();
    _controller = AnimationController(
      vsync: this,
      duration: const Duration(milliseconds: 1050),
    )..repeat();
  }

  @override
  void dispose() {
    _controller.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) {
    return AnimatedBuilder(
      animation: _controller,
      builder: (context, _) {
        return Row(
          mainAxisSize: MainAxisSize.min,
          children: List.generate(3, (index) {
            final phase = (_controller.value + index * 0.18) % 1.0;
            final bounce = phase < 0.4
                ? Curves.easeOut.transform(phase / 0.4)
                : phase < 0.8
                ? Curves.easeIn.transform((0.8 - phase) / 0.4)
                : 0.0;
            return Padding(
              padding: EdgeInsets.only(right: index == 2 ? 0 : 6),
              child: Transform.translate(
                offset: Offset(0, -5 * bounce),
                child: Opacity(
                  opacity: 0.35 + (0.65 * bounce),
                  child: Container(
                    width: 8,
                    height: 8,
                    decoration: const BoxDecoration(
                      color: Color(0xFF64748B),
                      shape: BoxShape.circle,
                    ),
                  ),
                ),
              ),
            );
          }),
        );
      },
    );
  }
}

class MessagesPage extends StatefulWidget {
  const MessagesPage({super.key});

  static const Color primaryNavy = Color(0xFF1A1851);

  @override
  State<MessagesPage> createState() => _MessagesPageState();
}

class _MessagesPageState extends State<MessagesPage> {
  final _searchController = TextEditingController();
  bool _loading = true;
  String? _error;

  @override
  void initState() {
    super.initState();
    ChatService.instance.addListener(_chatChanged);
    _initialize();
  }

  @override
  void dispose() {
    ChatService.instance.removeListener(_chatChanged);
    _searchController.dispose();
    super.dispose();
  }

  void _chatChanged() {
    if (mounted) setState(() {});
  }

  Future<void> _initialize() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final authenticated = await ChatService.instance.initialize();
      if (!authenticated) {
        throw const ChatException(
          'Please log in again to connect to CampusHub Chat.',
        );
      }
    } catch (error) {
      _error = error.toString();
    }
    if (mounted) setState(() => _loading = false);
  }

  List<ChatConversation> get _visibleConversations {
    final query = _searchController.text.trim().toLowerCase();
    final actorKey = ChatService.instance.actorKey;
    if (query.isEmpty) return ChatService.instance.conversations;
    return ChatService.instance.conversations
        .where((conversation) {
          final name = conversation.displayNameFor(actorKey).toLowerCase();
          final preview = conversation.lastMessage?.body.toLowerCase() ?? '';
          return name.contains(query) || preview.contains(query);
        })
        .toList(growable: false);
  }

  Future<void> _refresh() async {
    try {
      await ChatService.instance.refreshConversations();
      if (mounted) setState(() => _error = null);
    } catch (error) {
      if (mounted) setState(() => _error = error.toString());
    }
  }

  @override
  Widget build(BuildContext context) {
    final conversations = _visibleConversations;
    return ColoredBox(
      color: Colors.white,
      child: SafeArea(
        bottom: false,
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Padding(
              padding: const EdgeInsets.fromLTRB(20, 18, 20, 0),
              child: Row(
                children: [
                  const Expanded(
                    child: Text(
                      'Messages',
                      style: TextStyle(
                        color: MessagesPage.primaryNavy,
                        fontSize: 30,
                        fontWeight: FontWeight.w900,
                        letterSpacing: -0.5,
                      ),
                    ),
                  ),
                  ListenableBuilder(
                    listenable: ChatService.instance,
                    builder: (context, _) {
                      final connected = ChatService.instance.isConnected;
                      return Tooltip(
                        message: connected
                            ? 'Chat online'
                            : 'Chat reconnecting',
                        child: Container(
                          width: 10,
                          height: 10,
                          decoration: BoxDecoration(
                            shape: BoxShape.circle,
                            color: connected
                                ? const Color(0xFF22C55E)
                                : const Color(0xFFF59E0B),
                          ),
                        ),
                      );
                    },
                  ),
                ],
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 8),
              child: TextField(
                controller: _searchController,
                onChanged: (_) => setState(() {}),
                decoration: InputDecoration(
                  hintText: 'Search messages...',
                  prefixIcon: const Icon(
                    Icons.search,
                    color: Color(0xFF9CA3AF),
                  ),
                  filled: true,
                  fillColor: const Color(0xFFF8FAFD),
                  contentPadding: const EdgeInsets.symmetric(vertical: 13),
                  enabledBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: const BorderSide(color: Color(0xFFE5E7EB)),
                  ),
                  focusedBorder: OutlineInputBorder(
                    borderRadius: BorderRadius.circular(12),
                    borderSide: const BorderSide(
                      color: MessagesPage.primaryNavy,
                      width: 1.4,
                    ),
                  ),
                ),
              ),
            ),
            if (_error != null)
              Padding(
                padding: const EdgeInsets.fromLTRB(16, 4, 16, 4),
                child: Material(
                  color: const Color(0xFFFEF2F2),
                  borderRadius: BorderRadius.circular(10),
                  child: Padding(
                    padding: const EdgeInsets.all(12),
                    child: Row(
                      children: [
                        const Icon(
                          Icons.cloud_off_outlined,
                          color: Color(0xFFDC2626),
                        ),
                        const SizedBox(width: 10),
                        Expanded(
                          child: Text(
                            _error!,
                            style: const TextStyle(
                              color: Color(0xFF991B1B),
                              fontSize: 12,
                            ),
                          ),
                        ),
                        TextButton(
                          onPressed: _initialize,
                          child: const Text('Retry'),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            Expanded(
              child: _loading
                  ? const Center(child: CircularProgressIndicator())
                  : RefreshIndicator(
                      onRefresh: _refresh,
                      child: conversations.isEmpty
                          ? ListView(
                              children: const [
                                SizedBox(height: 150),
                                _MessagesEmptyState(),
                              ],
                            )
                          : ListView.separated(
                              padding: const EdgeInsets.only(
                                top: 4,
                                bottom: 12,
                              ),
                              itemCount: conversations.length,
                              separatorBuilder: (_, _) => const Divider(
                                height: 1,
                                color: Color(0xFFF1F5F9),
                                indent: 82,
                              ),
                              itemBuilder: (context, index) {
                                final conversation = conversations[index];
                                return _ConversationTile(
                                  conversation: conversation,
                                  actorKey: ChatService.instance.actorKey,
                                  onTap: () => Navigator.of(context).push(
                                    MaterialPageRoute(
                                      builder: (_) => ChatConversationScreen(
                                        conversation: conversation,
                                      ),
                                    ),
                                  ),
                                );
                              },
                            ),
                    ),
            ),
          ],
        ),
      ),
    );
  }
}

class _MessagesEmptyState extends StatelessWidget {
  const _MessagesEmptyState();

  @override
  Widget build(BuildContext context) {
    return const Padding(
      padding: EdgeInsets.symmetric(horizontal: 32),
      child: Column(
        children: [
          Icon(Icons.forum_outlined, size: 52, color: Color(0xFFCBD5E1)),
          SizedBox(height: 12),
          Text(
            'No conversations yet',
            style: TextStyle(
              color: MessagesPage.primaryNavy,
              fontSize: 17,
              fontWeight: FontWeight.w800,
            ),
          ),
          SizedBox(height: 6),
          Text(
            'When CampusHub support starts a conversation, it will appear here.',
            textAlign: TextAlign.center,
            style: TextStyle(
              color: Color(0xFF6B7280),
              fontSize: 13.5,
              height: 1.4,
            ),
          ),
        ],
      ),
    );
  }
}

class _ConversationTile extends StatelessWidget {
  const _ConversationTile({
    required this.conversation,
    required this.actorKey,
    required this.onTap,
  });

  final ChatConversation conversation;
  final String actorKey;
  final VoidCallback onTap;

  String get _name => conversation.displayNameFor(actorKey);

  String get _time {
    final date = conversation.lastMessage?.createdAt ?? conversation.updatedAt;
    final now = DateTime.now();
    if (now.difference(date).inDays == 0) {
      final hour = date.hour % 12 == 0 ? 12 : date.hour % 12;
      final minute = date.minute.toString().padLeft(2, '0');
      return '$hour:$minute ${date.hour >= 12 ? 'PM' : 'AM'}';
    }
    return '${date.month}/${date.day}/${date.year}';
  }

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      child: Padding(
        padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
        child: Row(
          children: [
            _ChatProfileAvatar(name: _name),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    _name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: MessagesPage.primaryNavy,
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  const SizedBox(height: 4),
                  Text(
                    conversation.lastMessage?.body ?? 'No messages yet',
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: Color(0xFF6B7280),
                      fontSize: 13.5,
                    ),
                  ),
                ],
              ),
            ),
            const SizedBox(width: 8),
            Column(
              crossAxisAlignment: CrossAxisAlignment.end,
              children: [
                Text(
                  _time,
                  style: const TextStyle(
                    color: Color(0xFF9CA3AF),
                    fontSize: 11,
                  ),
                ),
                if (conversation.unreadCount > 0) ...[
                  const SizedBox(height: 7),
                  Container(
                    constraints: const BoxConstraints(
                      minWidth: 20,
                      minHeight: 20,
                    ),
                    padding: const EdgeInsets.symmetric(horizontal: 5),
                    alignment: Alignment.center,
                    decoration: const BoxDecoration(
                      color: MessagesPage.primaryNavy,
                      shape: BoxShape.circle,
                    ),
                    child: Text(
                      '${conversation.unreadCount}',
                      style: const TextStyle(
                        color: Colors.white,
                        fontSize: 10,
                        fontWeight: FontWeight.w800,
                      ),
                    ),
                  ),
                ],
              ],
            ),
          ],
        ),
      ),
    );
  }
}

class ChatConversationScreen extends StatefulWidget {
  const ChatConversationScreen({super.key, required this.conversation});

  final ChatConversation conversation;

  @override
  State<ChatConversationScreen> createState() => _ChatConversationScreenState();
}

class _ChatConversationScreenState extends State<ChatConversationScreen> {
  final _messageController = TextEditingController();
  final _scrollController = ScrollController();
  final List<ChatMessage> _messages = [];
  StreamSubscription<ChatMessage>? _subscription;
  StreamSubscription<int>? _clearSubscription;
  StreamSubscription<ChatTypingEvent>? _typingSubscription;
  StreamSubscription<ChatReadEvent>? _readSubscription;
  Timer? _typingStopTimer;
  bool _loading = true;
  bool _sending = false;
  bool _typingActive = false;
  bool _remoteTyping = false;
  String _remoteTypingName = '';
  int _peerLastReadId = 0;
  String? _error;

  @override
  void initState() {
    super.initState();
    _peerLastReadId = widget.conversation.peerLastReadId(
      ChatService.instance.actorKey,
    );
    _messageController.addListener(_onComposerChanged);
    _subscription = ChatService.instance.messages.listen((message) {
      if (message.conversationId != widget.conversation.id || !mounted) return;
      setState(() {
        _remoteTyping = false;
        _remoteTypingName = '';
        _upsertMessage(message);
      });
      if (message.senderKey != ChatService.instance.actorKey) {
        _markRead();
      }
      _scrollToBottom();
    });
    _clearSubscription = ChatService.instance.clearedConversations.listen((
      conversationId,
    ) {
      if (conversationId != widget.conversation.id || !mounted) return;
      setState(() => _messages.clear());
    });
    _typingSubscription = ChatService.instance.typingEvents.listen((event) {
      if (event.conversationId != widget.conversation.id || !mounted) return;
      setState(() {
        _remoteTyping = event.isTyping;
        _remoteTypingName = event.isTyping ? event.name : '';
      });
      if (event.isTyping) _scrollToBottom();
    });
    _readSubscription = ChatService.instance.readEvents.listen((event) {
      if (event.conversationId != widget.conversation.id || !mounted) return;
      if (event.actorKey == ChatService.instance.actorKey) return;
      setState(() {
        _peerLastReadId = event.lastReadMessageId;
        _applyDeliveryStatuses();
      });
    });
    _load();
  }

  @override
  void dispose() {
    _typingStopTimer?.cancel();
    if (_typingActive) {
      ChatService.instance.sendTyping(widget.conversation.id, isTyping: false);
    }
    _subscription?.cancel();
    _clearSubscription?.cancel();
    _typingSubscription?.cancel();
    _readSubscription?.cancel();
    _messageController.removeListener(_onComposerChanged);
    _messageController.dispose();
    _scrollController.dispose();
    super.dispose();
  }

  void _upsertMessage(ChatMessage message) {
    // Replace optimistic sending bubble when server confirms.
    final pendingIndex = _messages.indexWhere(
      (item) =>
          item.isLocalPending &&
          item.body == message.body &&
          item.senderKey == message.senderKey,
    );
    if (pendingIndex >= 0 && !message.isLocalPending) {
      _messages[pendingIndex] = message.copyWith(
        deliveryStatus: _statusFor(message),
        clientKey: _messages[pendingIndex].clientKey,
      );
      _applyDeliveryStatuses();
      return;
    }
    if (_messages.any((item) => item.id == message.id && message.id > 0)) {
      return;
    }
    if (message.clientKey != null &&
        _messages.any((item) => item.clientKey == message.clientKey)) {
      final index = _messages.indexWhere(
        (item) => item.clientKey == message.clientKey,
      );
      _messages[index] = message.copyWith(deliveryStatus: _statusFor(message));
      _applyDeliveryStatuses();
      return;
    }
    _messages.add(message.copyWith(deliveryStatus: _statusFor(message)));
    _applyDeliveryStatuses();
  }

  ChatDeliveryStatus _statusFor(ChatMessage message) {
    if (message.deliveryStatus == ChatDeliveryStatus.sending ||
        message.isLocalPending) {
      return ChatDeliveryStatus.sending;
    }
    if (message.id > 0 && _peerLastReadId >= message.id) {
      return ChatDeliveryStatus.seen;
    }
    return ChatDeliveryStatus.delivered;
  }

  void _applyDeliveryStatuses() {
    for (var i = 0; i < _messages.length; i++) {
      final message = _messages[i];
      if (message.senderKey != ChatService.instance.actorKey) continue;
      if (message.deliveryStatus == ChatDeliveryStatus.sending) continue;
      _messages[i] = message.copyWith(deliveryStatus: _statusFor(message));
    }
  }

  void _onComposerChanged() {
    final hasText = _messageController.text.trim().isNotEmpty;
    if (hasText) {
      if (!_typingActive) {
        _typingActive = true;
        ChatService.instance.sendTyping(widget.conversation.id, isTyping: true);
      }
      _typingStopTimer?.cancel();
      _typingStopTimer = Timer(const Duration(milliseconds: 1600), () {
        if (!_typingActive) return;
        _typingActive = false;
        ChatService.instance.sendTyping(
          widget.conversation.id,
          isTyping: false,
        );
      });
    } else if (_typingActive) {
      _typingStopTimer?.cancel();
      _typingActive = false;
      ChatService.instance.sendTyping(widget.conversation.id, isTyping: false);
    }
  }

  Future<void> _load() async {
    try {
      final rows = await ChatService.instance.loadMessages(
        widget.conversation.id,
      );
      await ChatService.instance.refreshConversations();
      ChatConversation? latest;
      for (final item in ChatService.instance.conversations) {
        if (item.id == widget.conversation.id) {
          latest = item;
          break;
        }
      }
      _peerLastReadId =
          latest?.peerLastReadId(ChatService.instance.actorKey) ??
          widget.conversation.peerLastReadId(ChatService.instance.actorKey);
      _messages
        ..clear()
        ..addAll(
          rows.map(
            (message) => message.copyWith(deliveryStatus: _statusFor(message)),
          ),
        );
      _applyDeliveryStatuses();
      _markRead();
    } catch (error) {
      _error = error.toString();
    }
    if (mounted) {
      setState(() => _loading = false);
      _scrollToBottom();
    }
  }

  void _markRead() {
    if (_messages.isEmpty) return;
    unawaited(
      ChatService.instance.markRead(widget.conversation.id, _messages.last.id),
    );
  }

  void _scrollToBottom() {
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (!_scrollController.hasClients) return;
      _scrollController.animateTo(
        _scrollController.position.maxScrollExtent,
        duration: const Duration(milliseconds: 220),
        curve: Curves.easeOut,
      );
    });
  }

  Future<void> _send() async {
    final text = _messageController.text.trim();
    if (text.isEmpty || _sending) return;
    _typingStopTimer?.cancel();
    if (_typingActive) {
      _typingActive = false;
      ChatService.instance.sendTyping(widget.conversation.id, isTyping: false);
    }
    setState(() => _sending = true);
    _messageController.clear();
    try {
      await ChatService.instance.sendMessage(widget.conversation.id, text);
    } catch (error) {
      _messageController.text = text;
      if (mounted) {
        ScaffoldMessenger.of(
          context,
        ).showSnackBar(SnackBar(content: Text(error.toString())));
      }
    }
    if (mounted) setState(() => _sending = false);
  }

  void _showAddMenu() {
    showModalBottomSheet<void>(
      context: context,
      showDragHandle: true,
      builder: (sheetContext) => SafeArea(
        child: Column(
          mainAxisSize: MainAxisSize.min,
          children: [
            const ListTile(
              title: Text(
                'Add to message',
                style: TextStyle(fontWeight: FontWeight.w800),
              ),
            ),
            ListTile(
              leading: const Icon(Icons.photo_outlined),
              title: const Text('Photo'),
              onTap: () => _showAttachmentNotice(sheetContext),
            ),
            ListTile(
              leading: const Icon(Icons.insert_drive_file_outlined),
              title: const Text('Document'),
              onTap: () => _showAttachmentNotice(sheetContext),
            ),
          ],
        ),
      ),
    );
  }

  void _showAttachmentNotice(BuildContext sheetContext) {
    Navigator.of(sheetContext).pop();
    ScaffoldMessenger.of(context).showSnackBar(
      const SnackBar(content: Text('Attachment upload is coming soon.')),
    );
  }

  Future<void> _clearChat() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: const Text('Clear chat?'),
        content: const Text('This removes all messages but keeps the chat.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.of(dialogContext).pop(true),
            child: const Text('Clear'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    try {
      await ChatService.instance.clearMessages(widget.conversation.id);
      if (mounted) setState(() => _messages.clear());
    } catch (error) {
      if (!mounted) return;
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text(error.toString())));
    }
  }

  @override
  Widget build(BuildContext context) {
    final actorKey = ChatService.instance.actorKey;
    final name = widget.conversation.displayNameFor(actorKey);
    return Scaffold(
      backgroundColor: const Color(0xFFF8FAFC),
      appBar: AppBar(
        backgroundColor: MessagesPage.primaryNavy,
        foregroundColor: Colors.white,
        titleSpacing: 0,
        title: Row(
          children: [
            _ChatProfileAvatar(
              name: name,
              size: 36,
              fontSize: 12,
              borderWidth: 1.5,
            ),
            const SizedBox(width: 10),
            Expanded(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontSize: 16,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                  Text(
                    _remoteTyping
                        ? '$_remoteTypingName is typing…'
                        : ChatService.instance.isConnected
                        ? 'Online'
                        : 'Connecting…',
                    style: const TextStyle(
                      color: Color(0xFFCBD5E1),
                      fontSize: 11,
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
        actions: [
          PopupMenuButton<String>(
            icon: const Icon(Icons.more_vert_rounded),
            onSelected: (value) {
              if (value == 'clear') _clearChat();
            },
            itemBuilder: (_) => const [
              PopupMenuItem<String>(value: 'clear', child: Text('Clear chat')),
            ],
          ),
        ],
      ),
      body: Column(
        children: [
          if (_error != null)
            MaterialBanner(
              content: Text(_error!),
              actions: [
                TextButton(onPressed: _load, child: const Text('Retry')),
              ],
            ),
          Expanded(
            child: _loading
                ? const Center(child: CircularProgressIndicator())
                : _messages.isEmpty && !_remoteTyping
                ? const Center(
                    child: Text(
                      'Send the first message',
                      style: TextStyle(color: Color(0xFF94A3B8)),
                    ),
                  )
                : ListView.builder(
                    controller: _scrollController,
                    padding: const EdgeInsets.all(14),
                    itemCount: _messages.length + (_remoteTyping ? 1 : 0),
                    itemBuilder: (context, index) {
                      if (_remoteTyping && index == _messages.length) {
                        return Align(
                          alignment: Alignment.centerLeft,
                          child: Padding(
                            padding: const EdgeInsets.only(bottom: 14),
                            child: Row(
                              mainAxisSize: MainAxisSize.min,
                              crossAxisAlignment: CrossAxisAlignment.end,
                              children: [
                                _ChatProfileAvatar(
                                  name: _remoteTypingName.isNotEmpty
                                      ? _remoteTypingName
                                      : name,
                                  size: 34,
                                  fontSize: 11,
                                  borderWidth: 1.5,
                                ),
                                const SizedBox(width: 8),
                                Container(
                                  padding: const EdgeInsets.symmetric(
                                    horizontal: 14,
                                    vertical: 10,
                                  ),
                                  decoration: BoxDecoration(
                                    color: const Color(0xFFEEF2F7),
                                    borderRadius: BorderRadius.circular(12),
                                    border: Border.all(
                                      color: const Color(0xFFE2E8F0),
                                    ),
                                  ),
                                  child: const _TypingDots(),
                                ),
                              ],
                            ),
                          ),
                        );
                      }
                      final message = _messages[index];
                      final outgoing = message.senderKey == actorKey;
                      final lastOutgoingIndex = _messages.lastIndexWhere(
                        (item) => item.senderKey == actorKey,
                      );
                      final nextMessage = index + 1 < _messages.length
                          ? _messages[index + 1]
                          : null;
                      return _MessageBubble(
                        message: message,
                        outgoing: outgoing,
                        peerName: name,
                        showTimestamp:
                            nextMessage == null ||
                            nextMessage.senderKey != message.senderKey,
                        showDeliveryStatus:
                            outgoing && index == lastOutgoingIndex,
                      );
                    },
                  ),
          ),
          SafeArea(
            top: false,
            child: Container(
              padding: const EdgeInsets.fromLTRB(12, 9, 8, 9),
              decoration: const BoxDecoration(
                color: Colors.white,
                border: Border(top: BorderSide(color: Color(0xFFE5E7EB))),
              ),
              child: Row(
                children: [
                  IconButton.filledTonal(
                    onPressed: _showAddMenu,
                    style: IconButton.styleFrom(
                      backgroundColor: const Color(0xFFE8E8F2),
                      foregroundColor: MessagesPage.primaryNavy,
                    ),
                    icon: const Icon(Icons.add_rounded),
                    tooltip: 'Add attachment',
                  ),
                  const SizedBox(width: 6),
                  Expanded(
                    child: TextField(
                      controller: _messageController,
                      minLines: 1,
                      maxLines: 4,
                      maxLength: 2000,
                      textCapitalization: TextCapitalization.sentences,
                      decoration: InputDecoration(
                        hintText: 'Type a message',
                        counterText: '',
                        filled: true,
                        fillColor: const Color(0xFFF1F5F9),
                        border: OutlineInputBorder(
                          borderRadius: BorderRadius.circular(22),
                          borderSide: BorderSide.none,
                        ),
                        contentPadding: const EdgeInsets.symmetric(
                          horizontal: 16,
                          vertical: 10,
                        ),
                      ),
                      onSubmitted: (_) => _send(),
                    ),
                  ),
                  const SizedBox(width: 6),
                  IconButton.filled(
                    onPressed: _sending ? null : _send,
                    style: IconButton.styleFrom(
                      backgroundColor: MessagesPage.primaryNavy,
                      foregroundColor: Colors.white,
                    ),
                    icon: _sending
                        ? const SizedBox(
                            width: 18,
                            height: 18,
                            child: CircularProgressIndicator(
                              strokeWidth: 2,
                              color: Colors.white,
                            ),
                          )
                        : const Icon(Icons.send_rounded),
                  ),
                ],
              ),
            ),
          ),
        ],
      ),
    );
  }
}

class _MessageBubble extends StatelessWidget {
  const _MessageBubble({
    required this.message,
    required this.outgoing,
    required this.peerName,
    required this.showTimestamp,
    this.showDeliveryStatus = false,
  });

  final ChatMessage message;
  final bool outgoing;
  final String peerName;
  final bool showTimestamp;
  final bool showDeliveryStatus;

  String get _deliveryLabel {
    switch (message.deliveryStatus) {
      case ChatDeliveryStatus.sending:
        return 'Sending';
      case ChatDeliveryStatus.seen:
        return 'Seen';
      case ChatDeliveryStatus.delivered:
        return 'Delivered';
    }
  }

  @override
  Widget build(BuildContext context) {
    final date = message.createdAt;
    final hour = date.hour % 12 == 0 ? 12 : date.hour % 12;
    final minute = date.minute.toString().padLeft(2, '0');
    final time = '$hour:$minute ${date.hour >= 12 ? 'PM' : 'AM'}';
    final avatarName = message.senderName.isNotEmpty
        ? message.senderName
        : (outgoing ? 'You' : peerName);
    final bubble = Container(
      constraints: BoxConstraints(
        maxWidth: MediaQuery.sizeOf(context).width * 0.70,
      ),
      padding: const EdgeInsets.symmetric(horizontal: 14, vertical: 10),
      decoration: BoxDecoration(
        color: outgoing ? MessagesPage.primaryNavy : const Color(0xFFEEF2F7),
        borderRadius: BorderRadius.circular(25),
      ),
      child: Text(
        message.body,
        style: TextStyle(
          color: outgoing ? Colors.white : const Color(0xFF0F172A),
          fontSize: 15,
          height: 1.3,
        ),
      ),
    );
    final avatar = _ChatProfileAvatar(
      name: avatarName,
      size: 40,
      fontSize: 12,
      borderWidth: 1.5,
    );
    return Padding(
      padding: const EdgeInsets.only(bottom: 14),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Align(
            alignment: outgoing ? Alignment.centerRight : Alignment.centerLeft,
            child: Column(
              crossAxisAlignment: outgoing
                  ? CrossAxisAlignment.end
                  : CrossAxisAlignment.start,
              children: [
                Row(
                  mainAxisSize: MainAxisSize.min,
                  crossAxisAlignment: CrossAxisAlignment.end,
                  children: outgoing
                      ? [bubble]
                      : [avatar, const SizedBox(width: 8), bubble],
                ),
                if (showDeliveryStatus) ...[
                  const SizedBox(height: 4),
                  Text(
                    _deliveryLabel,
                    style: const TextStyle(
                      color: Color(0xFF94A3B8),
                      fontSize: 11,
                      fontWeight: FontWeight.w700,
                    ),
                  ),
                ],
              ],
            ),
          ),
          if (showTimestamp) ...[
            const SizedBox(height: 4),
            Padding(
              padding: EdgeInsets.only(left: outgoing ? 0 : 48),
              child: Align(
                alignment: outgoing
                    ? Alignment.centerRight
                    : Alignment.centerLeft,
                child: Text(
                  time,
                  style: const TextStyle(
                    color: Color(0xFF94A3B8),
                    fontSize: 10,
                    fontWeight: FontWeight.w600,
                  ),
                ),
              ),
            ),
          ],
        ],
      ),
    );
  }
}
