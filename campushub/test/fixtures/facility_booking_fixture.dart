import 'package:campushub/module_app/models/facility_item.dart';
import 'package:campushub/module_app/services/facility_booking_service.dart';

// Isolated UI test data. Never imported by the application.
final testFacility = FacilityItem.fromJson({
  'id': 'TEST-COURT', 'name': 'Test Covered Court', 'facility_type': 'covered_court',
  'status': 'available', 'capacity': 50, 'rate': '500.00', 'price_type': 'hour',
  'booking_mode': 'slot', 'image_url': '', 'location': 'Test Sports Complex',
  'description': 'Facility description for layout verification.',
  'amenities': ['Basketball Court', 'Sound System', 'Lighting'],
  'terms_conditions': 'Observe the facility rules and your approved schedule.',
});

class TestBookingService extends FacilityBookingService {
  bool conflict = false;
  int submissions = 0;
  Map<String, dynamic>? submitted;
  @override
  Future<List<Map<String, dynamic>>> slots(String facilityId, DateTime date) async => [
    {'start': '08:00', 'end': '12:00', 'label': '8:00 AM - 12:00 PM', 'status': 'class'},
    {'start': '13:00', 'end': '17:00', 'label': '1:00 PM - 5:00 PM', 'status': 'available'},
  ];
  @override
  Future<Map<String, dynamic>> request(String path, {Map<String, dynamic>? body}) async {
    if (path.endsWith('quote/')) {
      if (conflict) throw const BookingException('This time slot is no longer available. Select another schedule.');
      return {'base_amount': '2000.00', 'total_amount': '2000.00', 'hours': '4'};
    }
    if (path == 'bookings/' && body != null) {
      submissions++;
      submitted = body;
      return {'booking': {
        'id': 'TEST-BOOKING', 'date': body['date'], 'start': body['start'], 'end': body['end'],
        'status': 'pending', 'created_at': DateTime.now().toIso8601String(),
        'total_amount': '2000.00', 'paid_amount': '0.00', 'payment_status': 'unpaid',
        'can_cancel': true, 'can_view_slip': false, 'details': body, 'receipts': [],
      }};
    }
    if (path.startsWith('bookings/') && path != 'bookings/') {
      return {'booking': {
        'id': 'BK-2026-0002',
        'facility': {
          'id': testFacility.id,
          'name': testFacility.name,
          'facility_type': testFacility.facilityType,
          'status': testFacility.status,
          'capacity': testFacility.capacity,
          'rate': testFacility.rate,
          'price_type': testFacility.priceType,
          'booking_mode': testFacility.bookingMode,
          'image_url': testFacility.imageUrl,
          'location': testFacility.location,
          'description': testFacility.description,
          'amenities': testFacility.amenities,
          'terms_conditions': testFacility.termsConditions,
        },
        'date': '2026-08-30', 'start': '13:00', 'end': '17:00',
        'status': path.contains('APPROVED') ? 'approved' : 'pending',
        'created_at': '2026-05-31T10:30:00Z',
        'total_amount': '2500.00', 'paid_amount': '0.00', 'payment_status': 'unpaid',
        'can_cancel': !path.contains('APPROVED'),
        'can_view_slip': path.contains('APPROVED'),
        'details': {
          'full_name': 'Lester Bulay',
          'organization': 'College of Information Technology',
          'contact_number': '0912 345 6789',
          'email': 'lesterbulay@ustp.edu.ph',
          'event_name': 'Basketball Practice',
          'purpose': 'Intramurals Practice',
          'attendees': 40,
          'additional_requirements': ['Sound System'],
          'notes': 'We will also need a scoreboard.',
        },
        'receipts': [],
      }};
    }
    return {'bookings': []};
  }
}
