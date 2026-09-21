import 'package:flutter/material.dart';
import '../../services/facility_booking_service.dart';
import '../../widgets/facilities/booking_widgets.dart';
import 'facility_booking_status_screen.dart';

class FacilityBookingHistoryScreen extends StatefulWidget {
  const FacilityBookingHistoryScreen({
    super.key,
    this.service = const FacilityBookingService(),
  });
  final FacilityBookingService service;
  @override
  State<FacilityBookingHistoryScreen> createState() =>
      _FacilityBookingHistoryScreenState();
}

class _FacilityBookingHistoryScreenState
    extends State<FacilityBookingHistoryScreen> {
  late Future<Map<String, dynamic>> _future;
  @override
  void initState() {
    super.initState();
    _future = widget.service.request('bookings/');
  }

  Future<void> _refresh() async {
    setState(() => _future = widget.service.request('bookings/'));
    try {
      await _future;
    } catch (_) {
      // FutureBuilder presents the retry state.
    }
  }

  @override
  Widget build(BuildContext context) => BookingScaffold(
    title: 'My Bookings',
    child: FutureBuilder<Map<String, dynamic>>(
      future: _future,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return Center(
            child: Padding(
              padding: const EdgeInsets.all(20),
              child: Column(
                mainAxisSize: MainAxisSize.min,
                children: [
                  Text('${snapshot.error}'),
                  const SizedBox(height: 10),
                  BookingButton(
                    label: 'Retry',
                    outlined: true,
                    onPressed: _refresh,
                  ),
                ],
              ),
            ),
          );
        }
        final bookings = (snapshot.data?['bookings'] ?? []) as List;
        return RefreshIndicator(
          onRefresh: _refresh,
          child: ListView(
            physics: const AlwaysScrollableScrollPhysics(),
            padding: const EdgeInsets.all(16),
            children: [
              if (bookings.isEmpty)
                const Padding(
                  padding: EdgeInsets.symmetric(vertical: 40),
                  child: Center(
                    child: Text(
                      'No booking requests yet.',
                      textAlign: TextAlign.center,
                      style: TextStyle(color: bookingMuted),
                    ),
                  ),
                ),
              for (final booking in bookings)
                Padding(
                  padding: const EdgeInsets.only(bottom: 12),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(8),
                    onTap: () async {
                      await Navigator.of(context).push(
                        MaterialPageRoute(
                          builder: (_) => FacilityBookingStatusScreen(
                            booking: Map<String, dynamic>.from(booking),
                            service: widget.service,
                          ),
                        ),
                      );
                      if (mounted) _refresh();
                    },
                    child: BookingCard(
                      padding: const EdgeInsets.all(14),
                      child: Row(
                        children: [
                          Container(
                            width: 40,
                            height: 40,
                            decoration: BoxDecoration(
                              color: const Color(0xFFF1F5F9),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: const Icon(
                              Icons.event_note_outlined,
                              color: bookingNavy,
                              size: 22,
                            ),
                          ),
                          const SizedBox(width: 12),
                          Expanded(
                            child: Column(
                              crossAxisAlignment: CrossAxisAlignment.start,
                              children: [
                                Text(
                                  '${booking['facility']?['name'] ?? 'Facility'}',
                                  style: const TextStyle(
                                    fontWeight: FontWeight.w700,
                                    fontSize: 14,
                                    color: bookingNavy,
                                  ),
                                ),
                                const SizedBox(height: 4),
                                Text(
                                  bookingDate(booking['date']),
                                  style: const TextStyle(
                                    fontSize: 12,
                                    color: bookingMuted,
                                  ),
                                ),
                              ],
                            ),
                          ),
                          BookingStatusBadge('${booking['status']}'),
                          const SizedBox(width: 6),
                          const Icon(
                            Icons.chevron_right,
                            color: bookingMuted,
                            size: 18,
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
            ],
          ),
        );
      },
    ),
  );
}
