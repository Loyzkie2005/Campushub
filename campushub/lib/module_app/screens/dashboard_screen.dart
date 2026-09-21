import 'dart:async';
import 'dart:convert';
import 'package:flutter/material.dart';
import 'package:flutter/services.dart';
import 'package:http/http.dart' as http;
import 'package:lucide_icons/lucide_icons.dart';
import '../services/cart_service.dart';
import 'facility_screen.dart';
import 'messages_screen.dart';
import 'profile_page.dart';
import '../config/api_config.dart';
import '../models/product_item.dart';
import '../services/facility_service.dart';
import '../services/favorite_service.dart';
import '../services/product_service.dart';
import '../session/session_service.dart';
import '../widgets/product_image.dart';
import '../widgets/navigation/floating_bottom_navbar.dart';
import 'product_details_screen.dart';
import 'products_screen.dart';
import 'cart_screen.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({super.key});

  static const Color primaryNavy = Color(0xFF142B47);
  static const Color primaryBlue = Color(0xFF1A56DB);
  static const Color webBrandBlue = Color(0xFF0175C2);
  static const Color campusGold = Color(0xFFFCB316);
  static const Color pageBackground = Color(0xFFF8FAFD);
  static const Color borderBlue = Color(0xFFBFD7FF);
  static String get apiBaseUrl => ApiConfig.baseUrl;
  static List<String> get apiBaseUrls => ApiConfig.serverBaseUrls;

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen> {
  static const Color pageBackground = DashboardScreen.pageBackground;

  final PageController _pageController = PageController();
  final TextEditingController _searchController = TextEditingController();
  final FocusNode _searchFocusNode = FocusNode();
  int _currentIndex = 0;
  bool _isSearchOpen = false;
  String _firstName = '';

  @override
  void initState() {
    super.initState();
    _loadUserName();
  }

  Future<void> _loadUserName() async {
    final user = await SessionService.loadUser();
    if (!mounted) return;
    setState(() {
      _firstName = user?.firstName ?? '';
    });
  }

  @override
  void dispose() {
    _pageController.dispose();
    _searchController.dispose();
    _searchFocusNode.dispose();
    super.dispose();
  }

  void _goToTab(int index) {
    if (_isSearchOpen) {
      _closeSearch();
    }
    if (index == _currentIndex) return;
    FocusManager.instance.primaryFocus?.unfocus();
    setState(() => _currentIndex = index);
    _pageController.animateToPage(
      index,
      duration: const Duration(milliseconds: 260),
      curve: Curves.easeOutCubic,
    );
  }

  void _openSearch() {
    setState(() => _isSearchOpen = true);
    WidgetsBinding.instance.addPostFrameCallback((_) {
      if (mounted) {
        _searchFocusNode.requestFocus();
      }
    });
  }

  void _closeSearch() {
    FocusManager.instance.primaryFocus?.unfocus();
    _searchFocusNode.unfocus();
    setState(() {
      _isSearchOpen = false;
      _searchController.clear();
    });
  }

  void _handleSearchSubmit(String query) {
    final trimmed = query.trim();
    if (trimmed.isEmpty) return;
    _closeSearch();
    _goToTab(1);
  }

  Future<void> _refreshHome() async {
    await _loadUserName();
    setState(() {});
    await Future<void>.delayed(const Duration(milliseconds: 450));
  }

  Future<void> _openAddProductForm() async {
    final created = await ProductsScreen.showAddProductSheet(context);
    if (created == true && mounted) {
      _refreshHome();
    }
  }

  void _openMessages() {
    Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => Scaffold(
          backgroundColor: Colors.white,
          appBar: AppBar(
            backgroundColor: Colors.white,
            foregroundColor: const Color(0xFF1A1851),
            elevation: 0,
            leading: IconButton(
              icon: const Icon(LucideIcons.arrowLeft),
              tooltip: 'Back',
              onPressed: () => Navigator.of(context).pop(),
            ),
            title: const Text(
              'Messages',
              style: TextStyle(
                color: Color(0xFF1A1851),
                fontSize: 18,
                fontWeight: FontWeight.w700,
              ),
            ),
          ),
          body: const MessagesPage(),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) {
    const appBarForeground = Color(0xFF1A1851);
    final pageTitle = switch (_currentIndex) {
      1 => 'Shop',
      2 => 'Facilities',
      3 => 'Profile',
      _ => _firstName.isNotEmpty ? 'Welcome Back, $_firstName' : 'Welcome Back',
    };
    return Scaffold(
      backgroundColor: pageBackground,
      drawer: _DashboardDrawer(
        currentIndex: _currentIndex,
        onSelectTab: _goToTab,
        onOpenMessages: _openMessages,
      ),
      appBar: AppBar(
        automaticallyImplyLeading: false,
        backgroundColor: pageBackground,
        foregroundColor: appBarForeground,
        surfaceTintColor: Colors.transparent,
        scrolledUnderElevation: 0,
        systemOverlayStyle: SystemUiOverlayStyle.dark.copyWith(
          statusBarColor: Colors.white,
          systemNavigationBarColor: Colors.white,
          systemNavigationBarIconBrightness: Brightness.dark,
        ),
        elevation: 0,
        toolbarHeight: 56,
        leading: _isSearchOpen
            ? IconButton(
                onPressed: _closeSearch,
                icon: const Icon(
                  LucideIcons.arrowLeft,
                  color: appBarForeground,
                ),
                tooltip: 'Back',
              )
            : Builder(
                builder: (context) => IconButton(
                  onPressed: () => Scaffold.of(context).openDrawer(),
                  icon: const Icon(LucideIcons.menu, color: appBarForeground),
                  tooltip: 'Menu',
                ),
              ),
        titleSpacing: 0,
        title: _isSearchOpen
            ? Container(
                height: 42,
                margin: const EdgeInsets.only(right: 16),
                decoration: BoxDecoration(
                  color: const Color(0xFFF1F5F9),
                  borderRadius: BorderRadius.circular(12),
                  border: Border.all(color: const Color(0xFFE2E8F0)),
                ),
                padding: const EdgeInsets.symmetric(horizontal: 12),
                child: Row(
                  children: [
                    const Icon(
                      LucideIcons.search,
                      size: 20,
                      color: Color(0xFF94A3B8),
                    ),
                    const SizedBox(width: 8),
                    Expanded(
                      child: TextField(
                        controller: _searchController,
                        focusNode: _searchFocusNode,
                        autofocus: true,
                        textInputAction: TextInputAction.search,
                        style: const TextStyle(
                          fontSize: 14,
                          color: Color(0xFF1A1851),
                          fontWeight: FontWeight.w500,
                        ),
                        decoration: const InputDecoration(
                          hintText: 'Search products, facilities...',
                          hintStyle: TextStyle(
                            color: Color(0xFF94A3B8),
                            fontSize: 14,
                            fontWeight: FontWeight.w400,
                          ),
                          border: InputBorder.none,
                          isDense: true,
                          contentPadding: EdgeInsets.symmetric(vertical: 10),
                        ),
                        onSubmitted: _handleSearchSubmit,
                      ),
                    ),
                    ValueListenableBuilder<TextEditingValue>(
                      valueListenable: _searchController,
                      builder: (context, value, _) {
                        if (value.text.isEmpty) return const SizedBox.shrink();
                        return GestureDetector(
                          onTap: () => _searchController.clear(),
                          child: const Padding(
                            padding: EdgeInsets.symmetric(horizontal: 4),
                            child: Icon(
                              LucideIcons.x,
                              size: 18,
                              color: Color(0xFF94A3B8),
                            ),
                          ),
                        );
                      },
                    ),
                  ],
                ),
              )
            : Text(
                pageTitle,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: appBarForeground,
                  fontSize: 18,
                  fontWeight: FontWeight.w800,
                  letterSpacing: -0.2,
                ),
              ),
        actions: _isSearchOpen
            ? null
            : [
                IconButton(
                  onPressed: _openSearch,
                  icon: const Icon(LucideIcons.search, color: appBarForeground),
                  tooltip: 'Search',
                  visualDensity: VisualDensity.compact,
                ),
                IconButton(
                  onPressed: () {},
                  icon: const Icon(LucideIcons.bell, color: appBarForeground),
                  tooltip: 'Notifications',
                  visualDensity: VisualDensity.compact,
                ),
                const SizedBox(width: 4),
              ],
      ),
      body: PopScope(
        canPop: !_isSearchOpen,
        onPopInvokedWithResult: (didPop, result) {
          if (didPop) return;
          if (_isSearchOpen) {
            _closeSearch();
          }
        },
        child: SafeArea(
          top: false,
          child: PageView(
            controller: _pageController,
            onPageChanged: (index) {
              FocusManager.instance.primaryFocus?.unfocus();
              setState(() => _currentIndex = index);
            },
            children: [
              _HomePage(
                onProductsTap: () => _goToTab(1),
                onFacilitiesTap: () => _goToTab(2),
                onRefresh: _refreshHome,
              ),
              const _MarketplacePage(),
              const FacilitiesPage(),
              const ProfilePage(),
            ],
          ),
        ),
      ),
      bottomNavigationBar: FloatingBottomNavbar(
        currentIndex: _currentIndex,
        onTap: _goToTab,
        onCenterActionTap: _openAddProductForm,
      ),
    );
  }
}

class _HomePage extends StatefulWidget {
  const _HomePage({
    required this.onProductsTap,
    required this.onFacilitiesTap,
    required this.onRefresh,
  });

  final VoidCallback onProductsTap;
  final VoidCallback onFacilitiesTap;
  final Future<void> Function() onRefresh;

  @override
  State<_HomePage> createState() => _HomePageState();
}

class _HomePageState extends State<_HomePage> {
  bool _isLoadingProducts = true;
  bool _isLoadingFacilities = true;
  List<ProductItem> _products = const [];
  List<_DashboardFacilityItem> _facilities = const [];

  @override
  void initState() {
    super.initState();
    _fetchProducts();
    _fetchFacilities();
  }

  Future<void> _refresh() async {
    await Future.wait([
      widget.onRefresh(),
      _fetchProducts(),
      _fetchFacilities(),
    ]);
  }

  Future<void> _fetchProducts() async {
    if (mounted) setState(() => _isLoadingProducts = true);

    for (final baseUrl in DashboardScreen.apiBaseUrls) {
      try {
        final response = await http
            .get(
              Uri.parse('$baseUrl/api/products/approved/'),
              headers: const {'Accept': 'application/json'},
            )
            .timeout(const Duration(seconds: 5));

        if (response.statusCode < 200 || response.statusCode >= 300) {
          continue;
        }

        final decoded = jsonDecode(response.body) as Map<String, dynamic>;
        final rows = decoded['products'] as List<dynamic>? ?? const [];
        final products = rows
            .whereType<Map>()
            .map(
              (row) => ProductItem.fromJson(
                row.map((key, value) => MapEntry(key.toString(), value)),
              ),
            )
            .take(4)
            .toList(growable: false);

        if (!mounted) return;
        ApiConfig.recordWorkingBaseUrl(baseUrl);
        setState(() {
          _products = products;
          _isLoadingProducts = false;
        });
        return;
      } catch (_) {}
    }

    if (!mounted) return;
    setState(() => _isLoadingProducts = false);
  }

  Future<void> _fetchFacilities() async {
    if (mounted) setState(() => _isLoadingFacilities = true);

    final result = await FacilityService.fetchFacilities();
    if (!mounted) return;

    setState(() {
      _facilities = result.success
          ? result.facilities
                .map(_DashboardFacilityItem.fromJson)
                .take(4)
                .toList(growable: false)
          : const [];
      _isLoadingFacilities = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    return RefreshIndicator(
      onRefresh: _refresh,
      child: ListView(
        cacheExtent: 700,
        padding: const EdgeInsets.fromLTRB(16, 14, 16, 24),
        children: [
          _HeroCarousel(
            onExploreTap: widget.onProductsTap,
            onBookTap: widget.onFacilitiesTap,
            onBrowseTap: widget.onProductsTap,
          ),
          const SizedBox(height: 20),
          _SectionHeader(title: 'Products', onViewAll: widget.onProductsTap),
          const SizedBox(height: 12),
          _DashboardProductsPreview(
            products: _products,
            isLoading: _isLoadingProducts,
            onViewAll: widget.onProductsTap,
          ),
          const SizedBox(height: 22),
          _SectionHeader(
            title: 'Facilities',
            onViewAll: widget.onFacilitiesTap,
          ),
          const SizedBox(height: 12),
          _DashboardFacilitiesPreview(
            facilities: _facilities,
            isLoading: _isLoadingFacilities,
            onViewAll: widget.onFacilitiesTap,
          ),
        ],
      ),
    );
  }
}

class _DashboardProductsPreview extends StatelessWidget {
  const _DashboardProductsPreview({
    required this.products,
    required this.isLoading,
    required this.onViewAll,
  });

  final List<ProductItem> products;
  final bool isLoading;
  final VoidCallback onViewAll;

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return const SizedBox(
        height: 194,
        child: Center(child: CircularProgressIndicator()),
      );
    }

    if (products.isEmpty) {
      return const SizedBox.shrink();
    }

    return SizedBox(
      height: 245,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        itemCount: products.length,
        separatorBuilder: (context, index) => const SizedBox(width: 14),
        itemBuilder: (context, index) {
          return SizedBox(
            width: 165,
            child: _LargeProductCard(product: products[index]),
          );
        },
      ),
    );
  }
}

class _DashboardFacilitiesPreview extends StatelessWidget {
  const _DashboardFacilitiesPreview({
    required this.facilities,
    required this.isLoading,
    required this.onViewAll,
  });

  final List<_DashboardFacilityItem> facilities;
  final bool isLoading;
  final VoidCallback onViewAll;

  @override
  Widget build(BuildContext context) {
    if (isLoading) {
      return const SizedBox(
        height: 178,
        child: Center(child: CircularProgressIndicator()),
      );
    }

    if (facilities.isEmpty) {
      return Container(
        height: 118,
        padding: const EdgeInsets.all(16),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: DashboardScreen.borderBlue),
        ),
        child: Row(
          children: [
            const Icon(
              Icons.assignment_outlined,
              color: DashboardScreen.primaryBlue,
              size: 32,
            ),
            const SizedBox(width: 12),
            const Expanded(
              child: Text(
                'Available facilities will appear here.',
                style: TextStyle(
                  color: Colors.black54,
                  fontSize: 13,
                  fontWeight: FontWeight.w700,
                ),
              ),
            ),
            TextButton(onPressed: onViewAll, child: const Text('See All')),
          ],
        ),
      );
    }

    return Column(
      children: facilities
          .take(2)
          .map((facility) {
            return Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: _DashboardFacilityCard(
                facility: facility,
                onTap: onViewAll,
              ),
            );
          })
          .toList(growable: false),
    );
  }
}

class _DashboardFacilityCard extends StatelessWidget {
  const _DashboardFacilityCard({required this.facility, required this.onTap});

  final _DashboardFacilityItem facility;
  final VoidCallback onTap;

  Color get _statusColor {
    switch (facility.status) {
      case 'Available':
        return const Color(0xFF10B981);
      case 'Reserved':
        return const Color(0xFF2563EB);
      case 'Maintenance':
        return const Color(0xFFDC2626);
      default:
        return DashboardScreen.primaryNavy;
    }
  }

  @override
  Widget build(BuildContext context) {
    return InkWell(
      onTap: onTap,
      borderRadius: BorderRadius.circular(8),
      child: Container(
        padding: const EdgeInsets.all(10),
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(8),
          border: Border.all(color: DashboardScreen.borderBlue),
        ),
        child: Row(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            ClipRRect(
              borderRadius: BorderRadius.circular(8),
              child: SizedBox(
                width: 112,
                height: 158,
                child: _DashboardFacilityImage(facility: facility),
              ),
            ),
            const SizedBox(width: 12),
            Expanded(
              child: SizedBox(
                height: 158,
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      facility.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: DashboardScreen.primaryNavy,
                        fontSize: 16,
                        fontWeight: FontWeight.w900,
                        height: 1.1,
                      ),
                    ),
                    const SizedBox(height: 8),
                    Wrap(
                      spacing: 8,
                      runSpacing: 5,
                      crossAxisAlignment: WrapCrossAlignment.center,
                      children: [
                        Container(
                          padding: const EdgeInsets.symmetric(
                            horizontal: 9,
                            vertical: 6,
                          ),
                          decoration: BoxDecoration(
                            color: _statusColor.withValues(alpha: 0.12),
                            borderRadius: BorderRadius.circular(10),
                          ),
                          child: Text(
                            facility.status,
                            style: TextStyle(
                              color: _statusColor,
                              fontSize: 11,
                              fontWeight: FontWeight.w900,
                            ),
                          ),
                        ),
                        const Row(
                          mainAxisSize: MainAxisSize.min,
                          children: [
                            Icon(
                              Icons.star,
                              color: DashboardScreen.campusGold,
                              size: 16,
                            ),
                            SizedBox(width: 4),
                            Text(
                              '0.0 (0)',
                              style: TextStyle(
                                color: Color(0xFF111827),
                                fontSize: 12,
                                fontWeight: FontWeight.w800,
                              ),
                            ),
                          ],
                        ),
                      ],
                    ),
                    const SizedBox(height: 8),
                    if ((int.tryParse(facility.capacity) ?? 0) > 0) ...[
                      _DashboardFacilityInfo(
                        icon: Icons.groups_2_outlined,
                        text: 'Capacity: ${facility.capacity}',
                      ),
                      const SizedBox(height: 4),
                    ],
                    _DashboardFacilityInfo(
                      icon: Icons.local_offer_outlined,
                      text: facility.priceLabel,
                    ),
                    if (facility.slots.trim().isNotEmpty) ...[
                      const SizedBox(height: 4),
                      _DashboardFacilityInfo(
                        icon: Icons.view_timeline_outlined,
                        text: facility.slots.trim(),
                      ),
                    ],
                    const Spacer(),
                    Align(
                      alignment: Alignment.bottomRight,
                      child: SizedBox(
                        height: 32,
                        child: ElevatedButton(
                          onPressed: onTap,
                          style: ElevatedButton.styleFrom(
                            backgroundColor: DashboardScreen.primaryNavy,
                            foregroundColor: Colors.white,
                            elevation: 0,
                            shape: RoundedRectangleBorder(
                              borderRadius: BorderRadius.circular(8),
                            ),
                            padding: const EdgeInsets.symmetric(horizontal: 12),
                          ),
                          child: const Text(
                            'Book Now',
                            style: TextStyle(
                              fontSize: 11,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                        ),
                      ),
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

class _DashboardFacilityImage extends StatelessWidget {
  const _DashboardFacilityImage({required this.facility});

  final _DashboardFacilityItem facility;

  @override
  Widget build(BuildContext context) {
    final imageUrl = facility.imageUrl.trim();

    // Handle base64 data URLs
    if (imageUrl.startsWith('data:image/')) {
      final commaIndex = imageUrl.indexOf(',');
      if (commaIndex != -1) {
        try {
          final bytes = base64.decode(imageUrl.substring(commaIndex + 1));
          return Image.memory(
            bytes,
            fit: BoxFit.cover,
            errorBuilder: (context, error, stackTrace) => _fallback,
          );
        } catch (_) {
          return _fallback;
        }
      }
    }

    // Handle network URLs
    if (imageUrl.startsWith('http://') || imageUrl.startsWith('https://')) {
      return Image.network(
        imageUrl,
        fit: BoxFit.cover,
        errorBuilder: (context, error, stackTrace) => _fallback,
      );
    }

    // Handle relative paths — prepend the API base URL
    if (imageUrl.startsWith('/')) {
      final fullUrl = '${ApiConfig.effectiveBaseUrl}$imageUrl';
      return Image.network(
        fullUrl,
        fit: BoxFit.cover,
        errorBuilder: (context, error, stackTrace) => _fallback,
      );
    }

    return _fallback;
  }

  Widget get _fallback => Container(
    color: const Color(0xFFEAF1FF),
    child: Icon(facility.icon, color: DashboardScreen.primaryNavy, size: 38),
  );
}

class _DashboardFacilityInfo extends StatelessWidget {
  const _DashboardFacilityInfo({required this.icon, required this.text});

  final IconData icon;
  final String text;

  @override
  Widget build(BuildContext context) {
    return Row(
      children: [
        Icon(icon, color: const Color(0xFF475569), size: 14),
        const SizedBox(width: 5),
        Expanded(
          child: Text(
            text,
            maxLines: 1,
            overflow: TextOverflow.ellipsis,
            style: const TextStyle(
              color: Color(0xFF334155),
              fontSize: 11,
              fontWeight: FontWeight.w700,
            ),
          ),
        ),
      ],
    );
  }
}

class _DashboardFacilityItem {
  const _DashboardFacilityItem({
    required this.name,
    required this.status,
    required this.capacity,
    required this.rate,
    required this.priceType,
    required this.slots,
    required this.icon,
    required this.imageUrl,
  });

  factory _DashboardFacilityItem.fromJson(Map<String, dynamic> json) {
    final statusKey = (json['status'] as String? ?? 'available').toLowerCase();
    final statusLabel = switch (statusKey) {
      'available' => 'Available',
      'reserved' || 'occupied' => 'Reserved',
      'maintenance' => 'Maintenance',
      _ => 'Available',
    };
    final name = (json['name'] as String? ?? 'Untitled Facility').trim();

    return _DashboardFacilityItem(
      name: name.isEmpty ? 'Untitled Facility' : name,
      status: statusLabel,
      capacity: (json['capacity'] ?? 0).toString(),
      rate: json['rate']?.toString() ?? '0',
      priceType: json['price_type'] as String? ?? 'hour',
      slots: (json['slots'] as String? ?? '').trim(),
      icon: _iconForDashboardFacility(name),
      imageUrl: json['image_url'] as String? ?? '',
    );
  }

  final String name;
  final String status;
  final String capacity;
  final String rate;
  final String priceType;
  final String slots;
  final IconData icon;
  final String imageUrl;

  String get priceLabel {
    if (rate.isEmpty || rate == '0') return 'Contact Admin';
    final parsed = double.tryParse(rate);
    final amount = parsed == null ? rate : parsed.toStringAsFixed(0);
    return '₱$amount / $priceType';
  }
}

IconData _iconForDashboardFacility(String value) {
  final lower = value.toLowerCase();
  if (lower.contains('court')) return Icons.sports_basketball_outlined;
  if (lower.contains('hall')) return Icons.account_balance_outlined;
  if (lower.contains('hostel') || lower.contains('dorm')) {
    return Icons.hotel_outlined;
  }
  if (lower.contains('lab')) return Icons.science_outlined;
  return Icons.assignment_outlined;
}

class _HeroCarousel extends StatefulWidget {
  const _HeroCarousel({
    required this.onExploreTap,
    required this.onBookTap,
    required this.onBrowseTap,
  });

  final VoidCallback onExploreTap;
  final VoidCallback onBookTap;
  final VoidCallback onBrowseTap;

  @override
  State<_HeroCarousel> createState() => _HeroCarouselState();
}

class _HeroCarouselState extends State<_HeroCarousel> {
  final PageController _controller = PageController();
  int _index = 0;
  Timer? _autoTimer;

  static const List<_HeroSlideData> _slides = [
    _HeroSlideData(
      title: 'Your Campus Essentials,\nSimplified',
      subtitle:
          'Book facilities, explore products, and access campus services in one platform.',
      buttonLabel: 'Explore Now',
    ),
    _HeroSlideData(
      title: 'Book Campus Facilities\nEasily',
      subtitle:
          'Reserve smart rooms, laboratories, covered courts, and event spaces anytime.',
      buttonLabel: 'Book Now',
    ),
    _HeroSlideData(
      title: 'Discover Products and\nCampus Services',
      subtitle:
          'Shop products, order meals, and connect with student services in one app.',
      buttonLabel: 'Browse Product',
    ),
  ];

  @override
  void initState() {
    super.initState();
    _startAutoSwitch();
  }

  void _startAutoSwitch() {
    _autoTimer = Timer.periodic(const Duration(seconds: 5), (_) {
      if (!mounted) return;
      final next = (_index + 1) % _slides.length;
      _controller.animateToPage(
        next,
        duration: const Duration(milliseconds: 400),
        curve: Curves.easeInOut,
      );
    });
  }

  @override
  void dispose() {
    _autoTimer?.cancel();
    _controller.dispose();
    super.dispose();
  }

  VoidCallback _buttonAction(int index) {
    if (index == 1) return widget.onBookTap;
    return index == 2 ? widget.onBrowseTap : widget.onExploreTap;
  }

  @override
  Widget build(BuildContext context) {
    return Column(
      children: [
        SizedBox(
          height: 224,
          child: PageView.builder(
            controller: _controller,
            itemCount: _slides.length,
            onPageChanged: (index) => setState(() => _index = index),
            itemBuilder: (context, index) {
              return _HeroSlideCard(
                slide: _slides[index],
                onPressed: _buttonAction(index),
              );
            },
          ),
        ),
        const SizedBox(height: 10),
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: List.generate(_slides.length, (index) {
            final active = index == _index;
            return AnimatedContainer(
              duration: const Duration(milliseconds: 180),
              curve: Curves.easeOut,
              width: active ? 22 : 7,
              height: 7,
              margin: const EdgeInsets.symmetric(horizontal: 3),
              decoration: BoxDecoration(
                borderRadius: BorderRadius.circular(999),
                color: active
                    ? DashboardScreen.primaryNavy
                    : DashboardScreen.primaryNavy.withValues(alpha: 0.16),
              ),
            );
          }),
        ),
      ],
    );
  }
}

class _HeroSlideCard extends StatelessWidget {
  const _HeroSlideCard({required this.slide, required this.onPressed});

  final _HeroSlideData slide;
  final VoidCallback onPressed;

  @override
  Widget build(BuildContext context) {
    return RepaintBoundary(
      child: Container(
        margin: const EdgeInsets.symmetric(horizontal: 2),
        decoration: BoxDecoration(
          color: const Color(0xFFF8F9FB),
          borderRadius: BorderRadius.circular(24),
          border: Border.all(color: const Color(0xFFE2E8F0)),
          boxShadow: [
            BoxShadow(
              color: DashboardScreen.primaryNavy.withValues(alpha: 0.07),
              blurRadius: 14,
              offset: const Offset(0, 8),
            ),
          ],
          gradient: const LinearGradient(
            colors: [Color(0xFFFFFFFF), Color(0xFFF1F5FF), Color(0xFFFFF7DE)],
            stops: [0.0, 0.62, 1.0],
            begin: Alignment.topLeft,
            end: Alignment.bottomRight,
          ),
        ),
        child: Padding(
          padding: const EdgeInsets.fromLTRB(20, 18, 20, 16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              Text(
                slide.title,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: DashboardScreen.primaryNavy,
                  fontSize: 23,
                  height: 1.16,
                  fontWeight: FontWeight.w900,
                ),
              ),
              const SizedBox(height: 10),
              Text(
                slide.subtitle,
                maxLines: 3,
                overflow: TextOverflow.ellipsis,
                style: const TextStyle(
                  color: Color(0xFF4A5568),
                  fontSize: 13,
                  height: 1.35,
                  fontWeight: FontWeight.w500,
                ),
              ),
              const Spacer(),
              SizedBox(
                height: 40,
                child: ElevatedButton(
                  onPressed: onPressed,
                  style: ElevatedButton.styleFrom(
                    elevation: 0,
                    backgroundColor: DashboardScreen.primaryNavy,
                    foregroundColor: Colors.white,
                    padding: const EdgeInsets.symmetric(horizontal: 20),
                    shape: RoundedRectangleBorder(
                      borderRadius: BorderRadius.circular(20),
                    ),
                  ),
                  child: Text(
                    slide.buttonLabel,
                    style: const TextStyle(
                      fontSize: 13,
                      fontWeight: FontWeight.w800,
                    ),
                  ),
                ),
              ),
            ],
          ),
        ),
      ),
    );
  }
}

class _MarketplacePage extends StatefulWidget {
  const _MarketplacePage();

  @override
  State<_MarketplacePage> createState() => _MarketplacePageState();
}

class _MarketplacePageState extends State<_MarketplacePage> {
  bool _isLoading = true;
  String? _error;
  List<ProductItem> _products = const [];
  List<ProductItem> _recommended = const [];

  @override
  void initState() {
    super.initState();
    _fetchApprovedProducts();
  }

  Future<void> _fetchRecommended(int? userId) async {
    final rows = await ProductService.fetchRecommended(
      userId: userId,
      limit: 8,
    );
    if (!mounted) return;
    setState(() {
      _recommended = rows
          .map(
            (row) => ProductItem.fromJson(
              row.map((key, value) => MapEntry(key.toString(), value)),
            ),
          )
          .toList(growable: false);
    });
  }

  Future<void> _fetchApprovedProducts() async {
    if (mounted) {
      setState(() {
        _isLoading = true;
        _error = null;
      });
    }

    for (final baseUrl in DashboardScreen.apiBaseUrls) {
      try {
        final response = await http
            .get(
              Uri.parse('$baseUrl/api/products/approved/'),
              headers: const {'Accept': 'application/json'},
            )
            .timeout(const Duration(seconds: 5));

        if (response.statusCode < 200 || response.statusCode >= 300) {
          continue;
        }

        final decoded = jsonDecode(response.body) as Map<String, dynamic>;
        final rows = decoded['products'] as List<dynamic>? ?? const [];
        final products = rows
            .whereType<Map>()
            .map(
              (row) => ProductItem.fromJson(
                row.map((key, value) => MapEntry(key.toString(), value)),
              ),
            )
            .toList(growable: false);

        if (!mounted) return;
        ApiConfig.recordWorkingBaseUrl(baseUrl);
        final user = await SessionService.loadUser();
        setState(() {
          _products = products;
          _isLoading = false;
        });
        await _fetchRecommended(user?.id);
        return;
      } catch (_) {}
    }

    if (!mounted) return;
    setState(() {
      _error = 'Start Django with: python manage.py runserver 0.0.0.0:8000';
      _isLoading = false;
    });
  }

  @override
  Widget build(BuildContext context) {
    final recentlyAdded = _products.take(4).toList(growable: false);
    final popular = _recommended.isNotEmpty
        ? _recommended
        : (_products.length > 4
              ? _products.skip(4).toList(growable: false)
              : const <ProductItem>[]);

    return RefreshIndicator(
      onRefresh: _fetchApprovedProducts,
      child: ListView(
        cacheExtent: 700,
        padding: const EdgeInsets.fromLTRB(16, 18, 16, 24),
        children: [
          const _PageTitle('Recently Added'),
          const SizedBox(height: 14),
          _buildProductsSection(
            products: recentlyAdded,
            emptyMessage: 'New approved products will appear here.',
          ),
          const SizedBox(height: 24),
          const _PageTitle('Recommended For You'),
          const SizedBox(height: 14),
          _buildProductsSection(
            products: popular,
            emptyMessage:
                'Browse products to get personalized recommendations.',
            // While loading we already showed a spinner above, avoid double spinner.
            showLoadingPlaceholder: false,
          ),
        ],
      ),
    );
  }

  Widget _buildProductsSection({
    required List<ProductItem> products,
    required String emptyMessage,
    bool showLoadingPlaceholder = true,
  }) {
    if (_isLoading && showLoadingPlaceholder) {
      return const Padding(
        padding: EdgeInsets.symmetric(vertical: 28),
        child: Center(child: CircularProgressIndicator()),
      );
    }
    if (_error != null && showLoadingPlaceholder) {
      return _ProductsMessageCard(
        icon: Icons.cloud_off_outlined,
        title: 'Unable to load products',
        message: _error!,
        actionLabel: 'Retry',
        onAction: _fetchApprovedProducts,
      );
    }
    if (products.isEmpty) {
      return _ProductsMessageCard(
        icon: Icons.shopping_bag_outlined,
        title: 'No products yet',
        message: emptyMessage,
        actionLabel: 'Refresh',
        onAction: _fetchApprovedProducts,
      );
    }
    return _ProductGrid(products: products);
  }
}

class _ProductsMessageCard extends StatelessWidget {
  const _ProductsMessageCard({
    required this.icon,
    required this.title,
    required this.message,
    required this.actionLabel,
    required this.onAction,
  });

  final IconData icon;
  final String title;
  final String message;
  final String actionLabel;
  final VoidCallback onAction;

  @override
  Widget build(BuildContext context) {
    return Container(
      padding: const EdgeInsets.symmetric(horizontal: 18, vertical: 24),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(8),
        border: Border.all(color: DashboardScreen.borderBlue),
      ),
      child: Column(
        children: [
          Icon(icon, color: DashboardScreen.primaryNavy, size: 34),
          const SizedBox(height: 10),
          Text(
            title,
            style: const TextStyle(
              color: DashboardScreen.primaryNavy,
              fontSize: 15,
              fontWeight: FontWeight.w800,
            ),
          ),
          const SizedBox(height: 6),
          Text(
            message,
            textAlign: TextAlign.center,
            style: const TextStyle(color: Colors.black54, fontSize: 12),
          ),
          const SizedBox(height: 12),
          OutlinedButton(
            onPressed: onAction,
            child: Text(
              actionLabel,
              style: const TextStyle(fontWeight: FontWeight.w800),
            ),
          ),
        ],
      ),
    );
  }
}

class _PageTitle extends StatelessWidget {
  const _PageTitle(this.title);

  final String title;

  @override
  Widget build(BuildContext context) {
    return Text(
      title,
      style: const TextStyle(
        color: Colors.black,
        fontSize: 20,
        fontWeight: FontWeight.w800,
      ),
    );
  }
}

class _ProductGrid extends StatelessWidget {
  const _ProductGrid({required this.products});

  final List<ProductItem> products;

  @override
  Widget build(BuildContext context) {
    return GridView.builder(
      shrinkWrap: true,
      physics: const NeverScrollableScrollPhysics(),
      itemCount: products.length,
      gridDelegate: const SliverGridDelegateWithFixedCrossAxisCount(
        crossAxisCount: 2,
        mainAxisSpacing: 14,
        crossAxisSpacing: 14,
        childAspectRatio: 0.68,
      ),
      itemBuilder: (context, index) {
        return _LargeProductCard(product: products[index]);
      },
    );
  }
}

class _SectionHeader extends StatelessWidget {
  const _SectionHeader({required this.title, required this.onViewAll});

  final String title;
  final VoidCallback onViewAll;

  @override
  Widget build(BuildContext context) {
    return Row(
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Text(
          title,
          style: const TextStyle(
            color: Colors.black,
            fontSize: 16,
            fontWeight: FontWeight.w800,
          ),
        ),
        TextButton(
          onPressed: onViewAll,
          style: TextButton.styleFrom(
            foregroundColor: DashboardScreen.primaryBlue,
            padding: EdgeInsets.zero,
            minimumSize: const Size(70, 32),
          ),
          child: const Row(
            mainAxisSize: MainAxisSize.min,
            children: [
              Text(
                'See All',
                style: TextStyle(fontSize: 15, fontWeight: FontWeight.w700),
              ),
              SizedBox(width: 4),
              Icon(Icons.chevron_right, size: 20),
            ],
          ),
        ),
      ],
    );
  }
}

class _LargeProductCard extends StatefulWidget {
  const _LargeProductCard({required this.product});

  final ProductItem product;

  @override
  State<_LargeProductCard> createState() => _LargeProductCardState();
}

class _LargeProductCardState extends State<_LargeProductCard> {
  ProductItem get product => widget.product;

  String get _favoriteKey =>
      favoriteKeyForProduct(id: product.id, name: product.name);

  @override
  void initState() {
    super.initState();
    FavoriteService.instance.load();
  }

  Future<void> _toggleFavorite() =>
      FavoriteService.instance.toggle(_favoriteKey);

  Future<void> _openDetails(BuildContext context) async {
    final user = await SessionService.loadUser();
    if (product.id != null && user != null) {
      await ProductService.trackInteraction(
        userId: user.id,
        productId: product.id!,
        interactionType: 'view',
      );
    }

    if (!context.mounted) return;
    await Navigator.of(context).push(
      MaterialPageRoute(
        builder: (_) => ProductDetailsScreen(
          id: product.id,
          userId: user?.id,
          sellerId: product.sellerId,
          name: product.name,
          priceLabel: product.price,
          imageUrl: product.imageUrl,
          images: product.images,
          category: product.category,
          seller: product.seller,
          sellerContact: product.sellerContact,
          stock: product.stock,
          description: product.description,
          expiryDate: product.expiryDate,
          inventoryStatus: product.inventoryStatus,
          inventoryStatusLabel: product.inventoryStatusLabel,
          isPurchasable: product.isPurchasable,
          soldCount: product.soldCount,
          customization: product.customization,
        ),
      ),
    );
  }

  Future<void> _handleQuickAdd() async {
    if (!product.isPurchasable) {
      if (!mounted) return;
      ScaffoldMessenger.of(context).showSnackBar(
        const SnackBar(
          content: Text('This product is unavailable.'),
          duration: Duration(seconds: 1),
        ),
      );
      return;
    }

    await CartService.instance.quickAdd(context: context, product: product);
  }

  @override
  Widget build(BuildContext context) {
    final isHot = product.soldCount > 0;
    final badgeLabel = isHot ? 'Hot' : 'New';

    return RepaintBoundary(
      child: Container(
        decoration: BoxDecoration(
          color: Colors.white,
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: const Color(0xFFCBD5E1), width: 1.2),
          boxShadow: [
            BoxShadow(
              color: const Color(0xFF1A1851).withValues(alpha: 0.05),
              blurRadius: 14,
              offset: const Offset(0, 4),
            ),
          ],
        ),
        foregroundDecoration: BoxDecoration(
          borderRadius: BorderRadius.circular(18),
          border: Border.all(color: const Color(0xFFCBD5E1), width: 1.2),
        ),
        child: Column(
          crossAxisAlignment: CrossAxisAlignment.start,
          children: [
            Expanded(
              child: GestureDetector(
                onTap: () => _openDetails(context),
                behavior: HitTestBehavior.opaque,
                child: ClipRRect(
                  borderRadius: const BorderRadius.vertical(
                    top: Radius.circular(17),
                  ),
                  child: Container(
                    color: const Color(0xFFF4F5F7),
                    child: Stack(
                      fit: StackFit.expand,
                      children: [
                        Padding(
                          padding: const EdgeInsets.fromLTRB(12, 12, 12, 12),
                          child: ProductImage(
                            imageUrl: product.imageUrl,
                            fallbackIcon: product.icon,
                            fit: BoxFit.contain,
                          ),
                        ),
                        Positioned(
                          top: 8,
                          left: 8,
                          child: Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 7,
                              vertical: 3,
                            ),
                            decoration: BoxDecoration(
                              color: isHot
                                  ? const Color(0xFFFCB316)
                                  : const Color(0xFF1A1851),
                              borderRadius: BorderRadius.circular(8),
                            ),
                            child: Text(
                              badgeLabel,
                              style: TextStyle(
                                color: isHot
                                    ? const Color(0xFF1A1851)
                                    : Colors.white,
                                fontSize: 9,
                                fontWeight: FontWeight.w800,
                                letterSpacing: 0.2,
                              ),
                            ),
                          ),
                        ),
                        Positioned(
                          top: 8,
                          right: 8,
                          child: ListenableBuilder(
                            listenable: FavoriteService.instance,
                            builder: (context, _) {
                              final isFav = FavoriteService.instance.isFavorite(
                                _favoriteKey,
                              );
                              return Material(
                                color: Colors.white.withValues(alpha: 0.9),
                                shape: const CircleBorder(),
                                elevation: 0.5,
                                child: InkWell(
                                  customBorder: const CircleBorder(),
                                  onTap: _toggleFavorite,
                                  child: Padding(
                                    padding: const EdgeInsets.all(6),
                                    child: Icon(
                                      isFav
                                          ? Icons.favorite
                                          : Icons.favorite_border,
                                      size: 16,
                                      color: isFav
                                          ? const Color(0xFFDC2626)
                                          : const Color(0xFF64748B),
                                    ),
                                  ),
                                ),
                              );
                            },
                          ),
                        ),
                      ],
                    ),
                  ),
                ),
              ),
            ),
            GestureDetector(
              onTap: () => _openDetails(context),
              behavior: HitTestBehavior.opaque,
              child: Padding(
                padding: const EdgeInsets.fromLTRB(12, 8, 12, 0),
                child: Column(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    Text(
                      product.seller.trim().isNotEmpty
                          ? product.seller.trim()
                          : 'Campus Marketplace',
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: Color(0xFF94A3B8),
                        fontSize: 10.5,
                        fontWeight: FontWeight.w500,
                      ),
                    ),
                    const SizedBox(height: 2),
                    Text(
                      product.name,
                      maxLines: 1,
                      overflow: TextOverflow.ellipsis,
                      style: const TextStyle(
                        color: Color(0xFF1A1851),
                        fontSize: 13.5,
                        fontWeight: FontWeight.w700,
                      ),
                    ),
                    if (product.category.isNotEmpty) ...[
                      const SizedBox(height: 2),
                      Text(
                        product.category,
                        maxLines: 1,
                        overflow: TextOverflow.ellipsis,
                        style: const TextStyle(
                          color: Color(0xFF94A3B8),
                          fontSize: 11,
                          fontWeight: FontWeight.w500,
                        ),
                      ),
                    ],
                  ],
                ),
              ),
            ),
            Padding(
              padding: const EdgeInsets.fromLTRB(12, 4, 12, 10),
              child: Row(
                mainAxisAlignment: MainAxisAlignment.spaceBetween,
                crossAxisAlignment: CrossAxisAlignment.center,
                children: [
                  Expanded(
                    child: GestureDetector(
                      onTap: () => _openDetails(context),
                      behavior: HitTestBehavior.opaque,
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Text(
                            product.price,
                            maxLines: 1,
                            overflow: TextOverflow.ellipsis,
                            style: const TextStyle(
                              color: Color(0xFF1A1851),
                              fontSize: 15,
                              fontWeight: FontWeight.w800,
                            ),
                          ),
                          if (product.hasReviews) ...[
                            const SizedBox(height: 3),
                            Row(
                              children: [
                                for (int i = 1; i <= 5; i++)
                                  Icon(
                                    i <= (product.rating ?? 0).floor()
                                        ? Icons.star
                                        : (i - (product.rating ?? 0) < 1 &&
                                                  (product.rating ?? 0) -
                                                          (product.rating ?? 0)
                                                              .floor() >=
                                                      0.3
                                              ? Icons.star_half
                                              : Icons.star_border),
                                    size: 12,
                                    color: const Color(0xFFFCB316),
                                  ),
                                const SizedBox(width: 3),
                                Text(
                                  '(${product.reviewsCount})',
                                  style: const TextStyle(
                                    fontSize: 10,
                                    color: Color(0xFF94A3B8),
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ],
                            ),
                          ],
                        ],
                      ),
                    ),
                  ),
                  Material(
                    color: const Color(0xFF1A1851),
                    borderRadius: BorderRadius.circular(10),
                    child: InkWell(
                      borderRadius: BorderRadius.circular(10),
                      onTap: _handleQuickAdd,
                      child: const Padding(
                        padding: EdgeInsets.all(7),
                        child: Icon(
                          LucideIcons.shoppingBag,
                          color: Colors.white,
                          size: 17,
                        ),
                      ),
                    ),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }
}

class _HeroSlideData {
  const _HeroSlideData({
    required this.title,
    required this.subtitle,
    required this.buttonLabel,
  });

  final String title;
  final String subtitle;
  final String buttonLabel;
}

class _DashboardDrawer extends StatelessWidget {
  const _DashboardDrawer({
    required this.currentIndex,
    required this.onSelectTab,
    this.onOpenMessages,
  });

  final int currentIndex;
  final ValueChanged<int> onSelectTab;
  final VoidCallback? onOpenMessages;

  @override
  Widget build(BuildContext context) {
    const navy = Color(0xFF1A1851);
    const gold = Color(0xFFFCB316);

    return Drawer(
      backgroundColor: Colors.white,
      child: Column(
        children: [
          Container(
            width: double.infinity,
            padding: EdgeInsets.fromLTRB(
              20,
              MediaQuery.of(context).padding.top + 24,
              20,
              20,
            ),
            color: navy,
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Row(
                  children: [
                    Image.asset(
                      'assets/img/logo.png',
                      width: 42,
                      height: 42,
                      fit: BoxFit.contain,
                      errorBuilder: (context, error, stackTrace) => Container(
                        width: 42,
                        height: 42,
                        decoration: const BoxDecoration(
                          shape: BoxShape.circle,
                          color: Colors.white24,
                        ),
                        child: const Icon(
                          Icons.school_outlined,
                          color: Colors.white,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    RichText(
                      text: const TextSpan(
                        style: TextStyle(
                          fontSize: 22,
                          fontWeight: FontWeight.w800,
                        ),
                        children: [
                          TextSpan(
                            text: 'Campus',
                            style: TextStyle(color: gold),
                          ),
                          TextSpan(
                            text: 'Hub',
                            style: TextStyle(color: Colors.white),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
                const SizedBox(height: 14),
                FutureBuilder(
                  future: SessionService.loadUser(),
                  builder: (context, snapshot) {
                    final user = snapshot.data;
                    final displayName = user?.fullName.isNotEmpty == true
                        ? user!.fullName
                        : (user?.firstName.isNotEmpty == true
                              ? '${user!.firstName} ${user.lastName}'.trim()
                              : 'USTP Oroquieta');
                    final subTitle = user?.email.isNotEmpty == true
                        ? user!.email
                        : (user?.role.isNotEmpty == true
                              ? user!.role.toUpperCase()
                              : 'Campus Marketplace & Facilities');
                    return Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        Text(
                          displayName,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: const TextStyle(
                            color: Colors.white,
                            fontSize: 15,
                            fontWeight: FontWeight.w700,
                          ),
                        ),
                        const SizedBox(height: 2),
                        Text(
                          subTitle,
                          maxLines: 1,
                          overflow: TextOverflow.ellipsis,
                          style: TextStyle(
                            color: Colors.white.withValues(alpha: 0.7),
                            fontSize: 12,
                          ),
                        ),
                      ],
                    );
                  },
                ),
              ],
            ),
          ),
          Expanded(
            child: ListView(
              padding: const EdgeInsets.symmetric(vertical: 8),
              children: [
                _DrawerNavTile(
                  icon: LucideIcons.home,
                  title: 'Home',
                  isSelected: currentIndex == 0,
                  onTap: () {
                    Navigator.of(context).pop();
                    onSelectTab(0);
                  },
                ),
                _DrawerNavTile(
                  icon: LucideIcons.shoppingBag,
                  title: 'Marketplace',
                  isSelected: currentIndex == 1,
                  onTap: () {
                    Navigator.of(context).pop();
                    onSelectTab(1);
                  },
                ),
                _DrawerNavTile(
                  icon: LucideIcons.building2,
                  title: 'Facilities Booking',
                  isSelected: currentIndex == 2,
                  onTap: () {
                    Navigator.of(context).pop();
                    onSelectTab(2);
                  },
                ),
                _DrawerNavTile(
                  icon: LucideIcons.messageSquare,
                  title: 'Messages',
                  isSelected: false,
                  onTap: () {
                    Navigator.of(context).pop();
                    if (onOpenMessages != null) {
                      onOpenMessages!();
                    } else {
                      onSelectTab(3);
                    }
                  },
                ),
                _DrawerNavTile(
                  icon: LucideIcons.user,
                  title: 'Profile & Account',
                  isSelected: currentIndex == 3,
                  onTap: () {
                    Navigator.of(context).pop();
                    onSelectTab(3);
                  },
                ),
                const Padding(
                  padding: EdgeInsets.symmetric(horizontal: 16, vertical: 8),
                  child: Divider(color: Color(0xFFE2E8F0), height: 1),
                ),
                _DrawerNavTile(
                  icon: LucideIcons.shoppingBag,
                  title: 'My Cart',
                  isSelected: false,
                  onTap: () {
                    Navigator.of(context).pop();
                    Navigator.of(context).push(
                      MaterialPageRoute(builder: (_) => const CartScreen()),
                    );
                  },
                ),
              ],
            ),
          ),
          Container(
            padding: const EdgeInsets.all(16),
            decoration: const BoxDecoration(
              border: Border(
                top: BorderSide(color: Color(0xFFE2E8F0), width: 1),
              ),
            ),
            child: Row(
              children: [
                const Icon(
                  LucideIcons.graduationCap,
                  size: 18,
                  color: Color(0xFF94A3B8),
                ),
                const SizedBox(width: 8),
                const Expanded(
                  child: Text(
                    'USTP Oroquieta Campus',
                    style: TextStyle(
                      color: Color(0xFF94A3B8),
                      fontSize: 11,
                      fontWeight: FontWeight.w600,
                    ),
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

class _DrawerNavTile extends StatelessWidget {
  const _DrawerNavTile({
    required this.icon,
    required this.title,
    required this.isSelected,
    required this.onTap,
  });

  final IconData icon;
  final String title;
  final bool isSelected;
  final VoidCallback onTap;

  @override
  Widget build(BuildContext context) {
    const navy = Color(0xFF1A1851);
    const gold = Color(0xFFFCB316);

    return Container(
      margin: const EdgeInsets.symmetric(horizontal: 10, vertical: 2),
      decoration: BoxDecoration(
        color: isSelected ? navy.withValues(alpha: 0.08) : Colors.transparent,
        borderRadius: BorderRadius.circular(10),
      ),
      child: ListTile(
        shape: RoundedRectangleBorder(borderRadius: BorderRadius.circular(10)),
        leading: Icon(
          icon,
          color: isSelected ? navy : const Color(0xFF64748B),
          size: 22,
        ),
        title: Text(
          title,
          style: TextStyle(
            color: isSelected ? navy : const Color(0xFF334155),
            fontSize: 14,
            fontWeight: isSelected ? FontWeight.w700 : FontWeight.w500,
          ),
        ),
        trailing: isSelected
            ? Container(
                width: 6,
                height: 6,
                decoration: const BoxDecoration(
                  shape: BoxShape.circle,
                  color: gold,
                ),
              )
            : null,
        onTap: onTap,
        dense: true,
        contentPadding: const EdgeInsets.symmetric(horizontal: 12, vertical: 0),
      ),
    );
  }
}
