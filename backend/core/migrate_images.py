"""One-time script: convert existing base64 image_url fields to media files."""
import django, os
os.environ['DJANGO_SETTINGS_MODULE'] = 'core.settings'
django.setup()

from api.models import Facility, Product
from api.product_images import persist_facility_image, persist_product_image

# Migrate facilities
print("=== Migrating Facility Images ===")
for f in Facility.objects.all():
    img = (f.image_url or "").strip()
    if img.startswith("data:image/"):
        new_url = persist_facility_image(img, f.id, f.facility_name)
        if new_url:
            f.image_url = new_url
            f.save(update_fields=["image_url"])
            print(f"  [OK] {f.facility_name} -> {new_url}")
        else:
            print(f"  [FAIL] {f.facility_name} - could not decode")
    else:
        print(f"  [SKIP] {f.facility_name} - already file/url or empty")

# Migrate products
print("\n=== Migrating Product Images ===")
for p in Product.objects.all():
    img = (p.image_url or "").strip()
    if img.startswith("data:image/"):
        new_url = persist_product_image(img, p.id, p.name)
        if new_url:
            p.image_url = new_url
            p.save(update_fields=["image_url"])
            print(f"  [OK] {p.name} -> {new_url}")
        else:
            print(f"  [FAIL] {p.name} - could not decode")
    else:
        print(f"  [SKIP] {p.name} - already file/url or empty")

print("\nDone!")
