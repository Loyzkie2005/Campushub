"""Search labels must distinguish history-based results from general discovery."""
from decimal import Decimal
from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse

from accounts.models import User
from api.models import Product, ProductInteraction
from modules.marketplace.services.recommendation import get_recommended_products


class SearchRecommendationTests(TestCase):
    def setUp(self):
        seller = User.objects.create_user(username="search-owner", role="Seller")
        self.seed = Product.objects.create(
            seller=seller, name="Chocolate Cookie", price=Decimal("20"),
            stock=10, approval_status=Product.STATUS_APPROVED,
        )
        self.related = Product.objects.create(
            seller=seller, name="Chocolate Cake", price=Decimal("40"),
            stock=8, approval_status=Product.STATUS_APPROVED,
        )
        self.matrix = patch(
            "modules.marketplace.services.recommendation._content_similarity_matrix",
            return_value=(None, None),
        )
        self.matrix.start()
        self.addCleanup(self.matrix.stop)

    def test_no_history_does_not_return_general_products_as_personal(self):
        self.assertEqual(get_recommended_products(user_id=73, personalized_only=True), [])
        self.assertTrue(get_recommended_products(user_id=73))

    def test_no_account_or_no_similarity_has_no_personal_fallback(self):
        self.assertEqual(get_recommended_products(personalized_only=True), [])
        ProductInteraction.objects.create(user_id=73, product=self.seed)
        self.assertEqual(get_recommended_products(user_id=73, personalized_only=True), [])

    def test_personal_results_use_existing_history_scores(self):
        ProductInteraction.objects.create(user_id=73, product=self.seed)
        with patch("modules.marketplace.services.recommendation._similarity_scores",
                   return_value=[(self.related.pk, 0.75)]):
            rows = get_recommended_products(user_id=73, personalized_only=True)
        self.assertEqual([p.pk for p in rows], [self.related.pk])

    def test_endpoint_opt_in_does_not_change_existing_fallback(self):
        url = reverse("recommended_products")
        response = self.client.get(url, {"user_id": 73, "personalized_only": "1"})
        self.assertEqual(response.status_code, 200)
        self.assertTrue(response.json()["personalized_only"])
        self.assertEqual(response.json()["products"], [])
        self.assertTrue(self.client.get(url).json()["products"])

    def test_explicit_seed_cannot_label_general_results_as_personal(self):
        self.assertEqual(get_recommended_products(
            user_id=73, seed_product_id=self.seed.pk, personalized_only=True), [])

    def test_archived_and_pending_records_remain_excluded(self):
        self.related.is_archived = True
        self.related.save(update_fields=["is_archived"])
        self.seed.approval_status = Product.STATUS_PENDING
        self.seed.save(update_fields=["approval_status"])
        self.assertEqual(get_recommended_products(), [])
