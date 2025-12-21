# Mirrormate Wrapper Design (v0.1)

Date: 2025-12-21
Status: Draft (validated)

## Goal
Provide a prefix-style wrapper so users can run `mirrormate docker ...` and have image pulls and build-time package downloads use configured mirror sources, without modifying repo Dockerfiles or compose files. The wrapper must be best-effort and never block normal `docker` or `docker compose` execution.

## Non-Goals
- No global daemon configuration.
- No repo file modification.
- No support for git/maven/gradle/gem/composer/nuget or yum/dnf.
- No helm support in v1.

## User Experience
- Usage: `mirrormate [--dry-run] [--verbose] docker ...` or `mirrormate [--dry-run] [--verbose] docker compose ...` or `mirrormate [--dry-run] [--verbose] docker-compose ...`.
- Mirrormate only parses its own flags before `docker`/`docker-compose`. Everything after belongs to Docker/Compose.
- `--dry-run` prints an execution summary (what would be rewritten/injected) and exits 0 without running docker.
- `--verbose` prints injection/rewrite details during normal execution.

## Configuration
Single config file: `~/.mirrormate.yaml`. No profiles. Presence of a section enables it; missing sections are skipped. No defaults are applied.

Example:
```yaml
registries:
  docker.io: m.daocloud.io/docker.io
  ghcr.io: m.daocloud.io/ghcr.io

apt:
  mirror: https://mirrors.aliyun.com/debian
  security: https://mirrors.aliyun.com/debian-security
apk:
  mirror: https://mirrors.aliyun.com/alpine

pip:
  index_url: https://pypi.tuna.tsinghua.edu.cn/simple
  trusted_host: pypi.tuna.tsinghua.edu.cn
npm:
  registry: https://registry.npmmirror.com
yarn:
  registry: https://registry.npmmirror.com
pnpm:
  registry: https://registry.npmmirror.com
go:
  proxy: https://goproxy.cn,direct
```

## Supported Commands
- `docker build`, `docker buildx build`.
- `docker compose` (v2) and `docker-compose` (v1).
- `docker pull`, `docker run` (best-effort image rewrite).

If a subcommand is not supported (e.g., `docker buildx bake`), mirrormate prints usage and exits non-zero.

## Architecture
1) Config Loader: parse `~/.mirrormate.yaml` into a runtime config.
2) Command Parser: detect target (`docker`, `docker compose`, `docker-compose`), capture relevant flags, and build an execution plan.
3) Registry Rewriter: rewrite image references using `registries` mapping.
4) Dockerfile Injector: generate a temporary Dockerfile and insert a mirror-injection snippet after each `FROM` where possible.
5) Compose Processor: parse YAML, rewrite `image:` fields, and replace `build.dockerfile` with temporary Dockerfiles when needed.
6) Executor: run the original command with temporary paths, preserve stdout/stderr/signal behavior, and return the original exit code.

## Dockerfile Injection
- For each stage, rewrite `FROM` image registry prefix if configured.
- Inject a small, idempotent shell snippet after `FROM` to configure mirrors:
  - apt (Debian/Ubuntu): rewrite `/etc/apt/sources.list` and entries under `/etc/apt/sources.list.d/`.
  - apk (Alpine): rewrite `/etc/apk/repositories`.
  - env-based tooling: set `PIP_*`, `NPM_CONFIG_REGISTRY`, `YARN_NPM_REGISTRY_SERVER`, `PNPM_*`, `GOPROXY/GONOSUMDB/GONOPROXY` based on config.
- If stage is `scratch` or `/bin/sh` is not available, skip injection for that stage; still rewrite `FROM` image.
- Injection must be best-effort; failures should not fail the build.

## Compose Processing
- Parse each compose file specified by `-f/--file` (v1 or v2); default to `docker-compose.yml` if omitted.
- Rewrite `image:` fields using registry mapping.
- For services with `build`, generate a temporary Dockerfile (if a Dockerfile is referenced) and update `build.dockerfile` to point to the temporary file.
- Preserve original order of compose files and pass them to docker in the same sequence.

## Image Rewrite for docker run/pull
- Attempt to locate the image argument in `docker run` and `docker pull` by parsing known flags.
- If parsing is ambiguous (unknown flag that may consume a value), skip rewriting and execute the command unchanged. When `--verbose` is set, emit a warning that rewrite was skipped.

## Error Handling and Degradation
- If `~/.mirrormate.yaml` is missing or invalid: print a warning and execute the command unchanged.
- If Dockerfile/compose path is missing or unreadable: do not block; execute command unchanged (docker/compose handles errors).
- If injection or parsing fails: fall back to minimal behavior or no-op; never block execution.

## Implementation Plan (Minimal)
- Replace `tools/mirrormate.go` with wrapper-based implementation.
- New internal packages (or files) for: config parsing, Dockerfile rewrite/inject, compose rewrite, command parsing, and exec.
- Keep the interface small: no extra flags beyond `--dry-run`, `--verbose`, `-h/--help`, `--version`.
- Maintain backward compatibility only at the binary name; behavior changes to wrapper semantics (documented in README or help output).

## Open Questions (Deferred)
- Whether to keep the old file-rewrite behavior as a separate tool.
- Whether to support more package managers or image sources in future versions.
