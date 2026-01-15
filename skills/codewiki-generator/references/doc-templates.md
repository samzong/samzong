# Doc Templates

## Shared header (all docs)
Start every page with a short header listing related code paths.

```
# <Title>

```text
# Related Code
- `path/to/file`
- `path/to/dir/`
```
```

## overview.md
- One-line definition
- Tech stack radar (bulleted)
- System context diagram (Mermaid)
- Top 3 architectural highlights + top 2 risks

## architecture/overview.md
- Architecture summary and rationale (why this shape)
- Component diagram (Mermaid)
- Data flow or deployment view (Mermaid)
- Tech debt notes

## core-components/overview.md
- Component dictionary (name -> responsibility)
- Relationship graph (Mermaid class or flow)
- Callouts to critical files/classes

## getting-started/quickstart.md
- Minimal prerequisites
- 3-7 steps to run
- Explicit commands with expected outputs

## development/overview.md
- Local dev workflow
- Debugging tips + common pitfalls
- Test strategy overview

## api-reference/overview.md (if applicable)
- API surface map
- Authn/authz overview
- Example requests/responses (short)

## build-and-release/ci-cd.md (if applicable)
- Pipeline stages and why
- Artifacts and versioning
- Release risks

## plugins/overview.md (if applicable)
- Plugin lifecycle
- Extension points
- Compatibility constraints

## application-lifecycle/bootstrap.md (if applicable)
- Startup sequence diagram (Mermaid)
- Key initialization steps and rationale
