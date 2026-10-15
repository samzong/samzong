import hashlib
import json
import os
from difflib import SequenceMatcher
from collections import Counter
from pathlib import Path

UNKNOWN = "unknown"
PERMISSION_FIELDS = (
    "approval_policy",
    "sandbox_policy",
    "permission_profile",
    "active_permission_profile",
    "file_system_sandbox_policy",
)
INJECTED_PREFIXES = (
    "# AGENTS.md instructions",
    "<environment_context>",
    "<user_instructions>",
    "<INSTRUCTIONS>",
)


def digest(text):
    return hashlib.sha256(text.encode("utf-8")).hexdigest()


def payload_model(payload):
    for key in ("model", "model_name"):
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value
    info = payload.get("model_info")
    value = info.get("slug") if isinstance(info, dict) else None
    return value if isinstance(value, str) and value.strip() else None


def payload_effort(payload):
    for key in ("effort", "reasoning_effort", "model_reasoning_effort", "thinking"):
        value = payload.get(key)
        if isinstance(value, (str, int, float, bool)):
            return value
    return None


def safe_permission_value(value, key=""):
    lowered = key.lower()
    if any(part in lowered for part in ("writable_roots", "path", "directory", "directories", "entries")):
        if isinstance(value, (list, dict)):
            return {"count": len(value)}
        return UNKNOWN if value is None else "redacted"
    if isinstance(value, dict):
        return {str(k): safe_permission_value(v, str(k)) for k, v in value.items()}
    if isinstance(value, list):
        return [safe_permission_value(item, key) for item in value]
    if isinstance(value, str) and value.startswith("/"):
        return "redacted-path"
    if value is None:
        return UNKNOWN
    if isinstance(value, (str, int, float, bool)):
        return value
    return UNKNOWN


def payload_permissions(payload):
    return {
        key: safe_permission_value(payload.get(key), key) if key in payload else UNKNOWN
        for key in PERMISSION_FIELDS
    }


def text_from_content(content):
    if not isinstance(content, list):
        return ""
    parts = []
    for item in content:
        if not isinstance(item, dict):
            continue
        kind = item.get("type")
        if kind in ("text", "output_text", "input_text"):
            value = item.get("text")
            if isinstance(value, str):
                parts.append(value)
        elif kind == "function_call":
            args = item.get("arguments")
            if isinstance(args, str):
                name = item.get("name") if isinstance(item.get("name"), str) else "tool"
                parts.append(f"[{name}] {args}")
        elif kind == "function_call_output":
            value = item.get("output")
            if isinstance(value, str):
                parts.append(value)
    return "\n".join(parts)


def injected_user_text(text):
    return any(
        line.lstrip().startswith(INJECTED_PREFIXES)
        for line in text.splitlines()
    )


def empty_permissions():
    return {key: UNKNOWN for key in PERMISSION_FIELDS}


def parse_source(row):
    path = row.get("source_file_path")
    state = {"model": UNKNOWN, "effort": UNKNOWN, "permission": empty_permissions()}
    messages = []
    errors = Counter()
    line_count = 0
    if not isinstance(path, str) or not os.path.isfile(path):
        errors["source_file_missing"] += 1
        return messages, errors

    forked_waiting = False
    user_last_index = None
    user_streams_seen = 0

    def add_message(role, text, line_number, stream=None):
        nonlocal user_last_index, user_streams_seen
        text_hash = digest(text)
        if role == "user":
            bit = {"event_msg": 1, "response_item": 2}.get(stream, 0)
            if (
                user_last_index is not None
                and user_last_index == len(messages) - 1
                and messages[user_last_index]["kind"] == "user"
                and messages[user_last_index]["text_sha256"] == text_hash
                and bit
                and not user_streams_seen & bit
            ):
                user_streams_seen |= bit
                return
            user_last_index = len(messages)
            user_streams_seen = bit
        elif messages and messages[-1]["kind"] == "assistant" and messages[-1]["text_sha256"] == text_hash:
            return
        messages.append({
            "kind": role,
            "text": text,
            "text_sha256": text_hash,
            "line": line_number,
            "model": state["model"],
            "effort": state["effort"],
            "permission": dict(state["permission"]),
        })

    try:
        with open(path, encoding="utf-8") as handle:
            for line_number, raw in enumerate(handle, 1):
                line_count = line_number
                if not raw.strip():
                    continue
                try:
                    envelope = json.loads(raw)
                except (json.JSONDecodeError, UnicodeDecodeError):
                    errors["invalid_json"] += 1
                    continue
                if not isinstance(envelope, dict):
                    errors["record_not_object"] += 1
                    continue
                record_type = envelope.get("type")
                payload = envelope.get("payload")
                payload = payload if isinstance(payload, dict) else {}
                if forked_waiting:
                    if record_type != "turn_context":
                        continue
                    forked_waiting = False
                if record_type in ("session_meta", "turn_context"):
                    model = payload_model(payload)
                    effort = payload_effort(payload)
                    if model is not None:
                        state["model"] = model
                    if effort is not None:
                        state["effort"] = effort
                    for key, value in payload_permissions(payload).items():
                        if value != UNKNOWN:
                            state["permission"][key] = value
                    if record_type == "session_meta" and payload.get("forked_from_id") is not None:
                        forked_waiting = True
                    continue
                if record_type == "event_msg":
                    event_type = payload.get("type")
                    if event_type in ("user_message", "agent_message"):
                        value = payload.get("message")
                        role = "user" if event_type == "user_message" else "assistant"
                        if isinstance(value, str) and value:
                            add_message(role, value, line_number, "event_msg")
                    continue
                if record_type != "response_item" or payload.get("type") != "message":
                    continue
                role = payload.get("role")
                if role not in ("user", "assistant"):
                    continue
                value = text_from_content(payload.get("content"))
                if value and not (role == "user" and injected_user_text(value)):
                    add_message(role, value, line_number, "response_item")
    except (OSError, UnicodeDecodeError):
        errors["source_read_error"] += 1
        messages = []

    if line_count == 0:
        errors["empty_source_file"] += 1
    return messages, errors


def unknown_event(expected, seq, locator=UNKNOWN):
    return {
        "kind": expected.get("role", UNKNOWN),
        "text_sha256": expected.get("text_sha256", UNKNOWN),
        "inventory_seq": UNKNOWN,
        "model": UNKNOWN,
        "effort": UNKNOWN,
        "permission": empty_permissions(),
        "evidence_locator": locator,
    }


def align_messages(inventory, source):
    inventory_keys = [(row.get("role", UNKNOWN), row.get("text_sha256", UNKNOWN)) for row in inventory]
    source_keys = [(row["kind"], row["text_sha256"]) for row in source]
    matcher = SequenceMatcher(None, inventory_keys, source_keys, autojunk=False)
    exact = {}
    mismatch = {}
    missing = 0
    source_only = 0
    roles = 0
    hashes = 0
    mismatch_messages = 0
    for tag, i1, i2, j1, j2 in matcher.get_opcodes():
        if tag == "equal":
            for offset in range(i2 - i1):
                exact[i1 + offset] = j1 + offset
        elif tag == "replace":
            paired = min(i2 - i1, j2 - j1)
            for offset in range(paired):
                inventory_index = i1 + offset
                source_index = j1 + offset
                mismatch[inventory_index] = source_index
                mismatch_messages += 1
                roles += inventory_keys[inventory_index][0] != source_keys[source_index][0]
                hashes += inventory_keys[inventory_index][1] != source_keys[source_index][1]
            missing += (i2 - i1) - paired
            source_only += (j2 - j1) - paired
        elif tag == "delete":
            missing += i2 - i1
        elif tag == "insert":
            source_only += j2 - j1
    return exact, mismatch, {
        "source_missing": missing,
        "source_only": source_only,
        "role_mismatches": roles,
        "hash_mismatches": hashes,
        "mismatch_messages": mismatch_messages,
    }


def process_session(row):
    inventory = row.get("messages") if isinstance(row.get("messages"), list) else []
    source, parse_errors = parse_source(row)
    path = row.get("source_file_path")
    events = []
    exact, mismatch, alignment = align_messages(inventory, source)
    mismatches = Counter(alignment)
    matched = 0
    unknown_reasons = Counter()
    for index, expected in enumerate(inventory):
        expected_seq = expected.get("seq", index) if isinstance(expected, dict) else UNKNOWN
        seq_ok = expected_seq == index
        if not seq_ok:
            mismatches["inventory_sequence"] += 1
        if not isinstance(expected, dict):
            mismatches["inventory_record_invalid"] += 1
            events.append(unknown_event({}, index))
            continue
        source_index = exact.get(index)
        if source_index is None:
            source_index = mismatch.get(index)
        candidate = source[source_index] if source_index is not None else None
        locator = f"{path}#L{candidate['line']}" if candidate is not None else UNKNOWN
        if index not in exact or not seq_ok:
            unknown_reasons["inventory_message_not_aligned"] += 1
            events.append(unknown_event(expected, index, locator))
            continue
        matched += 1
        unknown_reasons["no_prior_model_state"] += candidate["model"] == UNKNOWN
        unknown_reasons["no_prior_effort_state"] += candidate["effort"] == UNKNOWN
        unknown_reasons["no_prior_core_permission_state"] += any(candidate["permission"].get(key) == UNKNOWN for key in ("approval_policy", "sandbox_policy"))
        events.append({
            "kind": expected.get("role", UNKNOWN),
            "text_sha256": expected.get("text_sha256", UNKNOWN),
            "inventory_seq": expected_seq,
            "model": candidate["model"],
            "effort": candidate["effort"],
            "permission": candidate["permission"],
            "evidence_locator": locator,
        })
    source_only = alignment["source_only"]
    per_field_unknown = {
        field: sum(event["permission"].get(field) == UNKNOWN for event in events)
        for field in PERMISSION_FIELDS
    }
    session = {
        "session_id": row.get("id", UNKNOWN),
        "message_validation": {
            "inventory_messages": len(inventory),
            "source_messages": len(source),
            "hash_matches": len(exact),
            "matched_messages": matched,
            "source_missing_messages": alignment["source_missing"],
            "source_only_messages": source_only,
            "role_mismatches": alignment["role_mismatches"],
            "hash_mismatches": alignment["hash_mismatches"],
            "mismatch_messages": alignment["mismatch_messages"],
            "inventory_sequence_mismatches": mismatches["inventory_sequence"],
        },
        "parse_errors": dict(sorted(parse_errors.items())),
        "mismatch_counts": dict(sorted((key, value) for key, value in mismatches.items() if value)),
        "unknown_reasons": dict(sorted((key, value) for key, value in unknown_reasons.items() if value)),
        "unknown_counts": {
            "model": sum(event["model"] == UNKNOWN for event in events),
            "effort": sum(event["effort"] == UNKNOWN for event in events),
            "permission_core": sum(any(event["permission"].get(key) == UNKNOWN for key in ("approval_policy", "sandbox_policy")) for event in events),
            "permission_fields": per_field_unknown,
        },
        "events": events,
    }
    return session


def extract(inventory_path: Path, output_path: Path, options: dict) -> dict:
    rows = json.loads(inventory_path.read_text(encoding="utf-8"))
    codex_rows = [row for row in rows if row.get("source") == "codex"]
    session_ids = [row.get("id") for row in codex_rows]
    if len(set(session_ids)) != len(codex_rows):
        raise ValueError("codex_inventory_session_id_uniqueness_failed")
    sessions = [process_session(row) for row in codex_rows]
    all_events = [event for session in sessions for event in session["events"]]
    validation = {
        "inventory_sessions": len(rows),
        "codex_sessions": len(codex_rows),
        "output_sessions": len(sessions),
        "inventory_messages": sum(s["message_validation"]["inventory_messages"] for s in sessions),
        "source_messages": sum(s["message_validation"]["source_messages"] for s in sessions),
        "hash_matches": sum(s["message_validation"]["hash_matches"] for s in sessions),
        "matched_messages": sum(s["message_validation"]["matched_messages"] for s in sessions),
        "hash_mismatches": sum(s["message_validation"]["hash_mismatches"] for s in sessions),
        "role_mismatches": sum(s["message_validation"]["role_mismatches"] for s in sessions),
        "inventory_sequence_mismatches": sum(s["message_validation"]["inventory_sequence_mismatches"] for s in sessions),
        "source_missing_messages": sum(s["message_validation"]["source_missing_messages"] for s in sessions),
        "source_only_messages": sum(s["message_validation"]["source_only_messages"] for s in sessions),
        "mismatch_messages": sum(s["message_validation"]["mismatch_messages"] for s in sessions),
        "source_files_missing": sum(s["parse_errors"].get("source_file_missing", 0) for s in sessions),
        "parse_errors": sum(sum(s["parse_errors"].values()) for s in sessions),
        "model_unknown_messages": sum(event["model"] == UNKNOWN for event in all_events),
        "effort_unknown_messages": sum(event["effort"] == UNKNOWN for event in all_events),
        "permission_core_unknown_messages": sum(any(event["permission"].get(key) == UNKNOWN for key in ("approval_policy", "sandbox_policy")) for event in all_events),
        "permission_field_unknown_messages": {
            field: sum(event["permission"].get(field) == UNKNOWN for event in all_events)
            for field in PERMISSION_FIELDS
        },
        "sessions_with_parse_errors": sum(bool(s["parse_errors"]) for s in sessions),
        "sessions_with_mismatches": sum(bool(s["mismatch_counts"]) for s in sessions),
        "sessions_with_missing_messages": sum(s["message_validation"]["source_missing_messages"] > 0 for s in sessions),
        "unknown_reason_counts": {
            key: sum(s["unknown_reasons"].get(key, 0) for s in sessions)
            for key in ("inventory_message_not_aligned", "no_prior_model_state", "no_prior_effort_state", "no_prior_core_permission_state")
        },
    }
    output = {"source": "codex", "sessions": sessions, "validation": validation}
    output_path.write_text(json.dumps(output, ensure_ascii=False, separators=(",", ":")) + "\n", encoding="utf-8")
    return output
