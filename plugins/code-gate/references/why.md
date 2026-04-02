# Why This Plugin Looks Like This

This plugin is narrow on purpose. The goal is to make a disciplined maintainer
workflow repeatable without taking judgment away from the user.

## Why commands, not one big mode parser

The user wants `/code-gate:init`, `/code-gate:feasibility`, and similar
commands because each gate is a distinct action with a hard stop. A single
command with a mode flag would technically work, but it weakens the command
surface and makes accidental full-flow behavior more likely.

## Why explicit only

This workflow is expensive in attention. If it auto-triggers on generic PR or
issue language, it becomes noise. It must be entered deliberately.

## Why one gate at a time

A full automatic chain sounds efficient, but it removes the exact control that
matters here. The real value is in deciding when to stop, when to go deeper, and
when a technically valid fix still is not worth shipping. Each gate ends with a
short verdict and waits.

## Why one live root-level case file

The case file is the continuity artifact for new sessions and other LLM tools.
It lives in the worktree root because it is trivial to find, tied to one task,
and removed with the worktree after the task is done.

## Why not `todo.md`

`todo.md` is for planned work. Live execution state is messier: verdicts change,
dead ends get disproven, and review feedback gets invalidated. Mixing them makes
both worse.

## Why status transitions, not command logging

Logging every command creates a long transcript that nobody wants to read.
What matters across sessions is the state machine: what stage the task is in,
what the current verdict is, what evidence changed that verdict, and what should
happen next.

## Why rejected paths are first-class

The most expensive repeated mistake in cross-session work is retrying something
that was already disproven. A good case file records not only what worked, but
also what was tried and rejected.

## Why no script layer yet

The first problem is protocol drift, not shell repetition. The command layer and
shared protocol are enough to prove the workflow shape. Runtime scripts can come
later if repeated manual steps remain painful.
