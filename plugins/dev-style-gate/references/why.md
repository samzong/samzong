# Why This Skill Looks Like This

This skill is intentionally narrow. The goal is not to automate maintainer
judgment away. The goal is to make a high-discipline review and shipping style
repeatable without retyping the same orchestration every time.

## 1. Explicit only

This workflow is expensive in attention, not in code. If it auto-triggers on
generic PR or issue language, it becomes noise and starts slowing down normal
work. The user asked for absolute control, so the skill only runs when named
explicitly. That keeps maintainer mode separate from everyday coding mode.

## 2. One gate at a time

A full automatic chain sounds efficient, but it removes the exact control that
matters here. The real value is in deciding when to stop, when to go deeper, and
when a technically valid fix still is not worth shipping. That is why the skill
never auto-advances. Each mode ends with a short verdict and waits.

## 3. The skill owns decisions, not shipping

Shipping already has its own flow. Repeating commit and PR mechanics inside this
skill would create overlap and confusion. This skill answers whether the work is
sound, aligned, and worth landing. A separate ship flow can still handle commit,
push, and PR creation after the maintainer has decided to proceed.

## 4. A live case file beats a generic handoff

Generic handoffs are broad and usually written near the end of a session. That
is useful for open-ended work, but this workflow is narrower and more specific.
The case file is a live artifact that stays current throughout the task. It is
meant to be read by a new conversation or another LLM before they start
reasoning, not reconstructed from memory after the fact.

## 5. Root-level file, one task, one file

The file lives in the worktree root on purpose:

- it is trivial to find
- it travels with the worktree
- it disappears with the worktree after merge
- it does not need repo-level structure or a persistent tracker

One task gets one file because the task needs a single current source of truth.
Multiple files per task force later sessions to reconcile competing narratives.

## 6. Not `todo.md`

`todo.md` is for planned work or agreed execution structure. Live state is
messier: verdicts change, dead ends appear, review comments get invalidated,
scope boundaries tighten, and verification evidence arrives late. Mixing that
into `todo.md` pollutes the plan and makes the plan less trustworthy.

## 7. Status transitions, not command logging

Logging every command creates a long transcript that nobody wants to read.
What matters across sessions is the state machine:

- what stage the task is in
- what the current verdict is
- what evidence changed that verdict
- what should happen next

That is why the file updates on transitions and meaningful evidence, not on
every shell action.

## 8. Rejected paths are first-class

The most expensive repeated mistake in cross-session work is retrying something
that was already disproven. A good case file records not only what worked, but
also what was tried and rejected. That protects future sessions from redoing the
same dead-end analysis.

## 9. Short structured output

The skill outputs `Verdict`, `Why`, `Missing evidence`, and `Next action`
because those are the smallest fields that still preserve judgment. Anything
less loses the reasoning. Anything more becomes essay-writing and defeats the
speed advantage.

## 10. No scripts in v1

The first problem is protocol drift, not keystroke count. A written protocol and
a stable template are enough to test whether the workflow is correct. Scripts
can come later if a repeated manual step is still painful after the protocol is
proven useful.

## Bottom line

This design keeps the expensive part human and the repeatable part explicit. It
gives the user a stable, local, task-scoped memory file and a disciplined gate
sequence without turning the workflow into an opaque autopilot.

