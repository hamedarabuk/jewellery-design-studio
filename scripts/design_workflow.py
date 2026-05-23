"""
scripts/design_workflow.py - File-system bookkeeping for the design workflow.

Helpers for the jewellery-design-from-reference skill. No image generation
here; that lives in gpt_image_client.py. This module handles:

    - Slugifying piece names ("Albion Garland" -> "albion-garland").
    - Computing the next position number from a brand's INDEX.md.
    - Building Telegram-friendly JPEG previews from large PNG renders.
    - Building 2x2 comparison collages for variation rounds.
    - Resolving brand and piece paths.

Run as a CLI for individual operations:

    python scripts/design_workflow.py slugify "Albion Garland"
    python scripts/design_workflow.py next-position --brand mappin-webb-collection-01
    python scripts/design_workflow.py preview --input render.png --output render-tg.jpg
    python scripts/design_workflow.py collage \\
        --inputs v1.png v2.png v3.png v4.png \\
        --labels "V1: wreath" "V2: twist" "V3: bloom" "V4: rose-only" \\
        --output comparison.png \\
        --title "Albion Garland - 4 variations"
    python scripts/design_workflow.py verify-clean --path render-front.png
"""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parent.parent
SCRIPTS_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(SCRIPTS_DIR))  # so `from lib.image_io import ...` works

EXIT_OK = 0
EXIT_ERROR = 1

PREVIEW_MAX_EDGE = 2400
PREVIEW_QUALITY = 92


def slugify(name: str) -> str:
    """Lowercase, hyphen-separated slug suitable for folder names.

    "Albion Garland" -> "albion-garland"
    "Robin Redbreast" -> "robin-redbreast"
    """
    s = name.strip().lower()
    s = re.sub(r"[^a-z0-9]+", "-", s)
    s = re.sub(r"-+", "-", s).strip("-")
    return s


def brand_root(brand_slug: str) -> Path:
    """Return the brand folder path (created lazily by callers)."""
    return PROJECT_ROOT / "brands" / brand_slug


def proposed_dir(brand_slug: str, piece_slug: str) -> Path:
    return brand_root(brand_slug) / "proposed" / piece_slug


def approved_dir(brand_slug: str, position: int, piece_slug: str) -> Path:
    nn = f"{position:02d}"
    return brand_root(brand_slug) / "approved" / f"{nn}-{piece_slug}"


def next_position(brand_slug: str) -> int:
    """Read brands/<slug>/approved/INDEX.md and return the next position number.

    INDEX.md is expected to list approved pieces in a table; the column "#"
    holds the position number. The next position is max(existing) + 1. If
    INDEX.md does not exist or no entries are found, returns 1.
    """
    index = brand_root(brand_slug) / "approved" / "INDEX.md"
    if not index.exists():
        return 1
    text = index.read_text(encoding="utf-8")
    # Look for two-digit position markers at the start of table rows like "| 01 | ... |"
    matches = re.findall(r"^\|\s*(\d{1,3})\s*\|", text, flags=re.MULTILINE)
    if not matches:
        return 1
    return max(int(m) for m in matches) + 1


def build_preview(input_path: Path, output_path: Path) -> tuple[int, int, int]:
    """Build a Telegram-friendly JPEG preview from a large PNG.

    Returns (width, height, kb_size) of the output.
    """
    from PIL import Image

    img = Image.open(input_path).convert("RGB")
    long_edge = max(img.size)
    if long_edge > PREVIEW_MAX_EDGE:
        scale = PREVIEW_MAX_EDGE / long_edge
        new_size = (int(img.size[0] * scale), int(img.size[1] * scale))
        img = img.resize(new_size, Image.LANCZOS)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    img.save(
        output_path,
        "JPEG",
        quality=PREVIEW_QUALITY,
        optimize=True,
        progressive=True,
    )
    kb = output_path.stat().st_size // 1024
    return img.size[0], img.size[1], kb


def build_collage(
    inputs: list[Path],
    labels: list[str],
    output_path: Path,
    title: str | None = None,
    cell_size: int = 900,
) -> Path:
    """Build a 2x2 labelled collage from up to 4 input images.

    Each cell is `cell_size x cell_size` pixels. A dark label band sits at
    the bottom of each cell. Optional title bar across the top.
    """
    from PIL import Image, ImageDraw, ImageFont

    if len(inputs) != len(labels):
        raise ValueError("inputs and labels must have the same length")
    if len(inputs) > 4:
        raise ValueError("collage supports a maximum of 4 cells (2x2)")
    while len(inputs) < 4:
        inputs.append(None)  # type: ignore
        labels.append("")

    header_h = 70 if title else 0
    canvas = Image.new("RGB", (cell_size * 2, cell_size * 2 + header_h), "white")
    draw = ImageDraw.Draw(canvas)

    try:
        font_label = ImageFont.truetype("arial.ttf", 30)
        font_title = ImageFont.truetype("arialbd.ttf", 40)
    except OSError:
        font_label = ImageFont.load_default()
        font_title = ImageFont.load_default()

    if title:
        draw.text((40, 18), title, fill="black", font=font_title)

    for i in range(4):
        path = inputs[i]
        label = labels[i]
        x = (i % 2) * cell_size
        y = header_h + (i // 2) * cell_size
        if path is not None:
            img = Image.open(path).convert("RGB").resize((cell_size, cell_size))
            canvas.paste(img, (x, y))
        if label:
            band_h = 52
            draw.rectangle(
                [(x, y + cell_size - band_h), (x + cell_size, y + cell_size)],
                fill=(20, 20, 20),
            )
            draw.text(
                (x + 22, y + cell_size - band_h + 10),
                label,
                fill="white",
                font=font_label,
            )

    output_path.parent.mkdir(parents=True, exist_ok=True)
    canvas.save(output_path, "PNG", optimize=True)
    return output_path


def write_manifest(manifest_path: Path, data: dict) -> None:
    """Write a piece manifest.json with consistent formatting."""
    manifest_path.parent.mkdir(parents=True, exist_ok=True)
    manifest_path.write_text(
        json.dumps(data, indent=2, ensure_ascii=False) + "\n",
        encoding="utf-8",
    )


# ---------------------------------------------------------------------------
# CLI
# ---------------------------------------------------------------------------


def _cmd_slugify(args: argparse.Namespace) -> int:
    print(slugify(args.name))
    return EXIT_OK


def _cmd_next_position(args: argparse.Namespace) -> int:
    print(next_position(args.brand))
    return EXIT_OK


def _cmd_preview(args: argparse.Namespace) -> int:
    w, h, kb = build_preview(args.input, args.output)
    print(f"preview: {w}x{h}, {kb} KB -> {args.output}", file=sys.stderr)
    return EXIT_OK


def _cmd_collage(args: argparse.Namespace) -> int:
    if len(args.inputs) != len(args.labels):
        print(
            f"collage: --inputs ({len(args.inputs)}) and --labels "
            f"({len(args.labels)}) must match",
            file=sys.stderr,
        )
        return EXIT_ERROR
    build_collage(
        inputs=list(args.inputs),
        labels=list(args.labels),
        output_path=args.output,
        title=args.title,
    )
    print(f"collage saved -> {args.output}", file=sys.stderr)
    return EXIT_OK


def _cmd_verify_clean(args: argparse.Namespace) -> int:
    """Byte-level sniff for AI-generator metadata. Exit 0 if clean, 1 if not."""
    from lib.image_io import has_c2pa_chunk, metadata_report
    import json

    if not args.path.exists():
        print(f"verify-clean: file not found: {args.path}", file=sys.stderr)
        return EXIT_ERROR

    report = metadata_report(args.path)
    if args.json:
        print(json.dumps(report, indent=2))
    else:
        print(f"path:    {report['path']}")
        print(f"format:  {report['format']}  mode={report['mode']}  size={report['size_px']}")
        print(f"info keys: {report['info_keys'] or '(none)'}")
        if report["info_sample"]:
            for k, v in report["info_sample"].items():
                print(f"  {k}: {v}")
        print(
            f"has_c2pa_signature: {report['has_c2pa_signature']}"
        )

    if has_c2pa_chunk(args.path):
        print(
            "verify-clean: FAIL - image still carries an AI-generator signature.",
            file=sys.stderr,
        )
        return EXIT_ERROR

    print("verify-clean: OK - no AI-generator metadata detected.", file=sys.stderr)
    return EXIT_OK


def main() -> int:
    parser = argparse.ArgumentParser(
        description="File-system bookkeeping for the jewellery design workflow."
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p_slug = sub.add_parser("slugify", help="Lowercase hyphenate a name.")
    p_slug.add_argument("name", help="Piece name to slugify.")
    p_slug.set_defaults(func=_cmd_slugify)

    p_next = sub.add_parser(
        "next-position",
        help="Read INDEX.md and return the next two-digit position number.",
    )
    p_next.add_argument("--brand", required=True, help="Brand slug.")
    p_next.set_defaults(func=_cmd_next_position)

    p_prev = sub.add_parser(
        "preview",
        help="Build a Telegram-friendly JPEG preview from a large PNG.",
    )
    p_prev.add_argument("--input", type=Path, required=True)
    p_prev.add_argument("--output", type=Path, required=True)
    p_prev.set_defaults(func=_cmd_preview)

    p_coll = sub.add_parser(
        "collage",
        help="Build a labelled 2x2 comparison collage from up to 4 renders.",
    )
    p_coll.add_argument("--inputs", nargs="+", type=Path, required=True)
    p_coll.add_argument("--labels", nargs="+", required=True)
    p_coll.add_argument("--output", type=Path, required=True)
    p_coll.add_argument("--title", default=None)
    p_coll.set_defaults(func=_cmd_collage)

    p_verify = sub.add_parser(
        "verify-clean",
        help=(
            "Verify a render has no AI-generator metadata (C2PA, "
            "ContentCredentials, OpenAI, SynthID signatures). Exits 0 if clean."
        ),
    )
    p_verify.add_argument("--path", type=Path, required=True)
    p_verify.add_argument(
        "--json", action="store_true", help="Output the report as JSON."
    )
    p_verify.set_defaults(func=_cmd_verify_clean)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
