# Theme: Dify-X

Use this theme for Reveal.js slides that need a technical, editorial, Dify-inspired presentation language: cobalt blue, paper and ink surfaces, precise grids, strong thesis typography, restrained glass panels, atmospheric media, and clear system diagrams.

The theme is a reusable visual system, not a copy of one Dify-X deck. Do not bake in company logos, partner colors, presenter details, photographs, Tailwind utilities, icon CDNs, language controls, or deck-specific scripts. The compiler renders optional brand and language chrome from `slides.json`; this theme only styles it.

## Visual language

- Dify Blue `#0033ff` for emphasis, progress, active states, and structural rules
- paper-gray canvas with a subtle 48px grid and diffused blue fields
- Inter and Noto Sans SC for display and body text
- JetBrains Mono for labels, versions, metrics, sources, and compact metadata
- language-aware tracking and line height for Chinese and Latin text
- 1920×1080 design canvas with left-aligned editorial composition
- small and medium radii, light borders, restrained shadows
- positive, caution, and danger status colors for real semantics
- one dominant thesis or visual hierarchy per slide

Use dark slides only for a deliberate chapter break, technical boundary, architecture contrast, or closing emphasis. Do not alternate light and dark surfaces decoratively.

## Optional deck chrome

When `slides.json` provides brand metadata or multiple locales, the compiler renders `.slides-chrome`, `.deck-brand`, `.deck-brand-logos`, `.deck-brand-label`, and `.slides-locales`. Do not author them in semantic slide sources.

The theme keeps the chrome fixed to the viewport, preserves logo color on dark slides, changes text contrast with the active `.dark` slide, and reduces chrome emphasis on `.credits` slides. If the metadata is absent, the chrome does not exist.

## Slide foundations

Place content inside `.slide-shell`. Use `.slide-header` for content pages and `.eyebrow` for the compact section label.

- `.slide-shell`
- `.slide-header`
- `.eyebrow`
- `.lede`
- `.kicker`
- `.tag` and `.chip`
- `.emphasis`
- `.mono`
- `.source-note`

## Layout vocabulary

Choose the smallest layout that communicates the claim:

- Cover: `.cover-layout`, `.cover-copy`, `.cover-meta`, `.cover-visual`
- Chapter divider: `.section-intro`, `.section-number`, `.section-copy`
- Thesis: `.statement`, `.statement-rule`
- Comparison or text-media split: `.split`, optionally `.wide-left` or `.wide-right`
- Framed content: `.panel`
- Cards: `.card-grid`, `.cols-2`, `.cols-3`, `.cols-4`, `.card`, `.card-index`
- Metrics: `.metric-grid`, `.metric`, `.metric-value`, `.metric-label`, `.metric-detail`
- Evidence: `.evidence-layout`, `.evidence-stack`, `.evidence-verdict`, `.source-note`
- Structured comparison: `.matrix`, optionally status rows
- Process: `.flow`, `.flow-step`, `.step-number`, `.flow-arrow`
- Architecture: `.architecture`, `.architecture-node`, `.primary`, `.span-3`, `.span-4`, `.span-6`, `.span-8`, `.span-12`
- Timeline: `.timeline`, `.timeline-item`, `.timeline-time`
- Quote: `.quote-layout`, `.quote-mark`, `.quote`, `.quote-source`
- Image: `.image-stage`, `.caption`; pair with `.split.wide-left` or `.wide-right`
- Atmospheric background: `.atmospheric` on a section with `data-background-image`
- Status: `.status-positive`, `.status-caution`, `.status-danger`
- Closing: `.closing`, `.closing-mark`
- Attribution: `.credits`, `.credits-list`

Add `dark` to a section for the supported dark surface. Theme components and optional chrome adapt automatically.

## Composition and rhythm

- Cover: one title, one short lede, compact metadata, and one visual field.
- Content page: eyebrow, claim-first heading, then the selected layout.
- On image-led slides, let the image occupy roughly 35–45% and information 55–65%.
- Alternate dense system, matrix, or evidence pages with lighter image, statement, quote, or chapter pages when the narrative allows it.
- Avoid repeating the same layout for more than two consecutive slides.
- Card and metric grids must use equal semantic weight; do not put prose of radically different lengths into symmetric cells.
- Architecture nodes describe ownership or data flow, not decorative boxes.
- Process arrows need an actual sequence.
- Use a real image stage only when the image carries evidence or atmosphere.
- Keep code below roughly 20 visible lines; extract the important region.
- Avoid more than four columns.
- Avoid nested cards, oversized pill collections, emoji icons, and generic stock dashboards.
- Put compact sources on the slide when they support a visible claim; keep longer caveats in speaker notes.
- Credit external visual assets on a `.credits` slide.

## Topic-specific CSS

Use `src/style.css` for one-off grid spans, connectors, image crops, Trust Center views, security boundaries, protocol maps, or upgrade boards. It must not redefine core colors, typography, deck chrome, Reveal controls, progress, slide numbering, runtime behavior, or the layout vocabulary above.

Promote a topic-specific layout into the theme only after it recurs across independent decks.
