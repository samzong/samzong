# Reject lexicon

Hard reject unless user explicitly overrides in intake.

## Category A — Normal / generic tech (Barrow session ban)

```
memory, recall, store, agent, mem, shell,
assistant, chatbot, brain, mind, vault, cache,
database, db, vector, embed, rag, llm, ai
```

Case-insensitive. Substring match on repo/crate name (e.g. `mem0` pattern — reject `mem*` roots for greenfield).

## Category B — Oversaturated agent metaphors

```
crew, swarm, hive, team, squad, orchestrator,
conductor, copilot, companion, buddy
```

## Category C — Known competitor collisions (extend as discovered)

```
mnemos, mnemo, vestige, cairn, conch, sibyl,
coral, anamnesis, eidolon, nautilus,
mem0, zep, letta, graphiti
```

## Category D — Claw family (when not fork of OpenClaw)

```
claw, paw, lobster, openclaw
```

Exception: contributing to OpenClaw upstream — different rules.

## Category E — Implementation leak patterns

Reject if name encodes internal algorithm the user never sees:

```
merge, probability, score, rank, bm25, vector, sqlite
```

Example: `merge-scout` rejected because user perceives "discover/pick" not "merge".

## Category F — Length / form

```
>6 letters
hyphens in primary name (merge-scout grandfathered only)
camelCase repo names
```

## Category G — npm / GitHub known dead (merge-scout session)

```
pick      — npm taken (deprecated lock)
winnow    — npm active package
oss-scout — semantic collision with OSS health tools
oneira    — dreaming AI agent + oneira.dev
```

Re-audit on every run; registry changes.

## Category H — Portfolio siblings

Reject confusable duplicates within Agent Bench:

```
Cannot add second Strata memory name without differentiating slot
Cannot add scout* if Discovery slot filled (until merge-scout renamed)
```

## Yellow flags (not auto-reject — note in audit)

- Real English word with unrelated famous product (merit → HR companies)
- Acronym opaque to newcomers (gmc OK — grandfathered)
- Pronunciation ambiguity (barve, aletve)
- Google DeepMind / big-tech project homonym (aletheia → prefer alethe)

## User override protocol

If user says "I want MemoryX anyway":
1. Warn with audit evidence
2. Require explicit "override reject lexicon" in intake
3. Log override in naming-sessions.md