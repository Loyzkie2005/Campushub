class ProductCustomizationOption {
  const ProductCustomizationOption({
    required this.name,
    this.extraPrice = 0,
    this.imageUrl = '',
  });

  factory ProductCustomizationOption.fromJson(Map<String, dynamic> json) {
    final rawPrice = json['extra_price']?.toString() ?? '0';
    return ProductCustomizationOption(
      name: (json['name'] as String? ?? '').trim(),
      extraPrice: double.tryParse(rawPrice) ?? 0,
      imageUrl: (json['image'] as String? ?? json['image_url'] as String? ?? '')
          .trim(),
    );
  }

  final String name;
  final double extraPrice;
  final String imageUrl;

  String get priceLabel =>
      extraPrice > 0 ? '+₱${extraPrice.toStringAsFixed(2)}' : '₱0';
}

class ProductCustomizationGroup {
  const ProductCustomizationGroup({
    required this.name,
    required this.selection,
    required this.required,
    required this.options,
  });

  factory ProductCustomizationGroup.fromJson(Map<String, dynamic> json) {
    final rawOptions = json['options'];
    final options = rawOptions is List
        ? rawOptions
              .whereType<Map>()
              .map(
                (item) => ProductCustomizationOption.fromJson(
                  item.map((key, value) => MapEntry('$key', value)),
                ),
              )
              .where((item) => item.name.isNotEmpty)
              .toList(growable: false)
        : const <ProductCustomizationOption>[];

    final selection = (json['selection'] as String? ?? 'single').trim();
    return ProductCustomizationGroup(
      name: (json['name'] as String? ?? '').trim(),
      selection: selection == 'multiple' ? 'multiple' : 'single',
      required: json['required'] == true,
      options: options,
    );
  }

  final String name;
  final String selection;
  final bool required;
  final List<ProductCustomizationOption> options;

  bool get isMultiple => selection == 'multiple';
}

class ProductCustomizationConfig {
  const ProductCustomizationConfig({
    this.enabled = false,
    this.groups = const [],
  });

  factory ProductCustomizationConfig.fromJson(Map<String, dynamic> json) {
    final rawGroups = json['customization_options'] ?? json['groups'];
    final groups = rawGroups is List
        ? rawGroups
              .whereType<Map>()
              .map(
                (item) => ProductCustomizationGroup.fromJson(
                  item.map((key, value) => MapEntry('$key', value)),
                ),
              )
              .where((item) => item.name.isNotEmpty && item.options.isNotEmpty)
              .toList(growable: false)
        : const <ProductCustomizationGroup>[];

    final enabled = json['customization_enabled'] == true && groups.isNotEmpty;
    return ProductCustomizationConfig(enabled: enabled, groups: groups);
  }

  final bool enabled;
  final List<ProductCustomizationGroup> groups;

  bool get hasOptions => enabled && groups.isNotEmpty;
}

class SelectedCustomization {
  const SelectedCustomization({
    required this.group,
    required this.option,
    required this.extraPrice,
  });

  Map<String, dynamic> toJson() => {
    'group': group,
    'option': option,
    'extra_price': extraPrice.toStringAsFixed(2),
  };

  final String group;
  final String option;
  final double extraPrice;
}

class BuySelection {
  const BuySelection({
    required this.quantity,
    required this.selections,
    required this.summary,
    required this.unitPrice,
  });

  final int quantity;
  final List<SelectedCustomization> selections;
  final String summary;
  final double unitPrice;

  List<Map<String, dynamic>> get customizationPayload =>
      selections.map((item) => item.toJson()).toList(growable: false);

  double get totalPrice => unitPrice * quantity;
}

String buildCustomizationSummary(List<SelectedCustomization> selections) {
  if (selections.isEmpty) return '';
  return selections
      .map((item) {
        if (item.extraPrice > 0) {
          return '${item.option} (+P${item.extraPrice.toStringAsFixed(2)})';
        }
        return item.option;
      })
      .join(', ');
}
