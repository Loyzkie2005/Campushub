"""Save uploaded images as files under MEDIA so the database stays small."""

import base64
import binascii
import re
from pathlib import Path

from django.conf import settings


_DATA_URL_RE = re.compile(
    r"^data:image/(?P<ext>\w+);base64,(?P<data>.+)$",
    re.DOTALL,
)


def _save_base64_image(raw: str, folder: str, filename_prefix: str) -> str:
    """Decode a base64 data URL and save to media/<folder>/<filename_prefix>.<ext>."""
    match = _DATA_URL_RE.match(raw)
    if not match:
        return raw

    ext = match.group("ext").lower().replace("jpeg", "jpg")
    if ext not in {"png", "jpg", "jpeg", "gif", "webp"}:
        ext = "jpg"

    try:
        binary = base64.b64decode(match.group("data"), validate=False)
    except (ValueError, binascii.Error):
        return ""

    media_root = Path(settings.MEDIA_ROOT)
    rel = Path(folder) / f"{filename_prefix}.{ext}"
    dest = media_root / rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(binary)

    media_url = settings.MEDIA_URL.rstrip("/")
    return f"{media_url}/{rel.as_posix()}"


def persist_product_image(raw_image_url: str, product_id: int, product_name: str = "") -> str:
    """
    Convert base64 data URLs to /media/upload/products/<name>_<id>.ext
    Leave http(s) and existing /media/ paths unchanged.
    """
    raw = (raw_image_url or "").strip()
    if not raw:
        return ""

    if raw.startswith("/media/"):
        return raw

    if raw.startswith("http://") or raw.startswith("https://"):
        return raw

    # Build filename from product name
    slug = re.sub(r'[^a-z0-9]+', '_', (product_name or "").strip().lower()).strip('_')
    if not slug:
        slug = f"product_{product_id}"
    else:
        slug = f"{slug}_{product_id}"

    return _save_base64_image(raw, "upload/products", slug)


def persist_product_images(raw_images, product_id: int, product_name: str = "") -> list:
    """
    Save multiple base64 images and return a list of URLs.
    Accepts a list of base64 strings or a single string.
    """
    if not raw_images:
        return []

    if isinstance(raw_images, str):
        raw_images = [raw_images]

    if not isinstance(raw_images, list):
        return []

    urls = []
    slug = re.sub(r'[^a-z0-9]+', '_', (product_name or "").strip().lower()).strip('_')
    if not slug:
        slug = f"product_{product_id}"

    for i, raw in enumerate(raw_images):
        raw = (raw or "").strip()
        if not raw:
            continue

        if raw.startswith("/media/") or raw.startswith("http://") or raw.startswith("https://"):
            urls.append(raw)
            continue

        prefix = f"{slug}_{product_id}_{i + 1}" if i > 0 else f"{slug}_{product_id}"
        saved = _save_base64_image(raw, "upload/products", prefix)
        if saved:
            urls.append(saved)

    return urls


import json

def persist_facility_image(raw_image_url: str, facility_id: str, facility_name: str = "") -> str:
    """
    Convert base64 data URLs to /media/upload/facilities/<name>_<id>.ext
    Leave http(s) and existing /media/ paths unchanged.
    """
    raw = (raw_image_url or "").strip()
    if not raw:
        return ""

    if raw.startswith("/media/"):
        return raw

    if raw.startswith("http://") or raw.startswith("https://"):
        return raw

    # Build filename from facility name
    slug = re.sub(r'[^a-z0-9]+', '_', (facility_name or "").strip().lower()).strip('_')
    if not slug:
        slug = f"facility_{facility_id}"
    else:
        slug = f"{slug}_{facility_id}"

    return _save_base64_image(raw, "upload/facilities", slug)


def persist_facility_images(raw_images, facility_id: str, facility_name: str = "") -> list:
    """
    Save multiple base64 images and return a list of URLs for facilities.
    Accepts a list of base64 strings/URLs or a single string.
    """
    if not raw_images:
        return []

    if isinstance(raw_images, str):
        raw = raw_images.strip()
        if raw.startswith("["):
            try:
                parsed = json.loads(raw)
                if isinstance(parsed, list):
                    raw_images = parsed
                else:
                    raw_images = [raw]
            except Exception:
                raw_images = [raw]
        else:
            raw_images = [raw]

    if not isinstance(raw_images, list):
        return []

    urls = []
    slug = re.sub(r'[^a-z0-9]+', '_', (facility_name or "").strip().lower()).strip('_')
    if not slug:
        slug = f"facility_{facility_id}"
    else:
        slug = f"{slug}_{facility_id}"

    for i, raw in enumerate(raw_images):
        raw = (raw or "").strip()
        if not raw:
            continue

        if raw.startswith("/media/") or raw.startswith("http://") or raw.startswith("https://"):
            urls.append(raw)
            continue

        prefix = f"{slug}_{i + 1}" if len(raw_images) > 1 else slug
        saved = _save_base64_image(raw, "upload/facilities", prefix)
        if saved:
            urls.append(saved)

    return urls
