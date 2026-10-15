---
name: blueprint
description: >
  Create, upgrade, rebuild, validate, preview, discover, export, and deploy blueprint-managed
  Artifacts using html, architecture, pitch, briefing, slides, archive, prototype, or dossier presets.
  Use when the user mentions blueprint, asks to create a page, demo, deck,
  report, architecture diagram, or Markdown archive, or wants to upgrade, check, preview, export, list, or
  publish an existing blueprint project. Do not use for unrelated websites or
  non-architecture image outputs.
---

**Reply language**: use Chinese with the user. Use English for code, comments, filenames, and Git text.

# blueprint

Use the `blueprint` CLI for deterministic scaffolding, compilation, validation, preview, discovery, and deployment. Handle intent, content, and visual judgment in the Skill.

When present, use the repository `CONTEXT.md` as the canonical terminology source. A Preset selects an Artifact contract, a Theme is reusable visual language within that contract, and CSS is an implementation mechanism. When a user informally says "CSS", "theme", "skin", "look", or "style", treat it as a visual direction unless they explicitly request stylesheet work or name a supported Theme.

## Route the request

- For a new project or content rebuild, follow **Create or rebuild**.
- For an existing project that should adopt current preset capabilities, follow **Upgrade an Artifact**.
- For validation, preview, or discovery, follow **Operate a project**.
- For publication, follow **Deploy**.
- Do not collect topic or preset inputs for an existing-project operation.

## Create or rebuild

### Collect inputs

Ask at most one blocking question and only for missing information that changes the output:

1. **Topic**: what the page must communicate.
2. **Output directory**: default demos, examples, and scratch work to `.local/<slug>` in the current repository; ask only for standalone-project locations.
3. **Preset**: infer it when exactly one row matches.

| Intent | Preset |
|---|---|
| Standalone HTML dashboard, explainer, report, or plain-JavaScript decision tool | `html` |
| Architecture diagram, system boundary, runtime topology, data flow, concept explainer | `architecture` |
| Investor pitch, product introduction, landing page | `pitch` |
| Stage presentation, conference talk, speaker deck, PPT | `slides` |
| Clickable concept, interaction demo, state switching | `prototype` |
| Research, comparison, diligence, white paper | `dossier` |
| Responsibility, process, governance, training, internal alignment | `briefing` |
| Markdown library, knowledge base, searchable document set | `archive` |

Route ordinary agent-authored standalone HTML to `html`. Choose content, layout, CSS, and optional JavaScript independently. Do not load design-system or Theme references for `html`. Use another themed workflow when explicitly selected; preserve the existing Preset for managed Artifacts.

Ask for the primary audience or delivery form only when multiple rows or none match.

For an architecture diagram, use the `architecture` Preset even when the user asks only to “draw a diagram.” Do not ask for nodes, coordinates, colors, or a style selector. Inspect the project, choose the message and composition, and directly author the complete SVG. When a diagram belongs inside another Blueprint Artifact, build and review it as an `architecture` Artifact first, export SVG, then embed the approved SVG in the destination Preset.

An explicit request for slides, PPT, Reveal.js, speaker notes, or stage delivery selects `slides` even when the subject could also fit `pitch` or `briefing`. Choose `prototype-lite` for one page with at most three core interaction states. Choose `prototype-full` for multiple views or sustained iteration. Default to `prototype-lite`. Use the `dify-x` Theme for `slides`; do not ask the user to choose a Theme while it is the only supported slides Theme. `briefing` and `archive` use fixed Themes, so do not ask for a Theme choice.

For `slides`, inspect the supplied material for real organization, product, partner, event, and language requirements before writing. Configure optional brand chrome only from verified local assets. Configure multiple locales only when requested or supported by source material, keep their slide topology aligned, and write each language for its audience instead of translating line by line. Never invent logos, partners, presenters, translations, citations, or image credits.

For an existing managed project, preserve its preset, project ID, and deployment metadata. For a new project, stop before writing when the output directory is non-empty.

### Rebuild dated material

When rebuilding a legacy page or time-sensitive product story:

1. Compare volatile claims with current code, runtime, accepted contracts, and authoritative sources before writing.
2. Classify each claim as current fact, dated fact, target, or hypothesis.
3. Keep only verified current facts in the main story. Label dated facts with their evidence date, and move unsupported numbers or superseded claims into an archive or `.local` claim ledger.
4. Preserve the legacy artifact as historical evidence unless the user explicitly requests deletion.

`blueprint check` proves structure, not factual freshness or visual equivalence.

### Load only the selected references

| Preset | References |
|---|---|
| `html` | None |
| `architecture` | [diagram direction](references/architecture-diagrams.md), [architecture contract](references/preset-architecture.md) |
| `pitch` | [design system](references/design-system.md), [pitch contract](references/preset-pitch.md) |
| `briefing` | [design system](references/design-system.md), [briefing theme](references/theme-briefing.md), [briefing contract](references/preset-briefing.md) |
| `slides` | [design system](references/design-system.md), [Dify-X theme](references/theme-dify-x.md), [slides contract](references/preset-slides.md) |
| `archive` | [win98-web theme](references/theme-win98-web.md), [archive contract](references/preset-archive.md) |
| `prototype-lite`, `prototype-full` | [design system](references/design-system.md), [prototype contract](references/preset-prototype.md) |
| `dossier` | [design system](references/design-system.md), [dossier contract](references/preset-dossier.md) |

### Generate

1. Run `blueprint --version`. Stop and request installation when unavailable; do not copy an old template as fallback.
2. Write content according to the selected references. For `architecture`, trace the live system and directly draw the full `src/diagram.svg`; the CLI must not decide its layout or visual language.
3. For `architecture`, `pitch`, `briefing`, `slides`, or `archive`, write only sources under `src/`, then run:

   ```bash
   blueprint create <preset> <output>
   blueprint check <output>/index.html
   ```

4. For `html`, run `blueprint create html <output>` first, then directly author `<output>/index.html` and run `blueprint check <output>`. Keep the stable directory and CLI-owned manifest. Author local images, CSS, JavaScript, and data in any layout under the Artifact directory. No framework bootstrap is required. Keep private working notes under `.local/` or outside the Artifact; dotfiles and hidden directories are not published, and symbolic links are rejected. Repeating create checks and preserves existing HTML.
5. For `prototype-lite`, `prototype-full`, or `dossier`, run `blueprint create <preset> <output>` before filling topic-specific content.
6. For `architecture`, render and inspect the PNG before returning the review path. For other Presets, return the output path and the appropriate preview command. Do not install dependencies or start a server unless the user requested preview or deployment.

Let `blueprint create` own the `.blueprint.json` schema and initial manifest. Never create, copy, delete, add, remove, or rename manifest fields. During a verified upgrade, the Agent may update only the existing `createdWith` value.

## Upgrade an Artifact

Treat an upgrade as a preservation-first semantic merge, not regeneration.

1. Run `blueprint list --json` and `blueprint --version`. Use the discovered `preset` to select the current references. Treat the discovered `createdWith` as the single version marker for the latest Blueprint preset contract successfully applied to the Artifact.
2. Inspect the current sources, output, and Git diff or history when available before writing. Treat content, branding, customized themes, custom CSS, and layout as user-owned even when they began as preset defaults.
3. For `html`, preserve the complete entry, CSS, and JavaScript. Apply only required delivery-contract corrections in place; never inject a Theme, design system, chrome, or framework. If the existing content conflicts with the current HTML delivery contract, report the concrete conflict instead of overwriting it.
4. Compare the Artifact with the current preset references. Apply missing Blueprint-owned runtime, compiler chrome, validation, accessibility, and required structural improvements with the smallest patch. Do not retrofit new default styling unless the user asks for it.
5. Preserve user-owned changes. When a required Blueprint change overlaps them, merge around the customization when safe; otherwise stop and report the conflict instead of overwriting it.
6. Do not copy a fresh preset over the project or begin by rerunning `blueprint create`. For compiled presets, regenerate compiler-owned output only after preserving any output-only customization in semantic sources. For scaffold presets, patch the existing source in place.
7. Run `blueprint check <target>`, visually verify the exact upgraded behavior, and inspect the final diff for lost content, branding, styles, or layout.
8. Only after the upgrade and verification succeed, update the existing `.blueprint.json.createdWith` value to the exact current Blueprint version while preserving every other manifest field. For `html`, successfully checking the unchanged entry against the current delivery contract also qualifies as a verified contract upgrade. `createdWith` records the last verified Blueprint contract version, not content history or rollback support. If no preset change was applied to another Preset or verification fails, leave it unchanged.

## Operate a project

- Validate: `blueprint check <target>`
- Discover from the current directory: `blueprint list`
- Discover under another root: `blueprint list --root <path>`
- Request machine-readable discovery output: append `--json`
- Preview: `blueprint preview <target>`; for `prototype-full` or `dossier`, run `pnpm install` first when dependencies are absent.
- Export an architecture SVG: `blueprint export <target> --format svg`
- Export an architecture PNG: `blueprint export <target> --format png`

Use paths returned by discovery; do not store absolute paths in `.blueprint.json`. Treat `deployed` as a record of a previously verified publish, not proof that the remote still exists.

## Deploy

Deploy only after the user has reviewed the preview and explicitly requested publication:

- Single-file output: `blueprint deploy <output>/index.html --name <worker-name>`
- Select among managed projects without a path: `blueprint deploy --project <project-name>`
- `prototype-full` or `dossier`: run `pnpm install && pnpm build`, then deploy `<output>/dist`
- Password-protect the published Worker: append `--protect`. The CLI gates the site behind HTTP basic auth with generated `viewer` credentials, prints them, and records them together with `protected: true` in `.blueprint.json`; protected redeploys reuse the recorded credentials. Treat `.blueprint.json` as sensitive for protected projects.

Redeploying without `--protect` publishes openly and removes that protection and the recorded credentials.

`--name` is only the Worker name. Do not use it to pick a managed project.

Derive `worker-name` without asking:

- Inside a Git repository: `<repo-name>-<task-name>`
- Outside a Git repository: `<task-name>`

Use the nearest Git root directory for `repo-name` and a stable task slug for `task-name`. Normalize to lowercase hyphen-case and keep the name within 63 characters. Honor an explicit user-provided name.

Omit `--account` by default. Let the CLI resolve the recorded account, `CLOUDFLARE_ACCOUNT_ID`, or the only available account. Ask only when no unique account can be resolved. Return the verified published URL.

## Boundaries

- Do not run `git init`, install dependencies, or start a server unless required by the requested operation.
- Do not add unrequested documentation, linters, formatters, hooks, state libraries, or UI frameworks.
- Do not write narration comments.
- Preview only the compiled root `index.html` for `architecture`, `pitch`, `briefing`, `slides`, and `archive`.
- Do not recreate compiler-owned navigation, progress, responsive behavior, deck chrome, language controls, or runtime in semantic sources. Architecture SVG sources own their drawing styles.
- Do not add CTA, contact, or approval slides to `briefing` unless explicitly requested.
