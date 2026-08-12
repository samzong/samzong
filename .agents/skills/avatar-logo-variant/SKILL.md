---
name: avatar-logo-variant
description: >
  Generate identity-preserving 3D cartoon profile-avatar variants with a platform
  chest badge (GitHub, X, Slack, Telegram, WeChat, OpenAI, company marks, or any
  new logo). Use when the user asks for a new logo avatar, platform avatar,
  badge variant, 「做一个 XX logo 头像」, 「新平台头像」, or runs
  /avatar-logo-variant. Owns image_edit generation + local chroma cutout into
  logos/avatar-*.png.
---

# Avatar logo variant

Produce one (or more) **1024×1024 RGBA** avatar(s) that keep the same person as the
base avatar, with a single platform chest pin, transparent background, and badge
size matched to the Telegram reference.

## Paths (repo-relative)

| Item | Path |
|---|---|
| Skill root | `.agents/skills/avatar-logo-variant/` |
| Base identity (do not overwrite) | `.agents/skills/avatar-logo-variant/assets/base-avatar.png` |
| Badge size standard | `.agents/skills/avatar-logo-variant/assets/size-reference-telegram.png` |
| Prompt templates | `.agents/skills/avatar-logo-variant/references/prompt-templates.md` |
| Cutout script | `.agents/skills/avatar-logo-variant/scripts/cutout.py` |
| QA preview script | `.agents/skills/avatar-logo-variant/scripts/qa_preview.py` |
| Default output | `logos/avatar-<slug>.png` |
| Scratch (chroma / previews) | `.local/imagegen/avatar-logo/` |

`<slug>` = lowercase platform id: `github`, `x`, `slack`, `telegram`, `weixin`,
`openai`, `if`, `discord`, …

## When the user says

Examples that must trigger this skill:

- `/avatar-logo-variant discord`
- 「给我做一个 Discord logo 的头像」
- 「新加一个 LinkedIn 胸章版」
- 「缩小 OpenAI 徽章到和 Telegram 一样」

If only a name is given, assume: **green shirt + earphone cord + official mark chest pin**, size = Telegram.

## Workflow (do every time)

### 0. Setup

```bash
mkdir -p .local/imagegen/avatar-logo logos
```

Python for cutout (prefer uv ephemeral deps):

```bash
uv run --with numpy --with pillow \
  python .agents/skills/avatar-logo-variant/scripts/cutout.py --help
```

If `uv` is unavailable, use the repo-local venv if present:
`.local/venv-img/bin/python`.

### 1. Generate chroma source (image_edit)

1. Read prompt templates from `references/prompt-templates.md`.
2. Call built-in **`image_edit`** (not pure text-to-image without the base):
   - Image 1: `assets/base-avatar.png` (identity)
   - Image 2: `assets/size-reference-telegram.png` (badge size only)
   - Optional Image 3: official logo file if the user provided one
3. Prompt must require:
   - identity lock (face/hair/glasses/pose/materials)
   - **one** chest pin for the requested brand
   - badge diameter matched to Image 2 (~6–8% width)
   - badge lower-right chest, **inside max inscribed circle**
   - flat solid **`#ff00ff`** background (no shadows on BG)
4. Save/copy the tool output to:
   `.local/imagegen/avatar-logo/<slug>-chroma.jpg` (or `.png`)

**Reject and re-edit if:**

- face drifts from base
- badge is medallion-sized vs Telegram
- badge sits on shoulder/neck or would clip under circular crop
- second badge appears
- background is not flat key color

### 2. Size / style fix loops (image_edit only)

- Too big / too small → “badge size only” template vs Telegram reference
- Color drift (e.g. OpenAI turned blue) → “fix badge color only” template
- Missing earphone cord on green-shirt variants → re-add cord from base; do not enlarge badge

### 3. Cutout to transparent PNG

```bash
uv run --with numpy --with pillow \
  python .agents/skills/avatar-logo-variant/scripts/cutout.py \
    --input .local/imagegen/avatar-logo/<slug>-chroma.jpg \
    --out logos/avatar-<slug>.png
```

Do **not** hand-roll a new chroma script. All fringe/lens logic lives in `cutout.py`.

Expect script stdout with `pink=0`, `edge_pink` low, `corners_a_sum=0`. If exit code 1, re-check chroma quality or re-run once with `--edge-contract 3`.

### 4. Visual QA (required before claiming done)

```bash
uv run --with pillow \
  python .agents/skills/avatar-logo-variant/scripts/qa_preview.py \
    --input logos/avatar-<slug>.png \
    --out-dir .local/imagegen/avatar-logo
```

Then **view** with the image tool:

1. Full avatar on light bg — no pink/red rim on hair/shoulders
2. Lens crop — no magenta fill, no green blob over nose, eyes/lenses look natural
3. Mentally circle-crop — badge still fully visible

### 5. Deliver

- Report path: `logos/avatar-<slug>.png`
- Do not overwrite `assets/base-avatar.png`
- Do not delete other `logos/avatar-*.png` unless user asks
- Keep intermediate chroma under `.local/` (gitignored scratch)

## Defaults and product rules

| Decision | Default |
|---|---|
| Canvas | 1024×1024 |
| Identity | `assets/base-avatar.png` only |
| Badge size reference | Telegram asset above |
| Shirt | olive green + brown earphone cord |
| Company / “if” style | may use navy shirt and drop cord **only if user asks or matches existing `avatar-if`** |
| Output name | `logos/avatar-<slug>.png` |
| Background in generation | `#ff00ff` flat chroma |
| Transparency | always via `cutout.py` |

## Batch

For multiple platforms: one `image_edit` per slug (parallel OK), then one `cutout.py` per chroma file. Do not share one prompt for different logos.

## Out of scope

- Replacing the base identity with a new character (needs explicit new base asset)
- Vector logo design systems
- Committing / pushing (needs separate user authorization)
