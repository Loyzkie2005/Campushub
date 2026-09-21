import 'dart:convert';

import 'package:flutter/material.dart';

import '../config/api_config.dart';

class FacilityItem {
  const FacilityItem({
    required this.id,
    required this.name,
    required this.facilityType,
    required this.facilityTypeLabel,
    required this.status,
    required this.capacity,
    required this.rate,
    required this.priceType,
    required this.bookingMode,
    required this.roomType,
    required this.slots,
    required this.rating,
    required this.reviews,
    required this.icon,
    required this.imageUrl,
    this.description = '',
    this.amenities = const [],
    this.requirements = '',
    this.termsConditions = '',
    this.location = '',
  });

  factory FacilityItem.fromJson(Map<String, dynamic> json) {
    final statusKey = (json['status'] as String? ?? 'available').toLowerCase();
    final statusLabel = switch (statusKey) {
      'available' => 'Open for Booking',
      'unavailable' || 'reserved' || 'occupied' => 'Temporarily Unavailable',
      'maintenance' => 'Under Maintenance',
      'inactive' => 'Inactive',
      _ => 'Temporarily Unavailable',
    };

    final rawAmenities = json['amenities'];
    final amenities = rawAmenities is List
        ? rawAmenities.map((e) => e.toString()).toList()
        : <String>[];

    final name = json['name'] as String? ?? 'Untitled Facility';
    final facilityType = (json['facility_type'] as String? ?? 'other');
    final facilityTypeLabel =
        (json['facility_type_label'] as String?)?.trim().isNotEmpty == true
        ? (json['facility_type_label'] as String)
        : labelForFacilityType(facilityType);

    return FacilityItem(
      id: (json['id'] as String? ?? ''),
      name: name,
      facilityType: facilityType,
      facilityTypeLabel: facilityTypeLabel,
      status: statusLabel,
      capacity: (json['capacity'] ?? 0).toString(),
      rate: (json['rate']?.toString() ?? '0'),
      priceType: (json['price_type'] as String? ?? 'hour'),
      bookingMode: (json['booking_mode'] as String? ?? 'room'),
      roomType: (json['room_type'] as String? ?? ''),
      slots: (json['slots'] as String? ?? ''),
      rating: (json['rating']?.toString() ?? ''),
      reviews: (json['reviews']?.toString() ?? ''),
      icon: iconForFacility(name, facilityType: facilityType),
      imageUrl: (json['image_url'] as String? ?? ''),
      description: (json['description'] as String?) ?? '',
      amenities: amenities,
      requirements: (json['requirements'] as String?) ?? '',
      termsConditions: (json['terms_conditions'] as String?) ?? '',
      location: (json['location'] as String?) ?? '',
    );
  }

  final String id;
  final String name;
  final String facilityType;
  final String facilityTypeLabel;
  final String status;
  final String capacity;
  final String rate;
  final String priceType;
  final String bookingMode;
  final String roomType;
  final String slots;
  final String rating;
  final String reviews;
  final IconData icon;
  final String imageUrl;
  final String description;
  final List<String> amenities;
  final String requirements;
  final String termsConditions;
  final String location;

  bool get supportsSlotBooking =>
      (bookingMode == 'slot' || bookingMode == 'assessment') &&
      !['hostel', 'food_analysis', 'lease_space'].contains(facilityType);

  static const String campusName = 'USTP Oroquieta Campus';

  String get priceLabel {
    if (rate.isEmpty || rate == '0') return 'Contact Admin';
    final priceNum = double.tryParse(rate);
    final formatted = priceNum != null
        ? '\u20b1${priceNum.toStringAsFixed(2)}'
        : '\u20b1$rate';
    return priceType == 'monthly'
        ? '$formatted monthly'
        : '$formatted per $priceType';
  }

  String get resolvedImageUrl {
    var url = imageUrl.trim();
    if (url.isEmpty) return '';
    if (url.startsWith('[')) {
      try {
        final parsed = jsonDecode(url);
        if (parsed is List && parsed.isNotEmpty) {
          url = parsed.first.toString().trim();
        }
      } catch (_) {}
    }
    if (url.startsWith('http') || url.startsWith('data:image/')) return url;
    if (url.startsWith('/')) return '${ApiConfig.effectiveBaseUrl}$url';
    return url;
  }

  List<String> get allImageUrls {
    final raw = imageUrl.trim();
    if (raw.isEmpty) return const [];
    if (raw.startsWith('[')) {
      try {
        final parsed = jsonDecode(raw);
        if (parsed is List) {
          return parsed.map((e) {
            final s = e.toString().trim();
            if (s.startsWith('http') || s.startsWith('data:image/')) return s;
            if (s.startsWith('/')) return '${ApiConfig.effectiveBaseUrl}$s';
            return s;
          }).toList();
        }
      } catch (_) {}
    }
    final single = resolvedImageUrl;
    return single.isNotEmpty ? [single] : const [];
  }

  /// Time ranges from admin `slots` field (comma/semicolon separated or single range).
  List<String> get timeSlotLabels {
    final raw = slots.trim();
    if (raw.isEmpty) return const [];

    final parts = raw
        .split(RegExp(r'[,;|\n]+'))
        .map((e) => e.trim())
        .where((e) => e.isNotEmpty)
        .toList();
    if (parts.isNotEmpty) return parts;

    return [raw];
  }

  bool get hasRating => rating.isNotEmpty && rating != '0';
  bool get hasReviews => reviews.isNotEmpty && reviews != '0';
}

String labelForFacilityType(String type) {
  return switch (type.toLowerCase()) {
    'covered_court' => 'Covered Court',
    'function_hall' => 'Function Hall',
    'hostel' => 'Hostel',
    'training_kitchen' => 'Training Kitchen',
    'food_analysis' => 'Food Analysis Lab',
    'lease_space' => 'Lease of Space',
    _ => 'Other',
  };
}

IconData iconForFacility(String name, {String facilityType = ''}) {
  final type = facilityType.toLowerCase();
  if (type == 'covered_court') return Icons.sports_basketball_outlined;
  if (type == 'function_hall') return Icons.account_balance_outlined;
  if (type == 'hostel') return Icons.hotel_outlined;
  if (type == 'training_kitchen') return Icons.local_fire_department_outlined;
  if (type == 'food_analysis') return Icons.science_outlined;
  if (type == 'lease_space') return Icons.business_outlined;

  final lower = name.toLowerCase();
  if (lower.contains('court')) return Icons.sports_basketball_outlined;
  if (lower.contains('hall')) return Icons.account_balance_outlined;
  if (lower.contains('hostel') ||
      lower.contains('dorm') ||
      lower.contains('hotel')) {
    return Icons.hotel_outlined;
  }
  if (lower.contains('lab') || lower.contains('analysis')) {
    return Icons.science_outlined;
  }
  if (lower.contains('kitchen')) return Icons.local_fire_department_outlined;
  if (lower.contains('assess')) return Icons.verified_outlined;
  return Icons.assignment_outlined;
}

IconData iconForAmenity(String amenity) {
  final lower = amenity.toLowerCase();
  if (lower.contains('basketball') || lower.contains('court')) {
    return Icons.sports_basketball_outlined;
  }
  if (lower.contains('bleacher') || lower.contains('seat')) {
    return Icons.stadium_outlined;
  }
  if (lower.contains('sound') || lower.contains('audio')) {
    return Icons.surround_sound_outlined;
  }
  if (lower.contains('light')) return Icons.light_mode_outlined;
  if (lower.contains('restroom') || lower.contains('comfort')) {
    return Icons.wc_outlined;
  }
  if (lower.contains('park')) return Icons.local_parking_outlined;
  if (lower.contains('wifi')) return Icons.wifi_outlined;
  if (lower.contains('air')) return Icons.ac_unit_outlined;
  if (lower.contains('cabinet')) return Icons.inventory_2_outlined;
  if (lower.contains('table') || lower.contains('study')) {
    return Icons.table_restaurant_outlined;
  }
  return Icons.check_circle_outline;
}
