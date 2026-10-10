# Preset: archive

Use this contract for a searchable, downloadable collection of Markdown documents.

## Source

```text
<project>/
  src/
    archive.json
    style.css          # optional
    docs/**/*.md
  index.html           # generated
  .blueprint.json      # managed
```

`archive.json` requires `title` and accepts:

- `lang`: valid language tag; defaults to `en`
- `downloadName`: ZIP filename; defaults to `<project>.zip`

The compiler recursively embeds `src/docs`, ignores hidden paths and `node_modules`, places a root `README.md` first, and derives labels from the first H1 or filename. The generated file includes the fixed `win98-web` Theme and compiler-owned renderer and runtime; it must not fetch source documents at runtime.
The archive chrome follows `lang`: Chinese projects use Chinese search, download, count, and empty-state labels; other languages use the English fallback.

## Runtime behavior

- Search filters titles and paths immediately.
- Hash routes preserve direct links and reloads.
- ZIP download preserves relative Markdown paths.
- Mermaid loads only when the active document contains a diagram.

## Build

```bash
blueprint create archive <project>
blueprint check <project>/index.html
```

## Content rules

- Use `README.md` as the landing document and one H1 per document.
- When current and historical documents coexist, use the root `README.md` to state the source hierarchy and make clear that dated material is not the current product contract.
- Preserve evidence labels, code fences, tables, quotes, and lists.
- Use fenced `mermaid` blocks only when a diagram improves the document.
- Put project-specific visual overrides in `src/style.css`.
- Edit Markdown sources, never the generated HTML or compiler CSS/runtime.
