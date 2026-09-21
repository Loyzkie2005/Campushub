from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from accounts.models import User
from modules.facilities.services.facility_configuration import validate_facility_payload

from .models import MarketplaceOrder, Product
from .views import (
    _normalize_person_name,
    _password_validation_error,
    _validate_mobile_profile,
    serialize_marketplace_order,
)


class MobileAccountValidationTests(SimpleTestCase):
    def test_name_initial_is_normalized_to_uppercase(self):
        self.assertEqual(_normalize_person_name("  lester  "), "Lester")
        self.assertEqual(_normalize_person_name("bulay"), "Bulay")

    def test_strong_password_is_accepted(self):
        self.assertIsNone(_password_validation_error("CampusHub1!"))

    def test_weak_passwords_are_rejected(self):
        weak_passwords = (
            "Short1!",
            "campushub1!",
            "CAMPUSHUB1!",
            "CampusHub!",
            "CampusHub1",
            "Campus Hub1!",
        )

        for password in weak_passwords:
            with self.subTest(password=password):
                self.assertIsNotNone(_password_validation_error(password))

    def test_student_and_faculty_require_an_institutional_id(self):
        self.assertIsNotNone(
            _validate_mobile_profile("student", "", "09171234567")
        )
        self.assertIsNone(
            _validate_mobile_profile("faculty", "FAC-12345", "09171234567")
        )

    def test_guest_does_not_require_an_institutional_id(self):
        self.assertIsNone(
            _validate_mobile_profile("guest", "", "+639171234567")
        )

    def test_profile_rejects_invalid_contact_number(self):
        self.assertIsNotNone(
            _validate_mobile_profile("student", "2023304615", "123")
        )


class MarketplaceOrderSerializerTests(TestCase):
    def test_message_to_seller_is_in_order_response(self):
        order = MarketplaceOrder.objects.create(
            product_name="Banana Cue",
            message_to_seller="Please prepare it by noon.",
            quantity=1,
            unit_price=Decimal("50.00"),
            total_price=Decimal("50.00"),
        )

        payload = serialize_marketplace_order(order)

        self.assertEqual(
            payload["message_to_seller"],
            "Please prepare it by noon.",
        )


class MarketplaceRecommendationTests(TestCase):
    def test_recommended_products_endpoint_returns_approved_products(self):
        seller = User.objects.create_user(
            username="recommendation-seller",
            password="CampusHub1!",
            role="Seller",
        )
        product = Product.objects.create(
            seller=seller,
            name="Campus Snack",
            category="Snacks",
            price=Decimal("25.00"),
            stock=10,
            approval_status=Product.STATUS_APPROVED,
        )

        response = self.client.get(reverse("recommended_products"))

        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json()["products"][0]["id"], product.id)


class FacilityConfigurationTests(SimpleTestCase):
    def valid_payload(self, facility_type):
        payloads = {
            "covered_court": {
                "mode": "slot",
                "price_type": "hour",
                "capacity": 100,
                "workflow_config": {"operating_hours": "8:00 AM-5:00 PM"},
            },
            "function_hall": {
                "mode": "slot",
                "price_type": "session",
                "capacity": 80,
                "workflow_config": {"operating_hours": "8:00 AM-8:00 PM"},
            },
            "hostel": {
                "mode": "room",
                "price_type": "night",
                "rooms_units": 10,
                "room_type": "Standard Room",
                "workflow_config": {
                    "capacity_per_room": "2",
                    "check_in_time": "14:00",
                    "check_out_time": "12:00",
                },
            },
            "food_analysis": {
                "mode": "service",
                "price_type": "service",
                "amenities": ["Protein Analysis"],
                "workflow_config": {"turnaround_information": "Two weeks"},
            },
            "training_kitchen": {
                "mode": "assessment",
                "price_type": "session",
                "capacity": 20,
                "workflow_config": {"assessment_service_type": "Cookery NC II"},
            },
            "lease_space": {
                "mode": "lease",
                "price_type": "monthly",
                "rooms_units": 3,
                "workflow_config": {"area_size": "45 sq m"},
            },
        }
        return {
            "name": "Test Facility",
            "facility_type": facility_type,
            "location": "Main Campus",
            "status": "available",
            "rate": "1000",
            "amenities": [],
            "workflow_config": {},
            **payloads[facility_type],
        }

    def test_all_supported_facility_types_are_valid(self):
        for facility_type in (
            "covered_court",
            "function_hall",
            "hostel",
            "food_analysis",
            "training_kitchen",
            "lease_space",
        ):
            with self.subTest(facility_type=facility_type):
                cleaned = validate_facility_payload(self.valid_payload(facility_type))
                self.assertEqual(cleaned["facility_type"], facility_type)

    def test_incompatible_booking_mode_is_rejected(self):
        payload = self.valid_payload("covered_court")
        payload["mode"] = "room"

        with self.assertRaisesMessage(ValidationError, "must use Slot-Based"):
            validate_facility_payload(payload)

    def test_incompatible_price_type_is_rejected(self):
        payload = self.valid_payload("hostel")
        payload["price_type"] = "hour"

        with self.assertRaisesMessage(ValidationError, "supports only: Per Night"):
            validate_facility_payload(payload)

    def test_type_specific_required_field_is_rejected(self):
        payload = self.valid_payload("food_analysis")
        payload["amenities"] = []

        with self.assertRaisesMessage(ValidationError, "Add at least one service"):
            validate_facility_payload(payload)

    def test_slot_details_are_not_part_of_the_facility_form_payload(self):
        payload = self.valid_payload("covered_court")
        payload["slots"] = "Manually entered schedule"

        cleaned = validate_facility_payload(payload)

        self.assertNotIn("slots", cleaned)

    def test_irrelevant_room_fields_are_cleared(self):
        payload = self.valid_payload("covered_court")
        payload.update({"rooms_units": 4, "room_type": "Standard Room"})

        cleaned = validate_facility_payload(payload)

        self.assertIsNone(cleaned["rooms_units"])
        self.assertIsNone(cleaned["room_type"])
