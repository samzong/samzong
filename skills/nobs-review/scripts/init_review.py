#!/usr/bin/env python3
from __future__ import annotations

import argparse
import datetime as dt
import os
import re
import secrets
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from _common import build_context, git_changed_files, git_changed_loc, load_json, now_utc, sh, write_json


def gen_review_id() -> str:
    ts = dt.datetime.now().strftime("%Y%m%d-%H%M%S")
    return f"{ts}-{secrets.token_hex(3)}"


def detect_dev_tool(explicit: str, repo_root: Path) -> dict:
    if explicit != "auto":
        return {
            "tool": explicit,
            "confidence": 1.0,
            "signals": [f"forced_by_flag:{explicit}"],
            "scores": {explicit: 10},
        }

    scores = {"claude": 0, "codex": 0, "gemini": 0}
    signals = []

    ppid = os.getppid()
    parent_cmd = sh(f"ps -o command= -p {ppid}", warn=True).lower()
    if parent_cmd:
        signals.append(f"parent:{parent_cmd[:120]}")

    if "claude" in parent_cmd:
        scores["claude"] += 2
    if "codex" in parent_cmd:
        scores["codex"] += 2
    if "gemini" in parent_cmd:
        scores["gemini"] += 2

    if (repo_root / ".claude").exists() or (repo_root / "CLAUDE.md").exists():
        scores["claude"] += 1
        signals.append("repo_has_claude_markers")

    if Path.home().joinpath(".codex").exists() or (repo_root / ".codex").exists():
        scores["codex"] += 1
        signals.append("codex_config_present")

    if Path.home().joinpath(".gemini").exists() or (repo_root / ".gemini").exists():
        scores["gemini"] += 1
        signals.append("gemini_config_present")

    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)
    top_tool, top_score = ranked[0]
    second_score = ranked[1][1]

    if top_score == 0 or top_score == second_score:
        return {
            "tool": "unknown",
            "confidence": 0.2,
            "signals": signals,
            "scores": scores,
        }

    confidence = 0.6 if top_score >= 2 else 0.4
    return {
        "tool": top_tool,
        "confidence": confidence,
        "signals": signals,
        "scores": scores,
    }



def analyze_risk(changed_files: list[str], changed_loc: int) -> dict:
    high_signal_tokens = {
        "auth",
        "login",
        "payment",
        "billing",
        "security",
        "secret",
        "token",
        "permission",
        "permissions",
        "oauth",
        "jwt",
    }
    low_signal_tokens = {
        "migrate",
        "migration",
        "schema",
        "database",
        "infra",
        "deploy",
        "workflow",
    }

    sensitive = []
    for f in changed_files:
        tokens = {t for t in re.split(r"[^a-z0-9]+", f.lower()) if t}
        if tokens & high_signal_tokens:
            sensitive.append(f)
        elif tokens & low_signal_tokens:
            sensitive.append(f)

    has_high = any(
        {t for t in re.split(r"[^a-z0-9]+", f.lower()) if t} & high_signal_tokens
        for f in sensitive
    )

    score = 0
    if len(changed_files) > 20:
        score += 2
    elif len(changed_files) > 8:
        score += 1

    if changed_loc > 800:
        score += 2
    elif changed_loc > 300:
        score += 1

    if has_high:
        score += 2
    elif sensitive:
        score += 1

    if score >= 4:
        level = "high"
    elif score >= 2:
        level = "medium"
    else:
        level = "low"

    return {
        "level": level,
        "score": score,
        "changed_files": len(changed_files),
        "changed_loc": changed_loc,
        "sensitive_hits": sensitive,
    }


def recommend_reviewers(dev_tool: str, risk: dict) -> tuple[list[str], list[str]]:
    reasons = []

    if dev_tool == "claude":
        picked = ["codex_high"]
        reasons.append("dev tool guessed as claude -> prefer codex as primary external reviewer")
    elif dev_tool == "codex":
        picked = ["claude_opus"]
        reasons.append("dev tool guessed as codex -> prefer claude as primary external reviewer")
    elif dev_tool == "gemini":
        picked = ["claude_opus"]
        reasons.append("dev tool guessed as gemini -> prefer claude as primary external reviewer")
    else:
        picked = ["codex_high"]
        reasons.append("dev tool unknown -> default to codex_high")

    if risk["level"] in {"medium", "high"}:
        picked.extend(["codex_high", "claude_opus"])
        reasons.append(f"risk={risk['level']} -> require at least two strong reviewers")

    if risk["level"] == "high" and risk["sensitive_hits"]:
        picked.append("gemini_pro")
        reasons.append("high-risk sensitive files detected -> add third reviewer")

    dedup = list(dict.fromkeys(picked))
    return dedup, reasons


def build_contract(review_id: str, task: str, repo_root: Path, detection: dict, risk: dict, recommended: list[str], reasons: list[str]) -> dict:
    reviewers = [
        {
            "id": "codex_high",
            "enabled": "codex_high" in recommended,
            "model": "gpt-5.3-codex",
            "command_template": "codex exec --model gpt-5.3-codex \"$(cat {prompt_file})\" > {raw_output_file}",
        },
        {
            "id": "claude_opus",
            "enabled": "claude_opus" in recommended,
            "model": "opus",
            "reasoning": "high",
            "command_template": "env -u CLAUDECODE claude --model opus --print \"$(cat {prompt_file})\" > {raw_output_file}",
        },
        {
            "id": "gemini_pro",
            "enabled": "gemini_pro" in recommended,
            "model": "gemini-3.1-pro",
            "reasoning": "high",
            "command_template": "gemini --model gemini-3.1-pro --prompt-file {prompt_file} > {raw_output_file}",
        },
    ]

    return {
        "schema_version": "1.1",
        "review_id": review_id,
        "created_at_utc": now_utc(),
        "task": task,
        "repo_root": str(repo_root),
        "detection": detection,
        "risk": risk,
        "recommendation": {
            "recommended_reviewers": recommended,
            "reasons": reasons,
            "requires_user_confirmation": True,
        },
        "policy": {
            "fix_threshold": "medium",
            "auto_fix_threshold": {"determinism": "high", "scope": "local"},
            "require_response_for_all_findings": True,
        },
        "reviewers": reviewers,
        "history": {"rounds": []},
    }


def build_prompt(contract: dict, reviewer_id: str) -> str:
    return f"""You are reviewer '{reviewer_id}'.

Read context.md and review only code relevant to the task and current diff.

Output STRICT JSON only with this shape:
{{
  "reviewer": "{reviewer_id}",
  "summary": "...",
  "findings": [
    {{
      "id": "...",
      "severity": "critical|high|medium|low|nit",
      "file": "...",
      "line": 1,
      "title": "...",
      "detail": "...",
      "suggested_fix": "...",
      "confidence": 0.0,
      "category": "correctness|security|performance|test|maintainability|ux",
      "fix_determinism": "high|medium|low",
      "fix_scope": "local|cross-file|architectural"
    }}
  ],
  "notes": []
}}

No markdown fences. No prose outside JSON.
Policy fix_threshold={contract['policy']['fix_threshold']}.

For fix_determinism:
  high   = exactly one correct fix, no judgment needed
  medium = fix pattern is clear but touches multiple callsites
  low    = fix requires design or business-logic judgment

For fix_scope:
  local        = 1-3 lines in one function/block
  cross-file   = changes span multiple files
  architectural = requires structural or API-level decisions
"""


def write_active_review_id(out_dir: Path, review_id: str) -> None:
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / ".active_review_id").write_text(review_id + "\n", encoding="utf-8")


def main() -> int:
    ap = argparse.ArgumentParser(description="Initialize a cross-model review workspace")
    ap.add_argument("--task", default="", help="What this review is for")
    ap.add_argument("--id", default="", help="Optional explicit review id")
    ap.add_argument("--out-dir", default=".reviews", help="Review root dir")
    ap.add_argument(
        "--dev-tool",
        default="auto",
        choices=["auto", "claude", "codex", "gemini", "unknown"],
        help="Developer tool override; default auto detection",
    )
    ap.add_argument(
        "--refresh",
        action="store_true",
        help="Refresh existing review id context/recommendation instead of creating a new workspace",
    )
    args = ap.parse_args()

    repo_root = Path.cwd().resolve()
    out_dir = (repo_root / args.out_dir).resolve()
    review_id = args.id or gen_review_id()

    root = out_dir / review_id
    prompts_dir = root / "prompts"
    rounds_dir = root / "rounds"
    contract_path = root / "contract.json"

    if root.exists():
        if not args.refresh:
            raise SystemExit(
                f"review id already exists: {review_id}. "
                "Use --refresh to rebuild context/recommendation, or continue review with run_review.py --round auto."
            )
        if not contract_path.exists():
            raise SystemExit(f"cannot refresh review without contract file: {contract_path}")
        prompts_dir.mkdir(parents=True, exist_ok=True)
        rounds_dir.mkdir(parents=True, exist_ok=True)
    else:
        prompts_dir.mkdir(parents=True, exist_ok=False)
        rounds_dir.mkdir(parents=True, exist_ok=False)

    detection = detect_dev_tool(args.dev_tool, repo_root)
    changed_files = git_changed_files()
    changed_loc = git_changed_loc()
    risk = analyze_risk(changed_files, changed_loc)
    recommended, reasons = recommend_reviewers(detection["tool"], risk)
    task_input = args.task.strip()

    if contract_path.exists():
        contract = load_json(contract_path)
        if not isinstance(contract, dict):
            raise SystemExit(f"corrupt contract: {contract_path}")
        effective_task = task_input or str(contract.get("task", "")).strip()
        if not effective_task:
            raise SystemExit("--task is required for a new review or when existing task is empty")
        # Patch mutable fields; keep user-edited reviewers and history.
        contract.update(
            detection=detection,
            risk=risk,
            task=effective_task,
            recommendation={"recommended_reviewers": recommended, "reasons": reasons, "requires_user_confirmation": True},
        )
    else:
        if not task_input:
            raise SystemExit("--task is required for a new review")
        effective_task = task_input
        contract = build_contract(review_id, effective_task, repo_root, detection, risk, recommended, reasons)

    write_json(contract_path, contract)
    (root / "context.md").write_text(build_context(effective_task, changed_files), encoding="utf-8")

    for r in contract["reviewers"]:
        p = build_prompt(contract, r["id"])
        (prompts_dir / f"{r['id']}.txt").write_text(p, encoding="utf-8")

    write_active_review_id(out_dir, review_id)

    print(f"Initialized review workspace: {root}")
    print(f"Active review id updated: {review_id}")
    print(f"Dev tool guess: {detection['tool']} (confidence={detection['confidence']})")
    print("Note: dev-tool detection is heuristic; override with --dev-tool if needed")
    print(f"Risk level: {risk['level']} (files={risk['changed_files']}, loc={risk['changed_loc']})")
    print(f"Recommended reviewers: {', '.join(recommended) if recommended else '<none>'}")
    print("Please confirm or edit contract reviewers before running.")
    print(f"Contract: {contract_path}")
    print(f"Run reviewers: python3 skills/nobs-review/scripts/run_review.py --id {review_id} --round auto")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
