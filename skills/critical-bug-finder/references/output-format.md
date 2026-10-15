# Output formats

Load this file only when the user requested `--format json`.

## JSON schema

```json
{
  "scope": ["path/or/module"],
  "summary": "Found N qualifying bugs across M files",
  "critical_bugs": [
    {
      "severity": "CRITICAL or HIGH",
      "location": "file:line or exact symbol",
      "category": "crash|data-loss|security|deadlock|race|core-logic",
      "description": "one sentence",
      "trigger": "concrete trigger scenario",
      "why_fatal": "why the impact is severe",
      "suggested_fix": "minimal fix direction"
    }
  ],
  "not_checked": ["path or reason"]
}
```

Rules:

- Use the exact top-level keys shown above
- Keep `critical_bugs` empty when no qualifying bugs are found
- Keep every field factual and concise
- Do not add markdown fences unless the user asked for them
