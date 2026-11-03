---
name: lody-duo
description: Coordinate investigation, implementation, and independent review through Agent Roles in Lody. Use when the user invokes lody-duo or asks you to select roles, delegate, and complete a task within Lody. Dispatch and recovery use Lody MCP.
---

# Lody Duo

The current session is the host. The host keeps responsibility for the goal, technical judgment, interpretation of authority, verification, and completion. Do not switch the host's model. For each concrete gap, select one Lody partner. The user does not manage roles, models, or sessions. Build Standard leads development by default. It consults Architect or delegates to Build Fast when that helps. The host can change partners when the phase changes. There is no fixed pipeline, and not every role must run.

## Hosting and authorization

- Establish the goal, scope, authority, and acceptance conditions from the task, prior decisions, and the actual workspace. Read the applicable user and repository `AGENTS.md` instructions, use relevant skills, and reuse valid evidence. Background discussion is not authorization to implement.
- Assume the user is not present. Advance authorized investigation, implementation, verification, correction, and delivery without asking for confirmation at each stage. The host resolves routine technical choices and failure diagnosis.
- Return only owner decisions that change the goal, scope, product semantics, authority, or material risk. First finish the independent authorized work. Put pending decisions in the final handoff. Actions that depend on a decision wait for an explicit answer. Absence, timeout, and silence do not grant authority.
- Tool access grants no authority. Honor runtime approvals. Never bypass a gate or approve a request for the owner. Merges, releases, deployments, and external messages need explicit authority.

The host sends runtime and production problems to Ops, then verifies its advice and evidence. A deployment, rollback, or configuration change still needs authority for that task.

## Common role constraints

- Follow the task scope, the user's authority, and the target repository's `AGENTS.md`. A permission mode adds no scope or publication rights. Analysis, review, and planning stay read-only. Implementation and delivery need task authority.
- Never expose or save credentials or unrelated private data. Never contact other people, force-push, release, deploy, or bypass a gate. Delegate only as this skill permits. Merge only with explicit authority.
- Change only the authorized directory and scope. Preserve existing and unrelated changes. Do not add code comments or documentation comments. Preserve machine-required content and licenses.
- Investigate technical uncertainty and decide routine implementation choices yourself. Do not ask again for an authorized action. Return an unresolved owner decision to the delegator and continue independent authorized work. Silence is not consent.
- Self-testing and a successful tool call are not acceptance. Independent review follows the final-target independent review packet in [independent-review.md](../liability-review/references/independent-review.md), which self-testing cannot replace.
- Report actual results, verifiable evidence, unverified items, and the specific decisions needed. Write the report in concise Chinese. Git artifacts follow the repository's language convention.

## Run only within Lody

Before you use this skill, call `lody_session_create_options` and confirm that it returns the current `sessionId`, `workspaceId`, `machineId`, and execution context. The current tool schema is authoritative.

Lody tools belong to the session that Lody returned. A native subagent with the host's tools is not a Lody host session. The real Lody host dispatches, receives automatic notifications, and accepts results. A native subagent returns bounded work and must not assume that a completion notice reaches it.

Install this skill together with the sibling [gmc](../gmc/SKILL.md) and [liability-review](../liability-review/SKILL.md) skills. The external `gmc` CLI must be available for worktree operations. Installing the skills does not install it.

If Lody tools return `INTERNAL_ERROR` and `lody_session_create_options` fails the same way, follow the host-blocked rule in the [recovery rules](references/delegation.md#recovery-rules).

In every other case where the Lody session or a necessary tool or skill is missing, report the missing capability and continue the authorized work that does not depend on it. Never replace a partner with the host's native subagent, never start a partner CLI directly, and never claim that a background task was accepted. This skill has no fallback outside Lody.

## Select roles

Use `lody_agent_role_list` to discover the roles in the current workspace, and follow pagination when needed. Call `lody_agent_role_get` for each selected role. Check its responsibilities, machine, Agent, model, reasoning effort, permissions, and availability. A name is only a hint for discovery. Dispatch with the stable `id` that the catalog returns. Never hardcode a machine-specific ID, and never create or change a role to fit a task.

To inspect, compare, or manually configure roles, read the [Agent Role configuration attachments](references/agent-roles.md). They install with this skill and do not create roles.

The table below is a starting point. The workspace catalog must already provide the roles, and it is authoritative for Agent, model, and reasoning settings. A role, Agent, or model that the user chose explicitly takes priority.

| Role | Suitable work |
|---|---|
| Research Fast | Defined searches, source checks, and narrow code location |
| Research Deep | Unknown root causes, causal analysis across modules, architectural trade-offs, and refutation |
| Build Fast | Bounded implementation or direct execution with a settled approach and acceptance conditions |
| Build Standard | Development lead: investigation, design judgment, primary implementation, Fast delegation, integration, and verification |
| Architect | Read-only consultation on complex designs, cross-module boundaries, and high-consequence choices. Bounded implementation only when explicitly assigned |
| Review Fast | Independent read-only review of routine, low-risk targets |
| Review Deep | Independent review of persistence, security, money, concurrency, public contracts, or irreversible changes |
| Ops | Post-deployment checks, reproduction of live symptoms, log, trace, and metric investigation, impact analysis, and rollback advice. Read-only, no delegation |

The host classifies the task before dispatch, after it reads the request and the critical materials. Do not judge by file count or changed lines, or because a task names a technology. Check which behavior the change alters. A Fast partner can report that a task needs escalation, but the host still must find complex or high-consequence boundaries.

Build Fast returns an unsettled design or a complex boundary to Build Standard. Complexity alone does not move the whole development task to Architect. To change partners, first confirm that the old partner has ended and verify its side effects, then hand over the concrete gap and the completed work. Never let two partners take the same write scope. If the user's chosen configuration is unavailable, report the limitation. Do not quietly change the model, machine, or permissions, and do not quietly replace an unavailable Build Standard with Architect.

## Build Standard's development responsibility and design consultation

The host gives the complete development goal to Build Standard. Build Standard owns investigation, the design, the primary implementation, integration, verification, and authorized delivery. The host does not split the work into steps or give Architect the same goal. A small independent task with a clear goal can go directly to Build Fast, with no extra dispatch layer. For several independent goals in one window, see [Several goals in one window](references/delegation.md#several-goals-in-one-window). Parallel modules inside one goal follow "Parallel modules".

- Build Standard first reads the code, the callers, and the actual state. It compares the existing path with the strongest simpler alternative and decides routine technical questions itself. Cross-module and high-consequence changes stay with Build Standard. Consult Architect only for a specific design doubt that affects the choice, a contradiction that investigation did not resolve, or a proposal that needs independent refutation. Do not consult it on every task, and do not hand it log analysis, routine implementation, testing, and integration.
- A consultation contains one concrete question, the necessary raw materials and versions, the constraints, the candidate approaches, and the unknown facts that decide between them. Architect is read-only by default. It returns a recommendation, the strongest alternative, the evidence, the failure paths, and a verification method. It does not change source or Git state, and it does not delegate again. Build Standard verifies the advice and then implements it. An Architect that took part in the design cannot give the independent passing review of that design.
- Architect implements a bounded part only when the host or Build Standard assigns a write scope and acceptance conditions. Before the transfer, confirm that the previous writer of that scope has ended, that no related turn is queued, and that its results are verified. A consultation notice does not transfer ownership. Build Standard stays responsible for the whole task.
- Delegate to Build Fast when the goal, scope, approach, and acceptance conditions are clear and the handoff and verification give a real benefit. Build Standard keeps the primary implementation, unsettled designs, cross-module boundaries, high-consequence parts, integration, and the final verification. Do not split work into small tasks only to delegate more. Run a check that one command settles yourself.
- Before Build Standard requests independent review, it reads and runs the [pre-review checks](references/pre-review-checks.md). They run the commit-time gates on the staged target and record the result in the evidence packet. For independent review, reuse, and corrections, see that file.

## Dispatch and working directories

Every assignment gives the goal, the input locations and versions, the accepted decisions, the authority and write scope, the required result, and the acceptance evidence. Ops receives runtime and production problems. It is read-only, does not delegate, and has no authority to deploy, roll back, or write external state. Pass on only the context that the task needs, and never copy private conversations, credentials, or unrelated personal data. A partner must not expand the task. A partner may recruit other Agents only in these cases: Build Standard consults Architect, delegates to Fast, and opens module sessions, and Research Deep delegates to Research Fast. Any other gap goes back to the host.

- Create a partner session with `lody_session_create` and `agentRoleId`. The role decides the machine, Agent, and run configuration. Passing a model, permission mode, or reasoning effort by hand does not override the role. For other settings, select another suitable role. Do not assume that an override took effect.
- Before dispatch, confirm the actual working directory. `useCurrentSessionAsParent=true` shares the host's exact directory and gives no file isolation. Use it only when the target is really there and write ownership is clear. It cannot be combined with `workContext`. Tab rules are in [Lody Duo delegation](references/delegation.md).
- Each worktree has one writer. While a partner writes, the host does not change that scope. After the partner ends, the host verifies the result and then takes over. Enable independent parallel writers only when the task needs them. Isolate them first under `gmc` and the repository rules, and name the owner of the integration. Do not use `worktree:true` to bypass `gmc`.
- An independent session for a project task, including Review and Ops, must use a `workContext` that the catalog verified and that points to the actual local project or GitHub repository. An independent session is not a chat, and a new context does not mean no project. For a role on another machine, find the project on that machine, because an absolute path of the current machine does not work there. If you cannot find it, do not silently use another repository or a chat. Use `workContext:{kind:"chat"}` only for a task that really has no project.
- Open an independent review in a new private session that has no access to the author's reasoning. Give it the target, the raw materials, and the acceptance contract. Keep the verified project binding, and point to the target `gmc` worktree with an absolute path and `git -C`. Full access gives no read-only isolation for files. The host compares the target fingerprint and the workspace before and after the review. A write by the reviewer makes the review invalid. First verify the damage, then correct it.
- For a discussion or an investigation, the host forms its own judgment first and then asks a partner to refute it. Use targeted cross-checks only for disagreements that change the conclusion. Independent review uses the applicable contract of [liability-review](../liability-review/SKILL.md). A recheck in the implementer's original session is not an independent pass.

Use `lody_session_chat` to continue accepted investigation, implementation, and corrections in the same partner session. Use a new context only for independent review. Keep one owner for a single goal. Use batch tools only for independent work with a clear benefit, and accept each item separately.

## Single-layer Deep and Fast delegation

The host or a lead (Build Standard or Research Deep) must read [Lody Duo delegation](references/delegation.md) before it delegates to a partner or receives a handoff from one. Follow the section with the same name. It covers Tabs and independent sessions, the "in progress" report and the final evidence packet, Fast delegation and its verification, and the format of partner links.

## Parallel modules

Suppose one development goal splits into two or more modules, each module needs its own investigation and implementation judgment, and each file has exactly one owner. The lead Build Standard then develops and integrates the modules in parallel as described in the "Parallel modules" section of [Lody Duo delegation](references/delegation.md). A Build Standard that works on a module only stages its changes. It does not commit, push, deliver, or open another Build Standard.

## Async execution and recovery

Give every dispatch or continuation a unique `operationId`. Link it to the task, the target, the version, the input, and the partner `sessionId`. Transport recovery of the same request keeps the original ID. A correction or an added task gets a new ID. Never use one ID for different input. Never change the ID to resend after a lost response.

Create and chat operations are asynchronous by default. After Lody accepts a request, continue independent work and wait for the automatic completion notification. Do not poll `operation_get`. Do not use the legacy `wait` option or timed questions. A notification reports only the result of the execution. The host still accepts the result.

Follow the [recovery rules](references/delegation.md#recovery-rules) after a lost response, an error, a timeout, a host recovery, a cancel request, or a late or duplicate completion notice. For an addition or withdrawal while a partner turn runs, see [Continuation and cancellation](references/delegation.md#continuation-and-cancellation).

For work that has several phases or can cross contexts, keep one lightweight task artifact. Record the operation IDs, the partner entry points, the write ownership, the result locations, the acceptance state, and the open items. Respect the artifact locations and read-only boundaries, and keep review records outside the repository. Do not copy whole Lody sessions or build a separate dispatch database.

### Partner archiving

Follow [Partner archiving](references/delegation.md#partner-archiving) for archiving and reporting.

## Session and Tab titles

Every opened session and Tab that you create through an Agent Role uses the title `[Role name] Task title`. Examples: `[Build Standard] Implement Export Command`, `[Architect] Review Migration Design`, `[Build Fast] Add Export Flag`. The prefix is the full `name` of the catalog role selected for this creation, not a model name, an Agent name, or a guessed role.

- The dispatcher chooses the title before creation and puts the title requirement in the partner's task. When `lody_session_create` returns the `sessionId` of the created target, immediately name it with `lody_session_rename_many`. For batch creation, name each successful item that has a `sessionId`. The `label` of a batch create is not a session title.
- In its first turn, each role uses Lody MCP to check the actual title of its own session. If the title has no prefix for this role, add it. Keep only one role prefix. Keep a correct prefix and replace the prefix of another role. Do not add a prefix twice. A continuation with `lody_session_chat` does not rename the session. When the task title needs an update, keep the role prefix. Do not rename old sessions in bulk.
- A task title usually has 4 to 9 English words and keeps the exact names of projects, Issues, PRs, and products. Do not add status words such as WIP, Done, or Fixed. The role prefix does not count toward the word count. The full title must stay within the 200-character limit of the tool. If it is too long, shorten only the task part.
- Read back the actual title with `lody_session_status_many`. A statement from the model does not prove it. Correct a naming failure only on the same `sessionId`, without a new session or a new copy of the task. If it still fails, report the limitation and continue the authorized work that does not depend on the title.

## Acceptance and handoff

Build Standard delivers within the authority of the task, in its original session, and follows the repository's own delivery rules for commit, push, and PR. A Build Standard that works on a module never delivers.
The host accepts the final state of the delivery at its actual entrypoint, for example the PR state, the checks on the current head, and the merge evidence when a merge was authorized. If an authorized merge is blocked, require the blocker report and the ready state. A green PR that the owner did not ask to keep as a draft must be ready for review. If it is still a draft without an owner instruction, reject the result and correct it before you report to the owner.

Verify the partner's source citations, the execution evidence, and the actual results at the affected entrypoint. Agreement of models, a successful tool call, and an Operation marked succeeded do not replace acceptance. Correct concrete gaps yourself and reuse evidence that is still valid. When more discussion adds no new evidence, stop and use a method that verifies the facts.

Deliver the requested result, the acceptance evidence, the unverified boundaries, and the owner decisions. Give the Markdown link for each partner (format in the delegation reference) and the location of the task artifact. Do not invent CLI resume commands. Describe only checks that actually passed.

The user's absence does not end authorized work. Lody keeps durable records for accepted Operations. This skill cannot guarantee that machines stay online, that an external side effect runs exactly once, or that the host recovers across restarts. When the runtime limits the work, record the real execution state, the results, and the next steps. Do not claim that an unattended loop is complete.
