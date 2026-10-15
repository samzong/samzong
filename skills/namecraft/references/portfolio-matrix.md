# Agent Bench — Portfolio Matrix

Last updated: 2026-06-29

## Mother narrative

> **The Agent Bench** — a workbench where coding agents shape code, run in parallel, and leave strata beneath.
>
> **Workshop** tools shape and operate at the surface (lathe, gmc, mote).
> **Strata** tools preserve and dream underground (barrow).
> **Discovery** tools pick what to work on next (merge-scout → pending rename).
> **Signal** tools ping the engineer when the world changes (mailbell, branchlight).
> **Recall** bridges sessions across agents (recall).

CLI name = brand name. English only. ≤6 letters for core matrix projects.

## Story script (external pitch)

I build on **The Agent Bench**:

1. **lathe** shapes APIs into agent-safe CLIs — the first tool on the bench.
2. **gmc** runs parallel agents in parallel worktrees — many hands on the bench.
3. **barrow** sinks verified context into strata; sessions start with dreamed, source-backed memory.
4. **merge-scout** (rename pending: issora / landable / issue-pick) picks issues worth landing.
5. **recall** finds yesterday's session across Codex, Claude, and OpenCode.
6. **mailbell** and **branchlight** signal mail and GitHub from the menu bar.
7. **pinged** relays GitHub Issue/PR events into Feishu group webhooks you configure.
8. **mote** rewrites selected text in place — a small bench intervention.
9. **kitup** lets any CLI ship one bundled skill and install it across agent hosts.

Peripheral utilities (mm, mdctl, mirrormate, SaveEye) sit outside the core agent story unless promoted.

## Slot map

```
                    THE AGENT BENCH
                          │
     ┌────────────────────┼────────────────────┐
     │                    │                    │
 WORKSHOP              PARALLEL              STRATA
 (shape/run)          (many agents)        (memory/depth)
     │                    │                    │
  lathe ─────────────── gmc ─────────────── barrow
  mote                  (git wt)            (dream/prepare)
     │                    │                    │
     └────────────────────┼────────────────────┘
                          │
              ┌───────────┴───────────┐
              │                       │
          DISCOVERY                 SIGNAL
          (pick work)              (notify)
              │                       │
    merge-scout* ─── recall      mailbell
    (*rename TBD)               branchlight
                                pinged
```

## Core matrix (backfilled)

| Name | Letters | Lane | Slot | Status | One-line role |
|------|---------|------|------|--------|---------------|
| **lathe** | 5 | Bench craft | Workshop / Shaping | shipped | Shape API specs into Cobra CLIs agents can inspect |
| **gmc** | 3 | Bench (acronym) | Parallel | shipped | Git multi-agent worktrees + AI commits |
| **barrow** | 6 | Strata | Strata / Memory | skeleton | Local memory layer; strata preserve & dream context |
| **merge-scout** | 11† | Bench (flawed) | Discovery | shipped | Rank GitHub issues by contributability × merge probability |
| **recall** | 6 | Bench verb | Discovery / Bridge | shipped | Search all local AI coding sessions, cross-agent |
| **mailbell** | 8† | Signal compound | Signal | shipped | Gmail menu-bar notifier |
| **branchlight** | 11† | Signal compound | Signal | shipped | Quiet GitHub menubar hub |
| **mote** | 4 | Bench noun | Workshop / Intervention | shipped | Background macOS text rewrite |
| **pinged** | 6 | Bench verb-adj | Signal | v1 | GitHub webhook → Feishu custom bot relay (multi-repo) |
| **kitup** | 5 | Bench verb | Bridge / Craft | planned | Producer-side SDK for installing bundled CLI skills into local agent hosts |

† Exceeds ≤6 letter rule — **legacy names**. New projects must not add hyphen compounds >6 letters unless grandfathered. Renames should converge core matrix to ≤6.

### Rename queue (documented intent)

| Current | Candidates | Slot | Notes |
|---------|------------|------|-------|
| merge-scout | issora, landable, merito, pick† | Discovery | User decided issora 2026-05-06; not executed. pick npm taken. |
| mailbell | — | Signal | 8 letters; consider **bell** (check collision) if ever renamed |
| branchlight | — | Signal | 11 letters; consider **prism** / **beacon** if renamed |

## Peripheral projects (outside core story)

| Name | Role | Matrix note |
|------|------|-------------|
| mm | K8s/docs maintenance CLI | Utility; acronym OK for narrow tool |
| mdctl | Markdown AI workflow CLI | Pre-Bench; docs tooling |
| mirrormate | Docker mirror injection wrapper | Infra helper |
| SaveEye | macOS eye-care reminder | Health utility; not agent bench |
| GithubNotifier | (legacy?) | Superseded by branchlight narrative |
| hf-model-downloader | HF model fetch | Data tooling |
| codex-agents-local | Local codex config | Meta/dev |
| ConfigForge / forge-prototype | Experiments | Not in pitch |
| lathe-registry / homebrew-* | Distribution | Infrastructure for lathe/gmc |
| samzong | Personal meta | Portfolio root |
| **pared** | Minimal macOS video compression (FFmpeg, drag-drop) | Peripheral; craft-adjacent utility |
| **slype** | Private Mihomo + LaunchDaemon macOS proxy stack | Peripheral / Bridge; covered-passage infra beside mirrormate |
| **adit** | macOS session-index shell: ChatGPT/Grok web chats → local resumable note list (URL pointers, no body) | Peripheral / Bridge; Strata-textured "re-entry adit" (mine entrance), beside slype/pared. Was `voice-notes`. |

## Slot definitions (for new projects)

| Slot | Question it answers | Naming bias |
|------|---------------------|-------------|
| **Workshop** | How is raw material shaped for agents? | Craft nouns: lathe, die, tap |
| **Parallel** | How do many agents run without collision? | Short control words: gmc, fork |
| **Strata** | What persists underground across sessions? | Earth/memory: barrow, stele, lith |
| **Discovery** | What should the agent work on next? | Verbs: pick, sift, land |
| **Signal** | What pings the human? | Alert nouns: bell, flare, ping |
| **Bridge** | How do tools/agents connect? | recall, span, link (≤6) |
| **Intervention** | Small in-place agent action? | mote, tap, nudge |

## Adding a new project

1. Pick slot (or propose new slot with justification).
2. Run namecraft full workflow.
3. Append row to **Core matrix** or **Peripheral**.
4. Update story script if core slot.
5. Record session in `naming-sessions.md`.
