---
name: codewiki-generator
description: Generate a deep, code-first project wiki and VitePress documentation site (DeepWiki-style) for a repository. Use when asked to create a complete wiki/manual for a new codebase, build a code-first documentation site, or generate a `codewiki/` folder with structured Markdown, diagrams, and navigation based on the source code (not existing docs).
---

# Codewiki Generator

## Overview
Generate a DeepWiki-style, code-first documentation site for a given repository. The output will reside in the `codewiki/` directory, including a VitePress configuration and an auto-generated sidebar. The documentation must reflect the project's current state and prioritize explaining the system's design rationale over merely describing its functionality.

## Workflow

### 0) Confirm Language Preference
Ask the user: "What language should the documentation be written in? (e.g., English, 中文, 日本語, etc.)"
IF the user specifies a language THEN store the provided language and apply it to all generated prose content.
ELSE IF the user does not specify a language THEN default to English.

### 1) Inspect the Codebase First (Code > Docs)
- Scan source files, configuration files, build/test pipelines, entry points, and architectural directories.
- Treat existing documentation (e.g., `README`, `docs/`) as secondary hints.
- Prioritize code evidence as the ultimate source of truth.
- Identify and report any discrepancies between documentation and code.

### 2) Analyze Codebase → Structured Metadata
Execute the analyzer script to scan the codebase and generate structured metadata. `<skill-root>` refers to the directory containing this `SKILL.md`.

```bash
python3 <skill-root>/scripts/codewiki_analyze.py \
  --repo-root <repo-root> \
  --out-dir codewiki \
  --force
```

This command generates the following outputs:
- `codewiki/.meta/` directory containing `deps.json`, `entrypoints.json`, `evidence.json`, `doc_plan.json`, and `symbols.json` (if ctags is available).
- `codewiki/quality-report.md` detailing coverage and pages with low confidence.
- VitePress configuration scaffolding, without placeholder `.md` files.

Note: This step does not generate placeholder `.md` files. The LLM is responsible for writing documentation content directly in Step 4.
Note: Images referenced in existing Markdown files are copied into `codewiki/assets/`.

### 3) Dynamically Determine the Documentation Set
- Include all minimally required pages.
- Add conditional modules only when corresponding code evidence exists.
- Split or merge pages based on project size and complexity.
- Adhere to the guidelines specified in `references/structure-and-heuristics.md`.
- Use lowercase directory and file names for all generated documentation.

### 4) Write the Documentation (Code-first, Visual-first)
Read `codewiki/.meta/doc_plan.json` and process each planned page:
- IF a page has no supporting evidence OR low relevance to the codebase THEN skip that page.
- ELSE create an `.md` file only for pages containing actual content.

Writing guidelines:
- Use the language determined in Step 0 for all prose content.
- Retain original formatting for code snippets, file paths, and technical terms.
- Start every page with a low-contrast `# Related Code` block (fenced `text` block), not a heading.
- Utilize Mermaid for diagrams (context, class, sequence, component, dataflow).
- Adhere to Mermaid-safe syntax: use simple node IDs, avoid `/`, `()`, and `:` in labels, and prefer `node[plain label]`.
- Explain the rationale behind design choices, trade-offs, and constraints.
- Provide informed opinions: highlight strengths, technical debt, or "code smells."
- Link concepts to specific file paths, classes, or entry points.
- Reuse existing images/diagrams IF they are accurate.
- Maintain Markdown lint-friendly practices: consistent headings, no trailing spaces, and proper list formatting.

Refer to `references/doc-templates.md` for detailed, evidence-linked page templates.

### 5) Refresh Sidebar and Run the Site
After documentation generation, update the sidebar to reflect the actual files:

```bash
python3 <skill-root>/scripts/codewiki_bootstrap.py \
  --repo-root <repo-root> \
  --out-dir codewiki \
  --refresh-sidebar
```

Install documentation dependencies (Mermaid support is enabled by default):

```bash
npm --prefix codewiki install
```

Launch the documentation site:

```bash
npm --prefix codewiki run docs:dev
```

Alternative launch command (without prior `npm install`):

```bash
npx -p vitepress -p vitepress-plugin-mermaid -p mermaid vitepress dev codewiki
```

### 6) Offer Optional Workflows
After the site is operational, inform the user about available options:

"Documentation site is ready! You can now:
- **Option A**: Deploy to Cloudflare Pages — publish the site to a live URL
- **Option B**: Add multi-language support (i18n) — translate docs to another language

Let me know if you'd like to proceed with any of these."

## Optional Workflows

These workflows are available for execution after the core documentation generation process is complete.

### Option A) Deploy to Cloudflare Pages

Deploy the documentation site to Cloudflare Pages using the `wrangler` CLI.

**Trigger**: The user requests to deploy, publish, or host the documentation.

**See**: `references/deploy-cloudflare.md` for comprehensive instructions (including `wrangler` installation, login verification, build process, deployment, and updating `index.md` with the live URL).

### Option B) Add Multi-language Support (i18n)

Translate existing documentation into a second language and configure the VitePress language switcher.

**Trigger**: The user requests translation, multi-language, or internationalization (i18n) support.

**See**: `references/i18n-setup.md` for comprehensive instructions (including directory structure, VitePress `locales` configuration, and translation guidelines).

## Quality Bar (Non-negotiable)
- **Visual First**: Prioritize diagrams over extensive text blocks.
- **Insightful**: Explain design intent beyond mere mechanics.
- **Opinionated**: Highlight architectural strengths and identified risks.
- **Linked**: Reference concrete files/classes for all key concepts.
- **Code-first**: The codebase is the authoritative source; documentation serves as a complementary explanation.

## Resources

### scripts/
- `codewiki_analyze.py`: Scans the codebase and generates `.meta/*.json` metadata files.
- `codewiki_bootstrap.py`: Scaffolds the `codewiki/` directory, copies referenced images, and generates the sidebar.

### references/
- `structure-and-heuristics.md`: Contains rules for module selection and signal identification.
- `doc-templates.md`: Provides comprehensive, evidence-linked templates for all page types.
- `deploy-cloudflare.md`: Details the workflow for deploying to Cloudflare Pages.
- `i18n-setup.md`: Outlines the configuration process for multi-language support.

### assets/
- `vitepress/`: Contains minimal VitePress configuration and a landing page template.