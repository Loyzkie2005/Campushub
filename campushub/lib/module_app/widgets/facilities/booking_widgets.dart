import 'package:flutter/material.dart';
import '../../models/facility_item.dart';
import '../../services/chat_service.dart';
import '../../services/facility_booking_service.dart';
import '../../screens/messages_screen.dart';
import '../product_image.dart';

const bookingNavy = Color(0xFF1A1851);
const bookingGold = Color(0xFFFCB316);
const bookingOutline = Color(0xFFE2E4EC);
const bookingMuted = Color(0xFF66687A);
const bookingGreen = Color(0xFF1B873F);
const bookingGreenBg = Color(0xFFEAF7EE);
const bookingGoldBg = Color(0xFFFFF8E6);
const bookingGoldText = Color(0xFFB45309);
const bookingRed = Color(0xFFDC2626);
const bookingRedBg = Color(0xFFFEE2E2);
const bookingBlueDot = Color(0xFF2563EB);
const bookingGreyDot = Color(0xFF9CA3AF);

String bookingMoney(dynamic amount) =>
    '\u20b1${(double.tryParse('$amount') ?? 0).toStringAsFixed(2)}';

String bookingDate(String value, {bool withWeekday = false}) {
  final date = DateTime.tryParse(value);
  if (date == null) return value;
  const months = [
    'Jan',
    'Feb',
    'Mar',
    'Apr',
    'May',
    'Jun',
    'Jul',
    'Aug',
    'Sep',
    'Oct',
    'Nov',
    'Dec',
  ];
  const weekdays = [
    'Monday',
    'Tuesday',
    'Wednesday',
    'Thursday',
    'Friday',
    'Saturday',
    'Sunday',
  ];
  final formatted = '${months[date.month - 1]} ${date.day}, ${date.year}';
  if (withWeekday) {
    return '$formatted (${weekdays[date.weekday - 1]})';
  }
  return formatted;
}

String bookingTime(String value) {
  final parts = value.split(':');
  if (parts.length < 2) return value;
  final hour = int.tryParse(parts[0]) ?? 0;
  return '${hour % 12 == 0 ? 12 : hour % 12}:${parts[1]} ${hour < 12 ? 'AM' : 'PM'}';
}

String bookingStatus(String status) => switch (status.toLowerCase()) {
  'pending' || 'pending approval' => 'Pending Approval',
  'approved' => 'Approved',
  'completed' => 'Completed',
  'cancelled' => 'Cancelled',
  'rejected' => 'Rejected',
  'paid' => 'Paid',
  'unpaid' || 'pending payment' => 'Pending Payment',
  'class' || 'class schedule' => 'Class Schedule',
  'maintenance' => 'Maintenance',
  'reserved' => 'Reserved',
  'available' || 'open for booking' => 'Available',
  _ => status.isEmpty ? 'Unavailable' : status,
};

class BookingStatusBadge extends StatelessWidget {
  const BookingStatusBadge(this.status, {super.key, this.fontSize = 11});
  final String status;
  final double fontSize;

  @override
  Widget build(BuildContext context) {
    final lower = status.toLowerCase();
    final isGreen = lower == 'available' ||
        lower == 'approved' ||
        lower == 'completed' ||
        lower == 'paid' ||
        lower == 'open for booking';
    final isGold = lower == 'pending' ||
        lower == 'pending approval' ||
        lower == 'unpaid' ||
        lower == 'pending payment';
    final isRed = lower == 'cancelled' || lower == 'rejected';
    final isClass = lower == 'class' || lower == 'class schedule';

    final Color bg;
    final Color fg;
    if (isGreen) {
      bg = bookingGreenBg;
      fg = bookingGreen;
    } else if (isGold) {
      bg = bookingGoldBg;
      fg = bookingGoldText;
    } else if (isRed) {
      bg = bookingRedBg;
      fg = bookingRed;
    } else if (isClass) {
      bg = const Color(0xFFEEF2FF);
      fg = bookingNavy;
    } else {
      bg = const Color(0xFFF1F5F9);
      fg = bookingMuted;
    }

    final displayLabel = lower == 'open for booking'
        ? 'Open for Booking'
        : bookingStatus(status);

    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 10, vertical: 4),
      decoration: BoxDecoration(
        color: bg,
        borderRadius: BorderRadius.circular(16),
      ),
      child: Text(
        displayLabel,
        style: TextStyle(
          fontSize: fontSize,
          fontWeight: FontWeight.w600,
          color: fg,
        ),
      ),
    );
  }
}

class BookingScaffold extends StatelessWidget {
  const BookingScaffold({
    super.key,
    required this.title,
    required this.child,
    this.bottom,
    this.actions,
  });
  final String title;
  final Widget child;
  final Widget? bottom;
  final List<Widget>? actions;
  @override
  Widget build(BuildContext context) => Theme(
    data: Theme.of(context).copyWith(
      colorScheme:
          ColorScheme.fromSeed(
            seedColor: bookingNavy,
            brightness: Brightness.light,
          ).copyWith(
            primary: bookingNavy,
            secondary: bookingGold,
            surface: Colors.white,
          ),
      scaffoldBackgroundColor: Colors.white,
      inputDecorationTheme: InputDecorationTheme(
        filled: true,
        fillColor: Colors.white,
        labelStyle: const TextStyle(color: bookingMuted, fontSize: 13),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 12,
          vertical: 15,
        ),
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: bookingOutline),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(8),
          borderSide: const BorderSide(color: bookingOutline),
        ),
      ),
    ),
    child: Scaffold(
      appBar: AppBar(
        title: Text(
          title,
          style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700),
        ),
        centerTitle: true,
        backgroundColor: Colors.white,
        foregroundColor: bookingNavy,
        surfaceTintColor: Colors.transparent,
        scrolledUnderElevation: 0,
        actions: actions,
      ),
      body: SafeArea(
        top: false,
        child: Align(
          alignment: Alignment.topCenter,
          child: ConstrainedBox(
            constraints: const BoxConstraints(maxWidth: 620),
            child: child,
          ),
        ),
      ),
      bottomNavigationBar: bottom == null
          ? null
          : SafeArea(
              top: false,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(16, 8, 16, 12),
                child: bottom,
              ),
            ),
    ),
  );
}

class BookingButton extends StatelessWidget {
  const BookingButton({
    super.key,
    required this.label,
    this.onPressed,
    this.busy = false,
    this.outlined = false,
    this.danger = false,
  });
  final String label;
  final VoidCallback? onPressed;
  final bool busy;
  final bool outlined;
  final bool danger;
  @override
  Widget build(BuildContext context) {
    final content = busy
        ? SizedBox(
            width: 20,
            height: 20,
            child: CircularProgressIndicator(
              strokeWidth: 2,
              color: outlined ? (danger ? bookingRed : bookingNavy) : Colors.white,
            ),
          )
        : Text(label, textAlign: TextAlign.center);
    if (outlined) {
      final color = danger ? bookingRed : bookingNavy;
      return OutlinedButton(
        onPressed: busy ? null : onPressed,
        style: OutlinedButton.styleFrom(
          minimumSize: const Size(double.infinity, 48),
          foregroundColor: color,
          side: BorderSide(color: color),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
          textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
        ),
        child: content,
      );
    }
    return ElevatedButton(
      onPressed: busy ? null : onPressed,
      style: ElevatedButton.styleFrom(
        minimumSize: const Size(double.infinity, 48),
        elevation: 0,
        backgroundColor: danger ? bookingRed : bookingNavy,
        foregroundColor: Colors.white,
        textStyle: const TextStyle(fontSize: 14, fontWeight: FontWeight.w700),
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(6)),
      ),
      child: content,
    );
  }
}

class BookingSection extends StatelessWidget {
  const BookingSection(this.title, {super.key, required this.child});
  final String title;
  final Widget child;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 18),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        Text(
          title,
          style: const TextStyle(
            fontSize: 15,
            fontWeight: FontWeight.w700,
            color: bookingNavy,
          ),
        ),
        const SizedBox(height: 8),
        child,
      ],
    ),
  );
}

class BookingCard extends StatelessWidget {
  const BookingCard({super.key, required this.child, this.padding});
  final Widget child;
  final EdgeInsetsGeometry? padding;

  @override
  Widget build(BuildContext context) => Container(
    padding: padding ?? const EdgeInsets.all(14),
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(8),
      border: Border.all(color: bookingOutline),
    ),
    child: child,
  );
}

class BookingSteps extends StatelessWidget {
  const BookingSteps(this.step, {super.key});
  final int step;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(top: 6, bottom: 18),
    child: Row(
      children: List.generate(
        4,
        (index) => Expanded(
          child: Column(
            children: [
              Row(
                children: [
                  Expanded(
                    child: Divider(
                      color: index == 0
                          ? Colors.transparent
                          : (index <= step ? bookingNavy : bookingOutline),
                    ),
                  ),
                  Semantics(
                    label: 'Step ${index + 1} of 4',
                    selected: index == step,
                    child: Container(
                      width: 30,
                      height: 30,
                      alignment: Alignment.center,
                      decoration: BoxDecoration(
                        shape: BoxShape.circle,
                        color: index <= step ? bookingNavy : Colors.white,
                        border: Border.all(
                          color: index <= step ? bookingNavy : bookingOutline,
                        ),
                      ),
                      child: Text(
                        '${index + 1}',
                        style: TextStyle(
                          color: index <= step ? Colors.white : bookingMuted,
                          fontSize: 12,
                          fontWeight: FontWeight.w700,
                        ),
                      ),
                    ),
                  ),
                  Expanded(
                    child: Divider(
                      color: index == 3
                          ? Colors.transparent
                          : (index < step ? bookingNavy : bookingOutline),
                    ),
                  ),
                ],
              ),
              const SizedBox(height: 8),
              Text(
                ['Schedule', 'Details', 'Review', 'Submit'][index],
                style: TextStyle(
                  fontSize: 11,
                  fontWeight: index == step ? FontWeight.w700 : FontWeight.w500,
                  color: index <= step ? bookingNavy : bookingMuted,
                ),
              ),
            ],
          ),
        ),
      ),
    ),
  );
}

class BookingValue extends StatelessWidget {
  const BookingValue(
    this.label,
    this.value, {
    super.key,
    this.icon,
    this.bold = false,
    this.valueSize,
    this.valueColor,
  });
  final String label;
  final String value;
  final IconData? icon;
  final bool bold;
  final double? valueSize;
  final Color? valueColor;

  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 7),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        if (icon != null) ...[
          Icon(icon, size: 16, color: bookingNavy),
          const SizedBox(width: 8),
        ],
        Expanded(
          child: Text(
            label,
            style: const TextStyle(fontSize: 12, color: bookingMuted),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Text(
            value,
            textAlign: TextAlign.right,
            style: TextStyle(
              fontSize: valueSize ?? 13,
              color: valueColor ?? bookingNavy,
              fontWeight: bold ? FontWeight.w700 : FontWeight.w600,
            ),
          ),
        ),
      ],
    ),
  );
}

class BookingFacilitySummary extends StatelessWidget {
  const BookingFacilitySummary(this.facility, {super.key});
  final FacilityItem facility;
  @override
  Widget build(BuildContext context) => Padding(
    padding: const EdgeInsets.only(bottom: 16),
    child: Row(
      children: [
        ClipRRect(
          borderRadius: BorderRadius.circular(6),
          child: SizedBox(
            width: 72,
            height: 72,
            child: ProductImage(
              imageUrl: facility.resolvedImageUrl,
              backgroundColor: Colors.white,
            ),
          ),
        ),
        const SizedBox(width: 12),
        Expanded(
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                facility.name,
                style: const TextStyle(
                  color: bookingNavy,
                  fontWeight: FontWeight.w700,
                  fontSize: 15,
                ),
              ),
              const SizedBox(height: 4),
              const Text(
                FacilityItem.campusName,
                style: TextStyle(fontSize: 12, color: bookingMuted),
              ),
              if (facility.location.isNotEmpty)
                Text(
                  facility.location,
                  style: const TextStyle(fontSize: 12, color: bookingMuted),
                ),
            ],
          ),
        ),
      ],
    ),
  );
}

Future<void> messageFacilitiesAdmin(
  BuildContext context,
  String facilityId,
) async {
  try {
    final contact = await const FacilityBookingService().request(
      'facilities/contact/',
    );
    final chat = ChatService.instance;
    if (!await chat.initialize()) {
      throw const BookingException('Sign in to message Facilities Admin.');
    }
    final conversation = await chat.createConversation(
      participantActorKey: contact['actor_key'],
      participantDisplayName: contact['name'],
      contextKey: 'facility:$facilityId',
    );
    if (!context.mounted) return;
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ChatConversationScreen(conversation: conversation),
      ),
    );
  } catch (error) {
    if (context.mounted) {
      ScaffoldMessenger.of(
        context,
      ).showSnackBar(SnackBar(content: Text('$error')));
    }
  }
}
