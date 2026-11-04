"""Permission-scoped Products filtering; availability retains Inventory's exact rules."""
from django.db.models import Case, Count, F, Q, Value, When
from django.db.models.functions import Coalesce, Concat
from django.utils import timezone
from .inventory import iter_product_low_stock


def low_stock_ids(products):
    fields = ('id', 'stock', 'category', 'expiry_date', 'customization_enabled',
              'customization_options', 'low_stock_threshold', 'product_type')
    today = timezone.localdate()
    return [product.pk for product in products.filter(is_archived=False, product_type='single')
            .only(*fields).iterator(chunk_size=500) if any(iter_product_low_stock(product, today=today))]


def catalog_selection(products, params):
    """Return filtered queryset, authorized overall counts and normalized controls."""
    stats = products.aggregate(total=Count('pk'), pending=Count('pk', filter=Q(approval_status='pending')),
        approved=Count('pk', filter=Q(approval_status='approved')),
        rejected=Count('pk', filter=Q(approval_status='rejected', is_archived=False)),
        archived=Count('pk', filter=Q(is_archived=True)))
    alerts = low_stock_ids(products)
    stats['low_stock'] = len(alerts)
    values = {key: (params.get(key) or '').strip() for key in
              ('search', 'status', 'program', 'major', 'category', 'inventory_status')}
    listing = params.get('listing_status', 'active').strip()
    values['listing_status'] = listing if listing in ('active', 'archived') else ''
    if values['status'] not in ('pending', 'approved', 'rejected'): values['status'] = ''
    if values['inventory_status'] not in ('low_stock', 'out_of_stock'): values['inventory_status'] = ''
    if values['listing_status']: products = products.filter(is_archived=values['listing_status'] == 'archived')
    if values['status']: products = products.filter(approval_status=values['status'])
    if values['category']: products = products.filter(category=values['category'])
    products = products.annotate(catalog_program=Coalesce('department_id', 'seller__department_id', 'mobile_seller__department_id'),
        catalog_major=Case(When(department_id__isnull=False, then=F('major_id')),
            default=Coalesce('seller__major_id', 'mobile_seller__major_id')))
    for key, field in (('program', 'catalog_program'), ('major', 'catalog_major')):
        if values[key]:
            products = products.filter(**{field: int(values[key])}) if values[key].isdecimal() else products.none()
    if values['search']:
        products = products.annotate(catalog_seller=Concat(Coalesce('mobile_seller__first_name', 'seller__first_name', Value('')), Value(' '),
            Coalesce('mobile_seller__last_name', 'seller__last_name', Value(''))))
        term = values['search']
        from api.models import InventorySKU
        sku_matches = [sku.product_id for sku in InventorySKU.objects.filter(product__in=products.values('pk'))
            .only('id', 'product_id', 'prefix', 'variant_code').iterator(chunk_size=500) if term.casefold() in sku.code.casefold()]
        products = products.filter(Q(name__icontains=term) | Q(catalog_seller__icontains=term)
            | Q(seller__username__icontains=term) | Q(mobile_seller__username__icontains=term)
            | Q(pk__in=sku_matches)).distinct()
    if values['inventory_status'] == 'low_stock': products = products.filter(pk__in=alerts)
    elif values['inventory_status'] == 'out_of_stock':
        from .inventory import get_product_quantity_status
        from .bundles import prime_bundle_inventory
        depleted = [product.pk for product in prime_bundle_inventory(products) if get_product_quantity_status(product) == 'out_of_stock']
        products = products.filter(pk__in=depleted)
    return products.order_by('-submitted_at', '-pk'), stats, values
