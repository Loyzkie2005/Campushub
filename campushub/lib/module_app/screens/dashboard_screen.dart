import 'dart:async';
import 'package:flutter/material.dart';
import '../theme/marketplace_colors.dart';
import 'package:flutter/services.dart';
import 'package:iconsax_flutter/iconsax_flutter.dart';
import 'products_screen.dart';
import '../services/cart_service.dart';
import 'facility_screen.dart';
import 'services_screen.dart';
import 'messages_screen.dart';
import 'profile_page.dart';
import 'seller_dashboard_page.dart';
import '../services/auth_service.dart';
import '../services/seller_application_service.dart';
import '../widgets/navigation/seller_drawer.dart';
import '../config/api_config.dart';
import '../models/product_item.dart';
import '../services/facility_service.dart';
import '../services/chat_service.dart';
import 'cart_screen.dart';
import 'home_page.dart';
import '../services/service_catalog.dart';
import '../services/favorite_service.dart';
import '../services/product_service.dart';
import '../session/session_service.dart';
import '../widgets/home/home_preview_cards.dart';
import '../widgets/product_image.dart';
import '../widgets/navigation/floating_bottom_navbar.dart';
import '../widgets/navigation/retained_tab.dart';
import '../widgets/navigation/campushub_brand.dart';
import '../widgets/navigation/header_search_button.dart';
import '../widgets/notification_permission_sheet.dart';
import 'product_details_screen.dart';
import 'search_page.dart';

class DashboardScreen extends StatefulWidget {
  const DashboardScreen({
    super.key,
    this.initialTab = 0,
    this.serviceCatalog = const ServiceCatalog(),
    this.loadHomeProducts = ProductService.fetchApproved,
    this.loadHomeFacilities = FacilityService.fetchFacilities,
    this.sellerService = const SellerApplicationService(),
  }) : assert(initialTab >= 0 && initialTab < 5);
  final int initialTab;
  final ServiceCatalog serviceCatalog;
  final Future<List<ProductItem>> Function() loadHomeProducts;
  final Future<FacilityServiceResult> Function() loadHomeFacilities;
  final SellerApplicationService sellerService;

  static const Color primaryNavy = Color(0xFF142B47);
  static const Color primaryBlue = Color(0xFF1A56DB);
  static const Color webBrandBlue = Color(0xFF0175C2);
  static const Color campusGold = Color(0xFFFCB315);
  static const Color pageBackground = Colors.white;
  static const Color headerNavy = Color(0xFF1A1851);
  static const Color headerTint = Colors.white;
  static const Color borderBlue = Color(0xFFBFD7FF);
  static String get apiBaseUrl => ApiConfig.baseUrl;
  static List<String> get apiBaseUrls => ApiConfig.serverBaseUrls;

  @override
  State<DashboardScreen> createState() => _DashboardScreenState();
}

class _DashboardScreenState extends State<DashboardScreen>
    with WidgetsBindingObserver {
  late final PageController _pageController;
  final _scaffoldKey = GlobalKey<ScaffoldState>();
  final _homeKey = GlobalKey<HomePageState>();
  int _currentIndex = 0;
  String _firstName = '';
  AuthUser? _user;
  bool _sellerApproved = false;
  String? _accessError;
  int _accessRequest = 0;
  int _sellerRefreshRevision = 0;
  bool _openingProduct = false;

  @override
  void initState() {
    super.initState();
    _currentIndex = widget.initialTab;
    _pageController = PageController(initialPage: _currentIndex);
    WidgetsBinding.instance.addObserver(this);
    _loadUserName();
    unawaited(_initializeChat());
  }

  Future<void> _initializeChat() async {
    try {
      await ChatService.instance.initialize();
    } on ChatException catch (error) {
      // Chat is optional on Home. Messages keeps its own visible error/retry.
      debugPrint('CampusHub chat unavailable: ${error.message}');
    }
  }

  Future<void> _loadUserName() async {
    final request = ++_accessRequest;
    setState(() {
      _accessError = null;
    });
    try {
      final user = await SessionService.loadUser();
      if (!mounted || request != _accessRequest) return;
      setState(() {
        _user = user;
        _firstName = user?.firstName ?? '';
      });
      final status = user != null && user.userType != 'admin'
          ? await widget.sellerService.status()
          : null;
      if (status != null && status['is_approved_seller'] is! bool) {
        throw const SellerApplicationException(
          'Unable to verify seller access. Retry.',
        );
      }
      if (!mounted || request != _accessRequest) return;
      final approved = status?['is_approved_seller'] == true;
      setState(() {
        _user = user;
        _firstName = user?.firstName ?? '';
        _sellerApproved = approved;
        if (approved) _sellerRefreshRevision++;
      });
    } catch (error) {
      if (!mounted || request != _accessRequest) return;
      setState(() {
        _sellerApproved = false;
        _accessError = error is SellerApplicationException
            ? error.message
            : 'Unable to verify seller access. Check your connection and retry.';
      });
    }
  }

  @override
  void didChangeAppLifecycleState(AppLifecycleState state) {
    if (state == AppLifecycleState.resumed) unawaited(_loadUserName());
  }

  @override
  void dispose() {
    WidgetsBinding.instance.removeObserver(this);
    _pageController.dispose();
    super.dispose();
  }

  void _goToTab(int index) {
    if (index == _currentIndex) return;
    FocusManager.instance.primaryFocus?.unfocus();
    setState(() => _currentIndex = index);
    _pageController.jumpToPage(index);
  }

  Future<void> _refreshHome() async {
    await _loadUserName();
  }

  void _openSearch() {
    final home = _homeKey.currentState;
    if (home != null) {
      home.openSearch();
      return;
    }
    // A direct launch into another tab may not have built Home yet.
    Navigator.of(context).push(
      MaterialPageRoute<void>(
        builder: (_) => SearchPage(
          catalog: widget.serviceCatalog,
          loadProducts: widget.loadHomeProducts,
          loadFacilities: widget.loadHomeFacilities,
        ),
      ),
    );
  }

  Future<void> _openAddProduct() async {
    if (!_sellerApproved || _user == null || _openingProduct) return;
    _openingProduct = true;
    try {
      final submitted = await ProductsScreen.showAddProductPage(context);
      if (submitted == true && mounted) await _refreshHome();
    } finally {
      _openingProduct = false;
    }
  }

  void _openSellerTool(SellerDestination destination) {
    if (!_sellerApproved || _user == null) return;
    if (destination == SellerDestination.overview) {
      _goToTab(0);
      return;
    }
    final navigator = Navigator.of(context);
    final ownerRoute = ModalRoute.of(context);
    navigator.push(
      MaterialPageRoute<void>(
        builder: (_) => SellerDashboardPage(
          user: _user!,
          service: widget.sellerService,
          initialDestination: destination,
          onBackToCampusHub: () {
            navigator.popUntil((route) => route == ownerRoute || route.isFirst);
            _goToTab(0);
          },
          onProfile: () {
            navigator.popUntil((route) => route == ownerRoute || route.isFirst);
            _goToTab(4);
          },
          onMessages: _openMessages,
          onNotifications: _openNotifications,
          onSearch: _openSearch,
        ),
      ),
    );
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
              icon: const Icon(Iconsax.arrow_left_copy),
              tooltip: 'Back',
              onPressed: () => Navigator.of(context).pop(),
            ),
            title: const CampusHubBrand(onNavy: false),
            actions: [
              HeaderSearchButton(onPressed: _openSearch),
              IconButton(
                tooltip: 'Notifications',
                icon: const Icon(Iconsax.notification_copy),
                onPressed: _openNotifications,
              ),
            ],
          ),
          body: const MessagesPage(),
        ),
      ),
    );
  }

  void _openNotifications() {
    showModalBottomSheet<void>(
      context: context,
      backgroundColor: Colors.white,
      shape: const RoundedRectangleBorder(
        borderRadius: BorderRadius.vertical(top: Radius.circular(16)),
      ),
      builder: (context) => const NotificationPermissionSheet(),
    );
  }

  Widget _drawerDestination(String label, IconData icon, int index) => ListTile(
    leading: Icon(icon, color: homeNavy),
    title: Text(label),
    selected: _currentIndex == index,
    textColor: homeNavy,
    selectedColor: homeNavy,
    selectedTileColor: homeGold.withValues(alpha: 0.18),
    onTap: () {
      Navigator.pop(context);
      _goToTab(index);
    },
  );

  @override
  Widget build(BuildContext context) {
    final isSeller = _sellerApproved && _user != null;
    final header = Container(
      key: const ValueKey('dashboard-brand-header'),
      color: Colors.white,
      child: SafeArea(
        bottom: false,
        child: Padding(
          padding: const EdgeInsets.fromLTRB(4, 4, 4, 8),
          child: Row(
            children: [
              IconButton(
                tooltip: 'Open menu',
                color: HomeAppColors.navy,
                onPressed: () => _scaffoldKey.currentState?.openDrawer(),
                icon: Icon(Iconsax.menu_1_copy, color: HomeAppColors.navy),
              ),
              Expanded(
                child: CampusHubBrand(
                  onNavy: false,
                  logoKey: const ValueKey('dashboard-brand-logo'),
                  wordmarkKey: const ValueKey('dashboard-brand-name'),
                ),
              ),
              HeaderSearchButton(onPressed: _openSearch),
              IconButton(
                tooltip: 'Notifications',
                color: HomeAppColors.navy,
                onPressed: _openNotifications,
                icon: const Icon(
                  Iconsax.notification_copy,
                  color: HomeAppColors.navy,
                ),
              ),
              const SizedBox(width: 4),
            ],
          ),
        ),
      ),
    );
    return AnnotatedRegion<SystemUiOverlayStyle>(
      value: SystemUiOverlayStyle(
        statusBarColor: Colors.white,
        statusBarIconBrightness: Brightness.dark,
        statusBarBrightness: Brightness.light,
        systemNavigationBarColor: Colors.white,
        systemNavigationBarIconBrightness: Brightness.dark,
      ),
      child: Scaffold(
        key: _scaffoldKey,
        backgroundColor: HomeAppColors.appBackground,
        drawer: _sellerApproved && _user != null
            ? SellerDrawer(
                user: _user!,
                selected: SellerDestination.overview,
                onSelected: (destination) {
                  Navigator.pop(context);
                  _openSellerTool(destination);
                },
                onBackToCampusHub: () {
                  Navigator.pop(context);
                  _goToTab(0);
                },
                onProfile: () {
                  Navigator.pop(context);
                  _goToTab(4);
                },
              )
            : Drawer(
                backgroundColor: Colors.white,
                surfaceTintColor: Colors.transparent,
                elevation: 0,
                child: SafeArea(
                  child: ListView(
                    padding: EdgeInsets.zero,
                    children: [
                      Padding(
                        padding: const EdgeInsets.all(24),
                        child: Text.rich(
                          TextSpan(
                            children: const [
                              TextSpan(
                                text: 'Campus',
                                style: TextStyle(color: HomeAppColors.navy),
                              ),
                              TextSpan(
                                text: 'Hub',
                                style: TextStyle(color: HomeAppColors.gold),
                              ),
                            ],
                          ),
                          style: const TextStyle(
                            fontFamily: 'SugarPie',
                            fontWeight: FontWeight.w400,
                            fontSize: 24,
                            letterSpacing: 0,
                          ),
                        ),
                      ),
                      _drawerDestination('Home', Iconsax.home_copy, 0),
                      _drawerDestination('Marketplace', Iconsax.shop_copy, 1),
                      _drawerDestination(
                        'Facilities Booking',
                        Iconsax.building_copy,
                        3,
                      ),
                      _drawerDestination('Services', Iconsax.briefcase_copy, 2),
                      ListTile(
                        leading: const Icon(
                          Iconsax.message_copy,
                          color: homeNavy,
                        ),
                        title: const Text(
                          'Messages',
                          style: TextStyle(color: homeNavy),
                        ),
                        onTap: () {
                          Navigator.pop(context);
                          _openMessages();
                        },
                      ),
                      _drawerDestination(
                        'Profile & Account',
                        Iconsax.user_copy,
                        4,
                      ),
                      const Divider(color: homeLine),
                      ListTile(
                        leading: const Icon(
                          Iconsax.bag_2_copy,
                          color: homeNavy,
                        ),
                        title: const Text(
                          'My Cart',
                          style: TextStyle(color: homeNavy),
                        ),
                        onTap: () {
                          Navigator.pop(context);
                          Navigator.of(context).push(
                            MaterialPageRoute<void>(
                              builder: (_) => const CartScreen(),
                            ),
                          );
                        },
                      ),
                    ],
                  ),
                ),
              ),
        body: Column(
          children: [
            header,
            Expanded(
              child: PageView(
                physics: const NeverScrollableScrollPhysics(),
                controller: _pageController,
                onPageChanged: (index) {
                  FocusManager.instance.primaryFocus?.unfocus();
                  setState(() => _currentIndex = index);
                },
                children:
                    [
                          HomePage(
                            key: _homeKey,
                            active: _currentIndex == 0,
                            firstName: _firstName,
                            sellerSections: _sellerApproved && _user != null
                                ? SellerDashboardPage(
                                    key: ValueKey('home-seller-${_user!.id}'),
                                    user: _user!,
                                    service: widget.sellerService,
                                    homeSection: true,
                                    refreshRevision: _sellerRefreshRevision,
                                    onOpenDestination: _openSellerTool,
                                  )
                                : _accessError != null
                                ? TextButton(
                                    onPressed: _loadUserName,
                                    child: Text(_accessError!),
                                  )
                                : null,
                            onMarketplace: () => _goToTab(1),
                            onFacilities: () => _goToTab(3),
                            onServices: () => _goToTab(2),
                            onRefresh: _refreshHome,
                            catalog: widget.serviceCatalog,
                            loadProducts: widget.loadHomeProducts,
                            loadFacilities: widget.loadHomeFacilities,
                            productBuilder: (product) =>
                                MarketplacePreviewCard(product: product),
                          ),
                          const _MarketplacePage(),
                          ServicesPage(catalog: widget.serviceCatalog),
                          const FacilitiesPage(),
                          ProfilePage(
                            active: _currentIndex == 4,
                            onHome: () => _goToTab(0),
                            onMarketplace: () => _goToTab(1),
                            onMessages: _openMessages,
                            onNotifications: _openNotifications,
                            onSellerAccessChanged: _loadUserName,
                          ),
                        ]
                        .asMap()
                        .entries
                        .map(
                          (entry) => RetainedTab(
                            key: ValueKey('dashboard-tab-${entry.key}'),
                            child: entry.value,
                          ),
                        )
                        .toList(),
              ),
            ),
          ],
        ),
        bottomNavigationBar: FloatingBottomNavbar(
          currentIndex: _currentIndex,
          onTap: _goToTab,
          onCenterActionTap: isSeller ? _openAddProduct : null,
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
  String _selectedCategory = 'All';

  static const List<String> _webCategories = [
    'All',
    'Rice Meals',
    'Snacks',
    'Desserts',
    'Beverages',
    'Combo Meals',
    'Breakfast',
    'School Supplies',
    'Electronics',
    'Clothing',
    'Accessories',
    'Personal Care',
    'Services',
    'Stationery',
    'Books',
    'Home & Living',
    'Sports',
    'Others',
  ];

  List<String> get _categories {
    final list = List<String>.from(_webCategories);
    for (final p in _products) {
      final cat = p.category.trim();
      if (cat.isNotEmpty &&
          !list.any((c) => c.toLowerCase() == cat.toLowerCase())) {
        list.add(cat);
      }
    }
    return list;
  }

  List<ProductItem> get _filteredCategoryProducts {
    if (_selectedCategory.toLowerCase() == 'all') {
      return _products;
    }
    return _products
        .where(
          (p) =>
              p.category.trim().toLowerCase() ==
              _selectedCategory.toLowerCase(),
        )
        .toList(growable: false);
  }

  IconData _getCategoryIcon(String category) {
    switch (category.toLowerCase()) {
      case 'all':
        return Icons.grid_view_rounded;
      case 'rice meals':
        return Icons.restaurant_rounded;
      case 'snacks':
        return Icons.cookie_outlined;
      case 'desserts':
        return Icons.cake_outlined;
      case 'beverages':
        return Icons.local_cafe_outlined;
      case 'combo meals':
        return Icons.fastfood_rounded;
      case 'breakfast':
        return Icons.breakfast_dining_rounded;
      case 'school supplies':
        return Icons.backpack_outlined;
      case 'electronics':
        return Icons.devices_rounded;
      case 'clothing':
        return Icons.checkroom_rounded;
      case 'accessories':
        return Icons.watch_outlined;
      case 'personal care':
        return Icons.clean_hands_outlined;
      case 'services':
        return Icons.build_outlined;
      case 'stationery':
        return Icons.edit_note_rounded;
      case 'books':
        return Icons.menu_book_rounded;
      case 'home & living':
        return Iconsax.home_copy;
      case 'sports':
        return Icons.sports_basketball_rounded;
      case 'others':
      default:
        return Icons.category_outlined;
    }
  }

  Widget _buildCategoryCards() {
    final categories = _categories;
    return SizedBox(
      height: 38,
      child: ListView.separated(
        scrollDirection: Axis.horizontal,
        physics: const BouncingScrollPhysics(),
        itemCount: categories.length,
        separatorBuilder: (context, index) => const SizedBox(width: 8),
        itemBuilder: (context, index) {
          final cat = categories[index];
          final isSelected =
              _selectedCategory.toLowerCase() == cat.toLowerCase();
          final icon = _getCategoryIcon(cat);

          return Material(
            color: Colors.transparent,
            child: InkWell(
              onTap: () {
                setState(() {
                  _selectedCategory = cat;
                });
              },
              borderRadius: BorderRadius.circular(20),
              child: AnimatedContainer(
                duration: const Duration(milliseconds: 200),
                padding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 8,
                ),
                decoration: BoxDecoration(
                  color: isSelected
                      ? DashboardScreen.primaryNavy
                      : Colors.white,
                  borderRadius: BorderRadius.circular(20),
                  border: Border.all(
                    color: isSelected
                        ? DashboardScreen.primaryNavy
                        : const Color(0xFFE2E8F0),
                    width: isSelected ? 1.4 : 1.0,
                  ),
                  boxShadow: [
                    BoxShadow(
                      color: isSelected
                          ? DashboardScreen.primaryNavy.withValues(alpha: 0.16)
                          : Colors.black.withValues(alpha: 0.03),
                      blurRadius: isSelected ? 4 : 2,
                      offset: const Offset(0, 1),
                    ),
                  ],
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    Icon(
                      icon,
                      size: 15,
                      color: isSelected
                          ? DashboardScreen.campusGold
                          : DashboardScreen.primaryNavy,
                    ),
                    const SizedBox(width: 6),
                    Text(
                      cat,
                      style: TextStyle(
                        fontSize: 12,
                        fontWeight: isSelected
                            ? FontWeight.w700
                            : FontWeight.w600,
                        color: isSelected
                            ? Colors.white
                            : const Color(0xFF1E293B),
                        height: 1.1,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          );
        },
      ),
    );
  }

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
    if (!mounted) return;
    setState(() {
      _isLoading = true;
      _error = null;
    });
    try {
      final products = await ProductService.fetchApproved();
      if (!mounted) return;
      setState(() => _products = products);
      // Optional recommendations must not hold the product spinner or refresh.
      unawaited(_loadCurrentUserRecommendations());
    } catch (_) {
      if (!mounted) return;
      setState(() => _error = ProductService.connectionMessage);
    } finally {
      if (mounted) setState(() => _isLoading = false);
    }
  }

  Future<void> _loadCurrentUserRecommendations() async {
    try {
      final user = await SessionService.loadUser();
      if (mounted) await _fetchRecommended(user?.id);
    } catch (_) {
      // Keep the real catalog visible when optional recommendations fail.
    }
  }

  @override
  Widget build(BuildContext context) {
    final recentlyAdded = _products.take(4).toList(growable: false);
    final popular = _recommended.isNotEmpty
        ? _recommended
        : (_products.length > 4
              ? _products.skip(4).toList(growable: false)
              : const <ProductItem>[]);
    final filteredCategoryProducts = _filteredCategoryProducts;

    return RefreshIndicator(
      onRefresh: _fetchApprovedProducts,
      child: ListView(
        cacheExtent: 700,
        padding: const EdgeInsets.fromLTRB(16, 18, 16, 24),
        children: [
          _buildCategoryCards(),
          const SizedBox(height: 18),
          Row(
            mainAxisAlignment: MainAxisAlignment.spaceBetween,
            children: [
              Text(
                _selectedCategory.toLowerCase() == 'all'
                    ? 'Products'
                    : _selectedCategory,
                style: const TextStyle(
                  color: Colors.black,
                  fontSize: 17,
                  fontWeight: FontWeight.w800,
                ),
              ),
              Text(
                '${filteredCategoryProducts.length} ${filteredCategoryProducts.length == 1 ? 'item' : 'items'}',
                style: const TextStyle(
                  color: Color(0xFF64748B),
                  fontSize: 13,
                  fontWeight: FontWeight.w600,
                ),
              ),
            ],
          ),
          const SizedBox(height: 12),
          _buildProductsSection(
            products: filteredCategoryProducts,
            emptyMessage: _selectedCategory.toLowerCase() == 'all'
                ? 'No products found.'
                : 'No products found in $_selectedCategory.',
            showLoadingPlaceholder: true,
          ),
          if (_selectedCategory.toLowerCase() == 'all') ...[
            const SizedBox(height: 24),
            const _PageTitle('Recently Added'),
            const SizedBox(height: 14),
            _buildProductsSection(
              products: recentlyAdded,
              emptyMessage: 'New approved products will appear here.',
              showLoadingPlaceholder: false,
            ),
            const SizedBox(height: 24),
            const _PageTitle('Recommended For You'),
            const SizedBox(height: 14),
            _buildProductsSection(
              products: popular,
              emptyMessage:
                  'Browse products to get personalized recommendations.',
              showLoadingPlaceholder: false,
            ),
          ],
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
        icon: Iconsax.bag_2_copy,
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
          sellerRef: product.sellerRef,
          name: product.name,
          priceLabel: product.price,
          imageUrl: product.imageUrl,
          images: product.images,
          category: product.category,
          seller: product.seller,
          sellerPhotoUrl: product.sellerPhotoUrl,
          sellerContact: product.sellerContact,
          stock: product.stock,
          description: product.description,
          expiryDate: product.expiryDate,
          inventoryStatus: product.inventoryStatus,
          inventoryStatusLabel: product.inventoryStatusLabel,
          isPurchasable: product.isPurchasable,
          soldCount: product.soldCount,
          rating: product.rating,
          reviewsCount: product.reviewsCount,
          submittedAt: product.submittedAt,
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
          color: MarketplaceColors.cardSurface,
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
                    color: MarketplaceColors.imageSurface,
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
                                  ? const Color(0xFFFCB315)
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
                                      color: const Color(0xFF1A1851),
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
                                    color: const Color(0xFFFCB315),
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
                          Iconsax.bag_2_copy,
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
