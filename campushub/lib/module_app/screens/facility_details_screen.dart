import 'package:flutter/material.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../models/facility_item.dart';
import '../services/facility_booking_service.dart';
import '../widgets/facilities/booking_widgets.dart';
import '../widgets/product_image.dart';
import 'facilities/facility_booking_screen.dart';

/// Reference flow: facility information, schedule, request, review, and tracking.
class FacilityDetailsScreen extends StatefulWidget {
  const FacilityDetailsScreen({
    super.key,
    required this.facility,
    this.service = const FacilityBookingService(),
  });
  final FacilityItem facility;
  final FacilityBookingService service;
  @override
  State<FacilityDetailsScreen> createState() => _FacilityDetailsScreenState();
}

class _FacilityDetailsScreenState extends State<FacilityDetailsScreen> {
  bool _expanded = false;
  bool _expandedRules = false;
  bool _favorite = false;
  late Future<List<Map<String, dynamic>>> _slots;
  FacilityItem get facility => widget.facility;

  @override
  void initState() {
    super.initState();
    _loadSlots();
    _loadFavorite();
  }

  Future<void> _loadFavorite() async {
    final preferences = await SharedPreferences.getInstance();
    if (mounted) {
      setState(
        () => _favorite =
            preferences.getBool('facility_favorite_${facility.id}') ?? false,
      );
    }
  }

  Future<void> _toggleFavorite() async {
    setState(() => _favorite = !_favorite);
    final preferences = await SharedPreferences.getInstance();
    await preferences.setBool('facility_favorite_${facility.id}', _favorite);
  }

  void _loadSlots() {
    _slots = widget.service.slots(facility.id, DateTime.now());
  }

  Future<void> _book() async {
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) =>
            FacilityBookingScreen(facility: facility, service: widget.service),
      ),
    );
    if (mounted) setState(_loadSlots);
  }

  @override
  Widget build(BuildContext context) => BookingScaffold(
    title: 'Facility Details',
    actions: [
      IconButton(
        tooltip: _favorite ? 'Remove from favorites' : 'Add to favorites',
        icon: Icon(
          _favorite ? Icons.favorite : Icons.favorite_border,
          color: _favorite ? Colors.red : bookingNavy,
        ),
        onPressed: _toggleFavorite,
      ),
    ],
    bottom: Row(
      children: [
        Expanded(
          child: BookingButton(
            label: 'Message Admin',
            outlined: true,
            onPressed: () => messageFacilitiesAdmin(context, facility.id),
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: BookingButton(
            label: facility.supportsSlotBooking
                ? 'Book Now'
                : 'Contact to Request',
            onPressed: facility.status != 'Open for Booking'
                ? null
                : facility.supportsSlotBooking
                ? _book
                : () => messageFacilitiesAdmin(context, facility.id),
          ),
        ),
      ],
    ),
    child: ListView(
      padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(8),
          child: AspectRatio(
            aspectRatio: 16 / 10,
            child: Stack(
              fit: StackFit.expand,
              children: [
                ProductImage(
                  imageUrl: facility.resolvedImageUrl,
                  fallbackIcon: facility.icon,
                ),
                Positioned(
                  bottom: 10,
                  right: 10,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 8,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.black.withValues(alpha: 0.65),
                      borderRadius: BorderRadius.circular(12),
                    ),
                    child: const Text(
                      '1/5',
                      style: TextStyle(
                        color: Colors.white,
                        fontSize: 11,
                        fontWeight: FontWeight.w600,
                      ),
                    ),
                  ),
                ),
              ],
            ),
          ),
        ),
        const SizedBox(height: 16),
        Text(
          facility.name,
          style: const TextStyle(
            fontSize: 22,
            height: 1.2,
            fontWeight: FontWeight.w700,
            color: bookingNavy,
          ),
        ),
        const SizedBox(height: 8),
        Align(
          alignment: Alignment.centerLeft,
          child: BookingStatusBadge(facility.status),
        ),
        const SizedBox(height: 8),
        const Text(
          FacilityItem.campusName,
          style: TextStyle(fontSize: 12, color: bookingMuted),
        ),
        if (facility.location.isNotEmpty)
          Text(
            facility.location,
            style: const TextStyle(fontSize: 12, color: bookingMuted),
          )
        else
          const Text(
            'Sports Complex',
            style: TextStyle(fontSize: 12, color: bookingMuted),
          ),
        const SizedBox(height: 18),
        Row(
          children: [
            Expanded(
              child: _FactCard(
                icon: Icons.people_outline,
                title: 'Capacity',
                value: facility.capacity,
                unit: 'persons',
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: _FactCard(
                icon: Icons.sell_outlined,
                title: 'Rate',
                value: bookingMoney(facility.rate),
                unit: 'per ${facility.priceType}',
              ),
            ),
          ],
        ),
        const SizedBox(height: 22),
        if (facility.description.trim().isNotEmpty)
          BookingSection(
            'About this Facility',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  facility.description,
                  maxLines: _expanded ? null : 4,
                  overflow: _expanded ? null : TextOverflow.ellipsis,
                  style: const TextStyle(
                    fontSize: 13,
                    height: 1.6,
                    color: bookingNavy,
                  ),
                ),
                TextButton(
                  style: TextButton.styleFrom(padding: EdgeInsets.zero),
                  onPressed: () => setState(() => _expanded = !_expanded),
                  child: Text(
                    _expanded ? 'View less' : 'View more',
                    style: const TextStyle(
                      fontSize: 12,
                      fontWeight: FontWeight.w600,
                      color: bookingNavy,
                    ),
                  ),
                ),
              ],
            ),
          ),
        if (facility.amenities.isNotEmpty)
          BookingSection(
            'Amenities',
            child: Wrap(
              spacing: 10,
              runSpacing: 10,
              children: facility.amenities
                  .map(
                    (amenity) => Container(
                      width: 76,
                      padding: const EdgeInsets.symmetric(
                        vertical: 10,
                        horizontal: 4,
                      ),
                      decoration: BoxDecoration(
                        color: Colors.white,
                        borderRadius: BorderRadius.circular(8),
                        border: Border.all(color: bookingOutline),
                      ),
                      child: Column(
                        children: [
                          Icon(
                            iconForAmenity(amenity),
                            color: bookingNavy,
                            size: 22,
                          ),
                          const SizedBox(height: 6),
                          Text(
                            amenity,
                            textAlign: TextAlign.center,
                            maxLines: 2,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              fontSize: 10,
                              fontWeight: FontWeight.w500,
                              color: bookingNavy,
                            ),
                          ),
                        ],
                      ),
                    ),
                  )
                  .toList(),
            ),
          ),
        if (facility.supportsSlotBooking)
          BookingSection(
            'Available Time Slots',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Row(
                  children: [
                    const Icon(
                      Icons.calendar_today_outlined,
                      size: 15,
                      color: bookingNavy,
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        'Today, ${bookingDate(FacilityBookingService.dateKey(DateTime.now()))}',
                        style: const TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                          color: bookingNavy,
                        ),
                      ),
                    ),
                    TextButton(
                      style: TextButton.styleFrom(padding: EdgeInsets.zero),
                      onPressed: facility.status == 'Open for Booking'
                          ? _book
                          : null,
                      child: const Text(
                        'View Calendar',
                        style: TextStyle(
                          fontSize: 12,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 8),
                FutureBuilder<List<Map<String, dynamic>>>(
                  future: _slots,
                  builder: (context, snapshot) {
                    if (snapshot.connectionState != ConnectionState.done) {
                      return const LinearProgressIndicator(minHeight: 2);
                    }
                    if (snapshot.hasError) {
                      return TextButton(
                        onPressed: () => setState(_loadSlots),
                        child: const Text('Unable to load schedule. Retry'),
                      );
                    }
                    final slots = snapshot.data ?? [];
                    if (slots.isEmpty) {
                      return const Text(
                        'No time slots configured. Contact Facilities Admin.',
                        style: TextStyle(fontSize: 12, color: bookingMuted),
                      );
                    }
                    return Wrap(
                      spacing: 8,
                      runSpacing: 8,
                      children: slots
                          .map(
                            (slot) => OutlinedButton(
                              onPressed: slot['status'] == 'available'
                                  ? _book
                                  : null,
                              style: OutlinedButton.styleFrom(
                                padding: const EdgeInsets.symmetric(
                                  horizontal: 12,
                                  vertical: 8,
                                ),
                                side: BorderSide(
                                  color: slot['status'] == 'available'
                                      ? bookingGreen
                                      : bookingOutline,
                                ),
                                shape: RoundedRectangleBorder(
                                  borderRadius: BorderRadius.circular(6),
                                ),
                              ),
                              child: Text(
                                "${slot['label']}\n${bookingStatus(slot['status'])}",
                                textAlign: TextAlign.center,
                                style: TextStyle(
                                  fontSize: 11,
                                  fontWeight: FontWeight.w600,
                                  color: slot['status'] == 'available'
                                      ? bookingGreen
                                      : bookingMuted,
                                ),
                              ),
                            ),
                          )
                          .toList(),
                    );
                  },
                ),
              ],
            ),
          ),
        if (!facility.supportsSlotBooking)
          BookingSection(
            'Request Process',
            child: Text(
              switch (facility.facilityType) {
                'food_analysis' =>
                  'Contact the laboratory for sample requirements and a job order. Analysis starts after sample acceptance and resource checks.',
                'hostel' =>
                  'Contact Facilities Admin with your check-in and check-out dates, room preference, and guest count.',
                'lease_space' =>
                  'Contact Facilities Admin to request a lease application for this space.',
                _ => 'Contact Facilities Admin to arrange this request.',
              },
              style: const TextStyle(fontSize: 13, height: 1.6),
            ),
          ),
        if (facility.requirements.isNotEmpty)
          BookingSection(
            'Requirements',
            child: Text(
              facility.requirements,
              style: const TextStyle(fontSize: 13, height: 1.6),
            ),
          ),
        if (facility.termsConditions.isNotEmpty)
          BookingSection(
            'Rules & Guidelines',
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  facility.termsConditions
                      .split('\n')
                      .map((line) => line.trim().startsWith('•') || line.trim().startsWith('-') ? line : '• $line')
                      .join('\n'),
                  maxLines: _expandedRules ? null : 3,
                  overflow: _expandedRules ? null : TextOverflow.ellipsis,
                  style: const TextStyle(fontSize: 13, height: 1.6),
                ),
                if (facility.termsConditions.length > 100)
                  TextButton(
                    style: TextButton.styleFrom(padding: EdgeInsets.zero),
                    onPressed: () =>
                        setState(() => _expandedRules = !_expandedRules),
                    child: Text(
                      _expandedRules ? 'View less' : 'View more',
                      style: const TextStyle(
                        fontSize: 12,
                        fontWeight: FontWeight.w600,
                        color: bookingNavy,
                      ),
                    ),
                  ),
              ],
            ),
          ),
      ],
    ),
  );
}

class _FactCard extends StatelessWidget {
  const _FactCard({
    required this.icon,
    required this.title,
    required this.value,
    required this.unit,
  });
  final IconData icon;
  final String title, value, unit;

  @override
  Widget build(BuildContext context) => BookingCard(
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
    child: Row(
      children: [
        Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(
            color: const Color(0xFFF1F5F9),
            borderRadius: BorderRadius.circular(6),
          ),
          child: Icon(icon, size: 20, color: bookingNavy),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(fontSize: 11, color: bookingMuted),
              ),
              const SizedBox(height: 2),
              Text(
                value,
                style: const TextStyle(
                  fontSize: 16,
                  fontWeight: FontWeight.w700,
                  color: bookingNavy,
                ),
              ),
              Text(
                unit,
                style: const TextStyle(fontSize: 11, color: bookingMuted),
              ),
            ],
          ),
        ),
      ],
    ),
  );
}
