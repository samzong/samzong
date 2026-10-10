# Agent Role Configurations

Read this index when inspecting, comparing, or manually configuring Lody Duo roles. Each attachment contains the saved name, description, visibility, full `runConfig`, and complete prompt prefix. The eight available workflow role configurations were read from Lody MCP on 2026-10-10.

These are configuration references, not Lody import payloads. Installing this Skill makes the attachments available; it does not create roles, change existing roles, or bind a machine. Dispatch still uses the current workspace catalog and its actual role IDs.

| Role and attachment | Agent | Model ID | Effort | Permission setting |
|---|---|---|---|---|
| [Archestrator](agent-roles/archestrator.md) | Claude Code | `claude-fable-5-1` | `medium` | `bypassPermissions` |
| [Build Standard](agent-roles/build-standard.md) | Codex | `gpt-6.1-sol` | `high` | `agent-full-access` |
| [Build Deep](agent-roles/build-deep.md) | Claude Code | `opus` | `medium` | `bypassPermissions` |
| [Build Fast](agent-roles/build-fast.md) | Codex | `gpt-6-luna` | `high` | `agent-full-access` |
| [Research Deep](agent-roles/research-deep.md) | Codex | `gpt-6.1-sol` | `high` | `agent-full-access` |
| [Research Fast](agent-roles/research-fast.md) | Codex | `gpt-6-luna` | `high` | `agent-full-access` |
| [Review Fast](agent-roles/review-fast.md) | Codex | `gpt-6.1-sol` | `medium` | `agent-full-access` |
| [Review Deep](agent-roles/review-deep.md) | Codex | `gpt-6.1-sol` | `high` | `agent-full-access` |

## Reuse on another installation

Select your own machine and matching Agent configuration in Lody. Copy the role's name, description, visibility, supported runtime settings, and prompt prefix from its attachment. Check the target catalog for model and option support before saving; an unavailable model is not permission to substitute another configuration silently.

Workspace, machine, Agent configuration, and role IDs are deliberately omitted because they belong to the source installation. Availability and source revision are capture metadata, not guarantees about your installation. Saved settings describe the role preset; they do not prove the model or effort used by a running session.

The descriptions and complete prompt prefixes are English translations of the captured source, preserving its instructions and language policy: conversation and progress replies remain concise Chinese, while Git artifacts follow repository language conventions. The source already replaced installation-specific Skill paths with instructions to discover the installed `lody-duo` or `liability-review` Skill and removed Archestrator's redundant local path hint. Review roles require [liability-review](../../liability-review/SKILL.md); install it separately if your installer copies only `lody-duo`.

The captured permission modes provide tool capabilities. Read-only research, consultation, and review remain task contracts; these modes do not enforce filesystem read-only access or grant additional business authority. Session and Tab titles use `[Role name] Task title` as specified in the prompts and the main Skill.

## Maintenance

When changing a role used by this workflow, update its attachment and this index from a fresh `lody_agent_role_get` result. Preserve the complete `runConfig`, including boolean options, and the full prompt prefix. Normalize installation-specific paths without rewriting role behavior.
