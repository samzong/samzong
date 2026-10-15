---
name: gofs
description: Serve local directories and built static output over HTTP with gofs. Use when an agent needs a lightweight file server, a machine-readable directory listing, multiple mounted directories, or a health-checked local preview without a framework-specific development server.
---

# gofs

## Serve files

Confirm the exact directory and whether network access is intended. Unless the user specifies a port, let the operating system choose an available port. Prefer a read-only mount on loopback:

```sh
gofs --host 127.0.0.1 --port 0 -d "/:/absolute/path:ro:Files"
```

Wait for the `Server listener created` log entry and use its `address` value. Set `GOFS_ENV=production` only when JSON logs are explicitly required. Serve built frontend output, not source trees that require a framework build or development server. Remove `:ro` only when the user explicitly needs uploads or directory creation.

For multiple mounts, repeat `-d`:

```sh
gofs -d "/assets:/srv/assets:ro:Assets" -d "/logs:/var/log:ro:Logs"
```

## Keep exposure narrow

- Keep the default `127.0.0.1` binding unless the user explicitly requests network access.
- Do not serve a repository root, credential directory, or hidden files without checking the contents first.
- Do not add `--show-hidden` unless hidden files are the requested content.

## Verify the running server

Wait for the server, then verify health:

```sh
curl --fail --silent "http://$address/healthz"
```

Request a machine-readable listing:

```sh
curl --fail --silent -H 'Accept: application/json' "http://$address/"
```

Report the selected address, verified URL, and mount scope. Stop the process when the preview or transfer is no longer needed.
