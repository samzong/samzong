#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import re
import shlex
import subprocess
import time
from pathlib import Path

from _common import list_round_ids, load_json, now_utc, resolve_review_id, to_round_id, update_json, write_json

ALLOWED_SEVERITY = {"critical", "high", "medium", "low", "nit"}


def _to_float(v) -> float:
    return float(v) if isinstance(v, (int, float)) else 0.0


def resolve_execution_round_id(root: Path, round_arg: str) -> str:
    rounds_dir = root / "rounds"
    rounds_dir.mkdir(parents=True, exist_ok=True)
    existing = list_round_ids(rounds_dir)

    if round_arg == "auto":
        if not existing:
            return "r001"
        last = int(existing[-1][1:])
        return f"r{last + 1:03d}"

    if round_arg == "latest":
        if existing:
            return existing[-1]
        raise SystemExit("no existing rounds; use --round auto to start the first round")

    return to_round_id(round_arg, usage="auto/latest/rNNN/NNN")


def try_parse_json_blob(text: str):
    text = text.strip()
    if not text:
        return None
    try:
        parsed = json.loads(text)
        if isinstance(parsed, dict) and ("findings" in parsed or "reviewer" in parsed):
            return parsed
    except json.JSONDecodeError:
        pass

    decoder = json.JSONDecoder()
    for start in reversed([i for i, ch in enumerate(text) if ch == "{"]):
        try:
            obj, end = decoder.raw_decode(text[start:])
        except json.JSONDecodeError:
            continue
        if text[start + end:].strip() == "" and isinstance(obj, dict) and ("findings" in obj or "reviewer" in obj):
            return obj
    return None


def normalize_output(reviewer_id: str, data) -> dict:
    if not isinstance(data, dict):
        return {
            "reviewer": reviewer_id,
            "summary": "invalid output",
            "findings": [],
            "notes": ["Output is not a JSON object"],
        }

    findings = data.get("findings")
    if not isinstance(findings, list):
        findings = []

    normalized = []
    for i, f in enumerate(findings, 1):
        if not isinstance(f, dict):
            continue
        sev = str(f.get("severity", "low")).lower()
        if sev not in ALLOWED_SEVERITY:
            sev = "low"
        line = f.get("line", 0)
        if not isinstance(line, int) or line < 0:
            line = 0
        normalized.append(
            {
                "id": str(f.get("id") or f"{reviewer_id}-{i:03d}"),
                "severity": sev,
                "file": str(f.get("file", "")),
                "line": line,
                "title": str(f.get("title", "")),
                "detail": str(f.get("detail", "")),
                "suggested_fix": str(f.get("suggested_fix", "")),
                "confidence": _to_float(f.get("confidence", 0.0)),
                "category": str(f.get("category", "maintainability")),
            }
        )

    return {
        "reviewer": str(data.get("reviewer", reviewer_id)),
        "summary": str(data.get("summary", "")),
        "findings": normalized,
        "notes": data.get("notes", []) if isinstance(data.get("notes", []), list) else [],
    }


def render_command(template: str, **kwargs: str) -> str:
    pattern = re.compile(r"\{([a-z_][a-z0-9_]*)\}")

    def repl(match: re.Match[str]) -> str:
        key = match.group(1)
        if key not in kwargs:
            raise SystemExit(f"missing placeholder value: {{{key}}}")
        return kwargs[key]

    return pattern.sub(repl, template)


def update_history(contract_path: Path, round_id: str, run_summary: dict) -> None:
    def mutate(data: dict) -> dict:
        history = data.setdefault("history", {})
        history["rounds"] = [r for r in history.get("rounds", []) if r.get("round_id") != round_id]
        history["rounds"].append(
            {
                "round_id": round_id,
                "ran_at_utc": run_summary.get("finished_at_utc"),
                "runs": run_summary.get("runs", []),
            }
        )
        data["history"] = history
        return data

    update_json(contract_path, mutate)


def main() -> int:
    ap = argparse.ArgumentParser(description="Run configured reviewers for one review workspace")
    ap.add_argument("--id", default="", help="Review id (optional if .reviews/.active_review_id exists)")
    ap.add_argument("--out-dir", default=".reviews", help="Review root dir")
    ap.add_argument("--reviewers", default="", help="Comma-separated reviewer ids to run")
    ap.add_argument("--timeout", type=int, default=1800, help="Per reviewer timeout in seconds")
    ap.add_argument("--round", default="auto", help="Round id: auto/latest/rNNN/NNN")
    args = ap.parse_args()

    out_dir = Path(args.out_dir)
    review_id = resolve_review_id(out_dir, args.id)

    root = out_dir / review_id
    contract_path = root / "contract.json"
    if not contract_path.exists():
        raise SystemExit(f"contract not found: {contract_path}")

    round_id = resolve_execution_round_id(root, args.round)
    round_dir = root / "rounds" / round_id
    raw_dir = round_dir / "raw"
    norm_dir = round_dir / "normalized"
    raw_dir.mkdir(parents=True, exist_ok=True)
    norm_dir.mkdir(parents=True, exist_ok=True)

    (out_dir / ".active_review_id").write_text(review_id + "\n", encoding="utf-8")
    (root / ".latest_round").write_text(round_id + "\n", encoding="utf-8")

    contract = load_json(contract_path)
    selected = {x.strip() for x in args.reviewers.split(",") if x.strip()}

    summary = {
        "review_id": review_id,
        "round_id": round_id,
        "started_at_utc": now_utc(),
        "runs": [],
    }

    for reviewer in contract.get("reviewers", []):
        reviewer_id = reviewer.get("id", "")
        if not reviewer_id:
            continue
        if selected and reviewer_id not in selected:
            continue
        if not reviewer.get("enabled", False):
            continue

        prompt_file = root / "prompts" / f"{reviewer_id}.txt"
        raw_file = raw_dir / f"{reviewer_id}.out.txt"
        normalized_file = norm_dir / f"{reviewer_id}.json"

        cmd_tpl = str(reviewer.get("command_template", "")).strip()
        if not cmd_tpl:
            summary["runs"].append({"reviewer": reviewer_id, "status": "skipped", "reason": "empty command_template"})
            continue

        cmd = render_command(
            cmd_tpl,
            prompt_file=shlex.quote(str(prompt_file)),
            raw_output_file=shlex.quote(str(raw_file)),
            json_output_file=shlex.quote(str(normalized_file)),
            review_dir=shlex.quote(str(root)),
            round_dir=shlex.quote(str(round_dir)),
            context_file=shlex.quote(str(root / "context.md")),
        )

        t0 = time.time()
        rc = 0
        err = ""
        try:
            # TRUST BOUNDARY: command_template is explicitly user-controlled in contract.json.
            # This executes the configured reviewer command verbatim.
            subprocess.run(cmd, shell=True, check=True, timeout=args.timeout)
            status = "ok"
        except subprocess.TimeoutExpired:
            status = "timeout"
            rc = 124
            err = f"timeout after {args.timeout}s"
        except subprocess.CalledProcessError as e:
            status = "failed"
            rc = int(e.returncode)
            err = f"exit={rc}"

        elapsed = round(time.time() - t0, 3)

        parsed = None
        if raw_file.exists():
            parsed = try_parse_json_blob(raw_file.read_text(encoding="utf-8", errors="replace"))
        if parsed is None and normalized_file.exists():
            try:
                parsed = load_json(normalized_file)
            except (json.JSONDecodeError, UnicodeDecodeError):
                parsed = None

        if parsed is None:
            normalized = {
                "reviewer": reviewer_id,
                "summary": "parse_failed",
                "findings": [],
                "notes": ["Reviewer output is not valid JSON. Check raw output."],
            }
        else:
            normalized = normalize_output(reviewer_id, parsed)

        write_json(normalized_file, normalized)

        summary["runs"].append(
            {
                "reviewer": reviewer_id,
                "status": status,
                "return_code": rc,
                "error": err,
                "elapsed_sec": elapsed,
                "normalized_file": str(normalized_file),
                "raw_file": str(raw_file),
            }
        )

    summary["finished_at_utc"] = now_utc()
    write_json(round_dir / "run-summary.json", summary)
    update_history(contract_path, round_id, summary)

    print(f"Run complete: {round_dir / 'run-summary.json'}")
    print(f"Merge next: python3 skills/nobs-review/scripts/merge_review.py --id {review_id} --round {round_id}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
