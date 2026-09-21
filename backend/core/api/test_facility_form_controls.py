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
                      {**self.hours(), "monday": {"open": "18:00", "close": "08:00"}},
                      {day: None for day in WEEKDAYS}):
            with self.subTest(hours=hours), self.assertRaises(ValidationError):
                payload = self.payload()
                payload["workflow_config"]["operating_hours"] = hours
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
