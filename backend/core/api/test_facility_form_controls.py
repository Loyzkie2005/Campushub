"""Structured form validation and compatibility with existing facility records."""

from datetime import date, time
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.test import SimpleTestCase

from api.models import Facility
from api.views import _apply_facility_payload, serialize_facility
from modules.facilities.services.facility_configuration import validate_facility_payload
from modules.facilities.services.mobile_booking import configured_slots
from modules.facilities.services.operating_schedule import WEEKDAYS, duration_hours, weekly_hours


class FacilityFormControlsTests(SimpleTestCase):
    def hours(self):
        return {day: {"open": "08:00", "close": "17:00"} if day in WEEKDAYS[:5] else None for day in WEEKDAYS}

    def payload(self):
        return {"name": "Test Court", "facility_type": "covered_court", "location": "Test Campus",
                "capacity": 50, "rate": "500", "mode": "slot", "price_type": "hour",
                "amenities": ["Lighting", "Sound System", "Custom | equipment"],
                "workflow_config": {"operating_hours": self.hours(), "minimum_booking_duration": "0.5"}}

    def test_structured_round_trip_keeps_amenities_and_weekdays(self):
        facility = Facility(id="TEST-ROUND-TRIP")
        _apply_facility_payload(facility, validate_facility_payload(self.payload()))
        data = serialize_facility(facility)
        self.assertEqual(data["amenities"], self.payload()["amenities"])
        self.assertEqual(data["workflow_config"]["operating_hours"], self.hours())
        self.assertEqual(data["workflow_config"]["minimum_booking_duration"], "0.5")
        self.assertEqual(data["status"], "available")

    def test_invalid_days_times_and_overnight_ranges_rejected(self):
        for hours in ({}, {**self.hours(), "holiday": None},
                      {**self.hours(), "monday": {"open": "", "close": "17:00"}},
                      {**self.hours(), "monday": {"open": "25:00", "close": "17:00"}},
                      {**self.hours(), "monday": {"open": "17:00", "close": "17:00"}},
                      {**self.hours(), "monday": {"open": "18:00", "close": "08:00"}}):
            with self.subTest(hours=hours), self.assertRaises(ValidationError):
                payload = self.payload()
                payload["workflow_config"]["operating_hours"] = hours
                validate_facility_payload(payload)

    def test_all_closed_schedule_does_not_invent_operating_hours(self):
        payload = self.payload()
        payload["workflow_config"]["operating_hours"] = {day: None for day in WEEKDAYS}
        cleaned = validate_facility_payload(payload)
        facility = Facility(workflow_config=cleaned["workflow_config"])
        self.assertEqual(configured_slots(facility, date(2026, 9, 14)), [])

    def test_old_day_policies_cannot_override_enabled_operating_days(self):
        from modules.facilities.services.operating_schedule import booking_day_restriction
        for category in ('covered_court', 'function_hall', 'hostel', 'other'):
            workflow = {"operating_hours": self.hours(), "weekend_only": True, "allowed_booking_days": []}
            facility = Facility(facility_type=category, booking_mode='slot', workflow_config=workflow)
            self.assertIsNone(booking_day_restriction(workflow, date(2030, 1, 7)))
            self.assertIsNotNone(booking_day_restriction(workflow, date(2030, 1, 6)))
            self.assertEqual(configured_slots(facility, date(2030, 1, 7)), [(time(8), time(17))])
            public = serialize_facility(facility)['workflow_config']
            self.assertNotIn('weekend_only', public)
            self.assertNotIn('allowed_booking_days', public)
            self.assertEqual(facility.workflow_config, workflow)

    def test_all_presets_and_custom_hours_round_trip_without_creating_a_policy(self):
        for days in (WEEKDAYS[:5], WEEKDAYS[5:], WEEKDAYS, ("tuesday", "saturday")):
            with self.subTest(days=days):
                hours = {day: {"open": "08:00", "close": "17:00"} if day in days else None for day in WEEKDAYS}
                if len(days) == 2 and "tuesday" in days:
                    hours["tuesday"] = {"open": "08:07", "close": "16:53"}
                payload = self.payload()
                payload["workflow_config"]["operating_hours"] = hours
                facility = Facility(id="SCHEDULE-ROUND-TRIP")
                _apply_facility_payload(facility, validate_facility_payload(payload))
                self.assertEqual(serialize_facility(facility)["workflow_config"]["operating_hours"], hours)
                self.assertFalse(facility.workflow_config.get("weekend_only", False))

    def test_all_add_categories_and_modes_use_operating_days_without_retired_flags(self):
        for category in ('covered_court', 'function_hall', 'hostel', 'other'):
            for mode in ('slot', 'room', 'daily', 'custom'):
                with self.subTest(category=category, mode=mode):
                    payload = {**self.payload(), 'facility_type': category, 'mode': mode,
                        'custom_facility_type': 'Isolated test venue'}
                    payload['workflow_config'].update(weekend_only=True, allowed_booking_days=[], booking_form_type='general')
                    cleaned = validate_facility_payload(payload)['workflow_config']
                    self.assertEqual(cleaned['operating_hours'], self.hours())
                    self.assertNotIn('weekend_only', cleaned)
                    self.assertNotIn('allowed_booking_days', cleaned)

    def test_add_and_edit_remove_retired_day_policies(self):
        payload = self.payload()
        payload['workflow_config'].update(weekend_only=True, allowed_booking_days=[])
        cleaned = validate_facility_payload(payload)
        self.assertNotIn('weekend_only', cleaned['workflow_config'])
        self.assertNotIn('allowed_booking_days', cleaned['workflow_config'])
        facility = Facility(id='OLD-POLICY')
        _apply_facility_payload(facility, cleaned)
        facility.workflow_config.update(weekend_only=True, allowed_booking_days=['sunday'])
        kept = validate_facility_payload({'workflow_config': {'operating_hours': self.hours()}}, facility=facility)
        self.assertNotIn('weekend_only', kept['workflow_config'])
        self.assertNotIn('allowed_booking_days', kept['workflow_config'])
        self.assertEqual(kept['workflow_config']['operating_hours'], self.hours())

    def test_old_api_day_fields_are_ignored_in_favor_of_operating_hours(self):
        for old_days in (None, True, {}, 'monday', ['holiday'], [], ['sunday']):
            with self.subTest(old_days=old_days):
                payload = self.payload()
                payload['workflow_config'].update(allowed_booking_days=old_days, weekend_only=True)
                cleaned = validate_facility_payload(payload)['workflow_config']
                self.assertNotIn('allowed_booking_days', cleaned)
                self.assertNotIn('weekend_only', cleaned)
                self.assertEqual(cleaned['operating_hours'], self.hours())

    def test_closed_or_invalid_operating_days_fail_closed_without_hidden_policies(self):
        from modules.facilities.services.operating_schedule import booking_day_restriction
        monday = date(2030, 1, 7)
        self.assertIsNone(booking_day_restriction({'weekend_only': True, 'allowed_booking_days': []}, monday))
        self.assertIsNone(booking_day_restriction({'operating_hours': '08:00-12:00;13:00-17:00'}, monday))
        for hours in ({}, 'Ask the office', {day: None for day in WEEKDAYS}):
            self.assertIsNotNone(booking_day_restriction({'operating_hours': hours}, monday))

    def test_operating_edits_close_and_reopen_without_retaining_hidden_restrictions(self):
        for saved_days in ([], ['monday'], ['sunday']):
            facility = Facility(id='RETIRED-POLICY')
            _apply_facility_payload(facility, validate_facility_payload(self.payload()))
            facility.workflow_config.update(allowed_booking_days=saved_days, weekend_only=True)
            original = dict(facility.workflow_config)
            closed = {day: None for day in WEEKDAYS}
            update = validate_facility_payload({'workflow_config': {'operating_hours': closed}}, facility=facility)
            self.assertEqual(facility.workflow_config, original)
            self.assertNotIn('allowed_booking_days', update['workflow_config'])
            _apply_facility_payload(facility, update)
            self.assertEqual(configured_slots(facility, date(2030, 1, 7)), [])
            _apply_facility_payload(facility, validate_facility_payload(
                {'workflow_config': {'operating_hours': self.hours()}}, facility=facility))
            self.assertEqual(configured_slots(facility, date(2030, 1, 7)), [(time(8), time(17))])

    def test_repeated_weekday_rows_and_incomplete_day_maps_are_rejected(self):
        for hours in ([{"day": "monday", "open": "08:00", "close": "17:00"}] * 2,
                      {day: None for day in WEEKDAYS[:-1]}):
            payload = self.payload()
            payload["workflow_config"]["operating_hours"] = hours
            with self.subTest(hours=hours), self.assertRaises(ValidationError):
                validate_facility_payload(payload)

    def test_legacy_day_range_and_duration_are_normalized(self):
        payload = self.payload()
        payload["workflow_config"] = {"operating_hours": "Monday-Friday, 8:00 AM-5:00 PM", "minimum_booking_duration": "30 minutes"}
        workflow = validate_facility_payload(payload)["workflow_config"]
        self.assertEqual(workflow["operating_hours"], self.hours())
        self.assertEqual(workflow["minimum_booking_duration"], "0.5")
        self.assertEqual(duration_hours("1 hour"), Decimal("1"))
        self.assertIsNone(weekly_hours("Ask the office"))

    def test_predefined_slots_ignore_redundant_minimum(self):
        payload = self.payload()
        payload["workflow_config"]["minimum_booking_duration"] = "not a duration"
        facility = Facility(slots="08:00-12:00;13:00-17:00")
        workflow = validate_facility_payload(payload, facility=facility)["workflow_config"]
        self.assertNotIn("minimum_booking_duration", workflow)

    def test_invalid_minimum_and_amenities_rejected(self):
        for duration in ("garbage", "NaN", "0", "-1", "25", {}, "0.333"):
            payload = self.payload()
            payload["workflow_config"]["minimum_booking_duration"] = duration
            with self.subTest(duration=duration), self.assertRaises(ValidationError):
                validate_facility_payload(payload)
        for amenities in ([{"name": "Lighting"}], [None], ["x" * 201], "Lighting"):
            payload = {**self.payload(), "amenities": amenities}
            with self.subTest(amenities=amenities), self.assertRaises(ValidationError):
                validate_facility_payload(payload)

    def test_closed_days_and_slots_outside_hours_not_returned(self):
        facility = Facility(slots="08:00-12:00;13:00-17:00;18:00-21:00", workflow_config={"operating_hours": self.hours()})
        self.assertEqual(configured_slots(facility, date(2026, 9, 14)), [(time(8), time(12)), (time(13), time(17))])
        self.assertEqual(configured_slots(facility, date(2026, 9, 19)), [])
        facility.workflow_config["operating_hours"] = "Monday-Friday, 8:00 AM-5:00 PM"
        self.assertEqual(configured_slots(facility, date(2026, 9, 19)), [])

    def test_no_predefined_slots_uses_the_configured_daily_window(self):
        facility = Facility(workflow_config={"operating_hours": self.hours()})
        self.assertEqual(configured_slots(facility, date(2026, 9, 14)), [(time(8), time(17))])
        self.assertEqual(configured_slots(facility, date(2026, 9, 20)), [])

    def test_unknown_or_corrupt_schedule_does_not_open_predefined_slots(self):
        facility = Facility(slots="08:00-12:00")
        for hours in ("Monday some time", "Monday and holidays, 08:00-12:00", {}, {"monday": None}):
            facility.workflow_config = {"operating_hours": hours}
            self.assertEqual(configured_slots(facility, date(2026, 9, 14)), [])

    def test_old_records_with_only_slots_still_work(self):
        facility = Facility(slots="8:00 AM-12:00 PM;1:00 PM-5:00 PM")
        self.assertEqual(configured_slots(facility, date(2026, 9, 19)), [(time(8), time(12)), (time(13), time(17))])
