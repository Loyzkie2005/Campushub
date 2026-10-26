/// Routing data only. Server ownership/authentication is checked again on open.
class ProductNotificationTarget {
  const ProductNotificationTarget({
    required this.productId,
    required this.recipientId,
    required this.type,
    required this.deliveryId,
  });
  final int productId, recipientId;
  final String type, deliveryId;

  String get key => '$recipientId/$type/$productId/$deliveryId';
  Map<String, String> toJson() => {
    'product_id': '$productId',
    'recipient_id': '$recipientId',
    'type': type,
    'delivery_id': deliveryId,
  };

  static ProductNotificationTarget? fromJson(Map<String, dynamic> data) {
    final product = int.tryParse('${data['product_id']}');
    final recipient = int.tryParse('${data['recipient_id']}');
    final type = data['type'];
    final delivery = '${data['delivery_id'] ?? ''}';
    if (product == null ||
        product <= 0 ||
        recipient == null ||
        recipient <= 0 ||
        !const ['product_approved', 'product_rejected'].contains(type) ||
        !RegExp(r'^\d{1,20}$').hasMatch(delivery)) {
      return null;
    }
    return ProductNotificationTarget(
      productId: product,
      recipientId: recipient,
      type: type as String,
      deliveryId: delivery,
    );
  }
}
