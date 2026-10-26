import 'package:flutter/material.dart';
import '../models/product_customization.dart';
import '../services/seller_application_service.dart';
import '../widgets/profile/profile_widgets.dart';

/// A recipe editor for the existing Product submission/approval workflow.
class SellerBundleForm extends StatefulWidget {
  const SellerBundleForm({
    super.key,
    required this.pairId,
    required this.products,
    required this.service,
  });
  final String pairId;
  final List<Map<String, dynamic>> products;
  final SellerApplicationService service;
  @override
  State<SellerBundleForm> createState() => _SellerBundleFormState();
}

class _SellerBundleFormState extends State<SellerBundleForm> {
  final form = GlobalKey<FormState>();
  late final name = TextEditingController(
    text: widget.products.map((p) => p['name']).join(' + '),
  );
  final price = TextEditingController();
  final notes = TextEditingController();
  late final quantities = [
    for (final _ in widget.products) TextEditingController(text: '1'),
  ];
  final selections = <String, Set<String>>{};
  String? category, error;
  bool saving = false;
  @override
  void dispose() {
    for (final controller in [name, price, notes, ...quantities]) {
      controller.dispose();
    }
    super.dispose();
  }

  List<ProductCustomizationGroup> groups(Map<String, dynamic> product) =>
      ProductCustomizationConfig.fromJson(product).groups;

  Future<void> submit() async {
    if (saving || !form.currentState!.validate()) return;
    setState(() {
      saving = true;
      error = null;
    });
    try {
      final components = <Map<String, dynamic>>[];
      for (var i = 0; i < widget.products.length; i++) {
        final product = widget.products[i];
        components.add({
          'product_id': product['id'],
          'required_quantity': int.parse(quantities[i].text),
          'selections': [
            for (final group in groups(product))
              for (final option
                  in selections['${product['id']}:${group.name}'] ?? <String>{})
                {'group': group.name, 'option': option},
          ],
        });
      }
      await widget.service.createProduct({
        'name': name.text.trim(),
        'price': price.text.trim(),
        'category': category,
        'description': notes.text.trim(),
        'product_type': 'bundle',
        'suggestion_id': widget.pairId,
        'bundle_components': components,
      });
      if (mounted) {
        Navigator.pop(context, true);
      }
    } catch (failure) {
      if (mounted) {
        setState(
          () => error = failure is SellerApplicationException
              ? failure.message
              : 'Unable to confirm submission. Check My Bundles before trying again.',
        );
      }
    } finally {
      if (mounted) setState(() => saving = false);
    }
  }

  InputDecoration field(String label) =>
      InputDecoration(labelText: label, border: const OutlineInputBorder());
  Widget space(Widget child) =>
      Padding(padding: const EdgeInsets.only(bottom: 16), child: child);

  @override
  Widget build(BuildContext context) => ProfileTheme(
    child: Scaffold(
      appBar: AppBar(title: const Text('Create Bundle')),
      body: Form(
        key: form,
        child: ListView(
          padding: const EdgeInsets.all(16),
          children: [
            Text(
              'Submit this bundle for marketplace review. Availability comes from its component inventory.',
              style: ProfileStyle.text(13),
            ),
            const SizedBox(height: 20),
            space(
              TextFormField(
                controller: name,
                enabled: !saving,
                decoration: field('Bundle Name'),
                maxLength: 150,
                validator: (value) => (value ?? '').trim().isEmpty
                    ? 'Enter a bundle name.'
                    : null,
              ),
            ),
            space(
              TextFormField(
                controller: price,
                enabled: !saving,
                decoration: field('Bundle Price (₱)'),
                keyboardType: const TextInputType.numberWithOptions(
                  decimal: true,
                ),
                validator: (value) {
                  final number = double.tryParse(value ?? '');
                  return number == null ||
                          !number.isFinite ||
                          number < 0 ||
                          !RegExp(r'^\d+(\.\d{1,2})?$').hasMatch(value!)
                      ? 'Enter a valid price with at most two decimal places.'
                      : null;
                },
              ),
            ),
            space(
              DropdownButtonFormField<String>(
                decoration: field('Category'),
                isExpanded: true,
                items: widget.products
                    .map((p) => '${p['category'] ?? ''}')
                    .where((s) => s.isNotEmpty)
                    .toSet()
                    .map(
                      (value) =>
                          DropdownMenuItem(value: value, child: Text(value)),
                    )
                    .toList(),
                onChanged: saving
                    ? null
                    : (value) => setState(() => category = value),
                validator: (value) =>
                    value == null ? 'Select a category.' : null,
              ),
            ),
            for (var i = 0; i < widget.products.length; i++) ...[
              Text(
                '${widget.products[i]['name']}',
                style: ProfileStyle.text(15, weight: 700),
              ),
              const SizedBox(height: 12),
              space(
                TextFormField(
                  controller: quantities[i],
                  enabled: !saving,
                  decoration: field('Required Quantity'),
                  keyboardType: TextInputType.number,
                  validator: (value) => (int.tryParse(value ?? '') ?? 0) < 1
                      ? 'Enter a positive whole quantity.'
                      : null,
                ),
              ),
              for (final group in groups(widget.products[i]))
                space(
                  FormField<Set<String>>(
                    validator: (_) {
                      final selected =
                          selections['${widget.products[i]['id']}:${group.name}'] ??
                          {};
                      return group.required && selected.isEmpty
                          ? 'Select ${group.name}.'
                          : null;
                    },
                    builder: (state) {
                      final key = '${widget.products[i]['id']}:${group.name}';
                      return Column(
                        crossAxisAlignment: CrossAxisAlignment.stretch,
                        children: [
                          Text(
                            '${group.name}${group.required ? ' *' : ''}',
                            style: ProfileStyle.text(13, weight: 600),
                          ),
                          for (final option in group.options)
                            CheckboxListTile(
                              contentPadding: EdgeInsets.zero,
                              dense: true,
                              title: Text(option.name),
                              value:
                                  selections[key]?.contains(option.name) ??
                                  false,
                              onChanged: saving
                                  ? null
                                  : (checked) => setState(() {
                                      final values = {...?selections[key]};
                                      if (!group.isMultiple) values.clear();
                                      if (checked == true) {
                                        values.add(option.name);
                                      } else {
                                        values.remove(option.name);
                                      }
                                      selections[key] = values;
                                      state.didChange(values);
                                    }),
                            ),
                          if (state.errorText != null)
                            Text(
                              state.errorText!,
                              style: ProfileStyle.text(12),
                            ),
                        ],
                      );
                    },
                  ),
                ),
            ],
            space(
              TextFormField(
                controller: notes,
                enabled: !saving,
                decoration: field('Description'),
                maxLines: 3,
              ),
            ),
            if (error != null)
              Padding(
                padding: const EdgeInsets.only(bottom: 16),
                child: Text(error!),
              ),
            FilledButton(
              onPressed: saving ? null : submit,
              style: FilledButton.styleFrom(
                minimumSize: const Size(48, 48),
                textStyle: ProfileStyle.text(13, weight: 600),
              ),
              child: Text(saving ? 'Submitting…' : 'Submit for Review'),
            ),
          ],
        ),
      ),
    ),
  );
}
