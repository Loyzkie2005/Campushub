"""Render the real admin template with isolated fixtures; never writes to the DB."""
import os
import sys
from pathlib import Path

root = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(root / "backend/core"))
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "core.settings")

import django
django.setup()

from django.template.loader import render_to_string
from api.models import Facility
from modules.facilities.services.facility_configuration import facility_form_configuration
from modules.facilities.services.operating_schedule import workflow_for_display

facility = Facility(id="TEST-FORM", facility_name="Test Court", facility_type="covered_court",
    location="Test Campus", capacity=50, rate=500, booking_mode="slot", price_type="hour",
    slots="08:00-12:00;13:00-17:00", amenities=["Lighting", "Custom | equipment"],
    workflow_config={"operating_hours": "Monday-Friday, 8:00 AM-5:00 PM", "minimum_booking_duration": "1 hour"})
facility.form_workflow = workflow_for_display(facility)
context = {"facilities": [facility], "facilities_total": 1, "open_for_booking_count": 1,
           "under_maintenance_count": 0, "rooms_units_total": 0, "can_manage_facilities": True,
           "can_book_facilities": True, "calendar_events": [],
           "facility_type_choices": Facility.TYPE_CHOICES,
           "facility_status_choices": Facility.STATUS_CHOICES,
           "facility_form_configuration": facility_form_configuration(),
           "perms": {"accounts": {"can_manage_facilities": True}}}
sys.stdout.buffer.write(render_to_string("facilities/pages/admin_facility.html", context).encode("utf-8"))
