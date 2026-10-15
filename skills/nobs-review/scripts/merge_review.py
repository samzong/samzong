#!/usr/bin/env python3
from __future__ import annotations

import argparse
import copy
from collections import Counter
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import list_round_ids, load_json, resolve_review_id, safe_float, to_round_id, write_json

SEV_ORDER = {"critical": 0, "high": 1, "medium": 2, "low": 3, "nit": 4}
_DET_RANK = {"high": 0, "medium": 1, "low": 2}
_SCOPE_RANK = {"local": 0, "cross-file": 1, "architectural": 2}


def normalize_auto_fix_threshold(threshold: dict) -> tuple[str, str]:
    if not isinstance(threshold, dict):
        threshold = {}
    req_det = str(threshold.get("determinism", "high")).lower()
    req_scope = str(threshold.get("scope", "local")).lower()
    if req_det not in _DET_RANK:
        req_det = "high"
    if req_scope not in _SCOPE_RANK:
        req_scope = "local"
    return req_det, req_scope


def is_auto_fixable(finding: dict, policy: dict) -> bool:
    """Return True iff the finding meets the auto_fix_threshold in policy."""
    if not isinstance(policy, dict):
        policy = {}
    req_det, req_scope = normalize_auto_fix_threshold(policy.get("auto_fix_threshold", {}))
    det_ok = _DET_RANK.get(finding.get("fix_determinism", "low"), 2) <= _DET_RANK.get(req_det, 0)
    scope_ok = _SCOPE_RANK.get(finding.get("fix_scope", "architectural"), 2) <= _SCOPE_RANK.get(req_scope, 0)
    return det_ok and scope_ok


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
            str(item.get("file", "")),
            str(item.get("line", 0)),
            str(item.get("title", "")).strip().lower(),
            str(item.get("detail", "")).strip().lower()[:160],
        ]
    )


def _normalized_severity(value: object) -> str:
    sev = str(value).lower()
    return sev if sev in SEV_ORDER else "low"


def _normalized_determinism(value: object) -> str:
    det = str(value).lower()
    return det if det in _DET_RANK else "low"


def _normalized_scope(value: object) -> str:
    scope = str(value).lower()
    return scope if scope in _SCOPE_RANK else "architectural"


def merge_duplicate_finding(prev: dict, cur: dict) -> dict:
    prev_conf = safe_float(prev.get("confidence", 0.0))
    cur_conf = safe_float(cur.get("confidence", 0.0))
    # Base fields (id, file, line, title, detail, etc.) come from the higher-confidence finding.
    merged = copy.deepcopy(cur if cur_conf > prev_conf else prev)

    prev_sev = _normalized_severity(prev.get("severity", "low"))
    cur_sev = _normalized_severity(cur.get("severity", "low"))
    merged["severity"] = prev_sev if SEV_ORDER[prev_sev] <= SEV_ORDER[cur_sev] else cur_sev

    prev_det = _normalized_determinism(prev.get("fix_determinism", "low"))
    cur_det = _normalized_determinism(cur.get("fix_determinism", "low"))
    # Conservative merge for auto-fix safety: if any reviewer is less deterministic, keep the lower determinism.
    merged["fix_determinism"] = prev_det if _DET_RANK[prev_det] >= _DET_RANK[cur_det] else cur_det

    prev_scope = _normalized_scope(prev.get("fix_scope", "architectural"))
    cur_scope = _normalized_scope(cur.get("fix_scope", "architectural"))
    # Conservative merge for auto-fix safety: if any reviewer reports wider scope, keep the wider scope.
    merged["fix_scope"] = prev_scope if _SCOPE_RANK[prev_scope] >= _SCOPE_RANK[cur_scope] else cur_scope

    # confidence: optimistic — if any reviewer is confident, keep the higher value.
    merged["confidence"] = max(prev_conf, cur_conf)

    return merged


def write_markdown(round_id: str, findings: list[dict], counts: Counter, auto_keys: set[str] | None = None) -> str:
    auto_keys = auto_keys or set()
    auto_count = sum(1 for f in findings if dedup_key(f) in auto_keys)
    out: list[str] = []
    out.append(f"# Merged Review: {round_id}")
    out.append("")
    out.append(f"- Total findings: **{len(findings)}**")
    out.append(
        f"- Severity: critical={counts.get('critical',0)}, high={counts.get('high',0)}, medium={counts.get('medium',0)}, low={counts.get('low',0)}, nit={counts.get('nit',0)}"
    )
    out.append(f"- Auto-fix candidates: **{auto_count}** / Human-review: **{len(findings) - auto_count}**")
    out.append("")
    out.append("## Findings")
    out.append("")

    if not findings:
        out.append("No findings.")
    else:
        for i, finding in enumerate(findings, 1):
            tag = " `[AUTO]`" if dedup_key(finding) in auto_keys else ""
            out.append(f"### {i}. [{finding.get('severity','low').upper()}] {finding.get('title','(no title)')}{tag}")
            out.append(f"- File: `{finding.get('file','')}`:{finding.get('line',0)}")
            out.append(f"- Category: `{finding.get('category','maintainability')}`")
            out.append(f"- Reviewer: `{finding.get('reviewer','')}`")
            out.append(f"- Fix determinism: `{finding.get('fix_determinism','low')}` / scope: `{finding.get('fix_scope','architectural')}`")
            out.append(f"- Detail: {finding.get('detail','')}".rstrip())
            out.append(f"- Suggested fix: {finding.get('suggested_fix','')}".rstrip())
            out.append("")

    return "\n".join(out).strip() + "\n"


def write_auto_fix_candidates(round_id: str, findings: list[dict], threshold: dict) -> str:
    out: list[str] = []
    req_det, req_scope = normalize_auto_fix_threshold(threshold)
    det_values = [name for name, rank in _DET_RANK.items() if rank <= _DET_RANK[req_det]]
    scope_values = [name for name, rank in _SCOPE_RANK.items() if rank <= _SCOPE_RANK[req_scope]]
    out.append(f"# Auto-Fix Candidates: {round_id}")
    out.append("")
    out.append(
        f"Findings with `fix_determinism in {{{', '.join(det_values)}}}` + `fix_scope in {{{', '.join(scope_values)}}}`."
    )
    out.append("Apply each fix, then re-run a new review round to verify:")
    out.append("```")
    out.append("python3 skills/nobs-review/scripts/run_review.py --round auto")
    out.append("python3 skills/nobs-review/scripts/merge_review.py --round latest")
    out.append("```")
    out.append("")

    if not findings:
        out.append("No auto-fixable findings.")
    else:
        for i, f in enumerate(findings, 1):
            out.append(f"## {i}. [{f.get('severity','low').upper()}] {f.get('title','')}")
            out.append(f"- File: `{f.get('file','')}`:{f.get('line',0)}")
            out.append(f"- Category: `{f.get('category','')}`")
            out.append(f"- Detail: {f.get('detail','')}".rstrip())
            out.append(f"- Fix: {f.get('suggested_fix','')}".rstrip())
            out.append("- Applied: [ ]")
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

    # Load policy for auto-fix classification.
    contract_path = root / "contract.json"
    policy = load_json(contract_path).get("policy", {}) if contract_path.exists() else {}

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
        deduped[key] = merge_duplicate_finding(deduped[key], item)

    merged_findings = sorted(
        deduped.values(),
        key=lambda x: (SEV_ORDER.get(str(x.get("severity", "low")), 9), str(x.get("file", "")), int(x.get("line", 0))),
    )

    counts = Counter([str(x.get("severity", "low")) for x in merged_findings])

    # Classify findings into auto-fixable vs human-review.
    keyed_findings = [(f, dedup_key(f)) for f in merged_findings]
    auto_keys = {key for f, key in keyed_findings if is_auto_fixable(f, policy)}
    auto_fixable = [f for f, key in keyed_findings if key in auto_keys]
    human_review = [f for f, key in keyed_findings if key not in auto_keys]
    merged = {
        "review_id": review_id,
        "round_id": round_id,
        "total_findings": len(merged_findings),
        "severity_counts": dict(counts),
        "sources": sources,
        "findings": merged_findings,
    }

    write_json(round_dir / "merged.json", merged)
    (round_dir / "merged.md").write_text(
        write_markdown(round_id, merged_findings, counts, auto_keys), encoding="utf-8"
    )
    (round_dir / "auto-fix-candidates.md").write_text(
        write_auto_fix_candidates(round_id, auto_fixable, policy.get("auto_fix_threshold", {})), encoding="utf-8"
    )
    (round_dir / "resolution.md").write_text(write_resolution(round_id, human_review), encoding="utf-8")

    # Keep latest pointers at review root for convenience.
    write_json(root / "merged-latest.json", merged)
    (root / "merged-latest.md").write_text(
        write_markdown(round_id, merged_findings, counts, auto_keys), encoding="utf-8"
    )
    (root / "auto-fix-candidates-latest.md").write_text(
        write_auto_fix_candidates(round_id, auto_fixable, policy.get("auto_fix_threshold", {})), encoding="utf-8"
    )
    (root / "resolution-latest.md").write_text(write_resolution(round_id, human_review), encoding="utf-8")
    (root / ".latest_round").write_text(round_id + "\n", encoding="utf-8")
    (out_dir / ".active_review_id").write_text(review_id + "\n", encoding="utf-8")

    print(f"Wrote: {round_dir / 'merged.json'}")
    print(f"Wrote: {round_dir / 'merged.md'}")
    print(f"Wrote: {round_dir / 'auto-fix-candidates.md'} ({len(auto_fixable)} items)")
    print(f"Wrote: {round_dir / 'resolution.md'} ({len(human_review)} items)")
    print(f"Updated latest: {root / 'merged-latest.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
