/// Calendar helpers for facility scheduling (availability from API when connected).
enum FacilityDayStatus { available, partial, full, maintenance }

enum FacilitySlotStatus { available, reserved, maintenance }

class FacilityTimeSlot {
  const FacilityTimeSlot({
    required this.label,
    required this.status,
    this.note,
  });

  final String label;
  final FacilitySlotStatus status;
  final String? note;
}

class FacilityScheduleData {
  FacilityScheduleData._();

  static const _monthNames = [
    'January',
    'February',
    'March',
    'April',
    'May',
    'June',
    'July',
    'August',
    'September',
    'October',
    'November',
    'December',
  ];

  static const _weekdays = ['Sun', 'Mon', 'Tue', 'Wed', 'Thu', 'Fri', 'Sat'];

  static String formatMonthYear(DateTime month) {
    return '${_monthNames[month.month - 1]} ${month.year}';
  }

  static String formatSelectedDate(DateTime date) {
    final now = DateTime.now();
    final today = DateTime(now.year, now.month, now.day);
    final target = DateTime(date.year, date.month, date.day);
    final label =
        '${_weekdays[date.weekday % 7]}, ${_monthNames[date.month - 1]} ${date.day}, ${date.year}';
    if (target == today) return 'Today — $label';
    return label;
  }

  static bool isSameDay(DateTime a, DateTime b) {
    return a.year == b.year && a.month == b.month && a.day == b.day;
  }

  static bool isBeforeDay(DateTime date, DateTime reference) {
    final d = DateTime(date.year, date.month, date.day);
    final r = DateTime(reference.year, reference.month, reference.day);
    return d.isBefore(r);
  }

  static int daysInMonth(DateTime month) {
    return DateTime(month.year, month.month + 1, 0).day;
  }

  static int firstWeekdayOffset(DateTime month) {
    return DateTime(month.year, month.month, 1).weekday % 7;
  }

  static FacilityDayStatus dayStatus(
    DateTime date, {
    required String facilityAvailability,
  }) {
    if (isBeforeDay(date, DateTime.now())) {
      return FacilityDayStatus.full;
    }
    final status = facilityAvailability.toLowerCase();
    if (status == 'maintenance' || status == 'under maintenance') {
      return FacilityDayStatus.maintenance;
    }
    if (status == 'reserved' ||
        status == 'occupied' ||
        status == 'temporarily unavailable' ||
        status == 'inactive') {
      return FacilityDayStatus.full;
    }
    return FacilityDayStatus.available;
  }

  static List<FacilityTimeSlot> slotsForDay(
    DateTime date,
    List<String> slotLabels, {
    required String facilityAvailability,
  }) {
    if (slotLabels.isEmpty) return const [];

    if (isBeforeDay(date, DateTime.now())) {
      return slotLabels
          .map(
            (label) => FacilityTimeSlot(
              label: label,
              status: FacilitySlotStatus.reserved,
            ),
          )
          .toList();
    }

    final status = facilityAvailability.toLowerCase();
    if (status == 'maintenance' || status == 'under maintenance') {
      return slotLabels
          .map(
            (label) => FacilityTimeSlot(
              label: label,
              status: FacilitySlotStatus.maintenance,
            ),
          )
          .toList();
    }
    if (status == 'reserved' ||
        status == 'occupied' ||
        status == 'temporarily unavailable' ||
        status == 'inactive') {
      return slotLabels
          .map(
            (label) => FacilityTimeSlot(
              label: label,
              status: FacilitySlotStatus.reserved,
            ),
          )
          .toList();
    }

    return slotLabels
        .map(
          (label) => FacilityTimeSlot(
            label: label,
            status: FacilitySlotStatus.available,
          ),
        )
        .toList();
  }

  static int firstSelectableSlotIndex(List<FacilityTimeSlot> slots) {
    final i = slots.indexWhere((s) => s.status == FacilitySlotStatus.available);
    return i >= 0 ? i : 0;
  }
}
