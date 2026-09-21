import 'dart:async';
import 'dart:convert';

import 'package:flutter/foundation.dart';
import 'package:http/http.dart' as http;
import 'package:web_socket_channel/web_socket_channel.dart';

import '../config/api_config.dart';
import '../models/chat_conversation.dart';
import '../models/chat_message.dart';
import '../session/session_service.dart';

class ChatService extends ChangeNotifier {
  ChatService._();

  static final ChatService instance = ChatService._();

  final _messageController = StreamController<ChatMessage>.broadcast();
  final _clearedConversationController = StreamController<int>.broadcast();
  final _typingController = StreamController<ChatTypingEvent>.broadcast();
  final _readController = StreamController<ChatReadEvent>.broadcast();
  final List<ChatConversation> _conversations = [];
  int _localMessageSeq = 0;

  WebSocketChannel? _channel;
  StreamSubscription<dynamic>? _socketSubscription;
  Timer? _reconnectTimer;
  String? _token;
  String? _actorKey;
  bool _connected = false;
  bool _connecting = false;
  int _reconnectAttempt = 0;

  List<ChatConversation> get conversations => List.unmodifiable(_conversations);
  Stream<ChatMessage> get messages => _messageController.stream;
  Stream<int> get clearedConversations => _clearedConversationController.stream;
  Stream<ChatTypingEvent> get typingEvents => _typingController.stream;
  Stream<ChatReadEvent> get readEvents => _readController.stream;
  String get actorKey => _actorKey ?? '';
  bool get isConnected => _connected;

  Future<bool> initialize() async {
    _token ??= await SessionService.loadChatToken();
    final user = await SessionService.loadUser();
    if (_token == null || _token!.isEmpty || user == null) return false;
    _actorKey = 'mobile:${user.id}';
    await refreshConversations();
    await _connect();
    return true;
  }

  Map<String, String> get _headers => {
    'Accept': 'application/json',
    'Content-Type': 'application/json',
    if (_token != null) 'Authorization': 'Bearer $_token',
  };

  Future<dynamic> _request(
    String path, {
    String method = 'GET',
    Object? body,
  }) async {
    final uri = Uri.parse('${ApiConfig.chatHttpUrl}$path');
    late http.Response response;
    try {
      if (method == 'POST') {
        response = await http
            .post(
              uri,
              headers: _headers,
              body: body == null ? null : jsonEncode(body),
            )
            .timeout(const Duration(seconds: 12));
      } else if (method == 'DELETE') {
        response = await http
            .delete(uri, headers: _headers)
            .timeout(const Duration(seconds: 12));
      } else {
        response = await http
            .get(uri, headers: _headers)
            .timeout(const Duration(seconds: 12));
      }
    } on TimeoutException {
      throw const ChatException(
        'Chat service timed out. Check that the chat service is running on port 8001 and that the phone is on the same Wi-Fi or hotspot.',
      );
    } on http.ClientException {
      throw const ChatException(
        'Unable to reach the chat service. Check the server address and port 8001.',
      );
    }

    dynamic decoded;
    try {
      decoded = response.body.isEmpty ? null : jsonDecode(response.body);
    } on FormatException {
      throw const ChatException(
        'Chat service returned an invalid response. Make sure the chat service is running on port 8001.',
      );
    }
    if (response.statusCode < 200 || response.statusCode >= 300) {
      final detail = decoded is Map
          ? decoded['detail'] ?? decoded['error']
          : null;
      throw ChatException(detail?.toString() ?? 'Chat request failed.');
    }
    return decoded;
  }

  List<dynamic> _listFrom(dynamic payload, String key) {
    if (payload is List) return payload;
    if (payload is Map && payload[key] is List) {
      return payload[key] as List;
    }
    if (payload is Map && payload['items'] is List) {
      return payload['items'] as List;
    }
    return const [];
  }

  Future<void> refreshConversations() async {
    if (_token == null || _token!.isEmpty) return;
    final payload = await _request('/conversations');
    final rows = _listFrom(payload, 'conversations');
    _conversations
      ..clear()
      ..addAll(
        rows.whereType<Map>().map(
          (row) => ChatConversation.fromJson(Map<String, dynamic>.from(row)),
        ),
      );
    notifyListeners();
  }

  Future<List<ChatMessage>> loadMessages(
    int conversationId, {
    int limit = 100,
  }) async {
    final payload = await _request(
      '/conversations/$conversationId/messages?limit=$limit',
    );
    return _listFrom(payload, 'messages')
        .whereType<Map>()
        .map((row) => ChatMessage.fromJson(Map<String, dynamic>.from(row)))
        .toList(growable: false);
  }

  Future<ChatConversation> createConversation({
    required String participantActorKey,
    required String participantDisplayName,
    String? contextKey,
  }) async {
    final payload = await _request(
      '/conversations',
      method: 'POST',
      body: {
        'participant': {
          'actor_key': participantActorKey,
          'display_name': participantDisplayName,
        },
        if (contextKey != null && contextKey.trim().isNotEmpty)
          'context_key': contextKey.trim(),
      },
    );
    final raw = payload is Map && payload['conversation'] is Map
        ? payload['conversation'] as Map
        : payload as Map;
    final conversation = ChatConversation.fromJson(
      Map<String, dynamic>.from(raw),
    );
    await refreshConversations();
    return conversation;
  }

  Future<bool> isActorOnline(String actorKey) async {
    final encodedActorKey = Uri.encodeComponent(actorKey);
    final payload = await _request('/presence/$encodedActorKey');
    return payload is Map && payload['online'] == true;
  }

  Future<ChatMessage> sendMessage(int conversationId, String text) async {
    final body = text.trim();
    if (body.isEmpty || body.length > 2000) {
      throw const ChatException('Message cannot be empty.');
    }
    _localMessageSeq += 1;
    final clientKey = 'local-$_localMessageSeq';
    final optimistic = ChatMessage(
      id: -_localMessageSeq,
      conversationId: conversationId,
      senderKey: actorKey,
      senderName: 'You',
      body: body,
      createdAt: DateTime.now(),
      deliveryStatus: ChatDeliveryStatus.sending,
      clientKey: clientKey,
    );
    _messageController.add(optimistic);

    if (_connected && _channel != null) {
      _channel!.sink.add(
        jsonEncode({
          'type': 'message.send',
          'conversation_id': conversationId,
          'body': body,
        }),
      );
      return optimistic;
    }

    final payload = await _request(
      '/conversations/$conversationId/messages',
      method: 'POST',
      body: {'body': body},
    );
    final raw = payload is Map && payload['message'] is Map
        ? payload['message'] as Map
        : payload as Map;
    final confirmed = ChatMessage.fromJson(
      Map<String, dynamic>.from(raw),
    ).copyWith(clientKey: clientKey);
    _messageController.add(confirmed);
    await refreshConversations();
    return confirmed;
  }

  void sendTyping(int conversationId, {required bool isTyping}) {
    if (!_connected || _channel == null) return;
    _channel!.sink.add(
      jsonEncode({
        'type': isTyping ? 'typing.start' : 'typing.stop',
        'conversation_id': conversationId,
      }),
    );
  }

  Future<void> markRead(int conversationId, int messageId) async {
    await _request(
      '/conversations/$conversationId/read',
      method: 'POST',
      body: {'message_id': messageId},
    );
  }

  Future<void> clearMessages(int conversationId) async {
    await _request('/conversations/$conversationId/messages', method: 'DELETE');
    _clearedConversationController.add(conversationId);
    await refreshConversations();
  }

  Future<void> _connect() async {
    if (_connecting || _connected || _token == null) return;
    _connecting = true;
    try {
      final channel = WebSocketChannel.connect(
        Uri.parse(ApiConfig.chatWebSocketUrl),
      );
      await channel.ready.timeout(const Duration(seconds: 8));
      _channel = channel;
      _socketSubscription = channel.stream.listen(
        _handleSocketEvent,
        onError: (_) => _handleDisconnect(),
        onDone: _handleDisconnect,
        cancelOnError: true,
      );
      channel.sink.add(jsonEncode({'type': 'auth', 'token': _token}));
    } catch (_) {
      _scheduleReconnect();
    } finally {
      _connecting = false;
    }
  }

  void _handleSocketEvent(dynamic raw) {
    try {
      final event = jsonDecode(raw.toString()) as Map<String, dynamic>;
      final type = event['type']?.toString();
      if (type == 'auth.ok' || type == 'authenticated') {
        _connected = true;
        _reconnectAttempt = 0;
        notifyListeners();
        return;
      }
      if (type == 'message.created' && event['message'] is Map) {
        final message = ChatMessage.fromJson(
          Map<String, dynamic>.from(event['message'] as Map),
        );
        _messageController.add(message);
        unawaited(refreshConversations());
        return;
      }
      if (type == 'typing.start' || type == 'typing.stop') {
        final conversationId = int.tryParse(
          event['conversation_id']?.toString() ?? '',
        );
        final senderKey = event['actor_key']?.toString() ?? '';
        if (conversationId == null || senderKey.isEmpty) return;
        if (senderKey == _actorKey) return;
        _typingController.add(
          ChatTypingEvent(
            conversationId: conversationId,
            actorKey: senderKey,
            name: event['name']?.toString() ?? 'Someone',
            isTyping: type == 'typing.start',
          ),
        );
        return;
      }
      if (type == 'conversation.deleted') {
        final conversationId = int.tryParse(
          event['conversation_id']?.toString() ?? '',
        );
        if (conversationId != null) {
          _conversations.removeWhere((item) => item.id == conversationId);
          notifyListeners();
        }
        return;
      }
      if (type == 'conversation.cleared') {
        final conversationId = int.tryParse(
          event['conversation_id']?.toString() ?? '',
        );
        if (conversationId != null) {
          _clearedConversationController.add(conversationId);
          unawaited(refreshConversations());
        }
        return;
      }
      if (type == 'conversation.updated') {
        final read = event['read'];
        if (read is Map) {
          final conversationId = int.tryParse(
            read['conversation_id']?.toString() ?? '',
          );
          final readerKey = read['actor_key']?.toString() ?? '';
          final lastReadId = int.tryParse(
            read['last_read_message_id']?.toString() ?? '',
          );
          if (conversationId != null &&
              readerKey.isNotEmpty &&
              lastReadId != null) {
            _readController.add(
              ChatReadEvent(
                conversationId: conversationId,
                actorKey: readerKey,
                lastReadMessageId: lastReadId,
              ),
            );
          }
        }
        unawaited(refreshConversations());
      }
    } catch (_) {
      // Ignore malformed frames without terminating the chat stream.
    }
  }

  void _handleDisconnect() {
    _connected = false;
    _channel = null;
    _socketSubscription = null;
    notifyListeners();
    _scheduleReconnect();
  }

  void _scheduleReconnect() {
    _connected = false;
    _reconnectTimer?.cancel();
    _reconnectAttempt += 1;
    final seconds = (1 << _reconnectAttempt.clamp(0, 4));
    _reconnectTimer = Timer(Duration(seconds: seconds), _connect);
  }

  Future<void> disconnect() async {
    _reconnectTimer?.cancel();
    await _socketSubscription?.cancel();
    await _channel?.sink.close();
    _channel = null;
    _connected = false;
    _token = null;
    _actorKey = null;
    _conversations.clear();
    notifyListeners();
  }
}

class ChatException implements Exception {
  const ChatException(this.message);

  final String message;

  @override
  String toString() => message;
}

class ChatTypingEvent {
  const ChatTypingEvent({
    required this.conversationId,
    required this.actorKey,
    required this.name,
    required this.isTyping,
  });

  final int conversationId;
  final String actorKey;
  final String name;
  final bool isTyping;
}

class ChatReadEvent {
  const ChatReadEvent({
    required this.conversationId,
    required this.actorKey,
    required this.lastReadMessageId,
  });

  final int conversationId;
  final String actorKey;
  final int lastReadMessageId;
}
