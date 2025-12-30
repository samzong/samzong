#!/usr/bin/env python3
"""
Parse a unified diff (as produced by `gh pr diff`) and produce a JSON mapping that
helps scope reviews to only PR-introduced changes.

Outputs per file:
  - hunks with old/new start/count
  - added and deleted lines with line numbers (new-side for additions, old-side for deletions)
"""

from __future__ import annotations

import argparse
import json
import re
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional


HUNK_RE = re.compile(r"^@@ -(\d+)(?:,(\d+))? \+(\d+)(?:,(\d+))? @@")


@dataclass
class DiffLine:
    line: int
    content: str


@dataclass
class Hunk:
    old_start: int
    old_count: int
    new_start: int
    new_count: int
    header: str
    added: List[DiffLine]
    deleted: List[DiffLine]


def _parse_hunk_header(line: str) -> Optional[Hunk]:
    match = HUNK_RE.match(line)
    if not match:
        return None
    old_start = int(match.group(1))
    old_count = int(match.group(2) or "1")
    new_start = int(match.group(3))
    new_count = int(match.group(4) or "1")
    return Hunk(
        old_start=old_start,
        old_count=old_count,
        new_start=new_start,
        new_count=new_count,
        header=line.rstrip("\n"),
        added=[],
        deleted=[],
    )


def parse_unified_diff(diff_text: str) -> Dict[str, Any]:
    files: Dict[str, Dict[str, Any]] = {}

    current_file: Optional[str] = None
    current_hunk: Optional[Hunk] = None

    old_line_no: Optional[int] = None
    new_line_no: Optional[int] = None
    last_old_path: Optional[str] = None

    def finalize_hunk() -> None:
        nonlocal current_hunk, current_file
        if current_file is None or current_hunk is None:
            return
        files[current_file]["hunks"].append(asdict(current_hunk))
        current_hunk = None

    def ensure_file(path: str) -> None:
        if path not in files:
            files[path] = {"hunks": []}

    for raw in diff_text.splitlines(keepends=True):
        line = raw.rstrip("\n")

        if line.startswith("diff --git "):
            finalize_hunk()
            current_file = None
            current_hunk = None
            old_line_no = None
            new_line_no = None
            last_old_path = None
            continue

        if line.startswith("--- "):
            # Examples: "--- a/foo.py", "--- /dev/null"
            path = line[len("--- ") :].strip()
            if path.startswith("a/"):
                last_old_path = path[2:]
            else:
                last_old_path = None
            continue

        # Identify the "new" path from the +++ header (b/<path>).
        if line.startswith("+++ "):
            # Examples: "+++ b/foo.py", "+++ /dev/null"
            if line == "+++ /dev/null":
                # File deletion: keep tracking deletions under the old path.
                if last_old_path:
                    current_file = last_old_path
                    ensure_file(current_file)
                else:
                    current_file = None
                continue
            path = line[len("+++ ") :].strip()
            if path.startswith("b/"):
                path = path[2:]
            current_file = path
            ensure_file(current_file)
            continue

        if current_file is None:
            continue

        maybe_hunk = _parse_hunk_header(line)
        if maybe_hunk:
            finalize_hunk()
            current_hunk = maybe_hunk
            old_line_no = current_hunk.old_start
            new_line_no = current_hunk.new_start
            continue

        if current_hunk is None:
            continue

        # Handle special marker lines like "\ No newline at end of file"
        if line.startswith("\\"):
            continue

        if line.startswith("+") and not line.startswith("+++"):
            assert new_line_no is not None
            current_hunk.added.append(DiffLine(line=new_line_no, content=line[1:]))
            new_line_no += 1
            continue

        if line.startswith("-") and not line.startswith("---"):
            assert old_line_no is not None
            current_hunk.deleted.append(DiffLine(line=old_line_no, content=line[1:]))
            old_line_no += 1
            continue

        # Context line
        if line.startswith(" "):
            assert old_line_no is not None and new_line_no is not None
            old_line_no += 1
            new_line_no += 1
            continue

        # Any other line type: ignore

    finalize_hunk()

    return {"files": files}


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--input", required=True, help="Path to unified diff file")
    parser.add_argument("--output", required=True, help="Path to write JSON")
    args = parser.parse_args()

    diff_path = Path(args.input)
    out_path = Path(args.output)

    diff_text = diff_path.read_text(encoding="utf-8", errors="replace")
    result = parse_unified_diff(diff_text)

    out_path.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


if __name__ == "__main__":
    main()
