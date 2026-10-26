"""Live, read-only recommendations; explicit CSV analysis is research-only."""
import csv
import re
from collections import defaultdict
from copy import deepcopy
from datetime import datetime
from decimal import Decimal, InvalidOperation
from functools import lru_cache
from pathlib import Path

from django.conf import settings
from django.db import DatabaseError
from django.db.models import Q
from django.urls import reverse

from .analytics import (MARKET_BASKET_MIN_ORDERS, MARKET_BASKET_MIN_MULTI_ITEM_ORDERS,
                        calculate_market_basket, valid_sales_queryset, _approved_seller_ids, _approved_mobile_seller_ids)


DISCLOSURE = (
    'The transaction dataset used for association-rule mining is synthetic and is '
    'used solely for system demonstration, development, testing, and evaluation of '
    'the Apriori algorithm. It does not represent actual CampusHub marketplace '
    'transactions or customer purchasing behavior.'
)
DATASET = Path(__file__).resolve().parents[1] / 'data' / 'synthetic_order_items.csv'
EMPTY_MESSAGE = 'No bundle suggestions available yet.'
EMPTY_DETAIL = 'Suggestions will appear after sufficient completed marketplace transactions are recorded.'


def can_view_bundle_suggestions(user):
    """Share the existing GET API's access boundary with dashboard rendering."""
    from accounts.role_permissions import user_has_admin_access
    return (user.is_authenticated
            and (user.is_superuser or user.role.strip().lower() in {'marketplace admin', 'super admin'})
            and user_has_admin_access(user)
            and user.has_perm('accounts.can_view_marketplace_analytics'))


def dashboard_bundle_suggestions(user, *, limit=3):
    """Read saved live results only; dashboard GET never runs Apriori or writes."""
    if user.is_superuser or (user.role or '').strip().lower() == 'super admin':
        # Generation is an explicit operator action, never part of dashboard GET.
        result = {'source': 'live', 'read_only': True, 'dashboard_limit': limit}
        from .bundle_monitoring import recommendations_for, presentation, activity_summary
        try:
            result['monitor_rows'] = []
            for row in recommendations_for(user).filter(is_current=True)[:min(limit, 3)]:
                item = presentation(row)
                if not item['eligible']:
                    continue
                result['monitor_rows'].append({key: item[key] for key in
                    ('id', 'products', 'product_a', 'product_b', 'seller', 'academic', 'response', 'delivery')})
            result['monitor_error'] = False
        except DatabaseError:
            result['monitor_rows'], result['monitor_error'] = [], True
        try:
            result['activity'] = activity_summary(user)
        except DatabaseError:
            result['activity'] = {'error': True, 'has_activity': False, 'summary': None}
        try:
            suggested = recommendations_for(user).filter(is_current=True).count()
        except DatabaseError:
            suggested = None
        result['error'] = suggested is None
        summary = result['activity']['summary'] if not result['activity']['error'] else {}
        result['dashboard_summary'] = {'suggested': suggested, 'sent': summary.get('sent'),
            'awaiting': summary.get('awaiting'), 'created': summary.get('created')}
        return result
    from .bundle_monitoring import activity_summary, recommendations_for, presentation
    result = {'source': 'live', 'read_only': True, 'error': False, 'monitor_rows': []}
    try:
        current = recommendations_for(user).filter(is_current=True)
        suggested = current.count()
        result['unsent_count'] = current.filter(sent_at__isnull=True).count()
    except DatabaseError:
        suggested = None
        result.update(error=True, unsent_count=None)
    try:
        # Bounded saved-record preview; reuse the existing same-owner eligibility check.
        for row in recommendations_for(user).filter(is_current=True).order_by('-generated_at', '-pk')[:min(limit, 3)]:
            item = presentation(row)
            if item['eligible']:
                preview = {key: item[key] for key in ('id', 'seller', 'response', 'delivery')}
                preview['products'] = [{key: product[key] for key in ('id', 'name', 'image_url')}
                                       for product in item['products']]
                result['monitor_rows'].append(preview)
        result['monitor_error'] = False
    except DatabaseError:
        result['monitor_error'] = True
    try:
        result['activity'] = activity_summary(user, include_rates=True)
    except DatabaseError:
        result['activity'] = {'error': True, 'has_activity': False, 'summary': None}
    activity = result['activity']
    summary = activity['summary'] if not activity['error'] else {}
    result['dashboard_summary'] = {
        'suggested': suggested,
        'sent': summary.get('sent'), 'awaiting': summary.get('awaiting'), 'created': summary.get('created'),
    }
    from .bundle_monitoring import saved_analysis_summary
    result['analysis_summary'] = saved_analysis_summary(user)
    return result


def recommendation_presentation(result, *, limit=3):
    """Rank on the server and expose product-only data, never research metrics."""
    if result['source'] != 'live':
        raise ValueError('Only live recommendations can be presented.')
    def public_row(row):
        return {key: row[key] for key in ('id', 'product_a', 'product_b', 'seller', 'seller_id')} | {
            'products': [{key: product[key] for key in ('id', 'name', 'image_url')}
                         for product in row['products']]}

    frequent = sorted(result['rows'], key=lambda row: (
        -row['support'], -row['lift'], -row['confidence'], row['id']))
    # Directional results retain the calculator's ranking; A -> B and B -> A
    # are distinct qualifying rules, not a reversed copy added by the UI.
    public = {key: result[key] for key in ('source', 'read_only', 'error', 'message', 'detail',
              'transaction_count', 'qualifying_pair_count', 'page_size', 'endpoint')}
    public['rows'] = [public_row(row) for row in result['rows']]
    public['frequent_results'] = [public_row(row) for row in frequent]
    public['directional_rows'] = [public_row(row) for row in result['directional_rows']]
    public['dashboard_limit'] = limit
    public['suggested_rows'] = public['rows'][:limit]
    public['suggested_has_more'] = len(public['rows']) > limit
    public['frequent_rows'] = public['frequent_results'][:limit]
    public['cross_sell_rows'] = public['directional_rows'][:limit]
    public['frequent_has_more'] = len(public['frequent_results']) > limit
    public['cross_sell_has_more'] = len(public['directional_rows']) > limit
    return public


def thresholds():
    support = float(getattr(settings, 'CAMPUSHUB_BUNDLE_MIN_SUPPORT', .02))
    confidence = float(getattr(settings, 'CAMPUSHUB_BUNDLE_MIN_CONFIDENCE', .30))
    lift = float(getattr(settings, 'CAMPUSHUB_BUNDLE_MIN_LIFT', 1))
    if not (0 <= support <= 1 and 0 <= confidence <= 1 and 1 <= lift < float('inf')):
        raise ValueError('Invalid association-rule threshold configuration.')
    return support, confidence, lift


def _recommendation_rows(mined, catalog, *, source, directional=False):
    """Map qualified identities to their own catalog; never join CSV IDs to products."""
    rows, seen = [], set()
    for rule in mined['rows']:
        left = catalog.get(rule['product_a_id'])
        right = catalog.get(rule['product_b_id'])
        if not left or not right:
            continue
        identities = (rule['product_a_id'], rule['product_b_id'])
        pair = identities if directional else tuple(sorted(identities))
        if left['seller_id'] != right['seller_id'] or pair in seen:
            continue
        seen.add(pair)  # Collapse reverse duplicates only for equal product pairs.
        rows.append({**rule, 'id': ('->' if directional else '|').join(pair), 'products': [left, right],
                     'bundle': ' + '.join(catalog[key]['name'] for key in pair),
                     'seller': (f"Synthetic Seller {left['seller_id']}" if source == 'synthetic'
                                else left['seller']),
                     'seller_id': left['seller_id'],
                     'source': source.title(), 'status': 'Generated', 'read_only': True})
    return rows


def analyze_live(user, limits, *, mobile_seller=None):
    """Mine persisted purchases; current checkout stores one sellable item per order."""
    from api.models import Product
    from .order_access import admin_order_queryset

    from api.models import SellerRequest
    from accounts.academic import scope_seller_requests
    eligible = SellerRequest.objects.filter(status="approved", is_suspended=False).filter(
        Q(user__is_active=True, user__is_suspended=False) | Q(mobile_user__is_active=True, mobile_user__is_suspended=False))
    if user is not None:
        eligible = scope_seller_requests(eligible, user)
    if mobile_seller is not None:
        eligible = eligible.filter(mobile_user=mobile_seller)
    identities = list(eligible.order_by().values_list("user_id", "mobile_user_id"))
    web_ids = [web for web, mobile in identities if web]
    mobile_ids = [mobile for web, mobile in identities if mobile]
    from .order_access import seller_order_queryset
    authorized_orders = (seller_order_queryset(mobile_seller) if mobile_seller is not None
                         else admin_order_queryset(user))
    orders = valid_sales_queryset(user).filter(
        pk__in=authorized_orders.values('pk'),
        product__approval_status=Product.STATUS_APPROVED,
        product__is_archived=False,
    ).filter(Q(product__seller_id__in=web_ids) | Q(product__mobile_seller_id__in=mobile_ids)).select_related('product', 'product__seller', 'product__mobile_seller').order_by('pk')
    transactions, catalog, products = [], {}, {}
    basket_scopes = defaultdict(int)
    for order in orders.iterator():
        # Legacy item-name snapshots are not verified OrderItem relations. Never
        # infer a basket from them, buyer/date proximity, variants or bundle recipes.
        if isinstance(order.customization, dict) and order.customization.get('items'):
            continue
        product = order.product
        seller = product.owner
        key = str(product.pk)
        products[key] = product
        images = product.get_image_list()
        catalog[key] = {'id': product.pk, 'seller_id': product.owner_key,
                        'seller': seller.get_full_name().strip() or seller.username,
                        'name': product.name, 'category': product.category,
                        'price': f'{product.price:.2f}',
                        'image_url': images[0] if images and isinstance(images[0], str) else ''}
        # A persisted order is a genuine transaction, even if its legacy code is
        # blank. Its quantity does not represent multiple distinct product items.
        transactions.append([(key, product.name)])
        # Count only the exact baskets passed below, using the canonical product
        # academic boundary. These private cohorts never enter the API payload.
        program_id = product.department_id or seller.department_id
        major_id = product.major_id if product.department_id else seller.major_id
        basket_scopes[(program_id, major_id)] += 1
    mined = calculate_market_basket(transactions, minimum_support=limits[0],
                                   minimum_confidence=limits[1], minimum_lift=limits[2],
                                   detailed=True, limit=None)
    rows = _recommendation_rows(mined, catalog, source='live')
    directional_rows = _recommendation_rows(mined, catalog, source='live', directional=True)
    if directional_rows:
        from django.db.models import Prefetch, prefetch_related_objects
        from api.models import BundleComponent
        from .inventory import get_product_inventory_status, INVENTORY_STATUS_EXPIRED, INVENTORY_STATUS_OUT_OF_STOCK
        targets = {row['product_b_id']: products[row['product_b_id']] for row in directional_rows}
        # Reuse Inventory's availability/variant/bundle logic; batch bundle recipes.
        prefetch_related_objects([product for product in targets.values() if product.product_type == Product.TYPE_BUNDLE],
            Prefetch('bundle_components', queryset=BundleComponent.objects.select_related('product', 'product__seller')))
        available_targets = {key for key, product in targets.items()
                             if get_product_inventory_status(product) not in {
                                 INVENTORY_STATUS_EXPIRED, INVENTORY_STATUS_OUT_OF_STOCK}}
        directional_rows = [row for row in directional_rows if row['product_b_id'] in available_targets]
    return {'rows': rows, 'transaction_count': mined['eligible_orders'],
            '_analysis_basket_scopes': [
                {'program_id': program, 'major_id': major, 'baskets': count, 'multi_item_baskets': 0}
                for (program, major), count in basket_scopes.items()],
            'directional_rows': directional_rows,
            'multi_item_count': mined['multi_item_orders'], 'sufficient': bool(rows),
            'qualifying_pair_count': len(rows), 'preview_rows': rows[:5]}


def analyze_synthetic(path, limits):
    """Validate genuine transaction IDs and mine seller-qualified product identities."""
    baskets, sellers, dates, catalog = defaultdict(set), {}, {}, {}
    with Path(path).open(encoding='utf-8-sig', newline='') as stream:
        reader = csv.DictReader(stream)
        required = {'transaction_id', 'date', 'seller_id', 'product_id', 'product_name',
                    'category', 'quantity', 'unit_price_php', 'data_origin'}
        if not required.issubset(reader.fieldnames or []):
            raise ValueError('Synthetic dataset columns are incomplete.')
        count = 0
        for count, row in enumerate(reader, 1):
            if count > 100000:
                raise ValueError('Synthetic dataset exceeds the supported row limit.')
            if any(not isinstance(row.get(key), str) for key in required):
                raise ValueError('Synthetic dataset rows are incomplete.')
            txn, seller, product = (row[key].strip() for key in ('transaction_id', 'seller_id', 'product_id'))
            if any(not re.fullmatch(r'[A-Za-z0-9_-]{1,80}', value) for value in (txn, seller, product)):
                raise ValueError('Synthetic dataset identities are invalid.')
            if not txn or not seller or not product or not row['product_name'].strip():
                raise ValueError('Synthetic rows need transaction, seller and product identities.')
            if row['data_origin'].strip().upper() != 'SYNTHETIC':
                raise ValueError('Only explicitly synthetic rows are allowed in this dataset.')
            quantity = int(row['quantity'])
            price = Decimal(row['unit_price_php'])
            day = datetime.strptime(row['date'], '%m/%d/%Y').date()
            if quantity <= 0 or not price.is_finite() or price < 0:
                raise ValueError('Synthetic quantities and prices are invalid.')
            if txn in sellers and (sellers[txn] != seller or dates[txn] != day):
                raise ValueError('A synthetic transaction cannot mix sellers or dates.')
            sellers[txn], dates[txn] = seller, day
            key = f'{seller}:{product}'
            entry = {'id': product, 'seller_id': seller, 'name': row['product_name'].strip(),
                     'category': row['category'].strip(), 'price': f'{price:.2f}', 'image_url': ''}
            if key in catalog and catalog[key] != entry:
                raise ValueError('Synthetic product identities have conflicting catalog values.')
            catalog[key] = entry
            baskets[txn].add(key)  # Repeated lines/quantity never duplicate a basket item.
            if len(baskets[txn]) > 100:
                raise ValueError('A synthetic transaction has too many distinct products.')
    mined = calculate_market_basket(
        [[(key, catalog[key]['name']) for key in basket] for basket in baskets.values()],
        minimum_support=limits[0], minimum_confidence=limits[1], minimum_lift=limits[2],
        detailed=True, limit=None,
    )
    rows = _recommendation_rows(mined, catalog, source='synthetic')
    directional_rows = _recommendation_rows(mined, catalog, source='synthetic', directional=True)
    top_rules = rows[:5]  # Presentation limit only; never limit the qualifying count.
    return {'rows': rows, 'directional_rows': directional_rows, 'transaction_count': len(baskets), 'item_count': count,
            'qualifying_pair_count': len(rows), 'preview_rows': top_rules,
            'chart': {'labels': [row['bundle'] for row in top_rules],
                      'values': [row['lift'] for row in top_rules],
                      'sellers': [row['seller'] for row in top_rules]},
            'multi_item_count': mined['multi_item_orders'],
            'sufficient': (len(baskets) >= MARKET_BASKET_MIN_ORDERS
                           and mined['multi_item_orders'] >= MARKET_BASKET_MIN_MULTI_ITEM_ORDERS),
            'date_start': min(dates.values()).isoformat() if dates else '',
            'date_end': max(dates.values()).isoformat() if dates else ''}


@lru_cache(maxsize=4)
def _cached_synthetic(path, modified_ns, size, limits):
    # The file revision and thresholds invalidate cached analysis; no dashboard writes.
    return analyze_synthetic(path, limits)


def build_bundle_suggestions(user, source='live', *, mobile_seller=None):
    """Default to live; CSV analysis requires an explicit internal research call."""
    if source not in {'live', 'synthetic'}:
        raise ValueError('Unsupported recommendation source.')
    result = {'source': source, 'rows': [], 'directional_rows': [], 'read_only': True, 'error': False,
              'disclosure': DISCLOSURE if source == 'synthetic' else '',
              'transaction_count': 0, 'qualifying_pair_count': 0, 'preview_rows': [],
              'chart': {'labels': [], 'values': [], 'sellers': []}, 'page_size': 8,
              'endpoint': reverse('bundle_suggestions_api')}
    try:
        limits = thresholds()
        result['thresholds'] = {'support': limits[0] * 100, 'confidence': limits[1] * 100, 'lift': limits[2]}
        if source == 'synthetic':
            path = Path(getattr(settings, 'CAMPUSHUB_SYNTHETIC_ORDER_ITEMS_PATH', '') or DATASET)
            stat = path.stat()
            result.update(deepcopy(_cached_synthetic(str(path), stat.st_mtime_ns, stat.st_size, limits)))
            result['message'] = 'No qualifying synthetic bundle suggestions found.'
            result['detail'] = 'Try a different configured analysis threshold or dataset.'
        else:
            result.update(analyze_live(user, limits, mobile_seller=mobile_seller) if mobile_seller is not None
                          else analyze_live(user, limits))
            result['message'] = EMPTY_MESSAGE
            result['detail'] = EMPTY_DETAIL
    except (OSError, ValueError, InvalidOperation, csv.Error, TypeError, KeyError, DatabaseError):
        result.update(error=True, transaction_count=None, qualifying_pair_count=None,
                      message='Synthetic transaction dataset is unavailable.' if source == 'synthetic'
                              else 'Unable to load bundle suggestions.',
                      detail=('Retry or ask the system administrator to check the dataset and analysis configuration.'
                              if source == 'synthetic' else 'Please try again.'))
    return result
