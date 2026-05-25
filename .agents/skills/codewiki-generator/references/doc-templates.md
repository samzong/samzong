# Deep Doc Templates (Strong)

These templates are designed for the "strong" mode. Keep them concise but evidence-linked.

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

## index.md (VitePress Home - REQUIRED)
The landing page MUST use VitePress home layout with hero and features.

```yaml
---
layout: home
hero:
  name: "Project Name"
  text: "One-line tagline"
  tagline: "Brief description"
  actions:
    - theme: brand
      text: Getting Started
      link: /getting-started/quickstart
    - theme: alt
      text: Architecture
      link: /architecture/overview
features:
  - icon: 🏗️
    title: "Feature 1"
    details: "Short description"
  - icon: ⚡
    title: "Feature 2"
    details: "Short description"
  - icon: 🔧
    title: "Feature 3"
    details: "Short description"
---
```

After frontmatter:
- Tech stack table (Layer | Technology)
- Quick navigation links to key sections

## overview.md
- One-line definition
- Tech stack radar (bulleted)
- System context diagram (Mermaid)
- Top 3 architectural highlights + top 2 risks
- "Why now" / "Why this shape"

## architecture/overview.md
- Architecture summary and rationale
- Component diagram (Mermaid)
- Data flow diagram (Mermaid)
- Deployment view or runtime topology (Mermaid)
- Tech debt notes

## core-components/overview.md
- Component dictionary (name -> responsibility + key files)
- Relationship graph (Mermaid)
- Critical paths (call chain or dataflow)

## getting-started/quickstart.md
- Minimal prerequisites
- 3-7 steps to run
- Explicit commands with expected outputs
- First-hour guide: entrypoints + key directories

## development/overview.md
- Local dev workflow
- Debugging tips + common pitfalls
- Test strategy overview
- How to trace a request/task end-to-end

## api-reference/overview.md (if applicable)
- API surface map
- Authn/authz overview
- Example requests/responses (short)
- Error model

## build-and-release/ci-cd.md (if applicable)
- Pipeline stages and why
- Artifacts and versioning
- Release risks
- Environments

## plugins/overview.md (if applicable)
- Plugin lifecycle
- Extension points
- Compatibility constraints

## security/auth-authz.md (if applicable)
- Authn/authz flow
- Roles and permissions
- Sensitive data handling

## observability/logging-metrics-tracing.md (if applicable)
- Signals and tools
- Critical dashboards
- Alerting philosophy

## observability/runbook.md (if applicable)
- Incident checklist
- Common failure modes

## data/domain-model.md (if applicable)
- Entities and relationships
- Data ownership and consistency

## data/storage-layout.md (if applicable)
- Schema layout
- Migrations strategy

## performance/bottlenecks.md (if applicable)
- Hot paths
- Known bottlenecks

## performance/scaling-strategy.md (if applicable)
- Scaling model
- Known limits

## troubleshooting/common-issues.md (if applicable)
- Common issues and fixes

## glossary.md (if applicable)
- Key domain terms
