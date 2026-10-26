// Isolated widget-test fixtures only; never imported by production screens.
import 'package:campushub/module_app/models/product_item.dart';
import 'package:campushub/module_app/models/service_item.dart';
import 'package:campushub/module_app/services/service_catalog.dart';
import 'package:campushub/module_app/services/facility_service.dart';
import 'package:flutter/material.dart';

class HomeTestCatalog extends ServiceCatalog {
  List<ServiceItem> rows = [
    ServiceItem.fromJson({
      'id': 'test-lab',
      'name': 'Test Laboratory',
      'status': 'active',
      'facility_type': 'food_analysis',
      'category_label': 'Laboratory Service',
      'description': 'Sample analysis information',
      'location': 'Test Office',
    }),
  ];
  bool fail = false;
  int calls = 0;
  @override
  Future<List<ServiceItem>> fetchServices() async {
    calls++;
    if (fail) throw const ServiceCatalogException('offline');
    return rows;
  }

  @override
  Future<ServiceItem> fetchService(String id) async =>
      rows.firstWhere((row) => row.id == id);
}

Future<List<ProductItem>> homeProducts() async => [
  const ProductItem(
    'Test Chocolate',
    '\u20b150.00',
    Icons.shopping_bag_outlined,
    Colors.white,
    seller: 'Test Seller',
    category: 'Food & Beverages',
    stock: 20,
    soldCount: 2,
  ),
  const ProductItem(
    'Test Notebook',
    '\u20b130.00',
    Icons.shopping_bag_outlined,
    Colors.white,
    seller: 'Test Seller',
    category: 'School Supplies',
    stock: 4,
  ),
];

Future<FacilityServiceResult> homeFacilities() async =>
    const FacilityServiceResult(
      success: true,
      facilities: [
        {
          'id': 'test-court',
          'name': 'Test Covered Court',
          'facility_type': 'covered_court',
          'status': 'available',
          'capacity': 500,
          'capacity_label': '300\u2013500 pax',
        },
      ],
    );
