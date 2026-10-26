import 'dart:convert';
import 'dart:typed_data';
import 'dart:ui' as ui;

import 'package:flutter/material.dart';
import 'package:image_picker/image_picker.dart';
import 'package:lucide_icons/lucide_icons.dart';

import '../models/product_item.dart';
import '../services/product_service.dart';
import '../services/seller_application_service.dart';
import '../widgets/home/home_preview_cards.dart';
import '../widgets/product_image.dart';

/// A smooth gradient outline border for active/focused labeled inputs.
class GradientOutlineInputBorder extends OutlineInputBorder {
  const GradientOutlineInputBorder({
    super.borderRadius = const BorderRadius.all(Radius.circular(12)),
    super.borderSide = const BorderSide(width: 1.8),
    required this.gradient,
  });

  final Gradient gradient;

  @override
  void paint(
    Canvas canvas,
    Rect rect, {
    double? gapStart,
    double gapExtent = 0.0,
    double gapPercentage = 0.0,
    TextDirection? textDirection,
  }) {
    final paint = Paint()
      ..shader = gradient.createShader(rect)
      ..strokeWidth = borderSide.width
      ..style = PaintingStyle.stroke;
    final rrect = borderRadius.toRRect(rect.deflate(borderSide.width / 2));
    canvas.drawRRect(rrect, paint);
  }

  @override
  GradientOutlineInputBorder copyWith({
    BorderSide? borderSide,
    BorderRadius? borderRadius,
    double? gapPadding,
    Gradient? gradient,
  }) => GradientOutlineInputBorder(
    borderSide: borderSide ?? this.borderSide,
    borderRadius: borderRadius ?? this.borderRadius,
    gradient: gradient ?? this.gradient,
  );
}

/// One continuous form; ownership and approval remain enforced by Django.
class SellerAddProductPage extends StatefulWidget {
  const SellerAddProductPage({super.key, required this.categories});

  final List<String> categories;

  @override
  State<SellerAddProductPage> createState() => _SellerAddProductPageState();
}

class _SellerAddProductPageState extends State<SellerAddProductPage> {
  static const _maxImageBytes = 5 * 1024 * 1024;
  static const _maxImages = 6;
  static const _line = Color(0xFFE8EAF0);
  static const _muted = Color(0xFF667085);
  final _form = GlobalKey<FormState>();
  final _name = TextEditingController();
  final _description = TextEditingController();
  final _tags = TextEditingController();
  final _price = TextEditingController();
  final _quantity = TextEditingController();
  // Prefilled with the backend default (CAMPUSHUB_LOW_STOCK_THRESHOLD = 5).
  final _lowStockThreshold = TextEditingController(text: '5');
  String? _category, _imageError, _submitError;
  final List<String?> _selectedImages = List.filled(_maxImages, null);
  DateTime? _expiry;
  bool _submitting = false, _picking = false, _submitted = false;
  bool _showLowStockCaution = false;

  bool get _busy => _submitting || _picking;
  int get _imageCount => _selectedImages.whereType<String>().length;
  bool get _perishable => ProductItem.isPerishableCategory(_category);

  @override
  void dispose() {
    for (final controller in [
      _name,
      _description,
      _tags,
      _price,
      _quantity,
      _lowStockThreshold,
    ]) {
      controller.dispose();
    }
    super.dispose();
  }

  String? _required(String? value, String label) =>
      (value ?? '').trim().isEmpty ? '$label is required.' : null;

  String? _validatePrice(String? value) {
    final text = (value ?? '').trim();
    final amount = double.tryParse(text);
    if (!RegExp(r'^\d{1,8}(\.\d{1,2})?$').hasMatch(text) ||
        amount == null ||
        !amount.isFinite ||
        amount <= 0) {
      return 'Enter a price greater than 0 with up to 2 decimal places.';
    }
    return null;
  }

  String? _validateStock(String? value) {
    final text = (value ?? '').trim();
    if (!RegExp(r'^\d+$').hasMatch(text) || int.tryParse(text) == null) {
      return 'Enter a whole-number stock of 0 or more.';
    }
    return null;
  }

  String? _validateLowStockThreshold(String? value) {
    final text = (value ?? '').trim();
    if (text.isEmpty) return 'Low stock threshold is required.';
    final parsed = int.tryParse(text);
    if (!RegExp(r'^\d+$').hasMatch(text) || parsed == null || parsed < 0) {
      return 'Enter a whole-number threshold of 0 or more.';
    }
    return null;
  }

  String? _imageMime(Uint8List bytes) {
    if (bytes.length >= 3 &&
        bytes[0] == 255 &&
        bytes[1] == 216 &&
        bytes[2] == 255) {
      return 'image/jpeg';
    }
    if (bytes.length >= 8 &&
        base64Encode(bytes.sublist(0, 8)) == 'iVBORw0KGgo=') {
      return 'image/png';
    }
    if (bytes.length >= 12 &&
        ascii.decode(bytes.sublist(0, 4), allowInvalid: true) == 'RIFF' &&
        ascii.decode(bytes.sublist(8, 12), allowInvalid: true) == 'WEBP') {
      return 'image/webp';
    }
    if (bytes.length >= 6 &&
        [
          'GIF87a',
          'GIF89a',
        ].contains(ascii.decode(bytes.sublist(0, 6), allowInvalid: true))) {
      return 'image/gif';
    }
    return null;
  }

  Future<String> _readImage(XFile file) async {
    if (await file.length() > _maxImageBytes) {
      throw const FormatException('Choose an image no larger than 5 MB.');
    }
    final bytes = await file.readAsBytes();
    final mime = _imageMime(bytes);
    if (bytes.isEmpty || bytes.length > _maxImageBytes || mime == null) {
      throw const FormatException(
        'Choose a JPEG, PNG, WebP or GIF image up to 5 MB.',
      );
    }
    final buffer = await ui.ImmutableBuffer.fromUint8List(bytes);
    try {
      final descriptor = await ui.ImageDescriptor.encoded(buffer);
      try {
        if (descriptor.width * descriptor.height > 20000000) {
          throw const FormatException(
            'Choose an image smaller than 20 megapixels.',
          );
        }
      } finally {
        descriptor.dispose();
      }
    } finally {
      buffer.dispose();
    }
    return 'data:$mime;base64,${base64Encode(bytes)}';
  }

  Future<void> _pickImages({int? slot}) async {
    if (_busy) return;
    final remaining = _maxImages - _imageCount;
    if (slot == null && remaining == 0) return;
    setState(() {
      _picking = true;
      _imageError = null;
    });
    try {
      final picker = ImagePicker();
      final List<XFile> files;
      if (slot != null || remaining == 1) {
        final file = await picker.pickImage(
          source: ImageSource.gallery,
          maxWidth: 1280,
          maxHeight: 1280,
          imageQuality: 85,
          requestFullMetadata: false,
        );
        files = file == null ? [] : [file];
      } else {
        files = await picker.pickMultiImage(
          maxWidth: 1280,
          maxHeight: 1280,
          imageQuality: 85,
          requestFullMetadata: false,
          limit: remaining,
        );
      }
      if (files.isEmpty || !mounted) return;
      if (files.length > (slot == null ? remaining : 1)) {
        throw const FormatException(
          'You can upload up to 6 images. Select fewer images.',
        );
      }
      // Validate the whole batch before changing any existing slot.
      final images = <String>[];
      for (final file in files) {
        images.add(await _readImage(file));
      }
      if (mounted) {
        setState(() {
          if (slot != null) {
            _selectedImages[slot] = images.single;
          } else {
            final emptySlots = [
              for (var i = 0; i < _maxImages; i++)
                if (_selectedImages[i] == null) i,
            ];
            for (var i = 0; i < images.length; i++) {
              _selectedImages[emptySlots[i]] = images[i];
            }
          }
        });
      }
    } catch (failure) {
      if (mounted) {
        setState(
          () => _imageError = failure is FormatException
              ? failure.message
              : 'Unable to open this image. Check photo access and try again.',
        );
      }
    } finally {
      if (mounted) setState(() => _picking = false);
    }
  }

  Future<void> _chooseExpiry() async {
    final today = DateUtils.dateOnly(DateTime.now());
    final picked = await showDatePicker(
      context: context,
      initialDate: _expiry ?? today.add(const Duration(days: 7)),
      firstDate: today,
      lastDate: today.add(const Duration(days: 365)),
    );
    if (picked != null && mounted) setState(() => _expiry = picked);
  }

  /// Opens the category list directly BELOW the field so it never covers
  /// the "Category *" label (DropdownButton overlays the button itself).
  Future<void> _showCategoryMenu(
    BuildContext fieldContext,
    List<String> categories,
    FormFieldState<String> state,
  ) async {
    FocusScope.of(context).unfocus();
    final box = fieldContext.findRenderObject()! as RenderBox;
    final overlay =
        Overlay.of(fieldContext).context.findRenderObject()! as RenderBox;
    final topLeft = box.localToGlobal(
      Offset(0, box.size.height + 4),
      ancestor: overlay,
    );
    final picked = await showMenu<String>(
      context: fieldContext,
      color: Colors.white,
      surfaceTintColor: Colors.white,
      elevation: 2,
      constraints: BoxConstraints(
        minWidth: box.size.width,
        maxWidth: box.size.width,
        maxHeight: 320,
      ),
      shape: RoundedRectangleBorder(
        borderRadius: BorderRadius.circular(12),
        side: const BorderSide(color: _line),
      ),
      position: RelativeRect.fromLTRB(
        topLeft.dx,
        topLeft.dy,
        overlay.size.width - topLeft.dx - box.size.width,
        overlay.size.height - topLeft.dy,
      ),
      items: [
        for (final category in categories)
          PopupMenuItem<String>(
            value: category,
            child: Text(
              category,
              style: TextStyle(
                fontFamily: 'Poppins',
                fontSize: 14,
                color: HomeAppColors.navy,
                fontWeight: category == _category
                    ? FontWeight.w600
                    : FontWeight.w400,
              ),
            ),
          ),
      ],
    );
    if (picked == null || !mounted) return;
    setState(() {
      _category = picked;
      if (!_perishable) _expiry = null;
    });
    state.didChange(picked);
  }

  Widget _buildLowStockCaution() => Container(
    key: const ValueKey('low-stock-caution'),
    padding: const EdgeInsets.symmetric(horizontal: 12, vertical: 10),
    decoration: BoxDecoration(
      color: const Color(0xFFFCB315),
      borderRadius: BorderRadius.circular(10),
      boxShadow: const [
        BoxShadow(
          color: Color(0x1F000000),
          blurRadius: 4,
          offset: Offset(0, 2),
        ),
      ],
    ),
    child: Row(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        const Padding(
          padding: EdgeInsets.only(top: 2),
          child: Icon(
            LucideIcons.alertCircle,
            size: 16,
            color: HomeAppColors.navy,
          ),
        ),
        const SizedBox(width: 8),
        const Expanded(
          child: Text(
            'You will be alerted when your stock reaches this quantity or lower.',
            style: TextStyle(
              fontSize: 12,
              height: 1.4,
              fontWeight: FontWeight.w500,
              color: HomeAppColors.navy,
            ),
          ),
        ),
        InkWell(
          key: const ValueKey('close-caution-popup'),
          onTap: () => setState(() => _showLowStockCaution = false),
          borderRadius: BorderRadius.circular(12),
          child: const Padding(
            padding: EdgeInsets.all(2),
            child: Icon(LucideIcons.x, size: 16, color: HomeAppColors.navy),
          ),
        ),
      ],
    ),
  );

  Future<void> _submit() async {
    setState(() => _submitted = true);
    if (_busy || !_form.currentState!.validate()) return;
    FocusScope.of(context).unfocus();
    setState(() {
      _submitting = true;
      _submitError = null;
    });
    try {
      final thresholdText = _lowStockThreshold.text.trim();
      await ProductService.submitProduct(
        name: _name.text.trim(),
        price: _price.text.trim(),
        category: _category!,
        stock: int.parse(_quantity.text.trim()),
        lowStockThreshold: thresholdText.isNotEmpty
            ? int.tryParse(thresholdText)
            : null,
        tags: _tags.text.trim().isNotEmpty ? _tags.text.trim() : null,
        description: _description.text.trim(),
        expiryDate: _perishable && _expiry != null
            ? '${_expiry!.year}-${_expiry!.month.toString().padLeft(2, '0')}-${_expiry!.day.toString().padLeft(2, '0')}'
            : null,
        images: _selectedImages.whereType<String>().toList(),
      );
      if (!mounted) return;
      final messenger = ScaffoldMessenger.of(context);
      setState(() => _submitting = false);
      Navigator.of(context).pop(true);
      messenger.showSnackBar(
        const SnackBar(
          content: Text('Product submitted for marketplace review.'),
        ),
      );
    } catch (failure) {
      if (mounted) {
        setState(
          () => _submitError = failure is SellerApplicationException
              ? failure.message
              : 'Unable to confirm submission. Check My Products before trying again.',
        );
      }
    } finally {
      if (mounted) setState(() => _submitting = false);
    }
  }

  InputDecoration _decoration(String hint) => InputDecoration(
    hintText: hint,
    hintStyle: const TextStyle(color: _muted, fontSize: 14),
    filled: true,
    fillColor: Colors.white,
    contentPadding: const EdgeInsets.symmetric(horizontal: 14, vertical: 15),
    border: OutlineInputBorder(borderRadius: BorderRadius.circular(12)),
    enabledBorder: OutlineInputBorder(
      borderRadius: BorderRadius.circular(12),
      borderSide: const BorderSide(color: _line),
    ),
    focusedBorder: const GradientOutlineInputBorder(
      borderRadius: BorderRadius.all(Radius.circular(12)),
      borderSide: BorderSide(width: 1.8),
      gradient: LinearGradient(
        colors: [HomeAppColors.navy, Color(0xFFFCB315)],
        begin: Alignment.topLeft,
        end: Alignment.bottomRight,
      ),
    ),
    errorMaxLines: 3,
  );

  /// [hasCaution], [onCautionTap] and [onCautionLongPress] add a circled "!" icon
  /// next to the label. [cautionWidget] appears inline between the label and the input.
  Widget _label(
    String label,
    Widget field, {
    VoidCallback? onCautionTap,
    VoidCallback? onCautionLongPress,
    bool hasCaution = false,
    Widget? cautionWidget,
  }) => Padding(
    padding: const EdgeInsets.only(bottom: 16),
    child: Column(
      crossAxisAlignment: CrossAxisAlignment.start,
      children: [
        Wrap(
          crossAxisAlignment: WrapCrossAlignment.center,
          children: [
            Text(
              label,
              style: const TextStyle(fontSize: 13, fontWeight: FontWeight.w500),
            ),
            if (hasCaution) ...[
              const SizedBox(width: 6),
              InkWell(
                key: ValueKey('caution-$label'),
                borderRadius: BorderRadius.circular(12),
                onTap: onCautionTap,
                onLongPress: onCautionLongPress,
                child: const Icon(
                  LucideIcons.alertCircle,
                  size: 16,
                  color: HomeAppColors.navy,
                ),
              ),
            ],
          ],
        ),
        if (cautionWidget != null) ...[
          const SizedBox(height: 8),
          cautionWidget,
        ],
        const SizedBox(height: 8),
        Semantics(label: label, child: field),
      ],
    ),
  );

  Widget _section(String title, List<Widget> children) => Padding(
    padding: const EdgeInsets.only(bottom: 24),
    child: Container(
      width: double.infinity,
      padding: const EdgeInsets.fromLTRB(16, 16, 16, 0),
      decoration: BoxDecoration(
        color: Colors.white,
        borderRadius: BorderRadius.circular(12),
        border: Border.all(color: _line),
      ),
      child: Column(
        crossAxisAlignment: CrossAxisAlignment.start,
        children: [
          Text(
            title,
            style: const TextStyle(fontSize: 16, fontWeight: FontWeight.w600),
          ),
          const SizedBox(height: 16),
          ...children,
        ],
      ),
    ),
  );

  Widget _imageSlot(int index, double size) {
    final image = _selectedImages[index];
    return SizedBox.square(
      key: ValueKey('product-image-slot-$index'),
      dimension: size,
      child: Stack(
        children: [
          Positioned.fill(
            child: Material(
              color: Colors.white,
              clipBehavior: Clip.antiAlias,
              shape: RoundedRectangleBorder(
                borderRadius: BorderRadius.circular(8),
                side: const BorderSide(color: _line),
              ),
              child: InkWell(
                onTap: _busy ? null : () => _pickImages(slot: index),
                child: Semantics(
                  button: true,
                  label:
                      '${image == null ? 'Add' : 'Replace'} image ${index + 1}',
                  child: image == null
                      ? const Center(
                          child: Icon(
                            LucideIcons.imagePlus,
                            size: 26,
                            color: _muted,
                          ),
                        )
                      : ProductImage(
                          key: ValueKey('product-image-preview-$index'),
                          imageUrl: image,
                          fit: BoxFit.cover,
                        ),
                ),
              ),
            ),
          ),
          if (image != null)
            Positioned(
              top: 0,
              right: 0,
              child: IconButton(
                key: ValueKey('remove-product-image-$index'),
                tooltip: 'Remove image ${index + 1}',
                constraints: const BoxConstraints(minWidth: 48, minHeight: 48),
                onPressed: _busy
                    ? null
                    : () => setState(() {
                        _selectedImages[index] = null;
                        _imageError = null;
                      }),
                icon: Container(
                  padding: const EdgeInsets.all(3),
                  decoration: BoxDecoration(
                    color: Colors.white,
                    border: Border.all(color: _line),
                    shape: BoxShape.circle,
                  ),
                  child: const Icon(
                    LucideIcons.x,
                    size: 16,
                    color: HomeAppColors.navy,
                  ),
                ),
              ),
            ),
        ],
      ),
    );
  }

  Widget _images() => _section('Upload Images', [
    SizedBox(
      width: double.infinity,
      child: OutlinedButton(
        key: const ValueKey('add-product-image'),
        onPressed: _busy || _imageCount == _maxImages ? null : _pickImages,
        style: OutlinedButton.styleFrom(
          padding: const EdgeInsets.all(20),
          minimumSize: const Size(0, 180),
          backgroundColor: Colors.white,
          side: const BorderSide(color: _line),
          shape: RoundedRectangleBorder(borderRadius: BorderRadius.zero),
        ),
        child: Column(
          children: [
            Container(
              width: 58,
              height: 58,
              color: HomeAppColors.navy,
              child: const Icon(
                LucideIcons.upload,
                color: Colors.white,
                size: 32,
              ),
            ),
            const SizedBox(height: 12),
            Text(
              _picking ? 'Opening photos…' : 'Choose product images',
              textAlign: TextAlign.center,
            ),
            const SizedBox(height: 8),
            Container(
              padding: const EdgeInsets.symmetric(horizontal: 16, vertical: 12),
              decoration: BoxDecoration(border: Border.all(color: _line)),
              child: Text(
                _imageCount == _maxImages
                    ? 'All 6 slots filled'
                    : 'Tap to browse',
                textAlign: TextAlign.center,
              ),
            ),
          ],
        ),
      ),
    ),
    const SizedBox(height: 12),
    LayoutBuilder(
      builder: (context, constraints) {
        final columns = constraints.maxWidth >= 304 ? 3 : 2;
        final size = (constraints.maxWidth - (columns - 1) * 8) / columns;
        return Wrap(
          spacing: 8,
          runSpacing: 8,
          children: [for (var i = 0; i < _maxImages; i++) _imageSlot(i, size)],
        );
      },
    ),
    const SizedBox(height: 12),
    const Text(
      'Supported: JPEG, PNG, WebP, GIF · Up to 6 images · 5 MB',
      style: TextStyle(fontSize: 12, color: _muted),
    ),
    const SizedBox(height: 8),
    Semantics(
      liveRegion: true,
      child: Text(
        '$_imageCount of 6 images',
        style: const TextStyle(fontSize: 12, color: HomeAppColors.navy),
      ),
    ),
    if (_imageError != null) ...[
      const SizedBox(height: 8),
      Semantics(
        liveRegion: true,
        child: Text(_imageError!, style: const TextStyle(fontSize: 13)),
      ),
    ],
    const SizedBox(height: 16),
  ]);

  @override
  Widget build(BuildContext context) {
    final original = Theme.of(context);
    final categories = widget.categories
        .where((item) => item.trim().isNotEmpty)
        .toSet()
        .toList();
    return Theme(
      data: original.copyWith(
        scaffoldBackgroundColor: Colors.white,
        textTheme: original.textTheme.apply(
          fontFamily: 'Poppins',
          bodyColor: HomeAppColors.navy,
          displayColor: HomeAppColors.navy,
        ),
        colorScheme: original.colorScheme.copyWith(
          primary: HomeAppColors.navy,
          onPrimary: Colors.white,
          secondary: HomeAppColors.gold,
          surface: Colors.white,
          onSurface: HomeAppColors.navy,
          error: HomeAppColors.navy,
          onError: Colors.white,
        ),
        textSelectionTheme: const TextSelectionThemeData(
          cursorColor: HomeAppColors.navy,
        ),
      ),
      child: PopScope(
        canPop: !_busy,
        child: Scaffold(
          backgroundColor: Colors.white,
          resizeToAvoidBottomInset: true,
          appBar: AppBar(
            centerTitle: true,
            backgroundColor: Colors.white,
            surfaceTintColor: Colors.white,
            foregroundColor: HomeAppColors.navy,
            elevation: 0,
            scrolledUnderElevation: 0,
            title: const Text(
              'Add Product',
              style: TextStyle(
                fontFamily: 'Poppins',
                fontSize: 20,
                fontWeight: FontWeight.w600,
              ),
            ),
            leading: BackButton(
              onPressed: _busy ? null : () => Navigator.of(context).pop(),
            ),
            shape: const Border(bottom: BorderSide(color: _line)),
          ),
          body: SafeArea(
            top: false,
            child: Align(
              alignment: Alignment.topCenter,
              child: ConstrainedBox(
                constraints: const BoxConstraints(maxWidth: 640),
                child: Form(
                  key: _form,
                  autovalidateMode: _submitted
                      ? AutovalidateMode.onUserInteraction
                      : AutovalidateMode.disabled,
                  child: SingleChildScrollView(
                    key: const ValueKey('add-product-scroll'),
                    keyboardDismissBehavior:
                        ScrollViewKeyboardDismissBehavior.onDrag,
                    padding: const EdgeInsets.all(16),
                    child: Column(
                      crossAxisAlignment: CrossAxisAlignment.start,
                      children: [
                        _section('Product Information', [
                          _label(
                            'Product Name *',
                            TextFormField(
                              key: const ValueKey('product-name'),
                              controller: _name,
                              enabled: !_busy,
                              maxLength: 150,
                              textCapitalization: TextCapitalization.sentences,
                              textInputAction: TextInputAction.next,
                              decoration: _decoration('Enter product name'),
                              validator: (value) =>
                                  _required(value, 'Product name'),
                            ),
                          ),
                          _label(
                            'Category *',
                            FormField<String>(
                              initialValue: _category,
                              validator: (_) => _category == null
                                  ? 'Select a category.'
                                  : null,
                              builder: (state) => Builder(
                                builder: (fieldContext) => InkWell(
                                  key: const ValueKey('product-category'),
                                  borderRadius: BorderRadius.circular(12),
                                  onTap: _busy || categories.isEmpty
                                      ? null
                                      : () => _showCategoryMenu(
                                          fieldContext,
                                          categories,
                                          state,
                                        ),
                                  child: InputDecorator(
                                    isEmpty: _category == null,
                                    decoration: _decoration('Select category')
                                        .copyWith(
                                          errorText: state.errorText,
                                          enabled:
                                              !_busy && categories.isNotEmpty,
                                          suffixIcon: const Icon(
                                            Icons.keyboard_arrow_down_rounded,
                                            color: HomeAppColors.navy,
                                          ),
                                        ),
                                    child: Text(
                                      _category ?? '',
                                      maxLines: 1,
                                      overflow: TextOverflow.ellipsis,
                                      style: const TextStyle(
                                        fontFamily: 'Poppins',
                                        fontSize: 14,
                                        color: HomeAppColors.navy,
                                      ),
                                    ),
                                  ),
                                ),
                              ),
                            ),
                          ),
                          if (categories.isEmpty)
                            const Padding(
                              padding: EdgeInsets.only(bottom: 16),
                              child: Text(
                                'No categories are available. Go back and reopen Add Product to retry.',
                                style: TextStyle(fontSize: 13),
                              ),
                            ),
                          _label(
                            'Description *',
                            TextFormField(
                              key: const ValueKey('product-description'),
                              controller: _description,
                              enabled: !_busy,
                              minLines: 3,
                              maxLines: 5,
                              keyboardType: TextInputType.multiline,
                              decoration: _decoration(
                                'Describe your product and relevant details',
                              ),
                              validator: (value) =>
                                  _required(value, 'Description'),
                            ),
                          ),
                          _label(
                            'Tags (Optional)',
                            TextFormField(
                              key: const ValueKey('product-tags'),
                              controller: _tags,
                              enabled: !_busy,
                              textInputAction: TextInputAction.next,
                              decoration: _decoration(
                                'Enter tags',
                              ).copyWith(helperText: 'Separate with commas.'),
                            ),
                          ),
                        ]),
                        _section('Pricing & Inventory', [
                          _label(
                            'Price (₱) *',
                            TextFormField(
                              key: const ValueKey('product-price'),
                              controller: _price,
                              enabled: !_busy,
                              keyboardType:
                                  const TextInputType.numberWithOptions(
                                    decimal: true,
                                  ),
                              textInputAction: TextInputAction.next,
                              decoration: _decoration(
                                '0.00',
                              ).copyWith(prefixText: '₱ '),
                              validator: _validatePrice,
                            ),
                          ),
                          _label(
                            'Stock *',
                            TextFormField(
                              key: const ValueKey('product-quantity'),
                              controller: _quantity,
                              enabled: !_busy,
                              keyboardType: TextInputType.number,
                              textInputAction: TextInputAction.next,
                              decoration: _decoration('Enter stock quantity'),
                              validator: _validateStock,
                            ),
                          ),
                          _label(
                            'Low Stock Threshold *',
                            TextFormField(
                              key: const ValueKey(
                                'product-low-stock-threshold',
                              ),
                              controller: _lowStockThreshold,
                              enabled: !_busy,
                              keyboardType: TextInputType.number,
                              textInputAction: TextInputAction.done,
                              decoration: _decoration('5'),
                              validator: _validateLowStockThreshold,
                            ),
                            hasCaution: true,
                            onCautionTap: () => setState(
                              () =>
                                  _showLowStockCaution = !_showLowStockCaution,
                            ),
                            onCautionLongPress: () =>
                                setState(() => _showLowStockCaution = true),
                            cautionWidget: _showLowStockCaution
                                ? _buildLowStockCaution()
                                : null,
                          ),
                          if (_perishable)
                            Padding(
                              padding: const EdgeInsets.only(bottom: 16),
                              child: Column(
                                crossAxisAlignment: CrossAxisAlignment.start,
                                children: [
                                  const Text(
                                    'Expiry Date (Optional)',
                                    style: TextStyle(
                                      fontSize: 13,
                                      fontWeight: FontWeight.w500,
                                    ),
                                  ),
                                  const SizedBox(height: 8),
                                  Wrap(
                                    spacing: 8,
                                    crossAxisAlignment:
                                        WrapCrossAlignment.center,
                                    children: [
                                      OutlinedButton.icon(
                                        onPressed: _busy ? null : _chooseExpiry,
                                        icon: const Icon(
                                          LucideIcons.calendarDays,
                                          size: 18,
                                        ),
                                        label: Text(
                                          _expiry == null
                                              ? 'Select expiry date'
                                              : MaterialLocalizations.of(
                                                  context,
                                                ).formatMediumDate(_expiry!),
                                        ),
                                      ),
                                      if (_expiry != null)
                                        TextButton(
                                          onPressed: _busy
                                              ? null
                                              : () => setState(
                                                  () => _expiry = null,
                                                ),
                                          child: const Text('Clear date'),
                                        ),
                                    ],
                                  ),
                                ],
                              ),
                            ),
                        ]),
                        _images(),
                        _section('Review', [
                          const Text(
                            'Your product will be reviewed by the ADMIN before appearing in Marketplace.',
                            style: TextStyle(
                              fontSize: 13,
                              color: _muted,
                              height: 1.6,
                            ),
                          ),
                          const SizedBox(height: 16),
                        ]),
                        if (_submitError != null)
                          Padding(
                            padding: const EdgeInsets.only(bottom: 16),
                            child: Semantics(
                              liveRegion: true,
                              child: Text(
                                _submitError!,
                                key: const ValueKey('product-submit-error'),
                                style: const TextStyle(
                                  fontSize: 13,
                                  height: 1.5,
                                ),
                              ),
                            ),
                          ),
                        SizedBox(
                          width: double.infinity,
                          child: FilledButton(
                            key: const ValueKey('submit-product'),
                            onPressed: _busy || categories.isEmpty
                                ? null
                                : _submit,
                            style: FilledButton.styleFrom(
                              backgroundColor: HomeAppColors.navy,
                              foregroundColor: Colors.white,
                              minimumSize: const Size(0, 52),
                              padding: const EdgeInsets.symmetric(
                                horizontal: 16,
                                vertical: 16,
                              ),
                              shape: RoundedRectangleBorder(
                                borderRadius: BorderRadius.circular(12),
                              ),
                              textStyle: const TextStyle(
                                fontFamily: 'Poppins',
                                fontSize: 14,
                                fontWeight: FontWeight.w600,
                              ),
                            ),
                            child: _submitting
                                ? const Row(
                                    mainAxisSize: MainAxisSize.min,
                                    children: [
                                      SizedBox(
                                        width: 18,
                                        height: 18,
                                        child: CircularProgressIndicator(
                                          strokeWidth: 2,
                                          color: Colors.white,
                                        ),
                                      ),
                                      SizedBox(width: 10),
                                      Text('Submitting…'),
                                    ],
                                  )
                                : const Text('Submit for Approval'),
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
      ),
    );
  }
}
