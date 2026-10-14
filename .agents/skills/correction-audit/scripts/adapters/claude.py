import collections
import datetime
import hashlib
import json
import os
import re
from pathlib import Path


def visible_text(content):
    if isinstance(content, str):
        return content
    if not isinstance(content, list):
        return ""
    return "\n".join(
        block["text"]
        for block in content
        if isinstance(block, dict)
        and block.get("type") == "text"
        and isinstance(block.get("text"), str)
        and block["text"]
    )


def timestamp_ms(value):
    if not isinstance(value, str):
        return None
    try:
        return int(datetime.datetime.fromisoformat(value.replace("Z", "+00:00")).timestamp() * 1000)
    except (ValueError, OverflowError):
        return None


def candidate_paths(projects_root, source_ids):
    found = collections.defaultdict(list)
    if not projects_root.is_dir() or not source_ids:
        return found
    for directory, _, files in os.walk(projects_root):
        for name in files:
            if name.endswith(".jsonl") and name[:-6] in source_ids:
                found[name[:-6]].append(str(Path(directory) / name))
    return found


def extract(inventory_path: Path, output_path: Path, options: dict) -> dict:
    inventory = json.loads(inventory_path.read_text(encoding="utf-8"))
    selected = [session for session in inventory if session.get("source") == "claude-code"]
    session_ids = [session.get("id") for session in selected]
    source_ids = [session.get("source_id") for session in selected]
    if len(set(session_ids)) != len(selected) or len({v for v in source_ids if v}) != len([v for v in source_ids if v]):
        raise ValueError("claude_inventory_session_or_source_id_uniqueness_failed")

    missing_original = [session for session in selected if not os.path.isfile(session.get("source_file_path") or "")]
    missing_source_ids = {str(session.get("source_id")) for session in missing_original}
    relocated_candidates = candidate_paths(Path(options.get("claude_projects", Path.home() / ".claude" / "projects")), missing_source_ids)
    results = []

    for session in selected:
        source_id = str(session.get("source_id") or "unknown")
        original_path = session.get("source_file_path") if isinstance(session.get("source_file_path"), str) else "unknown"
        original_exists = original_path != "unknown" and os.path.isfile(original_path)
        candidates = relocated_candidates.get(source_id, []) if not original_exists else []
        if original_exists:
            source_path = original_path
            source_status = "original_path_exists"
        elif len(candidates) == 1:
            source_path = candidates[0]
            source_status = "relocated_same_source_id"
        elif len(candidates) > 1:
            source_path = None
            source_status = "ambiguous_relocation_candidates"
        else:
            source_path = None
            source_status = "source_missing"

        refs_by_key = collections.defaultdict(list)
        invalid_refs = []
        for ref in session.get("messages", []):
            role = ref.get("role")
            digest = ref.get("text_sha256")
            seq = ref.get("seq")
            if role not in {"user", "assistant"} or not isinstance(seq, int) or not isinstance(digest, str) or not re.fullmatch(r"[0-9a-f]{64}", digest):
                invalid_refs.append({"inventory_seq": seq if isinstance(seq, int) else "unknown", "reason": "invalid_inventory_message_reference"})
                continue
            refs_by_key[(role, digest)].append(ref)
        for refs in refs_by_key.values():
            refs.sort(key=lambda ref: ref["seq"])

        session_result = {
            "session_id": session.get("id", "unknown"),
            "source_id": source_id,
            "original_source_path": original_path,
            "source_path": source_path if source_path else "unknown",
            "source_status": source_status,
            "events": [],
            "parse_errors": [],
            "hash_matches": 0,
            "missing": [],
            "source_messages_not_in_inventory": 0,
            "timestamp_mismatches": 0,
        }
        used_refs = collections.Counter()
        if source_path:
            permission = "unknown"
            try:
                with open(source_path, encoding="utf-8") as source:
                    for line_number, raw in enumerate(source, 1):
                        try:
                            row = json.loads(raw)
                        except json.JSONDecodeError:
                            session_result["parse_errors"].append({"raw_line": line_number, "error": "invalid_json"})
                            continue
                        if not isinstance(row, dict):
                            session_result["parse_errors"].append({"raw_line": line_number, "error": "row_not_object"})
                            continue

                        row_type = row.get("type")
                        if row_type == "permission-mode":
                            value = row.get("permissionMode")
                            permission = value if isinstance(value, str) else "unknown"
                            if permission == "unknown":
                                session_result["parse_errors"].append({"raw_line": line_number, "error": "permission_mode_value_missing"})
                            continue
                        if row_type not in {"user", "assistant"}:
                            continue

                        row_permission = row.get("permissionMode")
                        if isinstance(row_permission, str):
                            permission = row_permission
                        message = row.get("message") if isinstance(row.get("message"), dict) else {}
                        content = message.get("content")
                        machinery = row.get("isCompactSummary") is True or row.get("isSidechain") is True or row.get("isMeta") is True
                        if machinery:
                            continue
                        text = visible_text(content)
                        if not text:
                            continue

                        digest = hashlib.sha256(text.encode("utf-8")).hexdigest()
                        key = (row_type, digest)
                        ref_index = used_refs[key]
                        candidates_for_hash = refs_by_key.get(key, [])
                        matched_ref = candidates_for_hash[ref_index] if ref_index < len(candidates_for_hash) else None
                        used_refs[key] += 1
                        if matched_ref is None:
                            session_result["source_messages_not_in_inventory"] += 1
                            continue

                        session_result["hash_matches"] += 1
                        if timestamp_ms(row.get("timestamp")) != matched_ref.get("timestamp"):
                            session_result["timestamp_mismatches"] += 1
                        model = message.get("model") if isinstance(message.get("model"), str) else "unknown"
                        effort = row.get("effort") if isinstance(row.get("effort"), str) else "unknown"
                        per_turn_effort = row.get("perTurnEffort") if isinstance(row.get("perTurnEffort"), str) else "unknown"
                        session_result["events"].append({
                            "kind": row_type,
                            "text_sha256": digest,
                            "inventory_seq": matched_ref["seq"],
                            "model": model,
                            "effort": effort,
                            "per_turn_effort": per_turn_effort,
                            "permission": permission,
                            "evidence_locator": f"{source_path}:{line_number}",
                        })
            except OSError as error:
                session_result["parse_errors"].append({"raw_line": "unknown", "error": type(error).__name__})
            except UnicodeDecodeError as error:
                session_result["parse_errors"].append({"raw_line": "unknown", "error": f"invalid_utf8:{error.start}"})

        for key, refs in refs_by_key.items():
            for ref in refs[used_refs[key]:]:
                session_result["missing"].append({
                    "inventory_seq": ref["seq"],
                    "kind": ref["role"],
                    "text_sha256": ref["text_sha256"],
                    "reason": "source_file_unavailable" if not source_path else "source_message_not_found",
                })
        for ref in invalid_refs:
            session_result["missing"].append({
                "inventory_seq": ref["inventory_seq"],
                "kind": "unknown",
                "text_sha256": "unknown",
                "reason": ref["reason"],
            })
            session_result["parse_errors"].append(ref)
        session_result["missing"].sort(key=lambda item: item["inventory_seq"] if isinstance(item["inventory_seq"], int) else -1)
        results.append(session_result)

    result = {"source": "claude-code", "sessions": results}
    output_path.write_text(json.dumps(result, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return result
