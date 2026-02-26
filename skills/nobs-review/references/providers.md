# Provider Command Templates

Use these as starting points in `contract.json -> reviewers[].command_template`.

Supported placeholders:
- `{prompt_file}`
- `{context_file}`
- `{raw_output_file}`
- `{json_output_file}`
- `{review_dir}`
- `{round_dir}`

Quoting contract:
- Placeholder values are shell-escaped by the runner before substitution.
- Do not add extra quotes around placeholders themselves.
- Example: use `cat {prompt_file}`, not `cat \"{prompt_file}\"`.

## Codex (high reasoning)

```bash
codex exec --model gpt-5 --reasoning high "$(cat {prompt_file})" > {raw_output_file}
```

## Claude (Opus)

```bash
claude --model opus --print "$(cat {prompt_file})" > {raw_output_file}
```

## Gemini (pro)

```bash
gemini --model gemini-2.5-pro --prompt-file {prompt_file} > {raw_output_file}
```

## JSON-safe local test

```bash
printf '%s\n' '{"reviewer":"local","summary":"ok","findings":[],"notes":[]}' > {raw_output_file}
```

## Advice

- Keep reviewer output to strict JSON only.
- For risky changes (auth, payments, migrations), enable at least 2 reviewers with high reasoning.
- Run additional rounds after fixes with the same review id (`--round auto`).
