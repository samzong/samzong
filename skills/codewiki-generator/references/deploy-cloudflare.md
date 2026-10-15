# Deploy to Cloudflare Pages

Deploy the generated documentation site to Cloudflare Pages using `wrangler` CLI.

## Prerequisites

### 1. Verify wrangler is installed

```bash
which wrangler
```

If not found, prompt user:

```bash
npm install -g wrangler
```

### 2. Verify login and permissions

```bash
wrangler whoami
```

Check output for:

- Successful authentication (shows account email/name)
- `pages:write` permission (or equivalent Cloudflare Pages access)

If not logged in, prompt user:

```bash
wrangler login
```

## Build and Deploy

### 1. Build the documentation

```bash
npm --prefix codewiki run docs:build
```

If build fails, fix errors before proceeding.

### 2. Deploy to Cloudflare Pages

```bash
wrangler pages deploy \
  --project-name <project-name> \
  --branch main \
  codewiki/.vitepress/dist/
```

Replace `<project-name>` with a URL-safe project identifier (e.g., `my-project-docs`).

### 3. Update index.md with deployment URL

After successful deployment, add a "Live Site" action in the hero section:

```yaml
hero:
  actions:
    - theme: brand
      text: Getting Started
      link: /getting-started/quickstart
    - theme: alt
      text: Live Site
      link: https://<project-name>.pages.dev
```

## Troubleshooting

| Issue | Solution |
|-------|----------|
| `wrangler: command not found` | `npm install -g wrangler` |
| `Not logged in` | `wrangler login` |
| `Permission denied` | Check Cloudflare dashboard for Pages access |
| Build fails | Fix VitePress/Mermaid errors first |
