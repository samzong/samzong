# Preset: slides

Use this contract for stage presentations, conference talks, speaker decks, PPT-like delivery, and any request that explicitly names Reveal.js. Reveal.js owns presentation state; the compiler owns its wrapper, runtime, optional deck chrome, responsive scaling, validation, and portable output.

## Source

```text
<project>/
  src/
    slides.json
    slides.html             # default single-language source
    locales/                # optional locale sources named by slides.json
      en.html
      zh-CN.html
    style.css               # optional topic-specific layout
    assets/                 # optional local images and logos
```

`slides.json` requires `title` and `theme`; `lang` is optional and defaults to `en`. The only supported theme is `dify-x`.

```json
{
  "title": "Presentation title",
  "lang": "zh-CN",
  "theme": "dify-x"
}
```

### Optional brand and languages

Add `brand` only when real organization, product, partner, or event assets are available. Brand logos must be local images under `src/`; the compiler inlines them. Omit `brand` to omit the persistent header.

Add `locales` only for a real multilingual deck. Every locale needs a label, language tag, and semantic source. Locale titles are optional and fall back to the top-level title. The default `lang` must be present, and every locale source must have the same horizontal and vertical slide topology. The compiler bundles every locale into one `index.html`; one locale does not render a switch.

```json
{
  "title": "Enterprise Agent",
  "lang": "zh-CN",
  "theme": "dify-x",
  "brand": {
    "label": "Governance × Operations",
    "logos": [
      { "src": "assets/dify.svg", "alt": "Dify" }
    ]
  },
  "locales": [
    { "lang": "zh-CN", "label": "ZH", "source": "locales/zh-CN.html", "title": "Enterprise Agent" },
    { "lang": "en", "label": "EN", "source": "locales/en.html", "title": "Enterprise Agent" }
  ]
}
```

Write each language for its audience instead of translating line by line. Keep the same claims, evidence, slide order, and terminology across locale sources.

## Semantic slides

Every locale source contains only top-level `<section>` elements. Do not include `.reveal`, `.slides`, deck chrome, language controls, styles, scripts, navigation, or runtime.

Use flat top-level sections by default. A top-level section may contain only nested sections when a real vertical chapter is needed:

```html
<section>
  <div class="slide-shell">...</div>
  <aside class="notes">Speaker notes.</aside>
</section>

<section>
  <section>Vertical slide one</section>
  <section>Vertical slide two</section>
</section>
```

Use `.fragment` only when staged disclosure improves the explanation. Put speaker notes in `<aside class="notes">`; the bundled Reveal Notes plugin exposes them with the `S` shortcut. `F` enters or exits fullscreen, `Esc` opens overview, and `?` shows the complete shortcut reference. The compiled runtime displays these shortcuts; do not recreate the hint in slide content.

Local JPEG, PNG, SVG, WebP, GIF, and AVIF images referenced by `<img>`, `poster`, SVG `<image>`, or `data-background-image` are inlined during compilation. Keep them under `src/`. Local URLs in links, video, iframes, `srcset`, inline styles, or `style.css` are rejected because the generated and deployed artifact contains only one `index.html`. CSS escape sequences are rejected so URL validation cannot be obscured.

Do not use Reveal's ambiguous `data-background` shortcut. Use `data-background-color`, `data-background-gradient`, or `data-background-image`; gradient values must remain self-contained CSS.

Use `src/style.css` only for topic-specific geometry, connectors, image crops, or layouts that do not recur across decks. Reuse the selected theme vocabulary first.

## Content rules

- Outline the narrative before writing markup.
- Give every slide one repeatable claim and one visual job.
- Let the talk length and narrative determine the slide count; split a slide before its content crowds the viewport. `blueprint check` enforces a conservative static viewport content budget. The budget is a content-density heuristic, not rendered-layout proof.
- Keep body copy readable from a room; move supporting detail into speaker notes.
- Prefer diagrams, comparisons, metrics, product evidence, and real visual assets over bullet walls.
- Alternate dense technical pages with lighter evidence, image, statement, or chapter pages when the material supports it.
- Use local optimized images only when they carry evidence or atmosphere; include useful alt text.
- Put volatile claims, release facts, security claims, and quantitative evidence in a compact `.source-note` and keep caveats in notes.
- Add a `.credits` slide when external visual assets require attribution.
- Use vertical stacks only for optional depth inside one chapter.
- Use fragments sparingly and never to hide required context.
- Write complete speaker notes for timed or externally presented decks.
- Check every claim that may have changed before presenting it as current.

## Build

```bash
blueprint create slides <project>
blueprint check <project>/index.html
blueprint preview <project>/index.html
```

Preview only the generated root `index.html`. Verify arrow navigation, `F` fullscreen toggling, overview, fragments, speaker view, every configured language, brand contrast on dark slides, images, and `?print-pdf` before delivery.
