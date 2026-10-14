import argparse
import collections
import datetime as dt
import hashlib
import importlib
import json
import math
import os
from pathlib import Path
import re
import shutil
import subprocess
import sys

HERE = Path(__file__).resolve().parent
UNKNOWN = 'unknown'


def digest(value):
    return hashlib.sha256(value).hexdigest()


def read(path):
    return json.loads(Path(path).read_text(encoding='utf-8'))


def lines(path):
    return [json.loads(s) for s in Path(path).read_text(encoding='utf-8').split('\n') if s.strip()]


def write(path, value, jsonl=False):
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    content = ''.join(json.dumps(x, ensure_ascii=False) + '\n' for x in value) if jsonl else json.dumps(value, ensure_ascii=False, indent=2) + '\n'
    path.write_text(content, encoding='utf-8')
    path.chmod(0o600)


def clean(text):
    text = re.sub(r'-----BEGIN [^-]*PRIVATE KEY-----[\s\S]*?-----END [^-]*PRIVATE KEY-----', '[credential removed]', text)
    text = re.sub(r'\b(?:sk-|gh[pousr]_|github_pat_|xox[baprs]-)[A-Za-z0-9_\-]{8,}', '[credential removed]', text)
    text = re.sub(r'(?i)bearer\s+[A-Za-z0-9._\-]+', '[credential removed]', text)
    text = re.sub(r'(?im)^.*(?:密码[是为:=：]|password[ :：=]|api[_ -]?key[ :：=]|secret[ :：=]).*$', '[credential line removed]', text)
    text = re.sub(r'(?i)((?:api[_-]?key|password|secret|access[_-]?token|authorization)\s*[:=]\s*)[^\s,;]+', r'\1[credential removed]', text)
    text = re.sub(r'\b(?:AKIA|ASIA)[A-Z0-9]{16}\b|\beyJ[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\.[A-Za-z0-9_-]+\b', '[credential removed]', text)
    text = re.sub(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}\b', '[email removed]', text)
    return text


def day(value, fallback=UNKNOWN):
    if isinstance(value, (float, int)):
        try:
            return dt.datetime.fromtimestamp(value / 1000, dt.timezone.utc).date().isoformat()
        except (ValueError, OverflowError, OSError):
            pass
    return fallback


def command(args):
    if not shutil.which(args[0]):
        raise ValueError(f'{args[0]} is not installed; install it and retry')
    result = subprocess.run(args, text=True, capture_output=True)
    if result.returncode:
        raise ValueError(f'{args[0]} failed (exit {result.returncode}); inspect it locally before retrying')
    return result.stdout


def private_dir(root):
    path = root / 'private'
    path.mkdir(parents=True, exist_ok=True)
    path.chmod(0o700)
    return path


def snapshot(root):
    p = private_dir(root)
    inventory, users = read(p / 'inventory.json'), lines(p / 'users.jsonl')
    validate_snapshot(inventory, users)
    return inventory, users


def validate_snapshot(inventory, users):
    if not inventory:
        raise ValueError('No sessions exported; run recall sync or broaden --project/--time/--source')
    if len({s['id'] for s in inventory}) != len(inventory) or len({u['uid'] for u in users}) != len(users):
        raise ValueError('Snapshot has duplicate session IDs or user UIDs')
    by_session = {s['id']: s for s in inventory}
    for session in inventory:
        if session.get('thread_role') != 'primary':
            raise ValueError('Snapshot must contain explicitly primary sessions only')
        if len({m['seq'] for m in session['messages']}) != len(session['messages']):
            raise ValueError('Snapshot has duplicate message sequence')
    refs = {(s['id'], m['seq']): m for s in inventory for m in s['messages']}
    for u in users:
        ref = refs.get((u['session'], u['seq']))
        if not ref or (ref['role'], ref['text_sha256']) != ('user', u['text_sha256']):
            raise ValueError('User hash/sequence does not match snapshot')
        if u['session'] not in by_session:
            raise ValueError('User references a session outside snapshot')


def export(args):
    p = private_dir(args.output)
    if (p / 'inventory.json').exists():
        raise ValueError('Snapshot already exists; choose a new output directory to preserve classification bindings')
    if args.prepared:
        inventory, users = read(args.prepared / 'inventory.json'), lines(args.prepared / 'users.jsonl')
        for u in users:
            for field in ('text', 'previous_assistant', 'first_user'):
                u[field] = clean(u.get(field, ''))
        raw_hash = digest((args.prepared / 'inventory.json').read_bytes() + (args.prepared / 'users.jsonl').read_bytes())
        invocation = ['prepared snapshot']
    else:
        invocation = [args.recall, 'export', '--project', args.project, '--time', args.time, '--thread-role', 'primary', '--include', 'metadata,messages,usage', '--limit', '0']
        if args.source:
            invocation += ['--source', args.source]
        raw = Path(args.input).read_text(encoding='utf-8') if args.input else command(invocation)
        raw_hash = digest(raw.encode())
        if args.input:
            invocation = ['frozen raw export', str(args.input)]
        inventory, users = [], []
        for line in raw.split('\n'):
            if not line.strip():
                continue
            row = json.loads(line)
            s = row['session']
            thread_role = s.get('thread_role') or (s.get('topology') or {}).get('thread_role')
            if thread_role != 'primary':
                continue
            inv = {k: s.get(k) for k in ('id', 'source', 'source_id', 'source_file_path', 'directory', 'repo_slug', 'started_at', 'updated_at', 'thread_role')}
            usage_keys = ('event_key', 'event_seq', 'message_seq', 'timestamp', 'model', 'provider', 'input_tokens', 'output_tokens', 'cache_read_tokens', 'cache_write_tokens', 'reasoning_tokens', 'token_source')
            inv.update(thread_role=thread_role, date=day(s.get('started_at')), messages=[], usage=[{k: e.get(k) for k in usage_keys} for e in row.get('usage_events', [])])
            previous, first, n = None, '', 0
            for m in sorted(row['messages'], key=lambda m: m['seq']):
                text = m.get('content') or ''
                text_hash = digest(text.encode())
                inv['messages'].append({'seq': m['seq'], 'role': m['role'], 'timestamp': m.get('timestamp'), 'text_sha256': text_hash})
                if m['role'] == 'assistant':
                    previous = m
                elif m['role'] == 'user':
                    n += 1
                    first = first or text
                    users.append({'uid': len(users) + 1, 'session': s['id'], 'source': s['source'], 'repo': s.get('repo_slug') or s.get('directory') or UNKNOWN, 'date': day(m.get('timestamp') or s.get('started_at')), 'session_date': inv['date'], 'seq': m['seq'], 'nth_user': n, 'text_sha256': text_hash, 'text': clean(text)[:6000], 'previous_assistant': clean((previous or {}).get('content', ''))[-2600:], 'assistant_seq': (previous or {}).get('seq'), 'first_user': clean(first)[:600], 'truncated': len(text) > 6000})
            inv['users'] = n
            inventory.append(inv)
    if not inventory:
        raise ValueError('No primary sessions exported; run recall sync or broaden filters')
    validate_snapshot(inventory, users)
    write(p / 'inventory.json', inventory)
    write(p / 'users.jsonl', users, True)
    write(p / 'export.json', {'command': invocation, 'raw_sha256': raw_hash, 'sessions': len(inventory), 'users': len(users)})
    return {'sessions': len(inventory), 'users': len(users)}


def prescreen(args):
    from prescreen_rules import reason, KEYWORDS, INJECTION, ACK
    _, users = snapshot(args.output)
    p = private_dir(args.output)
    candidates, excluded = [], []
    for u in users:
        (candidates if reason(u) == 'candidate' else excluded).append({**u, 'screen_reason': reason(u)})
    write(p / 'candidates.jsonl', candidates, True)
    write(p / 'excluded.jsonl', excluded, True)
    batches = []
    for i in range(0, len(candidates), args.batch_size):
        name = f'batches/{i // args.batch_size + 1:04d}.jsonl'
        write(p / name, candidates[i:i + args.batch_size], True)
        batches.append({'file': name, 'sha256': digest((p / name).read_bytes()), 'rows': min(args.batch_size, len(candidates) - i)})
    samples = []
    for source in sorted({u['source'] for u in users}):
        for name, population in [('candidate', candidates), ('excluded', excluded)]:
            group = [u for u in population if u['source'] == source and u['nth_user'] > 1]
            group.sort(key=lambda u: digest(f'{args.seed}:{u["session"]}:{u["seq"]}:{u["text_sha256"]}'.encode()))
            samples.extend({**u, 'audit_stratum': name} for u in group[:max(1, math.ceil(len(group) * args.audit_fraction))])
    if args.replay_audit:
        by_uid = {u['uid']: u for u in users}
        selected = lines(args.replay_audit)
        if len({u['uid'] for u in selected}) != len(selected):
            raise ValueError('Duplicate replay audit UID')
        samples = []
        candidate_ids = {u['uid'] for u in candidates}
        for u in selected:
            original = by_uid.get(u['uid'])
            if not original or u.get('text_sha256') != original['text_sha256']:
                raise ValueError('Replay audit UID/hash does not match snapshot')
            samples.append({**original, 'audit_stratum': 'candidate' if u['uid'] in candidate_ids else 'excluded'})
    write(p / 'audit-input.jsonl', samples, True)
    bindings = {name: digest((p / name).read_bytes()) for name in ('inventory.json', 'users.jsonl', 'candidates.jsonl', 'excluded.jsonl', 'audit-input.jsonl')}
    write(p / 'prescreen.json', {'bindings': bindings, 'rules_sha256': digest((KEYWORDS + INJECTION + ACK).encode()), 'candidates': len(candidates), 'excluded': len(excluded), 'counts': dict(collections.Counter(reason(u) for u in users)), 'seed': args.seed, 'audit_fraction': args.audit_fraction, 'audit_rows': len(samples), 'audit_mode': 'frozen_sample_replay' if args.replay_audit else 'stratified_sample', 'audit_strata': dict(collections.Counter(u['audit_stratum'] for u in samples)), 'batches': batches})
    catalog = p / 'clusters.json'
    if not catalog.exists():
        write(catalog, read(HERE.parent / 'references' / 'cluster-seeds.json'))
    return {'candidates': len(candidates), 'audit_rows': len(samples), 'batches': len(batches)}


def validate_events(inventory, events):
    refs = {(s['id'], m['seq']): m for s in inventory for m in s['messages']}
    seen = set()
    for e in events:
        key = e['session_id'], e['inventory_seq']
        ref = refs.get(key)
        if key in seen:
            raise ValueError('Duplicate attributed message')
        if not ref or e.get('kind') not in ('user', 'assistant') or (e['kind'], e.get('text_sha256')) != (ref['role'], ref['text_sha256']):
            raise ValueError('Attributed role/hash does not match snapshot; refusing attribution')
        seen.add(key)
    return {(e['session_id'], e['inventory_seq']): e for e in events}


def attribute(args):
    inventory, _ = snapshot(args.output)
    p = private_dir(args.output)
    events, coverage = [], []
    by_session = {s['id']: s for s in inventory}
    if args.replay_events:
        events = lines(args.replay_events)
        counts = collections.Counter(e['session_id'] for e in events)
        coverage = [{'session_id': s['id'], 'matched_messages': counts[s['id']], 'reason': 'frozen_event_replay'} for s in inventory]
    else:
        for name in ('claude', 'codex', 'other'):
            adapter = importlib.import_module('adapters.' + name)
            result = adapter.extract(p / 'inventory.json', p / f'{name}.json', {'claude_projects': args.claude_projects})
            for s in result['sessions']:
                refs = {m['seq']: m for m in by_session[s['session_id']]['messages']}
                matched = 0
                for e in s['events']:
                    seq = e.get('inventory_seq')
                    if e.get('kind') not in ('user', 'assistant') or seq not in refs or e.get('inventory_match') is False:
                        continue
                    events.append({**e, 'session_id': s['session_id']})
                    matched += 1
                coverage.append({'session_id': s['session_id'], 'matched_messages': matched})
    validate_events(inventory, events)
    covered = {s['session_id'] for s in coverage}
    coverage.extend({'session_id': s['id'], 'matched_messages': 0, 'reason': 'unsupported_source'} for s in inventory if s['id'] not in covered)
    write(p / 'events.jsonl', events, True)
    write(p / 'attribution.json', {'mode': 'frozen_event_replay' if args.replay_events else 'native_sources', 'replay_sha256': digest(args.replay_events.read_bytes()) if args.replay_events else None, 'sessions': coverage})
    return {'sessions': len(coverage), 'matched_messages': len(events), 'unsupported_sessions': len(inventory) - len(covered), 'mode': 'frozen_event_replay' if args.replay_events else 'native_sources'}


def config(event):
    if not event or event.get('model') in ('<synthetic>', 'bridge-toolcall', 'auto'):
        return UNKNOWN, UNKNOWN
    effort = event.get('per_turn_effort')
    if effort is None or effort == UNKNOWN:
        effort = event.get('effort')
    def metadata(value):
        value = str(value or UNKNOWN)
        return value if re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/+-]{0,159}', value) and clean(value) == value else UNKNOWN
    return metadata(event.get('model')), metadata(effort)


def validate_labels(root, users):
    p = private_dir(root)
    for name, expected in read(p / 'prescreen.json')['bindings'].items():
        if digest((p / name).read_bytes()) != expected:
            raise ValueError('Prescreen inputs changed; rerun prescreen and classification')
    by_user = {u['uid']: u for u in users}
    catalog = read(p / 'clusters.json')
    ids = {c['id'] for c in catalog}
    if len(ids) != len(catalog):
        raise ValueError('Duplicate cluster IDs')
    for c in catalog:
        if not re.fullmatch(r'[a-z0-9-]+', c['id']) or not c.get('public_title') or clean(c['public_title']) != c['public_title'] or re.search(r'(?:/Users/|/home/|[A-Z]:\\|https?://)', c['public_title']):
            raise ValueError('Cluster requires a safe public_title and lowercase ASCII ID')
    labels = lines(p / 'labels.jsonl')
    audits = lines(p / 'audit-result.jsonl')
    def check(rows):
        if len({x['uid'] for x in rows}) != len(rows):
            raise ValueError('Duplicate classification UID')
        for x in rows:
            u = by_user.get(x['uid'])
            if not u or x.get('text_sha256') != u['text_sha256']:
                raise ValueError('Classification hash/UID does not match snapshot')
            if any(type(x.get(k)) is not bool for k in ('corrected', 'uncertain', 'injection')):
                raise ValueError('Classification booleans are required')
            if x.get('cluster') not in ids | {''} or not isinstance(x.get('reason'), str) or not x['reason'].strip():
                raise ValueError('Classification requires a known cluster and reason')
            if x['corrected'] and not x['uncertain'] and not x['injection'] and (u['nth_user'] <= 1 or not x.get('cluster') or (not isinstance(x.get('summary'), str) or not x['summary'].strip())):
                raise ValueError('Confirmed correction requires prior turn, cluster, and summary')
    check(labels)
    check(audits)
    expected = [u['uid'] for u in lines(p / 'candidates.jsonl')]
    candidate_ids = set(expected)
    if [x['uid'] for x in labels if x['uid'] in candidate_ids] != expected:
        raise ValueError('Labels must cover every candidate once in candidate order')
    expected_audit = [u['uid'] for u in lines(p / 'audit-input.jsonl')]
    if [x['uid'] for x in audits] != expected_audit:
        raise ValueError('Audit results must cover audit-input in its exact order')
    by_label = {x['uid']: x for x in labels}
    keys = ('corrected', 'uncertain', 'injection', 'cluster')
    for a in audits:
        b = by_label.get(a['uid'])
        if b and any(a[k] != b[k] for k in keys):
            raise ValueError('Unresolved classification/audit disagreement; reconcile labels before analysis')
        by_label[a['uid']] = a
    return by_label, catalog


def analyze(args):
    inventory, users = snapshot(args.output)
    p = private_dir(args.output)
    labels, catalog = validate_labels(args.output, users)
    by_session = {s['id']: s for s in inventory}
    by_user = {u['uid']: u for u in users}
    events = validate_events(inventory, lines(p / 'events.jsonl'))
    corrections = []
    for uid, label in sorted(labels.items()):
        if not label['corrected'] or label['uncertain'] or label['injection']:
            continue
        u = by_user[uid]
        model, effort = config(events.get((u['session'], u['assistant_seq'])))
        corrections.append({'uid': uid, 'date': u['date'], 'source': u['source'], 'repo': u['repo'], 'model': model, 'effort': effort, 'cluster': label['cluster'], 'user_seq': u['nth_user'], 'message_seq': u['seq'], 'session_id': u['session'], 'summary': clean(label['summary'])})
    active = collections.defaultdict(set)
    rows = {}
    def exposure(sid, month, cfg):
        key = sid, month, *cfg
        if key not in rows:
            s = by_session[sid]
            usage = s.get('usage', [])
            token = sum(sum(e.get(k) or 0 for k in ('input_tokens', 'output_tokens', 'cache_read_tokens', 'cache_write_tokens', 'reasoning_tokens')) for e in usage) if usage else None
            rows[key] = {'session_id': sid, 'month': month, 'source': s['source'], 'repo': s.get('repo_slug') or s.get('directory') or UNKNOWN, 'model': cfg[0], 'effort': cfg[1], 'active': int(month in active[sid]), 'exposed': 0, 'user_messages': 0, 'token': token}
        return rows[key]
    for s in inventory:
        for m in s['messages']:
            active[s['id']].add(day(m.get('timestamp'), s['date'])[:7])
    for s in inventory:
        for mon in active[s['id']]:
            exposure(s['id'], mon, ('', ''))
        found = False
        for m in s['messages']:
            if m['role'] == 'assistant':
                exposure(s['id'], day(m.get('timestamp'), s['date'])[:7], config(events.get((s['id'], m['seq']))))['exposed'] = 1
                found = True
        if not found:
            exposure(s['id'], s['date'][:7], (UNKNOWN, UNKNOWN))
    for u in users:
        event = events.get((u['session'], u['assistant_seq']))
        if u['nth_user'] == 1:
            following = next((m for m in by_session[u['session']]['messages'] if m['seq'] > u['seq'] and m['role'] == 'assistant'), None)
            event = events.get((u['session'], following['seq'])) if following else None
        row = exposure(u['session'], u['date'][:7], config(event))
        row['user_messages'] += 1
        row['exposed'] = 1
    for c in corrections:
        exposure(c['session_id'], c['date'][:7], (c['model'], c['effort']))['exposed'] = 1
    exposures = [rows[k] for k in sorted(rows)]
    def aggregate(dimensions, all_time=False):
        grouped = collections.defaultdict(lambda: {'ids': set(), 'users': 0, 'corrections': 0})
        for r in exposures:
            if dimensions == ('model', 'effort') or 'model' in dimensions:
                if not r['model'] or (not all_time and not r['exposed']):
                    continue
            elif not r['active']:
                continue
            key = tuple(r[d] for d in dimensions)
            grouped[key]['ids'].add(r['session_id'])
            grouped[key]['users'] += r['user_messages']
        for c in corrections:
            key = tuple(c['date'][:7] if d == 'month' else c[d] for d in dimensions)
            grouped[key]['corrections'] += 1
        result = []
        for key, value in sorted(grouped.items()):
            n, k = len(value['ids']), value['corrections']
            result.append({**dict(zip(dimensions, key)), 'sessions': n, 'users': value['users'], 'corrections': k, 'rate': round(100 * k / n, 3) if n else None})
        return result
    repeated = []
    for cluster in sorted({c['cluster'] for c in corrections}):
        cs = [c for c in corrections if c['cluster'] == cluster]
        n = len({c['session_id'] for c in cs})
        repeated.append({'cluster': cluster, 'corrections': len(cs), 'sessions': n, 'repeated': n >= 2})
    changes = []
    if args.agents:
        if not args.agents.is_file():
            raise ValueError('--agents must point to an existing file')
        repository = command(['git', '-C', str(args.agents.parent), 'rev-parse', '--show-toplevel']).strip()
        relative = args.agents.resolve().relative_to(Path(repository).resolve())
        history = command(['git', '-C', repository, 'log', '--follow', '--format=%cs%x09%H', '--', str(relative)])
        changes = [{'date': x.split('\t')[0], 'commit': x.split('\t')[1]} for x in history.splitlines() if '\t' in x]
    attribution = read(p / 'attribution.json') if (p / 'attribution.json').exists() else {'mode': 'unrecorded'}
    coverage = {'mode': attribution['mode'], 'matched_messages': len(events), 'visible_messages': sum(m['role'] in ('user', 'assistant') for s in inventory for m in s['messages']), 'unmatched_sessions': len(set(by_session) - {e[0] for e in events})}
    stats = {'attribution': coverage, 'sessions': len(inventory), 'users': len(users), 'corrections': len(corrections), 'config_rates': aggregate(('model', 'effort'), True), 'monthly': aggregate(('month',)), 'source_monthly': aggregate(('month', 'source')), 'model_monthly': aggregate(('month', 'model', 'effort')), 'clusters': repeated, 'agents_changes': changes, 'unknown_corrections': sum(c['model'] == UNKNOWN for c in corrections), 'classification': {'candidates': len(lines(p / 'candidates.jsonl')), 'classified': len(labels), 'uncertain': sum(x['uncertain'] for x in labels.values()), 'injection': sum(x['injection'] for x in labels.values()), 'audit_rows': len(lines(p / 'audit-result.jsonl')), 'audit_mode': read(p / 'prescreen.json')['audit_mode'], 'audit_strata': read(p / 'prescreen.json')['audit_strata']}}
    write(p / 'corrections.jsonl', corrections, True)
    write(p / 'exposures.json', exposures)
    write(p / 'analysis.json', stats)
    write(p / 'analysis-bindings.json', {name: digest((p / name).read_bytes()) for name in ('inventory.json', 'users.jsonl', 'events.jsonl', 'labels.jsonl', 'audit-input.jsonl', 'audit-result.jsonl', 'clusters.json', 'prescreen.json', 'corrections.jsonl', 'exposures.json', 'analysis.json')})
    return {k: stats[k] for k in ('sessions', 'users', 'corrections', 'unknown_corrections')}


def payload(root, private=False):
    p = private_dir(root)
    for name, expected in read(p / 'analysis-bindings.json').items():
        if digest((p / name).read_bytes()) != expected:
            raise ValueError('Analysis inputs changed; rerun analyze before report/dashboard')
    stats, corrections, exposures = read(p / 'analysis.json'), lines(p / 'corrections.jsonl'), read(p / 'exposures.json')
    catalog = {c['id']: c['public_title'] for c in read(p / 'clusters.json')}
    if not private:
        sessions = {s['id']: f'session-{i + 1:05d}' for i, s in enumerate(read(p / 'inventory.json'))}
        repos = {s: f'repo-{i + 1:03d}' for i, s in enumerate(sorted({x['repo'] for x in corrections + exposures}))}
        for rows in (corrections, exposures):
            for x in rows:
                x['session_id'] = sessions[x['session_id']]
                x['repo'] = repos[x['repo']]
                if 'summary' in x:
                    x['summary'] = catalog[x['cluster']]
                if 'message_seq' in x:
                    del x['message_seq']
        for cluster in stats['clusters']:
            cluster['cluster'] = catalog[cluster['cluster']]
        stats['agents_changes'] = [{'date': c['date']} for c in stats['agents_changes']]
    for c in corrections:
        c['cluster'] = catalog[c['cluster']]
    return {'private': private, 'statistics': stats, 'corrections': corrections, 'exposures': exposures, 'tables': [{'head': ['Date', 'Commit', 'Record', 'Rule date'], 'rows': [[c['date'], c.get('commit', 'redacted'), '', 'Yes'] for c in stats['agents_changes']]}]}


def report(args):
    data = payload(args.output, args.private)
    s = data['statistics']
    out = private_dir(args.output) / 'report.md' if args.private else args.output / 'report.md'
    parts = ['# Coding agent correction audit', '', 'The correction rate is confirmed human correction events per 100 sessions. It is not a probability and can exceed 100. Rates are associated with models, tasks, and time periods; correlation does not establish that a rule change caused a difference.', '', f"Sessions: {s['sessions']}; user messages: {s['users']}; confirmed corrections: {s['corrections']}; unknown model: {s['unknown_corrections']}.", '', 'Prescreening does not provide full semantic recall, and its recall is not guaranteed. Locally inspect false negatives among excluded rows. Ambiguous and injection rows are excluded from the correction numerator; unknown remains in the denominator. Public row summaries use safe cluster titles; original text and identifiers remain under private/.', '', f"Attribution: {s['attribution']['mode']}; matched visible messages {s['attribution']['matched_messages']}/{s['attribution']['visible_messages']}; zero-match sessions {s['attribution']['unmatched_sessions']}.", '', f"Classification audit: {s['classification']['audit_mode']}, strata {s['classification']['audit_strata']}; this records coverage, not semantic accuracy.", '', '## Model × effort', '', '| Model | Effort | Corrections | Sessions | Events / 100 sessions |', '| --- | --- | ---: | ---: | ---: |']
    def esc(v):
        return str(v).replace('|', '\\|').replace('\n', ' ')
    for r in s['config_rates']:
        parts.append(f"| {esc(r['model'])} | {esc(r['effort'])} | {r['corrections']} | {r['sessions']} | {r['rate']} |")
    parts += ['', '## Monthly', '', '| Month | Corrections | Active sessions | Events / 100 sessions |', '| --- | ---: | ---: | ---: |']
    parts += [f"| {r['month']} | {r['corrections']} | {r['sessions']} | {r['rate']} |" for r in s['monthly']]
    catalog = {c['id']: c['public_title'] for c in read(private_dir(args.output) / 'clusters.json')}
    parts += ['', '## Cross-session clusters', '', '| Cluster | Corrections | Distinct sessions | Repeated |', '| --- | ---: | ---: | --- |']
    parts += [f"| {esc(catalog[r['cluster']] if args.private else r['cluster'])} | {r['corrections']} | {r['sessions']} | {r['repeated']} |" for r in s['clusters']]
    parts += ['', '## AGENTS.md changes', '', ', '.join(c['date'] for c in s['agents_changes']) or 'Not supplied / no committed history.', '', '## Corrections', '', '| Date | Model / effort | Cluster | Session | Repo | Summary |', '| --- | --- | --- | --- | --- | --- |']
    parts += ['| ' + ' | '.join(esc(r[k]) for k in ('date', 'model', 'cluster', 'session_id', 'repo', 'summary')) + ' |' for r in [{**x, 'model': x['model'] + ' / ' + x['effort']} for x in data['corrections']]]
    out.write_text('\n'.join(parts) + '\n', encoding='utf-8')
    if args.private:
        out.chmod(0o600)
    return {'report': str(out), 'private': args.private}


def dashboard(args):
    data = payload(args.output, args.private)
    out = private_dir(args.output) / 'dashboard' if args.private else args.output / 'dashboard'
    if not (out / '.blueprint.json').exists():
        if out.exists() and any(out.iterdir()):
            raise ValueError('Dashboard directory is nonempty without Blueprint manifest; choose a clean output')
        command(['blueprint', 'create', 'html', str(out)])
    template = (HERE.parent / 'references' / 'dashboard.html').read_text(encoding='utf-8')
    encoded = json.dumps(data, ensure_ascii=False, separators=(',', ':')).replace('<', '\\u003c').replace('\u2028', '\\u2028').replace('\u2029', '\\u2029')
    (out / 'index.html').write_text(template.replace('__DATA__', encoded), encoding='utf-8')
    command(['blueprint', 'check', str(out)])
    return {'dashboard': str(out), 'private': args.private, 'blueprint_check': 'passed'}


def parser():
    p = argparse.ArgumentParser(description='Reproducible local correction audit; classification is a separate semantic step.')
    p.add_argument('--output', type=Path, default=Path('.local/correction-audit') / dt.date.today().isoformat())
    commands = p.add_subparsers(dest='action', required=True)
    e = commands.add_parser('export')
    e.add_argument('--recall', default='recall')
    e.add_argument('--project', default='all')
    e.add_argument('--time', default='all')
    e.add_argument('--source')
    inputs = e.add_mutually_exclusive_group()
    inputs.add_argument('--input', type=Path, help='Frozen recall export JSONL; no recall command invoked')
    inputs.add_argument('--prepared', type=Path, help='Replay a normalized snapshot directory with inventory.json and users.jsonl')
    s = commands.add_parser('prescreen')
    s.add_argument('--batch-size', type=int, default=100)
    s.add_argument('--audit-fraction', type=float, default=.1)
    s.add_argument('--replay-audit', type=Path, help='Replay a frozen prior audit-input.jsonl sample with exact UID/hash binding')
    s.add_argument('--seed', default='correction-audit-v1')
    a = commands.add_parser('attribute')
    a.add_argument('--replay-events', type=Path, help='Replay hash/role-validated frozen events.jsonl; not a fresh native-source read')
    a.add_argument('--claude-projects', type=Path, default=Path.home() / '.claude' / 'projects')
    a = commands.add_parser('analyze')
    a.add_argument('--agents', type=Path, help='AGENTS.md whose committed Git dates should be overlaid')
    for name in ('report', 'dashboard'):
        a = commands.add_parser(name)
        visibility = a.add_mutually_exclusive_group()
        visibility.add_argument('--private', action='store_true')
        visibility.add_argument('--public', action='store_true', help='Explicit default: redact identifiers and use cluster summaries')
    return p


def main():
    args = parser().parse_args()
    os.umask(0o077)
    try:
        if args.action == 'prescreen' and (args.batch_size < 1 or not 0 < args.audit_fraction <= 1):
            raise ValueError('batch-size must be positive; audit-fraction must be in (0,1]')
        result = globals()[args.action](args)
        print(json.dumps(result, ensure_ascii=False))
    except (ValueError, OSError, KeyError, TypeError, json.JSONDecodeError) as e:
        print(f'correction-audit: {type(e).__name__}: check local input files and command options' if not isinstance(e, ValueError) or isinstance(e, json.JSONDecodeError) else f'correction-audit: {e}', file=sys.stderr)
        return 2
    return 0


if __name__ == '__main__':
    sys.exit(main())
