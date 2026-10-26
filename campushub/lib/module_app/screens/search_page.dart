import 'package:flutter/material.dart';
import '../theme/app_typography.dart';

import '../models/facility_item.dart';
import '../models/product_item.dart';
import '../models/service_item.dart';
import '../services/facility_service.dart';
import '../services/product_service.dart';
import '../services/service_catalog.dart';
import '../widgets/home/home_preview_cards.dart';
import '../widgets/product_image.dart';
import 'facility_details_screen.dart';
import 'service_details_screen.dart';

enum SearchCategory {
  all('All'),
  products('Products'),
  facilities('Facilities'),
  services('Services');

  const SearchCategory(this.label);
  final String label;
}

/// Searches the same public catalogs as Home; never writes search/sample records.
class SearchPage extends StatefulWidget {
  const SearchPage({
    super.key,
    this.loadProducts = ProductService.fetchApproved,
    this.loadFacilities = FacilityService.fetchFacilities,
    this.loadRecommendations = ProductService.fetchSearchRecommendations,
    this.catalog = const ServiceCatalog(),
    this.initialProducts,
    this.initialFacilities,
    this.initialServices,
  });

  final Future<List<ProductItem>> Function() loadProducts;
  final Future<FacilityServiceResult> Function() loadFacilities;
  final Future<List<ProductItem>> Function() loadRecommendations;
  final ServiceCatalog catalog;
  final Future<List<ProductItem>>? initialProducts;
  final Future<List<FacilityItem>>? initialFacilities;
  final Future<List<ServiceItem>>? initialServices;

  @override
  State<SearchPage> createState() => _SearchPageState();
}

class _SearchPageState extends State<SearchPage> {
  final _query = TextEditingController();
  final _focus = FocusNode();
  late Future<List<ProductItem>> _products;
  late Future<List<FacilityItem>> _facilities;
  late Future<List<ServiceItem>> _services;
  late Future<List<ProductItem>> _recommendations;
  bool _submitted = false;
  SearchCategory _category = SearchCategory.all;

  Future<List<T>> _observe<T>(Future<List<T>> future) {
    // A section can be hidden while another catalog is still loading.
    future.ignore();
    return future;
  }

  Future<List<FacilityItem>> _readFacilities() async {
    final result = await widget.loadFacilities();
    if (!result.success) throw StateError('Facility catalog unavailable');
    return result.facilities.map(FacilityItem.fromJson).toList();
  }

  @override
  void initState() {
    super.initState();
    _products = _observe(widget.initialProducts ?? widget.loadProducts());
    _facilities = _observe(widget.initialFacilities ?? _readFacilities());
    _services = _observe(
      widget.initialServices ?? widget.catalog.fetchServices(),
    );
    _recommendations = _observe(widget.loadRecommendations());
  }

  @override
  void dispose() {
    _query.dispose();
    _focus.dispose();
    super.dispose();
  }

  bool _matches(String value) =>
      value.toLowerCase().contains(_query.text.trim().toLowerCase());

  void _submit() {
    if (_query.text.trim().isEmpty) return;
    _focus.unfocus();
    setState(() => _submitted = true);
  }

  Widget _heading(String text) => Padding(
    padding: const EdgeInsets.only(top: 24, bottom: 12),
    child: Text(
      text,
      style: const TextStyle(fontSize: 17, fontWeight: FontWeight.w700),
    ),
  );

  Widget _message(String text, {VoidCallback? retry}) => Padding(
    padding: const EdgeInsets.symmetric(vertical: 16),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Text(text, style: const TextStyle(height: 1.5)),
        if (retry != null)
          TextButton(onPressed: retry, child: const Text('Retry')),
      ],
    ),
  );

  Widget _catalog<T>({
    required Future<List<T>> future,
    required String name,
    required VoidCallback retry,
    required Widget Function(List<T>) builder,
  }) => FutureBuilder<List<T>>(
    future: future,
    builder: (context, snapshot) {
      if (snapshot.connectionState != ConnectionState.done) {
        return Padding(
          padding: const EdgeInsets.all(24),
          child: Center(
            child: SizedBox.square(
              dimension: 24,
              child: CircularProgressIndicator(
                strokeWidth: 2,
                color: HomeAppColors.navy,
                semanticsLabel: 'Loading $name',
              ),
            ),
          ),
        );
      }
      if (snapshot.hasError) {
        return _message(
          'Unable to load $name. Check your connection and retry.',
          retry: retry,
        );
      }
      return builder(snapshot.data ?? <T>[]);
    },
  );

  Widget _tile({
    required String name,
    required String detail,
    required String image,
    required IconData icon,
    required VoidCallback onTap,
  }) => Padding(
    padding: const EdgeInsets.only(bottom: 8),
    child: Material(
      color: Colors.white,
      borderRadius: BorderRadius.circular(12),
      clipBehavior: Clip.antiAlias,
      child: InkWell(
        onTap: onTap,
        child: Padding(
          padding: const EdgeInsets.all(12),
          child: Row(
            children: [
              ClipRRect(
                borderRadius: BorderRadius.circular(8),
                child: SizedBox.square(
                  dimension: 52,
                  child: ProductImage(
                    imageUrl: image,
                    fallbackIcon: icon,
                    fallbackColor: HomeAppColors.navy,
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
                      name,
                      style: const TextStyle(
                        fontWeight: FontWeight.w600,
                        height: 1.4,
                      ),
                    ),
                    if (detail.isNotEmpty) ...[
                      const SizedBox(height: 4),
                      Text(
                        detail,
                        style: const TextStyle(fontSize: 12, height: 1.4),
                      ),
                    ],
                  ],
                ),
              ),
              const SizedBox(width: 8),
              const Icon(Icons.chevron_right_rounded, size: 20),
            ],
          ),
        ),
      ),
    ),
  );

  Widget _productTile(ProductItem row) => _tile(
    name: row.name,
    detail: row.price,
    image: row.imageUrl,
    icon: row.icon,
    onTap: () => openMarketplaceProduct(context, row),
  );

  Widget _productCards(List<ProductItem> rows) => LayoutBuilder(
    builder: (context, constraints) {
      final scale = MediaQuery.textScalerOf(context);
      final columns = constraints.maxWidth < 300 || scale.scale(14) > 20
          ? 1
          : (constraints.maxWidth >= 700 ? 3 : 2);
      final width = (constraints.maxWidth - (columns - 1) * 12) / columns;
      final height =
          180 +
          scale.scale(14) * 2.5 +
          scale.scale(15) * 1.5 +
          scale.scale(11) * 3;
      return Wrap(
        spacing: 12,
        runSpacing: 12,
        children: [
          for (final row in rows)
            SizedBox(
              width: width,
              height: height,
              child: MarketplacePreviewCard(product: row, width: width),
            ),
        ],
      );
    },
  );

  Widget _productContent(List<ProductItem> rows) {
    if (_query.text.trim().isNotEmpty) {
      final matches = rows
          .where(
            (row) => _matches(
              '${row.name} ${row.seller} ${row.category} ${row.description}',
            ),
          )
          .toList();
      if (matches.isEmpty) {
        return _message(
          _submitted
              ? 'No matching products. Try another name or category.'
              : 'No matching product suggestions. Submit your search to check facilities and services.',
        );
      }
      return Column(children: [for (final row in matches) _productTile(row)]);
    }
    final recent = [...rows]
      ..sort(
        (a, b) => (b.submittedAt ?? DateTime.fromMillisecondsSinceEpoch(0))
            .compareTo(a.submittedAt ?? DateTime.fromMillisecondsSinceEpoch(0)),
      );
    return Column(
      crossAxisAlignment: CrossAxisAlignment.stretch,
      children: [
        FutureBuilder<List<ProductItem>>(
          future: _recommendations,
          builder: (context, snapshot) {
            // Rejoin to the current public catalog: never show stale/unapproved records.
            final eligible = {
              for (final row in rows)
                if (row.id != null) row.id: row,
            };
            final recommendations = (snapshot.data ?? <ProductItem>[])
                .map((row) => eligible[row.id])
                .whereType<ProductItem>()
                .toList();
            final personal = recommendations.isNotEmpty;
            return Column(
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                _heading(
                  personal ? 'Recommended for You' : 'Recently Added Products',
                ),
                if (recent.isEmpty)
                  _message('No products are currently available.')
                else
                  _productCards(
                    (personal ? recommendations : recent).take(4).toList(),
                  ),
              ],
            );
          },
        ),
        _heading('Explore Available Products'),
        if (rows.isEmpty)
          _message('No products are currently available.')
        else
          _productCards(rows),
      ],
    );
  }

  @override
  Widget build(BuildContext context) {
    final theme = Theme.of(context);
    final searching = _query.text.trim().isNotEmpty;
    return Theme(
      data: theme.copyWith(
        iconTheme: const IconThemeData(color: HomeAppColors.navy),
        textTheme: AppTypography.textTheme(theme.textTheme).apply(
          bodyColor: HomeAppColors.navy,
          displayColor: HomeAppColors.navy,
        ),
        colorScheme: ColorScheme.fromSeed(
          seedColor: HomeAppColors.navy,
          primary: HomeAppColors.navy,
          secondary: HomeAppColors.gold,
          surface: Colors.white,
          brightness: Brightness.light,
        ),
      ),
      child: Scaffold(
        backgroundColor: Colors.white,
        appBar: AppBar(
          backgroundColor: Colors.white,
          foregroundColor: HomeAppColors.navy,
          surfaceTintColor: Colors.transparent,
          elevation: 0,
          leading: BackButton(onPressed: () => Navigator.pop(context)),
          titleSpacing: 0,
          title: Padding(
            padding: const EdgeInsets.only(right: 16),
            child: TextField(
              key: const ValueKey('catalog-search-input'),
              controller: _query,
              focusNode: _focus,
              autofocus: true,
              textInputAction: TextInputAction.search,
              cursorColor: HomeAppColors.navy,
              style: AppTypography.text(
                color: HomeAppColors.navy,
                fontSize: 14,
              ),
              onChanged: (_) => setState(() => _submitted = false),
              onSubmitted: (_) => _submit(),
              decoration: InputDecoration(
                hintText: 'Search products, facilities, services...',
                hintStyle: const TextStyle(
                  fontSize: 12,
                  color: HomeAppColors.secondaryText,
                ),
                suffixIconColor: HomeAppColors.navy,
                contentPadding: const EdgeInsets.symmetric(
                  horizontal: 12,
                  vertical: 12,
                ),
                border: OutlineInputBorder(
                  borderRadius: BorderRadius.circular(24),
                ),
                suffixIcon: searching
                    ? IconButton(
                        tooltip: 'Clear search',
                        icon: const Icon(Icons.close_rounded),
                        onPressed: () {
                          setState(() {
                            _query.clear();
                            _submitted = false;
                          });
                          _focus.requestFocus();
                        },
                      )
                    : const Icon(Icons.search_rounded),
              ),
            ),
          ),
        ),
        body: SafeArea(
          top: false,
          child: ListView(
            key: ValueKey('search-content-$_submitted-$_category-$searching'),
            keyboardDismissBehavior: ScrollViewKeyboardDismissBehavior.onDrag,
            padding: const EdgeInsets.fromLTRB(16, 0, 16, 24),
            children: [
              if (searching) ...[
                _heading(_submitted ? 'Search Results' : 'Search Suggestions'),
                if (!_submitted)
                  Align(
                    alignment: Alignment.centerLeft,
                    child: TextButton.icon(
                      onPressed: _submit,
                      icon: const Icon(Icons.search_rounded, size: 18),
                      label: const Text('Search all categories'),
                    ),
                  ),
              ],
              if (_submitted)
                Padding(
                  padding: const EdgeInsets.only(bottom: 16),
                  child: Wrap(
                    spacing: 8,
                    runSpacing: 4,
                    children: [
                      for (final category in SearchCategory.values)
                        ChoiceChip(
                          label: Text(category.label),
                          selected: _category == category,
                          selectedColor: HomeAppColors.gold,
                          backgroundColor: Colors.white,
                          checkmarkColor: HomeAppColors.navy,
                          labelStyle: AppTypography.text(
                            color: HomeAppColors.navy,
                            fontSize: 12,
                          ),
                          onSelected: (_) =>
                              setState(() => _category = category),
                        ),
                    ],
                  ),
                ),
              if (!_submitted ||
                  _category == SearchCategory.all ||
                  _category == SearchCategory.products) ...[
                if (_submitted) _heading('Products'),
                _catalog<ProductItem>(
                  future: _products,
                  name: 'products',
                  retry: () => setState(() {
                    _products = _observe(widget.loadProducts());
                  }),
                  builder: _productContent,
                ),
              ],
              if (_submitted &&
                  (_category == SearchCategory.all ||
                      _category == SearchCategory.facilities)) ...[
                _heading('Facilities'),
                _catalog<FacilityItem>(
                  future: _facilities,
                  name: 'facilities',
                  retry: () => setState(() {
                    _facilities = _observe(_readFacilities());
                  }),
                  builder: (rows) {
                    final matches = rows
                        .where(
                          (row) => _matches(
                            '${row.name} ${row.facilityTypeLabel} ${row.location}',
                          ),
                        )
                        .toList();
                    if (matches.isEmpty) {
                      return _message(
                        'No matching facilities. Try another name or category.',
                      );
                    }
                    return Column(
                      children: [
                        for (final row in matches)
                          _tile(
                            name: row.name,
                            detail: row.facilityTypeLabel,
                            image: row.resolvedImageUrl,
                            icon: row.icon,
                            onTap: () => Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) =>
                                    FacilityDetailsScreen(facility: row),
                              ),
                            ),
                          ),
                      ],
                    );
                  },
                ),
              ],
              if (_submitted &&
                  (_category == SearchCategory.all ||
                      _category == SearchCategory.services)) ...[
                _heading('Services'),
                _catalog<ServiceItem>(
                  future: _services,
                  name: 'services',
                  retry: () => setState(() {
                    _services = _observe(widget.catalog.fetchServices());
                  }),
                  builder: (rows) {
                    final matches = rows
                        .where(
                          (row) =>
                              row.active &&
                              _matches(
                                '${row.name} ${row.category} ${row.facility.description}',
                              ),
                        )
                        .toList();
                    if (matches.isEmpty) {
                      return _message(
                        'No matching services. Try another name or category.',
                      );
                    }
                    return Column(
                      children: [
                        for (final row in matches)
                          _tile(
                            name: row.name,
                            detail: row.category,
                            image: row.facility.resolvedImageUrl,
                            icon: row.facility.icon,
                            onTap: () => Navigator.push(
                              context,
                              MaterialPageRoute(
                                builder: (_) => ServiceDetailsScreen(
                                  service: row,
                                  catalog: widget.catalog,
                                ),
                              ),
                            ),
                          ),
                      ],
                    );
                  },
                ),
              ],
            ],
          ),
        ),
      ),
    );
  }
}
