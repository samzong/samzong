#!/usr/bin/env python3
"""Composite avatar PNG on white and export a lens crop for visual QA."""

from __future__ import annotations

import argparse
from pathlib import Path

from PIL import Image


def main() -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", "-i", type=Path, required=True)
    p.add_argument("--out-dir", type=Path, required=True)
    p.add_argument("--bg", default="#f0f0f0", help="Hex background for full preview")
    args = p.parse_args()

    im = Image.open(args.input).convert("RGBA")
    args.out_dir.mkdir(parents=True, exist_ok=True)
    stem = args.input.stem

    hexbg = args.bg.lstrip("#")
    rgb = tuple(int(hexbg[i : i + 2], 16) for i in (0, 2, 4))
    white = Image.new("RGBA", im.size, (*rgb, 255))
    white.alpha_composite(im)
    full = args.out_dir / f"{stem}-on-bg.jpg"
    white.convert("RGB").save(full, quality=92)

    crop = im.crop((340, 380, 600, 520))
    bg = Image.new("RGBA", crop.size, (*rgb, 255))
    bg.alpha_composite(crop)
    lens = args.out_dir / f"{stem}-lens.jpg"
    bg.resize((crop.width * 2, crop.height * 2), Image.NEAREST).convert("RGB").save(
        lens, quality=92
    )
    print(f"wrote {full}")
    print(f"wrote {lens}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
