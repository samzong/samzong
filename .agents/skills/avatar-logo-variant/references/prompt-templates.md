# Prompt templates (image_edit)

Use these with the built-in `image_edit` tool. Image paths are relative to the skill root unless noted.

## Assets

| Role | Path |
|---|---|
| Identity source (authoritative) | `assets/base-avatar.png` |
| Badge size standard | `assets/size-reference-telegram.png` (or repo `logos/avatar-telegram.png`) |
| Optional style ref | existing `logos/avatar-*.png` or user-provided logo |

## New platform variant (generate chroma source)

```text
Identity-preserving edit of Image 1 (authoritative character).
Same exact 3D cartoon person: face, glasses, brown hair, expression, three-quarter pose looking left, soft clay Pixar/Memoji materials, studio lighting.
Keep the olive-green t-shirt and brown earphone cord (unless the platform variant intentionally changes clothing).
Add only one change: a circular pin badge on the lower-right chest for <PLATFORM>, using the official <LOGO DESCRIPTION>.
Badge size must match Image 2 (Telegram size reference): medium-small discreet chest pin, about 6–8% of image width — not a large medallion.
Badge center near ~62% width, ~78% height, fully on the shirt fabric, fully inside the max inscribed circle so circular crop keeps the whole badge.
Place the character on a perfectly flat solid #ff00ff magenta chroma-key background, uniform color, no shadows/gradients on the background, subject cleanly separated.
No text beyond the logo mark, no watermark, no extra objects, no second badge.
```

Images: `[assets/base-avatar.png, assets/size-reference-telegram.png]`  
Optional third image: official logo mark if available.

## Shrink / enlarge badge only

```text
Precise identity-preserving edit of Image 1 only.
Keep the exact same face, glasses, hair, pose, clothing, badge design, and composition.
Image 2 is ONLY a size reference for the badge.
<Shrink|Enlarge> the circular pin badge so its diameter clearly matches the Telegram pin on Image 2.
Keep one badge only on the lower-right chest, fully on the shirt, fully inside the max inscribed circle.
Place the character on a perfectly flat solid #ff00ff magenta chroma-key background.
Do not change colors of the badge design. Do not add a second badge.
```

## Fix badge color (after size edit drifted)

```text
Precise identity-preserving edit of Image 1.
Keep everything identical: face, pose, clothing, badge size and placement, magenta background.
Only fix the badge style/colors to match the official <PLATFORM> mark: <COLOR/STYLE DESCRIPTION>.
Do not enlarge or shrink the badge.
```

## Clothing / company theme (optional)

```text
...same identity block...
Change clothing only if requested: e.g. solid dark navy crew-neck and remove earphone cord for company brand.
Badge: <company mark description>, size-matched to Image 2.
Magenta #ff00ff flat background as above.
```

## Hard constraints (always)

1. Base identity from `assets/base-avatar.png` only — do not invent a new face.
2. Final deliverable is RGBA PNG via `scripts/cutout.py`, never leave chroma magenta.
3. Do not overwrite `assets/base-avatar.png`.
4. Default output path: repo `logos/avatar-<slug>.png`.
5. Circle-crop safety: badge must remain fully visible after max inscribed circle crop.
6. No oversized lens ROI post-processing outside `scripts/cutout.py`.
