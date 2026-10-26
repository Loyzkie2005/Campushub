// Isolated UI fixtures only; no production screen imports this file.
Map<String, dynamic> sellerWorkspaceFixture({
  List<Map<String, dynamic>>? products,
}) => {
  'products':
      products ??
      [
        {
          'id': 1,
          'name': 'Test Notebook',
          'category': 'School Supplies',
          'price': '20.00',
          'stock': 6,
          'approval_status': 'approved',
          'product_type': 'single',
        },
        {
          'id': 2,
          'name': 'Test Pen',
          'category': 'School Supplies',
          'price': '10.00',
          'stock': 2,
          'approval_status': 'approved',
          'product_type': 'single',
        },
        {
          'id': 3,
          'name': 'Test Bundle',
          'category': 'School Supplies',
          'price': '25.00',
          'stock': 2,
          'approval_status': 'approved',
          'product_type': 'bundle',
          'bundle': {
            'components': [
              {'product_name': 'Test Notebook', 'required_quantity': 1},
            ],
          },
        },
      ],
  'inventory': [
    {
      'product_id': 1,
      'product_name': 'Test Notebook',
      'name': 'Large',
      'sku': 'TST-L-001',
      'on_hand': 8,
      'reserved': 2,
      'available': 6,
      'threshold': 2,
      'status': 'in_stock',
      'status_label': 'In Stock',
    },
  ],
  'orders': [
    {
      'id': 7,
      'code': 'TEST-ORDER',
      'product_name': 'Test Notebook',
      'buyer_name': 'Test Customer',
      'quantity': 2,
      'total': '40.00',
      'status': 'Processing',
      'payment_status': 'Unpaid',
      'created_at': '2026-10-18T08:00:00+08:00',
      'pickup_location': 'Test Office',
      'items': [
        {'product_name': 'Test Notebook', 'quantity': 2, 'subtotal': '40.00'},
      ],
    },
  ],
  'overview': {'active_products': 3, 'completed_orders': 2, 'pending_orders': 0},
  'bundle_submissions': <Map<String, dynamic>>[],
  'order_count': 1,
  'orders_page': 1,
  'orders_pages': 1,
  'recommendations': {
    'error': false,
    'message': '',
    'detail': '',
    'rows': [sellerPairFixture()],
  },
  'saved_suggestions': <Map<String, dynamic>>[],
  'analytics': {
    'period': '30',
    'label': 'Last 30 Days',
    'revenue': '80.00',
    'units_sold': 4,
    'completed_orders': 2,
    'average_order_value': '40.00',
    'top_products': [],
    'trend': {
      'labels': ['Oct 18'],
      'sales': [80.0],
    },
  },
};

Map<String, dynamic> sellerPairFixture() => {
  'id': '1|2',
  'seller': 'Test Student Seller',
  'products': [
    {'id': 1, 'name': 'Test Notebook', 'image_url': ''},
    {'id': 2, 'name': 'Test Pen', 'image_url': ''},
  ],
};
