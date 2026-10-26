import 'dart:convert';
import 'facility_item.dart';

/// Public catalog data; does not treat a service as a physical reservation.
class ServiceItem {
  ServiceItem.fromJson(Map<String, dynamic> json)
    : facility = FacilityItem.fromJson({
        ...json,
        if (json['images'] is List && (json['images'] as List).isNotEmpty)
          'image_url': jsonEncode(json['images']),
      }),
      category = '${json['category_label'] ?? ''}',
      active = json['status'] == 'active',
      information = (json['information'] as List? ?? const [])
          .whereType<Map>()
          .map(
            (row) => MapEntry('${row['label'] ?? ''}', '${row['value'] ?? ''}'),
          )
          .toList();

  final FacilityItem facility;
  final String category;
  final bool active;
  final List<MapEntry<String, String>> information;
  String get id => facility.id;
  String get name => facility.name;
  String get kind => switch (facility.facilityType) {
    'food_analysis' => 'laboratory',
    'training_kitchen' => 'assessment',
    'lease_space' => 'lease',
    _ => switch (facility.bookingMode) {
      'assessment' => 'assessment',
      'lease' => 'lease',
      _ => 'service',
    },
  };
  String get actionLabel => 'How to Request This Service';
}
