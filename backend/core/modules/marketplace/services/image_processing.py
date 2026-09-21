import base64
import io
import logging
from typing import Optional, Tuple
from PIL import Image

logger = logging.getLogger(__name__)

_REMBG_SESSION = None
_REMBG_AVAILABLE = None


def is_rembg_available() -> bool:
    global _REMBG_AVAILABLE
    if _REMBG_AVAILABLE is not None:
        return _REMBG_AVAILABLE
    try:
        import rembg  # noqa: F401
        _REMBG_AVAILABLE = True
    except ImportError:
        _REMBG_AVAILABLE = False
    return _REMBG_AVAILABLE


def get_rembg_session(model_name: str = "u2netp"):
    global _REMBG_SESSION
    if _REMBG_SESSION is not None:
        return _REMBG_SESSION
    try:
        import rembg
        _REMBG_SESSION = rembg.new_session(model_name)
        return _REMBG_SESSION
    except Exception as exc:
        logger.warning("Could not initialize rembg session with model %s: %s", model_name, exc)
        # Fallback to default session if specific model fails
        try:
            import rembg
            _REMBG_SESSION = rembg.new_session()
            return _REMBG_SESSION
        except Exception:
            return None


def resize_if_needed(image: Image.Image, max_dim: int = 1280) -> Image.Image:
    """Downscale large images to keep AI inference fast (1-2s) while preserving high quality."""
    width, height = image.size
    if width <= max_dim and height <= max_dim:
        return image

    if width > height:
        new_width = max_dim
        new_height = int(height * (max_dim / width))
    else:
        new_height = max_dim
        new_width = int(width * (max_dim / height))

    return image.resize((new_width, new_height), Image.Resampling.LANCZOS)


def remove_background_from_bytes(image_bytes: bytes, max_dim: int = 1280) -> Tuple[bytes, bool]:
    """
    Takes raw image bytes (JPEG, PNG, WEBP), performs AI foreground segmentation,
    and returns (transparent_png_bytes, success_bool).
    """
    if not is_rembg_available():
        raise RuntimeError("The 'rembg' package is not installed or available on this system.")

    import rembg

    input_image = Image.open(io.BytesIO(image_bytes))
    input_image = resize_if_needed(input_image, max_dim=max_dim)

    # Ensure format is RGB/RGBA before processing
    if input_image.mode not in ("RGB", "RGBA"):
        input_image = input_image.convert("RGB")

    session = get_rembg_session("u2netp")
    if session:
        output_image = rembg.remove(input_image, session=session)
    else:
        output_image = rembg.remove(input_image)

    out_buffer = io.BytesIO()
    output_image.save(out_buffer, format="PNG", optimize=True)
    return out_buffer.getvalue(), True


def remove_background_from_data_url(data_url: str) -> str:
    """
    Accepts a base64 Data URL (e.g. data:image/jpeg;base64,...),
    removes background, and returns a transparent PNG Data URL (data:image/png;base64,...).
    """
    if "," in data_url:
        _, encoded = data_url.split(",", 1)
    else:
        encoded = data_url

    raw_bytes = base64.b64decode(encoded)
    png_bytes, _ = remove_background_from_bytes(raw_bytes)
    b64_output = base64.b64encode(png_bytes).decode("ascii")
    return f"data:image/png;base64,{b64_output}"
