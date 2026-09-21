import 'package:flutter/material.dart';
import '../routes/app_routes.dart';
import '../services/order_service.dart';
import '../services/auth_service.dart';
import '../services/chat_service.dart';
import '../session/session_service.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({super.key});

  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  static const Color primaryNavy = Color(0xFF142B47);
  static const Color primaryBlue = Color(0xFF1A56DB);

  AuthUser? _user;
  List<Map<String, dynamic>> _orders = const [];
  bool _loading = true;

  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    final user = await SessionService.loadUser();
    final orders = await OrderService.loadOrderHistory();
    if (!mounted) return;
    setState(() {
      _user = user;
      _orders = orders;
      _loading = false;
    });
  }

  Future<void> _confirmLogout() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => AlertDialog(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(16)),
        title: const Text(
          'Log Out',
          style: TextStyle(color: primaryNavy, fontWeight: FontWeight.w700),
        ),
        content: const Text('Are you sure you want to log out?'),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(ctx, false),
            child: const Text('Cancel'),
          ),
          ElevatedButton(
            onPressed: () => Navigator.pop(ctx, true),
            style: ElevatedButton.styleFrom(
              backgroundColor: Colors.redAccent,
              foregroundColor: Colors.white,
            ),
            child: const Text('Log Out'),
          ),
        ],
      ),
    );

    if (confirm != true) return;
    if (!mounted) return;

    await ChatService.instance.disconnect();
    await SessionService.clearUser();
    if (!mounted) return;

    Navigator.of(
      context,
    ).pushNamedAndRemoveUntil(AppRoutes.login, (_) => false);
  }

  @override
  Widget build(BuildContext context) {
    if (_loading) {
      return const Center(child: CircularProgressIndicator());
    }

    final user = _user;
    final accountType = switch (user?.userType) {
      'student' => 'Student',
      'faculty' => 'Faculty',
      'guest' => 'Guest / Visitor',
      _ => user?.role.isNotEmpty == true ? user!.role : 'Not set',
    };
    final institutionalIdLabel = user?.userType == 'faculty'
        ? 'Faculty ID'
        : 'Student ID';
    final initials = user == null
        ? '?'
        : ((user.firstName.isNotEmpty ? user.firstName[0] : '') +
                  (user.lastName.isNotEmpty ? user.lastName[0] : ''))
              .toUpperCase();

    return SafeArea(
      child: SingleChildScrollView(
        padding: const EdgeInsets.fromLTRB(20, 24, 20, 24),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: [
            // Avatar + name
            Center(
              child: Column(
                children: [
                  CircleAvatar(
                    radius: 48,
                    backgroundColor: primaryNavy,
                    child: Text(
                      initials.isEmpty ? '?' : initials,
                      style: const TextStyle(
                        fontSize: 32,
                        fontWeight: FontWeight.w800,
                        color: Colors.white,
                      ),
                    ),
                  ),
                  const SizedBox(height: 14),
                  Text(
                    user?.fullName.trim().isNotEmpty == true
                        ? user!.fullName
                        : (user?.studentId ?? 'Guest'),
                    style: const TextStyle(
                      fontSize: 20,
                      fontWeight: FontWeight.w700,
                      color: primaryNavy,
                    ),
                  ),
                  if (user?.role != null && user!.role.isNotEmpty)
                    Container(
                      margin: const EdgeInsets.only(top: 6),
                      padding: const EdgeInsets.symmetric(
                        horizontal: 12,
                        vertical: 4,
                      ),
                      decoration: BoxDecoration(
                        color: primaryBlue.withValues(alpha: 0.1),
                        borderRadius: BorderRadius.circular(20),
                      ),
                      child: Text(
                        user.role,
                        style: const TextStyle(
                          color: primaryBlue,
                          fontWeight: FontWeight.w600,
                        ),
                      ),
                    ),
                ],
              ),
            ),
            const SizedBox(height: 28),

            // Account info card
            Container(
              decoration: BoxDecoration(
                color: Colors.white,
                borderRadius: BorderRadius.circular(14),
                border: Border.all(color: Colors.black12),
              ),
              child: Column(
                children: [
                  _InfoRow(
                    icon: Icons.alternate_email,
                    label: 'Username',
                    value: user?.studentId ?? '-',
                  ),
                  const Divider(height: 1),
                  _InfoRow(
                    icon: Icons.person_outline,
                    label: 'Account Type',
                    value: accountType,
                  ),
                  if (user?.profileStudentId.isNotEmpty == true) ...[
                    const Divider(height: 1),
                    _InfoRow(
                      icon: Icons.badge_outlined,
                      label: 'Student ID',
                      value: user!.profileStudentId,
                    ),
                  ],
                  if (user?.institutionalId.isNotEmpty == true) ...[
                    const Divider(height: 1),
                    _InfoRow(
                      icon: Icons.badge_outlined,
                      label: institutionalIdLabel,
                      value: user!.institutionalId,
                    ),
                  ],
                  if (user?.contactNumber.isNotEmpty == true) ...[
                    const Divider(height: 1),
                    _InfoRow(
                      icon: Icons.phone_outlined,
                      label: 'Contact Number',
                      value: user!.contactNumber,
                    ),
                  ],
                  const Divider(height: 1),
                  _InfoRow(
                    icon: Icons.email_outlined,
                    label: 'Email',
                    value: user?.email ?? '-',
                  ),
                  const Divider(height: 1),
                  _InfoRow(
                    icon: Icons.badge_outlined,
                    label: 'Full Name',
                    value: user?.fullName ?? '-',
                  ),
                ],
              ),
            ),
            const SizedBox(height: 28),

            const Text(
              'Order History',
              style: TextStyle(
                color: primaryNavy,
                fontSize: 18,
                fontWeight: FontWeight.w800,
              ),
            ),
            const SizedBox(height: 10),
            if (_orders.isEmpty)
              Container(
                padding: const EdgeInsets.all(16),
                decoration: BoxDecoration(
                  color: Colors.white,
                  borderRadius: BorderRadius.circular(14),
                  border: Border.all(color: Colors.black12),
                ),
                child: const Text(
                  'No orders yet.',
                  style: TextStyle(color: Colors.black54),
                ),
              )
            else
              ..._orders
                  .take(8)
                  .map((order) => _OrderHistoryCard(order: order)),
            const SizedBox(height: 28),

            // Logout button
            SizedBox(
              height: 52,
              child: ElevatedButton.icon(
                onPressed: _confirmLogout,
                icon: const Icon(Icons.logout, color: Colors.white),
                label: const Text(
                  'Log Out',
                  style: TextStyle(
                    color: Colors.white,
                    fontWeight: FontWeight.w700,
                    fontSize: 16,
                  ),
                ),
                style: ElevatedButton.styleFrom(
                  backgroundColor: Colors.redAccent,
                  elevation: 0,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                  ),
                ),
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _InfoRow extends StatelessWidget {
  const _InfoRow({
    required this.icon,
    required this.label,
    required this.value,
  });

  final IconData icon;
  final String label;
  final String value;

  @override
  Widget build(BuildContext context) {
    return Padding(
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
      child: Row(
        children: [
          Icon(icon, color: const Color(0xFF1A56DB), size: 22),
          const SizedBox(width: 14),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  label,
                  style: const TextStyle(fontSize: 12, color: Colors.black54),
                ),
                const SizedBox(height: 2),
                Text(
                  value,
                  style: const TextStyle(
                    fontSize: 15,
                    fontWeight: FontWeight.w600,
                    color: Color(0xFF142B47),
                  ),
                ),
              ],
            ),
          ),
        ],
      ),
    );
  }
}

String _orderSubtitle(Map<String, dynamic> order) {
  final option = (order['option'] as String?)?.trim();
  if (option != null && option.isNotEmpty) return option;

  final customization = order['customization'];
  if (customization is Map) {
    final summary = (customization['summary'] as String?)?.trim();
    if (summary != null && summary.isNotEmpty) return summary;
    final selections = customization['selections'];
    if (selections is List && selections.isNotEmpty) {
      return selections
          .whereType<Map>()
          .map((item) => '${item['option'] ?? ''}')
          .where((value) => value.isNotEmpty)
          .join(', ');
    }
  }
  return 'Order';
}

class _OrderHistoryCard extends StatelessWidget {
  const _OrderHistoryCard({required this.order});

  final Map<String, dynamic> order;

  @override
  Widget build(BuildContext context) {
    final quantity = order['quantity'] ?? 1;
    final total = double.tryParse('${order['total_price'] ?? 0}') ?? 0;
    return Container(
      margin: const EdgeInsets.only(bottom: 10),
      padding: const EdgeInsets.all(14),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(14),
        border: Border.all(color: Colors.black12),
      ),
      child: Row(
        children: [
          const Icon(Icons.receipt_long_outlined, color: Color(0xFF1A56DB)),
          const SizedBox(width: 12),
          Expanded(
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  '${order['product_name'] ?? 'Product'}',
                  maxLines: 1,
                  overflow: TextOverflow.ellipsis,
                  style: const TextStyle(
                    color: Color(0xFF142B47),
                    fontWeight: FontWeight.w800,
                  ),
                ),
                const SizedBox(height: 3),
                Text(
                  '${_orderSubtitle(order)} • Qty $quantity',
                  style: const TextStyle(color: Colors.black54, fontSize: 12),
                ),
              ],
            ),
          ),
          Text(
            '₱${total.toStringAsFixed(2)}',
            style: const TextStyle(
              color: Color(0xFF1A56DB),
              fontWeight: FontWeight.w800,
            ),
          ),
        ],
      ),
    );
  }
}
