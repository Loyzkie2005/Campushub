# Facilities migrations index

**Schema owner:** `api` app (`backend/core/api/migrations/`)

| Migration | What it adds |
|-----------|----------------|
| `0003_campushubuser_facility.py` | Facility, rooms, bookings (initial) |
| `0008_rename_tables_campushub.py` | Table renames |
| `0009_rename_all_tables_campushub.py` | Table renames |

**Models:** `api.models` — `Facility`, `Room`, `Booking`, `FacilityPayment`, `FacilityFeedback`

**Admin UI:** `modules/facilities/templates/`

**New migrations:** Add facility/booking changes under `api/migrations/`.
