# blueprint Shared Design System

Presets use this system unless a theme overrides it:

- `briefing` uses `theme-briefing.md` for colors and slide components, while retaining these typography and restraint rules.
- `slides` uses `theme-dify-x.md` for its canvas, colors, presentation type scale, radii, and layout vocabulary, while retaining these semantic and content-restraint rules.
- `archive` uses `theme-win98-web.md` for the full visual system.

Add shared tokens here only when multiple presets need them. Preset-only values belong in its theme or source CSS.

## Foundations

- Sans: `Inter, "Noto Sans SC", system-ui, sans-serif`
- Mono: `"JetBrains Mono", ui-monospace, "SF Mono", Menlo, monospace`
- Body: `16px`, line-height `1.5`
- Mono is reserved for code, versions, dates, metrics, and technical labels.

| Token | Value | Use |
|---|---|---|
| `bg` | `#ffffff` | Main surface |
| `bg-subtle` | `#fafafa` | Alternate section or canvas |
| `bg-muted` | `#f5f5f5` | Muted cards |
| `fg` | `#0a0a0a` | Primary text |
| `fg-muted` | `#525252` | Secondary text |
| `fg-subtle` | `#a3a3a3` | Captions |
| `border` | `#e7e7e7` | Default border |
| `border-strong` | `#d4d4d4` | Emphasized border |
| `accent` | `#2563eb` | Primary action or emphasis |
| `accent-soft` | `#dbeafe` | Accent surface |
| `accent-ultra` | `#eff6ff` | Light accent surface |
| `highlight` | `#fef08a` | One short inline highlight |

Multi-party comparisons may use four stable slots: teal `#0f766e`, orange `#c2410c`, blue `#2563eb`, and purple `#7c3aed`.

## Layout and type

- Section width: `1280px`; narrow reading width: `960px`.
- Default section padding: `110px 48px 72px`.
- Card radius: `6–8px`; reserve the shared lift shadow for one important surface.
- Headings use weight `700–900`.
- Negative letter spacing is for Latin display text, not Chinese.
- Chinese body copy needs more line height; keep `.mono` letter spacing neutral.
- Use at most one highlight per paragraph, section, or slide.

## Icons and motion

- Single-file output uses inline SVG. React output adds `lucide-react` only when icons are present.
- Icons use `currentColor`, 1.5px strokes, and an 18–20px default size.
- Prefer CSS transitions. Add `framer-motion` only for real orchestrated motion.
- Use restrained one-time entrance motion and honor reduced-motion preferences.

## Reuse

Use compiler tokens and existing `.mono`, `.highlight`, grid, canvas, and slide primitives before adding topic-specific CSS. The preset templates already define their Tailwind theme and background utilities; do not duplicate those implementations in generated source.

`briefing` slide classes belong to `theme-briefing.md`. Do not apply its slide chrome to `pitch`.

## Avoid

- radii of 16px or more
- gradients as the primary palette
- emoji used as icons
- multiple decorative font families
- heavy or stacked shadows
- default CTA or approval slides in `briefing`
- forcing the `pitch` marketing sequence onto `briefing`
