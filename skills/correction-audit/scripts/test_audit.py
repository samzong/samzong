import importlib.util
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

HERE = Path(__file__).resolve().parent
spec = importlib.util.spec_from_file_location('audit', HERE / 'audit.py')
audit = importlib.util.module_from_spec(spec)
spec.loader.exec_module(audit)


class AuditContracts(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name) / 'run'
        self.p = audit.private_dir(self.root)

    def tearDown(self):
        self.temp.cleanup()

    def invoke(self, *args, expected=0):
        result = subprocess.run([sys.executable, str(HERE / 'audit.py'), '--output', str(self.root), *args], capture_output=True, text=True)
        self.assertEqual(result.returncode, expected, result.stderr)
        return result

    def fixture(self):
        ms = lambda date: int(__import__('datetime').datetime.fromisoformat(date + 'T12:00:00+00:00').timestamp() * 1000)
        sessions = [
            {'id': 'private-session-a', 'source': 'codex', 'thread_role': 'primary', 'source_id': 'a', 'source_file_path': str(self.p / 'missing-source'), 'repo_slug': 'private/repo-a', 'date': '2026-05-31', 'users': 2, 'messages': [
                {'seq': 0, 'role': 'user', 'timestamp': ms('2026-05-31'), 'text_sha256': 'a' * 64},
                {'seq': 1, 'role': 'assistant', 'timestamp': ms('2026-05-31'), 'text_sha256': 'b' * 64},
                {'seq': 2, 'role': 'user', 'timestamp': ms('2026-06-01'), 'text_sha256': 'c' * 64},
                {'seq': 3, 'role': 'assistant', 'timestamp': ms('2026-06-01'), 'text_sha256': 'd' * 64}], 'usage': []},
            {'id': 'private-session-b', 'source': 'codex', 'thread_role': 'primary', 'source_id': 'b', 'source_file_path': str(self.p / 'missing-b'), 'repo_slug': 'private/repo-b', 'date': '2026-06-01', 'users': 2, 'messages': [
                {'seq': 0, 'role': 'user', 'timestamp': ms('2026-06-01'), 'text_sha256': 'e' * 64},
                {'seq': 1, 'role': 'assistant', 'timestamp': ms('2026-06-01'), 'text_sha256': 'f' * 64},
                {'seq': 2, 'role': 'user', 'timestamp': ms('2026-06-01'), 'text_sha256': '0' * 64}], 'usage': []}]
        users = [
            {'uid': 1, 'session': sessions[0]['id'], 'source': 'codex', 'repo': 'private/repo-a', 'date': '2026-05-31', 'seq': 0, 'nth_user': 1, 'assistant_seq': None, 'text_sha256': 'a' * 64, 'text': 'Do a task'},
            {'uid': 2, 'session': sessions[0]['id'], 'source': 'codex', 'repo': 'private/repo-a', 'date': '2026-06-01', 'seq': 2, 'nth_user': 2, 'assistant_seq': 1, 'text_sha256': 'c' * 64, 'text': 'wrong, avoid the private label'},
            {'uid': 3, 'session': sessions[1]['id'], 'source': 'codex', 'repo': 'private/repo-b', 'date': '2026-06-01', 'seq': 0, 'nth_user': 1, 'assistant_seq': None, 'text_sha256': 'e' * 64, 'text': 'Do a task'},
            {'uid': 4, 'session': sessions[1]['id'], 'source': 'codex', 'repo': 'private/repo-b', 'date': '2026-06-01', 'seq': 2, 'nth_user': 2, 'assistant_seq': 1, 'text_sha256': '0' * 64, 'text': 'wrong, avoid the private label'}]
        audit.write(self.p / 'inventory.json', sessions)
        audit.write(self.p / 'users.jsonl', users, True)
        self.invoke('prescreen', '--audit-fraction', '1')
        audit.write(self.p / 'clusters.json', [{'id': 'scope', 'public_title': 'Unrequested scope', 'definition': 'agent changed scope'}])
        labels = [{'uid': u['uid'], 'text_sha256': u['text_sha256'], 'corrected': True, 'uncertain': False, 'injection': False, 'cluster': 'scope', 'summary': 'Private person PRIVATE_NAME asked about /home/private/project', 'reason': 'explicit correction of prior assistant'} for u in users if u['nth_user'] > 1]
        audit.write(self.p / 'labels.jsonl', labels, True)
        ordered = {x['uid']: x for x in labels}
        audit.write(self.p / 'audit-result.jsonl', [ordered[x['uid']] for x in audit.lines(self.p / 'audit-input.jsonl')], True)
        events = [{'session_id': sessions[0]['id'], 'inventory_seq': 1, 'model': 'model-a', 'effort': 'high'}, {'session_id': sessions[0]['id'], 'inventory_seq': 3, 'model': 'model-b', 'effort': 'low'}, {'session_id': sessions[1]['id'], 'inventory_seq': 1, 'model': 'model-a', 'effort': 'high'}]
        for e in events:
            e['kind'] = 'assistant'
            e['text_sha256'] = next(m['text_sha256'] for session in sessions if session['id'] == e['session_id'] for m in session['messages'] if m['seq'] == e['inventory_seq'])
        audit.write(self.p / 'events.jsonl', events, True)
        return labels

    def test_switch_cross_month_denominators_and_public_output(self):
        self.fixture()
        self.invoke('analyze')
        stats = audit.read(self.p / 'analysis.json')
        self.assertEqual([(x['month'], x['sessions'], x['corrections']) for x in stats['monthly']], [('2026-05', 1, 0), ('2026-06', 2, 2)])
        self.assertEqual([(x['model'], x['sessions'], x['users'], x['corrections']) for x in stats['config_rates']], [('model-a', 2, 4, 2), ('model-b', 1, 0, 0)])
        self.assertTrue(stats['clusters'][0]['repeated'])
        self.invoke('report')
        public = (self.root / 'report.md').read_text()
        for private in ('private-session', 'private/repo', 'PRIVATE_NAME', '/home/private'):
            self.assertNotIn(private, public)
        self.invoke('report', '--private')
        self.assertIn('PRIVATE_NAME', (self.p / 'report.md').read_text())
        self.invoke('dashboard', '--public')
        self.assertTrue((self.root / 'dashboard' / 'index.html').is_file())
        self.assertNotIn('PRIVATE_NAME', (self.root / 'dashboard' / 'index.html').read_text())
        self.invoke('dashboard', '--private')
        self.assertIn('PRIVATE_NAME', (self.p / 'dashboard' / 'index.html').read_text())
        self.assertEqual(self.p.stat().st_mode & 0o777, 0o700)
        self.assertEqual((self.p / 'labels.jsonl').stat().st_mode & 0o777, 0o600)

    def test_missing_source_single_source_and_empty_adapters(self):
        self.fixture()
        self.invoke('attribute')
        self.assertEqual(audit.lines(self.p / 'events.jsonl'), [])
        self.invoke('analyze')
        stats = audit.read(self.p / 'analysis.json')
        self.assertEqual(stats['config_rates'][0]['model'], 'unknown')
        self.assertEqual(stats['unknown_corrections'], 2)

    def test_hash_binding_missing_labels_and_disagreement(self):
        labels = self.fixture()
        labels[0]['text_sha256'] = 'bad'
        audit.write(self.p / 'labels.jsonl', labels, True)
        self.assertIn('hash/UID', self.invoke('analyze', expected=2).stderr)
        labels[0]['text_sha256'] = 'c' * 64
        labels.pop()
        audit.write(self.p / 'labels.jsonl', labels, True)
        self.assertIn('every candidate', self.invoke('analyze', expected=2).stderr)
        labels = self.fixture()
        labels[0]['corrected'] = False
        audit.write(self.p / 'labels.jsonl', labels, True)
        self.assertIn('disagreement', self.invoke('analyze', expected=2).stderr)

    def test_input_changes_invalidate_render(self):
        self.fixture()
        self.invoke('analyze')
        with (self.p / 'labels.jsonl').open('a') as out:
            out.write('\n')
        self.assertIn('inputs changed', self.invoke('report', expected=2).stderr)

    def test_event_and_candidate_tampering_rejected(self):
        self.fixture()
        events = audit.lines(self.p / 'events.jsonl')
        events[0]['text_sha256'] = 'bad'
        audit.write(self.p / 'events.jsonl', events, True)
        self.assertIn('role/hash', self.invoke('analyze', expected=2).stderr)
        self.fixture()
        audit.write(self.p / 'candidates.jsonl', [], True)
        self.assertIn('Prescreen inputs changed', self.invoke('analyze', expected=2).stderr)

    def test_frozen_events_replay_and_derived_tampering(self):
        self.fixture()
        archived = self.p / 'archived-events.jsonl'
        audit.write(archived, audit.lines(self.p / 'events.jsonl'), True)
        self.invoke('attribute', '--replay-events', str(archived))
        self.assertEqual(audit.read(self.p / 'attribution.json')['mode'], 'frozen_event_replay')
        self.invoke('analyze')
        audit.write(self.p / 'corrections.jsonl', [], True)
        self.assertIn('inputs changed', self.invoke('report', expected=2).stderr)

    def test_repository_fallback_consistency(self):
        self.fixture()
        inventory = audit.read(self.p / 'inventory.json')
        inventory[0]['repo_slug'] = None
        inventory[0]['directory'] = '/home/private/repo-a'
        users = audit.lines(self.p / 'users.jsonl')
        for user in users:
            if user['session'] == inventory[0]['id']:
                user['repo'] = inventory[0]['directory']
        audit.write(self.p / 'inventory.json', inventory)
        audit.write(self.p / 'users.jsonl', users, True)
        self.invoke('prescreen', '--audit-fraction', '1')
        self.invoke('analyze')
        corrections = audit.lines(self.p / 'corrections.jsonl')
        exposures = audit.read(self.p / 'exposures.json')
        for correction in corrections:
            self.assertEqual({row['repo'] for row in exposures if row['session_id'] == correction['session_id']}, {correction['repo']})

    def test_public_cluster_statistics_remove_private_ids(self):
        labels = self.fixture()
        private_id = 'private-repo-a-secretproj'
        audit.write(self.p / 'clusters.json', [{'id': private_id, 'public_title': 'Scope correction', 'definition': 'scope'}])
        for label in labels:
            label['cluster'] = private_id
        audit.write(self.p / 'labels.jsonl', labels, True)
        audit.write(self.p / 'audit-result.jsonl', labels, True)
        self.invoke('analyze')
        self.assertNotIn(private_id, json.dumps(audit.payload(self.root)))
        self.assertIn(private_id, json.dumps(audit.payload(self.root, True)))

    def test_invalid_export_can_retry_and_replay_provenance(self):
        prepared = Path(self.temp.name) / 'prepared'
        prepared.mkdir()
        sessions = [{'id': 's', 'thread_role': None, 'messages': []}]
        audit.write(prepared / 'inventory.json', sessions)
        audit.write(prepared / 'users.jsonl', [], True)
        self.invoke('export', '--prepared', str(prepared), expected=2)
        self.assertFalse((self.p / 'inventory.json').exists())
        self.assertFalse((self.p / 'users.jsonl').exists())
        sessions[0]['thread_role'] = 'primary'
        audit.write(prepared / 'inventory.json', sessions)
        self.invoke('export', '--prepared', str(prepared))
        self.assertEqual(audit.read(self.p / 'export.json')['command'], ['prepared snapshot'])

    def test_missing_agents_file_is_error(self):
        self.fixture()
        self.assertIn('existing file', self.invoke('analyze', '--agents', str(self.p / 'absent.md'), expected=2).stderr)

    def test_missing_recall_and_empty_export(self):
        self.assertIn('not installed', self.invoke('export', '--recall', 'missing-recall-executable-0000', expected=2).stderr)
        empty = Path(self.temp.name) / 'empty.jsonl'
        empty.write_text('')
        self.assertIn('No primary sessions', self.invoke('export', '--input', str(empty), expected=2).stderr)

    def test_raw_export_and_credential_removal(self):
        source = Path(self.temp.name) / 'export.jsonl'
        audit.write(source, [{'session': {'id': 'session', 'source': 'future-source', 'topology': {'thread_role': 'primary'}, 'started_at': 1780272000000}, 'messages': [{'seq': 0, 'role': 'user', 'content': 'password=DO_NOT_SAVE_THIS\ntext\u2028after\u0085newline', 'timestamp': 1780272000000}]}], True)
        self.invoke('export', '--input', str(source))
        self.assertEqual(audit.read(self.p / 'export.json')['command'], ['frozen raw export', str(source)])
        text = (self.p / 'users.jsonl').read_text()
        self.assertNotIn('DO_NOT_SAVE_THIS', text)
        self.assertIn('credential line removed', text)
        self.invoke('attribute')
        self.invoke('prescreen')
        audit.write(self.p / 'labels.jsonl', [], True)
        audit.write(self.p / 'audit-result.jsonl', [], True)
        self.invoke('analyze')
        stats = audit.read(self.p / 'analysis.json')
        self.assertEqual(stats['config_rates'][0]['sessions'], 1)
        self.assertEqual(stats['corrections'], 0)
        self.assertIn('already exists', self.invoke('export', '--input', str(source), expected=2).stderr)


if __name__ == '__main__':
    unittest.main()
