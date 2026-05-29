"""Sync the maintainer's canonical brand content into this public skill.

Single source of truth: the Persian CLAW workspace at
``D:/01 Projects/Persian CLAW/workspace/silux/brand/``. This skill repo carries
a working copy so the two stop drifting. Run this after editing the source.

What it copies:
  luxury-studio-grammar.md          -> docs/                       (ships)
  photography-styles/*.md           -> styles/                     (ships)
  subjects/{eleanor,yasmin,margaret}/* -> brands/silux-london/subjects/<slug>/
  collections/*.json + brand.json   -> brands/silux-london/

Note: ``brands/`` and ``*.png`` are gitignored in this public repo by design
(the white-label pattern keeps each brand's data and renders private). So the
Silux ambassadors and collections refresh the maintainer's LOCAL clone only;
``styles/`` and ``docs/`` are the parts that ship. Edit upstream, never here.

Usage:
    python scripts/sync_from_source.py            # copy
    python scripts/sync_from_source.py --dry-run  # show what would change
"""
from __future__ import annotations

import argparse
import shutil
import sys
from pathlib import Path

SOURCE_ROOT = Path(r"D:/01 Projects/Persian CLAW/workspace/silux/brand")
REPO_ROOT = Path(__file__).resolve().parent.parent
SILUX = REPO_ROOT / "brands" / "silux-london"

# (source relative to SOURCE_ROOT, destination relative to REPO_ROOT)
FILE_MAP: list[tuple[str, str]] = [
    ("luxury-studio-grammar.md", "docs/luxury-studio-grammar.md"),
    ("brand.json", "brands/silux-london/brand.json"),
]
DIR_MAP: list[tuple[str, str]] = [
    ("photography-styles", "styles"),
    ("collections", "brands/silux-london/collections"),
]
SUBJECTS = ["eleanor", "yasmin", "margaret"]


def copy_file(src: Path, dst: Path, dry: bool) -> int:
    if not src.is_file():
        print(f"  skip (missing source): {src}")
        return 0
    print(f"  {'would copy' if dry else 'copied'}: {src.name} -> {dst.relative_to(REPO_ROOT)}")
    if not dry:
        dst.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(src, dst)
    return 1


def copy_dir(src: Path, dst: Path, dry: bool, pattern: str = "*") -> int:
    if not src.is_dir():
        print(f"  skip (missing source dir): {src}")
        return 0
    count = 0
    for item in sorted(src.glob(pattern)):
        if item.is_file():
            count += copy_file(item, dst / item.name, dry)
    return count


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--dry-run", action="store_true", help="show changes only")
    args = parser.parse_args()
    dry = args.dry_run

    if not SOURCE_ROOT.is_dir():
        print(f"Source not found: {SOURCE_ROOT}")
        print("This sync only runs on the maintainer's machine. Nothing to do.")
        return 0

    print(f"Syncing from {SOURCE_ROOT}{' (dry run)' if dry else ''}")
    total = 0
    for rel_src, rel_dst in FILE_MAP:
        total += copy_file(SOURCE_ROOT / rel_src, REPO_ROOT / rel_dst, dry)
    for rel_src, rel_dst in DIR_MAP:
        total += copy_dir(SOURCE_ROOT / rel_src, REPO_ROOT / rel_dst, dry)
    for slug in SUBJECTS:
        total += copy_dir(
            SOURCE_ROOT / "subjects" / slug, SILUX / "subjects" / slug, dry
        )

    print(f"\n{'Would sync' if dry else 'Synced'} {total} file(s).")
    return 0


if __name__ == "__main__":
    sys.exit(main())
