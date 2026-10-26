"""Validate and normalize real account photos before writing to media storage."""
from io import BytesIO
import warnings

from django.core.exceptions import ValidationError
from django.core.files.base import ContentFile
from PIL import Image, ImageOps, UnidentifiedImageError

MAX_PHOTO_BYTES = 5 * 1024 * 1024
MAX_PHOTO_PIXELS = 20_000_000


def normalize_profile_photo(upload):
    """Return a metadata-free JPEG (at most 512px), or a user-readable error."""
    if upload is None:
        raise ValidationError("Choose a profile picture first.")
    if upload.size > MAX_PHOTO_BYTES:
        raise ValidationError("Choose a picture smaller than 5 MB.")
    try:
        with warnings.catch_warnings():
            warnings.simplefilter("error", Image.DecompressionBombWarning)
            with Image.open(upload) as source:
                if source.format not in {"JPEG", "PNG", "WEBP"}:
                    raise ValidationError("Choose a JPEG, PNG, or WebP picture.")
                if source.width * source.height > MAX_PHOTO_PIXELS:
                    raise ValidationError("Choose a picture with no more than 20 megapixels.")
                if getattr(source, "is_animated", False):
                    raise ValidationError("Choose a still picture instead of an animation.")
                source.load()
                image = ImageOps.exif_transpose(source)
                image.thumbnail((512, 512), Image.Resampling.LANCZOS)
                rgba = image.convert("RGBA")
                photo = Image.new("RGB", rgba.size, "white")
                photo.paste(rgba, mask=rgba.getchannel("A"))
                output = BytesIO()
                photo.save(output, format="JPEG", quality=85, optimize=True)
    except (UnidentifiedImageError, OSError, ValueError, Image.DecompressionBombError, Image.DecompressionBombWarning) as exc:
        raise ValidationError("This picture could not be read. Choose another JPEG, PNG, or WebP picture.") from exc
    return ContentFile(output.getvalue())
