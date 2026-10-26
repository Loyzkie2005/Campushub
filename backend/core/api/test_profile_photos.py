from io import BytesIO
from tempfile import TemporaryDirectory
from unittest.mock import patch

from django.core.files.uploadedfile import SimpleUploadedFile
from django.db import connection
from django.test import TestCase, override_settings
from django.urls import reverse
from PIL import Image

from api.models import CampusHubUser
from modules.messages.auth import mobile_chat_token


def picture(fmt="PNG", size=(800, 600)):
    output = BytesIO()
    image = Image.new("RGB", size, "white")
    exif = Image.Exif()
    exif[270] = "Private image metadata"
    image.save(output, format=fmt, exif=exif)
    # A misleading filename/content type must not bypass actual image decoding.
    return SimpleUploadedFile("client-name.txt", output.getvalue(), content_type="text/plain")


class ProfilePhotoTests(TestCase):
    @classmethod
    def setUpClass(cls):
        if CampusHubUser._meta.db_table not in connection.introspection.table_names():
            with connection.schema_editor() as editor:
                editor.create_model(CampusHubUser)
        super().setUpClass()

    def setUp(self):
        self.media = TemporaryDirectory(prefix="campushub-profile-test-")
        self.addCleanup(self.media.cleanup)
        self.settings_override = override_settings(MEDIA_ROOT=self.media.name)
        self.settings_override.enable()
        self.addCleanup(self.settings_override.disable)
        self.owner = CampusHubUser.objects.create(
            username="photo-owner", first_name="Photo", last_name="Owner",
            email="photo-owner@example.test", password_hash="unused",
            user_type="guest", role="User", contact_number="09171234567",
        )
        self.other = CampusHubUser.objects.create(
            username="other-photo-owner", first_name="Other", last_name="Owner",
            email="other-photo-owner@example.test", password_hash="unused",
        )
        self.auth = {"HTTP_AUTHORIZATION": "Bearer " + mobile_chat_token(self.owner)}
        self.url = reverse("mobile_profile_photo")

    def upload(self, file=None, **extra):
        return self.client.post(self.url, {"photo": file or picture(), **extra}, **self.auth)

    def test_get_and_upload_require_an_active_mobile_owner(self):
        self.assertEqual(self.client.get(self.url).status_code, 401)
        self.assertEqual(self.client.post(self.url, {"photo": picture()}).status_code, 401)
        self.assertEqual(self.client.get(self.url, HTTP_AUTHORIZATION="Bearer invalid").status_code, 401)
        self.assertEqual(self.client.put(self.url, **self.auth).status_code, 405)
        self.owner.is_suspended = True
        self.owner.save(update_fields=["is_suspended"])
        self.assertEqual(self.upload().status_code, 403)
        self.owner.is_suspended = False
        self.owner.is_active = False
        self.owner.save(update_fields=["is_suspended", "is_active"])
        self.assertEqual(self.client.get(self.url, **self.auth).status_code, 403)

    def test_upload_is_owner_scoped_and_round_trips_through_profile(self):
        response = self.upload(user_id=self.other.pk, role="Super Admin", contact_number="changed")
        self.assertEqual(response.status_code, 200, response.content)
        payload = response.json()["user"]
        self.assertEqual(payload["id"], self.owner.pk)
        self.assertTrue(payload["profile_photo_url"].startswith(f"/media/profile-photos/{self.owner.pk}/"))
        self.owner.refresh_from_db()
        self.other.refresh_from_db()
        self.assertFalse(self.other.profile_photo)
        self.assertEqual(self.owner.role, "User")
        self.assertEqual(self.owner.contact_number, "09171234567")
        current = self.client.get(self.url, **self.auth)
        self.assertEqual(current.json()["user"]["profile_photo_url"], payload["profile_photo_url"])
        self.assertIn("no-store", current.headers["Cache-Control"])
        with self.owner.profile_photo.open("rb") as saved:
            with Image.open(saved) as image:
                self.assertEqual(image.format, "JPEG")
                self.assertEqual(image.size, (512, 384))
                self.assertFalse(image.getexif())

    def test_replace_removes_previous_owner_file_after_success(self):
        self.assertEqual(self.upload().status_code, 200)
        self.owner.refresh_from_db()
        storage, previous = self.owner.profile_photo.storage, self.owner.profile_photo.name
        self.assertTrue(storage.exists(previous))
        with self.captureOnCommitCallbacks(execute=True):
            self.assertEqual(self.upload(picture("JPEG")).status_code, 200)
        self.owner.refresh_from_db()
        self.assertNotEqual(previous, self.owner.profile_photo.name)
        self.assertFalse(storage.exists(previous))
        self.assertTrue(storage.exists(self.owner.profile_photo.name))

    def test_invalid_missing_oversize_unsupported_and_high_pixel_files_leave_photo_intact(self):
        self.upload()
        self.owner.refresh_from_db()
        original = self.owner.profile_photo.name
        self.assertEqual(self.client.post(self.url, {}, **self.auth).status_code, 400)
        for invalid in [
            SimpleUploadedFile("fake.jpg", b"not an image", content_type="image/jpeg"),
            SimpleUploadedFile("huge.jpg", b"x" * (5 * 1024 * 1024 + 1)),
            picture("GIF"),
        ]:
            self.assertEqual(self.upload(invalid).status_code, 400)
        with patch("api.profile_photos.MAX_PHOTO_PIXELS", 100):
            self.assertEqual(self.upload(picture(size=(11, 10))).status_code, 400)
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.profile_photo.name, original)
        self.assertTrue(self.owner.profile_photo.storage.exists(original))

    def test_failed_database_save_preserves_previous_photo_and_cleans_new_file(self):
        self.upload()
        self.owner.refresh_from_db()
        original = self.owner.profile_photo.name
        with patch.object(CampusHubUser, "save", side_effect=RuntimeError("test save failure")):
            with self.assertRaises(RuntimeError):
                self.upload()
        self.owner.refresh_from_db()
        self.assertEqual(self.owner.profile_photo.name, original)
        _, files = self.owner.profile_photo.storage.listdir(f"profile-photos/{self.owner.pk}")
        self.assertEqual(files, [original.rsplit("/", 1)[-1]])

    def test_empty_photo_serializes_as_empty_and_png_transparency_uses_white(self):
        self.assertEqual(self.client.get(self.url, **self.auth).json()["user"]["profile_photo_url"], "")
        output = BytesIO()
        Image.new("RGBA", (20, 20), (0, 0, 0, 0)).save(output, format="PNG")
        response = self.upload(SimpleUploadedFile("transparent.png", output.getvalue()))
        self.assertEqual(response.status_code, 200)
        self.owner.refresh_from_db()
        with self.owner.profile_photo.open("rb") as saved:
            with Image.open(saved) as image:
                self.assertEqual(image.getpixel((0, 0)), (255, 255, 255))
