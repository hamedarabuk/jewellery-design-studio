"""
scripts/lib/image_io.py - image metadata sanitiser for AI-generated images.

Why this exists: gpt-image-2, Gemini Nano Banana, and other AI image
generators embed C2PA / Content Authenticity Initiative metadata as PNG
iTXt chunks (a `c2pa` keyword plus `xmpRights` etc) or JPEG XMP segments.
LinkedIn, Instagram, and other social platforms read these and display a
visible "Cr" or "Made with AI" badge on the post.

This module strips ALL ancillary metadata by re-encoding the pixel data
into a fresh image, leaving only the bare image. The invisible SynthID
watermark embedded in pixels by Google cannot be removed by metadata
stripping (and we make no attempt to do so).

Stdlib + Pillow only.

Public API:
    strip_metadata(path) -> Path        # strip in place, returns the path
    has_c2pa_chunk(path) -> bool        # quick sniff for verification
"""

from __future__ import annotations

from pathlib import Path
from typing import Optional


def strip_metadata(path: Path | str, out_path: Optional[Path | str] = None) -> Path:
    """
    Strip ALL metadata (EXIF, XMP, iTXt including C2PA, tEXt, etc.) from a
    PNG, JPEG, or WebP image. If `out_path` is None, overwrites the source
    file in place.

    The strip is implemented by building a fresh Image with the same mode
    and size, copying raw pixel data via putdata, then saving with explicit
    empty metadata arguments. This guarantees no ancillary chunks survive.

    Returns the path written. Raises ImportError if Pillow is not installed.
    """
    from PIL import Image

    src = Path(path)
    dst = Path(out_path) if out_path is not None else src

    img = Image.open(src)
    img.load()

    # Build a fresh image with the same mode and size, copy raw pixel data
    # only. This drops all metadata-bearing chunks because the new image
    # has no info dict and no ancillary chunks attached.
    clean = Image.new(img.mode, img.size)
    clean.putdata(list(img.getdata()))

    fmt = (img.format or "PNG").upper()
    save_kwargs: dict = {"format": fmt}
    if fmt == "PNG":
        save_kwargs["optimize"] = True
        # pnginfo=empty PngInfo ensures no chunks beyond the required ones
        # are written.
        from PIL import PngImagePlugin

        save_kwargs["pnginfo"] = PngImagePlugin.PngInfo()
    elif fmt in ("JPEG", "JPG"):
        save_kwargs["quality"] = 95
        save_kwargs["optimize"] = True
        # exif=b"" prevents Pillow from carrying any EXIF.
        save_kwargs["exif"] = b""
    elif fmt == "WEBP":
        save_kwargs["quality"] = 95
        # WebP metadata is handled via separate kwargs; passing exif/xmp
        # empty explicitly drops them.
        save_kwargs["exif"] = b""
        save_kwargs["xmp"] = b""

    clean.save(dst, **save_kwargs)
    return dst


def has_c2pa_chunk(path: Path | str) -> bool:
    """Quick byte-level sniff: does this image file contain a C2PA manifest
    or any of the well-known AI-generator metadata signatures?

    Returns True if any of the following byte patterns appear in the file:
    c2pa, JUMB, contentauth, contentcredentials, openai, synthid, gpt-image.
    Case-insensitive.

    Useful as a smoke test after strip_metadata to confirm the strip worked.
    """
    p = Path(path)
    data = p.read_bytes()
    lower = data.lower()
    needles = [
        b"c2pa",
        b"jumb",
        b"contentauth",
        b"contentcredentials",
        b"openai",
        b"gpt-image",
        b"synthid",
    ]
    for needle in needles:
        if needle in lower:
            return True
    return False


def metadata_report(path: Path | str) -> dict:
    """Return a structured report on what metadata-bearing keys an image
    currently carries. Useful for debugging suspected leaks.
    """
    from PIL import Image

    p = Path(path)
    img = Image.open(p)
    info_dict = dict(img.info) if img.info else {}

    # Sanitise bytes values for JSON-safe reporting.
    safe_info = {}
    for k, v in info_dict.items():
        if isinstance(v, bytes):
            safe_info[k] = f"<{len(v)} bytes>"
        else:
            safe_info[k] = str(v)[:200]

    return {
        "path": str(p),
        "format": img.format,
        "mode": img.mode,
        "size_px": list(img.size),
        "info_keys": list(info_dict.keys()),
        "info_sample": safe_info,
        "has_c2pa_signature": has_c2pa_chunk(p),
    }
