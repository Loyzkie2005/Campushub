import 'package:flutter/material.dart';
import 'package:iconsax_flutter/iconsax_flutter.dart';

import '../widgets/home/home_preview_cards.dart';
import '../widgets/navigation/seller_drawer.dart';
import '../widgets/product_image.dart';
import '../widgets/seller/seller_sales_trend.dart';
import '../widgets/profile/profile_widgets.dart';
import '../services/seller_application_service.dart';

/// Presentation only: all totals, stock, recipes and qualifying pairs come from Django.
class SellerWorkspaceContent extends StatefulWidget {
  const SellerWorkspaceContent({
    super.key,
    required this.destination,
    required this.data,
    required this.onNavigate,
    required this.onAddProduct,
    required this.onCreateBundle,
    required this.onReload,
    required this.onPeriod,
    required this.onOrdersPage,
    required this.sellerFirstName,
    this.homeHighlightsOnly = false,
    this.productSearchOpen = false,
    this.onOrderProgress,
  });
  final SellerDestination destination;
  final Map<String, dynamic> data;
  final ValueChanged<SellerDestination> onNavigate;
  final VoidCallback onAddProduct, onReload;
  final ValueChanged<Map<String, dynamic>> onCreateBundle;
  final ValueChanged<String> onPeriod;
  final ValueChanged<int> onOrdersPage;
  final String sellerFirstName;
  final bool homeHighlightsOnly;
  final bool productSearchOpen;
  final Future<void> Function(int, String)? onOrderProgress;

  @override
  State<SellerWorkspaceContent> createState() => _SellerWorkspaceContentState();
}

class _SellerWorkspaceContentState extends State<SellerWorkspaceContent> {
  static const _salesPeriods = {
    'day': 'Daily',
    '7': 'Weekly',
    'month': 'Monthly',
  };

  String _productSearch = '';
  String _productFilter = 'all';
  final _productSearchController = TextEditingController();

  @override
  void didUpdateWidget(covariant SellerWorkspaceContent oldWidget) {
    super.didUpdateWidget(oldWidget);
    if ((!widget.productSearchOpen && oldWidget.productSearchOpen) ||
        (oldWidget.destination != widget.destination &&
            widget.destination == SellerDestination.products)) {
      _productSearch = '';
      _productSearchController.clear();
    }
  }

  @override
  void dispose() {
    _productSearchController.dispose();
    super.dispose();
  }

  String _inventorySearch = '';
  String _inventoryFilter = 'all';

  String _orderSearch = '';
  String _orderFilter = 'all';
  bool _orderActionPending = false;

  Future<void> _advanceOrder(Map<String, dynamic> row, String action) async {
    if (_orderActionPending) return;
    final confirmed = await showDialog<bool>(
      context: context,
      builder: (dialogContext) => AlertDialog(
        title: Text(
          action == 'delivered'
              ? 'Confirm seller delivery'
              : 'Update fulfillment',
        ),
        content: Text(
          action == 'delivered'
              ? 'Confirm that you personally delivered this order. Payment remains unchanged; cancellation is unavailable after delivery.'
              : 'Record this fulfillment step for your order?',
        ),
        actions: [
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, false),
            child: const Text('Cancel'),
          ),
          TextButton(
            onPressed: () => Navigator.pop(dialogContext, true),
            child: const Text('Confirm'),
          ),
        ],
      ),
    );
    if (confirmed != true || !mounted) return;
    setState(() => _orderActionPending = true);
    try {
      final id = int.parse('${row['id']}');
      if (widget.onOrderProgress != null) {
        await widget.onOrderProgress!(id, action);
      } else {
        await const SellerApplicationService().orderProgress(id, action);
      }
      if (!mounted) return;
      Navigator.of(context).pop();
      widget.onReload();
    } catch (error) {
      if (mounted) {
        ScaffoldMessenger.of(context).showSnackBar(
          SnackBar(
            content: Text(
              error is SellerApplicationException
                  ? error.message
                  : 'Unable to confirm progress. Refresh this order before retrying.',
            ),
          ),
        );
      }
    } finally {
      if (mounted) setState(() => _orderActionPending = false);
    }
  }

  Widget _orderProgressAction(Map<String, dynamic> row) {
    final status = '${row['status_key'] ?? ''}';
    final delivery = row['fulfillment_method'] == 'seller_delivery';
    final String? action = status == 'pending'
        ? 'start_processing'
        : status == 'processing'
        ? 'ready'
        : status == 'ready_for_pickup' &&
              delivery &&
              row['delivered_at'] == null
        ? (row['delivery_started_at'] == null ? 'start_delivery' : 'delivered')
        : null;
    if (action == null) return const SizedBox.shrink();
    final label = switch (action) {
      'start_processing' => 'Start Processing',
      'ready' => delivery ? 'Ready for Seller Delivery' : 'Ready for Pickup',
      'start_delivery' => 'Start Seller Delivery',
      _ => 'Confirm Delivered',
    };
    var pending = false;
    return StatefulBuilder(
      builder: (context, setLocalState) => TextButton(
        onPressed: pending
            ? null
            : () async {
                setLocalState(() => pending = true);
                await _advanceOrder(row, action);
                if (context.mounted) setLocalState(() => pending = false);
              },
        child: Text(label),
      ),
    );
  }

  static const actionText = TextStyle(
    fontFamily: 'Poppins',
    fontSize: 12,
    fontWeight: FontWeight.w600,
  );
  ButtonStyle get actionStyle => TextButton.styleFrom(
    textStyle: actionText,
    minimumSize: const Size(48, 48),
  );

  List<Map<String, dynamic>> rows(String key) => maps(widget.data[key]);
  static List<Map<String, dynamic>> maps(dynamic value) => value is List
      ? value
            .whereType<Map>()
            .map((row) => Map<String, dynamic>.from(row))
            .toList()
      : [];
  Map<String, dynamic> get analytics =>
      Map<String, dynamic>.from(widget.data['analytics'] as Map);
  Map<String, dynamic> get recommendations =>
      Map<String, dynamic>.from(widget.data['recommendations'] as Map);

  String money(dynamic amount) {
    if ('$amount'.startsWith('₱')) return '$amount';
    final number = double.tryParse('$amount');
    if (number == null) return 'Not recorded';
    final parts = number.toStringAsFixed(2).split('.');
    final whole = parts[0].replaceAllMapped(
      RegExp(r'(\d{1,3})(?=(\d{3})+(?!\d))'),
      (Match m) => '${m[1]},',
    );
    return '₱$whole.${parts[1]}';
  }

  String quantity(dynamic value) => value == null ? '—' : '$value';

  String date(dynamic raw) {
    final value = DateTime.tryParse('$raw')?.toLocal();
    if (value == null) return 'Not recorded';
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
    return '${months[value.month - 1]} ${value.day}, ${value.year}';
  }

  Widget heading(String title) => Padding(
    padding: const EdgeInsets.only(top: 20, bottom: 12),
    child: Text(title, style: ProfileStyle.text(16, weight: 700)),
  );

  Widget message(String text) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 20),
    child: Text(
      text,
      style: ProfileStyle.text(13, color: ProfileStyle.secondary),
    ),
  );

  Widget line(String label, dynamic value) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 5),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Expanded(
          child: Text(
            label,
            style: ProfileStyle.text(12, color: ProfileStyle.secondary),
          ),
        ),
        const SizedBox(width: 12),
        Flexible(
          child: Text(
            '$value',
            textAlign: TextAlign.right,
            style: ProfileStyle.text(13, weight: 600),
          ),
        ),
      ],
    ),
  );

  Widget card({
    String? title,
    String? subtitle,
    Widget? child,
    VoidCallback? onTap,
  }) => Padding(
    padding: const EdgeInsets.only(bottom: 12),
    child: Material(
      color: Colors.white,
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: HomeAppColors.border),
      ),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(16),
          child: Column(
            crossAxisAlignment: CrossAxisAlignment.stretch,
            children: [
              if (title != null)
                Text(title, style: ProfileStyle.text(14, weight: 700)),
              if (subtitle != null && subtitle.isNotEmpty) ...[
                const SizedBox(height: 4),
                Text(
                  subtitle,
                  style: ProfileStyle.text(12, color: ProfileStyle.secondary),
                ),
              ],
              if (child != null) ...[const SizedBox(height: 12), child],
            ],
          ),
        ),
      ),
    ),
  );

  void detail(BuildContext context, String title, List<Widget> children) {
    Navigator.push(
      context,
      MaterialPageRoute<void>(
        builder: (_) => ProfileDetailScaffold(
          title: title,
          child: ListView(
            padding: const EdgeInsets.all(20),
            children: children,
          ),
        ),
      ),
    );
  }

  String approval(Map<String, dynamic> product) =>
      product['is_archived'] == true
      ? 'Archived'
      : switch (product['approval_status']) {
          'approved' => 'Approved',
          'rejected' => 'Rejected',
          'archived' => 'Archived',
          _ => 'Pending Review',
        };

  Widget searchField(
    String hint,
    String currentVal,
    ValueChanged<String> onChanged, {
    TextEditingController? controller,
    bool autofocus = false,
  }) => Padding(
    padding: const EdgeInsets.only(bottom: 12),
    child: TextField(
      controller:
          controller ??
          (TextEditingController(text: currentVal)
            ..selection = TextSelection.collapsed(offset: currentVal.length)),
      autofocus: autofocus,
      style: const TextStyle(fontFamily: 'Poppins', fontSize: 13),
      decoration: InputDecoration(
        hintText: hint,
        hintStyle: const TextStyle(
          fontFamily: 'Poppins',
          fontSize: 13,
          color: HomeAppColors.secondaryText,
        ),
        prefixIcon: const Icon(
          Icons.search_rounded,
          size: 20,
          color: HomeAppColors.secondaryText,
        ),
        contentPadding: const EdgeInsets.symmetric(
          horizontal: 14,
          vertical: 10,
        ),
        filled: true,
        fillColor: Colors.white,
        border: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: HomeAppColors.border),
        ),
        enabledBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: HomeAppColors.border),
        ),
        focusedBorder: OutlineInputBorder(
          borderRadius: BorderRadius.circular(10),
          borderSide: const BorderSide(color: HomeAppColors.navy),
        ),
      ),
      onChanged: onChanged,
    ),
  );

  Widget filterChips({
    required List<(String label, String value)> options,
    required String selected,
    required ValueChanged<String> onSelected,
    bool solidSelected = false,
  }) => SingleChildScrollView(
    scrollDirection: Axis.horizontal,
    padding: const EdgeInsets.only(bottom: 14),
    child: Row(
      children: [
        for (final (label, val) in options) ...[
          Padding(
            padding: EdgeInsets.only(right: solidSelected ? 6 : 8),
            child: ChoiceChip(
              label: Text(label),
              padding: solidSelected ? EdgeInsets.zero : null,
              labelPadding: solidSelected
                  ? const EdgeInsets.symmetric(horizontal: 8)
                  : null,
              selected: selected == val,
              onSelected: (_) => onSelected(val),
              showCheckmark: solidSelected ? false : null,
              selectedColor: solidSelected
                  ? HomeAppColors.navy
                  : HomeAppColors.navy.withValues(alpha: 0.12),
              backgroundColor: Colors.white,
              labelStyle: TextStyle(
                fontFamily: 'Poppins',
                fontSize: 12,
                fontWeight: selected == val ? FontWeight.w600 : FontWeight.w500,
                color: selected == val && solidSelected
                    ? Colors.white
                    : selected == val
                    ? HomeAppColors.navy
                    : HomeAppColors.secondaryText,
              ),
              side: BorderSide(
                color: selected == val
                    ? HomeAppColors.navy
                    : HomeAppColors.border,
              ),
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(20),
              ),
            ),
          ),
        ],
      ],
    ),
  );

  void _showProductDetails(
    BuildContext context,
    Map<String, dynamic> product,
  ) => detail(context, '${product['name']}', [
    line('Approval Status', approval(product)),
    line('Category', product['category']),
    line('Price', product['price_display'] ?? money(product['price'])),
    line('Available', quantity(product['stock'])),
    if (product['product_type'] == 'bundle') ...[
      heading('Bundle Components'),
      for (final component in maps((product['bundle'] as Map?)?['components']))
        card(
          title: '${component['product_name']}',
          child: line('Required quantity', component['required_quantity']),
        ),
    ],
    if ('${product['description'] ?? ''}'.isNotEmpty) ...[
      heading('Description'),
      Text('${product['description']}'),
    ],
  ]);

  String _productStatus(Map<String, dynamic> product) =>
      product['is_archived'] == true
      ? 'archived'
      : '${product['approval_status'] ?? 'pending'}'.toLowerCase();

  Widget _productRow(BuildContext context, Map<String, dynamic> product) {
    final bundle = product['product_type'] == 'bundle';
    final variants = int.tryParse('${product['variant_count']}') ?? 0;
    return Container(
      key: ValueKey('seller-product-${product['id']}'),
      margin: const EdgeInsets.only(bottom: 8),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: HomeAppColors.border),
      ),
      child: Material(
        color: Colors.transparent,
        borderRadius: BorderRadius.circular(12),
        clipBehavior: Clip.antiAlias,
        child: Stack(
          children: [
            InkWell(
              onTap: () => _showProductDetails(context, product),
              child: Padding(
                padding: const EdgeInsets.all(12),
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.start,
                  children: [
                    ClipRRect(
                      borderRadius: BorderRadius.circular(8),
                      child: SizedBox.square(
                        dimension: 76,
                        child: ProductImage(
                          imageUrl: '${product['image_url'] ?? ''}',
                          fallbackIcon: Iconsax.box_1_copy,
                          fallbackColor: HomeAppColors.navy,
                          fallbackSize: 24,
                          backgroundColor: HomeAppColors.appBackground,
                        ),
                      ),
                    ),
                    const SizedBox(width: 12),
                    Expanded(
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Padding(
                            padding: const EdgeInsets.only(right: 28),
                            child: Text(
                              '${product['name']}',
                              maxLines: 2,
                              overflow: TextOverflow.ellipsis,
                              style: ProfileStyle.text(14, weight: 600),
                            ),
                          ),
                          const SizedBox(height: 3),
                          Padding(
                            padding: const EdgeInsets.only(right: 24),
                            child: Text(
                              '${product['category'] ?? ''} · ${bundle ? 'Bundle Product' : 'Single Product'}',
                              style: ProfileStyle.text(
                                12,
                                color: HomeAppColors.secondaryText,
                              ),
                            ),
                          ),
                          const SizedBox(height: 6),
                          Container(
                            padding: const EdgeInsets.symmetric(
                              horizontal: 7,
                              vertical: 3,
                            ),
                            decoration: BoxDecoration(
                              color: _productStatus(product) == 'pending'
                                  ? HomeAppColors.gold.withValues(alpha: .18)
                                  : HomeAppColors.navy.withValues(alpha: .06),
                              borderRadius: BorderRadius.circular(5),
                            ),
                            child: Text(
                              approval(product),
                              style: ProfileStyle.text(11, weight: 500),
                            ),
                          ),
                          const SizedBox(height: 8),
                          SizedBox(
                            width: double.infinity,
                            child: Wrap(
                              alignment: WrapAlignment.spaceBetween,
                              spacing: 12,
                              runSpacing: 4,
                              children: [
                                Text(
                                  '${product['price_display'] ?? money(product['price'])}',
                                  style: ProfileStyle.text(13, weight: 700),
                                ),
                                Column(
                                  crossAxisAlignment: CrossAxisAlignment.end,
                                  children: [
                                    Text(
                                      '${quantity(product['stock'])} ${bundle ? 'bundles' : 'pcs'}',
                                      style: ProfileStyle.text(12, weight: 600),
                                    ),
                                    if (variants > 0)
                                      Text(
                                        '$variants variants',
                                        style: ProfileStyle.text(
                                          11,
                                          color: HomeAppColors.secondaryText,
                                        ),
                                      ),
                                    if (product['quantity_status'] ==
                                            'low_stock' ||
                                        product['quantity_status'] ==
                                            'out_of_stock')
                                      Text(
                                        product['quantity_status'] ==
                                                'low_stock'
                                            ? 'Low Stock'
                                            : 'Out of Stock',
                                        style: ProfileStyle.text(
                                          11,
                                          weight: 500,
                                        ),
                                      ),
                                  ],
                                ),
                              ],
                            ),
                          ),
                        ],
                      ),
                    ),
                  ],
                ),
              ),
            ),
            Positioned(
              top: 0,
              right: 0,
              child: PopupMenuButton<String>(
                tooltip: 'Product actions',
                color: Colors.white,
                surfaceTintColor: Colors.transparent,
                icon: const RotatedBox(
                  quarterTurns: 1,
                  child: Icon(
                    Iconsax.more_copy,
                    size: 18,
                    color: HomeAppColors.navy,
                  ),
                ),
                onSelected: (action) {
                  if (action == 'view') {
                    _showProductDetails(context, product);
                  } else {
                    widget.onNavigate(SellerDestination.inventory);
                  }
                },
                itemBuilder: (_) => const [
                  PopupMenuItem(value: 'view', child: Text('View Details')),
                  PopupMenuItem(
                    value: 'inventory',
                    child: Text('View Inventory'),
                  ),
                ],
              ),
            ),
          ],
        ),
      ),
    );
  }

  Widget _myProducts(BuildContext context) => Column(
    crossAxisAlignment: CrossAxisAlignment.stretch,
    children: [
      Padding(
        padding: const EdgeInsets.fromLTRB(4, 4, 16, 0),
        child: Row(
          children: [
            IconButton(
              tooltip: 'Back to Dashboard',
              onPressed: () => widget.onNavigate(SellerDestination.overview),
              icon: const Icon(
                Iconsax.arrow_left_2_copy,
                size: 20,
                color: HomeAppColors.navy,
              ),
            ),
            Expanded(
              child: Semantics(
                header: true,
                child: Text(
                  'My Products',
                  style: ProfileStyle.text(18, weight: 700),
                ),
              ),
            ),
            const SizedBox(width: 8),
            PopupMenuButton<String>(
              key: const ValueKey('seller-add-product'),
              tooltip: 'Add product',
              color: Colors.white,
              surfaceTintColor: Colors.transparent,
              onSelected: (action) {
                if (action == 'single') {
                  widget.onAddProduct();
                } else {
                  widget.onNavigate(SellerDestination.recommendations);
                }
              },
              itemBuilder: (_) => const [
                PopupMenuItem(
                  value: 'single',
                  child: Text('Add Single Product'),
                ),
                PopupMenuItem(
                  value: 'bundle',
                  child: Text('Create Bundle Product'),
                ),
              ],
              child: Container(
                constraints: const BoxConstraints(minHeight: 48),
                padding: const EdgeInsets.symmetric(horizontal: 12),
                decoration: BoxDecoration(
                  color: HomeAppColors.navy,
                  borderRadius: BorderRadius.circular(9),
                ),
                child: Row(
                  mainAxisSize: MainAxisSize.min,
                  children: [
                    const Icon(Iconsax.add_copy, size: 16, color: Colors.white),
                    const SizedBox(width: 6),
                    Text(
                      'Add',
                      style: ProfileStyle.text(
                        12,
                        weight: 600,
                        color: Colors.white,
                      ),
                    ),
                  ],
                ),
              ),
            ),
          ],
        ),
      ),
      Padding(
        padding: const EdgeInsets.fromLTRB(16, 8, 16, 0),
        child: Column(
          children: [
            if (widget.productSearchOpen)
              searchField(
                'Search my products',
                _productSearch,
                (value) => setState(() => _productSearch = value),
                controller: _productSearchController,
                autofocus: true,
              ),
            filterChips(
              solidSelected: true,
              options: const [
                ('All', 'all'),
                ('Single', 'single'),
                ('Bundles', 'bundle'),
                ('Pending', 'pending'),
                ('Approved', 'approved'),
                ('Rejected', 'rejected'),
                ('Archived', 'archived'),
              ],
              selected: _productFilter,
              onSelected: (value) => setState(() => _productFilter = value),
            ),
          ],
        ),
      ),
      Expanded(
        child: ListView(
          key: const PageStorageKey('seller-products'),
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
          children: productList(context),
        ),
      ),
    ],
  );

  List<Widget> productList(BuildContext context, {bool bundles = false}) {
    var products = rows(
      'products',
    ).where((row) => !bundles || row['product_type'] == 'bundle').toList();
    if (_productSearch.trim().isNotEmpty) {
      final query = _productSearch.trim().toLowerCase();
      products = products
          .where(
            (product) =>
                '${product['name']}'.toLowerCase().contains(query) ||
                '${product['category']}'.toLowerCase().contains(query),
          )
          .toList();
    }
    if (!bundles && _productFilter != 'all') {
      products = products
          .where(
            (product) => switch (_productFilter) {
              'single' => product['product_type'] != 'bundle',
              'bundle' => product['product_type'] == 'bundle',
              _ => _productStatus(product) == _productFilter,
            },
          )
          .toList();
    }
    return [
      if (bundles)
        Row(
          children: [
            Expanded(
              child: searchField(
                'Search bundles...',
                _productSearch,
                (value) => setState(() => _productSearch = value),
                controller: _productSearchController,
              ),
            ),
            const SizedBox(width: 8),
            Padding(
              padding: const EdgeInsets.only(bottom: 12),
              child: FilledButton.icon(
                key: const ValueKey('seller-create-bundle'),
                onPressed: () =>
                    widget.onNavigate(SellerDestination.recommendations),
                icon: const Icon(Icons.add_rounded, size: 18),
                label: const Text('Create Bundle'),
                style: FilledButton.styleFrom(
                  textStyle: actionText,
                  minimumSize: const Size(48, 48),
                  backgroundColor: HomeAppColors.navy,
                  foregroundColor: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(10),
                  ),
                ),
              ),
            ),
          ],
        ),
      if (products.isEmpty)
        if (bundles)
          message('No bundles yet.')
        else if (rows('products').isEmpty)
          message(
            'No products yet. Add a product to submit it for marketplace approval.',
          )
        else
          Padding(
            padding: const EdgeInsets.symmetric(vertical: 24),
            child: Column(
              crossAxisAlignment: CrossAxisAlignment.start,
              children: [
                Text(
                  'No matching products',
                  style: ProfileStyle.text(14, weight: 600),
                ),
                const SizedBox(height: 6),
                Text(
                  'Try another search or filter.',
                  style: ProfileStyle.text(
                    12,
                    color: HomeAppColors.secondaryText,
                  ),
                ),
                TextButton(
                  onPressed: () => setState(() {
                    _productSearch = '';
                    _productSearchController.clear();
                    _productFilter = 'all';
                  }),
                  child: const Text('Clear search and filters'),
                ),
              ],
            ),
          ),
      for (final product in products)
        if (!bundles)
          _productRow(context, product)
        else
          card(
            title: '${product['name']}',
            subtitle: '${product['category']} · ${approval(product)}',
            child: Column(
              children: [
                line(
                  'Price',
                  product['price_display'] ?? money(product['price']),
                ),
                line(
                  'Derived Availability',
                  '${quantity(product['stock'])} bundles',
                ),
              ],
            ),
            onTap: () => _showProductDetails(context, product),
          ),
    ];
  }

  Widget _inventorySummary(List<Map<String, dynamic>> all) {
    final total = all.length;
    final lowStock = all.where((i) => i['status'] == 'low_stock').length;
    final outOfStock = all.where((i) => i['status'] == 'out_of_stock').length;
    return Container(
      margin: const EdgeInsets.only(bottom: 14),
      padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: HomeAppColors.border),
      ),
      child: Row(
        mainAxisAlignment: MainAxisAlignment.spaceAround,
        children: [
          _statItem('Total Items', '$total'),
          _statDivider(),
          _statItem('Low Stock', '$lowStock'),
          _statDivider(),
          _statItem('Out of Stock', '$outOfStock'),
        ],
      ),
    );
  }

  Widget _statItem(String label, String value) => Column(
    children: [
      Text(label, style: ProfileStyle.text(11, color: ProfileStyle.secondary)),
      const SizedBox(height: 2),
      Text(value, style: ProfileStyle.text(16, weight: 700)),
    ],
  );

  Widget _statDivider() =>
      Container(height: 24, width: 1, color: HomeAppColors.border);

  List<Widget> inventory({bool attention = false}) {
    final allItems = rows('inventory');
    var items = allItems
        .where(
          (row) =>
              !attention ||
              ['low_stock', 'out_of_stock', 'expired'].contains(row['status']),
        )
        .toList();

    if (!attention && _inventorySearch.trim().isNotEmpty) {
      final q = _inventorySearch.trim().toLowerCase();
      items = items
          .where(
            (i) =>
                '${i['product_name']}'.toLowerCase().contains(q) ||
                '${i['sku']}'.toLowerCase().contains(q),
          )
          .toList();
    }
    if (!attention && _inventoryFilter != 'all') {
      items = items
          .where((i) => '${i['status']}'.toLowerCase() == _inventoryFilter)
          .toList();
    }

    return [
      if (!attention) ...[
        _inventorySummary(allItems),
        searchField('Search inventory by name or SKU...', _inventorySearch, (
          v,
        ) {
          setState(() => _inventorySearch = v);
        }),
        filterChips(
          options: const [
            ('All', 'all'),
            ('Low Stock', 'low_stock'),
            ('Out of Stock', 'out_of_stock'),
          ],
          selected: _inventoryFilter,
          onSelected: (v) => setState(() => _inventoryFilter = v),
        ),
      ],
      if (items.isEmpty)
        message(
          attention && allItems.isNotEmpty
              ? 'Inventory levels are currently healthy.'
              : 'No inventory records yet.',
        ),
      for (final row in attention ? items.take(3) : items)
        card(
          title: '${row['product_name']}',
          subtitle:
              '${'${row['name'] ?? ''}'.isEmpty ? 'Single Product' : row['name']} · SKU: ${row['sku']}',
          child: Column(
            children: [
              line('On Hand', quantity(row['on_hand'])),
              line('Reserved', quantity(row['reserved'])),
              line(
                row['derived'] == true ? 'Available Bundles' : 'Available',
                quantity(row['available']),
              ),
              line('Threshold', quantity(row['threshold'])),
              line('Status', row['status_label']),
            ],
          ),
        ),
    ];
  }

  List<Widget> orders(BuildContext context, {bool preview = false}) {
    final page = (widget.data['orders_page'] as num?)?.toInt() ?? 1;
    final pages = (widget.data['orders_pages'] as num?)?.toInt() ?? 1;
    var orderList = rows('orders');

    if (!preview && _orderSearch.trim().isNotEmpty) {
      final q = _orderSearch.trim().toLowerCase();
      orderList = orderList
          .where(
            (o) =>
                '${o['code']}'.toLowerCase().contains(q) ||
                '${o['buyer_name']}'.toLowerCase().contains(q) ||
                '${o['product_name']}'.toLowerCase().contains(q),
          )
          .toList();
    }
    if (!preview && _orderFilter != 'all') {
      orderList = orderList
          .where(
            (o) =>
                '${o['status_key'] ?? o['status']}'.toLowerCase().replaceAll(
                  ' ',
                  '_',
                ) ==
                _orderFilter,
          )
          .toList();
    }

    return [
      if (!preview) ...[
        searchField('Search orders by code or customer...', _orderSearch, (v) {
          setState(() => _orderSearch = v);
        }),
        filterChips(
          options: const [
            ('All', 'all'),
            ('Pending', 'pending'),
            ('Processing', 'processing'),
            ('Ready', 'ready_for_pickup'),
            ('Completed', 'completed'),
            ('Cancelled', 'cancelled'),
          ],
          selected: _orderFilter,
          onSelected: (v) => setState(() => _orderFilter = v),
        ),
      ],
      if (orderList.isEmpty) message('No orders yet.'),
      for (final row in preview ? orderList.take(3) : orderList)
        card(
          title: '${row['code']}',
          subtitle: '${row['product_name']} · ${row['status']}',
          child: Column(
            children: [
              line('Quantity', row['quantity']),
              line('Total', money(row['total'])),
              line('Payment', row['payment_status']),
              line('Fulfillment', row['fulfillment_label'] ?? 'Not recorded'),
              line('Placed', date(row['created_at'])),
            ],
          ),
          onTap: () => detail(context, 'Order ${row['code']}', [
            line(
              'Customer',
              '${row['buyer_name']}'.isEmpty
                  ? 'Not recorded'
                  : row['buyer_name'],
            ),
            line('Order Status', row['status']),
            line('Payment Status', row['payment_status']),
            line(
              'Fulfillment Method',
              row['fulfillment_label'] ?? 'Not recorded',
            ),
            line(
              'Fulfillment Progress',
              row['fulfillment_progress'] ?? row['status'],
            ),
            if (row['fulfillment_method'] == 'seller_delivery') ...[
              line('Delivery Destination', row['delivery_destination']),
              line('Seller Delivery Started', date(row['delivery_started_at'])),
              line('Delivered', date(row['delivered_at'])),
            ],
            line(
              'Payment Method',
              row['fulfillment_method'] == 'seller_delivery'
                  ? 'Cash — recorded separately'
                  : 'Cash on Pickup',
            ),
            line('Total', money(row['total'])),
            if (row['fulfillment_method'] != 'seller_delivery')
              line(
                'Pickup Location',
                '${row['pickup_location']}'.isEmpty
                    ? 'Not recorded'
                    : row['pickup_location'],
              ),
            heading('Items'),
            for (final item in maps(row['items']))
              card(
                title: '${item['product_name']}',
                child: Column(
                  children: [
                    line('Quantity', item['quantity']),
                    line('Subtotal', money(item['subtotal'])),
                  ],
                ),
              ),
            _orderProgressAction(row),
          ]),
        ),
      if (!preview && pages > 1)
        Row(
          mainAxisAlignment: MainAxisAlignment.center,
          children: [
            IconButton(
              tooltip: 'Previous orders page',
              onPressed: page > 1 ? () => widget.onOrdersPage(page - 1) : null,
              icon: const Icon(Icons.chevron_left_rounded),
            ),
            Text('$page / $pages'),
            IconButton(
              tooltip: 'Next orders page',
              onPressed: page < pages
                  ? () => widget.onOrdersPage(page + 1)
                  : null,
              icon: const Icon(Icons.chevron_right_rounded),
            ),
          ],
        ),
    ];
  }

  Widget pair(BuildContext context, Map<String, dynamic> row) {
    final products = maps(row['products']);
    final title = products.map((product) => product['name']).join(' + ');
    return card(
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.stretch,
        children: [
          Row(
            crossAxisAlignment: CrossAxisAlignment.start,
            children: [
              for (var i = 0; i < products.length; i++) ...[
                if (i > 0)
                  const Padding(
                    padding: EdgeInsets.symmetric(horizontal: 12, vertical: 20),
                    child: Icon(Icons.add_rounded, size: 18),
                  ),
                Expanded(
                  child: Column(
                    children: [
                      SizedBox(
                        height: 60,
                        child: ProductImage(
                          imageUrl: '${products[i]['image_url'] ?? ''}',
                          fallbackIcon: Icons.inventory_2_outlined,
                          fallbackColor: HomeAppColors.navy,
                          backgroundColor: Colors.white,
                        ),
                      ),
                      const SizedBox(height: 8),
                      Text(
                        '${products[i]['name']}',
                        textAlign: TextAlign.center,
                        style: ProfileStyle.text(12, weight: 600),
                      ),
                    ],
                  ),
                ),
              ],
            ],
          ),
          const SizedBox(height: 12),
          Wrap(
            spacing: 8,
            children: [
              TextButton(
                style: actionStyle,
                onPressed: () => detail(context, 'Bundle Suggestion', [
                  Text(title, style: ProfileStyle.text(16, weight: 700)),
                  const SizedBox(height: 12),
                  for (final product in products)
                    line('Product', product['name']),
                  line('Seller', row['seller']),
                ]),
                child: const Text('View Suggestion'),
              ),
              OutlinedButton(
                onPressed: () => widget.onCreateBundle(row),
                child: const Text('Create Bundle'),
              ),
            ],
          ),
        ],
      ),
    );
  }

  List<Widget> suggestions(BuildContext context, {bool preview = false}) {
    final ownedIds = rows('products').map((p) => '${p['id']}').toSet();
    final list = maps(recommendations['rows']).where((row) {
      final pair = maps(row['products']);
      return pair.length == 2 &&
          pair.every((p) => ownedIds.contains('${p['id']}'));
    }).toList();
    return [
      if (list.isEmpty) ...[
        message('No bundle suggestions available yet.'),
        Text(
          'Suggestions will appear after sufficient completed marketplace transactions are recorded.',
          style: ProfileStyle.text(12, color: ProfileStyle.secondary),
        ),
      ] else ...[
        for (final row in preview ? list.take(3) : list) pair(context, row),
      ],
    ];
  }

  List<Widget> homeHighlights(BuildContext context) => [
    Row(
      key: const ValueKey('seller-sales-overview-header'),
      children: [
        Expanded(
          child: Text(
            'Sales Overview',
            style: ProfileStyle.text(16, weight: 700),
          ),
        ),
        const SizedBox(width: 8),
        salesPeriod(compact: true),
      ],
    ),
    const SizedBox(height: 12),
    LayoutBuilder(
      builder: (context, constraints) {
        final columns = MediaQuery.textScalerOf(context).scale(14) > 21 ? 1 : 2;
        final overview = widget.data['overview'] is Map
            ? widget.data['overview'] as Map
            : const {};
        final entries = <_SellerOverviewMetric>[
          _SellerOverviewMetric(
            title: 'Total Sales',
            value: money(analytics['revenue']),
            icon: Iconsax.wallet_2_copy,
          ),
          _SellerOverviewMetric(
            title: 'Total Orders',
            value: '${widget.data['order_count'] ?? 0}',
            icon: Iconsax.bag_2_copy,
          ),
          _SellerOverviewMetric(
            title: 'Completed Orders',
            value:
                '${overview['completed_orders'] ?? analytics['completed_orders'] ?? 0}',
            icon: Iconsax.tick_circle_copy,
          ),
          _SellerOverviewMetric(
            title: 'Pending Orders',
            value: '${overview['pending_orders'] ?? 0}',
            icon: Iconsax.clock_copy,
          ),
        ];
        return Column(
          children: [
            for (var i = 0; i < entries.length; i += columns) ...[
              if (i > 0) const SizedBox(height: 12),
              IntrinsicHeight(
                child: Row(
                  crossAxisAlignment: CrossAxisAlignment.stretch,
                  children: [
                    for (
                      var j = i;
                      j < i + columns && j < entries.length;
                      j++
                    ) ...[
                      if (j > i) const SizedBox(width: 12),
                      Expanded(child: _overviewMetricCard(entries[j])),
                    ],
                  ],
                ),
              ),
            ],
          ],
        );
      },
    ),
    sectionHeader(
      'Suggested Product Bundles',
      SellerDestination.recommendations,
    ),
    ...suggestions(context, preview: true),
    const SizedBox(height: 20),
    card(
      title: 'Sales Trend',
      child: SellerSalesTrend(
        trend: analytics['trend'] is Map ? analytics['trend'] as Map : const {},
      ),
    ),
    sectionHeader('Inventory Attention', SellerDestination.inventory),
    ...inventory(attention: true),
    sectionHeader('Recent Orders', SellerDestination.orders),
    ...orders(context, preview: true),
  ];

  Widget _overviewMetricCard(_SellerOverviewMetric metric) => Container(
    padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 14),
    decoration: BoxDecoration(
      color: Colors.white,
      borderRadius: BorderRadius.circular(16),
      border: Border.all(color: HomeAppColors.border),
    ),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      mainAxisAlignment: MainAxisAlignment.spaceBetween,
      children: [
        Row(
          mainAxisAlignment: MainAxisAlignment.spaceBetween,
          crossAxisAlignment: CrossAxisAlignment.center,
          children: [
            Expanded(
              child: Text(
                metric.title,
                maxLines: 1,
                overflow: TextOverflow.ellipsis,
                style: ProfileStyle.text(
                  13,
                  weight: 500,
                  color: HomeAppColors.secondaryText,
                ),
              ),
            ),
            const SizedBox(width: 8),
            Icon(metric.icon, size: 20, color: HomeAppColors.navy),
          ],
        ),
        const SizedBox(height: 14),
        Text(
          metric.value,
          style: ProfileStyle.text(22, weight: 700, color: HomeAppColors.navy),
        ),
      ],
    ),
  );

  List<Widget> overview(BuildContext context) => [
    Text(
      widget.sellerFirstName.trim().isEmpty
          ? 'Welcome back!'
          : 'Welcome back, ${widget.sellerFirstName.trim()}!',
      style: ProfileStyle.text(15, weight: 600),
    ),
    ...homeHighlights(context),
  ];

  Widget sectionHeader(String title, SellerDestination destination) => Padding(
    key: ValueKey('seller-section-${destination.name}'),
    padding: const EdgeInsets.only(top: 16, bottom: 4),
    child: Row(
      children: [
        Expanded(child: Text(title, style: ProfileStyle.text(16, weight: 700))),
        TextButton(
          style: actionStyle,
          onPressed: () => widget.onNavigate(destination),
          child: const Text('See All >'),
        ),
      ],
    ),
  );

  Widget salesPeriod({bool compact = false}) {
    if (compact) {
      return Semantics(
        value: _salesPeriods['${analytics['period']}'],
        child: PopupMenuButton<String>(
          tooltip: 'Filter sales period',
          initialValue: '${analytics['period']}',
          color: Colors.white,
          surfaceTintColor: Colors.transparent,
          onSelected: widget.onPeriod,
          itemBuilder: (_) => [
            for (final period in _salesPeriods.entries)
              CheckedPopupMenuItem<String>(
                value: period.key,
                checked: period.key == '${analytics['period']}',
                child: Text(
                  period.value,
                  style: ProfileStyle.text(13, weight: 500),
                ),
              ),
          ],
          child: Container(
            constraints: const BoxConstraints(minHeight: 48),
            padding: const EdgeInsets.symmetric(horizontal: 12),
            decoration: BoxDecoration(
              color: Colors.white,
              border: Border.all(color: HomeAppColors.border),
              borderRadius: BorderRadius.circular(12),
            ),
            child: Row(
              mainAxisSize: MainAxisSize.min,
              children: [
                Text(
                  _salesPeriods['${analytics['period']}'] ??
                      '${analytics['label']}',
                  style: ProfileStyle.text(12, weight: 500),
                ),
                const SizedBox(width: 6),
                const Icon(
                  Iconsax.arrow_down_1_copy,
                  size: 16,
                  color: HomeAppColors.navy,
                ),
              ],
            ),
          ),
        ),
      );
    }
    return DropdownButtonFormField<String>(
      isExpanded: true,
      style: ProfileStyle.text(13, weight: 500),
      initialValue: '${analytics['period']}',
      decoration: InputDecoration(
        labelText: 'Sales period',
        labelStyle: ProfileStyle.text(12, weight: 500),
        border: const OutlineInputBorder(),
      ),
      items: [
        for (final period in _salesPeriods.entries)
          DropdownMenuItem(value: period.key, child: Text(period.value)),
      ],
      onChanged: (value) {
        if (value != null) widget.onPeriod(value);
      },
    );
  }

  List<Widget> salesAnalytics() => [
    salesPeriod(),
    heading('Completed and Paid Orders'),
    line('Marketplace Sales', money(analytics['revenue'])),
    line('Completed Orders', analytics['completed_orders']),
    line('Units Sold', analytics['units_sold']),
    line('Average Order Value', money(analytics['average_order_value'])),
    heading('Top Selling Products'),
    if (maps(analytics['top_products']).isEmpty)
      message('No completed paid sales in this period.'),
    for (final row in maps(analytics['top_products']))
      card(
        title: '${row['product']}',
        child: Column(
          children: [
            line('Units Sold', row['units']),
            line('Sales', row['sales']),
          ],
        ),
      ),
    heading('Sales by Day'),
    for (
      var i = 0;
      i < ((analytics['trend'] as Map)['labels'] as List).length;
      i++
    )
      line(
        '${(analytics['trend'] as Map)['labels'][i]}',
        money((analytics['trend'] as Map)['sales'][i]),
      ),
  ];

  @override
  Widget build(BuildContext context) => widget.homeHighlightsOnly
      ? Column(
          crossAxisAlignment: CrossAxisAlignment.stretch,
          children: homeHighlights(context),
        )
      : widget.destination == SellerDestination.products
      ? _myProducts(context)
      : ListView(
          key: PageStorageKey('seller-${widget.destination.name}'),
          physics: const AlwaysScrollableScrollPhysics(),
          padding: const EdgeInsets.all(16),
          children: switch (widget.destination) {
            SellerDestination.overview => overview(context),
            SellerDestination.products => productList(context),
            SellerDestination.inventory => inventory(),
            SellerDestination.bundles => productList(context, bundles: true),
            SellerDestination.orders => orders(context),
            SellerDestination.recommendations => suggestions(context),
            SellerDestination.analytics => salesAnalytics(),
            _ => const <Widget>[],
          },
        );
}

class _SellerOverviewMetric {
  const _SellerOverviewMetric({
    required this.title,
    required this.value,
    required this.icon,
  });
  final String title;
  final String value;
  final IconData icon;
}
