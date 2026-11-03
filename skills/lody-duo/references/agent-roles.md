# Agent Role Configurations

Read this index when you inspect, compare, or manually configure Lody Duo roles. Each attachment contains the saved name, description, visibility, full `runConfig`, and the target prompt. The runtime settings of all nine indexed roles were read with `lody_agent_role_get` on 2026-10-22.

These are configuration references and not Lody import payloads. Installing this skill makes the attachments available. It does not create roles, change existing roles, or bind a machine. Dispatch still uses the current workspace catalog and its actual role IDs.

| Role and attachment | Agent | Model ID | Effort | Permission setting |
|---|---|---|---|---|
| [Head](agent-roles/head.md) | Claude Code | `opus` | `high` | `bypassPermissions` |
| [Build Standard](agent-roles/build-standard.md) | Codex | `gpt-6.1-sol` | `high` | `agent-full-access` |
| [Architect](agent-roles/architect.md) | Claude Code | `opus` | `high` | `bypassPermissions` |
| [Build Fast](agent-roles/build-fast.md) | Codex | `gpt-6-luna` | `high` | `agent-full-access` |
| [Research Deep](agent-roles/research-deep.md) | Codex | `gpt-6.1-sol` | `high` | `agent-full-access` |
| [Research Fast](agent-roles/research-fast.md) | Codex | `gpt-6-luna` | `high` | `agent-full-access` |
| [Review Fast](agent-roles/review-fast.md) | Codex | `gpt-6.1-sol` | `high` | `agent-full-access` |
| [Review Deep](agent-roles/review-deep.md) | Claude Code | `opus` | `high` | `bypassPermissions` |
| [Ops](agent-roles/ops.md) | Codex | `gpt-6.1-sol` | `high` | `agent-full-access` |

## Reuse on another installation

Select your own machine and the matching Agent configuration in Lody. Copy the name, description, visibility, supported runtime settings, and target prompt of a role from its attachment into the Lody UI. Before you save, check the target catalog for model and option support. An unavailable model is not permission to substitute another configuration silently.

The workspace, machine, Agent configuration, and role IDs are left out on purpose, because they belong to the source installation. The capture date and the runtime source describe when and how the settings were collected. They are not guarantees about your installation. Saved settings describe the role preset. They do not prove the model or effort of a running session.

The first sentence of each target prompt is the persona of the role. Keep it when you shorten or merge shared constraints. The prompts are English translations of the source text. They keep the language policy of the source: conversation and progress replies are concise Chinese, and Git artifacts follow the repository's language convention. Each prompt keeps the duties of its role and refers to the shared constraints and the session title rules of the main skill. Installation-specific skill paths are replaced with an instruction to discover the installed `lody-duo` or `liability-review` skill. The review roles require [liability-review](../../liability-review/SKILL.md). Install it separately if your installer copies only `lody-duo`.

The permission modes give tool capabilities. Read-only research, consultation, review, and Ops stay task contracts. The modes do not enforce read-only access to files and do not grant more business authority. The main skill is the only source of the session and Tab title rules, in its "Session and Tab titles" section.

## Role name history

On 2026-11-03 the role `Archestrator` was renamed to `Head`, and the role `Build Deep` was renamed to `Architect`. Responsibilities did not change. Earlier names of the host role were `Orchestrator` and then `Archestrator`. Ops, Build Standard, Build Fast, Research Deep, Research Fast, Review Deep, and Review Fast keep their names.

## Maintenance

Read the complete `runConfig` of an existing role again with `lody_agent_role_get`, including boolean options. Then update its attachment and this index. The prompts are target text. `lody_agent_role_update` proposes changes to the name, the description, and the prompt, and they take effect only after the owner saves them on its review card. Change the machine, Agent, model, effort, and permission settings in the Lody UI. Editing this repository and installing this skill do not change online roles.
