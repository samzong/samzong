# Preset: dossier

Use this contract for technical diligence, competitor teardown, research reports, white papers, and maintained multi-section evidence dashboards.

```bash
blueprint create dossier <output>
```

The scaffold owns Vite, React, strict TypeScript, Tailwind CSS 4, pnpm, continuous and sectioned report layouts, responsive navigation, comparison surfaces, evidence cards, a native evidence dialog, and source filters. Fill:

- `src/data/content.ts` with verified data and prose
- `src/types.ts` with stable domain shapes
- `src/App.tsx` with presentation and real interaction
- `src/index.css` with topic-specific styles

Keep the generated output semantic and maintainable. Production bundles, copied minified application code, and iframe wrappers may be preserved as local reference evidence, but they are not an acceptable dossier implementation.

## Content rules

- Include at least three substantive sections.
- Separate fact, inference, and recommendation.
- Reuse vendor slots from `design-system.md` for multi-party comparisons.
- Lead with the decision, evidence date, audience, and current confidence.
- Give comparable subjects the same fields. Do not hide uneven evidence behind different card structures.
- Keep every strong claim adjacent to its evidence level, limitation, decision implication, and source references.
- Add icon or motion dependencies only when the interface uses them.
- Do not add state libraries, UI frameworks, CSS-in-JS, ESLint, Prettier, or Husky unless requested.

## Entity color strategy

Treat color as identity, not page decoration. Choose the color strategy from the completed information architecture:

- Use one report accent when top-level navigation represents chapters or analysis dimensions of one subject.
- Use entity-scoped colors only when top-level destinations represent parallel companies, products, people, or technical routes.
- Reuse the stable teal, orange, blue, and purple comparison slots from `design-system.md`. Keep each entity's slot consistent throughout the report.
- Apply entity color to a soft section surface, border, active navigation indicator, and small identity markers. Keep body text, cards, controls, spacing, and interaction behavior consistent.
- Apply the same entity mapping in both `continuous` and `sectioned` layouts.
- Do not assign different colors merely because pages are different. Do not let entity colors replace evidence-status colors or textual labels.
- If the content needs more distinct identities than the supported slots, keep one report accent unless an expanded palette has been explicitly designed and contrast-checked.

## Layout selection

Set `dossier.layout` while making the dossier:

- Use `continuous` when the report is a short, linear argument and readers benefit from moving through every section in sequence.
- Use `sectioned` when the total report is long, when readers commonly enter one top-level section directly, or when any section contains a substantial collection.

In `sectioned` mode, every top-level navigation item is an independent page state. Mount only the active section, keep its hash in the URL, and preserve browser back, forward, refresh, and deep linking. Do not special-case papers: the same rule applies to long source, evidence, people, or comparison sections.

Choose the layout from the completed content before handoff. Do not switch layouts automatically at runtime.

## Hierarchical navigation

Second-level navigation is opt-in, not a default. Use it only when a top-level section contains at least two substantial destinations that each justify navigation:

- In `continuous` mode, primary items jump to major sections and secondary items jump to anchors inside them.
- In `sectioned` mode, primary items select independent pages and secondary items jump within the active page.
- Keep both levels in the URL hash so refresh, deep linking, back, and forward preserve context.
- Open desktop submenus on hover and keyboard focus. On narrow screens, show the active page's secondary items as a visible horizontal row; never make them hover-only.
- A destination should own a substantial content block, normally around a viewport or more, so selecting it produces a clear location change.
- Do not promote summaries, metrics, filters, adjacent headings, or ordinary card groups into secondary navigation.
- Do not create a menu item for every paper or source record in a large collection.
- Omit the submenu when its destinations are already visible together or the page reads comfortably without it.

## Research library pattern

Use this only when the dossier includes a maintained paper, source, or evidence corpus:

- Give every externally shared record one canonical public source URL. Prefer an abstract or publisher landing page over a PDF; never expose machine-local files or invent a link.
- Use native search and select controls for the filters the corpus actually needs. Category, evidence status, and sort order are enough for most collections.
- Keep deep-read evidence separate from metadata-only records. Evidence cards should state the finding, limitation, and decision implication.
- Add a reading route only when it explains how the evidence supports a decision or operating loop.
- Put collection controls before long highlights or result lists. Paginate a collection when rendering it in full would dominate the page.
- On narrow screens, stack controls and cards; keep all controls keyboard reachable with visible focus.

## Existing page rebuild

When rebuilding from a live URL, screenshot, recovered artifact, or legacy output:

1. Use `browser-cdp` to capture desktop and mobile structure plus every meaningful interaction state.
2. Inventory the content hierarchy, comparison axes, evidence records, source links, and visual assets.
3. Treat recovered HTML, CSS, bundles, and screenshots as reference inputs only.
4. Rebuild the report from typed semantic data and maintainable React components.
5. Put required media under `public/` with stable local paths. Keep canonical public URLs on source records.
6. Preserve the original artifact separately unless the user explicitly requests replacement.

## Acceptance

Before a requested preview, visual review, or deployment handoff:

1. Run `blueprint check <project>`.
2. Run `pnpm build`.
3. Preview through Blueprint or the project Vite server.
4. Use `browser-cdp` at desktop and mobile widths to verify the full content surface, navigation, filters, dialogs, local assets, and console state.
5. Confirm there are no unresolved starter records, broken images, unexpected remote runtime assets, or missing source links.
6. For a visual rebuild, compare matching viewport and interaction-state screenshots. `blueprint check` alone does not prove fidelity.
