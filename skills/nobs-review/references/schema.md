# Review JSON Schema (Practical)

Each reviewer should output JSON in this shape:

```json
{
  "reviewer": "codex_high",
  "summary": "short summary",
  "findings": [
    {
      "id": "COD-001",
      "severity": "high",
      "file": "src/app.ts",
      "line": 42,
      "title": "Missing auth check",
      "detail": "Route allows update without verifying ownership.",
      "suggested_fix": "Check owner_id against session user before update.",
      "confidence": 0.86,
      "category": "security"
    }
  ],
  "notes": ["Any extra notes"]
}
```

Rules:
- `severity`: one of `critical`, `high`, `medium`, `low`, `nit`
- `file`: repo-relative path
- `line`: integer >= 1, optional (use 0 if unknown)
- `confidence`: 0..1, optional
- `findings`: empty array if no issue

Round handling:
- Reviewer output does not need `review_id` or `round_id`.
- The orchestrator binds output to current `.reviews/<id>/rounds/rNNN/` automatically.
