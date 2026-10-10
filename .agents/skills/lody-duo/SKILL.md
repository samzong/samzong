---
name: lody-duo
description: Coordinate investigation, implementation, and independent review through Agent Roles in Lody. Use when the user invokes lody-duo or asks you to select roles, delegate, and complete a task within Lody; use Lody MCP for dispatch and recovery.
---

# Lody Duo

The current session is the host. Keep responsibility for the goal, technical judgment, authorization, verification, and completion; do not switch the host's model. Select a Lody partner for a concrete gap. The user assigns the task rather than managing roles, models, or sessions. Build Standard leads development by default, consulting Build Deep or delegating to Build Fast when useful. Change partners when the phase requires it; there is no fixed pipeline or requirement to run every role.

## Hosting and authorization

- Establish the goal, scope, authority, and acceptance conditions from the task, prior decisions, and actual workspace. Read applicable user and repository `AGENTS.md` instructions, use relevant available skills, and reuse valid evidence. Background discussion is not implementation authorization.
- Assume the user may be absent. Advance authorized investigation, implementation, verification, correction, and delivery without asking for confirmation at every stage. The host resolves routine technical choices and failures.
- Return only owner decisions that change the goal, scope, product semantics, authority, or material risk. Finish independent authorized work first, show concrete results, and include pending decisions in the handoff. Actions depending on a decision wait for an explicit answer. Absence, timeout, and silence do not grant new authority.
- Full access, Bypass permissions, and Always Approve describe tool capabilities, not additional business authority. Follow the runtime's approval rules. Do not bypass required checks, approve requests on the user's behalf, or extend the task to merging, releasing, deploying, or external messages without authorization.

## Run only within Lody

Before using this workflow, call `lody_session_create_options` and confirm the current `sessionId`, `workspaceId`, `machineId`, and execution context. Resolve tool namespaces in the active runtime. Current tool descriptions and schemas are authoritative; this skill does not duplicate them.

Native subagents that inherit the host's Lody tools do not thereby gain an independent Lody host session. The tools belong to the session returned by Lody. The actual Lody host must dispatch, receive automatic notifications, and accept results; a native subagent returns bounded work without assuming notifications will reach it.

Install this skill together with the sibling [gmc](../gmc/SKILL.md) and [liability-review](../liability-review/SKILL.md) skills. The `gmc` CLI is an external tool and must be available for worktree operations; installing these skills does not install it.

If the current Lody session or necessary tools or skills are missing, report the missing capability and continue authorized work that does not depend on it. Do not silently switch to another orchestration system, launch partner CLIs directly, or claim a background task was accepted. This skill does not provide an outside-Lody fallback.

## Select roles

Discover available workspace roles with `lody_agent_role_list`, following pagination when needed. Read each selected role with `lody_agent_role_get` and verify its responsibilities, machine, agent configuration, model, reasoning effort, permissions, and availability. Names are discovery hints; dispatch with the stable `id` returned by the catalog. Never hardcode machine-specific IDs or create or modify roles to make a task fit.

The table is a reference division of responsibilities. Required roles must already be supplied by the user's workspace catalog; installing this skill does not install or create roles. Agent, model, and reasoning settings can change, so verify the current catalog. Explicit user choices of role, agent, and model take priority when selecting a compatible role.

| Role | Suitable work |
|---|---|
| Research Fast | Defined searches, source checks, and narrow code location tasks |
| Research Deep | Unknown root causes, causal analysis across modules, architectural trade-offs, and refutation |
| Build Fast | Bounded implementation or execution with a settled approach and acceptance conditions |
| Build Standard | Development lead: investigation, design judgment, primary implementation, Fast delegation, integration, and verification |
| Build Deep | Read-only consultation on specific difficult designs, module boundaries, or high-consequence choices; bounded implementation only when explicitly assigned |
| Review Fast | Independent read-only review of routine, low-risk targets |
| Review Deep | Independent review of persistence, security, money, concurrency, public contracts, or irreversible changes |

Classify the task after reading the request and critical materials, before dispatch. Judge changed behavior and consequences rather than file count, line count, or technical vocabulary. A Fast partner's escalation supplements this judgment; it does not replace the host's duty to identify unresolved or high-consequence boundaries.

Build Fast returns unsettled designs or complex boundaries to Build Standard. Complexity alone does not transfer the whole development task to Build Deep. Before changing partners, confirm that the previous partner has ended and verify its side effects; hand over the concrete remaining gap and completed work. Do not give two partners the same write scope. If a required role or user-selected configuration is missing, unavailable, or incompatible, report the actual limitation. Do not silently substitute a model, machine, permission mode, or Build Deep for Build Standard.

## Build Standard's development responsibility and design consultation

The host assigns the complete development goal to Build Standard, which owns investigation, design judgment, primary implementation, integration, verification, and authorized delivery. The host need not dispatch each implementation step and must not also assign Build Deep the same goal. A clearly defined, very small independent task can go directly to Build Fast without another scheduling layer.

- Build Standard first reads code, callers, actual runtime or data, existing changes, and acceptance conditions. Compare the existing path with the strongest simpler alternative and decide routine technical questions independently. Build Standard retains cross-module and high-consequence work. Consult Build Deep only for a specific design uncertainty that affects the choice, a contradiction unresolved by investigation, or a proposal needing independent refutation. Do not consult a particular model for every task or hand off all log analysis, routine implementation, testing, and integration.
- A consultation supplies one concrete question, necessary raw materials and versions, constraints, candidate approaches, and unknown facts that decide between them. Build Deep is read-only by default: return a recommendation, strongest alternative, evidence, failure paths, and verification method; do not change source or Git state or delegate again. Build Standard verifies the advice and implements it. A consultant who helped design a solution cannot provide its independent passing review.
- Build Deep implements a bounded part only when the host or Build Standard explicitly assigns a write scope and acceptance conditions. Before transferring write ownership, confirm that the previous writer has ended, has no relevant queued turns, and has verified results. A consultation completion notification is not implementation authorization. Build Standard remains responsible for the whole development task.
- Delegate to Build Fast when the goal, scope, approach, and acceptance conditions are clear and handoff plus verification offers a real benefit. Build Standard retains primary implementation, unsettled designs, cross-module boundaries, high-consequence parts, integration, and final verification. Do not fragment work merely to increase delegation. Run a deterministic one-command check yourself.
- After self-testing, the host selects a fresh Review session for independent review. Consultation, self-testing, and Fast reports do not replace that review. Build Standard normally corrects findings in its original session rather than reassigning the whole task to Build Deep.

## Dispatch and working directories

Every assignment includes the goal, input locations and versions, accepted decisions, authority and write scope, required result, and acceptance evidence. Share only context needed for the task, excluding credentials, private conversations, and unrelated personal information. Partners must not expand the task. Partners may delegate only through Build Standard's Build Deep consultation and Build Fast delegation, or Research Deep's Research Fast delegation; other gaps return to the host. Respect any narrower user or runtime delegation limits.

- Create a partner with `lody_session_create` and `agentRoleId`. The role determines machine, agent configuration, and run settings. Manual model, permission, or reasoning fields do not override it. If different settings are needed, select a suitable role within the user's authority; do not assume an override took effect.
- Verify the actual working directory before dispatch. `useCurrentSessionAsParent=true` shares the current session's exact directory; it provides no file isolation. Use it only when the target is actually there and write ownership is explicit. It is mutually exclusive with `workContext`. Do not infer the write location from defaults.
- Allow one writer per worktree. While a partner writes, the host does not modify that worktree. Verify the partner's completed work before taking ownership back. Enable parallel writers only when the task needs them: first isolate worktrees using `gmc` under the user's and repository's lifecycle rules and assign integration ownership. Lody's `worktree:true` must not bypass those rules.
- Use a catalog-verified `workContext` for an independent project session. For a role on another machine, discover the actual project on that machine. A local absolute path does not establish remote access. If the project cannot be found, do not silently switch repositories or use a blank chat to implement the task.
- Review in a fresh independent session without the author's reasoning. Keep review transcripts private unless the user authorizes sharing. Supply the target, raw materials, and acceptance contract. `workContext:{kind:"chat"}` can establish an independent session that accesses a verified same-machine path under a read-only assignment. Full access does not enforce file read-only isolation; compare target fingerprints and workspace state before and after review. Unauthorized writes invalidate the review; inspect damage before correction.
- For discussion and investigation, form the host's own judgment first, then ask a partner to refute it. Use targeted cross-checks only for disagreements that affect the conclusion. Independent review uses the full applicable contract of [liability-review](../liability-review/SKILL.md), including its T2 refutation and finder passes when required. Rechecking in the implementer's original session cannot provide independent acceptance.

Continue accepted investigation, implementation, and corrections with `lody_session_chat` in the same partner session. Use fresh context for independent review. Normally keep one partner; use batch tools only for independent work with a clear benefit. Accept each item separately: one successful item does not prove the whole batch succeeded.

## Single-layer Deep and Fast delegation

Build Standard is the development lead; Research Deep is the investigation lead. In this section, both are called leads. Build Standard may consult Build Deep and delegate to Build Fast. Research Deep may delegate only to Research Fast. Build Deep, Review, and Fast roles do not delegate. Assigning a lead under this skill grants these bounded delegation permissions, subject to the caller's actual authority and runtime limits. Leads follow the same dispatch, directory, async, and recovery rules and verify role IDs in the catalog before dispatch.

Lody has two session relationships. A Tab (`useCurrentSessionAsParent`) belongs to its creating session and shares its directory; a Tab cannot create another Tab. An opened session with explicit `workContext` is independent and has its own working context. The host opens a lead as an independent session with `workContext`, rather than as a Tab. That lead may create same-directory Fast or read-only Build Deep consultant Tabs; those Tabs cannot recruit partners. If the current lead is already a Tab, return the dispatch need to the host rather than attempting nested Tabs or bypassing the delegation boundary. Use `workContext` for a partner that needs another directory and state its verified actual directory in the assignment. Continue the same subtask or design question with `lody_session_chat` in the original partner session. After dispatch, end the current turn when no independent work remains: automatic completion is delivered when the lead has no active turn, so waiting within a turn delays delivery.

- Fast receives only tasks with a clear goal, scope, settled approach, and acceptance conditions. Research Deep delegates useful search, location, and fact checks to Research Fast; Build Standard uses the development boundaries above. Clarify unresolved work yourself before dispatching it to Fast.
- There is no fixed Fast partner count. Read-only Research Fast tasks may run in parallel when independent. Build Fast still obeys one writer per worktree: dispatch sequentially in the same worktree; when parallel writes are needed, Build Standard first uses `gmc` to create a separate worktree for each Fast under the user's and repository's lifecycle rules and owns integration.
- Each assignment specifies the goal, input version, directory verified in Fast's actual environment, unique write scope, settled approach, acceptance commands, and a report of roughly 20 lines or fewer. Require commands actually executed and key outputs. Treat conclusions without execution evidence as incomplete. Delegate no more authority than you received. Fast must not push or open PRs; it may make a local commit only when explicitly assigned to do so in its own isolated worktree.
- Do not accept Fast's prose as execution evidence. The lead reruns conclusion-critical checks and individually verifies diffs and cited locations. Lody's visible session history is not a substitute for raw tool-execution evidence; commands and outputs quoted in reports are leads to verify. Negative claims such as "not found," "cannot access," or "no tools" require execution evidence too. Without evidence, mark the task incomplete and continue with a bounded correction or do it yourself. Fast reasoning effort must be at least `high` as an evidence-reliability constraint; this setting does not guarantee correctness or replace verification. If the catalog cannot provide a compatible Fast role, report the limitation rather than silently lowering effort or changing configurations. The original lead takes over work beyond Fast's capability. Build Standard decides whether specific design consultation is needed; it does not automatically transfer the task to Build Deep.
- The lead's handoff lists every partner's `session://` link, `operationId`, and verification conclusion. For consultation, include which advice was adopted or rejected and why. The host checks for unauthorized delegation, write conflicts, unverified Fast results, and consultants presented as independent reviewers.

## Async execution and recovery

Assign a unique `operationId` to every new dispatch or continuation. In the current task record, associate it with the task unit, target, version, input, and partner `sessionId`. Transport recovery of the same request retains its ID; corrections or additional tasks receive a new ID. Never reuse an ID for changed input or create a new ID merely to resend after a lost response.

Create and chat operations are asynchronous. After acceptance, continue independent work and wait for Lody's automatic completion notification. Do not poll `lody_operation_get`, use legacy `wait`, or send timed repeat questions to keep the task alive. A notification reports execution of the accepted task; it does not establish acceptance of its result.

- After a lost response, timeout, or host recovery, use an occasional `lody_operation_get` or `lody_operation_list`, together with `lody_session_status_many` and, when needed, `lody_session_history`, to verify the original request, queue, target turn, and side effects. Operations are owned by the invoking session; do not assume another session can recover them. Paginate history only as needed and avoid exporting unrelated transcripts.
- Resume an accepted create using the original `operationId` and `resume:true`, without resending the prompt. Do not apply create's `resume` rule to chat, which has no such field. Follow the current tool's identity and recovery contract; verify acceptance and effects before any replay.
- Timeout, successful cancellation, an offline machine, or missing output does not prove the partner stopped. Operation cancellation finishes the Operation while target-turn cancellation is best-effort. Before resending or taking over the same write scope, verify that execution has ended, no relevant turns remain queued, and write results have been inspected. Without that evidence, retain uncertainty and continue independent work.
- For late or duplicate completion notifications, reconcile the task record and reuse accepted results; do not restart a completed goal. Do not archive a running partner to clean it up. Archiving a parent cascades to its Tabs, and pending deliveries remain pending until a human restores the session.

For multi-stage work or work spanning contexts, maintain one lightweight task artifact containing operation IDs, partner entrypoints, write ownership, result locations, acceptance, and unresolved items. Respect the task's artifact locations and read-only boundaries; review records stay outside the repository. Do not copy entire Lody conversations or build a separate scheduling database.

## Session and Tab titles

New opened sessions and Tabs created through an Agent Role use `[Role name] Task title`, such as `[Build Standard] Implement Project Export Command`, `[Build Deep] Evaluate Project Migration Design`, or `[Build Fast] Add Project Export Flag`. Use the selected catalog role's full `name`, not a model name, agent name, or guessed role.

- Before creation, choose the role prefix and task title and include the title requirement in the assignment. When `lody_session_create` returns the new `sessionId`, immediately name it with `lody_session_rename_many`. For batch creation, name every successful item with a returned `sessionId`. A batch `label` is not a session title.
- In its first turn, each role checks its current session ID and actual title through Lody MCP. Add its role prefix if missing; keep exactly one role prefix, preserving a correct prefix and replacing a different one. Do not rename on later `lody_session_chat` continuations. Retain the role prefix when an authorized task-title update is needed. Do not batch-rename historical sessions.
- Task titles normally contain 4–9 English words, retaining exact project, Issue, PR, and product names. Omit status words such as WIP, Done, and Fixed. The prefix does not count toward the word count. Keep the entire title within the tool's 200-character limit; shorten only the task portion if necessary.
- Read back actual titles with `lody_session_status_many`; a model's claim does not prove naming succeeded. Correct a naming failure only on the same created `sessionId`, without creating a replacement session or resending the task. If naming still fails, report the concrete limitation and continue authorized work that does not depend on it.

## Acceptance and handoff

Verify partner source citations, execution evidence, and actual results at the affected entrypoint. Model agreement, a successful tool call, and an Operation marked succeeded do not prove the requested outcome. Correct concrete gaps autonomously and reuse still-valid evidence. When further discussion adds no evidence, stop repeating it and use a method that verifies the facts.

Deliver the requested result, acceptance evidence, unverified boundaries, and owner decisions. Include each partner's `[Session title](session://sessionId)` entrypoint and the task artifact location when one exists. Do not invent CLI resume commands. Describe only checks that actually passed. Complete the task only when the accepted outcome and required gates are satisfied; otherwise report the exact remaining work and real execution state.

The user's absence does not end authorized work. Lody maintains durable records and completion notifications for accepted Operations. This skill organizes tools and authority; it cannot guarantee continuous machine availability, exactly-once execution of arbitrary external side effects, or automatic host recovery across restarts. Under runtime limits, preserve actual execution state, results, and next steps rather than claiming an unattended workflow completed.
