enum ChatDeliveryStatus { sending, delivered, seen }

class ChatMessage {
  const ChatMessage({
    required this.id,
    required this.conversationId,
    required this.senderKey,
    required this.senderName,
    required this.body,
    required this.createdAt,
    this.deliveryStatus = ChatDeliveryStatus.delivered,
    this.clientKey,
  });

  final int id;
  final int conversationId;
  final String senderKey;
  final String senderName;
  final String body;
  final DateTime createdAt;
  final ChatDeliveryStatus deliveryStatus;
  final String? clientKey;

  bool get isLocalPending =>
      deliveryStatus == ChatDeliveryStatus.sending || (clientKey != null && id <= 0);

  factory ChatMessage.fromJson(Map<String, dynamic> json) {
    return ChatMessage(
      id: _asInt(json['id']),
      conversationId: _asInt(json['conversation_id']),
      senderKey:
          json['sender_actor_key']?.toString() ??
          json['sender_key']?.toString() ??
          '',
      senderName: json['sender_name']?.toString() ?? '',
      body: json['body']?.toString() ?? '',
      createdAt:
          DateTime.tryParse(json['created_at']?.toString() ?? '')?.toLocal() ??
          DateTime.now(),
      deliveryStatus: ChatDeliveryStatus.delivered,
    );
  }

  ChatMessage copyWith({
    int? id,
    int? conversationId,
    String? senderKey,
    String? senderName,
    String? body,
    DateTime? createdAt,
    ChatDeliveryStatus? deliveryStatus,
    String? clientKey,
  }) {
    return ChatMessage(
      id: id ?? this.id,
      conversationId: conversationId ?? this.conversationId,
      senderKey: senderKey ?? this.senderKey,
      senderName: senderName ?? this.senderName,
      body: body ?? this.body,
      createdAt: createdAt ?? this.createdAt,
      deliveryStatus: deliveryStatus ?? this.deliveryStatus,
      clientKey: clientKey ?? this.clientKey,
    );
  }

  static int _asInt(dynamic value) {
    return value is int ? value : int.tryParse('$value') ?? 0;
  }
}
