# Architecture diagram direction

The user should be able to say “draw an architecture diagram” and receive a composed diagram, not a schema to fill in. Inspect the live repository, determine the one message the diagram must make obvious, and directly author the complete `src/diagram.svg`.

## Start from system truth

Trace the actual entrypoints, runtime flow, storage, public surfaces, external dependencies, and ownership boundaries. Use current code and accepted architecture documents; ordinary README prose is supporting evidence. Choose one altitude and omit facts that do not help its message.

Write a conclusion-led title. Keep paths, commands, protocols, versions, and ownership labels exact. An arrow must mean data flow, invocation, dependency, or ownership transition; remove decorative connectors.

## Shared visual DNA

Recall and rx are visual anchors, not rigid templates. Preserve these shared traits:

- One clear thesis, visible before any component detail.
- Large canvas, disciplined whitespace, and a deliberate reading direction.
- Strong sans headings or an intentional hand-drawn voice; monospace only for code facts.
- Thin outlines, restrained rounded corners, sparse shadows, and semantic color.
- Blue for entry or control, orange for selection or execution, green for local/provider success, purple for data or semantic work, and black for evidence rails.
- Labels belong to the line or boundary they explain. Avoid legends that make the reader translate the drawing.
- Every region has a reason to occupy its area. Empty space may create hierarchy but must not reveal an unfinished composition.

## Composition patterns

Use a system map when the important story is ownership and flow. Favor a warm or soft canvas, rounded boundary regions, a vertical or hybrid path, generous gaps, and carefully routed connectors. This is the Recall family: sources feed a core, the core exposes interfaces, and peers or external systems remain visibly outside it.

Use a runtime poster when the important story is an exact execution path. Favor a hard top rule, a conclusion headline, strict modular lanes, numbered stages, dense alignment, and a dark evidence rail. This is the rx family: entrypoints, pipeline, processes, provider surfaces, and lifecycle evidence read left to right.

Adapt either pattern to the system. Do not turn them into named user options or mix both mechanically. A diagram may borrow the poster's evidence rail inside a system map when the content earns it.

## Direct drawing workflow

1. Inspect the project and state the diagram's one-sentence thesis internally.
2. Sketch the major visual regions and reading order before adding detail.
3. Write the complete SVG directly, including type hierarchy, shapes, connectors, and small icons.
4. Run `blueprint create architecture <project>` and `blueprint check <project>`.
5. Render the PNG, inspect it at full size and thumbnail size, and revise visible imbalance, collision, repetition, weak hierarchy, misleading routes, and clipped text.
6. Give the user the reviewable HTML or rendered image. Export SVG or PNG after the composition is accepted.

Never stop at structural validity. A valid but generic equal-card grid is a failed architecture diagram unless the system genuinely has equal parallel units. Do not use repeated cards as a substitute for composition. Do not make the user do the layout work.
