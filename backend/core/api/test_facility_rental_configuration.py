"""Configuration validation/round trips; example records exist only in tests."""
import json
import os
import uuid
from decimal import Decimal
from pathlib import Path
from unittest.mock import patch

from django.core.exceptions import ValidationError
from django.db import connection
from django.test import SimpleTestCase, TestCase
from django.urls import reverse

from accounts.models import AccountActivity, User
from accounts.role_permissions import sync_user_admin_permissions
from api.models import Booking, CampusHubUser, Facility, FacilityFeedback, FacilityPayment, Room
from api.views import _apply_facility_payload, serialize_facility
from modules.facilities.services.facility_configuration import validate_facility_payload
from modules.facilities.services.operating_schedule import WEEKDAYS
from modules.facilities.services.rental_configuration import capacity_label, pricing_label, slot_base_amount


class RentalConfigurationValidationTests(SimpleTestCase):
    def test_shared_accommodation_rates_round_trip_without_guest_count_inference(self):
        facility = self.facility(facility_type="hostel", mode="room", price_type="person_night", rate="800",
            workflow_config={"pricing":{"partner_rate":"500", "partner_occupancy_required":2}})
        self.assertEqual(facility.rate, Decimal("800"))
        self.assertEqual(facility.workflow_config["pricing"], {"partner_rate":"500", "partner_occupancy_required":2})
        self.assertIn("2 guests in one room", pricing_label(facility))
        kept = validate_facility_payload({"description":"Unrelated edit"}, facility=facility)
        self.assertEqual(kept["workflow_config"]["pricing"], facility.workflow_config["pricing"])
        with self.assertRaisesMessage(ValidationError, "requires a quote"):
            slot_base_amount(facility, Decimal("2"))
        cleared = validate_facility_payload({"price_type":"night", "workflow_config":{"discount_rules":[]}}, facility=facility)
        self.assertNotIn("pricing", cleared["workflow_config"])
        optional = self.facility(price_type="person_night", workflow_config={"pricing":{"partner_rate":"", "partner_occupancy_required":"stale"}})
        self.assertNotIn("pricing", optional.workflow_config)

    def test_shared_rate_requires_valid_money_and_same_room_occupancy(self):
        valid = {"partner_rate":"500", "partner_occupancy_required":2}
        for field, values in {
            "partner_rate": (-1, "NaN", "1.001", True, {}),
            "partner_occupancy_required": (None, "", 0, 1, -1, 1.5, True, "two"),
        }.items():
            for value in values:
                with self.subTest(field=field, value=value), self.assertRaises(ValidationError):
                    self.facility(price_type="person_night", workflow_config={"pricing":{**valid,field:value}})

    def test_discount_scope_matrix_is_enforced_for_each_pricing_method(self):
        from modules.facilities.services.rental_configuration import DISCOUNT_SCOPE_METHODS, DISCOUNT_SCOPES
        rule = {"eligible_client_type":"student", "discount_type":"fixed", "discount_value":"10", "active":False}
        for method, allowed in DISCOUNT_SCOPE_METHODS.items():
            pricing = {"base_duration":"4", "additional_hour_rate":"100"} if method == "base_hour" else {"partner_rate":"500", "partner_occupancy_required":2} if method == "person_night" else {"notes":"Manually approved quote"} if method == "custom" else {}
            for scope in DISCOUNT_SCOPES:
                details = {**rule,"applies_to":scope, **({"custom_scope":"Manually approved rental portion"} if scope == "custom" else {})}
                payload = self.payload(price_type=method, workflow_config={"pricing":pricing,"discount_rules":[details]})
                with self.subTest(method=method,scope=scope):
                    if scope in allowed: validate_facility_payload(payload)
                    else:
                        with self.assertRaises(ValidationError): validate_facility_payload(payload)
        with self.assertRaises(ValidationError):
            self.facility(price_type="person_night", workflow_config={"discount_rules":[{**rule,"applies_to":"partner_rate"}]})

    def test_daily_and_custom_configuration_do_not_apply_hourly_minimum(self):
        from datetime import date, time
        from modules.facilities.services.mobile_booking import rental_quote
        for mode in ("daily", "custom"):
            with self.subTest(mode=mode):
                facility = self.facility(mode=mode, workflow_config={"minimum_booking_duration":"not hourly"})
                self.assertEqual(facility.booking_mode, mode)
                self.assertNotIn("minimum_booking_duration", facility.workflow_config)
                with self.assertRaisesMessage(ValidationError, "different request process"):
                    rental_quote(facility, date(2026,10,20), time(8), time(9))

    def test_physical_pricing_requires_an_explicit_method(self):
        for value in (None, "", " "):
            payload = self.payload()
            if value is None: payload.pop("price_type")
            else: payload["price_type"] = value
            with self.subTest(value=value), self.assertRaises(ValidationError) as failure:
                validate_facility_payload(payload)
            self.assertIn("price_type", failure.exception.message_dict)
        facility = self.facility(price_type="session")
        kept = validate_facility_payload({"description":"Unrelated edit"}, facility=facility)
        self.assertEqual(kept["price_type"], "session")

    def test_features_and_item_fees_are_valid_without_equipment_records(self):
        features = ["Chairs", "Tables", "Sound System", "Projector", "Microphone", "Bedding", "Pickleball Net"]
        facility = self.facility(amenities=features, workflow_config={"additional_fees":[
            {"name":"Chair Rental", "amount":"10", "unit":"item", "active":True}]})
        self.assertEqual(facility.amenities, features)
        self.assertNotIn("equipment", facility.workflow_config)
        self.assertEqual(facility.workflow_config["additional_fees"][0]["name"], "Chair Rental")
        self.assertEqual(self.facility().workflow_config["additional_fees"], [])
        with self.assertRaises(ValidationError):
            self.facility(workflow_config={"equipment":[]})

    def test_fee_bases_custom_explanation_and_stale_clearing(self):
        for unit in ("item", "hour", "booking", "day", "night", "person", "fixed", "custom", "unit"):
            with self.subTest(unit=unit):
                fee = {"name":"Manually entered fee", "amount":"10.00", "unit":unit, "active":False,
                    "custom_basis":"  Agreed per-event rate  "}
                saved = self.facility(workflow_config={"additional_fees":[fee]}).workflow_config["additional_fees"][0]
                self.assertEqual(saved["unit"], unit)
                self.assertFalse(saved["active"])
                self.assertEqual(saved["amount"], "10.00")
                if unit == "custom": self.assertEqual(saved["custom_basis"], "Agreed per-event rate")
                else: self.assertNotIn("custom_basis", saved)

    def test_invalid_additional_fee_configuration_is_rejected(self):
        fee = {"name":"Chair Rental", "amount":"10", "unit":"item", "active":True}
        bad = [{}, None, {**fee,"name":" "}, {**fee,"name":{}}, {**fee,"amount":"-1"},
            {**fee,"amount":"NaN"}, {**fee,"amount":"1.001"}, {**fee,"amount":""},
            {**fee,"unit":""}, {**fee,"unit":{}}, {**fee,"active":"false"},
            {**fee,"unit":"custom","custom_basis":" "}, {**fee,"unit":"custom","custom_basis":"x"*201}]
        for row in bad:
            with self.subTest(row=row), self.assertRaises(ValidationError):
                self.facility(workflow_config={"additional_fees":[row]})

    def test_other_feature_validates_round_trips_clears_and_preserves_partial_updates(self):
        facility = self.facility(amenities=["Fans"], workflow_config={"other_feature":"  Accessible Ramp  "})
        self.assertEqual(facility.amenities, ["Fans", "Accessible Ramp"])
        self.assertEqual(facility.workflow_config["other_feature"], "Accessible Ramp")
        kept = validate_facility_payload({"description":"Unrelated edit"}, facility=facility)
        self.assertEqual(kept["amenities"], facility.amenities)
        cleared = validate_facility_payload({"workflow_config":{"other_feature":None}}, facility=facility)
        self.assertEqual(cleared["amenities"], ["Fans"])
        self.assertNotIn("other_feature", cleared["workflow_config"])
        for text in ("", " ", 42, "<b>feature</b>", "x"*201):
            with self.subTest(text=text), self.assertRaises(ValidationError):
                self.facility(workflow_config={"other_feature":text})
        with self.assertRaises(ValidationError):
            self.facility(amenities=["Other"])

    def test_legacy_equipment_metadata_is_preserved_without_new_management(self):
        facility = self.facility()
        legacy = [{"name":"Old configured item", "is_active":True, "has_additional_fee":True}]
        facility.workflow_config["equipment"] = legacy
        kept = validate_facility_payload({"description":"Unrelated edit"}, facility=facility)
        self.assertEqual(kept["workflow_config"]["equipment"], legacy)
        with self.assertRaisesMessage(ValidationError, "Equipment charges require"):
            slot_base_amount(facility, Decimal("2"))
        facility.workflow_config["equipment"][0]["is_active"] = False
        self.assertEqual(slot_base_amount(facility, Decimal("2")), Decimal("1400.00"))

    def payload(self, **changes):
        payload = {"name": "Manually Named Test Resource", "facility_type": "other", "location": "Test location",
            "custom_facility_type": "Test Rentable Space",
            "mode": "slot", "capacity": 50, "price_type": "hour", "rate": "700", "amenities": [],
            "workflow_config": {}, **changes}
        payload["workflow_config"] = {"booking_form_type": "general", **payload["workflow_config"]}
        return payload

    def facility(self, **changes):
        facility = Facility(id="ISOLATED-CONFIGURATION")
        _apply_facility_payload(facility, validate_facility_payload(self.payload(**changes)))
        return facility

    def test_capacity_range_and_independent_booking_mode(self):
        facility = self.facility(workflow_config={"capacity_min": 30})
        self.assertEqual(capacity_label(facility), "30–50 pax")
        self.assertEqual(capacity_label(self.facility()), "50 pax")
        room = self.facility(facility_type="covered_court", mode="room", price_type="person_night", rate="800")
        self.assertEqual(room.booking_mode, "room")
        self.assertIsNone(room.rooms_units)
        self.assertEqual(pricing_label(room), "₱800 / person / night")

    def test_base_pricing_and_all_other_methods_round_trip(self):
        facility = self.facility(price_type="base_hour", rate="3000", workflow_config={"pricing": {"base_duration": "4", "additional_hour_rate": "500"}})
        self.assertEqual(pricing_label(facility), "₱3,000 / first 4 hrs + ₱500/hr")
        self.assertEqual(slot_base_amount(facility, Decimal("6")), Decimal("4000.00"))
        self.assertEqual(slot_base_amount(facility, Decimal("2")), Decimal("3000.00"))
        for method in ("hour", "day", "person", "person_night", "night", "session"):
            with self.subTest(method=method):
                value = self.facility(price_type=method)
                self.assertEqual(serialize_facility(value)["price_type"], method)
        custom = self.facility(price_type="custom", rate="", workflow_config={"pricing": {"notes": "Quote based on requested equipment"}})
        self.assertEqual(custom.rate, 0)
        self.assertEqual(pricing_label(custom), "Quote based on requested equipment")

    def test_saved_pricing_summaries_do_not_assume_hourly_rates(self):
        for method, summary in (("hour", "₱500 / hour"), ("day", "₱500 / day"),
                ("person", "₱500 / person"), ("person_night", "₱500 / person / night"),
                ("night", "₱500 / night"), ("session", "₱500 fixed")):
            with self.subTest(method=method):
                self.assertEqual(pricing_label(self.facility(price_type=method, rate="500")), summary)
        custom = self.facility(price_type="custom", rate="", workflow_config={"pricing": {"notes": "Configured custom quote"}})
        self.assertEqual(pricing_label(custom), "Configured custom quote")
        custom.workflow_config["pricing"]["notes"] = "<script>invalid</script>"
        self.assertEqual(pricing_label(custom), "Custom quote")
        custom.price_type = ""
        self.assertEqual(pricing_label(custom), "Pricing needs review")

    def test_rules_deposit_and_flexible_fees(self):
        raw = {"requires_approval": False, "requires_pre_use_inspection": True, "requires_post_use_inspection": True,
            "booking_form_type": "general", "damage_deposit_applicable": True,
            "damage_deposit": {"type": "percentage", "value": "40"},
            "additional_fees": [{"name": "Admin-entered charge", "amount": "25.50", "unit": "unit", "active": False}]}
        facility = self.facility(workflow_config=raw)
        self.assertEqual(facility.workflow_config["damage_deposit"]["value"], "40")
        self.assertFalse(facility.workflow_config["requires_approval"])
        self.assertFalse(facility.workflow_config["additional_fees"][0]["active"])
        with self.assertRaises(ValidationError):
            slot_base_amount(facility, Decimal("2"))

    def test_bad_numbers_never_become_concatenated_values(self):
        for value in ("300500 pax", "30–50", -1, True, 2.5, "NaN", "Infinity", {}, [], 2147483648):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                validate_facility_payload(self.payload(capacity=value))
        for value in ("-1", "NaN", "Infinity", "1.001", True, "100000000", "1,500"):
            with self.subTest(rate=value), self.assertRaises(ValidationError):
                validate_facility_payload(self.payload(rate=value))
        with self.assertRaises(ValidationError):
            self.facility(workflow_config={"capacity_min": 60})

    def test_missing_rates_deposits_base_duration_and_fee_fields(self):
        examples = [self.payload(rate=""), self.payload(price_type="base_hour"),
            self.payload(price_type="custom"), self.payload(mode="unsupported"),
            self.payload(workflow_config={"damage_deposit_applicable": True}),
            self.payload(workflow_config={"damage_deposit_applicable": True, "damage_deposit": {"type": "percentage", "value": "101"}}),
            self.payload(workflow_config={"requires_approval": "false"}),
            self.payload(workflow_config={"additional_fees": [{"name": "", "amount": "-1", "unit": "warehouse"}]}),
            self.payload(workflow_config={"booking_form_type": []})]
        for payload in examples:
            with self.subTest(payload=payload), self.assertRaises(ValidationError):
                validate_facility_payload(payload)

    def test_explicit_hidden_settings_are_discarded(self):
        raw = {"pricing": {"base_duration": "4", "additional_hour_rate": "500"},
            "damage_deposit_applicable": False, "damage_deposit": {"type": "percentage", "value": "40"},
            "capacity_per_room": "2", "check_in_time": "14:00", "check_out_time": "11:00"}
        facility = self.facility(workflow_config=raw, room_type="Dormitory", rooms_units=5)
        for field in ("pricing", "damage_deposit", "capacity_per_room", "check_in_time", "check_out_time"):
            self.assertNotIn(field, facility.workflow_config)
        self.assertIsNone(facility.rooms_units)
        self.assertIsNone(facility.room_type)

    def test_omitted_update_fields_and_unowned_configuration_preserved(self):
        facility = self.facility(price_type="base_hour", rate="3000", workflow_config={"pricing": {"base_duration": "4", "additional_hour_rate": "500"}, "capacity_min": 30})
        facility.workflow_config["service_capacity"] = {"total": 42}
        facility.image_url = '["/media/existing.png"]'
        cleaned = validate_facility_payload({"description": "Only description updated"}, facility=facility)
        self.assertEqual(cleaned["rate"], facility.rate)
        self.assertEqual(cleaned["capacity"], 50)
        self.assertEqual(cleaned["workflow_config"], facility.workflow_config)
        self.assertEqual(cleaned["name"], facility.facility_name)
        self.assertEqual(facility.image_url, '["/media/existing.png"]')

    def test_blank_add_settings_are_honest_and_schedule_is_validated(self):
        facility = self.facility(capacity="", rate="0", workflow_config={"operating_hours": {day: None for day in WEEKDAYS}})
        self.assertEqual(facility.capacity, 0)
        self.assertEqual(facility.workflow_config["additional_fees"], [])
        self.assertNotIn("damage_deposit", facility.workflow_config)
        self.assertNotIn("capacity_min", facility.workflow_config)
        with self.assertRaises(ValidationError):
            self.facility(workflow_config={"operating_hours": {**{day: None for day in WEEKDAYS}, "monday": {"open": "17:00", "close": "08:00"}}})

    def test_legacy_text_and_zero_capacity_survive_description_update(self):
        facility = self.facility()
        facility.workflow_config = {"operating_hours": "Ask the Facilities Office", "minimum_booking_duration": "1 hour"}
        cleaned = validate_facility_payload({"description": "New text"}, facility=facility)
        self.assertEqual(cleaned["workflow_config"]["operating_hours"], "Ask the Facilities Office")
        self.assertEqual(cleaned["workflow_config"]["minimum_booking_duration"], "1")

    def test_simple_mobile_prices_unchanged_and_unsupported_quotes_fail_closed(self):
        self.assertEqual(slot_base_amount(self.facility(), Decimal("2")), Decimal("1400.00"))
        self.assertEqual(slot_base_amount(self.facility(price_type="session"), Decimal("2")), Decimal("700.00"))
        for method in ("person", "day", "person_night", "night", "custom"):
            kwargs = {"price_type": method}
            if method == "custom":
                kwargs["workflow_config"] = {"pricing": {"notes": "Manual quote"}}
            with self.subTest(method=method), self.assertRaises(ValidationError):
                slot_base_amount(self.facility(**kwargs), Decimal("2"))

    def test_custom_type_required_trimmed_and_separate_from_name(self):
        facility = self.facility(name="Campus Events Ground", custom_facility_type="  Open Grounds  ")
        self.assertEqual(facility.facility_name, "Campus Events Ground")
        self.assertEqual(facility.facility_type, "other")
        self.assertEqual(facility.custom_facility_type, "Open Grounds")
        self.assertEqual(facility.get_facility_type_display(), "Open Grounds")
        self.assertEqual(serialize_facility(facility)["facility_type_label"], "Open Grounds")
        self.assertEqual(facility.workflow_config["custom_facility_type"], "Open Grounds")
        for value in ("", "   ", None, [], {}, True, "x" * 121, "<script>bad</script>", "bad\x00type", "---", "\u200b"):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                self.facility(custom_facility_type=value)
        omitted = self.payload()
        omitted.pop("custom_facility_type")
        with self.assertRaisesMessage(ValidationError, "Specify Facility Category is required"):
            validate_facility_payload(omitted)

    def test_predefined_labels_keep_codes_and_ignore_stale_custom_values(self):
        facility = self.facility(name="Mock Hotel", facility_type="hostel", mode="room", price_type="night", custom_facility_type=[])
        self.assertEqual(facility.facility_type, "hostel")
        self.assertEqual(facility.facility_name, "Mock Hotel")
        self.assertEqual(facility.get_facility_type_display(), "Hostel / Room Accommodation")
        self.assertEqual(facility.custom_facility_type, "")
        self.assertNotIn("custom_facility_type", facility.workflow_config)

    def test_switching_from_other_clears_only_the_custom_type(self):
        facility = self.facility(custom_facility_type="Conference Room", workflow_config={"requires_pre_use_inspection": True})
        facility.workflow_config["future_setting"] = {"keep": True}
        cleaned = validate_facility_payload({"facility_type": "function_hall"}, facility=facility)
        self.assertNotIn("custom_facility_type", cleaned["workflow_config"])
        self.assertTrue(cleaned["workflow_config"]["requires_pre_use_inspection"])
        self.assertEqual(cleaned["workflow_config"]["future_setting"], {"keep": True})
        self.assertEqual(cleaned["rate"], facility.rate)

    def test_legacy_other_partial_update_does_not_invent_a_type(self):
        facility = self.facility()
        facility.workflow_config.pop("custom_facility_type")
        self.assertEqual(facility.get_facility_type_display(), "Other")
        cleaned = validate_facility_payload({"description": "Unrelated edit"}, facility=facility)
        self.assertNotIn("custom_facility_type", cleaned["workflow_config"])
        with self.assertRaises(ValidationError):
            validate_facility_payload({"custom_facility_type": "  "}, facility=facility)
        facility.facility_type = "covered_court"
        with self.assertRaises(ValidationError):
            validate_facility_payload({"facility_type": "other"}, facility=facility)

    def test_discount_rules_round_trip_without_applying_or_seeding_values(self):
        rule = {"eligible_client_type": "student", "discount_type": "percentage", "discount_value": "12.5", "applies_to": "rental_fee", "active": False}
        facility = self.facility(workflow_config={"discount_rules": [rule]})
        self.assertEqual(facility.workflow_config["discount_rules"], [rule])
        self.assertEqual(self.facility().workflow_config["discount_rules"], [])
        custom = {**rule, "eligible_client_type": "other", "discount_type": "fixed", "discount_value": "50", "applies_to": "custom", "custom_scope": "  Approved room group rate  "}
        facility = self.facility(workflow_config={"discount_rules": [custom]})
        self.assertEqual(facility.workflow_config["discount_rules"][0]["custom_scope"], "Approved room group rate")
        for client in ("internal", "immediate_family", "student", "other"):
            self.facility(workflow_config={"discount_rules": [{**rule, "eligible_client_type": client}]})
        facility = self.facility(workflow_config={"discount_rules": [{**rule, "custom_scope": "stale"}]})
        self.assertNotIn("custom_scope", facility.workflow_config["discount_rules"][0])

    def test_invalid_discount_configurations_are_rejected(self):
        base = {"eligible_client_type": "internal", "discount_type": "percentage", "discount_value": "10", "applies_to": "rental_fee", "active": True}
        rules = [None, {}, "not a list", [None], [base] * 31]
        for field, values in {
            "eligible_client_type": ([], "unknown", None),
            "discount_type": ([], "free", ""),
            "discount_value": ("", -1, True, "NaN", "100.01", "1.001"),
            "applies_to": ([], "damage_deposit", "additional_fees", "refund", "base_rate", "additional_hour_rate"),
            "active": ("false", None, 1),
        }.items():
            rules.extend([[{**base, field: value}] for value in values])
        rules.extend([[{**base, "applies_to": "custom", "custom_scope": value}] for value in ("", "  ", [], "x" * 201, "<script>")])
        for value in rules:
            with self.subTest(rules=value), self.assertRaises(ValidationError):
                self.facility(workflow_config={"discount_rules": value})

    def test_active_discount_requires_eligibility_quote_inactive_keeps_normal_quote(self):
        rule = {"eligible_client_type": "student", "discount_type": "fixed", "discount_value": "25", "applies_to": "entire_rental_rate", "active": True}
        facility = self.facility(workflow_config={"discount_rules": [rule]})
        with self.assertRaisesMessage(ValidationError, "Discount eligibility"):
            slot_base_amount(facility, Decimal("2"))
        rule["active"] = False
        self.assertEqual(slot_base_amount(self.facility(workflow_config={"discount_rules": [rule]}), Decimal("2")), Decimal("1400.00"))

    def test_booking_form_suggestions_and_inspection_defaults_preserve_false(self):
        for kind, mode, method, form in (("covered_court", "slot", "hour", "rental"),
                ("function_hall", "slot", "session", "rental"), ("hostel", "room", "night", "accommodation")):
            data = self.payload(facility_type=kind, mode=mode, price_type=method)
            data["workflow_config"].pop("booking_form_type")
            cleaned = validate_facility_payload(data)
            self.assertEqual(cleaned["workflow_config"]["booking_form_type"], form)
            self.assertTrue(cleaned["workflow_config"]["requires_pre_use_inspection"])
            self.assertTrue(cleaned["workflow_config"]["requires_post_use_inspection"])
            facility = Facility(id="NO-SAVED-INSPECTION")
            _apply_facility_payload(facility, cleaned)
            facility.workflow_config.update(requires_pre_use_inspection=False, requires_post_use_inspection=False)
            updated = validate_facility_payload({"description": "Unrelated change"}, facility=facility)
            self.assertFalse(updated["workflow_config"]["requires_pre_use_inspection"])
            self.assertFalse(updated["workflow_config"]["requires_post_use_inspection"])
        data = self.payload()
        data["workflow_config"].pop("booking_form_type")
        with self.assertRaises(ValidationError):
            validate_facility_payload(data)
        with self.assertRaises(ValidationError):
            validate_facility_payload(self.payload(mode=""))

    def test_mapped_categories_ignore_manual_booking_form_overrides(self):
        from modules.facilities.services.rental_configuration import booking_form_for_category
        for kind,mode,method,expected in (("covered_court","slot","hour","rental"),
                ("function_hall","slot","session","rental"),("hostel","room","night","accommodation")):
            for supplied in ("general","wrong-form",[],None):
                with self.subTest(kind=kind,supplied=supplied):
                    data=self.payload(facility_type=kind,mode=mode,price_type=method,
                        workflow_config={"booking_form_type":supplied})
                    cleaned=validate_facility_payload(data)
                    self.assertEqual(cleaned["workflow_config"]["booking_form_type"],expected)
                    self.assertEqual(booking_form_for_category(kind,{"booking_form_type":supplied}),expected)
        facility=self.facility(facility_type="covered_court")
        facility.workflow_config["booking_form_type"]="general"
        self.assertEqual(validate_facility_payload({"description":"Keep existing data"},facility=facility)
            ["workflow_config"]["booking_form_type"],"rental")
        updated=validate_facility_payload({"facility_type":"hostel","mode":"room","price_type":"night"},facility=facility)
        self.assertEqual(updated["workflow_config"]["booking_form_type"],"accommodation")

    def test_other_keeps_explicit_form_and_historical_label_wins(self):
        from modules.facilities.services.rental_configuration import booking_slip_label, FORM_TYPES
        for form in FORM_TYPES:
            self.assertEqual(validate_facility_payload(self.payload(workflow_config={"booking_form_type":form}))
                ["workflow_config"]["booking_form_type"],form)
        with self.assertRaises(ValidationError):
            validate_facility_payload(self.payload(workflow_config={"booking_form_type":"unknown"}))
        facility=self.facility(facility_type="covered_court")
        self.assertEqual(booking_slip_label(facility,{"form_label":"Saved Historical Form"}),"Saved Historical Form")
        self.assertEqual(booking_slip_label(facility,{}, {"booking_form_type":"accommodation"}),FORM_TYPES["accommodation"])
        self.assertEqual(booking_slip_label(facility,{}, {"booking_form_type":[]}),FORM_TYPES["rental"])
        self.assertEqual(booking_slip_label(facility),FORM_TYPES["rental"])

    def test_custom_minimum_minutes_round_trip_and_room_ignores_duration(self):
        from modules.facilities.services.operating_schedule import duration_hours
        for minutes in (1, 47, 1440):
            facility = self.facility(workflow_config={"minimum_booking_duration": f"{minutes} minutes"})
            stored = facility.workflow_config["minimum_booking_duration"]
            self.assertEqual(duration_hours(stored), duration_hours(f"{minutes} minutes"))
        for minutes in ("0 minutes", "1441 minutes", "1.5 minutes", "custom"):
            with self.subTest(value=minutes), self.assertRaises(ValidationError):
                self.facility(workflow_config={"minimum_booking_duration": minutes})
        room = self.facility(mode="room", price_type="night", workflow_config={"minimum_booking_duration": "custom"})
        self.assertNotIn("minimum_booking_duration", room.workflow_config)


class FacilityRentalAPITests(TestCase):
    def test_existing_history_survives_missing_target_without_service_leakage(self):
        event = AccountActivity.objects.create(account_source="admin", full_name="Historical Administrator",
            module="Facilities", activity_type="facility_reactivated", activity="Recorded historical action",
            result="success", metadata={"facility_id":"MISSING-HISTORICAL", "facility_name":"Historical Court"})
        AccountActivity.objects.create(account_source="admin", module="Facilities", activity_type="facility_added",
            activity="Deleted service history", result="success", metadata={"facility_id":"MISSING-SERVICE",
                "facility_name":"Historical Lab", "resource_kind":"service"})
        count = AccountActivity.objects.count()
        page = self.client.get(reverse("admin_facility_page"))
        self.assertContains(page, "Historical Court reactivated.")
        self.assertContains(page, "Historical Administrator")
        self.assertNotContains(page, "Historical Lab")
        self.assertEqual(AccountActivity.objects.count(), count)
        self.assertEqual(AccountActivity.objects.get(pk=event.pk).activity, "Recorded historical action")

    def test_management_summary_uses_recorded_performer_and_specific_configuration_actions(self):
        empty = self.client.get(reverse("admin_facility_page"))
        self.assertContains(empty, "No recent facility activity.")
        self.assertNotContains(empty, "Facility changes will appear here.")
        self.admin.first_name, self.admin.last_name = "Recorded", "Administrator"
        self.admin.save(update_fields=["first_name", "last_name"])
        self.client.force_login(self.admin)
        created = self.post(reverse("facilities_create"), self.payload)
        pk = created.json()["facility"]["id"]
        self.assertEqual(created.json()["activity"]["performed_by"], "Recorded Administrator")
        updates = (
            ({"workflow_config": {"discount_rules": [{"eligible_client_type": "student", "discount_type": "percentage", "discount_value": "10", "applies_to": "base_rate", "active": True}]}}, "facility_discount_updated"),
            ({"workflow_config": {"requires_approval": False}}, "facility_booking_config_updated"),
            ({"workflow_config": {"operating_hours": {**{day: None for day in WEEKDAYS}, "monday": {"open": "08:00", "close": "17:00"}}}}, "facility_schedule_updated"),
            ({"amenities": ["Chairs"]}, "facility_features_updated"),
        )
        for payload, event_type in updates:
            response = self.post(reverse("facilities_update", args=[pk]), payload)
            self.assertEqual(response.status_code, 200, response.content)
            event = AccountActivity.objects.latest("pk")
            self.assertEqual(event.activity_type, event_type)
            self.assertEqual(response.json()["activity"]["performed_by"], "Recorded Administrator")
            self.assertIn("•", response.json()["activity"]["time_label"])
        page = self.client.get(reverse("admin_facility_page"))
        self.assertEqual(len(page.context["recent_facility_activities"]), 5)
        self.assertContains(page, "Recorded Administrator")
        self.assertNotContains(page, "View All Activity")  # Facilities Admin has no central monitoring access.
        from modules.facilities.services.activity import facility_activity_row
        event = AccountActivity.objects.latest("pk")
        event.full_name, event.username = "", ""
        row = facility_activity_row(event)
        self.assertEqual(row["performed_by"], "System")
        self.assertFalse({"metadata", "ip_address", "user_agent", "session_identifier", "account_id", "id"} & row.keys())

    def test_view_all_uses_existing_monitoring_module_filter_and_preserves_history(self):
        self.post(reverse("facilities_create"), self.payload)
        event_count = AccountActivity.objects.count()
        super_admin = User.objects.create_superuser(username="facility-history-owner", email="history@example.com", password="TestOnly123!", role="Super Admin")
        AccountActivity.objects.create(account_source="admin", account_id=super_admin.pk, account_ref=f"admin:{super_admin.pk}",
            module="Marketplace", activity_type="product_added", activity="Unrelated product", result="success")
        self.client.force_login(super_admin)
        self.assertContains(self.client.get(reverse("admin_facility_page")), "?module=Facilities#recent-user-activity")
        response = self.client.get(reverse("admin_user_monitoring_page"), {"module": "Facilities"})
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Facilities Activity Log")
        self.assertContains(response, 'name="module" value="Facilities"')
        self.assertTrue(all(event.module == "Facilities" for event in response.context["activity_page_obj"]))
        self.assertEqual(AccountActivity.objects.count(), event_count + 1)  # Viewing does not create events.

    def test_real_facility_events_are_scoped_ordered_and_not_inferred_from_bookings(self):
        created = self.post(reverse("facilities_create"), self.payload)
        self.assertEqual(created.status_code, 201)
        pk = created.json()["facility"]["id"]
        self.assertEqual(created.json()["activity"]["title"], "Manually Named Test Resource added.")
        self.assertEqual(AccountActivity.objects.get(activity_type="facility_added").metadata["facility_id"], pk)
        first_count = AccountActivity.objects.count()
        unchanged = self.post(reverse("facilities_update", args=[pk]), {})
        self.assertEqual(unchanged.status_code, 200)
        self.assertIsNone(unchanged.json()["activity"])
        self.assertEqual(AccountActivity.objects.count(), first_count)
        updated = self.post(reverse("facilities_update", args=[pk]), {"status": "maintenance"})
        self.assertEqual(updated.json()["activity"]["title"], "Manually Named Test Resource status changed to Under Maintenance.")
        facility = Facility.objects.get(pk=pk)
        Booking.objects.create(id="AUDIT-BOOKING", facility=facility, purpose="Do not put booking changes here", status="approved")
        AccountActivity.objects.create(account_source="admin", module="Marketplace", activity_type="product_added",
            activity="Unrelated product", result="success", metadata={"facility_id": pk})
        service = Facility.objects.create(id="AUDIT-SERVICE", facility_name="Unrelated Lab", facility_type="food_analysis", booking_mode="service")
        AccountActivity.objects.create(account_source="admin", module="Facilities", activity_type="facility_added",
            activity="Unrelated service", result="success", metadata={"facility_id": service.pk, "facility_name": service.facility_name})
        summary = self.client.get(reverse("admin_facility_page")).context["recent_facility_activities"]
        self.assertEqual(len(summary), 2)
        self.assertEqual(summary[0]["description"], "Status Change")
        self.assertNotContains(self.client.get(reverse("admin_facility_page")), "Do not put booking changes here")
        self.assertEqual(self.post(reverse("facilities_archive", args=[pk]), {}).status_code, 200)
        self.assertEqual(self.post(reverse("facilities_archive", args=[pk]), {}).json()["activity"], None)
        archived = self.client.get(reverse("admin_facility_page"))
        self.assertContains(archived, "Reactivate Facility")
        self.assertContains(archived, "Edit Facility")
        self.assertContains(archived, "Manually Named Test Resource archived.")
        edit = self.post(reverse("facilities_update", args=[pk]), {"description": "Edit archived configuration"})
        self.assertTrue(edit.json()["facility"]["is_archived"])
        self.assertEqual(self.post(reverse("facilities_restore", args=[pk]), {}).json()["activity"]["description"], "Reactivation")
        self.assertIsNone(self.post(reverse("facilities_restore", args=[pk]), {}).json()["activity"])

    def test_pricing_event_summary_is_bounded_and_failed_writes_do_not_log(self):
        pk = self.post(reverse("facilities_create"), self.payload).json()["facility"]["id"]
        for rate in range(3001, 3011):
            response = self.post(reverse("facilities_update", args=[pk]), {"rate": str(rate)})
            self.assertEqual(response.status_code, 200)
            self.assertEqual(response.json()["activity"]["description"], "Pricing Update")
        response = self.client.get(reverse("admin_facility_page"))
        self.assertEqual(len(response.context["recent_facility_activities"]), 5)
        before = (Facility.objects.count(), AccountActivity.objects.count())
        failed = self.post(reverse("facilities_update", args=[pk]), {"capacity": -1})
        self.assertEqual(failed.status_code, 400)
        with patch("api.views.record_facility_activity", side_effect=RuntimeError("Audit unavailable")):
            self.assertEqual(self.post(reverse("facilities_create"), self.payload).status_code, 500)
            self.assertEqual(self.post(reverse("facilities_update", args=[pk]), {"rate": "9999"}).status_code, 500)
        self.assertEqual((Facility.objects.count(), AccountActivity.objects.count()), before)
        self.assertEqual(Facility.objects.get(pk=pk).rate, Decimal("3010"))

    def test_category_display_mapping_preserves_codes_names_and_saved_configuration(self):
        for code, category in (("covered_court", "Court / Sports Facility"), ("function_hall", "Hall / Function Space")):
            facility = Facility.objects.create(id=f"LABEL-{code}", facility_name=f"Specific {code}",
                facility_type=code, booking_mode="slot", location="Test campus", capacity=500, rate=700,
                workflow_config={"capacity_min": 300})
            response = self.client.get(reverse("admin_facility_page"))
            self.assertContains(response, category)
            self.assertContains(response, "300–500 pax")
            self.assertContains(response, "Facility Name / Display Name")
            self.assertContains(response, "Facility Category")
            updated = self.post(reverse("facilities_update", args=[facility.pk]), {"description": "Changed description only"})
            self.assertEqual(updated.status_code, 200, updated.content)
            facility.refresh_from_db()
            self.assertEqual(facility.facility_type, code)
            self.assertEqual(facility.facility_name, f"Specific {code}")
            self.assertEqual(facility.workflow_config["capacity_min"], 300)
            self.assertEqual(updated.json()["facility"]["facility_type_label"], category)

    def test_capacity_and_kpi_count_actual_rooms_not_declared_units(self):
        court = Facility.objects.create(id="COUNT-COURT", facility_name="Count Court", facility_type="covered_court",
            booking_mode="slot", rooms_units=99, capacity=500, workflow_config={"capacity_min": 300})
        hostel = Facility.objects.create(id="COUNT-HOSTEL", facility_name="Count Hostel", facility_type="hostel",
            booking_mode="room", rooms_units=6, capacity=12)
        archived = Facility.objects.create(id="COUNT-ARCHIVED", facility_name="Archived Hostel", facility_type="hostel",
            booking_mode="room", is_archived=True)
        self.assertEqual(serialize_facility(hostel)["capacity_label"], "12 pax")
        for facility in (hostel, hostel, court, archived):
            Room.objects.create(id=uuid.uuid4(), facility=facility, room_name="Configured room", capacity=2)
        response = self.client.get(reverse("admin_facility_page"))
        self.assertEqual(response.context["rooms_units_total"], 3)
        labels = {facility.pk: facility.capacity_display for facility in response.context["facilities"]}
        self.assertEqual(labels[court.pk], "300–500 pax")
        self.assertEqual(labels[hostel.pk], "2 Rooms / 12 pax")
        hostel = Facility.objects.get(pk=hostel.pk)
        self.assertEqual(serialize_facility(hostel)["capacity_label"], "2 Rooms / 12 pax")
        self.client.logout()
        with self.assertNumQueries(1):
            public = self.client.get(reverse("facilities_list"))
        self.assertEqual(public.status_code, 200)
        self.assertEqual(next(f for f in public.json()["facilities"] if f["id"] == hostel.pk)["configured_room_count"], 2)

    @classmethod
    def setUpClass(cls):
        existing = connection.introspection.table_names()
        with connection.schema_editor() as editor:
            for model in (CampusHubUser, Facility, Room, Booking, FacilityPayment, FacilityFeedback):
                if model._meta.db_table not in existing:
                    editor.create_model(model)
        super().setUpClass()

    def setUp(self):
        self.admin = User.objects.create_user(username="rental-test-admin", role="Facilities Admin", is_staff=True)
        sync_user_admin_permissions(self.admin)
        self.client.force_login(self.admin)
        self.payload = {"name": "Manually Named Test Resource", "facility_type": "other", "location": "Test location",
            "custom_facility_type": "Test Rentable Space",
            "mode": "slot", "capacity": "50", "price_type": "base_hour", "rate": "3000", "amenities": ["Lighting"],
            "workflow_config": {"capacity_min": "30", "pricing": {"base_duration": "4", "additional_hour_rate": "500"}}}
        self.payload["workflow_config"]["booking_form_type"] = "general"

    def post(self, path, data):
        return self.client.post(path, json.dumps(data), content_type="application/json")

    def test_create_and_description_only_update_preserve_real_configuration(self):
        before = (Room.objects.count(), Booking.objects.count(), FacilityPayment.objects.count())
        result = self.post(reverse("facilities_create"), self.payload)
        self.assertEqual(result.status_code, 201, result.content)
        pk = result.json()["facility"]["id"]
        self.assertEqual(result.json()["facility"]["capacity_label"], "30–50 pax")
        self.assertEqual(result.json()["facility"]["price_label"], "₱3,000 / first 4 hrs + ₱500/hr")
        facility = Facility.objects.get(pk=pk)
        facility.image_url = '["/media/existing-one.png", "/media/existing-two.webp"]'
        facility.workflow_config["future_saved_setting"] = {"keep": True}
        facility.save()
        updated = self.post(reverse("facilities_update", args=[pk]), {"description": "Updated description"})
        self.assertEqual(updated.status_code, 200, updated.content)
        facility.refresh_from_db()
        self.assertEqual(facility.rate, Decimal("3000"))
        self.assertEqual(facility.workflow_config["future_saved_setting"], {"keep": True})
        self.assertEqual(len(facility.get_image_list()), 2)
        self.assertEqual(before, (Room.objects.count(), Booking.objects.count(), FacilityPayment.objects.count()))
        page = self.client.get(reverse("admin_facility_page"))
        self.assertNotContains(page, 'id="facilityAssessmentServiceType"')
        self.assertNotContains(page, 'id="facilityAreaSize"')
        self.assertNotContains(page, 'id="facilityTurnaroundInformation"')
        self.assertNotContains(page, "Supported Activities")

    def test_simple_features_fees_api_preserves_history_and_omitted_requirements(self):
        self.payload["amenities"] = ["Chairs", "Lighting"]
        self.payload["workflow_config"].update(other_feature="  Access Ramp  ", additional_fees=[
            {"name":"Chair Rental", "amount":"10", "unit":"item", "active":False}])
        before = (Room.objects.count(), Booking.objects.count(), FacilityPayment.objects.count())
        created = self.post(reverse("facilities_create"), self.payload)
        self.assertEqual(created.status_code, 201, created.content)
        pk = created.json()["facility"]["id"]
        path = reverse("facilities_update", args=[pk])
        facility = Facility.objects.get(pk=pk)
        self.assertNotIn("equipment", facility.workflow_config)
        facility.image_url = '/media/preserved-test-image.png'
        facility.requirements = 'Historical requirements text'
        legacy = [{"name":"Older test item", "is_active":False, "has_additional_fee":False}]
        facility.workflow_config["equipment"] = legacy
        facility.save()
        self.assertEqual(before, (Room.objects.count(), Booking.objects.count(), FacilityPayment.objects.count()))
        historical = Booking.objects.create(id="FEATURE-HISTORY", facility=facility, status="completed", total_amount="250")
        payment = FacilityPayment.objects.create(id="FEATURE-PAYMENT", booking=historical, payment_status="paid", paid_amount="250")
        before = (Room.objects.count(), Booking.objects.count(), FacilityPayment.objects.count())
        updated = self.post(path, {"description":"Unrelated edit", "terms_conditions":"Current terms", "workflow_config":{
            "other_feature":None, "additional_fees":[{"name":"Chair Rental", "amount":"12", "unit":"item", "active":True}]}})
        self.assertEqual(updated.status_code, 200, updated.content)
        facility.refresh_from_db()
        self.assertEqual(facility.requirements, 'Historical requirements text')
        self.assertEqual(facility.terms_conditions, 'Current terms')
        self.assertEqual(facility.workflow_config["equipment"], legacy)
        self.assertEqual(facility.workflow_config["additional_fees"][0]["amount"], "12")
        self.assertNotIn("Access Ramp", facility.amenities)
        self.assertEqual(facility.image_url, '/media/preserved-test-image.png')
        removed = self.post(path, {"workflow_config":{"additional_fees":[]}})
        self.assertEqual(removed.status_code, 200, removed.content)
        self.assertEqual(removed.json()["facility"]["workflow_config"]["additional_fees"], [])
        self.assertEqual(before, (Room.objects.count(), Booking.objects.count(), FacilityPayment.objects.count()))
        historical.refresh_from_db(); payment.refresh_from_db()
        self.assertEqual(historical.status, "completed")
        self.assertEqual(historical.total_amount, Decimal("250"))
        self.assertEqual(payment.paid_amount, Decimal("250"))
        page = self.client.get(reverse("admin_facility_page"))
        self.assertContains(page, 'Facility Features')
        self.assertNotContains(page, 'Equipment / Additional Requirements')
        self.assertNotContains(page, 'Available Equipment')
        self.assertNotContains(page, 'id="facilityRequirements"')
        self.assertNotContains(page, 'equipment_form_controls.js')
        self.assertContains(page, 'placeholder="Describe the facility or space"')
        self.assertContains(page, 'placeholder="Enter terms and conditions for facility use"')
        self.assertContains(page, "30–50 pax")
        self.assertContains(page, "₱3,000 / first 4 hrs + ₱500/hr")
        self.assertContains(page, 'data-rate="3000.00"')

    def test_invalid_save_is_atomic_and_unauthorized_user_cannot_write(self):
        count = Facility.objects.count()
        result = self.post(reverse("facilities_create"), {**self.payload, "capacity": "30–50"})
        self.assertEqual(result.status_code, 400)
        self.assertIn("capacity", result.json()["errors"])
        self.assertEqual(Facility.objects.count(), count)
        missing_price = {**self.payload, "price_type":""}
        result = self.post(reverse("facilities_create"), missing_price)
        self.assertEqual(result.status_code, 400)
        self.assertIn("price_type", result.json()["errors"])
        self.assertEqual(Facility.objects.count(), count)
        user = User.objects.create_user(username="rental-test-market", role="Marketplace Admin", is_staff=True)
        sync_user_admin_permissions(user)
        self.client.force_login(user)
        self.assertNotEqual(self.post(reverse("facilities_create"), self.payload).status_code, 201)
        self.assertEqual(Facility.objects.count(), count)

    def test_room_configuration_does_not_generate_rooms_or_transactions(self):
        before = (Room.objects.count(), Booking.objects.count(), FacilityPayment.objects.count())
        result = self.post(reverse("facilities_create"), {**self.payload, "mode": "room", "price_type": "person_night", "rate": "800",
            "workflow_config": {"booking_form_type": "accommodation", "requires_pre_use_inspection": True}})
        self.assertEqual(result.status_code, 201, result.content)
        self.assertEqual(result.json()["facility"]["booking_mode"], "room")
        self.assertEqual(before, (Room.objects.count(), Booking.objects.count(), FacilityPayment.objects.count()))

    def test_custom_type_round_trip_table_report_and_predefined_switch(self):
        from modules.reports.reporting import _facility_utilization_report

        result = self.post(reverse("facilities_create"), {**self.payload,
            "name": "Campus Events Ground", "custom_facility_type": "  Open Grounds  "})
        self.assertEqual(result.status_code, 201, result.content)
        value = result.json()["facility"]
        self.assertEqual(value["facility_type"], "other")
        self.assertEqual(value["custom_facility_type"], "Open Grounds")
        self.assertEqual(value["facility_type_label"], "Open Grounds")
        facility = Facility.objects.get(pk=value["id"])
        self.assertEqual(facility.custom_facility_type, "Open Grounds")
        self.assertContains(self.client.get(reverse("admin_facility_page")), 'data-custom-facility-type="Open Grounds"')
        self.assertEqual(self.client.get(reverse("facilities_list")).json()["facilities"][0]["facility_type_label"], "Open Grounds")
        # An isolated booking verifies the existing report calls the shared resolver.
        Booking.objects.create(id="CUSTOM-TYPE-REPORT", facility=facility, status="approved")
        rows, _, _, _ = _facility_utilization_report(None, None)
        self.assertEqual(rows[0]["Type"], "Open Grounds")
        updated = self.post(reverse("facilities_update", args=[facility.pk]), {"description": "Keep all configuration"})
        self.assertEqual(updated.status_code, 200)
        self.assertEqual(updated.json()["facility"]["facility_type_label"], "Open Grounds")
        switched = self.post(reverse("facilities_update", args=[facility.pk]), {"facility_type": "function_hall", "custom_facility_type": "stale value"})
        self.assertEqual(switched.status_code, 200, switched.content)
        facility.refresh_from_db()
        self.assertNotIn("custom_facility_type", facility.workflow_config)
        self.assertEqual(facility.get_facility_type_display(), "Hall / Function Space")
        self.assertEqual(facility.facility_name, "Campus Events Ground")

    def test_missing_custom_type_is_rejected_without_creating_a_facility(self):
        payload = dict(self.payload)
        payload.pop("custom_facility_type")
        count = Facility.objects.count()
        response = self.post(reverse("facilities_create"), payload)
        self.assertEqual(response.status_code, 400)
        self.assertIn("custom_facility_type", response.json()["errors"])
        self.assertEqual(Facility.objects.count(), count)

    def test_saved_discount_rules_preserve_configuration_on_edit_and_can_be_removed(self):
        rule = {"eligible_client_type": "immediate_family", "discount_type": "fixed", "discount_value": "25", "applies_to": "base_rate", "active": False}
        payload = {**self.payload, "workflow_config": {**self.payload["workflow_config"], "discount_rules": [rule],
            "requires_pre_use_inspection": False, "requires_post_use_inspection": False}}
        before = (Room.objects.count(), Booking.objects.count(), FacilityPayment.objects.count())
        created = self.post(reverse("facilities_create"), payload)
        self.assertEqual(created.status_code, 201, created.content)
        pk = created.json()["facility"]["id"]
        updated = self.post(reverse("facilities_update", args=[pk]), {"description": "Unrelated edit"})
        self.assertEqual(updated.status_code, 200, updated.content)
        saved = updated.json()["facility"]["workflow_config"]
        self.assertEqual(saved["discount_rules"], [rule])
        self.assertFalse(saved["requires_pre_use_inspection"])
        self.assertEqual(saved["pricing"], payload["workflow_config"]["pricing"])
        removed = self.post(reverse("facilities_update", args=[pk]), {"workflow_config": {"discount_rules": []}})
        self.assertEqual(removed.status_code, 200)
        self.assertEqual(removed.json()["facility"]["workflow_config"]["discount_rules"], [])
        self.assertEqual(before, (Room.objects.count(), Booking.objects.count(), FacilityPayment.objects.count()))

    def test_invalid_discount_api_does_not_insert_records(self):
        count = Facility.objects.count()
        bad = {**self.payload, "workflow_config": {**self.payload["workflow_config"], "discount_rules": [{
            "eligible_client_type": "student", "discount_type": "percentage", "discount_value": "101", "applies_to": "rental_fee", "active": True}]}}
        response = self.post(reverse("facilities_create"), bad)
        self.assertEqual(response.status_code, 400)
        self.assertIn("discount_rules.0", response.json()["errors"])
        self.assertEqual(Facility.objects.count(), count)

    def test_accommodation_tiers_api_preserves_and_clears_real_configuration(self):
        payload = {**self.payload, "facility_type":"hostel", "mode":"room", "price_type":"person_night", "rate":"800",
            "workflow_config":{"booking_form_type":"accommodation", "pricing":{"partner_rate":"500", "partner_occupancy_required":2},
                "discount_rules":[{"eligible_client_type":"student", "discount_type":"percentage", "discount_value":"10", "applies_to":"partner_rate", "active":False}]}}
        before = (Room.objects.count(), Booking.objects.count(), FacilityPayment.objects.count())
        created = self.post(reverse("facilities_create"), payload)
        self.assertEqual(created.status_code, 201, created.content)
        pk = created.json()["facility"]["id"]
        edited = self.post(reverse("facilities_update", args=[pk]), {"description":"Unrelated edit"})
        self.assertEqual(edited.status_code, 200, edited.content)
        self.assertEqual(edited.json()["facility"]["workflow_config"]["pricing"], payload["workflow_config"]["pricing"])
        cleared = self.post(reverse("facilities_update", args=[pk]), {"price_type":"night", "workflow_config":{"discount_rules":[]}})
        self.assertEqual(cleared.status_code, 200, cleared.content)
        self.assertNotIn("pricing", cleared.json()["facility"]["workflow_config"])
        self.assertEqual(before, (Room.objects.count(), Booking.objects.count(), FacilityPayment.objects.count()))

    def test_export_unsaved_browser_fixtures(self):
        folder = os.environ.get("RENTAL_FORM_REVIEW_DIR")
        if not folder:
            return
        root = Path(folder); root.mkdir(parents=True, exist_ok=True)
        (root / "facility-empty.html").write_bytes(self.client.get(reverse("admin_facility_page")).content)
        # Stored in the TEST database only for authentic rendering of edit/view.
        result = self.post(reverse("facilities_create"), self.payload)
        self.assertEqual(result.status_code, 201)
        facility = Facility.objects.get(pk=result.json()["facility"]["id"])
        facility.workflow_config.update({"requires_pre_use_inspection": True, "damage_deposit_applicable": True,
            "other_feature": "Test Accessible Ramp",
            "requires_post_use_inspection": False,
            "minimum_booking_duration": "0.7833333333333333333333333333",
            "discount_rules": [{"eligible_client_type": "student", "discount_type": "fixed", "discount_value": "25", "applies_to": "base_rate", "active": False}],
            "damage_deposit": {"type": "percentage", "value": "40"},
            "additional_fees": [{"name": "Saved Test Charge", "amount": "25", "unit": "booking", "active": False}]})
        facility.requirements = "Historical requirements preserved in storage"
        facility.image_url = "/static/assets/img/icon.png"
        facility.amenities = ["Lighting", "Test Accessible Ramp", "Chairs"]
        facility.save()
        audit_responses = {
            "archive": self.post(reverse("facilities_archive", args=[facility.pk]), {}).json(),
            "edit": self.post(reverse("facilities_update", args=[facility.pk]), {"description":"Saved archived edit test"}).json(),
            "reactivate": self.post(reverse("facilities_restore", args=[facility.pk]), {}).json(),
        }
        response = self.client.get(reverse("admin_facility_page"))
        self.assertEqual(response.status_code, 200)
        root = Path(folder); root.mkdir(parents=True, exist_ok=True)
        (root / "facility.html").write_bytes(response.content)
        (root / "audit-responses.json").write_text(json.dumps(audit_responses), encoding="utf-8")
