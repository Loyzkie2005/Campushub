import 'package:flutter/material.dart';
import 'package:lucide_icons/lucide_icons.dart';
import '../models/service_item.dart';
import '../routes/app_routes.dart';
import '../services/service_catalog.dart';
import '../widgets/facilities/booking_widgets.dart';
import 'service_details_screen.dart';

class ServicesPage extends StatefulWidget {
  const ServicesPage({super.key, this.catalog = const ServiceCatalog()});
  final ServiceCatalog catalog;
  @override
  State<ServicesPage> createState() => _ServicesPageState();
}

class _ServicesPageState extends State<ServicesPage> {
  List<ServiceItem> _services = [];
  bool _loading = true;
  String? _error;
  String _query = '';
  @override
  void initState() {
    super.initState();
    _load();
  }

  Future<void> _load() async {
    setState(() {
      _loading = true;
      _error = null;
    });
    try {
      final rows = await widget.catalog.fetchServices();
      if (mounted) setState(() => _services = rows);
    } catch (_) {
      if (mounted) {
        setState(
          () => _error =
              'Unable to load services. Check your connection and retry.',
        );
      }
    } finally {
      if (mounted) setState(() => _loading = false);
    }
  }

  @override
  Widget build(BuildContext context) {
    final rows = _services
        .where(
          (row) => '${row.name} ${row.category} ${row.facility.description}'
              .toLowerCase()
              .contains(_query.toLowerCase().trim()),
        )
        .toList();
    return RefreshIndicator(
      onRefresh: _load,
      color: bookingNavy,
      child: ListView(
        key: const PageStorageKey('mobile-services-list'),
        physics: const AlwaysScrollableScrollPhysics(),
        padding: const EdgeInsets.fromLTRB(16, 18, 16, 24),
        children: [
          const Text(
            'Services',
            style: TextStyle(
              fontSize: 22,
              fontWeight: FontWeight.w700,
              color: bookingNavy,
            ),
          ),
          const SizedBox(height: 16),
          TextField(
            key: const ValueKey('service-search'),
            style: const TextStyle(color: bookingNavy),
            onChanged: (value) => setState(() => _query = value),
            decoration: InputDecoration(
              labelText: 'Search services',
              hintText: 'Search by service name or category',
              filled: true,
              fillColor: Colors.white,
              labelStyle: const TextStyle(color: bookingMuted),
              hintStyle: const TextStyle(color: bookingMuted),
              prefixIcon: const Icon(LucideIcons.search, color: bookingNavy),
              border: OutlineInputBorder(
                borderRadius: BorderRadius.circular(8),
              ),
            ),
          ),
          const SizedBox(height: 20),
          const Text(
            'Available Services',
            style: TextStyle(fontWeight: FontWeight.w700, color: bookingNavy),
          ),
          const SizedBox(height: 12),
          if (_loading)
            const Padding(
              padding: EdgeInsets.all(32),
              child: Center(
                child: CircularProgressIndicator(color: bookingNavy),
              ),
            )
          else if (_error != null) ...[
            Text(_error!, style: const TextStyle(color: bookingNavy)),
            TextButton(onPressed: _load, child: const Text('Retry')),
          ] else if (_services.isEmpty)
            const Padding(
              padding: EdgeInsets.symmetric(vertical: 32),
              child: Text(
                'No services are currently available.',
                style: TextStyle(color: bookingMuted),
              ),
            )
          else if (rows.isEmpty)
            const Text(
              'No services match your search.',
              style: TextStyle(color: bookingMuted),
            )
          else
            for (final row in rows)
              Padding(
                padding: const EdgeInsets.only(bottom: 12),
                child: Material(
                  color: Colors.white,
                  shape: RoundedRectangleBorder(
                    borderRadius: BorderRadius.circular(8),
                    side: const BorderSide(color: bookingOutline),
                  ),
                  child: InkWell(
                    borderRadius: BorderRadius.circular(8),
                    onTap: () => Navigator.of(context).push(
                      MaterialPageRoute<void>(
                        settings: RouteSettings(
                          name: AppRoutes.serviceDetails,
                          arguments: row.id,
                        ),
                        builder: (_) => ServiceDetailsScreen(
                          service: row,
                          catalog: widget.catalog,
                        ),
                      ),
                    ),
                    child: Padding(
                      padding: const EdgeInsets.all(16),
                      child: Column(
                        crossAxisAlignment: CrossAxisAlignment.start,
                        children: [
                          Icon(row.facility.icon, color: bookingNavy, size: 24),
                          const SizedBox(height: 12),
                          Text(
                            row.name,
                            style: const TextStyle(
                              color: bookingNavy,
                              fontSize: 16,
                              fontWeight: FontWeight.w700,
                            ),
                          ),
                          const SizedBox(height: 4),
                          Text(
                            row.category,
                            style: const TextStyle(color: bookingMuted),
                          ),
                          if (row.facility.description.isNotEmpty)
                            Padding(
                              padding: const EdgeInsets.only(top: 6),
                              child: Text(
                                row.facility.description,
                                style: const TextStyle(color: bookingMuted),
                                maxLines: 2,
                                overflow: TextOverflow.ellipsis,
                              ),
                            ),
                          const SizedBox(height: 12),
                          const Row(
                            children: [
                              Flexible(
                                child: Text(
                                  'View Service',
                                  style: TextStyle(
                                    color: bookingNavy,
                                    fontWeight: FontWeight.w600,
                                  ),
                                ),
                              ),
                              SizedBox(width: 6),
                              Icon(
                                LucideIcons.arrowRight,
                                size: 16,
                                color: bookingNavy,
                              ),
                            ],
                          ),
                        ],
                      ),
                    ),
                  ),
                ),
              ),
        ],
      ),
    );
  }
}
