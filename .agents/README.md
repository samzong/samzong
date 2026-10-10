# Shared Agent Workflow Snapshot

This directory is an English public snapshot of Samzong's personal cross-repository agent rules, the eleven skills directly named by those rules, and Lody Duo. Human-facing replies default to Chinese. Exact Chinese authorization phrases and examples are intentionally preserved.

## Use the snapshot

Read [AGENTS.md](AGENTS.md) and adapt it to your own policy before adopting it. Place the rules at the global or project instruction entrypoint your agent host actually reads, using that host's supported mechanism. Their presence at `.agents/AGENTS.md` in this repository does not establish that a host has loaded them.

Install only the workflows you need and their required sibling skill directories into your host's skill search path, keeping their `SKILL.md`, `agents/`, `references/`, `assets/`, and `scripts/` together where present. Generic `~/.agents/` paths describe the shared installation convention used by these rules; use the corresponding supported location in your own environment. Installing a skill does not install its external tools, create Lody roles, or configure an MCP client.

For Lody Duo, install [lody-duo](skills/lody-duo/SKILL.md), [gmc](skills/gmc/SKILL.md), and [liability-review](skills/liability-review/SKILL.md) as sibling directories. All three skills are required for the complete workflow. The `gmc` CLI is a separate external requirement and is not installed by this package. You do not need to install all twelve skills to use a selected workflow and its required dependencies.

Lody Duo includes [eight workflow role configuration references](skills/lody-duo/references/agent-roles.md), with English descriptions and complete translated prompt prefixes that retain the Chinese conversation policy. They support manual inspection and configuration, are not import payloads, and do not create roles or bind a machine. Dispatch uses the current workspace catalog.

This is a manual snapshot. Editing the repository copy does not change `~/.agents/`, and there is no automatic synchronization, installer, hook configuration, or scheduler in this package.

## Included skills and external requirements

Requirements apply to the selected workflow, rather than every skill installation.

The root rules prefer each repository's declared toolchain. Their macOS defaults use `uv` for Python, Homebrew for Go/Rust/Node, and `pnpm` for frontend packages. They also use `rtk` to filter noisy output, with raw commands or `rtk proxy` for exact JSON, help, and errors. These tools are external and are not installed by this snapshot.

| Skill | Purpose | External requirements |
|---|---|---|
| [gmc](skills/gmc/SKILL.md) | Git worktree lifecycle and explicit gmc operations | `gmc`; Git for repository operations; `gh` for GitHub-dependent actions |
| [systematic-debugging](skills/systematic-debugging/SKILL.md) | Evidence-led diagnosis and verified corrections | The affected project's existing toolchain; browser work follows browser-cdp |
| [mirror](skills/mirror/SKILL.md) | Consequential decisions tied to owner intent | Evidence from the affected project; liability-review when code review is required |
| [liability-review](skills/liability-review/SKILL.md) | Read-only review of an exact local diff or PR | Git; authenticated `gh` for PR mode; an isolated reviewer for required independent passes |
| [pr-eval](skills/pr-eval/SKILL.md) | Evaluate feedback and repair authorized owned-PR blockers | Git, authenticated `gh`, the project's checks, pre-ship, and an evidenced repository review mechanism |
| [pre-ship](skills/pre-ship/SKILL.md) | Read-only verification before commit or push | Git, liability-review, and the repository's canonical checks; optional hook helper described below |
| [ship](skills/ship/SKILL.md) | Authorized staged delivery through a commit, push, and PR | Git, authenticated `gh`, pre-ship, repository gates, `gmc` for the delivery-loop worktree, and mirror when consequential |
| [commit](skills/commit/SKILL.md) | Explicit commit workflow with conditional push | Git, pre-ship, configured signing where required, and mirror when consequential |
| [blueprint](skills/blueprint/SKILL.md) | Blueprint Artifact creation and lifecycle | `blueprint`; `pnpm` for dependency-based Presets; browser-cdp for browser acceptance; authorized Cloudflare access for deployment |
| [gofs](skills/gofs/SKILL.md) | Local static HTTP serving and health checks | `gofs` and `curl` |
| [browser-cdp](skills/browser-cdp/SKILL.md) | Shared Chrome DevTools MCP and bounded setup | Chrome 144+, supported Node.js and `npx`, the configured Chrome DevTools MCP, and the selected agent client; host-native Browser transport only under the skill's fallback contract |
| [lody-duo](skills/lody-duo/SKILL.md) | Lody role delegation, verification, and independent review | Lody MCP in a Lody session, the sibling gmc and liability-review skills, the external `gmc` CLI for worktree operations, and compatible roles already supplied by the workspace catalog; Fast reasoning effort at least `high` |

The liability-review independent-review contract prefers a fresh in-runtime reviewer and conditionally uses Confer as a fallback. Confer MCP and the `confer` skill are external and are not bundled here. If no valid independent path is available, retain the contract's unavailable-review verdict and explicit exemption boundary; do not silently replace the transport or waive the review.

The optional `~/.agents/bin/pre-ship-gate` helper and client hooks that consume its receipts are not bundled. Use that receipt mechanism only when such a hook is already active, as specified by pre-ship; otherwise omit the receipt.

The browser scripts include their setup, structural doctor, and live-check implementations. Running them is separate from installing the snapshot. Setup requires an explicit request naming the target clients; `--live` starts a debugging connection and can require the user's Chrome permission approval. Client-specific adapters such as `pi-mcp-adapter` and `@deepseek-ai/dsh-mcp-client` remain external. The scripts use the DeepSeek Harness installation's `js-yaml` for its configuration path.

Other skills mentioned conditionally by these contracts, such as `no-comment`, are not added by this snapshot. Follow the contract's availability behavior and the user's authorization; do not claim an absent skill or tool is installed.

## License and attribution

The repository uses the [MIT License](../LICENSE).

The included [Blueprint skill](https://github.com/samzong/blueprint) and references retain `Copyright (c) 2026 samzong`. The included [gofs skill](https://github.com/samzong/gofs) retains `Copyright (c) 2025 samzong`. Both source packages use the MIT terms retained in the repository license.
