import hashlib
import json
import sqlite3
from pathlib import Path

TARGET_SOURCES = ('cursor', 'pi', 'omp')


def sha(text):
    return hashlib.sha256(text.encode('utf-8')).hexdigest()


def normalize_cursor_text(text, is_user):
    if is_user:
        start = text.find('<user_query>')
        if start >= 0:
            end = text.find('</user_query>', start + len('<user_query>'))
            if end >= 0:
                inner = text[start + len('<user_query>'):end].strip()
                if inner:
                    return inner
        trimmed = text.strip()
        if trimmed.startswith(('<user_info>', '<system_reminder>', '<agent_skill', '<available_skills>', '<manually_attached', '<cursor_commands>')):
            return ''
        if trimmed.startswith('<user_query>') and trimmed.endswith('</user_query>'):
            trimmed = trimmed[len('<user_query>'):-len('</user_query>')]
        return trimmed.strip()
    return text.strip()


def cursor_content(content, is_user):
    if isinstance(content, str):
        return normalize_cursor_text(content, is_user)
    if isinstance(content, list):
        parts = []
        for item in content:
            if isinstance(item, dict) and item.get('type') == 'text' and isinstance(item.get('text'), str):
                visible = normalize_cursor_text(item['text'], is_user)
                if visible:
                    parts.append(visible)
        return '\n'.join(parts).strip()
    return ''


def varint(data, offset):
    value = 0
    shift = 0
    while offset < len(data):
        byte = data[offset]
        offset += 1
        value |= (byte & 127) << shift
        if byte < 128:
            return value, offset
        shift += 7
        if shift > 63:
            return None, offset
    return None, offset


def protobuf_fields(data):
    fields = []
    offset = 0
    while offset < len(data):
        key, offset = varint(data, offset)
        if key is None:
            break
        number = key >> 3
        wire = key & 7
        if wire == 0:
            value, offset = varint(data, offset)
            if value is None:
                break
            fields.append((number, 'varint', value))
        elif wire == 1:
            if offset + 8 > len(data):
                break
            offset += 8
        elif wire == 2:
            length, offset = varint(data, offset)
            if length is None or offset + length > len(data):
                break
            fields.append((number, 'bytes', data[offset:offset + length]))
            offset += length
        elif wire == 5:
            if offset + 4 > len(data):
                break
            offset += 4
        else:
            break
    return fields


def cursor_meta(connection):
    raw = connection.execute('SELECT value FROM meta LIMIT 1').fetchone()
    if not raw or not isinstance(raw[0], str):
        raise ValueError('meta.value missing or not text')
    value = raw[0]
    try:
        meta = json.loads(bytes.fromhex(value).decode('utf-8'))
    except (ValueError, UnicodeDecodeError):
        meta = json.loads(value)
    if not isinstance(meta, dict):
        raise ValueError('meta.value is not an object')
    return meta


def cursor_messages(row):
    path = Path(row['source_file_path'])
    connection = sqlite3.connect('file:' + str(path) + '?mode=ro', uri=True)
    try:
        tables = {r[0] for r in connection.execute("SELECT name FROM sqlite_master WHERE type='table'")}
        if not {'blobs', 'meta'}.issubset(tables):
            raise ValueError('expected blobs and meta tables')
        meta = cursor_meta(connection)
        root_id = meta.get('latestRootBlobId')
        if not isinstance(root_id, str):
            raise ValueError('meta.latestRootBlobId missing')
        root_row = connection.execute('SELECT data FROM blobs WHERE id=?', (root_id,)).fetchone()
        if not root_row or not isinstance(root_row[0], bytes):
            raise ValueError('root blob missing or not bytes')
        blob_ids = [v.hex() for n, kind, v in protobuf_fields(root_row[0]) if n == 1 and kind == 'bytes' and len(v) == 32]
        messages = []
        fingerprints = {}
        for blob_id in blob_ids:
            blob_row = connection.execute('SELECT data FROM blobs WHERE id=?', (blob_id,)).fetchone()
            if not blob_row or not isinstance(blob_row[0], bytes):
                continue
            try:
                message = json.loads(blob_row[0])
            except (ValueError, UnicodeDecodeError):
                continue
            if not isinstance(message, dict):
                continue
            provider_options = message.get('providerOptions')
            cursor_options = provider_options.get('cursor') if isinstance(provider_options, dict) else None
            fingerprint = cursor_options.get('systemPromptFingerprint') if isinstance(cursor_options, dict) else None
            model = fingerprint.get('model') if isinstance(fingerprint, dict) else None
            if isinstance(model, str) and model:
                fingerprint_entry = fingerprints.setdefault(model, {'model': model, 'observations': 0, 'first_evidence_locator': 'table=blobs key=' + blob_id})
                fingerprint_entry['observations'] += 1
            if message.get('role') not in ('user', 'assistant'):
                continue
            content = cursor_content(message.get('content'), message['role'] == 'user')
            if content:
                messages.append({'kind': message['role'], 'text_sha256': sha(content), 'evidence_locator': 'table=blobs key=' + blob_id})
        return messages, meta, [fingerprints[key] for key in sorted(fingerprints)]
    finally:
        connection.close()


def pi_content(content):
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return '\n'.join(item['text'] for item in content if isinstance(item, dict) and item.get('type') in ('text', 'output_text') and isinstance(item.get('text'), str))
    return ''


def pi_messages(row):
    messages = []
    current_model = 'unknown'
    current_effort = 'unknown'
    model_values = set()
    effort_values = set()
    with Path(row['source_file_path']).open('r', encoding='utf-8') as stream:
        for line_number, raw in enumerate(stream, 1):
            if not raw.strip():
                continue
            try:
                entry = json.loads(raw)
            except json.JSONDecodeError:
                continue
            if not isinstance(entry, dict):
                continue
            kind = entry.get('type')
            if kind == 'model_change':
                model = entry.get('modelId', entry.get('model', current_model))
                current_model = model if isinstance(model, str) and model else 'unknown'
                if current_model != 'unknown':
                    model_values.add(current_model)
            elif kind == 'thinking_level_change':
                effort = entry.get('thinkingLevel', entry.get('level', 'unknown'))
                current_effort = effort if isinstance(effort, str) and effort else 'unknown'
                if current_effort != 'unknown':
                    effort_values.add(current_effort)
            elif kind == 'custom_message':
                content = pi_content(entry.get('content'))
                if content.strip():
                    messages.append({'kind': 'user', 'text_sha256': sha(content), 'model': 'unknown', 'effort': current_effort, 'permission': 'unknown', 'evidence_locator': 'jsonl_line=' + str(line_number) + ' type=custom_message'})
            elif kind in ('compaction', 'branch_summary'):
                content = entry.get('summary')
                if isinstance(content, str) and content.strip():
                    messages.append({'kind': 'assistant', 'text_sha256': sha(content), 'model': current_model, 'effort': current_effort, 'permission': 'unknown', 'evidence_locator': 'jsonl_line=' + str(line_number) + ' type=' + kind})
            elif kind == 'message' and isinstance(entry.get('message'), dict):
                message = entry['message']
                role = 'user' if message.get('role') == 'custom' else message.get('role')
                if role not in ('user', 'assistant'):
                    continue
                content = pi_content(message.get('content'))
                if not content.strip():
                    continue
                model = message.get('model', current_model)
                effort = entry.get('thinkingLevel', current_effort)
                permission = entry.get('permission', message.get('permission', 'unknown'))
                messages.append({
                    'kind': role,
                    'text_sha256': sha(content),
                    'model': model if isinstance(model, str) and model else 'unknown',
                    'effort': effort if isinstance(effort, str) and effort else 'unknown',
                    'permission': permission if isinstance(permission, (str, int, float, bool)) else 'unknown',
                    'evidence_locator': 'jsonl_line=' + str(line_number) + ' type=message',
                })
    return messages, {'models_from_state_changes': sorted(model_values), 'efforts_from_state_changes': sorted(effort_values)}


def extract(inventory_path: Path, output_path: Path, options: dict) -> dict:
    raw_inventory = inventory_path.read_bytes()
    inventory_sha256 = hashlib.sha256(raw_inventory).hexdigest()
    inventory = json.loads(raw_inventory)
    requested = [row for row in inventory if row.get('source') in TARGET_SOURCES]
    session_ids = [row.get('id') for row in requested]
    if len(set(session_ids)) != len(requested):
        raise ValueError('other_inventory_session_id_uniqueness_failed')
    sessions = []
    totals = {'input_source_sessions': len(requested), 'output_sessions': 0, 'input_messages': 0, 'matched_messages': 0, 'missing_messages': 0, 'extra_source_messages': 0, 'hash_mismatches': 0, 'parse_errors': 0}
    for row in requested:
        expected = row.get('messages', [])
        totals['input_messages'] += len(expected)
        source_path = Path(row.get('source_file_path') or '')
        session = {
            'session_id': row.get('id', 'unknown'),
            'source': row['source'],
            'input_message_count': len(expected),
            'matched_message_count': 0,
            'missing_message_count': 0,
            'extra_source_message_count': 0,
            'hash_mismatch_count': 0,
            'events': [],
            'fingerprint_metadata': {},
            'unknown_reasons': [],
        }
        if not source_path.is_file():
            session['missing_message_count'] = len(expected)
            session['unknown_reasons'].append('source_file_missing; inventory locator retained only for this extraction run')
            totals['missing_messages'] += len(expected)
            sessions.append(session)
            continue
        try:
            if row['source'] == 'cursor':
                actual, meta, fingerprints = cursor_messages(row)
                session['fingerprint_metadata'] = {
                    'system_prompt_fingerprint_models': fingerprints,
                    'last_used_model': meta.get('lastUsedModel', 'unknown'),
                    'last_used_model_scope': 'session_metadata_only_not_per_message',
                }
                if not fingerprints:
                    session['unknown_reasons'].append('no per-blob systemPromptFingerprint.model observed')
                session['unknown_reasons'].append('Cursor source contains no direct per-message model, effort, or permission fields used by this extraction')
            elif row['source'] == 'pi':
                actual, pi_state = pi_messages(row)
                session['fingerprint_metadata'] = pi_state
                if not pi_state['models_from_state_changes']:
                    session['unknown_reasons'].append('no model_change model observed')
                if not pi_state['efforts_from_state_changes']:
                    session['unknown_reasons'].append('no thinking_level_change effort observed')
                session['unknown_reasons'].append('permission unknown where message record has no permission field')
            else:
                actual = []
                session['unknown_reasons'].append('OMP source file missing; parser could not inspect messages')
        except Exception as exc:
            actual = []
            totals['parse_errors'] += 1
            session['unknown_reasons'].append('parse_error_type=' + type(exc).__name__)
        common = min(len(actual), len(expected))
        for index in range(common):
            observed = actual[index]
            wanted = expected[index]
            if wanted.get('role') != observed['kind'] or wanted.get('text_sha256') != observed['text_sha256']:
                session['hash_mismatch_count'] += 1
                continue
            event = {
                'kind': observed['kind'],
                'text_sha256': observed['text_sha256'],
                'inventory_seq': wanted.get('seq', 'unknown'),
                'model': observed.get('model', 'unknown') if row['source'] == 'pi' else 'unknown',
                'effort': observed.get('effort', 'unknown') if row['source'] == 'pi' else 'unknown',
                'permission': observed.get('permission', 'unknown') if row['source'] == 'pi' else 'unknown',
                'evidence_locator': observed['evidence_locator'],
            }
            session['events'].append(event)
        session['missing_message_count'] = max(0, len(expected) - common)
        session['extra_source_message_count'] = max(0, len(actual) - common)
        session['matched_message_count'] = len(session['events'])
        if session['hash_mismatch_count']:
            session['unknown_reasons'].append('inventory_message_hash_or_role_mismatch')
        if len(actual) != len(expected):
            session['unknown_reasons'].append('source_and_inventory_message_counts_differ')
        totals['matched_messages'] += session['matched_message_count']
        totals['missing_messages'] += session['missing_message_count']
        totals['extra_source_messages'] += session['extra_source_message_count']
        totals['hash_mismatches'] += session['hash_mismatch_count']
        sessions.append(session)
    totals['output_sessions'] = len(sessions)
    result = {
        'schema_version': 1,
        'input_inventory_sha256': inventory_sha256,
        'target_sources': list(TARGET_SOURCES),
        'acceptance': totals,
        'sessions': sessions,
    }
    output_path.write_text(json.dumps(result, ensure_ascii=False, separators=(',', ':')) + '\n', encoding='utf-8')
    return result
