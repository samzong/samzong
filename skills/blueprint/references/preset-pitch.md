# Preset: pitch

Use this contract for investor narratives, product introductions, launches, and compact public stories. Let the compiler own the shell, tokens, navigation, responsive behavior, validation, and preview.

## Source

```text
<project>/
  src/
    brand.svg         # optional local brand logo
    pitch.json
    sections.html
    style.css          # optional
```

`pitch.json` requires `title`, `brand`, `date`, and `footer`. `brandLogo`, `brandTagline`, `brandUrl`, and `lang` are optional; `lang` defaults to `en`. `brandLogo` must point to a JPEG, PNG, SVG, or WebP file inside `src/`; the compiler inlines it into the portable output.

```json
{
  "title": "Document title",
  "brand": "Brand",
  "brandLogo": "brand.svg",
  "brandTagline": "Short product category",
  "brandUrl": "https://example.com",
  "date": "YYYY-MM-DD",
  "footer": "Copyright or repository line",
  "lang": "en"
}
```

`sections.html` contains only section markup. Do not include document chrome, styles, scripts, navigation, or footer. Include `hero`, `solution`, and `cta` section IDs. Use as many real sections as the story needs; split a section before its heading, prose, and repeated components exceed one desktop viewport. `blueprint check` enforces a conservative static viewport content budget and tells the author to split likely-overflowing sections. The budget is a content-density heuristic, not rendered-layout proof.

Use `src/style.css` only for topic-specific layout. Reuse compiler classes and shared tokens; do not copy deck CSS or runtime.

## Reusable components

The pitch visual system provides opt-in presentation classes for technical product stories:

- `hero`, `hero-kicker`, `hero-sub`, `hero-facts`, and `hero-fact`
- `problem-grid`, `problem-stack`, `problem-row`, and `callout`
- `stack-wrap`, `stack`, `stack-card`, `principles`, and `principle`
- `loop`, `loop-step`, and `contract-line`
- `proof-layout`, `metrics`, `metric`, and `terminal`
- `starter-grid`, `starter-card`, `vision-lines`, `vision-line`, and `north-star`
- `source-note` for dated evidence and compact source links
- `gate-grid` for concise, non-clickable decision or readiness gates
- `cta`, `cta-copy`, `cta-actions`, `cta-btn`, and `cta-command`

Use these classes only when their semantic pattern fits. Keep product copy, brand assets, and one-off decoration in the project source.

## Content rules

- Lead each section with one repeatable claim, then evidence.
- Challenge outdated defaults, not the audience.
- For legacy or time-sensitive rebuilds, classify claims as current fact, dated fact, target, or hypothesis before writing.
- Keep unsupported or superseded numbers in a claim ledger or archive instead of presenting them as current facts.
- Use at most one `.highlight` per section.
- Use `.mono` for numbers, versions, and timestamps.
- Break Chinese display headings intentionally.
- Prefer inline SVG or data URIs for portable assets.
- Keep mobile layouts readable and controls at least 44px tall.

## Build

```bash
blueprint create pitch <project>
blueprint check <project>/index.html
blueprint preview <project>/index.html
```

Preview only the generated root `index.html`.
