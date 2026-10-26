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
  int _currentImageIndex = 0;
  late final PageController _pageController;
  late Future<List<Map<String, dynamic>>> _slots;
  FacilityItem get facility => widget.facility;

  List<String> get _galleryImages {
    final urls = facility.allImageUrls;
    if (urls.isNotEmpty) return urls;
    final single = facility.resolvedImageUrl;
    return single.isNotEmpty ? [single] : const [''];
  }

  @override
  void initState() {
    super.initState();
    _pageController = PageController();
    _loadSlots();
    _loadFavorite();
  }

  @override
  void dispose() {
    _pageController.dispose();
    super.dispose();
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

  String get _categoryText {
    final loc = facility.location.trim();
    final typeLabel = facility.facilityTypeLabel.trim();
    if (loc.isNotEmpty &&
        typeLabel.isNotEmpty &&
        loc.toLowerCase() != typeLabel.toLowerCase() &&
        !loc.toLowerCase().contains(typeLabel.toLowerCase())) {
      return loc;
    }
    if (loc.isNotEmpty) return loc;
    if (typeLabel.isNotEmpty) return typeLabel;
    return 'Campus Facility';
  }

  List<String> get _parsedRules {
    final raw = facility.termsConditions.trim();
    if (raw.isEmpty) return const [];
    final lines = raw
        .split('\n')
        .map(
          (line) => line.trim().replaceFirst(RegExp(r'^[•\-\*]\s*'), '').trim(),
        )
        .where((line) => line.isNotEmpty)
        .toList();
    return lines;
  }

  @override
  Widget build(BuildContext context) {
    final images = _galleryImages;
    final rules = _parsedRules;
    final visibleRules = _expandedRules || rules.length <= 4
        ? rules
        : rules.take(4).toList();

    return BookingScaffold(
      title: 'Facility Details',
      backgroundColor: const Color(0xFFF8FAFC),
      actions: [
        Padding(
          padding: const EdgeInsets.only(right: 14),
          child: Center(
            child: Material(
              color: _favorite ? const Color(0xFFFFF8E6) : bookingSurfaceLight,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(11),
                side: BorderSide(
                  color: _favorite ? bookingGold : bookingOutline,
                ),
              ),
              child: InkWell(
                key: const ValueKey('facility-favorite-button'),
                borderRadius: BorderRadius.circular(11),
                onTap: _toggleFavorite,
                child: Tooltip(
                  message: _favorite
                      ? 'Remove from favorites'
                      : 'Add to favorites',
                  child: SizedBox(
                    width: 38,
                    height: 38,
                    child: Icon(
                      _favorite
                          ? Icons.bookmark_rounded
                          : Icons.bookmark_border_rounded,
                      size: 20,
                      color: bookingNavy,
                    ),
                  ),
                ),
              ),
            ),
          ),
        ),
      ],
      bottom: Row(
        children: [
          Expanded(
            child: BookingButton(
              label: 'Message Admin',
              icon: Icons.chat_bubble_outline_rounded,
              outlined: true,
              onPressed: () => messageFacilitiesAdmin(context, facility.id),
            ),
          ),
          const SizedBox(width: 12),
          Expanded(
            child: BookingButton(
              label: facility.supportsSlotBooking
                  ? 'Book Now'
                  : 'Contact to Request',
              icon: facility.supportsSlotBooking
                  ? Icons.calendar_month_rounded
                  : Icons.outgoing_mail,
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
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 24),
        children: [
          // 1. Hero Image Carousel Section
          _FacilityHeroGallery(
            images: images,
            currentIndex: _currentImageIndex.clamp(0, images.length - 1),
            controller: _pageController,
            fallbackIcon: facility.icon,
            categoryLabel: facility.facilityTypeLabel,
            onPageChanged: (index) =>
                setState(() => _currentImageIndex = index),
          ),
          const SizedBox(height: 14),

          // 2. Main Info Card (Name, Badge, Campus, Category, Capacity & Rate)
          _FacilitySurfaceCard(
            key: const ValueKey('facility-main-info-card'),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Expanded(
                      child: Text(
                        facility.name,
                        style: const TextStyle(
                          fontFamily: 'Poppins',
                          fontSize: 20,
                          height: 1.2,
                          fontWeight: FontWeight.w700,
                          color: bookingNavy,
                        ),
                      ),
                    ),
                    const SizedBox(width: 10),
                    BookingStatusBadge(facility.status, showDot: true),
                  ],
                ),
                const SizedBox(height: 10),
                Row(
                  children: [
                    const Icon(
                      Icons.location_on_outlined,
                      size: 15,
                      color: bookingNavy,
                    ),
                    const SizedBox(width: 6),
                    const Expanded(
                      child: Text(
                        FacilityItem.campusName,
                        style: TextStyle(
                          fontFamily: 'Poppins',
                          fontSize: 12.5,
                          fontWeight: FontWeight.w500,
                          color: bookingMuted,
                        ),
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 4),
                Row(
                  children: [
                    const Icon(
                      Icons.domain_outlined,
                      size: 15,
                      color: bookingGoldText,
                    ),
                    const SizedBox(width: 6),
                    Expanded(
                      child: Text(
                        _categoryText,
                        style: const TextStyle(
                          fontFamily: 'Poppins',
                          fontSize: 12,
                          fontWeight: FontWeight.w500,
                          color: bookingMuted,
                        ),
                      ),
                    ),
                  ],
                ),
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 14),
                  child: Divider(
                    height: 1,
                    thickness: 1,
                    color: Color(0xFFF1F5F9),
                  ),
                ),
                Row(
                  children: [
                    Expanded(
                      child: _FactCard(
                        icon: Icons.groups_outlined,
                        iconBg: const Color(0xFFEEF2FF),
                        iconColor: bookingNavy,
                        title: 'Capacity',
                        valueWidget: Text(
                          '${facility.capacity} persons',
                          style: const TextStyle(
                            fontFamily: 'Poppins',
                            fontSize: 13.5,
                            fontWeight: FontWeight.w700,
                            color: bookingNavy,
                          ),
                        ),
                        subtitle: 'Max occupancy',
                      ),
                    ),
                    const SizedBox(width: 10),
                    Expanded(
                      child: _FactCard(
                        icon: Icons.payments_outlined,
                        iconBg: bookingGoldBg,
                        iconColor: bookingGoldText,
                        title: 'Rate',
                        valueWidget: bookingMoneyText(
                          facility.rate,
                          fontSize: 14,
                          fontWeight: FontWeight.w700,
                          color: bookingNavy,
                        ),
                        subtitle: 'per ${facility.priceType}',
                      ),
                    ),
                  ],
                ),
              ],
            ),
          ),

          // 3. About Section
          if (facility.description.trim().isNotEmpty) ...[
            const SizedBox(height: 14),
            _FacilitySurfaceCard(
              key: const ValueKey('facility-about-card'),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const _CardSectionHeader(
                    icon: Icons.info_outline_rounded,
                    title: 'About this Facility',
                  ),
                  const SizedBox(height: 8),
                  Text(
                    facility.description,
                    maxLines: _expanded ? null : 4,
                    overflow: _expanded ? null : TextOverflow.ellipsis,
                    style: const TextStyle(
                      fontFamily: 'Poppins',
                      fontSize: 12.5,
                      height: 1.55,
                      color: Color(0xFF334155),
                    ),
                  ),
                  if (facility.description.length > 160) ...[
                    const SizedBox(height: 6),
                    InkWell(
                      onTap: () => setState(() => _expanded = !_expanded),
                      borderRadius: BorderRadius.circular(6),
                      child: Padding(
                        padding: const EdgeInsets.symmetric(vertical: 2),
                        child: Text(
                          _expanded ? 'View less' : 'View more',
                          style: const TextStyle(
                            fontFamily: 'Poppins',
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: bookingNavy,
                          ),
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],

          // 4. Amenities Section (Clean 2-Column Equal-Height Grid)
          if (facility.amenities.isNotEmpty) ...[
            const SizedBox(height: 14),
            _FacilitySurfaceCard(
              key: const ValueKey('facility-amenities-card'),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Row(
                    children: [
                      const Expanded(
                        child: _CardSectionHeader(
                          icon: Icons.grid_view_rounded,
                          title: 'Amenities',
                        ),
                      ),
                      Container(
                        padding: const EdgeInsets.symmetric(
                          horizontal: 8,
                          vertical: 3,
                        ),
                        decoration: BoxDecoration(
                          color: bookingSurfaceLight,
                          borderRadius: BorderRadius.circular(12),
                          border: Border.all(color: bookingOutline),
                        ),
                        child: Text(
                          '${facility.amenities.length} included',
                          style: const TextStyle(
                            fontFamily: 'Poppins',
                            fontSize: 10.5,
                            fontWeight: FontWeight.w600,
                            color: bookingMuted,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 12),
                  LayoutBuilder(
                    builder: (context, constraints) {
                      final textScale = MediaQuery.textScalerOf(
                        context,
                      ).scale(1);
                      final singleCol =
                          constraints.maxWidth < 260 || textScale > 1.4;
                      if (singleCol) {
                        return Column(
                          children: [
                            for (
                              var i = 0;
                              i < facility.amenities.length;
                              i++
                            ) ...[
                              if (i > 0) const SizedBox(height: 8),
                              _AmenityGridItem(amenity: facility.amenities[i]),
                            ],
                          ],
                        );
                      }
                      final rows = <Widget>[];
                      for (var i = 0; i < facility.amenities.length; i += 2) {
                        if (i > 0) rows.add(const SizedBox(height: 8));
                        final hasSecond = i + 1 < facility.amenities.length;
                        rows.add(
                          IntrinsicHeight(
                            child: Row(
                              crossAxisAlignment: CrossAxisAlignment.stretch,
                              children: [
                                Expanded(
                                  child: _AmenityGridItem(
                                    amenity: facility.amenities[i],
                                  ),
                                ),
                                const SizedBox(width: 8),
                                Expanded(
                                  child: hasSecond
                                      ? _AmenityGridItem(
                                          amenity: facility.amenities[i + 1],
                                        )
                                      : const SizedBox.shrink(),
                                ),
                              ],
                            ),
                          ),
                        );
                      }
                      return Column(children: rows);
                    },
                  ),
                ],
              ),
            ),
          ],

          // 5. Availability Preview Section
          if (facility.supportsSlotBooking) ...[
            const SizedBox(height: 14),
            _FacilitySurfaceCard(
              key: const ValueKey('facility-availability-card'),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  Row(
                    children: [
                      const Expanded(
                        child: _CardSectionHeader(
                          icon: Icons.schedule_rounded,
                          title: 'Available Time Slots',
                        ),
                      ),
                      InkWell(
                        key: const ValueKey('facility-view-schedule-button'),
                        borderRadius: BorderRadius.circular(8),
                        onTap: facility.status == 'Open for Booking'
                            ? _book
                            : null,
                        child: Padding(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 6,
                            vertical: 4,
                          ),
                          child: Row(
                            mainAxisSize: MainAxisSize.min,
                            children: [
                              Text(
                                'View Schedule',
                                style: TextStyle(
                                  fontFamily: 'Poppins',
                                  fontSize: 12,
                                  fontWeight: FontWeight.w600,
                                  color: facility.status == 'Open for Booking'
                                      ? bookingNavy
                                      : bookingMuted,
                                ),
                              ),
                              const SizedBox(width: 2),
                              Icon(
                                Icons.chevron_right_rounded,
                                size: 16,
                                color: facility.status == 'Open for Booking'
                                    ? bookingNavy
                                    : bookingMuted,
                              ),
                            ],
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 4),
                  Row(
                    children: [
                      const Icon(
                        Icons.calendar_today_outlined,
                        size: 13,
                        color: bookingMuted,
                      ),
                      const SizedBox(width: 6),
                      Expanded(
                        child: Text(
                          'Today, ${bookingDate(FacilityBookingService.dateKey(DateTime.now()))}',
                          style: const TextStyle(
                            fontFamily: 'Poppins',
                            fontSize: 11.5,
                            fontWeight: FontWeight.w500,
                            color: bookingMuted,
                          ),
                        ),
                      ),
                    ],
                  ),
                  const SizedBox(height: 10),
                  FutureBuilder<List<Map<String, dynamic>>>(
                    future: _slots,
                    builder: (context, snapshot) {
                      if (snapshot.connectionState != ConnectionState.done) {
                        return const Padding(
                          padding: EdgeInsets.symmetric(vertical: 8),
                          child: LinearProgressIndicator(minHeight: 2),
                        );
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
                          style: TextStyle(
                            fontFamily: 'Poppins',
                            fontSize: 12,
                            color: bookingMuted,
                          ),
                        );
                      }
                      return Column(
                        children: [
                          for (var i = 0; i < slots.length; i++) ...[
                            if (i > 0) const SizedBox(height: 8),
                            _TimeSlotChipCard(
                              slot: slots[i],
                              onTap: slots[i]['status'] == 'available'
                                  ? _book
                                  : null,
                            ),
                          ],
                        ],
                      );
                    },
                  ),
                ],
              ),
            ),
          ],

          if (!facility.supportsSlotBooking) ...[
            const SizedBox(height: 14),
            _FacilitySurfaceCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const _CardSectionHeader(
                    icon: Icons.assignment_turned_in_outlined,
                    title: 'Request Process',
                  ),
                  const SizedBox(height: 8),
                  Text(
                    switch (facility.facilityType) {
                      'food_analysis' =>
                        'Contact the laboratory for sample requirements and a job order. Analysis starts after sample acceptance and resource checks.',
                      'hostel' =>
                        'Contact Facilities Admin with your check-in and check-out dates, room preference, and guest count.',
                      'lease_space' =>
                        'Contact Facilities Admin to request a lease application for this space.',
                      _ => 'Contact Facilities Admin to arrange this request.',
                    },
                    style: const TextStyle(
                      fontFamily: 'Poppins',
                      fontSize: 12.5,
                      height: 1.55,
                      color: Color(0xFF334155),
                    ),
                  ),
                ],
              ),
            ),
          ],

          if (facility.requirements.isNotEmpty) ...[
            const SizedBox(height: 14),
            _FacilitySurfaceCard(
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const _CardSectionHeader(
                    icon: Icons.fact_check_outlined,
                    title: 'Requirements',
                  ),
                  const SizedBox(height: 8),
                  Text(
                    facility.requirements,
                    style: const TextStyle(
                      fontFamily: 'Poppins',
                      fontSize: 12.5,
                      height: 1.55,
                      color: Color(0xFF334155),
                    ),
                  ),
                ],
              ),
            ),
          ],

          // 6. Rules & Guidelines Section
          if (rules.isNotEmpty) ...[
            const SizedBox(height: 14),
            _FacilitySurfaceCard(
              key: const ValueKey('facility-rules-card'),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  const _CardSectionHeader(
                    icon: Icons.verified_user_outlined,
                    title: 'Rules & Guidelines',
                  ),
                  const SizedBox(height: 10),
                  Container(
                    padding: const EdgeInsets.all(12),
                    decoration: BoxDecoration(
                      color: bookingSurfaceLight,
                      borderRadius: BorderRadius.circular(12),
                      border: Border.all(color: bookingOutline),
                    ),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        for (var i = 0; i < visibleRules.length; i++) ...[
                          if (i > 0) const SizedBox(height: 8),
                          Row(
                            crossAxisAlignment: CrossAxisAlignment.start,
                            children: [
                              Container(
                                margin: const EdgeInsets.only(top: 2),
                                width: 18,
                                height: 18,
                                decoration: const BoxDecoration(
                                  color: Color(0xFFEEF2FF),
                                  shape: BoxShape.circle,
                                ),
                                child: const Icon(
                                  Icons.check_rounded,
                                  size: 12,
                                  color: bookingNavy,
                                ),
                              ),
                              const SizedBox(width: 9),
                              Expanded(
                                child: Text(
                                  visibleRules[i],
                                  style: const TextStyle(
                                    fontFamily: 'Poppins',
                                    fontSize: 12,
                                    height: 1.45,
                                    color: Color(0xFF334155),
                                  ),
                                ),
                              ),
                            ],
                          ),
                        ],
                      ],
                    ),
                  ),
                  if (rules.length > 4) ...[
                    const SizedBox(height: 8),
                    InkWell(
                      onTap: () =>
                          setState(() => _expandedRules = !_expandedRules),
                      borderRadius: BorderRadius.circular(6),
                      child: Padding(
                        padding: const EdgeInsets.symmetric(vertical: 2),
                        child: Text(
                          _expandedRules ? 'View less' : 'View more',
                          style: const TextStyle(
                            fontFamily: 'Poppins',
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: bookingNavy,
                          ),
                        ),
                      ),
                    ),
                  ],
                ],
              ),
            ),
          ],
        ],
      ),
    );
  }
}

class _FacilityHeroGallery extends StatelessWidget {
  const _FacilityHeroGallery({
    required this.images,
    required this.currentIndex,
    required this.controller,
    required this.fallbackIcon,
    required this.categoryLabel,
    required this.onPageChanged,
  });

  final List<String> images;
  final int currentIndex;
  final PageController controller;
  final IconData fallbackIcon;
  final String categoryLabel;
  final ValueChanged<int> onPageChanged;

  @override
  Widget build(BuildContext context) {
    return Container(
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: bookingOutline),
        boxShadow: const [
          BoxShadow(
            color: Color(0x121A1851),
            blurRadius: 14,
            offset: Offset(0, 5),
          ),
        ],
      ),
      child: ClipRRect(
        borderRadius: BorderRadius.circular(15),
        child: AspectRatio(
          aspectRatio: 16 / 9.5,
          child: Stack(
            fit: StackFit.expand,
            children: [
              PageView.builder(
                controller: controller,
                itemCount: images.length,
                onPageChanged: onPageChanged,
                itemBuilder: (context, index) => ProductImage(
                  imageUrl: images[index],
                  fallbackIcon: fallbackIcon,
                  fallbackSize: 48,
                  backgroundColor: const Color(0xFFEEF2F6),
                ),
              ),
              Positioned(
                left: 0,
                right: 0,
                bottom: 0,
                height: 54,
                child: IgnorePointer(
                  child: DecoratedBox(
                    decoration: BoxDecoration(
                      gradient: LinearGradient(
                        begin: Alignment.topCenter,
                        end: Alignment.bottomCenter,
                        colors: [
                          Colors.transparent,
                          Colors.black.withValues(alpha: 0.52),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
              if (categoryLabel.trim().isNotEmpty)
                Positioned(
                  top: 10,
                  left: 10,
                  child: Container(
                    padding: const EdgeInsets.symmetric(
                      horizontal: 10,
                      vertical: 4,
                    ),
                    decoration: BoxDecoration(
                      color: Colors.white.withValues(alpha: 0.92),
                      borderRadius: BorderRadius.circular(20),
                    ),
                    child: Row(
                      mainAxisSize: MainAxisSize.min,
                      children: [
                        Icon(fallbackIcon, size: 13, color: bookingNavy),
                        const SizedBox(width: 5),
                        Text(
                          categoryLabel,
                          style: const TextStyle(
                            fontFamily: 'Poppins',
                            fontSize: 10.5,
                            fontWeight: FontWeight.w600,
                            color: bookingNavy,
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              Positioned(
                left: 12,
                bottom: 11,
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: List.generate(images.length, (index) {
                    final active = index == currentIndex;
                    return AnimatedContainer(
                      duration: const Duration(milliseconds: 200),
                      margin: const EdgeInsets.only(right: 5),
                      width: active ? 18 : 6,
                      height: 6,
                      decoration: BoxDecoration(
                        color: active
                            ? bookingGold
                            : Colors.white.withValues(alpha: 0.65),
                        borderRadius: BorderRadius.circular(4),
                      ),
                    );
                  }),
                ),
              ),
              Positioned(
                bottom: 9,
                right: 10,
                child: Container(
                  padding: const EdgeInsets.symmetric(
                    horizontal: 9,
                    vertical: 4,
                  ),
                  decoration: BoxDecoration(
                    color: bookingNavy.withValues(alpha: 0.82),
                    borderRadius: BorderRadius.circular(14),
                  ),
                  child: Row(
                    mainAxisSize: MainAxisSize.min,
                    children: [
                      const Icon(
                        Icons.photo_library_outlined,
                        size: 12,
                        color: Colors.white,
                      ),
                      const SizedBox(width: 4),
                      Text(
                        '${currentIndex + 1}/${images.length}',
                        style: const TextStyle(
                          fontFamily: 'Poppins',
                          color: Colors.white,
                          fontSize: 10.5,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _FacilitySurfaceCard extends StatelessWidget {
  const _FacilitySurfaceCard({super.key, required this.child});
  final Widget child;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.all(15),
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: bookingOutline),
      boxShadow: const [
        BoxShadow(
          color: Color(0x0A1A1851),
          blurRadius: 10,
          offset: Offset(0, 3),
        ),
      ],
    ),
    child: child,
  );
}

class _CardSectionHeader extends StatelessWidget {
  const _CardSectionHeader({required this.icon, required this.title});
  final IconData icon;
  final String title;

  @override
  Widget build(BuildContext context) => Row(
    children: [
      Container(
        width: 28,
        height: 28,
        decoration: BoxDecoration(
          color: const Color(0xFFEEF2FF),
          borderRadius: BorderRadius.circular(8),
        ),
        child: Icon(icon, size: 16, color: bookingNavy),
      ),
      const SizedBox(width: 8),
      Expanded(
        child: Text(
          title,
          style: const TextStyle(
            fontFamily: 'Poppins',
            fontSize: 14.5,
            fontWeight: FontWeight.w700,
            color: bookingNavy,
          ),
        ),
      ),
    ],
  );
}

class _FactCard extends StatelessWidget {
  const _FactCard({
    required this.icon,
    required this.iconBg,
    required this.iconColor,
    required this.title,
    required this.valueWidget,
    required this.subtitle,
  });
  final IconData icon;
  final Color iconBg;
  final Color iconColor;
  final String title;
  final Widget valueWidget;
  final String subtitle;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 11, vertical: 10),
    decoration: BoxDecoration(
      color: bookingSurfaceLight,
      borderRadius: BorderRadius.circular(12),
      border: Border.all(color: bookingOutline),
    ),
    child: Row(
      children: [
        Container(
          width: 36,
          height: 36,
          decoration: BoxDecoration(
            color: iconBg,
            borderRadius: BorderRadius.circular(10),
          ),
          child: Icon(icon, size: 19, color: iconColor),
        ),
        const SizedBox(width: 9),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                title,
                style: const TextStyle(
                  fontFamily: 'Poppins',
                  fontSize: 10.5,
                  fontWeight: FontWeight.w500,
                  color: bookingMuted,
                ),
              ),
              const SizedBox(height: 1),
              valueWidget,
              Text(
                subtitle,
                style: const TextStyle(
                  fontFamily: 'Poppins',
                  fontSize: 10.5,
                  color: bookingMuted,
                ),
              ),
            ],
          ),
        ),
      ],
    ),
  );
}

class _AmenityGridItem extends StatelessWidget {
  const _AmenityGridItem({required this.amenity});
  final String amenity;

  @override
  Widget build(BuildContext context) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 9),
    decoration: BoxDecoration(
      color: bookingSurfaceLight,
      borderRadius: BorderRadius.circular(11),
      border: Border.all(color: bookingOutline),
    ),
    child: Row(
      children: [
        Container(
          width: 30,
          height: 30,
          decoration: BoxDecoration(
            color: Colors.white,
            borderRadius: BorderRadius.circular(8),
            border: Border.all(color: bookingOutline),
          ),
          child: Icon(iconForAmenity(amenity), color: bookingNavy, size: 16),
        ),
        const SizedBox(width: 8),
        Expanded(
          child: Text(
            amenity,
            maxLines: 2,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              fontFamily: 'Poppins',
              fontSize: 11.5,
              fontWeight: FontWeight.w600,
              color: bookingNavy,
            ),
          ),
        ),
      ],
    ),
  );
}

class _TimeSlotChipCard extends StatelessWidget {
  const _TimeSlotChipCard({required this.slot, this.onTap});
  final Map<String, dynamic> slot;
  final VoidCallback? onTap;

  @override
  Widget build(BuildContext context) {
    final statusRaw = (slot['status'] as String? ?? '').toLowerCase();
    final isAvailable = statusRaw == 'available';
    final label = (slot['label'] as String? ?? '').trim();

    return Material(
      color: isAvailable ? const Color(0xFFF4FBF7) : bookingSurfaceLight,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(11),
        side: BorderSide(
          color: isAvailable
              ? bookingGreen.withValues(alpha: 0.35)
              : bookingOutline,
        ),
      ),
      child: InkWell(
        onTap: onTap,
        borderRadius: BorderRadius.circular(11),
        child: Padding(
          padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 9),
          child: Row(
            children: [
              Icon(
                Icons.access_time_rounded,
                size: 16,
                color: isAvailable ? bookingGreen : bookingMuted,
              ),
              const SizedBox(width: 8),
              Expanded(
                child: Text(
                  label,
                  style: TextStyle(
                    fontFamily: 'Poppins',
                    fontSize: 12,
                    fontWeight: FontWeight.w600,
                    color: isAvailable ? bookingNavy : bookingMuted,
                  ),
                ),
              ),
              const SizedBox(width: 8),
              BookingStatusBadge(
                statusRaw,
                fontSize: 10.5,
                showDot: isAvailable,
              ),
            ],
          ),
        ),
      ),
    );
  }
}
