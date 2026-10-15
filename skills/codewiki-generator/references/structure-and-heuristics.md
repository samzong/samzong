# Structure and Heuristics

## Minimal required modules
Always produce these pages (content adapts to project complexity):
- `overview.md`
- `getting-started/quickstart.md`
- `architecture/overview.md`
- `core-components/overview.md`
- `development/overview.md`

## Conditional modules (create only with strong code evidence)
- UI app: `application-lifecycle/bootstrap.md`, `user-inference/ux-model.md`
- API: `api-reference/overview.md` + per-surface pages
- Plugins: `plugins/overview.md` + per-plugin pages
- Build & Release: `build-and-release/ci-cd.md`, `build-and-release/release-process.md`
- Data model/storage: `data/domain-model.md`, `data/storage-layout.md`
- Security: `security/auth-authz.md`, `security/threat-model.md`
- Observability: `observability/logging-metrics-tracing.md`, `observability/runbook.md`
- Performance: `performance/bottlenecks.md`, `performance/scaling-strategy.md`
- Integrations: `integrations/external-services.md`
- Troubleshooting: `troubleshooting/common-issues.md`
- Glossary: `glossary.md`

## Evidence signals (examples, not exhaustive)
- UI app: `package.json` with React/Vue/Svelte, `src/App.*`, `ios/`, `android/`, `.xcodeproj`, `MainActivity`
- API: `openapi.*`, `swagger.*`, `routes/`, `controllers/`, `proto/`, HTTP server frameworks
- Plugins: `plugins/`, `extensions/`, `hooks/`, dynamic module loading or plugin registry
- CI/CD: `.github/workflows/`, `.gitlab-ci.yml`, `Jenkinsfile`, `Makefile`, `Dockerfile`
- Data: `migrations/`, `schema.sql`, `models/`, `entities/`, ORM configs
- Observability: `otel`, `prometheus`, `metrics`, `tracing`, structured logging
- Security: `auth`, `oauth`, `jwt`, `rbac`, `policy`

## Evidence scoring (strong mode)
Strong mode uses `references/evidence-rules.json` to score each module.
- **Included**: score >= threshold
- **Candidate**: score >= candidate_threshold
- **Excluded**: below candidate_threshold

The analyzer writes `codewiki/.meta/evidence.json` and `doc_plan.json` so you can
audit why modules were included or skipped.

## Granularity rules
- If a module has multiple meaningful sub-systems, split into multiple docs.
- Prefer fewer, deeper docs for small repos; prefer multiple focused docs for large repos.
- Use directories as architecture signals; split along those boundaries when possible.

## Existing docs
- Treat existing docs as hints only; validate against code before using.
- Enforce lowercase directory and file names for all generated docs.
