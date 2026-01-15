# Codewiki Generator

Generate DeepWiki-style documentation sites for any codebase.

## Core Principles

| Principle | Meaning |
|-----------|---------|
| **Code-first** | Code is truth, docs are secondary |
| **Visual-first** | Mermaid diagrams over walls of text |
| **Insightful** | Explain why, not just what |

## Quick Start

```bash
# 1. Bootstrap codewiki directory
python <skill-root>/scripts/codewiki_bootstrap.py \
    --repo-root <target-repo> \
    --out-dir codewiki \
    --force

# 2. Launch the doc site
npm --prefix codewiki install
npm --prefix codewiki run docs:dev
```

## Generated Structure

```
codewiki/
├── overview.md              # Project overview
├── getting-started/         # Quickstart guide
├── architecture/            # Architecture design
├── core-components/         # Core components
├── development/             # Development guide
└── .vitepress/              # VitePress config
```

## Module Selection

**Required**: overview, getting-started, architecture, core-components, development

**Conditional** (needs code evidence): api-reference, plugins, build-and-release, security, observability, etc.

See [structure-and-heuristics.md](references/structure-and-heuristics.md) for details.
