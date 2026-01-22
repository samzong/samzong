---
name: codewiki-generator
description: Generate a deep, code-first project wiki and VitePress documentation site (DeepWiki-style) for a repository. Use when asked to create a complete wiki/manual for a new codebase, build a code-first documentation site, or generate a `codewiki/` folder with structured Markdown, diagrams, and navigation based on the source code (not existing docs).
---

# Codewiki Generator

## Overview
Create a DeepWiki-style, code-first documentation site for a repository. Output lives in `codewiki/` with VitePress config and a generated sidebar. Documentation must adapt to project reality and emphasize why the system is designed this way, not just what it does.

## Workflow

### 0) Confirm language preference
Before starting, ask the user:
> What language should the documentation be written in? (e.g., English, 中文, 日本語, etc.)

Store the answer and apply it to all generated prose content. Default to English if not specified.

### 1) Inspect the codebase first (code > docs)
- Scan source, configs, build/test pipelines, entrypoints, and architectural directories.
- Treat existing docs (README, `docs/`) as secondary hints only.
- Prefer code evidence for truth; call out doc/code mismatches.

### 2) Bootstrap `codewiki/` (evidence-driven)
Run the analyzer to scaffold the folder, generate metadata, and create VitePress config. `<skill-root>` is the directory containing this SKILL.md.

```
python3 <skill-root>/scripts/codewiki_analyze.py \
  --repo-root <repo-root> \
  --out-dir codewiki \
  --force \
  --refresh-sidebar
```

Outputs:
- `codewiki/.meta/` with `deps.json`, `entrypoints.json`, `evidence.json`, `doc_plan.json`, `symbols.json` (ctags if available)
- `codewiki/quality-report.md` with coverage and low-confidence pages
- Evidence-scored conditional modules
- VitePress config and sidebar

Notes:
- Creates minimal required pages and folders.
- Copies images referenced in existing Markdown into `codewiki/assets/`.
- Use `--refresh-sidebar` after new docs are added.

### 3) Decide the doc set dynamically
- Always include the minimal required pages.
- Add conditional modules only when code evidence exists.
- Split or merge pages based on project size and complexity.
- Follow guidance in `references/structure-and-heuristics.md`.
- Use lowercase directory and file names for all generated docs.

### 4) Write the docs (code-first, visual-first)
- **Use the language specified in Step 0** for all prose content. Keep code snippets, file paths, and technical terms in original form.
- Start every page with a low-contrast **# Related Code** block (fenced `text` block), not a heading.
- Use Mermaid for diagrams (context, class, sequence, component, dataflow).
- Use Mermaid-safe syntax: simple node ids, avoid `/`, `()`, `:` in labels, prefer `node[plain label]`.
- Explain **why** the design exists: rationale, tradeoffs, constraints.
- Be opinionated: highlight strengths and tech debt or "bad smells".
- Link concepts to concrete file paths, classes, or entrypoints.
- Reuse existing images/diagrams when accurate; do not blindly trust old docs.
- Keep Markdown lint-friendly: consistent headings, no trailing spaces, proper lists.

Use `references/doc-templates.md` for deep, evidence-linked page templates.

### 5) Refresh sidebar and run the site
After generating new files:

```
python3 <skill-root>/scripts/codewiki_bootstrap.py \
  --repo-root <repo-root> \
  --out-dir codewiki \
  --refresh-sidebar
```

Install doc dependencies (Mermaid support is enabled by default):

```
npm --prefix codewiki install
```

Launch the site:

```
npm --prefix codewiki run docs:dev
```

Alternative (no install):

```
npx -p vitepress -p vitepress-plugin-mermaid -p mermaid vitepress dev codewiki
```

### Alternative: Bootstrap only (no analysis)
If you only need to scaffold without deep analysis:

```
python3 <skill-root>/scripts/codewiki_bootstrap.py \
  --repo-root <repo-root> \
  --out-dir codewiki \
  --force
```

This creates the folder structure without generating `.meta/` evidence files.

---

## Optional Workflows

These workflows are available after completing the main documentation generation.

### Option A) Deploy to Cloudflare Pages

Deploy the site to Cloudflare Pages using `wrangler` CLI.

**Trigger**: User asks to deploy, publish, or host the documentation.

**See**: `references/deploy-cloudflare.md` for full steps (wrangler install, login check, build, deploy, update index.md with live URL).

### Option B) Add Multi-language Support (i18n)

Translate docs to a second language and configure VitePress language switcher.

**Trigger**: User asks for translation, multi-language, or i18n support.

**See**: `references/i18n-setup.md` for full steps (directory structure, VitePress locales config, translation guidelines).


## Quality Bar (non-negotiable)
- **Visual First**: prefer diagrams over walls of text.
- **Insightful**: explain design intent, not just mechanics.
- **Opinionated**: surface architectural highlights and risks.
- **Linked**: reference concrete files/classes for every key concept.
- **Code-first**: code is the source of truth; docs are secondary.

## Resources

### scripts/
- `codewiki_bootstrap.py`: scaffolds `codewiki/`, copies referenced images, generates sidebar.

### references/
- `structure-and-heuristics.md`: module selection rules and evidence signals.
- `doc-templates.md`: deep, evidence-linked templates for all pages.
- `deploy-cloudflare.md`: Cloudflare Pages deployment workflow.
- `i18n-setup.md`: multi-language support configuration.

### assets/
- `vitepress/`: minimal VitePress config and landing page template.
