"""Synthetic, offline acceptance tests for R1–R8 and E2E-5."""
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest
from unittest.mock import patch

from motor.core import Store, Scope, Signal, canonical_url
from motor.sources import collect, import_url, HTTPClient, public_url, PublicRedirect

ROOT = Path(__file__).resolve().parents[1]
FIXTURES = ROOT / 'pruebas/fixtures/fuentes'


def scope(**changes):
    data = dict(objective='Comprender fricciones', topic='repair', market_language='idioma inglés; mercado desconocido',
                sources=['hn'], limit=10)
    return Scope(**(data | changes))


def signal(key, **changes):
    data = dict(source='hn', native_id=key, url=f'https://news.ycombinator.com/item?id={key}',
                accessed_at='2026-09-17T12:00:00+00:00', published_at='2026-09-16T12:00:00+00:00',
                access='verified', content_hash=f'hash-{key}', summary=f'Fricción sintética {key}',
                actor='taller', problem='coordinar reparaciones', consequence='tiempo perdido',
                alternative='llamadas', independence=key)
    return Signal(**(data | changes))


def group(ids):
    return dict(title='Coordinar reparaciones', signal_ids=ids,
                hypothesis='Ayudar a reducir llamadas', objection='Puede bastar una planilla',
                dimensions={'consequence': {'value': 'fuerte', 'evidence': ids[:1]},
                            'alternative': {'value': 'parcial', 'evidence': ids[:1]}})


class FakeHTTP:
    def __init__(self, source):
        self.data = json.loads((FIXTURES / f'{source}.json').read_text(encoding='utf-8'))
        self.calls = []
        self.sleeps = []

    def get(self, url):
        self.calls.append(url)
        for fragment, response in self.data.items():
            if fragment in url:
                return response
        raise AssertionError(f'Unexpected network request: {url}')

    def pause(self, seconds):
        self.sleeps.append(seconds)


class Rules(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.addCleanup(self.temp.cleanup)
        self.db = Path(self.temp.name) / 'corpus.sqlite'
        self.store = Store(self.db)
        self.addCleanup(self.store.close)
        self.run = self.store.start(scope())

    def test_R1_scope_required_before_collection(self):
        for changes in ({'topic': ''}, {'sources': []}, {'limit': 0}, {'market_language': ''}):
            with self.assertRaises(ValueError):
                self.store.start(scope(**changes))

    def test_R3_unverified_cannot_support_groups(self):
        sid = self.store.add(self.run, signal('1', access='blocked'))
        with self.assertRaises(ValueError):
            self.store.set_groups(self.run, [group([sid])])
        self.assertIn('blocked', self.store.report(self.run))

    def test_R4_all_duplicate_identities_count_once(self):
        ids = [self.store.add(self.run, signal('1')),
               self.store.add(self.run, signal('1', summary='otra extracción')),
               self.store.add(self.run, signal('2', url=signal('1').url + '&utm_source=test')),
               self.store.add(self.run, signal('3', content_hash='hash-1')),
               self.store.add(self.run, signal('4'))]
        self.store.relate(self.run, ids[-1], ids[0], 'derived_from')
        self.store.set_groups(self.run, [group(list(dict.fromkeys(ids)))])
        result = self.store.result(self.run)['groups'][0]
        self.assertEqual(result['observations'], 1)
        self.assertEqual(result['level'], 'incipiente')

    def test_R4_unknown_independence_does_not_inflate_recurrence(self):
        ids = [self.store.add(self.run, signal('1')), self.store.add(self.run, signal('2', independence=''))]
        self.store.set_groups(self.run, [group(ids)])
        self.assertEqual(self.store.result(self.run)['groups'][0]['observations'], 1)

    def test_R5_references_values_and_field_evidence_validated(self):
        sid = self.store.add(self.run, signal('1', consequence=''))
        proposals = [group([999]), group([sid])]
        proposals.append(group([sid]) | {'dimensions': {'access': {'value': 'fuerte', 'evidence': []}}})
        proposals.append(group([sid]) | {'dimensions': {'access': {'value': 'fantastic', 'evidence': [sid]}}})
        for proposal in proposals:
            with self.assertRaises(ValueError):
                self.store.set_groups(self.run, [proposal])

    def test_R6_unknown_stays_unknown_and_no_filler_hypotheses(self):
        sid = self.store.add(self.run, signal('1'))
        self.store.set_groups(self.run, [group([sid])])
        result = self.store.result(self.run)
        self.assertEqual(result['groups'][0]['dimensions']['access']['value'], 'desconocida')
        self.assertEqual(len(result['hypotheses']), 1)
        self.assertNotIn('validada', self.store.report(self.run).lower())

    def test_R7_report_survives_reopening_without_network(self):
        ids = [self.store.add(self.run, signal(str(i))) for i in (1, 2)]
        self.store.query(self.run, 'hn', 'repair', 'synthetic://fixture', 'ok')
        self.store.set_groups(self.run, [group(ids)])
        expected = self.store.report(self.run)
        self.store.close()
        with patch('urllib.request.OpenerDirector.open', side_effect=AssertionError('R7: network forbidden')):
            restored = Store(self.db)
            self.addCleanup(restored.close)
            self.assertEqual(restored.report(self.run), expected, 'R7: persistence lost the report')
            self.assertEqual(restored.result(self.run)['groups'][0]['level'], 'sustentado')
            self.assertEqual(len(restored.result(self.run)['queries']), 1)

    def test_R6_hypotheses_require_distinct_problem_evidence_and_cap_at_five(self):
        sid = self.store.add(self.run, signal('1'))
        self.store.set_groups(self.run, [group([sid]) | {'title': f'Grupo {i}'} for i in range(6)])
        self.assertEqual(len(self.store.result(self.run)['hypotheses']), 1)
        ids = [self.store.add(self.run, signal(str(i))) for i in range(2, 8)]
        self.store.set_groups(self.run, [group([i]) for i in ids])
        self.assertEqual(len(self.store.result(self.run)['hypotheses']), 5)

    def test_R7_relations_and_annotations_survive_reopening(self):
        a = self.store.add(self.run, signal('1'))
        b = self.store.add(self.run, signal('2'))
        self.store.annotate(self.run, a, {'summary': 'Paráfrasis revisada'})
        self.store.relate(self.run, b, a, 'duplicates_of')
        self.store.set_groups(self.run, [group([a, b])])
        restored = Store(self.db)
        self.addCleanup(restored.close)
        data = restored.result(self.run)
        self.assertEqual(data['signals'][0]['summary'], 'Paráfrasis revisada')
        self.assertEqual(data['groups'][0]['observations'], 1)
        self.assertEqual(len(data['relations']), 1)

    def test_R5_run_boundaries_and_atomic_group_updates(self):
        other = self.store.start(scope())
        sid = self.store.add(other, signal('1'))
        with self.assertRaises(ValueError):
            self.store.set_groups(self.run, [group([sid])])
        self.assertEqual(self.store.result(self.run)['groups'], [])

    def test_canonical_url_preserves_semantic_query(self):
        self.assertEqual(canonical_url('https://example.org/a?x=1&utm_source=x#b'), 'https://example.org/a?x=1')
        with self.assertRaises(ValueError):
            canonical_url('file:///etc/passwd')


class Connectors(unittest.TestCase):
    def test_R2_hn_limit_metadata_and_no_author_or_full_body(self):
        client = FakeHTTP('hn')
        rows, queries = collect(scope(limit=1), 'hn', client)
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0].native_id, '101')
        self.assertEqual(rows[0].access, 'verified')
        self.assertTrue(rows[0].content_hash)
        self.assertNotIn('PRIVATE_AUTHOR', repr(rows))
        self.assertNotIn('FULL_BODY', repr(rows))
        self.assertTrue(queries)

    def test_R2_stackexchange_pagination_backoff_and_limit(self):
        client = FakeHTTP('se')
        rows, _ = collect(scope(sources=['se'], limit=2), 'se', client)
        self.assertEqual(len(rows), 2)
        self.assertEqual(client.sleeps, [2])
        self.assertTrue(any('page=2' in url for url in client.calls))

    def test_R2_discourse_and_unavailable_are_visible(self):
        rows, _ = collect(scope(sources=['discourse:https://forum.example.org']),
                          'discourse:https://forum.example.org', FakeHTTP('discourse'))
        self.assertEqual(rows[0].url, 'https://forum.example.org/t/repair/10/1')
        with patch.object(HTTPClient, 'get', side_effect=OSError('unavailable')):
            rows, queries = collect(scope(), 'hn', HTTPClient())
        self.assertEqual(rows, [])
        self.assertEqual(queries[-1]['status'], 'failed')

    def test_R3_url_import_opens_source_and_marks_failure(self):
        client = FakeHTTP('url')
        row = import_url('https://example.org/problem', 'Resumen abstracto', client)
        self.assertEqual(row.access, 'verified')
        self.assertEqual(len(client.calls), 1)
        with patch.object(client, 'get', side_effect=OSError('403')):
            self.assertEqual(import_url('https://example.org/problem', '', client).access, 'blocked')


class Security(unittest.TestCase):
    def test_private_network_and_credentials_rejected(self):
        with patch('socket.getaddrinfo', return_value=[(2, 1, 6, '', ('127.0.0.1', 443))]):
            with self.assertRaises(ValueError):
                public_url('https://example.org')
            with self.assertRaises(ValueError):
                PublicRedirect().redirect_request(None, None, 302, '', {}, 'https://example.org')
        with self.assertRaises(ValueError):
            canonical_url('https://user:password@example.org')

    def test_annotations_cannot_forge_verification(self):
        temp = tempfile.TemporaryDirectory()
        self.addCleanup(temp.cleanup)
        store = Store(Path(temp.name) / 'corpus.sqlite')
        self.addCleanup(store.close)
        run = store.start(scope())
        sid = store.add(run, signal('1', access='blocked'))
        with self.assertRaises(ValueError):
            store.annotate(run, sid, {'access': 'verified'})
        self.assertEqual(store.signals(run)[0]['access'], 'blocked')


class EndToEnd(unittest.TestCase):
    def test_E2E5_cli_persistence_import_group_report_and_regeneration(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'corpus.sqlite'
            def cli(*args):
                proc = subprocess.run([sys.executable, str(ROOT / 'scripts/descubrir.py'), '--db', str(db), *args],
                                      cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(proc.returncode, 0, proc.stderr)
                return proc.stdout
            run = json.loads(cli('iniciar', '--objetivo', 'Fricciones', '--tema', 'repair',
                                 '--mercado-idioma', 'inglés, mercado desconocido', '--fuentes', 'hn', '--limite', '2'))['run']
            cli('recopilar', run, '--fixtures', str(FIXTURES))
            corpus = json.loads(cli('corpus', run))
            self.assertTrue(corpus['synthetic'])
            ids = [row['id'] for row in corpus['signals']]
            proposal = Path(tmp) / 'proposal.json'
            proposal.write_text(json.dumps([dict(title='Fricción sintética', signal_ids=ids,
                hypothesis='Investigar coordinación', objection='Evidencia insuficiente', dimensions={})]), encoding='utf-8')
            cli('agrupar', run, str(proposal))
            first = cli('informe', run)
            self.assertEqual(first, cli('informe', run))
            self.assertIn('SINTÉTICO', first)
            self.assertIn('desconocida', first)
            self.assertIn('https://news.ycombinator.com/item?id=101', first)

    def test_R8_protocol_routes_discovery_and_preserves_memory(self):
        agents = (ROOT / 'AGENTS.md').read_text(encoding='utf-8')
        self.assertIn('guias/descubrimiento.md', agents)
        self.assertIn('guias/memoria.md', agents)
        guide = (ROOT / 'guias/descubrimiento.md').read_text(encoding='utf-8')
        for text in ('scripts/descubrir.py', 'sin tema', 'desconocida', 'no alcanza', 'independencia'):
            self.assertIn(text, guide)


if __name__ == '__main__':
    unittest.main()
