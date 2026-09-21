import 'package:flutter/material.dart';
import '../../models/facility_item.dart';
import '../../services/facility_booking_service.dart';
import '../../session/session_service.dart';
import '../../widgets/facilities/booking_widgets.dart';
import 'facility_booking_status_screen.dart';

class FacilityBookingScreen extends StatefulWidget {
  const FacilityBookingScreen({
    super.key,
    required this.facility,
    this.service = const FacilityBookingService(),
  });
  final FacilityItem facility;
  final FacilityBookingService service;
  @override
  State<FacilityBookingScreen> createState() => _FacilityBookingScreenState();
}

class _FacilityBookingScreenState extends State<FacilityBookingScreen> {
  final _form = GlobalKey<FormState>();
  final _scroll = ScrollController();
  final _fields = {
    for (final key in [
      'full_name',
      'organization',
      'contact_number',
      'email',
      'event_name',
      'purpose',
      'attendees',
      'other_requirements',
      'notes',
    ])
      key: TextEditingController(),
  };
  final _requirements = <String>{};
  final _requestKey = FacilityBookingService.newRequestKey();
  late DateTime _date;
  List<Map<String, dynamic>> _slots = [];
  Map<String, dynamic>? _slot, _quote, _booking;
  String? _error;
  int _step = 0;
  int _loadVersion = 0;
  bool _loading = false, _busy = false;

  @override
  void initState() {
    super.initState();
    final now = DateTime.now();
    _date = DateTime(now.year, now.month, now.day);
    _loadSlots();
    _prefill();
  }

  Future<void> _prefill() async {
    final user = await SessionService.loadUser();
    if (!mounted || user == null) return;
    for (final item in {
      'full_name': user.fullName,
      'contact_number': user.contactNumber,
      'email': user.email,
    }.entries) {
      if (_fields[item.key]!.text.isEmpty) _fields[item.key]!.text = item.value;
    }
  }

  @override
  void dispose() {
    for (final controller in _fields.values) {
      controller.dispose();
    }
    _scroll.dispose();
    super.dispose();
  }

  Future<void> _loadSlots() async {
    final version = ++_loadVersion;
    setState(() {
      _loading = true;
      _slot = null;
      _error = null;
    });
    try {
      final slots = await widget.service.slots(widget.facility.id, _date);
      if (!mounted || version != _loadVersion) return;
      setState(() => _slots = slots);
    } catch (error) {
      if (mounted && version == _loadVersion) setState(() => _error = '$error');
    } finally {
      if (mounted && version == _loadVersion) setState(() => _loading = false);
    }
  }

  Map<String, dynamic> get _schedule => {
    'date': FacilityBookingService.dateKey(_date),
    'start': _slot!['start'],
    'end': _slot!['end'],
  };

  void _go(int step) {
    setState(() {
      _step = step;
      _error = null;
    });
    if (_scroll.hasClients) _scroll.jumpTo(0);
  }

  Future<void> _next() async {
    if (_busy || _slot == null) return;
    if (_step == 1 && !_form.currentState!.validate()) return;
    setState(() {
      _busy = true;
      _error = null;
    });
    try {
      if (_step < 2) {
        final quote = await widget.service.request(
          'facilities/${widget.facility.id}/quote/',
          body: _schedule,
        );
        if (!mounted) return;
        setState(() => _quote = quote);
        _go(_step + 1);
      } else {
        final response = await widget.service.request(
          'bookings/',
          body: {
            ..._schedule,
            'facility_id': widget.facility.id,
            'request_key': _requestKey,
            'quoted_amount': _quote!['total_amount'],
            for (final item in _fields.entries)
              item.key: item.value.text.trim(),
            'additional_requirements': _requirements.toList(),
          },
        );
        if (!mounted) return;
        setState(
          () => _booking = Map<String, dynamic>.from(response['booking']),
        );
        _go(3);
      }
    } catch (error) {
      if (mounted) setState(() => _error = '$error');
    } finally {
      if (mounted) setState(() => _busy = false);
    }
  }

  Widget _field(
    String key,
    String label, {
    bool required = true,
    int lines = 1,
    TextInputType? keyboard,
    String? suffix,
  }) => Padding(
    padding: const EdgeInsets.only(bottom: 14),
    child: TextFormField(
      controller: _fields[key],
      maxLines: lines,
      keyboardType: keyboard,
      style: const TextStyle(fontSize: 14, color: bookingNavy),
      decoration: InputDecoration(
        labelText: label,
        alignLabelWithHint: true,
        suffixText: suffix,
        suffixStyle: const TextStyle(color: bookingMuted, fontSize: 13),
      ),
      validator: (value) {
        final text = value?.trim() ?? '';
        if (required && text.isEmpty) return 'Enter ${label.toLowerCase()}.';
        if (key == 'email' &&
            !RegExp(r'^[^\s@]+@[^\s@]+\.[^\s@]+$').hasMatch(text)) {
          return 'Enter a valid email address.';
        }
        if (key == 'attendees') {
          final count = int.tryParse(text) ?? 0;
          final capacity = int.tryParse(widget.facility.capacity) ?? 0;
          if (count < 1 || (capacity > 0 && count > capacity)) {
            return capacity > 0
                ? 'Enter 1 to $capacity attendees.'
                : 'Enter at least one attendee.';
          }
        }
        if (key == 'other_requirements' &&
            _requirements.contains('Others') &&
            text.isEmpty) {
          return 'Specify your requirements.';
        }
        return null;
      },
    ),
  );

  @override
  Widget build(BuildContext context) => PopScope(
    canPop: _step == 0 || _step == 3,
    onPopInvokedWithResult: (didPop, result) {
      if (!didPop && !_busy) _go(_step - 1);
    },
    child: BookingScaffold(
      title: [
        'Select Schedule',
        'Booking Details',
        'Review Booking',
        'Booking Submitted',
      ][_step],
      bottom: _step == 3
          ? Column(
              mainAxisSize: MainAxisSize.min,
              children: [
                BookingButton(
                  label: 'View Booking Details',
                  onPressed: () {
                    Navigator.of(context).pushReplacement(
                      MaterialPageRoute(
                        builder: (_) => FacilityBookingStatusScreen(
                          booking: _booking!,
                          service: widget.service,
                        ),
                      ),
                    );
                  },
                ),
                const SizedBox(height: 8),
                BookingButton(
                  label: 'Message Admin',
                  outlined: true,
                  onPressed: () =>
                      messageFacilitiesAdmin(context, widget.facility.id),
                ),
                const SizedBox(height: 4),
                TextButton(
                  onPressed: () => Navigator.of(context).pop(),
                  child: const Text('Back to Facilities'),
                ),
              ],
            )
          : BookingButton(
              label: [
                'Next: Booking Details',
                'Next: Review Booking',
                'Submit Booking Request',
              ][_step],
              busy: _busy,
              onPressed: _loading || _slot == null ? null : _next,
            ),
      child: ListView(
        controller: _scroll,
        padding: const EdgeInsets.fromLTRB(16, 0, 16, 32),
        children: [
          BookingSteps(_step),
          if (_error != null)
            Padding(
              padding: const EdgeInsets.only(bottom: 16),
              child: Container(
                padding: const EdgeInsets.all(12),
                decoration: BoxDecoration(
                  color: bookingRedBg,
                  borderRadius: BorderRadius.circular(8),
                  border: Border.all(color: bookingRed.withValues(alpha: 0.3)),
                ),
                child: Row(
                  children: [
                    const Icon(Icons.error_outline, size: 20, color: bookingRed),
                    const SizedBox(width: 8),
                    Expanded(
                      child: Text(
                        _error!,
                        style: const TextStyle(
                          color: bookingRed,
                          fontSize: 13,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                  ],
                ),
              ),
            ),
          if (_step == 0) ...[
            BookingSection(
              'Select Date',
              child: CalendarDatePicker(
                initialDate: _date,
                firstDate: DateUtils.dateOnly(DateTime.now()),
                lastDate: DateTime(DateTime.now().year + 2),
                onDateChanged: (date) {
                  _date = date;
                  _loadSlots();
                },
              ),
            ),
            BookingSection(
              'Available Time Slots',
              child: Wrap(
                spacing: 16,
                runSpacing: 10,
                children: [
                  _legendDot('Available', bookingGreen),
                  _legendDot('Unavailable', bookingGreyDot),
                  _legendDot('Reserved', bookingBlueDot),
                  _legendIcon('Maintenance', Icons.build_outlined),
                  _legendIcon('Class Schedule', Icons.school_outlined),
                ],
              ),
            ),
            BookingSection(
              'Selected Date',
              child: Row(
                children: [
                  const Icon(
                    Icons.calendar_today_outlined,
                    size: 16,
                    color: bookingNavy,
                  ),
                  const SizedBox(width: 8),
                  Text(
                    bookingDate(FacilityBookingService.dateKey(_date)),
                    style: const TextStyle(
                      fontWeight: FontWeight.w600,
                      color: bookingNavy,
                    ),
                  ),
                ],
              ),
            ),
            if (_loading)
              const Center(child: CircularProgressIndicator())
            else if (_error != null)
              BookingButton(
                label: 'Retry Schedule',
                outlined: true,
                onPressed: _loadSlots,
              )
            else if (_slots.isEmpty)
              const Padding(
                padding: EdgeInsets.symmetric(vertical: 16),
                child: Text(
                  'No time slots have been configured. Contact Facilities Admin.',
                  style: TextStyle(color: bookingMuted),
                ),
              )
            else
              ..._slots.map((slot) {
                final selected = _slot == slot;
                final available = slot['status'] == 'available';
                return Padding(
                  padding: const EdgeInsets.only(bottom: 10),
                  child: OutlinedButton(
                    onPressed: available
                        ? () => setState(() => _slot = slot)
                        : null,
                    style: OutlinedButton.styleFrom(
                      minimumSize: const Size(double.infinity, 52),
                      backgroundColor: selected
                          ? bookingGoldBg
                          : (available ? Colors.white : const Color(0xFFF8FAFC)),
                      side: BorderSide(
                        color: selected
                            ? bookingGold
                            : (available ? bookingOutline : const Color(0xFFEEF0F6)),
                        width: selected ? 1.5 : 1,
                      ),
                      shape: RoundedRectangleBorder(
                        borderRadius: BorderRadius.circular(8),
                      ),
                    ),
                    child: Row(
                      children: [
                        Expanded(
                          child: Text(
                            '${slot['label']}',
                            style: TextStyle(
                              fontSize: 13,
                              fontWeight: FontWeight.w600,
                              color: available ? bookingNavy : bookingMuted,
                            ),
                          ),
                        ),
                        const SizedBox(width: 8),
                        Text(
                          bookingStatus(slot['status']),
                          style: TextStyle(
                            fontSize: 12,
                            fontWeight: FontWeight.w600,
                            color: available ? bookingGreen : bookingMuted,
                          ),
                        ),
                        if (selected) ...[
                          const SizedBox(width: 8),
                          const Icon(
                            Icons.check_circle,
                            size: 20,
                            color: bookingNavy,
                          ),
                        ],
                      ],
                    ),
                  ),
                );
              }),
          ],
          if (_step == 1)
            Form(
              key: _form,
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.stretch,
                children: [
                  BookingSection(
                    'Requestor Information',
                    child: Column(
                      children: [
                        _field('full_name', 'Full Name'),
                        _field(
                          'organization',
                          'Organization / Office',
                          required: false,
                        ),
                        _field(
                          'contact_number',
                          'Contact Number',
                          keyboard: TextInputType.phone,
                        ),
                        _field(
                          'email',
                          'Email Address',
                          keyboard: TextInputType.emailAddress,
                        ),
                      ],
                    ),
                  ),
                  BookingSection(
                    'Event Information',
                    child: Column(
                      children: [
                        _field('event_name', 'Event / Activity Name'),
                        _field('purpose', 'Purpose'),
                        _field(
                          'attendees',
                          'Expected Number of Attendees',
                          keyboard: TextInputType.number,
                          suffix: 'persons',
                        ),
                      ],
                    ),
                  ),
                  BookingSection(
                    'Additional Requirements',
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        const Text(
                          '(Select if needed)',
                          style: TextStyle(fontSize: 12, color: bookingMuted),
                        ),
                        const SizedBox(height: 6),
                        for (final label in [
                          'Chairs',
                          'Tables',
                          'Sound System',
                          'Projector',
                          'Others',
                        ])
                          CheckboxListTile(
                            contentPadding: EdgeInsets.zero,
                            controlAffinity: ListTileControlAffinity.leading,
                            title: Text(
                              label,
                              style: const TextStyle(fontSize: 14),
                            ),
                            value: _requirements.contains(label),
                            onChanged: (checked) => setState(() {
                              if (checked == true) {
                                _requirements.add(label);
                              } else {
                                _requirements.remove(label);
                              }
                            }),
                          ),
                        if (_requirements.contains('Others'))
                          _field(
                            'other_requirements',
                            'Please specify',
                            required: false,
                          ),
                        const SizedBox(height: 4),
                        const Text(
                          'Additional requirements are subject to availability and a separate quote.',
                          style: TextStyle(fontSize: 12, color: bookingMuted),
                        ),
                      ],
                    ),
                  ),
                  BookingSection(
                    'Additional Notes',
                    child: _field('notes', 'Notes', required: false, lines: 3),
                  ),
                ],
              ),
            ),
          if (_step == 2) ...[
            BookingSection(
              'Booking Summary',
              child: BookingCard(
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    BookingFacilitySummary(widget.facility),
                    const Divider(color: bookingOutline),
                    const SizedBox(height: 6),
                    const Text(
                      'Schedule',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color: bookingNavy,
                      ),
                    ),
                    const SizedBox(height: 6),
                    BookingValue(
                      'Date',
                      bookingDate(
                        FacilityBookingService.dateKey(_date),
                        withWeekday: true,
                      ),
                      icon: Icons.calendar_today_outlined,
                    ),
                    BookingValue(
                      'Time',
                      '${bookingTime(_slot!['start'])} - ${bookingTime(_slot!['end'])}',
                      icon: Icons.access_time,
                    ),
                    BookingValue('Duration', '${_quote!['hours']} hours'),
                    const Divider(color: bookingOutline),
                    const SizedBox(height: 6),
                    const Text(
                      'Requestor Information',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color: bookingNavy,
                      ),
                    ),
                    const SizedBox(height: 6),
                    BookingValue(
                      'Name',
                      _fields['full_name']!.text,
                      icon: Icons.person_outline,
                    ),
                    if (_fields['organization']!.text.isNotEmpty)
                      BookingValue(
                        'Organization',
                        _fields['organization']!.text,
                        icon: Icons.apartment_outlined,
                      ),
                    BookingValue(
                      'Contact',
                      _fields['contact_number']!.text,
                      icon: Icons.phone_outlined,
                    ),
                    BookingValue(
                      'Email',
                      _fields['email']!.text,
                      icon: Icons.mail_outline,
                    ),
                    const Divider(color: bookingOutline),
                    const SizedBox(height: 6),
                    const Text(
                      'Event Information',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color: bookingNavy,
                      ),
                    ),
                    const SizedBox(height: 6),
                    BookingValue('Event / Activity', _fields['event_name']!.text),
                    BookingValue('Purpose', _fields['purpose']!.text),
                    BookingValue(
                      'Attendees',
                      '${_fields['attendees']!.text} persons',
                    ),
                    if (_requirements.isNotEmpty) ...[
                      const Divider(color: bookingOutline),
                      const SizedBox(height: 6),
                      const Text(
                        'Additional Requirements',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                          color: bookingNavy,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        [
                          ..._requirements,
                          if (_requirements.contains('Others') &&
                              _fields['other_requirements']!.text.isNotEmpty)
                            _fields['other_requirements']!.text,
                        ].join(', '),
                        style: const TextStyle(fontSize: 13, color: bookingNavy),
                      ),
                    ],
                    if (_fields['notes']!.text.isNotEmpty) ...[
                      const Divider(color: bookingOutline),
                      const SizedBox(height: 6),
                      const Text(
                        'Additional Notes',
                        style: TextStyle(
                          fontSize: 13,
                          fontWeight: FontWeight.w700,
                          color: bookingNavy,
                        ),
                      ),
                      const SizedBox(height: 6),
                      Text(
                        _fields['notes']!.text,
                        style: const TextStyle(fontSize: 13, color: bookingNavy),
                      ),
                    ],
                    const Divider(color: bookingOutline),
                    const SizedBox(height: 6),
                    const Text(
                      'Estimated Cost Breakdown',
                      style: TextStyle(
                        fontSize: 13,
                        fontWeight: FontWeight.w700,
                        color: bookingNavy,
                      ),
                    ),
                    const SizedBox(height: 6),
                    BookingValue(
                      'Base Rental Fee (${_quote!['hours']} hours)',
                      bookingMoney(_quote!['base_amount']),
                    ),
                    if (_requirements.isNotEmpty)
                      const BookingValue(
                        'Additional Requirements',
                        'Subject to admin quotation',
                      ),
                    const Divider(color: bookingOutline),
                    BookingValue(
                      'Total Amount',
                      bookingMoney(_quote!['total_amount']),
                      bold: true,
                      valueSize: 18,
                      valueColor: bookingNavy,
                    ),
                  ],
                ),
              ),
            ),
            if (widget.facility.termsConditions.isNotEmpty)
              BookingSection(
                'Rules & Guidelines',
                child: BookingCard(
                  child: Text(
                    widget.facility.termsConditions,
                    style: const TextStyle(fontSize: 13, height: 1.5),
                  ),
                ),
              ),
          ],
          if (_step == 3) ...[
            Padding(
              padding: const EdgeInsets.symmetric(vertical: 20),
              child: Center(
                child: Container(
                  width: 96,
                  height: 96,
                  decoration: BoxDecoration(
                    color: const Color(0xFFEEF2FF),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    Icons.assignment_turned_in_outlined,
                    size: 54,
                    color: bookingNavy,
                  ),
                ),
              ),
            ),
            const Text(
              'Booking Request Submitted!',
              textAlign: TextAlign.center,
              style: TextStyle(
                fontSize: 20,
                fontWeight: FontWeight.w700,
                color: bookingNavy,
              ),
            ),
            const SizedBox(height: 10),
            const Text(
              'Your booking request has been successfully submitted. Please wait for the admin to review and approve your request.',
              textAlign: TextAlign.center,
              style: TextStyle(fontSize: 13, height: 1.5, color: bookingMuted),
            ),
            const SizedBox(height: 22),
            BookingCard(
              child: Column(
                children: [
                  BookingValue('Booking ID', _booking!['id'], bold: true),
                  BookingValue('Facility', widget.facility.name),
                  BookingValue('Date', bookingDate(_booking!['date'])),
                  BookingValue(
                    'Time',
                    '${bookingTime(_booking!['start'])} - ${bookingTime(_booking!['end'])}',
                  ),
                  Padding(
                    padding: const EdgeInsets.symmetric(vertical: 7),
                    child: Row(
                      mainAxisAlignment: MainAxisAlignment.spaceBetween,
                      children: [
                        const Text(
                          'Status',
                          style: TextStyle(fontSize: 12, color: bookingMuted),
                        ),
                        BookingStatusBadge(_booking!['status']),
                      ],
                    ),
                  ),
                ],
              ),
            ),
          ],
        ],
      ),
    ),
  );

  Widget _legendDot(String label, Color color) => Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Container(
        width: 8,
        height: 8,
        decoration: BoxDecoration(color: color, shape: BoxShape.circle),
      ),
      const SizedBox(width: 5),
      Text(label, style: const TextStyle(fontSize: 11)),
    ],
  );

  Widget _legendIcon(String label, IconData icon) => Row(
    mainAxisSize: MainAxisSize.min,
    children: [
      Icon(icon, size: 14, color: bookingNavy),
      const SizedBox(width: 5),
      Text(label, style: const TextStyle(fontSize: 11)),
    ],
  );
}
