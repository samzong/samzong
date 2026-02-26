#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import re
import sys
import datetime as dt
from contextlib import contextmanager
from pathlib import Path
from typing import Callable

try:
    import fcntl  # type: ignore
except Exception:  # pragma: no cover
    fcntl = None

ROUND_RE = re.compile(r"^r(\d{3})$")
_LOCK_WARNED = False


def now_utc() -> str:
    return dt.datetime.now(dt.timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def load_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))


def write_json(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_path = path.with_name(f"{path.name}.tmp-{os.getpid()}")
    tmp_path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    os.replace(tmp_path, path)


def resolve_review_id(out_dir: Path, review_id: str) -> str:
    if review_id:
        return review_id
    p = out_dir / ".active_review_id"
    if p.exists():
        rid = p.read_text(encoding="utf-8").strip()
        if rid:
            return rid
    raise SystemExit("review id is required (or initialize once to set .active_review_id)")


def list_round_ids(rounds_dir: Path) -> list[str]:
    if not rounds_dir.exists():
        return []
    out = []
    for p in rounds_dir.iterdir():
        if p.is_dir() and ROUND_RE.match(p.name):
            out.append(p.name)
    return sorted(out)


def to_round_id(value: str, *, usage: str) -> str:
    if ROUND_RE.match(value):
        return value
    if value.isdigit():
        return f"r{int(value):03d}"
    raise SystemExit(f"invalid round format: {value} (use {usage})")


@contextmanager
def _file_lock(lock_path: Path):
    global _LOCK_WARNED
    lock_path.parent.mkdir(parents=True, exist_ok=True)
    with lock_path.open("a+", encoding="utf-8") as f:
        if fcntl is not None:
            fcntl.flock(f.fileno(), fcntl.LOCK_EX)
        elif not _LOCK_WARNED:
            print("warning: file locking unavailable on this platform; concurrent writes are not protected", file=sys.stderr)
            _LOCK_WARNED = True
        try:
            yield
        finally:
            if fcntl is not None:
                fcntl.flock(f.fileno(), fcntl.LOCK_UN)


def update_json(path: Path, mutator: Callable[[dict], dict]) -> dict:
    lock_path = path.with_suffix(path.suffix + ".lock")
    with _file_lock(lock_path):
        if path.exists():
            data = load_json(path)
            if not isinstance(data, dict):
                raise SystemExit(f"expected JSON object in {path}, got {type(data).__name__}")
        else:
            data = {}

        new_data = mutator(data)
        if not isinstance(new_data, dict):
            raise SystemExit(f"mutator must return dict for {path}")

        write_json(path, new_data)
        return new_data
