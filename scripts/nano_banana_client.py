"""
Gemini image generation client for jewellery-design-studio.

API contract: --action generate with --prompt, optional --reference (up to 5),
--aspect (default 4:5), --size (default 1280x1600), --output. Strips C2PA
metadata on every successful generation. SynthID pixel watermark is left intact.

Ported from Persian CLAW scripts/nano_banana_client.py on 2026-05-27.
Standalone: no Persian CLAW imports; uses this repo's config.py and
scripts/lib/image_io.py.

Dependencies:
    pip install google-genai pillow>=10.0

Auth:
    GEMINI_API_KEY must be set in .env (at project root).

Usage:
    python scripts/nano_banana_client.py \\
        --action generate \\
        --prompt "..." \\
        --aspect 4:5 \\
        --output brands/my-brand/proposed/my-piece/render-v1.png

    # With character/style consistency references (up to 5):
    python scripts/nano_banana_client.py \\
        --action generate \\
        --prompt "..." \\
        --reference brands/my-brand/proposed/my-piece/render-v1.png \\
        --aspect 4:5 \\
        --output brands/my-brand/proposed/my-piece/render-v2.png

Exit codes: 0 = success, 1 = error.

Note: SynthID watermark is always embedded by Google and cannot be removed.
Pricing: ~$0.039/image. Free tier: 500 requests/day.
"""

from __future__ import annotations

import argparse
import base64
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent

EXIT_OK = 0
EXIT_ERROR = 1

_VALID_RATIOS = {
    "1:1", "16:9", "9:16", "4:5", "3:4", "3:2", "2:3", "4:3",
}

# Aspect-ratio hint appended to the prompt. Gemini image models do not accept
# a structured aspect_ratio config parameter so we embed the hint in the text.
_RATIO_HINT = {
    "1:1":  "square 1:1 aspect ratio",
    "16:9": "wide landscape 16:9 aspect ratio",
    "9:16": "tall portrait 9:16 aspect ratio",
    "4:5":  "portrait 4:5 aspect ratio",
    "3:4":  "portrait 3:4 aspect ratio",
    "3:2":  "landscape 3:2 aspect ratio",
    "2:3":  "portrait 2:3 aspect ratio",
    "4:3":  "landscape 4:3 aspect ratio",
}

_MODEL = "gemini-3-pro-image-preview"


def _load_api_key() -> str:
    sys.path.insert(0, str(PROJECT_ROOT))
    try:
        from config import config
    except ImportError as exc:
        print(
            f"nano_banana: could not import config.py from project root: {exc}",
            file=sys.stderr,
        )
        sys.exit(EXIT_ERROR)
    if not config.gemini_api_key:
        print(
            "nano_banana: GEMINI_API_KEY is not set. "
            "Add it to .env at the project root.",
            file=sys.stderr,
        )
        sys.exit(EXIT_ERROR)
    return config.gemini_api_key


def _strip(output_path: Path) -> None:
    """Strip C2PA / Content Authenticity metadata in place."""
    try:
        sys.path.insert(0, str(PROJECT_ROOT / "scripts"))
        from lib.image_io import strip_metadata
        strip_metadata(output_path)
    except Exception as exc:
        print(
            f"nano_banana: warning — metadata strip failed: {exc}",
            file=sys.stderr,
        )


def _generate(
    prompt: str,
    aspect_ratio: str,
    output_path: Path,
    reference_paths: list[Path] | None = None,
    keep_metadata: bool = False,
) -> None:
    try:
        from google import genai
        from google.genai import types
    except ImportError:
        print(
            "nano_banana: google-genai is not installed. "
            "Run: pip install google-genai",
            file=sys.stderr,
        )
        sys.exit(EXIT_ERROR)

    if aspect_ratio not in _VALID_RATIOS:
        print(
            f"nano_banana: unsupported aspect ratio '{aspect_ratio}'. "
            f"Valid options: {', '.join(sorted(_VALID_RATIOS))}",
            file=sys.stderr,
        )
        sys.exit(EXIT_ERROR)

    api_key = _load_api_key()
    client = genai.Client(api_key=api_key)

    full_prompt = f"{prompt}, {_RATIO_HINT[aspect_ratio]}"

    refs = reference_paths or []
    if refs:
        print(
            f"nano_banana: generating {aspect_ratio} image via {_MODEL} "
            f"with {len(refs)} reference(s) ...",
            file=sys.stderr,
        )
        parts: list = []
        for ref_path in refs:
            img_bytes = ref_path.read_bytes()
            ext = ref_path.suffix.lower()
            mime = {
                ".jpg": "image/jpeg", ".jpeg": "image/jpeg",
                ".png": "image/png", ".webp": "image/webp",
            }.get(ext, "image/png")
            parts.append(types.Part.from_bytes(data=img_bytes, mime_type=mime))
        parts.append(full_prompt)
        contents = parts
    else:
        print(
            f"nano_banana: generating {aspect_ratio} image via {_MODEL} ...",
            file=sys.stderr,
        )
        contents = full_prompt

    response = client.models.generate_content(
        model=_MODEL,
        contents=contents,
        config=types.GenerateContentConfig(
            response_modalities=["IMAGE", "TEXT"],
        ),
    )

    image_bytes: bytes | None = None
    for part in response.candidates[0].content.parts:
        if part.inline_data is not None:
            raw = part.inline_data.data
            if isinstance(raw, (bytes, bytearray)):
                image_bytes = bytes(raw)
            else:
                image_bytes = base64.b64decode(raw)
            break

    if not image_bytes:
        print("nano_banana: no image returned by the API.", file=sys.stderr)
        sys.exit(EXIT_ERROR)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    output_path.write_bytes(image_bytes)

    if keep_metadata:
        print(
            "nano_banana: keep-metadata flag set, leaving C2PA tags intact. "
            "Re-strip before social publish.",
            file=sys.stderr,
        )
    else:
        _strip(output_path)

    size_kb = output_path.stat().st_size // 1024
    print(f"nano_banana: saved {size_kb} KB -> {output_path}", file=sys.stderr)


def _upscale(input_path: Path, target: str, output_path: Path) -> None:
    try:
        from PIL import Image
    except ImportError:
        print(
            "nano_banana: Pillow is not installed. Run: pip install pillow>=10.0",
            file=sys.stderr,
        )
        sys.exit(EXIT_ERROR)

    try:
        w_str, h_str = target.split("x")
        target_w, target_h = int(w_str), int(h_str)
    except ValueError:
        print(
            f"nano_banana: --size value '{target}' must be WIDTHxHEIGHT, "
            "e.g. 1280x1600",
            file=sys.stderr,
        )
        sys.exit(EXIT_ERROR)

    print(
        f"nano_banana: upscaling {input_path.name} -> {target_w}x{target_h} "
        "(LANCZOS) ...",
        file=sys.stderr,
    )
    with Image.open(input_path) as img:
        upscaled = img.resize((target_w, target_h), Image.LANCZOS)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        upscaled.save(output_path, format="PNG", optimize=True)

    size_kb = output_path.stat().st_size // 1024
    print(
        f"nano_banana: upscaled {size_kb} KB -> {output_path}",
        file=sys.stderr,
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description=(
            "Generate images via Gemini (Nano Banana) for editorial "
            "on-model jewellery renders. See docs/luxury-studio-grammar.md "
            "for the full prompt grammar."
        )
    )
    parser.add_argument(
        "--action",
        choices=["generate"],
        required=True,
        help="Action to perform.",
    )
    parser.add_argument(
        "--prompt",
        required=True,
        help="Text prompt. Assemble using templates/on-model-prompt-template.md.",
    )
    parser.add_argument(
        "--aspect",
        default="4:5",
        dest="aspect_ratio",
        metavar="RATIO",
        help=(
            f"Aspect ratio. One of: {', '.join(sorted(_VALID_RATIOS))}. "
            "Default: 4:5 (editorial portrait, the recommended default for "
            "on-model jewellery)."
        ),
    )
    parser.add_argument(
        "--size",
        metavar="WIDTHxHEIGHT",
        default="1280x1600",
        help=(
            "If set, upscale the generated image to this resolution using "
            "Pillow LANCZOS and write to --output. Default: 1280x1600 "
            "(4:5 retina, ~188 KB JPG after strip)."
        ),
    )
    parser.add_argument(
        "--output",
        required=True,
        type=Path,
        help="Output file path (PNG). Parent directories are created automatically.",
    )
    parser.add_argument(
        "--reference",
        action="append",
        default=[],
        dest="reference",
        type=Path,
        metavar="PATH",
        help=(
            "Local image file (PNG, JPG, or WebP) for character or style "
            "consistency. Pass up to 5 times. Google AI caps references at 5."
        ),
    )
    parser.add_argument(
        "--keep-metadata",
        action="store_true",
        dest="keep_metadata",
        help=(
            "Do NOT strip C2PA / Content Authenticity metadata. Use only when "
            "feeding the output to another AI model whose content filter relies "
            "on those tags. Always re-strip before any social publish."
        ),
    )
    args = parser.parse_args()

    reference_paths: list[Path] = args.reference or []
    if len(reference_paths) > 5:
        print(
            f"nano_banana: too many --reference files ({len(reference_paths)}). "
            "Maximum is 5 (Google AI character consistency cap).",
            file=sys.stderr,
        )
        return EXIT_ERROR

    for ref in reference_paths:
        if not ref.exists():
            print(
                f"nano_banana: --reference path does not exist: {ref}",
                file=sys.stderr,
            )
            return EXIT_ERROR
        if not ref.is_file():
            print(
                f"nano_banana: --reference path is not a file: {ref}",
                file=sys.stderr,
            )
            return EXIT_ERROR

    if args.action == "generate":
        # Always generate at native aspect ratio first, then upscale if --size.
        if args.size and args.size != "native":
            native_stem = args.output.stem + "_native"
            native_path = args.output.with_stem(native_stem)
            _generate(
                args.prompt, args.aspect_ratio, native_path,
                reference_paths, keep_metadata=args.keep_metadata,
            )
            _upscale(native_path, args.size, args.output)
            # Remove the intermediate native file.
            try:
                native_path.unlink(missing_ok=True)
            except Exception:
                pass
        else:
            _generate(
                args.prompt, args.aspect_ratio, args.output,
                reference_paths, keep_metadata=args.keep_metadata,
            )

    return EXIT_OK


if __name__ == "__main__":
    sys.exit(main())
