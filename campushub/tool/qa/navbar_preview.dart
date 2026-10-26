// Emulator-only QA of the production widget; no accounts, records or APIs.
import 'package:flutter/material.dart';
import 'package:campushub/module_app/widgets/navigation/floating_bottom_navbar.dart';

void main() => runApp(const NavbarPreview());

class NavbarPreview extends StatefulWidget {
  const NavbarPreview({super.key});
  @override
  State<NavbarPreview> createState() => _NavbarPreviewState();
}

class _NavbarPreviewState extends State<NavbarPreview> {
  int index = 0;
  bool dark = false;
  bool large = false;
  @override
  Widget build(BuildContext context) => MaterialApp(
    debugShowCheckedModeBanner: false,
    theme: ThemeData(
      brightness: dark ? Brightness.dark : Brightness.light,
      colorSchemeSeed: const Color(0xFF1A1851),
    ),
    builder: (context, child) => MediaQuery(
      data: MediaQuery.of(
        context,
      ).copyWith(textScaler: TextScaler.linear(large ? 2 : 1)),
      child: child!,
    ),
    home: Scaffold(
      appBar: AppBar(
        title: const Text('Navigation preview'),
        actions: [
          IconButton(
            tooltip: 'Toggle theme',
            onPressed: () => setState(() => dark = !dark),
            icon: const Icon(Icons.brightness_6),
          ),
          IconButton(
            tooltip: 'Larger text',
            onPressed: () => setState(() => large = !large),
            icon: const Icon(Icons.text_fields),
          ),
        ],
      ),
      body: Center(
        child: Text(
          FloatingBottomNavbar.default5Items[index].label,
          style: const TextStyle(fontSize: 24),
        ),
      ),
      bottomNavigationBar: FloatingBottomNavbar(
        currentIndex: index,
        onTap: (value) => setState(() => index = value),
      ),
    ),
  );
}
