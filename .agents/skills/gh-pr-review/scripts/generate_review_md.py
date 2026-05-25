#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple


def _read_text(path: Path) -> str:
    return path.read_text(encoding="utf-8", errors="replace")


def _read_json(path: Path) -> Dict[str, Any]:
    return json.loads(_read_text(path))


def _truncate_lines(text: str, max_lines: int = 200) -> str:
    lines = text.splitlines()
    if len(lines) <= max_lines:
        return text.rstrip("\n")
    head = "\n".join(lines[:max_lines])
    return f"{head}\n... (truncated, total {len(lines)} lines)"


def _safe_get(d: Dict[str, Any], *keys: str, default: str = "") -> str:
    cur: Any = d
    for k in keys:
        if not isinstance(cur, dict) or k not in cur:
            return default
        cur = cur[k]
    if cur is None:
        return default
    return str(cur)


def _line_range(lines: List[Dict[str, Any]]) -> Optional[Tuple[int, int]]:
    if not lines:
        return None
    nums = [int(item["line"]) for item in lines if "line" in item]
    if not nums:
        return None
    return min(nums), max(nums)


def _render_files_overview(changed: Dict[str, Any]) -> str:
    files: Dict[str, Any] = changed.get("files", {}) if isinstance(changed, dict) else {}
    if not files:
        return "- (No changed files detected from diff.)"

    out: List[str] = []
    for path in sorted(files.keys()):
        hunks = files[path].get("hunks", [])
        added = sum(len(h.get("added", []) or []) for h in hunks)
        deleted = sum(len(h.get("deleted", []) or []) for h in hunks)
        out.append(f"- `{path}` (hunks: {len(hunks)}, +{added}, -{deleted})")
    return "\n".join(out)


def _render_file_reviews(changed: Dict[str, Any]) -> str:
    files: Dict[str, Any] = changed.get("files", {}) if isinstance(changed, dict) else {}
    if not files:
        return "_No changed files detected._"

    blocks: List[str] = []

    for path in sorted(files.keys()):
        hunks: List[Dict[str, Any]] = files[path].get("hunks", []) or []
        blocks.append(f"### `{path}`\n")

        if not hunks:
            blocks.append("_No hunks detected._\n")
            continue

        blocks.append("**Changed hunks (only these lines are in-scope for review):**\n")

        for idx, h in enumerate(hunks, start=1):
            header = h.get("header", "").strip()
            added_lines: List[Dict[str, Any]] = h.get("added", []) or []
            deleted_lines: List[Dict[str, Any]] = h.get("deleted", []) or []

            new_range = _line_range(added_lines)
            old_range = _line_range(deleted_lines)

            blocks.append(f"- Hunk {idx}: `{header}`")
            if new_range:
                blocks.append(f"  - New-side changed lines: `L{new_range[0]}-L{new_range[1]}`")
            else:
                blocks.append("  - New-side changed lines: (none)")
            if old_range:
                blocks.append(f"  - Old-side deletions: `L{old_range[0]}-L{old_range[1]}`")
            else:
                blocks.append("  - Old-side deletions: (none)")

            if added_lines:
                preview = []
                for item in added_lines[:10]:
                    content = str(item.get("content", "")).rstrip("\n")
                    preview.append(f"+ {content}")
                blocks.append("  - Added/modified preview:")
                blocks.append("```diff")
                blocks.extend(preview)
                if len(added_lines) > 10:
                    blocks.append(f"... (truncated, total {len(added_lines)} added lines in this hunk)")
                blocks.append("```")

            blocks.append("  - Review items:")
            example_line = added_lines[0]["line"] if added_lines else (new_range[0] if new_range else "?")
            blocks.append(f"    - `{path}:L{example_line}` — Verdict: `Accept | Nit | Request changes`")
            blocks.append("      - Suggested GitHub comment (EN):")
            blocks.append("        > TODO")
            blocks.append("      - Rationale (ZH): TODO")
            blocks.append("      - Proposed fix: TODO")

        blocks.append("")  # spacing between files

    return "\n".join(blocks).rstrip() + "\n"


def _render_checks_section(checks_text: str, failed_logs_text: str) -> str:
    checks_text = checks_text.strip()
    failed_logs_text = failed_logs_text.strip()

    out: List[str] = []
    # Best-effort: if checks output is JSON (e.g. statusCheckRollup), render a quick human summary.
    if checks_text.startswith("{") or checks_text.startswith("["):
        try:
            parsed = json.loads(checks_text)
            rollup = parsed.get("statusCheckRollup") if isinstance(parsed, dict) else None
            if isinstance(rollup, list) and rollup:
                total = len(rollup)
                by_conclusion: Dict[str, int] = {}
                for item in rollup:
                    conclusion = str(item.get("conclusion") or "NONE").upper()
                    by_conclusion[conclusion] = by_conclusion.get(conclusion, 0) + 1

                out.append("### Checks summary (parsed)\n")
                out.append(f"- Total: {total}")
                out.append(
                    "- By conclusion: "
                    + ", ".join(f"{k}={v}" for k, v in sorted(by_conclusion.items(), key=lambda kv: (-kv[1], kv[0])))
                )
                out.append("")
                out.append("| Name | Status | Conclusion | Workflow | URL |")
                out.append("| --- | --- | --- | --- | --- |")
                for item in rollup[:60]:
                    name = str(item.get("name") or "")
                    status = str(item.get("status") or "")
                    conclusion = str(item.get("conclusion") or "")
                    workflow = str(item.get("workflowName") or "")
                    url = str(item.get("detailsUrl") or item.get("targetUrl") or "")
                    out.append(f"| {name} | {status} | {conclusion} | {workflow} | {url} |")
                if len(rollup) > 60:
                    out.append(f"\n_... (truncated, total {len(rollup)} checks)_\n")
        except Exception:
            # Fall back to raw
            pass

    out.append("### Checks summary (raw)\n")
    out.append("```text")
    out.append(_truncate_lines(checks_text or "(no checks output)", max_lines=120))
    out.append("```\n")

    out.append("<details>")
    out.append("<summary>Failed job logs (raw, best-effort)</summary>\n")
    out.append("```text")
    out.append(_truncate_lines(failed_logs_text or "(no failed logs captured)", max_lines=160))
    out.append("```")
    out.append("</details>\n")

    out.append("### CI evaluation (to be filled)\n")
    out.append("- 是否有失败 job：TODO")
    out.append("- 失败是否与本 PR 修改相关：TODO（若相关，请指向具体文件/行并给出修复建议）")
    out.append("- 若无关：TODO（说明理由即可）")
    return "\n".join(out).rstrip() + "\n"


def render_template(template: str, variables: Dict[str, str]) -> str:
    out = template
    for k, v in variables.items():
        out = out.replace(f"{{{{{k}}}}}", v)
    return out


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--pr-json", required=True)
    parser.add_argument("--checks", required=True)
    parser.add_argument("--failed-logs", required=True)
    parser.add_argument("--changed-lines", required=True)
    parser.add_argument("--template", required=True)
    parser.add_argument("--output", required=True)
    args = parser.parse_args()

    pr = _read_json(Path(args.pr_json))
    changed = _read_json(Path(args.changed_lines))

    pr_number = _safe_get(pr, "number", default="")
    pr_title = _safe_get(pr, "title", default="")
    pr_url = _safe_get(pr, "url", default="")
    pr_author = _safe_get(pr, "author", "login", default=_safe_get(pr, "author", default=""))
    base_ref = _safe_get(pr, "baseRefName", default="")
    head_ref = _safe_get(pr, "headRefName", default="")
    head_sha = _safe_get(pr, "headRefOid", default="")

    checks_text = _read_text(Path(args.checks))
    failed_logs_text = _read_text(Path(args.failed_logs))

    template_text = _read_text(Path(args.template))
    generated_at = dt.datetime.now(dt.timezone.utc).astimezone().isoformat(timespec="seconds")

    files_overview = _render_files_overview(changed)
    file_reviews = _render_file_reviews(changed)
    checks_summary = _render_checks_section(checks_text, failed_logs_text)

    variables = {
        "PR_TITLE": pr_title or "(unknown title)",
        "PR_NUMBER": str(pr_number) if pr_number else "(unknown)",
        "PR_URL": pr_url or "(unknown url)",
        "PR_AUTHOR": pr_author or "(unknown author)",
        "BASE_REF": base_ref or "(unknown)",
        "HEAD_REF": head_ref or "(unknown)",
        "HEAD_SHA": head_sha or "(unknown)",
        "GENERATED_AT": generated_at,
        "SUMMARY_ZH": "TODO：用 3-6 句话概述这个 PR 改了什么、为什么改、风险点与是否建议合入。",
        "CHECKS_SUMMARY": checks_summary,
        "FILES_CHANGED_OVERVIEW": files_overview,
        "FILE_REVIEWS": file_reviews,
        "MERGE_RECOMMENDATION": "TODO（Recommend merge / Request changes / Neutral）",
        "BLOCKERS_ZH": "TODO（无则填：无）",
        "NON_BLOCKING_ZH": "TODO（无则填：无）",
    }

    out_text = render_template(template_text, variables)
    Path(args.output).write_text(out_text, encoding="utf-8")


if __name__ == "__main__":
    main()
