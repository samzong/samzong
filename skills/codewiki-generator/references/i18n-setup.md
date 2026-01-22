# Multi-language Support (i18n)

Translate documentation to a second language and configure VitePress for language switching.

## Determine Target Language

| Original Language | Target | Directory |
|-------------------|--------|-----------|
| 中文 (Chinese) | English | `en/` |
| English | 中文 | `zh/` |

## Directory Structure

```
codewiki/
├── index.md           # Default language landing
├── overview.md        # Default language content
├── en/                # English version (if translating from Chinese)
│   ├── index.md
│   ├── overview.md
│   ├── getting-started/
│   ├── architecture/
│   └── ...
├── zh/                # Chinese version (if translating from English)
│   ├── index.md
│   ├── overview.md
│   └── ...
└── .vitepress/
    └── config.mjs     # Updated with i18n config
```

## Configure VitePress

Update `.vitepress/config.mjs` with locales:

```javascript
import { defineConfig } from 'vitepress'

export default defineConfig({
  // ... existing config ...

  locales: {
    root: {
      label: '中文',
      lang: 'zh-CN',
    },
    en: {
      label: 'English',
      lang: 'en',
      link: '/en/',
      themeConfig: {
        nav: [
          { text: 'Overview', link: '/en/overview' },
          { text: 'Guide', link: '/en/getting-started/quickstart' },
        ],
        sidebar: {
          '/en/': [
            {
              text: 'Getting Started',
              items: [
                { text: 'Quickstart', link: '/en/getting-started/quickstart' },
              ]
            },
            {
              text: 'Architecture',
              items: [
                { text: 'Overview', link: '/en/architecture/overview' },
              ]
            }
          ]
        }
      }
    }
  }
})
```

## Translation Guidelines

| Keep Original | Translate |
|--------------|-----------|
| Code snippets | Prose content |
| File paths | Headings |
| Technical terms | Descriptions |
| Mermaid node labels | Hero/features text |
| CLI commands | Navigation labels |

## Translate index.md

Each language needs its own `index.md` with translated hero and features:

**English version (`en/index.md`):**

```yaml
---
layout: home
hero:
  name: "Project Name"
  text: "Tagline in English"
  tagline: "Description in English"
  actions:
    - theme: brand
      text: Getting Started
      link: /en/getting-started/quickstart
    - theme: alt
      text: Architecture
      link: /en/architecture/overview
features:
  - icon: 🏗️
    title: "Feature 1"
    details: "Description in English"
---
```

## Refresh Sidebar

After creating translated files, regenerate the sidebar:

```bash
python3 <skill-root>/scripts/codewiki_bootstrap.py \
  --repo-root <repo-root> \
  --out-dir codewiki \
  --refresh-sidebar
```
