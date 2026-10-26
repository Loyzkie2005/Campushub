import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import '../services/auth_service.dart';
import '../services/order_service.dart';
import '../services/theme_service.dart';
import '../session/session_service.dart';
import '../widgets/profile/profile_widgets.dart';
import 'components/account_recovery_dialog.dart';
import 'profile_setup_screen.dart';

class ProfileInformationPage extends StatelessWidget {
  const ProfileInformationPage({
    super.key,
    required this.title,
    required this.paragraphs,
  });
  final String title;
  final List<String> paragraphs;
  @override
  Widget build(BuildContext context) => ProfileDetailScaffold(
    title: title,
    child: ListView(
      padding: const EdgeInsets.all(20),
      children: [
        for (final text in paragraphs)
          Padding(
            padding: const EdgeInsets.only(bottom: 16),
            child: SelectableText(text, style: ProfileStyle.text(14)),
          ),
      ],
    ),
  );
}

class PersonalInformationPage extends StatefulWidget {
  const PersonalInformationPage({super.key, required this.user});
  final AuthUser user;
  @override
  State<PersonalInformationPage> createState() =>
      _PersonalInformationPageState();
}

class _PersonalInformationPageState extends State<PersonalInformationPage> {
  late AuthUser _user = widget.user;
  @override
  Widget build(BuildContext context) {
    final user = _user;
    final fields = <String, String>{
      'Full Name': user.fullName,
      'Username': user.studentId,
      if (user.profileStudentId.isNotEmpty) 'Student ID': user.profileStudentId,
      if (user.institutionalId.isNotEmpty)
        'Institutional ID': user.institutionalId,
      'Account Type': profileAccountType(user),
      if (user.userType == 'student') 'Year / Section': user.yearSection,
      if (user.program.isNotEmpty || user.userType == 'student')
        'Program': user.program.isEmpty ? 'Unassigned' : user.program,
      if (user.program.isNotEmpty && user.major.isNotEmpty) 'Major': user.major,
      'Email Address': user.email,
      'Contact Number': user.contactNumber,
    };
    return ProfileDetailScaffold(
      title: 'Personal Information',
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          for (final field in fields.entries)
            Padding(
              padding: const EdgeInsets.only(bottom: 20),
              child: Column(
                crossAxisAlignment: CrossAxisAlignment.start,
                children: [
                  Text(
                    field.key,
                    style: ProfileStyle.text(12, color: ProfileStyle.secondary),
                  ),
                  const SizedBox(height: 4),
                  SelectableText(
                    field.value.isEmpty ? 'Not provided' : field.value,
                    style: ProfileStyle.text(14, weight: 600),
                  ),
                ],
              ),
            ),
          Text(
            'Name and email are managed through your account. Profile editing updates your institutional information and contact number.',
            style: ProfileStyle.text(12, color: ProfileStyle.secondary),
          ),
          const SizedBox(height: 20),
          OutlinedButton.icon(
            onPressed: () async {
              final saved = await Navigator.of(context).push<AuthUser>(
                MaterialPageRoute(
                  builder: (_) => ProfileTheme(
                    child: ProfileSetupScreen(editingUser: user),
                  ),
                ),
              );
              if (saved != null && mounted) setState(() => _user = saved);
            },
            icon: const Icon(Icons.edit_outlined, size: 18),
            label: const Text('Edit Profile'),
          ),
        ],
      ),
    );
  }
}

class AccountSecurityPage extends StatefulWidget {
  const AccountSecurityPage({
    super.key,
    required this.user,
    this.embedded = false,
  });
  final AuthUser user;
  final bool embedded;
  @override
  State<AccountSecurityPage> createState() => _AccountSecurityPageState();
}

class _AccountSecurityPageState extends State<AccountSecurityPage> {
  late AuthUser _user = widget.user;
  Future<void> _recover({bool verify = false}) async {
    final token = verify ? await SessionService.loadChatToken() : null;
    if (!mounted) return;
    if (verify && (token == null || token.isEmpty)) {
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(content: Text('Sign in again to verify your email.')),
      );
      return;
    }
    await showDialog<bool>(
      context: context,
      builder: (_) => ProfileTheme(
        child: AccountRecoveryDialog(
          initialEmail: _user.email,
          verificationToken: token,
        ),
      ),
    );
    final saved = await SessionService.loadUser();
    if (mounted && saved != null) setState(() => _user = saved);
  }

  @override
  Widget build(BuildContext context) => ProfileDetailScaffold(
    title: 'Account & Security',
    embedded: widget.embedded,
    child: ListView(
      padding: const EdgeInsets.all(20),
      children: [
        Text(_user.email, style: ProfileStyle.text(14, weight: 600)),
        const SizedBox(height: 6),
        Text(
          _user.emailVerified ? 'Email verified' : 'Email not verified',
          style: ProfileStyle.text(13),
        ),
        ProfileSection(
          title: 'SECURITY',
          children: [
            ProfileNavRow(
              icon: Icons.lock_outline_rounded,
              title: 'Reset Password',
              subtitle: 'Verify your email before creating a new password',
              onTap: () => _recover(),
            ),
            if (!_user.emailVerified)
              ProfileNavRow(
                icon: Icons.mark_email_read_outlined,
                title: 'Verify Email Address',
                onTap: () => _recover(verify: true),
              ),
          ],
        ),
        const SizedBox(height: 20),
        Text(
          'If CampusHub says your login has expired, log out and sign in again.',
          style: ProfileStyle.text(13, color: ProfileStyle.secondary),
        ),
      ],
    ),
  );
}

class ProfileOrdersPage extends StatefulWidget {
  const ProfileOrdersPage({super.key});
  @override
  State<ProfileOrdersPage> createState() => _ProfileOrdersPageState();
}

class _ProfileOrdersPageState extends State<ProfileOrdersPage> {
  final _orders = OrderService.loadOrderHistory();
  @override
  Widget build(BuildContext context) => ProfileDetailScaffold(
    title: 'My Orders',
    child: FutureBuilder<List<Map<String, dynamic>>>(
      future: _orders,
      builder: (context, snapshot) {
        if (snapshot.connectionState != ConnectionState.done) {
          return const Center(child: CircularProgressIndicator());
        }
        if (snapshot.hasError) {
          return const Center(child: Text('Unable to load saved orders.'));
        }
        final orders = snapshot.data ?? [];
        return ListView(
          padding: const EdgeInsets.all(20),
          children: [
            Text(
              'Saved order history on this device',
              style: ProfileStyle.text(12, color: ProfileStyle.secondary),
            ),
            const SizedBox(height: 16),
            if (orders.isEmpty) const Text('No orders yet.'),
            for (final order in orders)
              Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Material(
                  color: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(14),
                    side: const BorderSide(color: ProfileStyle.border),
                  ),
                  child: Padding(
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          '${order['product_name'] ?? 'Product'}',
                          style: ProfileStyle.text(14, weight: 600),
                        ),
                        const SizedBox(height: 6),
                        Text(
                          '${_orderOption(order)} · Qty ${order['quantity'] ?? 1}',
                          style: ProfileStyle.text(
                            12,
                            color: ProfileStyle.secondary,
                          ),
                        ),
                        const SizedBox(height: 8),
                        Text(
                          '₱${(double.tryParse('${order['total_price']}') ?? 0).toStringAsFixed(2)}',
                          style: ProfileStyle.text(14, weight: 700),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
          ],
        );
      },
    ),
  );
}

String _orderOption(Map<String, dynamic> order) {
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

class ProfileAppSettingsPage extends StatelessWidget {
  const ProfileAppSettingsPage({super.key});
  @override
  Widget build(BuildContext context) => ProfileDetailScaffold(
    title: 'App Settings',
    child: AnimatedBuilder(
      animation: ThemeService.instance,
      builder: (_, _) => ListView(
        padding: const EdgeInsets.all(20),
        children: [
          SwitchListTile.adaptive(
            contentPadding: EdgeInsets.zero,
            title: Text(
              'Light theme',
              style: ProfileStyle.text(14, weight: 600),
            ),
            subtitle: Text(
              'Use the existing app theme preference',
              style: ProfileStyle.text(12, color: ProfileStyle.secondary),
            ),
            value: ThemeService.instance.isLightMode,
            onChanged: ThemeService.instance.setLightMode,
          ),
        ],
      ),
    ),
  );
}

class ProfileFaqPage extends StatelessWidget {
  const ProfileFaqPage({super.key});
  @override
  Widget build(BuildContext context) => ProfileDetailScaffold(
    title: 'Frequently Asked Questions',
    child: ListView(
      padding: const EdgeInsets.all(16),
      children: [
        for (final entry in const <String, String>{
          'How do I apply to sell?':
              'Open Shopping & Selling, choose Apply to Sell, and complete the application. Seller access starts after administrator approval.',
          'How do I pay for marketplace orders?':
              'CampusHub marketplace orders use cash on pickup.',
          'Where are facility bookings?':
              'Open Facilities in the bottom navigation to browse facilities and booking options.',
          'How do I request a service?':
              'Open Services and select a service to read its requirements and contact-office guidance.',
          'Why does my login token expire?':
              'For security, login tokens expire. Log out and sign in again when the app asks you to.',
        }.entries)
          ExpansionTile(
            title: Text(entry.key, style: ProfileStyle.text(14, weight: 600)),
            childrenPadding: const EdgeInsets.fromLTRB(16, 0, 16, 16),
            children: [
              Text(
                entry.value,
                style: ProfileStyle.text(13, color: ProfileStyle.secondary),
              ),
            ],
          ),
      ],
    ),
  );
}

class ProfileProblemPage extends StatefulWidget {
  const ProfileProblemPage({super.key});
  @override
  State<ProfileProblemPage> createState() => _ProfileProblemPageState();
}

class _ProfileProblemPageState extends State<ProfileProblemPage> {
  final _description = TextEditingController();
  final _form = GlobalKey<FormState>();
  String? _category;
  @override
  void dispose() {
    _description.dispose();
    super.dispose();
  }

  @override
  Widget build(BuildContext context) => ProfileDetailScaffold(
    title: 'Report a Problem',
    child: Form(
      key: _form,
      child: ListView(
        padding: const EdgeInsets.all(20),
        children: [
          Text(
            'Prepare a report to share with your campus support office. No report is sent from this screen.',
            style: ProfileStyle.text(13, color: ProfileStyle.secondary),
          ),
          const SizedBox(height: 24),
          DropdownButtonFormField<String>(
            isExpanded: true,
            decoration: const InputDecoration(
              labelText: 'Problem Category',
              hintText: 'Select a category',
            ),
            items: ['Account', 'Marketplace', 'Facilities', 'Services', 'Other']
                .map(
                  (label) => DropdownMenuItem(value: label, child: Text(label)),
                )
                .toList(),
            onChanged: (value) => _category = value,
            validator: (value) => value == null ? 'Select a category.' : null,
          ),
          const SizedBox(height: 20),
          TextFormField(
            controller: _description,
            minLines: 5,
            maxLines: 10,
            maxLength: 2000,
            decoration: const InputDecoration(
              labelText: 'Description',
              hintText: 'Describe what happened. Do not include your password.',
            ),
            validator: (value) => value == null || value.trim().isEmpty
                ? 'Describe the problem.'
                : null,
          ),
          const SizedBox(height: 24),
          OutlinedButton.icon(
            onPressed: () async {
              if (!_form.currentState!.validate()) return;
              await Clipboard.setData(
                ClipboardData(
                  text:
                      'CampusHub problem report\nCategory: $_category\n${_description.text.trim()}',
                ),
              );
              if (context.mounted) {
                ScaffoldMessenger.of(context).showSnackBar(
                  const SnackBar(
                    content: Text(
                      'Report copied. Share it through your official campus support channel.',
                    ),
                  ),
                );
              }
            },
            icon: const Icon(Icons.copy_outlined, size: 18),
            label: const Text('Copy Report'),
          ),
        ],
      ),
    ),
  );
}

class ProfileAboutPage extends StatelessWidget {
  const ProfileAboutPage({super.key});
  @override
  Widget build(BuildContext context) => ProfileDetailScaffold(
    title: 'About CampusHub',
    child: ListView(
      padding: const EdgeInsets.all(24),
      children: [
        Center(
          child: Image.asset(
            'assets/img/logo.png',
            width: 80,
            height: 80,
            semanticLabel: 'CampusHub logo',
          ),
        ),
        const SizedBox(height: 24),
        Text(
          'CampusHub',
          textAlign: TextAlign.center,
          style: ProfileStyle.text(22, weight: 700),
        ),
        const SizedBox(height: 16),
        Text(
          'A Campus Marketplace & Facilities Booking System with Real-Time Availability Monitoring and Analytics Dashboard',
          textAlign: TextAlign.center,
          style: ProfileStyle.text(14),
        ),
        const SizedBox(height: 20),
        Text(
          'University of Science and Technology of Southern Philippines – Oroquieta Campus',
          textAlign: TextAlign.center,
          style: ProfileStyle.text(13, color: ProfileStyle.secondary),
        ),
      ],
    ),
  );
}
