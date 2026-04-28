---
description: 判断变更是否值得合并
argument-hint: "[PR, diff, or current change]"
allowed-tools: Read, Grep, Glob, Bash(git:*), Edit, AskUserQuestion
---

Read `${CLAUDE_PLUGIN_ROOT}/shared/protocol.md` before acting.

Raw arguments:
`$ARGUMENTS`

Run only the `merge-value` gate.

Rules:

- If re-running (decision log already has a merge-value entry), show previous
  verdict for comparison.
- Set status to `merge-value`.
- Append decision log entry.
- Apply the Source-Backed Maintainer Review Lens from the protocol before
  deciding value.
- Explicitly separate:
  - upstream-baseline gap or redundancy
  - implementation correctness
  - owner/boundary fit
  - security, data-access, permission, supply-chain, and public-contract impact
  - tests/docs/changelog evidence
  - maintenance cost
  - best possible solution
  - remaining risk/open question
- Do not treat unrelated base CI failures as merge blockers unless the diff
  introduced or touched the failing surface.
