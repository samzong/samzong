# Naming session archive

Decisions and near-misses. Agents must read this before proposing names in the same semantic space.

---

## Barrow (2026-06-05) — Grok session `019e953d`

**Product:** Local-first embeddable memory layer for Shell/CLI agents. Rust crate + CLI.

**User constraints:**
- Not "normal" — reject Memory/Recall/Store/Agent/Mem/Shell*
- Poetic, myth/literary, memory texture (traces, layers, preservation, dream)
- Liked: Aletheia (#1), Barrow (#7), Stele (#8)
- Include dream/consolidation metaphor
- ≤6 letters; fusion OK if natural
- GitHub zero conflict mandatory

**Rounds:**

| Round | Highlights |
|-------|------------|
| 1 | Wyrd, Leyline, Spindle, Vellichor, Khepri, Stele, Rhizome, **Barrow**, Arcanum, Palimpsest |
| 2 | Aletheia, Reliquary, Amber, Remnant, Palimpsest, Tracery, Barrow, Stele, Vellichor, Spindle |
| 3 | + Reverie, **Oneira**, Somnara, Alethebarrow, Reverstele, Somnolith, Oneirstele |
| 4 | Alethe, **Barrow**, Stele, Oneir, Somn, Aletir, Steir, Barve, Somir, Aletve |

**Rejected with reason:**

| Name | Why |
|------|-----|
| Oneira | `laguerric/Oneira` dreaming AI agent + Memory Store; oneira.dev dream journal + memory |
| Mnemos*, Vestige, Cairn, Conch, Sibyl, Coral, Anamnesis | Competitor / taken lexicon |
| Alethebarrow, Oneirstele, Somnolith | Too long |
| Aletheia (full) | Some agent usage (DeepMind Aletheia); Alethe (5) was safer short form |

**Winner:** **Barrow** (user: "那我就用 2" = round 4 #2)

**Metaphor:** Burial mound — quiet preservation; old sessions interred, excavated on recall. Dream = background `prepare` / consolidation (product term: "dream it").

**Post-name:** Landing DESIGN.md explicitly bans burial-mound *visuals*; metaphor stays in README/philosophy only.

---

## merge-scout → issora (2026-05-06) — Codex session `019dfc70`

**Product:** AI-first CLI; rank GitHub issues by contributability × merge probability.

**Prior name:** issue-lens → merge-scout (2026-03-30, commit d298556)

**User complaint:** merge-scout misleading — sounds like git merge tool; leaks implementation; user is picking issues not merging.

**Steipete lane explored:**
- **pick** — ideal verb, npm TAKEN
- issue-pick, winnow, pounce — winnow taken, pounce risky

**Audited survivors (npm + GitHub GREEN):**
- contrib-scout, issue-radar, issue-pick

**Poetic lane explored:**
- **merito** — Latin merit; maps to scoring formula
- **issora** — issue + ora (gold); zero collision on npm/GitHub/domains

**User decision:** issora (over merito — cleaner .io/.app, zero brand confusion)

**Status:** Rename planned 2026-05-06, **not executed** — repo still merge-scout.

**Runners-up worth keeping:**
| Name | Lane | Letters | Note |
|------|------|---------|------|
| issora | Strata-gold | 6 | User pick |
| landable | Bench verb-adj | 8† | "Will the PR land?" — exceeds 6 |
| merito | Strata | 6 | Merit scoring |
| issue-pick | Bench | 9† | steipete compound |
| pick | Bench | 4 | npm dead |

---

## HiClaw rename contest (2026) — Grok session `019e643c`

**Context:** Community rename for AgentTeams placeholder. User wanted winning entry, not GitHub post.

**User constraints:**
- Avoid Claw/Paw/Lobster
- No descriptive long names (AgentTeams, TeamOS)
- Metaphor must map 1:1 to Matrix Rooms + K8s governance + human-in-loop
- Enterprise/governance tone OK
- Short CLI

**Top recommendations:**
1. **Conclave** — locked room, high-stakes visible decision (winner pitch)
2. Quorum — governance, human must be present
3. Aperture — visibility + control
4. Cabinet — executive team structure

**Avoid:** team/crew/swarm/hive (oversaturated)

**Note:** Different product domain than Agent Bench, but shows user values **governance metaphor precision** and **contest-grade storytelling**.

---

## Pared (2026-06-17) — Grok session `019ed3e9`

**Product:** Minimal native macOS app. Drag a video, preview two compression sizes (smallest vs visually lossless), one-click FFmpeg convert. Open source, MIT.

**Lane:** Peripheral utility (outside core Agent Bench matrix).

**User constraints:**
- Pure, minimal macOS app — no settings maze
- FFmpeg only, two presets: smallest file / keep quality
- Drag → preview sizes → convert → done
- ≤6 letters, great name, MIT OSS

**Audited survivors:**

| Name | npm | gh semantic | crate | Verdict |
|------|-----|-------------|-------|---------|
| **pared** | GREEN | GREEN | GREEN | **Winner** |
| wisp | RED (taken) | GREEN | GREEN | Runner-up |
| snug | RED (taken) | GREEN | GREEN | Runner-up |
| lithe | RED (taken) | GREEN | GREEN | — |
| heft | RED (taken) | GREEN | GREEN | — |

**Winner:** **pared** (5 letters)

**Metaphor:** *Pared down* — stripped to essentials; matches the one-window, two-button product shape.

**Repo:** `~/git/samzong/pared`

---

## Slype (2026-06-21) — Grok session (proxy-config rename)

**Product:** Local private macOS proxy stack — Mihomo config, LaunchDaemon plists, install/reload/verify scripts, runbooks. Decoupled from Clash Verge Rev profile regeneration.

**Prior name:** proxy-config (descriptive, >6 letters with hyphen, implementation leak)

**Lane:** A — architectural / Strata-adjacent metaphor (covered passage)

**Matrix slot:** Peripheral / Bridge (personal network plumbing; beside mirrormate)

**User constraints:**
- ≤6 letters; English only; no proxy/mihomo/clash in name
- Private infra repo; sensitive config stays local
- User confirmed **slype** and requested clean slate (README + .gitignore only) for restructure

**Audited survivors:**

| Name | npm | crate | gh semantic | Verdict |
|------|-----|-------|-------------|---------|
| **slype** | GREEN | GREEN | GREEN (0 proxy hits) | **Winner** |
| bylane | GREEN | GREEN | GREEN | Runner-up |
| gusset | GREEN | GREEN | GREEN | Runner-up |
| outvia | GREEN | GREEN | GREEN (0 gh name hits) | Runner-up |
| kerf | GREEN | GREEN | RED (Kerf tick DB) | Dropped |
| tunly / shunt / flume | — | — | RED (proxy/tunnel sem) | Dropped |

**Winner:** **slype** (5 letters)

**Metaphor:** Covered passage — TUN tunnel + private repo + LaunchDaemon persistence; traffic through a wall-side corridor, not the GUI storefront.

**Repo:** `~/git/samzong/slype`

---

## pinged (2026-06-22) — Cursor session

**Product:** Cloudflare Worker relay: GitHub repo webhooks → Feishu custom bot webhooks (multi-repo, multi-channel). D1 config, hidden panel path.

**Lane:** B — Signal

**Matrix slot:** Signal (GitHub → Feishu group relay; complements branchlight)

**User decision:** pinged (accepted over peal, blare)

**Runners-up:** peal (4), blare (5)

**Audit notes:** npm GREEN for pinged; peal.dev YELLOW (307 redirect); domain spot check GREEN for pinged.dev

**Repo:** `~/git/samzong/pinged`

---

## adit (2026-06-23) — Claude Code session

**Product:** macOS chromeless Electron shell that aggregates ChatGPT/Grok web sessions into a local resumable note list. Each note = a session-URL pointer back into a live conversation. No chat UI, no ASR. (Working title `voice-notes`, dropped — descriptive compound, misleads as voice/ASR.)

**Lane:** A — Strata-textured / Peripheral macOS utility (beside pared, slype).

**Matrix slot:** Peripheral / Bridge.

**Audited survivors:**

| Name | npm | gh path | gh semantic | domain | Verdict |
|------|-----|---------|-------------|--------|---------|
| **adit** | taken (irrelevant, DMG) | FREE | **GREEN** (Aditya person-name repos + one low-profile Win remote tool) | parked YELLOW | **Winner** |
| seam | taken | FREE | YELLOW (seam.co API + repos) | GREEN (all NX) | Runner-up (accessible, clean domains) |
| caul | GREEN | FREE | GREEN | .app/.io free | Runner-up (sheath metaphor, clean) |
| spool | taken | FREE | YELLOW (print spooler/filament) | YELLOW | — |
| skein / lode | taken | FREE | YELLOW (Skein hash / lodestar) | YELLOW | — |

**Dropped (RED/near):** sill (SillyTavern owns the search, same LLM-chat space), stoa (stoat.chat product), quire (quire.io + Getty Quire).

**Cross-agent contender — volva (rejected):** another agent recommended `volva` (mushroom sheath = "thin shell wrapping native page"). Rejected here on two counts: (1) **phonetics** — near-homophone of *vulva*, plus Volvo sound-alike (consumer/App-Store liability the other agent under-flagged); (2) **names the wrapper (implementation), not the user value** (re-entry). `caul` offered as a strictly-cleaner same-family alternative.

**Winner:** **adit** (4 letters) — user picked over volva/seam/caul.

**Metaphor:** A mine *adit* is the horizontal tunnel you re-enter the underground workings through. Each note = a kept entrance back into a conversation that lives elsewhere; you store the adit, not the mine. On-brand with Strata worldview (barrow/slype register), zero phonetic landmines.

**Repo:** `~/git/samzong/adit`

**Steipete/ergonomics note:** clean as a future CLI too — `adit open <note>`, `adit list`.

---

## kitup (2026-06-29) — Codex session

**Product:** Producer-side cross-agent skill installer/update SDK for CLI authors. A CLI developer imports one package, points it at a bundled `SKILL.md` directory, and the SDK detects local agent hosts, installs/updates the skill, and writes host-specific paths without each CLI reimplementing 100+ adapters.

**Lane:** B — Bench verb / infrastructure.

**Matrix slot:** Bridge / Craft.

**User decision:** kitup.

**Audited survivors:**

| Name | npm | crate | gh path | domain | Verdict |
|------|-----|-------|---------|--------|---------|
| **kitup** | GREEN | GREEN | `samzong/kitup` free; GitHub user exists | `kitup.dev` Cloudflare Access | **Winner** |
| spile | GREEN | GREEN | repo free; GitHub user exists | no quick site | Runner-up |
| sneck | GREEN | GREEN | repo free; GitHub user exists | no quick site | Runner-up |
| snib | GREEN | GREEN | repo free; GitHub user exists | `snib.io` blockchain site | Runner-up |
| kitbag | GREEN | GREEN | repo free; GitHub user exists | active domains | Runner-up |

**Dropped:** dowel, bodkin, linch, sley — Rust crate names taken or semantically noisy.

**Winner:** **kitup** (5 letters)

**Metaphor:** A CLI kits itself up with agent skills. Direct verb, easy CLI, and maps to the producer-side SDK boundary: ship one bundled skill, let the shared installer wire it into every supported agent host.

**Repo:** `~/git/samzong/kitup` planned.

---

1. ≤6 letters hard limit (user confirmed 2026-06-07)
2. Dual lane: Strata poetic vs Bench verb; shared Agent Bench worldview
3. Workshop + Strata materials coexist: bench produces → sinks underground
4. CLI = brand, no alias
5. Full collision audit before recommend
6. English only
7. Manual skill invoke only
8. Two-phase: diverge 15–20 → audit → top 5 → user decides
9. Record every decision in this file
