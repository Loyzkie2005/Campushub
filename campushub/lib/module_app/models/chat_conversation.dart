import 'chat_message.dart';

class ChatParticipant {
  const ChatParticipant({
    required this.actorKey,
    required this.displayName,
    this.lastReadMessageId,
  });

  final String actorKey;
  final String displayName;
  final int? lastReadMessageId;

  factory ChatParticipant.fromJson(Map<String, dynamic> json) {
    return ChatParticipant(
      actorKey: json['actor_key']?.toString() ?? '',
      displayName:
          json['display_name']?.toString() ??
          json['name']?.toString() ??
          'CampusHub User',
      lastReadMessageId: json['last_read_message_id'] == null
          ? null
          : _asInt(json['last_read_message_id']),
    );
  }

  static int _asInt(dynamic value) {
    return value is int ? value : int.tryParse('$value') ?? 0;
  }
}

class ChatConversation {
  const ChatConversation({
    required this.id,
    required this.title,
    required this.participants,
    this.lastMessage,
    required this.updatedAt,
    this.unreadCount = 0,
  });

  final int id;
  final String title;
  final List<ChatParticipant> participants;
  final ChatMessage? lastMessage;
  final DateTime updatedAt;
  final int unreadCount;

  factory ChatConversation.fromJson(Map<String, dynamic> json) {
    final rawParticipants = json['participants'];
    final rawLastMessage = json['last_message'];
    return ChatConversation(
      id: _asInt(json['id']),
      title: json['title']?.toString() ?? '',
      participants: rawParticipants is List
          ? rawParticipants
                .whereType<Map>()
                .map(
                  (item) =>
                      ChatParticipant.fromJson(Map<String, dynamic>.from(item)),
                )
                .toList(growable: false)
          : const [],
      lastMessage: rawLastMessage is Map
          ? ChatMessage.fromJson(Map<String, dynamic>.from(rawLastMessage))
          : null,
      updatedAt:
          DateTime.tryParse(json['updated_at']?.toString() ?? '')?.toLocal() ??
          DateTime.now(),
      unreadCount: _asInt(json['unread_count']),
    );
  }

  ChatParticipant? otherParticipant(String actorKey) {
    for (final participant in participants) {
      if (participant.actorKey != actorKey) return participant;
    }
    return participants.isEmpty ? null : participants.first;
  }

  String displayNameFor(String actorKey) {
    return otherParticipant(actorKey)?.displayName ??
        (title.isEmpty ? 'Conversation' : title);
  }

  int peerLastReadId(String actorKey) {
    return otherParticipant(actorKey)?.lastReadMessageId ?? 0;
  }

  static int _asInt(dynamic value) {
    return value is int ? value : int.tryParse('$value') ?? 0;
  }
}
