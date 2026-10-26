import 'package:flutter/material.dart';
import '../models/service_item.dart';
import '../widgets/product_image.dart';
import '../services/service_catalog.dart';
import '../widgets/facilities/booking_widgets.dart';

class ServiceDetailsScreen extends StatefulWidget {
  const ServiceDetailsScreen({
    super.key,
    required this.service,
    this.catalog = const ServiceCatalog(),
  });
  final ServiceItem service;
  final ServiceCatalog catalog;
  @override
  State<ServiceDetailsScreen> createState() => _ServiceDetailsScreenState();
}

class _ServiceDetailsScreenState extends State<ServiceDetailsScreen> {
  late Future<ServiceItem> _details;
  @override
  void initState() {
    super.initState();
    _details = widget.catalog.fetchService(widget.service.id);
  }

  void _requirements(ServiceItem service) {
    final guidance = switch (service.kind) {
      'laboratory' =>
        'Contact the office about the required sample quantity, sealing and handling before submitting a sample. The office verifies sample acceptance and laboratory resources.',
      'assessment' =>
        'Contact the office to confirm assessment eligibility, required documents and the available BPP NC II assessment schedule. Office hours do not confirm an assessment slot.',
      'lease' =>
        'Contact the office about available commercial spaces, the application requirements and lease conditions. The office reviews the application before any lease agreement.',
      _ =>
        'Contact the office to confirm the requirements and arrangements for this service.',
    };
    showModalBottomSheet<void>(
      context: context,
      isScrollControlled: true,
      backgroundColor: Colors.white,
      builder: (sheetContext) => SafeArea(
        child: Padding(
          padding: const EdgeInsets.all(20),
          child: SingleChildScrollView(
            child: Column(
              mainAxisSize: MainAxisSize.min,
              crossAxisAlignment: CrossAxisAlignment.stretch,
              children: [
                Text(
                  service.actionLabel,
                  style: const TextStyle(
                    fontSize: 20,
                    fontWeight: FontWeight.w700,
                    color: bookingNavy,
                  ),
                ),
                const SizedBox(height: 12),
                Text(guidance, style: const TextStyle(color: bookingNavy)),
                if (service.facility.requirements.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 12),
                    child: Text(service.facility.requirements),
                  ),
                if (service.facility.location.isNotEmpty)
                  Padding(
                    padding: const EdgeInsets.only(top: 12),
                    child: Text(
                      'Office / Location: ${service.facility.location}',
                    ),
                  ),
                const SizedBox(height: 12),
                const Text(
                  'Online submission is not available yet. No request has been submitted.',
                  style: TextStyle(color: bookingMuted),
                ),
                const SizedBox(height: 20),
                BookingButton(
                  label: 'Message Office',
                  onPressed: () {
                    Navigator.of(sheetContext).pop();
                    messageFacilitiesAdmin(context, service.id);
                  },
                ),
                TextButton(
                  onPressed: () => Navigator.of(sheetContext).pop(),
                  child: const Text('Close'),
                ),
              ],
            ),
          ),
        ),
      ),
    );
  }

  @override
  Widget build(BuildContext context) => FutureBuilder<ServiceItem>(
    future: _details,
    builder: (context, snapshot) {
      final service = snapshot.data;
      return BookingScaffold(
        title: 'Service Details',
        bottom: service != null && service.active
            ? BookingButton(
                label: service.actionLabel,
                onPressed: () => _requirements(service),
              )
            : null,
        child: snapshot.connectionState != ConnectionState.done
            ? const Center(child: CircularProgressIndicator(color: bookingNavy))
            : snapshot.hasError || service == null || !service.active
            ? Column(
                children: [
                  const Text(
                    'This service could not be loaded or is no longer available.',
                  ),
                  TextButton(
                    onPressed: () => setState(() {
                      _details = widget.catalog.fetchService(widget.service.id);
                    }),
                    child: const Text('Retry'),
                  ),
                ],
              )
            : ListView(
                padding: const EdgeInsets.all(16),
                children: [
                  if (service.facility.allImageUrls.isNotEmpty) ...[
                    SizedBox(
                      height: 190,
                      child: PageView(
                        children: [
                          for (final image in service.facility.allImageUrls)
                            ClipRRect(
                              borderRadius: BorderRadius.circular(8),
                              child: ProductImage(
                                imageUrl: image,
                                fallbackIcon: service.facility.icon,
                                fallbackColor: bookingNavy,
                              ),
                            ),
                        ],
                      ),
                    ),
                    const SizedBox(height: 20),
                  ],
                  Text(
                    service.name,
                    style: const TextStyle(
                      fontSize: 22,
                      fontWeight: FontWeight.w700,
                      color: bookingNavy,
                    ),
                  ),
                  const SizedBox(height: 6),
                  Text(
                    service.category,
                    style: const TextStyle(color: bookingMuted),
                  ),
                  const SizedBox(height: 20),
                  if (service.facility.description.isNotEmpty)
                    BookingSection(
                      'About this service',
                      child: Text(service.facility.description),
                    ),
                  if (service.facility.location.isNotEmpty)
                    BookingSection(
                      'Location',
                      child: Text(service.facility.location),
                    ),
                  for (final info in service.information)
                    BookingSection(info.key, child: Text(info.value)),
                  BookingSection(
                    'Requirements',
                    child: Text(
                      service.facility.requirements.isEmpty
                          ? 'Contact the office to confirm the requirements.'
                          : service.facility.requirements,
                    ),
                  ),
                  if (service.facility.termsConditions.isNotEmpty)
                    BookingSection(
                      'Terms & Conditions',
                      child: Text(service.facility.termsConditions),
                    ),
                ],
              ),
      );
    },
  );
}
