# Preset: architecture

Use this contract for system boundaries, runtime topology, data flow, protocol flow, component ownership, and concept explainers. The Agent owns research, message, composition, typography, color, paths, and every SVG primitive. Blueprint owns only the review shell, source validation, preview, and deterministic export.

## Source

```text
<project>/
  src/
    diagram.svg
```

`diagram.svg` is the complete editable drawing. Do not replace it with Mermaid, a node list, coordinates in JSON, or a generated card grid. Author the SVG directly after inspecting the actual project.

The root must provide:

- `xmlns="http://www.w3.org/2000/svg"`
- `data-blueprint-diagram="true"`
- a `viewBox` with positive integer pixel dimensions as the only root dimension; omit root `width` and `height`
- one non-empty `<title>` and `<desc>`

Use unique IDs. Keep all fonts, styles, markers, filters, patterns, and vector artwork inline. Raster imagery may use `data:image/...`; external URLs, scripts, event handlers, nested SVGs, and `foreignObject` are rejected.

## Build and review

```bash
blueprint create architecture <project>
blueprint check <project>
blueprint preview <project>
```

`create` wraps the exact source SVG in a neutral review page. It does not restyle or lay out the diagram. Change `src/diagram.svg`, rebuild, and inspect the rendered result until hierarchy, spacing, connector routes, exact copy, and edge crops survive at the intended size.

Do not ask the user to provide nodes, coordinates, colors, or a Theme. Infer them from the repository and the requested message. Ask one question only when the intended audience or architecture altitude would materially change the diagram.

## Export and reuse

```bash
blueprint export <project> --format svg
blueprint export <project> --format png
```

SVG export preserves the canonical drawing. PNG export renders that same SVG. When a diagram belongs in another Blueprint Artifact, review it as an `architecture` Artifact first, export SVG, then embed the approved result. Keep `src/diagram.svg` as the editable owner.
