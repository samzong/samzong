from __future__ import annotations

import datetime as dt
import json
import os
import re
import shutil
import subprocess
import time
from pathlib import Path
from typing import Iterable


KNOWN_BOT_LOGINS = {
    "github-actions",
    "netlify",
    "copilot-swe-agent[bot]",
    "copilot",
    "copilot-pull-request-reviewer",
    "coderabbitai",
    "codecov",
    "dependabot[bot]",
    "renovate[bot]",
}

KNOWN_AI_LOGIN_FRAGMENTS = (
    "copilot",
    "coderabbit",
    "swe-agent",
    "ai-review",
)


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat()


def months_ago(months: int) -> dt.date:
    return dt.date.today() - dt.timedelta(days=30 * months)


def run(
    args: Iterable[str],
    *,
    cwd: Path,
    check: bool = True,
    retries: int = 0,
) -> str:
    argv = list(args)
    attempts = retries + 1
    last_result: subprocess.CompletedProcess[str] | None = None
    for attempt in range(1, attempts + 1):
        last_result = subprocess.run(
            argv,
            cwd=str(cwd),
            check=False,
            text=True,
            capture_output=True,
        )
        if not check or last_result.returncode == 0:
            return last_result.stdout
        if attempt < attempts:
            time.sleep(attempt)

    assert last_result is not None
    raise RuntimeError(
        f"command failed ({last_result.returncode}): {' '.join(argv)}\n{last_result.stderr.strip()}"
    )


def run_json(args: Iterable[str], *, cwd: Path) -> object:
    argv = list(args)
    retries = 2 if argv and argv[0] == "gh" else 0
    output = run(argv, cwd=cwd, retries=retries)
    return json.loads(output)


def ensure_directory(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def replace_path(path: Path) -> None:
    if path.is_symlink() or path.is_file():
        path.unlink()
    elif path.exists():
        shutil.rmtree(path)


def ensure_relative_symlink(link_path: Path, target_path: Path) -> None:
    ensure_directory(link_path.parent)
    if link_path.exists() or link_path.is_symlink():
        if link_path.is_symlink() and link_path.resolve() == target_path.resolve():
            return
        replace_path(link_path)
    relative_target = os.path.relpath(target_path, start=link_path.parent)
    link_path.symlink_to(relative_target)


def write_text(path: Path, content: str) -> None:
    ensure_directory(path.parent)
    path.write_text(content, encoding="utf-8")


def write_json(path: Path, payload: object) -> None:
    ensure_directory(path.parent)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def slugify(value: str) -> str:
    slug = re.sub(r"[^a-z0-9]+", "-", value.lower()).strip("-")
    return slug or "scope"


def is_bot_login(login: str | None) -> bool:
    if not login:
        return True
    lowered = login.lower()
    if lowered in KNOWN_BOT_LOGINS:
        return True
    if lowered.endswith("[bot]"):
        return True
    return any(fragment in lowered for fragment in KNOWN_AI_LOGIN_FRAGMENTS)


def top_n(counter: dict[str, int], limit: int) -> list[dict[str, int | str]]:
    items = sorted(counter.items(), key=lambda item: (-item[1], item[0]))
    return [{"name": key, "count": value} for key, value in items[:limit]]


def compact_whitespace(value: str) -> str:
    return re.sub(r"\s+", " ", value).strip()


def truncate(value: str, limit: int = 160) -> str:
    text = compact_whitespace(value)
    if len(text) <= limit:
        return text
    return text[: limit - 3].rstrip() + "..."
