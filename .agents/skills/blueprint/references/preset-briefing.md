# Preset: briefing

Use this contract for internal explanations, alignment, responsibility boundaries, process clarification, research summaries, observations, and training. Let the compiler own the slide shell, theme, navigation, responsive behavior, validation, and preview.

## Source

```text
<project>/
  src/
    briefing.json
    slides.html
    style.css          # optional
    assets/            # optional local images
```

`briefing.json` requires `title`; `lang` is optional and defaults to `en`.

```json
{
  "title": "Document title",
  "lang": "en"
}
```

`slides.html` contains only slide sections:

```html
<section class="slide" id="stable-topic" data-rail-title="Short title">
  <div class="slide-tag">Section tag</div>
  <div class="slide-inner">...</div>
</section>
```

Include exactly one `.slide.cover`, at least three content slides, and `.slide-tag` plus `.slide-inner` on every slide. The compiler inserts page numbers and derives each deck rail label from the slide tag or heading. Omit `data-rail-title` unless that navigation label should differ. Use as many useful pages as the subject needs, and split a slide before its content crowds the viewport. `blueprint check` enforces a conservative static viewport content budget. The budget is a content-density heuristic, not rendered-layout proof.

The compiler assigns positional IDs such as `slide-01` when a slide has no `id`. Add a concise explicit ID when its shared URL must remain stable as slides are reordered. Generated briefings keep the current slide in the URL hash and open directly to a valid slide hash.

Use `src/style.css` only for topic-specific layout. Reuse the page types and component vocabulary in `theme-briefing.md`; do not copy theme CSS or runtime.

## Content rules

- Outline before writing markup; choose page types that fit the topic.
- Give every slide one repeatable claim and one visual job: responsibility, process, evidence, risk, or decision.
- Write claim-first headings instead of generic chapter labels.
- Alternate dense matrix, process, or evidence pages with lighter statements or dividers when the narrative allows it.
- Architecture and process visuals must express real ownership, data flow, or sequence.
- Put compact sources in `.source-note` when they support visible, volatile, or quantitative claims.
- Write complete statements, not Lorem Ipsum or TODO shells.
- Use at most one `.highlight` per slide.
- Use `.mono` for numbers, dates, versions, and codes.
- Use intentional line breaks for Chinese display headings.
- Keep wide tables usable on narrow screens.
- Keep local JPEG, PNG, SVG, WebP, GIF, and AVIF images under `src/`; the compiler inlines them from `<img>`, SVG `<image>`, and video `poster` attributes.
- Do not use local CSS URLs, `@import`, `srcset`, iframes, or local video sources.
- Do not add CTA, contact, or approval-request pages unless explicitly requested.

## Build

```bash
blueprint create briefing <project>
blueprint check <project>/index.html
blueprint preview <project>/index.html
```

Preview only the generated root `index.html`.
