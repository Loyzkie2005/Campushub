import 'dart:convert';

import 'package:flutter/material.dart';

import '../models/facility_item.dart';
import '../services/facility_service.dart';
import 'facility_details_screen.dart';
import 'facilities/facility_booking_history_screen.dart';

class FacilitiesPage extends StatefulWidget {
  const FacilitiesPage({super.key});

  @override
  State<FacilitiesPage> createState() => _FacilitiesPageState();
}

class _FacilitiesPageState extends State<FacilitiesPage> {
  List<FacilityItem> _facilities = const [];
  bool _isLoading = true;
  String? _errorMessage;

  @override
  void initState() {
    super.initState();
    _fetchFacilities();
  }

  Future<void> _fetchFacilities() async {
    setState(() {
      _isLoading = true;
      _errorMessage = null;
    });

    final result = await FacilityService.fetchFacilities();
    if (!mounted) return;

    if (result.success) {
      setState(() {
        _facilities = result.facilities.map(FacilityItem.fromJson).toList();
        _isLoading = false;
      });
      return;
    }

    setState(() {
      _errorMessage = result.message ?? 'Cannot reach CampusHub server.';
      _isLoading = false;
    });
  }

  void _openFacilityDetails(FacilityItem facility) {
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => FacilityDetailsScreen(facility: facility),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _fetchFacilities,
      child: ListView(
        cacheExtent: 700,
        padding: const EdgeInsets.fromLTRB(16, 18, 16, 24),
        children: [
          Align(
            alignment: Alignment.centerRight,
            child: TextButton.icon(
              icon: const Icon(Icons.receipt_long_outlined, size: 18),
              label: const Text('My Bookings'),
              onPressed: () => Navigator.of(context).push(
                MaterialPageRoute(
                  builder: (_) => const FacilityBookingHistoryScreen(),
                ),
              ),
            ),
          ),
          if (_isLoading)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 32),
              child: Center(child: CircularProgressIndicator()),
            )
          else if (_errorMessage != null)
            _FacilityEmptyState(
              icon: Icons.cloud_off_outlined,
              title: 'Unable to load facilities',
              message: _errorMessage!,
              actionLabel: 'Retry',
              onAction: _fetchFacilities,
            )
          else if (_facilities.isEmpty)
            _FacilityEmptyState(
              icon: Icons.assignment_outlined,
              title: 'No facilities yet',
              message: 'Newly added facilities will appear here.',
              actionLabel: 'Refresh',
              onAction: _fetchFacilities,
            )
          else
            for (final facility in _facilities) ...[
              GestureDetector(
                onTap: () => _openFacilityDetails(facility),
                child: _FacilityListCard(
                  facility: facility,
                  onBookNow: () => _openFacilityDetails(facility),
                ),
              ),
              const SizedBox(height: 12),
            ],
        ],
      ),
    );
  }
}

class _FacilityEmptyState extends StatelessWidget {
  const _FacilityEmptyState({
    required this.icon,
    required this.title,
    required this.message,
    required this.actionLabel,
    required this.onAction,
  });

  final IconData icon;
  final String title;
  final String message;
  final String actionLabel;
  final VoidCallback onAction;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 28),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(16),
        border: Border.all(color: const Color(0xFFE9EEF7)),
      ),
      child: Column(
        children: [
          Icon(icon, size: 36, color: _FacilityColors.primaryNavy),
          const SizedBox(height: 10),
          Text(
            title,
            style: const TextStyle(
              color: _FacilityColors.primaryNavy,
              fontSize: 15,
              fontWeight: FontWeight.w900,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            message,
            textAlign: TextAlign.center,
            style: const TextStyle(
              color: Color(0xFF6B7280),
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
          const SizedBox(height: 14),
          OutlinedButton(
            onPressed: onAction,
            style: OutlinedButton.styleFrom(
              foregroundColor: _FacilityColors.primaryNavy,
              side: const BorderSide(color: Color(0xFFE5E9F1)),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(10),
              ),
            ),
            child: Text(
              actionLabel,
              style: const TextStyle(fontWeight: FontWeight.w800),
            ),
          ),
        ],
      ),
    );
  }
}

class _FacilityListCard extends StatelessWidget {
  const _FacilityListCard({required this.facility, required this.onBookNow});

  final FacilityItem facility;
  final VoidCallback onBookNow;

  Color get _statusColor {
    switch (facility.status) {
      case 'Open for Booking':
        return const Color(0xFF10B981);
      case 'Temporarily Unavailable':
        return const Color(0xFF2563EB);
      case 'Under Maintenance':
        return const Color(0xFFDC2626);
      default:
        return _FacilityColors.primaryNavy;
    }
  }

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(16),
          border: Border.all(color: const Color(0xFFE9EEF7)),
          boxShadow: [
            BoxShadow(
              color: Colors.black.withValues(alpha: 0.045),
              blurRadius: 18,
              offset: const Offset(0, 8),
            ),
          ],
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            _FacilityPhoto(facility: facility),
            const SizedBox(width: 12),
            Expanded(
              child: Column(
                mainAxisSize: MainAxisSize.min,
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    facility.name,
                    maxLines: 1,
                    overflow: TextOverflow.ellipsis,
                    style: const TextStyle(
                      color: _FacilityColors.primaryNavy,
                      fontSize: 17,
                      fontWeight: FontWeight.w900,
                      height: 1.1,
                    ),
                  ),
                  const SizedBox(height: 7),
                  Wrap(
                    spacing: 10,
                    runSpacing: 5,
                    crossAxisAlignment: WrapCrossAlignment.center,
                    children: [
                      _FacilityStatusPill(
                        label: facility.status,
                        color: _statusColor,
                      ),
                      if (facility.hasRating || facility.hasReviews)
                        Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            const Icon(
                              Icons.star,
                              color: _FacilityColors.campusGold,
                              size: 17,
                            ),
                            const SizedBox(width: 4),
                            Text(
                              facility.hasReviews
                                  ? '${facility.rating} (${facility.reviews})'
                                  : facility.rating,
                              style: const TextStyle(
                                color: Color(0xFF111827),
                                fontSize: 12,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                          ],
                        ),
                    ],
                  ),
                  const SizedBox(height: 8),
                  if ((int.tryParse(facility.capacity) ?? 0) > 0) ...[
                    _FacilityInfoLine(
                      icon: Icons.groups_2_outlined,
                      text: 'Capacity: ${facility.capacity}',
                    ),
                    const SizedBox(height: 4),
                  ],
                  if (facility.rate.isNotEmpty && facility.rate != '0')
                    _FacilityInfoLine(
                      icon: Icons.local_offer_outlined,
                      text: facility.priceLabel,
                    ),
                  if (facility.rate.isNotEmpty && facility.rate != '0')
                    const SizedBox(height: 4),
                  if (facility.slots.trim().isNotEmpty)
                    _FacilityInfoLine(
                      icon: Icons.view_timeline_outlined,
                      text: facility.slots.trim(),
                    ),
                  if (facility.slots.trim().isNotEmpty)
                    const SizedBox(height: 4),
                  const SizedBox(height: 10),
                  Align(
                    alignment: Alignment.bottomRight,
                    child: SizedBox(
                      height: 38,
                      child: ElevatedButton(
                        onPressed: onBookNow,
                        style: ElevatedButton.styleFrom(
                          backgroundColor: _FacilityColors.primaryNavy,
                          foregroundColor: Colors.white,
                          elevation: 0,
                          shape: RoundedRectangleBorder(
                            borderRadius: BorderRadius.circular(10),
                          ),
                          padding: const EdgeInsets.symmetric(horizontal: 12),
                        ),
                        child: const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Text(
                              'Book Now',
                              style: TextStyle(
                                fontSize: 13,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                            SizedBox(width: 5),
                            Icon(Icons.chevron_right, size: 21),
                          ],
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _FacilityPhoto extends StatelessWidget {
  const _FacilityPhoto({required this.facility});

  final FacilityItem facility;

  @override
  Widget build(BuildContext context) {
    final imageUrl = facility.resolvedImageUrl;
    final image = _buildFacilityImage(imageUrl);
    return ClipRRect(
      borderRadius: BorderRadius.circular(12),
      child: Container(
        width: 112,
        height: 150,
        decoration: const BoxDecoration(
          gradient: LinearGradient(
            colors: [Color(0xFFEAF1FF), Color(0xFFF8FAFD)],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: image ?? _fallbackIcon,
      ),
    );
  }

  Widget get _fallbackIcon =>
      Icon(facility.icon, color: _FacilityColors.primaryNavy, size: 44);

  Widget? _buildFacilityImage(String imageUrl) {
    if (imageUrl.isEmpty) return null;

    if (imageUrl.startsWith('data:image/')) {
      final commaIndex = imageUrl.indexOf(',');
      if (commaIndex == -1) return null;

      try {
        final bytes = base64Decode(imageUrl.substring(commaIndex + 1));
        return Image.memory(
          bytes,
          fit: BoxFit.cover,
          gaplessPlayback: true,
          errorBuilder: (context, error, stackTrace) => _fallbackIcon,
        );
      } catch (_) {
        return null;
      }
    }

    final uri = Uri.tryParse(imageUrl);
    if (uri == null || (uri.scheme != 'http' && uri.scheme != 'https')) {
      return null;
    }

    return Image.network(
      imageUrl,
      fit: BoxFit.cover,
      gaplessPlayback: true,
      errorBuilder: (context, error, stackTrace) => _fallbackIcon,
    );
  }
}

class _FacilityStatusPill extends StatelessWidget {
  const _FacilityStatusPill({required this.label, required this.color});

  final String label;
  final Color color;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 9, vertical: 6),
      decoration: BoxDecoration(
        color: color.withValues(alpha: 0.12),
        borderRadius: BorderRadius.circular(10),
      ),
      child: Row(
        mainAxisSize: MainAxisSize.min,
        children: [
          Container(
            width: 7,
            height: 7,
            decoration: BoxDecoration(color: color, shape: BoxShape.circle),
          ),
          const SizedBox(width: 5),
          Text(
            label,
            style: TextStyle(
              color: color,
              fontSize: 11,
              fontWeight: FontWeight.w900,
            ),
          ),
        ],
      ),
    );
  }
}

class _FacilityInfoLine extends StatelessWidget {
  const _FacilityInfoLine({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisSize: MainAxisSize.min,
      children: [
        Icon(icon, size: 15, color: const Color(0xFF374151)),
        const SizedBox(width: 7),
        Flexible(
          child: Text(
            text,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: Color(0xFF111827),
              fontSize: 12,
              fontWeight: FontWeight.w500,
            ),
          ),
        ),
      ],
    );
  }
}

class _FacilityColors {
  static const Color primaryNavy = Color(0xFF142B47);
  static const Color campusGold = Color(0xFFFCB316);
}
