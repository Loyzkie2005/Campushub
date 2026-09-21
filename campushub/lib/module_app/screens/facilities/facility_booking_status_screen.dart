import 'package:flutter/material.dart';
import '../../models/facility_item.dart';
import '../../services/facility_booking_service.dart';
import '../../widgets/facilities/booking_widgets.dart';

class FacilityBookingStatusScreen extends StatefulWidget {
  const FacilityBookingStatusScreen({
    super.key,
    required this.booking,
    this.service = const FacilityBookingService(),
  });
  final Map<String, dynamic> booking;
  final FacilityBookingService service;
  @override
  State<FacilityBookingStatusScreen> createState() =>
      _FacilityBookingStatusScreenState();
}

class _FacilityBookingStatusScreenState
    extends State<FacilityBookingStatusScreen>
    with WidgetsBindingObserver {
  late Map<String, dynamic> _booking;
  bool _busy = false;
  String? _error;

  @override
  void initState() {
    super.initState();
    _booking = widget.booking;
    WidgetsBinding.instance.addObserver(this);
    _refresh();
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    super.dispose();
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) _refresh();
  }

  Future<void> _refresh() async {
    try {
      final result = await widget.service.request(
        'bookings/${_booking['id']}/',
      );
      if (mounted) {
        setState(() {
          _booking = Map<String, dynamic>.from(result['booking']);
          _error = null;
        });
      }
    } catch (error) {
      if (mounted) setState(() => _error = '$error');
    }
  }

  Future<void> _cancel() async {
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (context) => AlertDialog(
        title: const Text(
          'Cancel this request?',
          style: TextStyle(fontWeight: FontWeight.w700, color: bookingNavy),
        ),
        content: const Text('Your selected schedule will be released.'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(context, false),
            child: const Text('Keep Request'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(context, true),
            style: TextButton.styleFrom(foregroundColor: bookingRed),
            child: const Text('Cancel Request'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    setState(() => _busy = true);
    try {
      final result = await widget.service.request(
        'bookings/${_booking['id']}/cancel/',
        body: {},
      );
      if (mounted) {
        setState(() {
          _booking = Map<String, dynamic>.from(result['booking']);
          _error = null;
        });
      }
    } catch (error) {
      if (mounted) setState(() => _error = '$error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final status = '${_booking['status']}';
    final approved = ['approved', 'completed'].contains(status);
    final paid = _booking['payment_status'] == 'paid';
    final terminal = ['rejected', 'cancelled'].contains(status);
    final canCancel = _booking['can_cancel'] == true;
    final facility = _booking['facility'] is Map
        ? FacilityItem.fromJson(Map<String, dynamic>.from(_booking['facility']))
        : null;

    final facilityName = facility?.name ??
        _booking['facility']?['name'] ??
        'Facility';

    return BookingScaffold(
      title: 'Booking Details',
      actions: [
        IconButton(
          tooltip: 'Refresh booking',
          onPressed: _refresh,
          icon: const Icon(Icons.refresh),
        ),
      ],
      bottom: approved
          ? Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                if (_booking['can_view_slip'] == true) ...[
                  BookingButton(
                    label: 'View Booking Slip',
                    onPressed: () => Navigator.of(context).push(
                      MaterialPageRoute(
                        builder: (_) => _BookingSlip(booking: _booking),
                      ),
                    ),
                  ),
                  const SizedBox(height: 8),
                ],
                if (facility != null)
                  BookingButton(
                    label: 'Message Admin',
                    outlined: true,
                    onPressed: () => messageFacilitiesAdmin(context, facility.id),
                  ),
              ],
            )
          : canCancel
          ? Row(
              children: [
                if (facility != null) ...[
                  Expanded(
                    child: BookingButton(
                      label: 'Message Admin',
                      outlined: true,
                      onPressed: () =>
                          messageFacilitiesAdmin(context, facility.id),
                    ),
                  ),
                  const SizedBox(width: 10),
                ],
                Expanded(
                  child: BookingButton(
                    label: _busy ? 'Cancelling...' : 'Cancel Request',
                    outlined: true,
                    danger: true,
                    onPressed: _busy ? null : _cancel,
                  ),
                ),
              ],
            )
          : (facility != null
              ? BookingButton(
                  label: 'Message Admin',
                  outlined: true,
                  onPressed: () => messageFacilitiesAdmin(context, facility.id),
                )
              : null),
      child: RefreshIndicator(
        onRefresh: _refresh,
        child: ListView(
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          children: [
            if (_error != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Container(
                  padding: const EdgeInsets.all(12),
                  decoration: BoxDecoration(
                    color: bookingRedBg,
                    borderRadius: BorderRadius.circular(8),
                  ),
                  child: Text(
                    _error!,
                    style: const TextStyle(
                      color: bookingRed,
                      fontWeight: FontWeight.w600,
                    ),
                  ),
                ),
              ),
            Row(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Expanded(
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.start,
                    children: [
                      const Text(
                        'Booking ID',
                        style: TextStyle(fontSize: 12, color: bookingMuted),
                      ),
                      const SizedBox(height: 4),
                      SelectableText(
                        '${_booking['id']}',
                        style: const TextStyle(
                          fontSize: 17,
                          fontWeight: FontWeight.w700,
                          color: bookingNavy,
                        ),
                      ),
                    ],
                  ),
                ),
                BookingStatusBadge(status),
              ],
            ),
            const SizedBox(height: 6),
            Text(
              approved
                  ? 'Approved on ${bookingDate(_booking['created_at'])}'
                  : 'Requested on ${bookingDate(_booking['created_at'])}',
              style: const TextStyle(fontSize: 12, color: bookingMuted),
            ),
            const SizedBox(height: 24),
            BookingSection(
              'Booking Progress',
              child: Column(
                children: [
                  _ProgressRow(
                    'Request Submitted',
                    'Your booking request has been submitted.',
                    timestamp: bookingDate(_booking['created_at']),
                    done: true,
                    useGreenCheck: approved,
                  ),
                  if (terminal)
                    _ProgressRow(
                      bookingStatus(status),
                      'This booking request is closed.',
                      done: true,
                      last: true,
                    )
                  else ...[
                    _ProgressRow(
                      'Under Review',
                      approved
                          ? 'The admin has reviewed your request.'
                          : 'Waiting for the admin to review your request.',
                      timestamp: approved ? bookingDate(_booking['created_at']) : null,
                      done: approved,
                      current: !approved,
                      useGreenCheck: approved,
                    ),
                    _ProgressRow(
                      'Approved',
                      approved
                          ? 'This booking has been approved by the admin.'
                          : 'Waiting for approval.',
                      timestamp: approved ? bookingDate(_booking['created_at']) : null,
                      done: approved,
                      useGreenCheck: approved,
                    ),
                    _ProgressRow(
                      'Payment Recorded',
                      paid
                          ? 'Payment has been recorded.'
                          : 'Waiting for payment confirmation.',
                      done: paid,
                      current: approved && !paid,
                      useGreenCheck: paid,
                    ),
                    _ProgressRow(
                      'Reserved',
                      approved
                          ? 'Your facility is reserved on the selected schedule.'
                          : 'Waiting for an approved reservation.',
                      done: approved,
                      last: true,
                      useGreenCheck: approved && paid,
                    ),
                  ],
                ],
              ),
            ),
            BookingSection(
              'Booking Information',
              child: BookingCard(
                child: Column(
                  children: [
                    BookingValue('Facility', facilityName),
                    BookingValue(
                      'Date',
                      bookingDate(_booking['date'], withWeekday: true),
                    ),
                    BookingValue(
                      'Time',
                      '${bookingTime(_booking['start'])} - ${bookingTime(_booking['end'])}',
                    ),
                    BookingValue(
                      'Total Amount',
                      bookingMoney(_booking['total_amount']),
                    ),
                    Padding(
                      padding: const EdgeInsets.symmetric(vertical: 7),
                      child: Row(
                        children: [
                          const Expanded(
                            child: Text(
                              'Payment Status',
                              style: TextStyle(fontSize: 12, color: bookingMuted),
                            ),
                          ),
                          const SizedBox(width: 8),
                          BookingStatusBadge('${_booking['payment_status']}'),
                        ],
                      ),
                    ),
                    if (paid || (double.tryParse('${_booking['paid_amount']}') ?? 0) > 0)
                      BookingValue(
                        'Amount Paid',
                        bookingMoney(_booking['paid_amount']),
                      ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _ProgressRow extends StatelessWidget {
  const _ProgressRow(
    this.title,
    this.description, {
    this.timestamp,
    this.done = false,
    this.current = false,
    this.last = false,
    this.useGreenCheck = false,
  });
  final String title, description;
  final String? timestamp;
  final bool done, current, last, useGreenCheck;

  @override
  Widget build(BuildContext context) => IntrinsicHeight(
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        SizedBox(
          width: 28,
          child: Column(
            children: [
              Icon(
                done
                    ? Icons.check_circle
                    : current
                    ? Icons.radio_button_checked
                    : Icons.radio_button_unchecked,
                size: 20,
                color: done
                    ? (useGreenCheck ? bookingGreen : bookingBlueDot)
                    : current
                    ? bookingGold
                    : bookingOutline,
              ),
              if (!last)
                Expanded(
                  child: VerticalDivider(
                    color: done
                        ? (useGreenCheck ? bookingGreen : bookingBlueDot)
                        : bookingOutline,
                    thickness: 1.5,
                  ),
                ),
            ],
          ),
        ),
        const SizedBox(width: 10),
        Expanded(
          child: Padding(
            padding: const EdgeInsets.only(bottom: 22),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  title,
                  style: const TextStyle(
                    fontSize: 13,
                    fontWeight: FontWeight.w700,
                    color: bookingNavy,
                  ),
                ),
                if (timestamp != null) ...[
                  const SizedBox(height: 2),
                  Text(
                    timestamp!,
                    style: const TextStyle(fontSize: 11, color: bookingMuted),
                  ),
                ],
                const SizedBox(height: 4),
                Text(
                  description,
                  style: const TextStyle(
                    fontSize: 12,
                    height: 1.4,
                    color: bookingMuted,
                  ),
                ),
              ],
            ),
          ),
        ),
      ],
    ),
  );
}

class _BookingSlip extends StatelessWidget {
  const _BookingSlip({required this.booking});
  final Map<String, dynamic> booking;
  @override
  Widget build(BuildContext context) {
    final details = Map<String, dynamic>.from(booking['details'] ?? {});
    return BookingScaffold(
      title: 'Booking Slip',
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          BookingCard(
            padding: const EdgeInsets.all(20),
            child: Column(
              children: [
                const Text(
                  'USTP Oroquieta Campus',
                  textAlign: TextAlign.center,
                  style: TextStyle(
                    fontSize: 16,
                    fontWeight: FontWeight.w700,
                    color: bookingNavy,
                  ),
                ),
                const SizedBox(height: 4),
                const Text(
                  'Facilities and Spaces Rental Booking Slip',
                  textAlign: TextAlign.center,
                  style: TextStyle(fontSize: 13, color: bookingMuted),
                ),
                const SizedBox(height: 20),
                BookingValue('Booking No.', booking['id'], bold: true),
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 7),
                  child: Row(
                    children: [
                      const Expanded(
                        child: Text(
                          'Status',
                          style: TextStyle(fontSize: 12, color: bookingMuted),
                        ),
                      ),
                      const SizedBox(width: 8),
                      BookingStatusBadge(booking['status']),
                    ],
                  ),
                ),
                const Divider(color: bookingOutline),
                BookingValue('Requestor', '${details['full_name'] ?? ''}'),
                if (details['organization'] != null &&
                    '${details['organization']}'.isNotEmpty)
                  BookingValue('Organization', '${details['organization']}'),
                BookingValue('Contact', '${details['contact_number'] ?? ''}'),
                BookingValue('Email', '${details['email'] ?? ''}'),
                const Divider(color: bookingOutline),
                BookingValue('Facility', '${booking['facility']?['name'] ?? ''}'),
                BookingValue(
                  'Date',
                  bookingDate(booking['date'], withWeekday: true),
                ),
                BookingValue('Start', bookingTime(booking['start'])),
                BookingValue('End', bookingTime(booking['end'])),
                if (details['event_name'] != null &&
                    '${details['event_name']}'.isNotEmpty)
                  BookingValue('Event', '${details['event_name']}'),
                if (details['purpose'] != null &&
                    '${details['purpose']}'.isNotEmpty)
                  BookingValue('Purpose', '${details['purpose']}'),
                if (details['attendees'] != null)
                  BookingValue('Attendees', '${details['attendees']} persons'),
                if (details['additional_requirements'] is List &&
                    (details['additional_requirements'] as List).isNotEmpty)
                  BookingValue(
                    'Requirements',
                    ((details['additional_requirements'] ?? []) as List)
                        .join(', '),
                  ),
                if (details['notes'] != null &&
                    '${details['notes']}'.isNotEmpty)
                  BookingValue('Notes', '${details['notes']}'),
                const Divider(color: bookingOutline),
                BookingValue(
                  'Rental Amount',
                  bookingMoney(booking['total_amount']),
                  bold: true,
                  valueSize: 16,
                ),
                Padding(
                  padding: const EdgeInsets.symmetric(vertical: 7),
                  child: Row(
                    children: [
                      const Expanded(
                        child: Text(
                          'Payment',
                          style: TextStyle(fontSize: 12, color: bookingMuted),
                        ),
                      ),
                      const SizedBox(width: 8),
                      BookingStatusBadge(booking['payment_status']),
                    ],
                  ),
                ),
                for (final receipt in booking['receipts'] ?? [])
                  BookingValue('Official Receipt', '${receipt['number']}'),
              ],
            ),
          ),
        ],
      ),
    );
  }
}
