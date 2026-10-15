# Preset: prototype

Use this contract for clickable concepts, interaction models, mode switching, and short-lived demos.

- `prototype-lite`: one page, at most three core interaction states, short lifetime.
- `prototype-full`: multiple views, sustained iteration, or expected growth.

## prototype-lite

```bash
blueprint create prototype-lite <output>
```

Edit `<output>/index.html`. Keep local React state and the existing scaffold; do not add a build chain, state library, or UI framework.

Content must provide:

- 2–3 distinct interaction or result modes, not navigation tabs
- a label, explanation, input, realistic examples, and distinct result for each mode
- working prompt buttons and form submission
- layouts suited to each result instead of one repeated card
- controls at least 44px tall and usable narrow-screen wrapping

Move to `prototype-full` when the file approaches 600 lines or needs routing.

## prototype-full

```bash
blueprint create prototype-full <output>
```

Fill `src/data/content.ts`, `src/types.ts`, `src/App.tsx`, and `src/index.css`. The scaffold owns Vite, React, strict TypeScript, Tailwind CSS 4, and pnpm. Keep state local and add routing only for real multiple pages.
