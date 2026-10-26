import 'dart:async';

import 'package:flutter/foundation.dart';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:image_picker/image_picker.dart';
import 'package:shared_preferences/shared_preferences.dart';
import '../routes/app_routes.dart';
import '../services/auth_service.dart';
import '../services/chat_service.dart';
import '../services/profile_photo_service.dart';
import '../services/seller_application_service.dart';
import '../session/session_service.dart';
import '../widgets/profile/profile_widgets.dart';
import 'seller_application_page.dart';
import 'seller_application_form.dart';
import 'products_screen.dart';
import 'cart_screen.dart';
import 'messages_screen.dart';
import 'profile_details_pages.dart';

class ProfilePage extends StatefulWidget {
  const ProfilePage({
    super.key,
    this.onMarketplace,
    this.active = true,
    this.onMessages,
    this.onNotifications,
    this.onHome,
    this.onSellerAccessChanged,
  });
  final VoidCallback? onMarketplace, onMessages, onNotifications;
  final VoidCallback? onHome;
  final Future<void> Function()? onSellerAccessChanged;
  final bool active;
  @override
  State<ProfilePage> createState() => _ProfilePageState();
}

class _ProfilePageState extends State<ProfilePage> {
  AuthUser? _user;
  bool _loading = true;
  Map<String, dynamic>? _sellerState;
  String? _sellerError;
  bool _changingPhoto = false;
  int _profileVersion = 0;
  static const _pendingPhotoOwner = 'campushub_pending_profile_photo_owner';

  @override
  void initState() {
    super.initState();
    _load().then((_) => _recoverPhoto());
  }

  @override
  void didUpdateWidget(covariant ProfilePage oldWidget) {
    super.didUpdateWidget(oldWidget);
    if (widget.active && !oldWidget.active) _load();
  }

  Future<void> _load() async {
    _profileVersion++;
    final user = await SessionService.loadUser();
    if (!mounted) return;
    setState(() {
      _user = user;
      _loading = false;
    });
    if (user != null) {
      await Future.wait([
        _refreshProfile(user),
        if (user.userType != 'admin') _refreshSeller(),
      ]);
    }
  }

  Future<void> _refreshProfile(AuthUser cached) async {
    if (_changingPhoto) return;
    final version = _profileVersion;
    try {
      final token = await SessionService.loadChatToken();
      if (token == null || token.isEmpty) return;
      final user = await const ProfilePhotoService().load(token);
      if (!mounted || version != _profileVersion || user.id != cached.id) {
        return;
      }
      final current = await SessionService.loadUser();
      if (!mounted || current?.id != user.id || version != _profileVersion) {
        return;
      }
      await SessionService.updateUser(user);
      if (mounted) setState(() => _user = user);
    } catch (_) {
      // Keep the saved identity/photo available while the server is unreachable.
    }
  }

  Future<void> _refreshSeller() async {
    try {
      final state = await const SellerApplicationService().status();
      if (mounted) {
        final newlyApproved =
            _sellerState != null &&
            _sellerState!['is_approved_seller'] != true &&
            state['is_approved_seller'] == true;
        setState(() {
          _sellerState = state;
          _sellerError = null;
        });
        if (newlyApproved) await widget.onSellerAccessChanged?.call();
      }
    } on SellerApplicationException catch (e) {
      if (mounted) {
        setState(() {
          _sellerState = null;
          _sellerError = e.message;
        });
      }
    } catch (_) {
      if (mounted) {
        setState(() {
          _sellerState = null;
          _sellerError = 'Unable to load application status. Tap to retry.';
        });
      }
    }
  }

  Future<void> _openSeller() async {
    if (_sellerError != null || _sellerState == null) {
      await _refreshSeller();
      if (_sellerError != null || _sellerState == null) return;
    }
    if (!mounted || _user == null) return;
    final user = _user!;
    final status = _sellerState!['status'];
    final ownerRoute = ModalRoute.of(context);
    final navigator = Navigator.of(context);
    void showProfile() =>
        navigator.popUntil((route) => route == ownerRoute || route.isFirst);
    void showHome() {
      showProfile();
      widget.onHome?.call();
    }

    void showSellerHome() async {
      showProfile();
      await widget.onSellerAccessChanged?.call();
      if (mounted) widget.onHome?.call();
    }

    if (_sellerState!['is_approved_seller'] == true) {
      showSellerHome();
      return;
    }

    await Navigator.of(context).push(
      MaterialPageRoute<void>(
        settings: const RouteSettings(name: '/seller-access'),
        builder: (introContext) => status == 'none'
            ? SellerApplicationPage(
                onStart: () => Navigator.of(introContext).push(
                  MaterialPageRoute<void>(
                    builder: (_) => SellerApplicationForm(
                      user: user,
                      onMarketplace: widget.onMarketplace,
                      onBackToCampusHub: showHome,
                      onMessages: widget.onMessages,
                      onNotifications: widget.onNotifications,
                      onSellerApproved: showSellerHome,
                    ),
                  ),
                ),
              )
            : SellerApplicationForm(
                user: user,
                onMarketplace: widget.onMarketplace,
                onBackToCampusHub: showHome,
                onMessages: widget.onMessages,
                onNotifications: widget.onNotifications,
                onSellerApproved: showSellerHome,
              ),
      ),
    );
    if (mounted) await _refreshSeller();
  }

  Future<void> _open(Widget page) =>
      Navigator.of(context).push(MaterialPageRoute<void>(builder: (_) => page));

  void _photoMessage(String message) {
    if (!mounted) return;
    ScaffoldMessenger.of(
      context,
    ).showSnackBar(SnackBar(content: Text(message)));
  }

  Future<void> _savePhoto(XFile file, AuthUser owner) async {
    if (await file.length() > ProfilePhotoService.maxBytes) {
      throw const ProfilePhotoException('Choose a picture smaller than 5 MB.');
    }
    final token = await SessionService.loadChatToken();
    final current = await SessionService.loadUser();
    if (token == null || token.isEmpty || current?.id != owner.id) {
      throw const ProfilePhotoException(
        'Sign in again to change your profile picture.',
      );
    }
    final user = await const ProfilePhotoService().upload(
      token,
      await file.readAsBytes(),
    );
    final after = await SessionService.loadUser();
    if (after?.id != owner.id || user.id != owner.id) return;
    await SessionService.updateUser(user);
    if (mounted) setState(() => _user = user);
    _photoMessage('Profile picture updated.');
  }

  Future<void> _changePhoto() async {
    final owner = _user;
    if (_changingPhoto || owner == null) return;
    setState(() => _changingPhoto = true);
    _profileVersion++;
    try {
      final prefs = await SharedPreferences.getInstance();
      await prefs.setInt(_pendingPhotoOwner, owner.id);
      final file = await ImagePicker().pickImage(
        source: ImageSource.gallery,
        maxWidth: 1024,
        maxHeight: 1024,
        imageQuality: 85,
        requestFullMetadata: false,
      );
      await prefs.remove(_pendingPhotoOwner);
      if (file != null && mounted) await _savePhoto(file, owner);
    } on ProfilePhotoException catch (e) {
      _photoMessage(e.message);
    } on PlatformException {
      _photoMessage(
        'Unable to open your photos. Allow photo access in Settings and try again.',
      );
    } on TimeoutException {
      _photoMessage(
        'The upload timed out. Refresh your profile to check the picture before trying again.',
      );
    } catch (_) {
      _photoMessage(
        'Unable to update your profile picture. Check your connection and try again.',
      );
    } finally {
      final prefs = await SharedPreferences.getInstance();
      await prefs.remove(_pendingPhotoOwner);
      if (mounted) setState(() => _changingPhoto = false);
    }
  }

  Future<void> _recoverPhoto() async {
    if (kIsWeb ||
        defaultTargetPlatform != TargetPlatform.android ||
        !mounted ||
        _changingPhoto) {
      return;
    }
    final prefs = await SharedPreferences.getInstance();
    if (_changingPhoto) return;
    final ownerId = prefs.getInt(_pendingPhotoOwner);
    if (ownerId == null) return;
    final owner = _user;
    try {
      final lost = await ImagePicker().retrieveLostData();
      await prefs.remove(_pendingPhotoOwner);
      if (!mounted || owner == null || owner.id != ownerId) return;
      if (lost.exception != null) throw lost.exception!;
      if (lost.files?.isNotEmpty != true) return;
      setState(() => _changingPhoto = true);
      _profileVersion++;
      await _savePhoto(lost.files!.first, owner);
    } on ProfilePhotoException catch (e) {
      _photoMessage(e.message);
    } catch (_) {
      _photoMessage('Unable to restore the selected picture. Choose it again.');
    } finally {
      await prefs.remove(_pendingPhotoOwner);
      if (mounted) setState(() => _changingPhoto = false);
    }
  }

  Future<void> _confirmLogout() async {
    final confirm = await showDialog<bool>(
      context: context,
      builder: (ctx) => ProfileTheme(
        child: AlertDialog(
          shape: RoundedRectangleBorder(
            borderRadius: BorderRadius.circular(16),
          ),
          title: Text('Log Out', style: ProfileStyle.text(20, weight: 700)),
          content: const Text('Are you sure you want to log out?'),
          actions: [
            TextButton(
              onPressed: () => Navigator.pop(ctx, false),
              child: const Text('Cancel'),
            ),
            FilledButton(
              onPressed: () => Navigator.pop(ctx, true),
              style: FilledButton.styleFrom(
                backgroundColor: const Color(0xFFDC2626),
                foregroundColor: Colors.white,
              ),
              child: const Text('Log Out'),
            ),
          ],
        ),
      ),
    );
    if (confirm != true || !mounted) return;
    await ChatService.instance.disconnect();
    await SessionService.clearUser();
    if (!mounted) return;
    Navigator.of(
      context,
    ).pushNamedAndRemoveUntil(AppRoutes.login, (_) => false);
  }

  ProfileNavRow _row(
    IconData icon,
    String title,
    VoidCallback onTap, {
    String? subtitle,
  }) =>
      ProfileNavRow(icon: icon, title: title, subtitle: subtitle, onTap: onTap);

  @override
  Widget build(BuildContext context) {
    if (_loading) return const Center(child: CircularProgressIndicator());
    final user = _user;
    if (user == null) {
      return ProfileTheme(
        child: Center(
          child: Column(
            mainAxisSize: MainAxisSize.min,
            children: [
              const Text('Sign in to view your profile.'),
              TextButton(
                onPressed: () => Navigator.of(
                  context,
                ).pushNamedAndRemoveUntil(AppRoutes.login, (_) => false),
                child: const Text('Sign In'),
              ),
            ],
          ),
        ),
      );
    }
    final approved = _sellerState?['is_approved_seller'] == true;
    final noApplication = _sellerState?['status'] == 'none';
    final sellerSubtitle =
        _sellerError ??
        (_sellerState == null
            ? 'Checking application status…'
            : approved
            ? 'Manage products and sales'
            : noApplication
            ? 'Sell products on CampusHub'
            : switch (_sellerState!['status']) {
                'pending' => 'Pending Review',
                'needs_revision' => 'Needs Revision',
                'rejected' => 'Rejected',
                'suspended' => 'Suspended',
                _ => 'Status unavailable',
              });
    return ProfileTheme(
      child: ColoredBox(
        color: ProfileStyle.background,
        child: SafeArea(
          top: false,
          child: RefreshIndicator(
            onRefresh: _load,
            color: ProfileStyle.navy,
            child: SingleChildScrollView(
              physics: const AlwaysScrollableScrollPhysics(),
              padding: const EdgeInsets.fromLTRB(16, 16, 16, 32),
              child: Center(
                child: ConstrainedBox(
                  constraints: const BoxConstraints(maxWidth: 640),
                  child: Column(
                    crossAxisAlignment: CrossAxisAlignment.stretch,
                    children: [
                      ProfileIdentityHeader(
                        user: user,
                        onChangePhoto: _changePhoto,
                        changingPhoto: _changingPhoto,
                      ),
                      ProfileSection(
                        title: 'ACCOUNT',
                        children: [
                          _row(
                            Icons.person_outline_rounded,
                            'Personal Information',
                            () async {
                              _profileVersion++;
                              await _open(PersonalInformationPage(user: user));
                              if (mounted) await _load();
                            },
                            subtitle: 'Profile and contact information',
                          ),
                          _row(
                            Icons.lock_outline_rounded,
                            'Account & Security',
                            () async {
                              await _open(AccountSecurityPage(user: user));
                              if (mounted) await _load();
                            },
                            subtitle: 'Password and email verification',
                          ),
                        ],
                      ),
                      ProfileSection(
                        title: 'SHOPPING & SELLING',
                        children: [
                          _row(
                            Icons.receipt_long_outlined,
                            'My Orders',
                            () => _open(const ProfileOrdersPage()),
                          ),
                          _row(
                            Icons.favorite_border_rounded,
                            'Favorites',
                            () => _open(
                              const ProductsScreen(favoritesOnly: true),
                            ),
                          ),
                          _row(
                            Icons.shopping_cart_outlined,
                            'My Cart',
                            () => _open(const CartScreen()),
                          ),
                          if (user.userType != 'admin' && !approved)
                            ProfileNavRow(
                              key: const ValueKey('profile-apply-to-sell'),
                              icon: Icons.storefront_outlined,
                              title: 'Apply to Sell',
                              subtitle: sellerSubtitle,
                              onTap: _openSeller,
                            ),
                        ],
                      ),
                      ProfileSection(
                        title: 'COMMUNICATION',
                        children: [
                          AnimatedBuilder(
                            animation: ChatService.instance,
                            builder: (_, _) => ProfileNavRow(
                              icon: Icons.chat_bubble_outline_rounded,
                              title: 'Messages',
                              count: ChatService.instance.conversations.fold(
                                0,
                                (sum, item) => sum + item.unreadCount,
                              ),
                              onTap:
                                  widget.onMessages ??
                                  () => _open(
                                    const ProfileDetailScaffold(
                                      title: 'Messages',
                                      child: MessagesPage(),
                                    ),
                                  ),
                            ),
                          ),
                          _row(
                            Icons.notifications_none_rounded,
                            'Notifications',
                            widget.onNotifications ??
                                () => _open(
                                  const ProfileInformationPage(
                                    title: 'Notifications',
                                    paragraphs: [
                                      'Mobile notifications are not available yet.',
                                    ],
                                  ),
                                ),
                          ),
                        ],
                      ),
                      ProfileSection(
                        title: 'SETTINGS & PRIVACY',
                        children: [
                          _row(
                            Icons.settings_outlined,
                            'App Settings',
                            () => _open(const ProfileAppSettingsPage()),
                          ),
                          _row(
                            Icons.privacy_tip_outlined,
                            'Privacy & Data',
                            () => _open(
                              const ProfileInformationPage(
                                title: 'Privacy & Data',
                                paragraphs: [
                                  'The official privacy notice is not available in the mobile app yet.',
                                  'Request the current policy from the campus office.',
                                ],
                              ),
                            ),
                          ),
                          _row(
                            Icons.description_outlined,
                            'Terms & Conditions',
                            () => _open(
                              const ProfileInformationPage(
                                title: 'Terms & Conditions',
                                paragraphs: [
                                  'The official Terms and Conditions are not available in the mobile app yet.',
                                  'Request the current terms from the campus office.',
                                ],
                              ),
                            ),
                          ),
                        ],
                      ),
                      ProfileSection(
                        title: 'HELP & SUPPORT',
                        children: [
                          _row(
                            Icons.help_outline_rounded,
                            'Frequently Asked Questions',
                            () => _open(const ProfileFaqPage()),
                          ),
                          _row(
                            Icons.support_agent_outlined,
                            'Contact Support',
                            () => _open(
                              const ProfileInformationPage(
                                title: 'Contact Support',
                                paragraphs: [
                                  'Contact the USTP Oroquieta campus office responsible for your concern.',
                                  'Verified support contact details have not been configured in the mobile app.',
                                ],
                              ),
                            ),
                          ),
                          _row(
                            Icons.report_problem_outlined,
                            'Report a Problem',
                            () => _open(const ProfileProblemPage()),
                          ),
                          _row(
                            Icons.info_outline_rounded,
                            'About CampusHub',
                            () => _open(const ProfileAboutPage()),
                          ),
                        ],
                      ),
                      const SizedBox(height: 24),
                      OutlinedButton.icon(
                        onPressed: _confirmLogout,
                        icon: const Icon(Icons.logout_rounded, size: 20),
                        label: const Text('Log Out'),
                        style: OutlinedButton.styleFrom(
                          foregroundColor: const Color(0xFFDC2626),
                          minimumSize: const Size(double.infinity, 52),
                          side: const BorderSide(color: ProfileStyle.border),
                        ),
                      ),
                    ],
                  ),
                ),
              ),
            ),
          ),
        ),
      ),
    );
  }
}
