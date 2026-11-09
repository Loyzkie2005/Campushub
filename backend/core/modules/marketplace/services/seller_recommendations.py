"""Seller-safe projections of live pairs and explicitly completed demo research.

No mining on seller GETs; demo identities never become PostgreSQL IDs implicitly.
"""
import hashlib
import json
import os
from pathlib import Path
from tempfile import NamedTemporaryFile

from django.conf import settings

from accounts.models import AccountActivity
from api.models import BundleRecommendation, Product, SellerBundleSuggestion
from .bundle_suggestions import DATASET, DISCLOSURE, thresholds
from .bundles import eligible_component

DISMISSED = 'SELLER_RECOMMENDATION_DISMISSED'


def _admin_identity(value):
    value = str(value)
    return int(value) if value.isascii() and value.isdigit() and 0 < len(value) <= 18 else None


def admin_response(row):
    """Read actual seller decisions and linked submissions, including history."""
    owner = row.product_a.mobile_seller_id
    bundles = row.created_bundles.filter(mobile_seller_id=owner, product_type=Product.TYPE_BUNDLE)
    if bundles.exists():
        return 'bundle_created'
    decision = AccountActivity.objects.filter(account_source='mobile', account_id=owner,
        module='Marketplace', result=AccountActivity.RESULT_SUCCESS,
        activity_type='BUNDLE_SUGGESTION_UPDATED', metadata__recommendation_id=row.pk,
        metadata__decision__in=['accepted', 'declined']).order_by('-created_at', '-pk').values_list(
            'metadata__decision', flat=True).first()
    if decision:
        return decision
    choice = SellerBundleSuggestion.objects.filter(seller_id=owner,
        product_a_id=row.product_a_id, product_b_id=row.product_b_id).first()
    if choice and choice.state == 'dismissed':
        return 'declined'
    return 'pending'


def admin_recommendations(account):
    """Only persisted recommendations explicitly sent to this seller; GET never mines."""
    from .bundle_monitoring import eligible_pair
    records = BundleRecommendation.objects.filter(sent_at__isnull=False,
        product_a__mobile_seller=account, product_b__mobile_seller=account).select_related(
        'product_a__mobile_seller', 'product_b__mobile_seller').order_by('-sent_at', '-pk')
    rows = []
    for row in records:
        status = admin_response(row)
        eligible = eligible_pair(row)
        products = []
        for product in (row.product_a, row.product_b):
            images = product.get_image_list()
            products.append({'id': product.pk, 'name': product.name,
                'image_url': images[0] if images else '', 'catalog_id': product.pk})
        rows.append({'id': str(row.pk), 'source': 'admin', 'revision': '',
            'products': products, 'status': status,
            'can_create': eligible and status in ('pending', 'accepted'),
            'creation_reason': '' if eligible else 'These products are no longer eligible.',
            'sent_at': row.sent_at.isoformat()})
    rows.sort(key=lambda item: item['status'] != 'pending')
    return {'source': 'admin', 'rows': rows, 'error': False, 'status': 'ready', 'revision': ''}


def accepted_admin_pair(account, identity, product_ids):
    """Used inside the existing product transaction, never as a new submission API."""
    from .bundle_monitoring import eligible_pair
    row = BundleRecommendation.objects.select_for_update(of=('self',)).filter(
        pk=_admin_identity(identity),
        sent_at__isnull=False, product_a__mobile_seller=account,
        product_b__mobile_seller=account).select_related(
            'product_a__mobile_seller', 'product_b__mobile_seller').first()
    if (row is None or set(product_ids) != {row.product_a_id, row.product_b_id}
            or not eligible_pair(row) or admin_response(row) != 'accepted'):
        raise ValueError('Accept an eligible recommendation that has not already created a bundle.')
    return row


def admin_recommendation_action(request, account, data):
    """Lock seller and pair in the same order as product submission; decisions are idempotent."""
    from django.db import transaction
    from accounts.activity_logging import log_marketplace_event
    from api.models import SellerRequest
    from ..mobile_seller_views import latest
    from .bundle_monitoring import eligible_pair
    from api.views import serialize_product
    with transaction.atomic():
        application = latest(account, 'mobile')
        application = SellerRequest.objects.select_for_update().get(pk=application.pk)
        if application.status != 'approved' or application.is_suspended:
            raise RecommendationError('Approved active seller access is required.', 403)
        row = BundleRecommendation.objects.select_for_update(of=('self',)).filter(
            pk=_admin_identity(data['id']),
            sent_at__isnull=False, product_a__mobile_seller=account,
            product_b__mobile_seller=account).select_related(
                'product_a__mobile_seller', 'product_b__mobile_seller').first()
        if row is None:
            raise RecommendationError('Recommendation not found.', 404)
        status, action = admin_response(row), data['action']
        desired = {'accept': 'accepted', 'decline': 'declined'}.get(action)
        if action not in ('accept', 'decline', 'validate'):
            raise RecommendationError('Choose Accept or Decline.', 400)
        if status == 'bundle_created' or (status == 'declined' and desired != 'declined'):
            raise RecommendationError('This recommendation already has a final response.')
        if status == 'accepted' and action == 'decline':
            raise RecommendationError('This recommendation was already accepted.')
        if action != 'decline' and not eligible_pair(row):
            raise RecommendationError('These products are no longer eligible.')
        if action == 'validate' and status != 'accepted':
            raise RecommendationError('Accept this recommendation before creating a bundle.')
        if desired and desired != status:
            SellerBundleSuggestion.objects.update_or_create(seller=account,
                product_a=row.product_a, product_b=row.product_b,
                defaults={'state': 'saved' if action == 'accept' else 'dismissed'})
            log_marketplace_event(request, account=account, source='mobile',
                activity_type='BUNDLE_SUGGESTION_UPDATED',
                activity=f'Seller {desired} an admin bundle recommendation.',
                metadata={'recommendation_id': row.pk, 'decision': desired,
                          'product_ids': [row.product_a_id, row.product_b_id]})
            status = desired
        return {'id': str(row.pk), 'source': 'admin', 'revision': '', 'status': status,
                'products': [serialize_product(product, request) for product in (row.product_a, row.product_b)]}


class RecommendationError(ValueError):
    def __init__(self, message, status=409):
        super().__init__(message)
        self.status = status


def demo_report_path():
    return Path(getattr(settings, 'CAMPUSHUB_SELLER_DEMO_REPORT_PATH', '') or
                settings.BASE_DIR / 'var' / 'reports' / 'seller-bundle-demo.v1.json')


def publish_demo(snapshot, result, limits):
    """Called only after the existing Super Admin research authorization succeeds."""
    rows = [{
        'id': row['id'],
        'products': [{key: product[key] for key in ('id', 'seller_id', 'name')}
                     for product in row['products']],
    } for row in result['rows']]
    saved = {'format': 1, 'source': 'synthetic', 'version': snapshot['version'],
             'limits': list(limits), 'rows': rows}
    path = demo_report_path()
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = None
    try:
        with NamedTemporaryFile(mode='w', encoding='utf-8', dir=path.parent,
                                prefix='.seller-demo-', suffix='.tmp', delete=False) as stream:
            temporary = Path(stream.name)
            json.dump(saved, stream, ensure_ascii=False)
            stream.flush()
            os.fsync(stream.fileno())
        os.replace(temporary, path)
    finally:
        if temporary is not None:
            temporary.unlink(missing_ok=True)


def _demo():
    try:
        saved = json.loads(demo_report_path().read_text(encoding='utf-8'))
    except FileNotFoundError:
        return None
    if (not isinstance(saved, dict) or saved.get('format') != 1
            or saved.get('source') != 'synthetic' or not isinstance(saved.get('rows'), list)):
        raise ValueError('Invalid generated demo report.')
    path = Path(getattr(settings, 'CAMPUSHUB_SYNTHETIC_ORDER_ITEMS_PATH', '') or DATASET)
    if (saved.get('limits') != list(thresholds())
            or saved.get('version') != hashlib.sha256(path.read_bytes()).hexdigest()):
        return None
    for row in saved['rows']:
        if (not isinstance(row, dict) or not isinstance(row.get('id'), str)
                or not isinstance(row.get('products'), list) or len(row['products']) != 2
                or any(not isinstance(product, dict) or
                       any(not isinstance(product.get(key), str) or not product[key]
                           for key in ('id', 'seller_id', 'name')) for product in row['products'])
                or row['products'][0]['seller_id'] != row['products'][1]['seller_id']):
            raise ValueError('Invalid generated demo pair.')
    return saved


def hidden_ids(account, source, revision):
    return set(AccountActivity.objects.filter(
        account_source='mobile', account_id=account.pk, module='Marketplace',
        activity_type=DISMISSED, result=AccountActivity.RESULT_SUCCESS,
        metadata__recommendation_source=source, metadata__revision=revision,
    ).values_list('metadata__recommendation_id', flat=True))


def seller_recommendations(account, source='live', *, live_result=None, include_hidden=False):
    if source == 'admin':
        return admin_recommendations(account)
    if source not in {'live', 'synthetic'}:
        raise RecommendationError('Choose Live Data or Synthetic Demo.', 400)
    result = {'source': source, 'label': 'Synthetic Demo' if source == 'synthetic' else 'Live Data',
              'rows': [], 'error': False, 'message': '', 'detail': '', 'revision': '',
              'disclosure': DISCLOSURE if source == 'synthetic' else '', 'available': True,
              'status': 'ready'}
    if source == 'live':
        if live_result is None:
            from ..mobile_seller_views import live_suggestions
            live_result = live_suggestions(account)
        result.update({key: live_result.get(key, default) for key, default in
                       (('error', False), ('message', ''), ('detail', ''))})
        choices = {(row.product_a_id, row.product_b_id): row.state for row in
                   SellerBundleSuggestion.objects.filter(seller=account)}
        source_rows = []
        for row in live_result['rows']:
            ids = tuple(sorted(int(product['id']) for product in row['products']))
            if choices.get(ids) == 'dismissed':
                continue
            source_rows.append({**row, 'saved': choices.get(ids) == 'saved'})
    else:
        try:
            saved = _demo()
        except (OSError, ValueError):
            result.update(error=True, status='error', message='Unable to load bundle suggestions.')
            return result
        if saved is None:
            result.update(available=False, status='not_generated',
                          detail='A Super Admin must run Synthetic Analysis in Research Analytics first.')
            return result
        result['revision'] = saved['version']
        source_rows = saved['rows']

    owned = {product.pk: product for product in Product.objects.filter(
        mobile_seller=account).select_related('mobile_seller')}
    mapping = getattr(settings, 'CAMPUSHUB_SYNTHETIC_PRODUCT_MAP', {})
    if not isinstance(mapping, dict):
        mapping = {}  # Invalid configuration must never enable creation.
    hidden = set() if include_hidden else hidden_ids(account, source, result['revision'])
    for row in source_rows:
        if row['id'] in hidden:
            continue
        products, verified = [], []
        for item in row['products']:
            identity = f"{item['seller_id']}:{item['id']}" if source == 'synthetic' else item['id']
            product_id = mapping.get(identity) if source == 'synthetic' else item['id']
            if source == 'live':
                product_id = int(product_id)
            product = owned.get(product_id) if type(product_id) is int else None
            if product is not None and eligible_component(product, f'mobile:{account.pk}'):
                images = product.get_image_list()
                products.append({'id': product.pk, 'name': product.name,
                                 'image_url': images[0] if images else '', 'catalog_id': product.pk})
                verified.append(product.pk)
            else:
                products.append({'id': identity, 'name': item['name'], 'image_url': '', 'catalog_id': None})
            if source == 'synthetic':
                products[-1]['source_id'] = identity
        can_create = len(verified) == 2 and len(set(verified)) == 2
        # A stale live pair must not be exposed as another owner's catalog data.
        if source == 'live' and not can_create:
            continue
        result['rows'].append({'id': row['id'], 'source': source, 'revision': result['revision'],
            **({'synthetic_seller_id': row['products'][0]['seller_id']} if source == 'synthetic' else {}),
            'products': products, 'saved': row.get('saved', False), 'can_create': can_create,
            'creation_reason': '' if can_create else
                'Demo only: both products need a verified mapping to your approved catalog before creating a bundle.'})
    result['status'] = 'error' if result['error'] else ('ready' if source_rows else 'no_qualifying_pairs')
    return result


def validated_pair(account, source, identity, revision=None):
    result = seller_recommendations(account, source)
    if result['error']:
        raise RecommendationError('Unable to verify this suggestion. Retry.', 503)
    if revision is not None and revision != result['revision']:
        raise RecommendationError('This suggestion changed. Refresh Suggested Product Bundles.')
    row = next((row for row in result['rows'] if row['id'] == identity), None)
    if row is None:
        raise RecommendationError('This suggestion no longer qualifies.')
    if not row['can_create']:
        raise RecommendationError(row['creation_reason'])
    return row
