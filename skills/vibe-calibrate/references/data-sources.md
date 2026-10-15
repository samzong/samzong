# Data Source Reference

## Claude Code Sessions (primary)

Location: `~/.claude/projects/<project-key>/<session-uuid>.jsonl`

Each project directory is named after its working directory path with `/` replaced by `-`.
Each session is a JSONL file named by its UUID. Subagent conversations are in
`<session-uuid>/subagents/agent-*.jsonl`.

Each line is a JSON object with a `type` field:
- `{"type": "user", "message": {"content": "..." | [{type: "text", text: "..."}]}, "timestamp": ...}`
- `{"type": "assistant", "message": {"content": [{type: "text", text: "..."}, {type: "tool_use", name: "...", input: {...}}]}}`

### Extraction snippets

```python
import json
with open(filepath) as f:
    for line in f:
        d = json.loads(line)
        t = d.get('type', '')
        if t == 'user':
            msg = d.get('message', {})
            content = msg.get('content', '')
            if isinstance(content, str):
                text = content
            elif isinstance(content, list):
                text = ' '.join(c.get('text', '') for c in content if isinstance(c, dict) and c.get('type') == 'text')
        elif t == 'assistant':
            msg = d.get('message', {})
            content = msg.get('content', [])
            if isinstance(content, list):
                for c in content:
                    if isinstance(c, dict) and c.get('type') == 'tool_use':
                        tool_count += 1
```

## OpenCode SQLite

Location: `~/.local/share/opencode/opencode.db`

### Schema (observed on OpenCode v0.3, macOS, 2026-04-08)

If schema differs on your machine, probe via `sqlite3 <db> '.schema'` and adapt.

```sql
CREATE TABLE session (
  id TEXT PK, project_id TEXT, parent_id TEXT, slug TEXT, directory TEXT,
  title TEXT, version TEXT, share_url TEXT, permission TEXT,
  time_created INTEGER, time_updated INTEGER, time_archived INTEGER,
  workspace_id TEXT, ...
);

CREATE TABLE message (
  id TEXT PK, session_id TEXT FK, time_created INTEGER, time_updated INTEGER,
  data TEXT NOT NULL  -- JSON: {role, agent, model, mode, variant, cost, tokens, ...}
);

CREATE TABLE part (
  id TEXT PK, message_id TEXT FK, session_id TEXT FK,
  time_created INTEGER, time_updated INTEGER,
  data TEXT NOT NULL  -- JSON: {type: "text"|"tool"|"patch"|..., text?, tool?, state?, ...}
);
```

Key points:
- `message` has NO `role` or `content` columns — role is `json_extract(data, '$.role')`
- `session` uses `time_created` (integer epoch ms), NOT `created_at`
- User message text lives in `part.data` where `type="text"`, not in `message.data`

### Key queries (verified on schema above)

```sql
SELECT COUNT(*) FROM session;
SELECT COUNT(*) FROM message;
SELECT COUNT(*) FROM part;

SELECT json_extract(data, '$.role') as role, COUNT(*) as n
FROM message GROUP BY role;

SELECT json_extract(data, '$.tool') as tool,
       SUM(CASE WHEN json_extract(data, '$.state.status')='error' THEN 1 ELSE 0 END) as errors,
       COUNT(*) as total,
       ROUND(100.0 * SUM(CASE WHEN json_extract(data, '$.state.status')='error' THEN 1 ELSE 0 END) / COUNT(*), 1) as pct
FROM part WHERE json_extract(data, '$.type')='tool'
GROUP BY tool HAVING total > 10 ORDER BY errors DESC;

SELECT json_extract(p.data, '$.text') as txt
FROM part p JOIN message m ON p.message_id = m.id
WHERE json_extract(m.data, '$.role') = 'user'
  AND json_extract(p.data, '$.type') = 'text'
  AND length(json_extract(p.data, '$.text')) > 20
ORDER BY p.time_created DESC;

SELECT
  CASE
    WHEN cnt < 10 THEN '<10'
    WHEN cnt < 50 THEN '10-50'
    WHEN cnt < 100 THEN '50-100'
    ELSE '>100'
  END as bucket, COUNT(*) as sessions
FROM (SELECT session_id, COUNT(*) as cnt FROM message GROUP BY session_id)
GROUP BY bucket;
```

## Claude Code Settings

Location: `~/.claude/settings.json`

Key fields to audit:
- `permissions.defaultMode` — "bypassPermissions" removes all safety gates
- `permissions.allow` / `permissions.deny` — tool permission rules
- `env.CLAUDE_CODE_DISABLE_GIT_INSTRUCTIONS` — disables built-in git safety
- `effortLevel` vs `env.CLAUDE_CODE_EFFORT_LEVEL` — can conflict
- `hooks` — custom pre/post tool hooks

## Git History

```bash
# Commit type distribution
git log main --format="%s" | grep -oE '^[a-z]+' | sort | uniq -c | sort -rn

# Fix commits by scope
git log main --format="%s" | grep -oE 'fix\([^)]+\)' | sort | uniq -c | sort -rn

# PR stats (requires gh CLI)
gh pr list --state merged --limit 200 --json number,title,additions,deletions,changedFiles

# PR budget violations
# Filter: additions > 500 OR changedFiles > 30
```

## Codex Sessions

Location: `~/.codex/sessions/YYYY/MM/DD/rollout-*.jsonl`

Each line is a JSON object with `timestamp`, `type`, and `payload` fields:
- `{"type": "session_meta", "payload": {"id": "...", "cwd": "...", "cli_version": "..."}}` — session header
- `{"type": "event_msg", "payload": {"type": "...", "turn_id": "..."}}` — conversation events

Sessions are organized by date in a `YYYY/MM/DD/` directory hierarchy.

### Finding recent sessions

```bash
find ~/.codex/sessions/ -name "*.jsonl" -newermt "7 days ago" | sort
```

## Project Memory Files

Location: `~/.claude/projects/*/memory/*.md`

These contain accumulated learnings. Read all `feedback_*.md` files — they record
previous mistakes and user corrections, which are the most valuable signal.
