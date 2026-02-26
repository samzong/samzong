#!/usr/bin/env python3
from __future__ import annotations

import argparse
from collections import Counter
from pathlib import Path

from _common import list_round_ids, load_json, resolve_review_id, to_round_id, write_json

SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "nit": 4}


def resolve_merge_round_id(root: Path, round_arg: str) -> str:
    rounds_dir = root / "rounds"
    existing = list_round_ids(rounds_dir)

    # Merge treats auto as alias of latest to avoid UX foot-guns.
    if round_arg in {"latest", "auto"}:
        latest_file = root / ".latest_round"
        if latest_file.exists():
            value = latest_file.read_text(encoding="utf-8").strip()
            if value:
                return value
        if existing:
            return existing[-1]
        return ""

    return to_round_id(round_arg, usage="latest/auto/rNNN/NNN")


def dedup_key(item: dict) -> str:
    return "|".join(
        [
            str(item.get("severity", "")),
            str(item.get("file", "")),
            str(item.get("line", 0)),
            str(item.get("title", "")).strip().lower(),
            str(item.get("detail", "")).strip().lower()[:160],
        ]
    )


def write_markdown(round_id: str, findings: list[dict], counts: Counter) -> str:
    out: list[str] = []
    out.append(f"# Merged Review: {round_id}")
    out.append("")
    out.append(f"- Total findings: **{len(findings)}**")
    out.append(
        f"- Severity: critical={counts.get('critical',0)}, high={counts.get('high',0)}, medium={counts.get('medium',0)}, low={counts.get('low',0)}, nit={counts.get('nit',0)}"
    )
    out.append("")
    out.append("## Findings")
    out.append("")

    if not findings:
        out.append("No findings.")
    else:
        for i, finding in enumerate(findings, 1):
            out.append(f"### {i}. [{finding.get('severity','low').upper()}] {finding.get('title','(no title)')}")
            out.append(f"- File: `{finding.get('file','')}`:{finding.get('line',0)}")
            out.append(f"- Category: `{finding.get('category','maintainability')}`")
            out.append(f"- Reviewer: `{finding.get('reviewer','')}`")
            out.append(f"- Detail: {finding.get('detail','')}".rstrip())
            out.append(f"- Suggested fix: {finding.get('suggested_fix','')}".rstrip())
            out.append("")

    return "\n".join(out).strip() + "\n"


def write_resolution(round_id: str, findings: list[dict]) -> str:
    out: list[str] = []
    out.append(f"# Resolution Checklist: {round_id}")
    out.append("")
    out.append("Status: `pending` / `accepted` / `rejected`")
    out.append("")

    if not findings:
        out.append("No findings to respond.")
    else:
        for i, finding in enumerate(findings, 1):
            out.append(f"## Item {i}: {finding.get('title','(no title)')}")
            out.append(f"- Severity: `{finding.get('severity','low')}`")
            out.append(f"- Location: `{finding.get('file','')}`:{finding.get('line',0)}")
            out.append("- Status: `pending`")
            out.append("- Decision: ")
            out.append("- Reason: ")
            out.append("- Change ref (file/commit): ")
            out.append("")

    return "\n".join(out).strip() + "\n"


def main() -> int:
    ap = argparse.ArgumentParser(description="Merge normalized reviewer findings")
    ap.add_argument("--id", default="", help="Review id (optional if .reviews/.active_review_id exists)")
    ap.add_argument("--out-dir", default=".reviews", help="Review root dir")
    ap.add_argument("--round", default="latest", help="Round id: latest/auto/rNNN/NNN")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    review_id = resolve_review_id(out_dir, args.id)
    root = out_dir / review_id

    round_id = resolve_merge_round_id(root, args.round)
    if not round_id:
        raise SystemExit("no rounds found to merge")

    round_dir = root / "rounds" / round_id
    norm_dir = round_dir / "normalized"
    if not norm_dir.exists():
        raise SystemExit(f"normalized dir not found: {norm_dir}")

    all_items = []
    sources = []
    for p in sorted(norm_dir.glob("*.json")):
        data = load_json(p)
        reviewer = data.get("reviewer", p.stem)
        sources.append({"reviewer": reviewer, "file": str(p)})
        for finding in data.get("findings", []):
            item = dict(finding)
            item["reviewer"] = reviewer
            all_items.append(item)

    deduped: dict[str, dict] = {}
    for item in all_items:
        key = dedup_key(item)
        if key not in deduped:
            deduped[key] = item
            continue
        prev = deduped[key]
        if float(item.get("confidence", 0.0)) > float(prev.get("confidence", 0.0)):
            deduped[key] = item

    merged_findings = sorted(
        deduped.values(),
        key=lambda x: (SEV_ORDER.get(str(x.get("severity", "low")), 9), str(x.get("file", "")), int(x.get("line", 0))),
    )

    counts = Counter([str(x.get("severity", "low")) for x in merged_findings])

    merged = {
        "review_id": review_id,
        "round_id": round_id,
        "total_findings": len(merged_findings),
        "severity_counts": dict(counts),
        "sources": sources,
        "findings": merged_findings,
    }

    write_json(round_dir / "merged.json", merged)
    (round_dir / "merged.md").write_text(write_markdown(round_id, merged_findings, counts), encoding="utf-8")
    (round_dir / "resolution.md").write_text(write_resolution(round_id, merged_findings), encoding="utf-8")

    # Keep latest pointers at review root for convenience.
    write_json(root / "merged-latest.json", merged)
    (root / "merged-latest.md").write_text(write_markdown(round_id, merged_findings, counts), encoding="utf-8")
    (root / "resolution-latest.md").write_text(write_resolution(round_id, merged_findings), encoding="utf-8")
    (root / ".latest_round").write_text(round_id + "\n", encoding="utf-8")
    (out_dir / ".active_review_id").write_text(review_id + "\n", encoding="utf-8")

    print(f"Wrote: {round_dir / 'merged.json'}")
    print(f"Wrote: {round_dir / 'merged.md'}")
    print(f"Wrote: {round_dir / 'resolution.md'}")
    print(f"Updated latest: {root / 'merged-latest.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
