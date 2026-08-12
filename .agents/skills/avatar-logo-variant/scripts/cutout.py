#!/usr/bin/env python3
"""Chroma-key cutout for identity-preserving logo avatar variants.

Input: RGB image with flat magenta/pink chroma-key background (from image_edit).
Output: RGBA PNG with:
  - edge-connected background removal
  - magenta/pink fringe despill + edge contract
  - lens key-reflection cleanup (tight ROIs; does not paint over face)

Deps: pillow, numpy
  Prefer:  uv run --with numpy --with pillow python scripts/cutout.py ...
"""

from __future__ import annotations

import argparse
import sys
from collections import deque
from pathlib import Path

import numpy as np
from PIL import Image, ImageFilter


def sample_border_key(arr: np.ndarray, border: int = 10) -> np.ndarray:
    strips = [
        arr[:border, :, :].reshape(-1, 3),
        arr[-border:, :, :].reshape(-1, 3),
        arr[:, :border, :].reshape(-1, 3),
        arr[:, -border:, :].reshape(-1, 3),
    ]
    return np.median(np.concatenate(strips, 0), axis=0)


def flood_bg(near: np.ndarray) -> np.ndarray:
    h, w = near.shape
    bg = np.zeros((h, w), dtype=bool)
    q: deque[tuple[int, int]] = deque()
    for x in range(w):
        if near[0, x]:
            bg[0, x] = True
            q.append((0, x))
        if near[h - 1, x]:
            bg[h - 1, x] = True
            q.append((h - 1, x))
    for y in range(h):
        if near[y, 0]:
            bg[y, 0] = True
            q.append((y, 0))
        if near[y, w - 1]:
            bg[y, w - 1] = True
            q.append((y, w - 1))
    while q:
        y, x = q.popleft()
        for ny, nx in ((y - 1, x), (y + 1, x), (y, x - 1), (y, x + 1)):
            if 0 <= ny < h and 0 <= nx < w and near[ny, nx] and not bg[ny, nx]:
                bg[ny, nx] = True
                q.append((ny, nx))
    return bg


def cutout(
    src_rgb: np.ndarray,
    *,
    thr_lo: float = 24.0,
    thr_hi: float = 72.0,
    edge_contract: int = 2,
) -> np.ndarray:
    """Return HxWx4 uint8 RGBA."""
    h, w, _ = src_rgb.shape
    src = src_rgb.astype(np.float32)
    key = sample_border_key(src, 10)
    dist = np.linalg.norm(src - key[None, None, :], axis=2)
    bg = flood_bg(dist <= thr_hi)
    span = max(thr_hi - thr_lo, 1e-6)

    alpha = np.ones((h, w), np.float32)
    alpha[bg] = np.clip((dist[bg] - thr_lo) / span, 0, 1)
    alpha[bg & (dist <= thr_lo)] = 0.0

    r, g, b = src[:, :, 0].copy(), src[:, :, 1].copy(), src[:, :, 2].copy()
    mag = np.maximum(0.0, np.minimum(r, b) - g)
    m = (alpha > 0.01) & (mag > 1.5)
    keyness = np.clip(1.0 - dist / thr_hi, 0, 1)
    s = np.clip(mag / 14.0 * 0.95 + keyness * 0.55, 0, 1)
    r = np.where(m, r - (r - g) * s, r)
    b = np.where(m, b - (b - g) * s, b)
    mag2 = np.maximum(0.0, np.minimum(r, b) - g)
    m2 = m & (mag2 > 3)
    mid = (r + g + b) / 3
    t = np.clip(mag2 / 16, 0, 1)
    r = np.where(m2, r * (1 - t) + mid * t, r)
    b = np.where(m2, b * (1 - t) + mid * t, b)
    g = np.where(m2, g * (1 - 0.5 * t) + mid * 0.5 * t, g)

    # Tight lens ROIs for the standard 3/4 pose base avatar (do not widen).
    yy, xx = np.mgrid[0:h, 0:w]
    lens = np.zeros((h, w), dtype=bool)
    for cx, cy, rx, ry in ((418, 448, 48, 36), (528, 450, 46, 34)):
        lens |= ((xx - cx) / rx) ** 2 + ((yy - cy) / ry) ** 2 <= 1.0

    src_r, src_g, src_b = src[:, :, 0], src[:, :, 1], src[:, :, 2]
    src_mag = np.maximum(0.0, np.minimum(src_r, src_b) - src_g)
    is_skinish = (
        (src_g > 85)
        & (src_r > src_g - 10)
        & (src_r > src_b + 10)
        & (src_mag < 15)
    )
    is_eyeish = (
        (src_r + src_g + src_b < 220)
        & (src_r > 40)
        & (src_g > 30)
        & (src_b > 20)
        & (src_mag < 12)
        & (src_r > src_b)
    )
    is_frame = (src_r + src_g + src_b < 100) & (
        (
            np.maximum(np.maximum(src_r, src_g), src_b)
            - np.minimum(np.minimum(src_r, src_g), src_b)
        )
        < 30
    )
    is_key_reflect = (
        (src_mag > 18)
        | ((dist < thr_hi * 0.95) & (src_mag > 8))
        | (
            (src_r > 90)
            & (src_b > 90)
            & (src_g < np.minimum(src_r, src_b) - 15)
        )
    )
    fix = lens & (~bg) & is_key_reflect & (~is_skinish) & (~is_eyeish) & (~is_frame)
    base = 40.0
    r = np.where(fix, base + (g - base) * 0.1, r)
    g = np.where(fix, base * 0.9 + g * 0.05, g)
    b = np.where(fix, base * 0.95 + (b - base) * 0.08, b)
    alpha = np.where(fix, 1.0, alpha)
    partial_key = lens & (~bg) & (alpha < 0.95) & is_key_reflect
    r = np.where(partial_key, 38, r)
    g = np.where(partial_key, 34, g)
    b = np.where(partial_key, 32, b)
    alpha = np.where(partial_key, 1.0, alpha)
    magf = np.maximum(0.0, np.minimum(r, b) - g)
    r = np.where(fix & (magf > 0), r - magf, r)
    b = np.where(fix & (magf > 0), b - magf, b)

    a8 = np.clip(np.rint(alpha * 255), 0, 255).astype(np.uint8)
    rgb8 = np.stack(
        [np.clip(r, 0, 255), np.clip(g, 0, 255), np.clip(b, 0, 255)], axis=2
    ).astype(np.uint8)
    rgb8[a8 <= 2] = 0
    a8[a8 <= 2] = 0
    out = Image.fromarray(np.dstack([rgb8, a8]), "RGBA")

    a_ch = out.getchannel("A")
    for _ in range(max(0, edge_contract)):
        a_ch = a_ch.filter(ImageFilter.MinFilter(3))
    rc, gc, bc, _ = out.split()
    out = Image.merge("RGBA", (rc, gc, bc, a_ch))
    arr = np.asarray(out).astype(np.float32)
    aa, rr, gg, bb = arr[:, :, 3], arr[:, :, 0], arr[:, :, 1], arr[:, :, 2]

    pad = np.pad(aa, 1, mode="edge")
    nmin = np.minimum.reduce(
        [
            pad[:-2, 1:-1],
            pad[2:, 1:-1],
            pad[1:-1, :-2],
            pad[1:-1, 2:],
            pad[:-2, :-2],
            pad[:-2, 2:],
            pad[2:, :-2],
            pad[2:, 2:],
        ]
    )
    edge = (aa > 20) & (nmin < 25)
    mag = np.maximum(0.0, np.minimum(rr, bb) - gg)

    aa = np.where(edge & (mag > 2.0), 0, aa)
    e = edge & (aa > 0)
    rr = np.where(e, rr - mag * 1.5, rr)
    bb = np.where(e, bb - mag * 1.5, bb)
    aa = np.where(e & (mag > 1), aa * 0.7, aa)

    interior = (aa > 200) & (~edge) & (mag > 5) & ((rr + gg + bb) < 400) & (gg < 140)
    rr = np.where(interior, rr - mag * 1.2, rr)
    bb = np.where(interior, bb - mag * 1.2, bb)

    mag = np.maximum(0.0, np.minimum(rr, bb) - gg)
    semi = (aa > 0) & (aa < 230) & (mag > 1)
    rr = np.where(semi, rr - mag * 1.4, rr)
    bb = np.where(semi, bb - mag * 1.4, bb)
    aa = np.where(semi & (mag > 3), aa * 0.45, aa)

    mag = np.maximum(0.0, np.minimum(rr, bb) - gg)
    rr = np.where(mag > 0, rr - mag, rr)
    bb = np.where(mag > 0, bb - mag, bb)

    aa = np.where(aa < 40, 0, aa)
    rr = np.where(aa == 0, 0, rr)
    gg = np.where(aa == 0, 0, gg)
    bb = np.where(aa == 0, 0, bb)

    fix2 = lens & is_key_reflect & (~is_skinish) & (~is_eyeish) & (~is_frame)
    solid = aa > 200
    sp = np.pad(solid.astype(np.int16), 1)
    sn = sp[:-2, 1:-1] + sp[2:, 1:-1] + sp[1:-1, :-2] + sp[1:-1, 2:]
    hole = fix2 & (aa < 40) & (sn >= 2)
    rr[hole] = 38
    gg[hole] = 34
    bb[hole] = 32
    aa[hole] = 255
    rr = np.where(fix2 & (aa > 0), np.minimum(rr, gg + 3), rr)
    bb = np.where(fix2 & (aa > 0), np.minimum(bb, gg + 3), bb)
    aa = np.where(fix2 & (aa > 0), 255, aa)

    out_arr = np.stack(
        [
            np.clip(rr, 0, 255).astype(np.uint8),
            np.clip(gg, 0, 255).astype(np.uint8),
            np.clip(bb, 0, 255).astype(np.uint8),
            np.clip(aa, 0, 255).astype(np.uint8),
        ],
        axis=2,
    )
    out_arr[out_arr[:, :, 3] == 0, :3] = 0
    return out_arr


def metrics(rgba: np.ndarray) -> dict[str, int]:
    a = rgba[:, :, 3]
    r = rgba[:, :, 0].astype(np.int16)
    g = rgba[:, :, 1].astype(np.int16)
    b = rgba[:, :, 2].astype(np.int16)
    mag = np.maximum(0, np.minimum(r, b) - g)
    pink = int(((a > 20) & (mag > 3)).sum())
    pad = np.pad(a, 1)
    nmin = np.minimum.reduce(
        [pad[:-2, 1:-1], pad[2:, 1:-1], pad[1:-1, :-2], pad[1:-1, 2:]]
    )
    edge_pink = int(((a > 20) & (mag > 3) & (nmin < 30)).sum())
    corners = [
        int(a[0, 0]),
        int(a[0, -1]),
        int(a[-1, 0]),
        int(a[-1, -1]),
    ]
    return {
        "pink": pink,
        "edge_pink": edge_pink,
        "corners_a_sum": sum(corners),
    }


def process_file(inp: Path, out: Path, edge_contract: int = 2) -> dict[str, int]:
    im = Image.open(inp).convert("RGB")
    rgba = cutout(np.asarray(im), edge_contract=edge_contract)
    out.parent.mkdir(parents=True, exist_ok=True)
    Image.fromarray(rgba, "RGBA").save(out, optimize=True)
    m = metrics(rgba)
    m["w"] = rgba.shape[1]
    m["h"] = rgba.shape[0]
    return m


def main(argv: list[str] | None = None) -> int:
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument("--input", "-i", type=Path, required=True, help="Chroma-key RGB image")
    p.add_argument("--out", "-o", type=Path, required=True, help="Output RGBA PNG")
    p.add_argument(
        "--edge-contract",
        type=int,
        default=2,
        help="Alpha erode iterations (default 2)",
    )
    args = p.parse_args(argv)
    if not args.input.is_file():
        print(f"missing input: {args.input}", file=sys.stderr)
        return 2
    m = process_file(args.input, args.out, edge_contract=args.edge_contract)
    print(
        f"wrote {args.out} {m['w']}x{m['h']} "
        f"pink={m['pink']} edge_pink={m['edge_pink']} "
        f"corners_a_sum={m['corners_a_sum']}"
    )
    if m["corners_a_sum"] != 0 or m["edge_pink"] > 50:
        print("WARN: cutout QA thresholds not fully clean", file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
