// Emulator-only visual QA of the production drawer. No login, APIs or writes.
// This target is not imported by lib/main.dart; identity is an explicit fixture.
import 'package:campushub/module_app/services/auth_service.dart';
import 'package:campushub/module_app/services/theme_service.dart';
import 'package:campushub/module_app/widgets/navigation/seller_drawer.dart';
import 'package:campushub/module_app/widgets/profile/profile_widgets.dart';
import 'package:flutter/material.dart';

Future<void> main() async {
  WidgetsFlutterBinding.ensureInitialized();
  await ThemeService.instance.setLightMode(true);
  runApp(const SellerDrawerPreview());
}

class SellerDrawerPreview extends StatefulWidget {
  const SellerDrawerPreview({super.key});

  @override
  State<SellerDrawerPreview> createState() => _SellerDrawerPreviewState();
}

class _SellerDrawerPreviewState extends State<SellerDrawerPreview> {
  final scaffold = GlobalKey<ScaffoldState>();
  final user = AuthUser.fromJson({
    'id': -1,
    'username': 'drawer-preview-only',
    'full_name': 'Alexandra Marie Santos',
    'program': 'BTLED-ICT',
    'email': 'alexandra.santos@example.edu',
    'year_section': '3-A',
    'user_type': 'student',
    'role': 'User',
  });
  SellerDestination selected = SellerDestination.overview;
  bool returned = false;

  @override
  void initState() {
    super.initState();
    WidgetsBinding.instance.addPostFrameCallback((_) {
      scaffold.currentState?.openDrawer();
    });
  }

  @override
  Widget build(BuildContext context) => MaterialApp(
    debugShowCheckedModeBanner: false,
    theme: ThemeData(fontFamily: 'Poppins', brightness: Brightness.light),
    darkTheme: ThemeData(fontFamily: 'Poppins', brightness: Brightness.dark),
    home: Scaffold(
      key: scaffold,
      appBar: AppBar(
        title: const Text('Seller drawer QA'),
        actions: [
          IconButton(
            tooltip: 'Preview profile identity',
            icon: const Icon(Icons.person_outline),
            onPressed: () => Navigator.of(scaffold.currentContext!).push(
              MaterialPageRoute<void>(
                builder: (_) => ProfileTheme(
                  child: Scaffold(
                    appBar: AppBar(title: const Text('Profile typography QA')),
                    body: SingleChildScrollView(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        children: [
                          ProfileIdentityHeader(
                            user: user,
                            // Preview only: never open a picker or upload.
                            onChangePhoto: () {},
                          ),
                          ProfileSection(
                            title: 'ACCOUNT',
                            children: [
                              ProfileNavRow(
                                icon: Icons.person_outline,
                                title: 'Personal Information',
                                onTap: () {},
                              ),
                              ProfileNavRow(
                                icon: Icons.lock_outline,
                                title: 'Account & Security',
                                onTap: () {},
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
            ),
          ),
        ],
      ),
      drawer: SellerDrawer(
        user: user,
        selected: selected,
        onSelected: (value) => setState(() => selected = value),
        onBackToCampusHub: () {
          scaffold.currentState?.closeDrawer();
          setState(() => returned = true);
        },
      ),
      body: Center(
        child: Text(returned ? 'Home return callback' : selected.label),
      ),
    ),
  );
}
