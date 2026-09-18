"""Synthetic, offline acceptance tests for R1–R8 and E2E-5."""
import json
import importlib.util
import os
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
                sources=['hn'], limit=10, market_country='')
    return Scope(**(data | changes))


def signal(key, **changes):
    data = dict(source='hn', native_id=key, url=f'https://news.ycombinator.com/item?id={key}',
                accessed_at='2026-09-17T12:00:00+00:00', published_at='2026-09-16T12:00:00+00:00',
                access='verified', content_hash=f'hash-{key}', summary=f'Fricción sintética {key}',
                actor='taller', problem='coordinar reparaciones', consequence='tiempo perdido',
                alternative='llamadas', independence=key, country='', territorial_basis='',
                evidence_class='unknown')
    return Signal(**(data | changes))


def group(ids):
    return dict(title='Coordinar reparaciones', signal_ids=ids,
                hypothesis='Ayudar a reducir llamadas', objection='Puede bastar una planilla',
                dimensions={'consequence': {'value': 'fuerte', 'evidence': ids[:1]},
                            'alternative': {'value': 'parcial', 'evidence': ids[:1]}})


def report_section(report, heading):
    start = report.index(f'### {heading}')
    end = report.find('\n### ', start + len(heading) + 4)
    return report[start:end if end >= 0 else len(report)]


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

    def test_AR_R1_market_country_is_structured_and_optional(self):
        argentina = self.store.start(scope(market_country='AR'))
        self.assertEqual(self.store.result(argentina)['scope']['market_country'], 'AR')
        self.assertEqual(self.store.result(self.run)['scope']['market_country'], '')
        self.assertNotIn('Cobertura argentina:', self.store.report(self.run))
        with self.assertRaises(ValueError):
            self.store.start(scope(market_country='Argentina'))

    def test_AR_R2_country_requires_basis_and_spanish_does_not_imply_argentina(self):
        spanish = self.store.add(self.run, signal('es', summary='Relato en español'))
        self.assertEqual(self.store.signals(self.run)[0]['country'], '')
        with self.assertRaises(ValueError):
            self.store.add(self.run, signal('ar-no-basis', country='AR', evidence_class='direct'))
        self.store.annotate(self.run, spanish, {'country': 'AR', 'territorial_basis': 'El relato ubica el comercio en Córdoba',
                                                'evidence_class': 'direct'})
        self.assertEqual(self.store.signals(self.run)[0]['country'], 'AR')

    def test_AR_R4_coverage_deduplicates_verified_local_direct_accounts(self):
        run = self.store.start(scope(market_country='AR'))
        local = dict(country='AR', territorial_basis='Actividad comercial ubicada en Argentina',
                     evidence_class='direct')
        a = self.store.add(run, signal('ar-1', **local, independence='episode-1'))
        self.store.add(run, signal('ar-copy', **local, content_hash='hash-ar-1', independence='episode-copy'))
        self.store.add(run, signal('global-es', country='US', territorial_basis='Relato ubicado en Estados Unidos',
                                   evidence_class='direct', independence='global-1'))
        self.store.add(run, signal('spanish-only', summary='Publicación global en español',
                                   independence='global-2'))
        report = self.store.report(run)
        self.assertIn('Relatos argentinos verificados e independientes: **1**', report)
        self.assertIn('Cobertura argentina: **insuficiente**', report)
        b = self.store.add(run, signal('ar-2', **local, independence='episode-2'))
        self.store.set_groups(run, [group([a, b])])
        report = self.store.report(run)
        self.assertIn('Relatos argentinos verificados e independientes: **2**', report)
        self.assertIn('Cobertura argentina: **mínima alcanzada**', report)

    def test_AR_R4_each_coverage_clause_excludes_an_observation(self):
        run = self.store.start(scope(market_country='AR'))
        local = dict(country='AR', territorial_basis='Actividad ubicada en Argentina')
        self.store.add(run, signal('qualifying', **local, evidence_class='direct', independence='episode-1'))
        self.store.add(run, signal('blocked', **local, access='blocked', evidence_class='direct',
                                   independence='episode-blocked'))
        self.store.add(run, signal('context', **local, evidence_class='context', independence='episode-context'))
        self.store.add(run, signal('dependent', **local, evidence_class='direct', independence=''))
        report = self.store.report(run)
        self.assertIn('Relatos argentinos verificados e independientes: **1**', report)
        self.assertIn('Cobertura argentina: **insuficiente**', report)

    def test_AR_R4_report_separates_all_provenance_classes(self):
        run = self.store.start(scope(market_country='AR'))
        self.store.add(run, signal('local', country='AR', territorial_basis='Comercio situado en Rosario',
                                   evidence_class='direct'))
        self.store.add(run, signal('context', country='AR', territorial_basis='Estadística nacional agregada',
                                   evidence_class='context'))
        self.store.add(run, signal('global', country='US', territorial_basis='Publicación ubicada en Estados Unidos',
                                   evidence_class='direct'))
        self.store.add(run, signal('unknown', summary='Publicación global en español'))
        report = self.store.report(run)
        for heading in ('Relatos argentinos', 'Contexto argentino', 'Señales globales', 'Procedencia desconocida'):
            self.assertIn(f'### {heading}', report)

    def test_AR_R4_unverified_or_unclassified_argentine_signals_are_not_local_accounts(self):
        run = self.store.start(scope(market_country='AR'))
        basis = 'La página identifica actividad en Argentina'
        blocked = self.store.add(run, signal('blocked-ar', access='blocked', country='AR',
                                             territorial_basis=basis, evidence_class='direct'))
        unclassified = self.store.add(run, signal('unknown-ar', country='AR', territorial_basis=basis,
                                                  evidence_class='unknown'))
        report = self.store.report(run)
        local_accounts = report_section(report, 'Relatos argentinos')
        honest = report_section(report, 'Señales argentinas no acreditadas')
        self.assertNotIn(f'S{blocked} ', local_accounts)
        self.assertNotIn(f'S{unclassified} ', local_accounts)
        self.assertIn(f'S{blocked} ', honest)
        self.assertIn(f'S{unclassified} ', honest)
        self.assertIn('Procedencia: AR · clase: unknown', honest)

    def test_AR_R7_historical_json_gets_unknown_provenance_defaults(self):
        sid = self.store.add(self.run, signal('legacy'))
        row = self.store.db.execute('SELECT data FROM signals WHERE id=?', (sid,)).fetchone()[0]
        legacy = json.loads(row)
        for field in ('country', 'territorial_basis', 'evidence_class'):
            legacy.pop(field)
        with self.store.db:
            self.store.db.execute('UPDATE signals SET data=? WHERE id=?', (json.dumps(legacy), sid))
        restored = Store(self.db)
        self.addCleanup(restored.close)
        loaded = restored.result(self.run)['signals'][0]
        self.assertEqual((loaded['country'], loaded['territorial_basis'], loaded['evidence_class']), ('', '', 'unknown'))

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

    def test_AR_R3_import_records_observed_basis_but_blocked_url_never_counts(self):
        client = FakeHTTP('url')
        row = import_url('https://example.org/problem', 'Relato', client, country='AR',
                         territorial_basis='La página identifica una pyme argentina', evidence_class='direct')
        self.assertEqual((row.access, row.country, row.evidence_class), ('verified', 'AR', 'direct'))
        with patch.object(client, 'get', side_effect=OSError('403')):
            blocked = import_url('https://example.org/problem', '', client, country='AR',
                                 territorial_basis='Resultado no abierto', evidence_class='direct')
        self.assertEqual(blocked.access, 'blocked')
        with tempfile.TemporaryDirectory() as tmp:
            store = Store(Path(tmp) / 'corpus.sqlite')
            run = store.start(scope(market_country='AR'))
            sid = store.add(run, blocked)
            report = store.report(run)
            store.close()
        self.assertIn('Relatos argentinos verificados e independientes: **0**', report)
        self.assertIn('Cobertura argentina: **insuficiente**', report)
        self.assertNotIn(f'S{sid} ', report_section(report, 'Relatos argentinos'))
        self.assertIn(f'S{sid} ', report_section(report, 'Señales argentinas no acreditadas'))


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

    def test_AR_E2E_scope_import_unavailable_source_and_reproducible_report(self):
        with tempfile.TemporaryDirectory() as tmp:
            db = Path(tmp) / 'corpus.sqlite'
            def cli(*args, expected=0):
                proc = subprocess.run([sys.executable, str(ROOT / 'scripts/descubrir.py'), '--db', str(db), *args],
                                      cwd=ROOT, capture_output=True, text=True, encoding='utf-8')
                self.assertEqual(proc.returncode, expected, proc.stderr)
                return proc.stdout
            run = json.loads(cli('iniciar', '--objetivo', 'Problemas locales', '--tema', 'comercios',
                                 '--mercado-idioma', 'español', '--mercado-pais', 'AR',
                                 '--fuentes', 'hn', '--limite', '2'))['run']
            cli('registrar-fuente', run, 'reddit', '--motivo', 'OAuth aprobado no disponible')
            with patch('motor.sources.HTTPClient.get', return_value='<html>relato</html>'):
                from scripts import descubrir
                self.assertEqual(descubrir.main(['--db', str(db), 'importar-url', run, 'https://example.org/ar',
                    '--resumen', 'Relato local', '--pais', 'AR', '--fundamento-territorial',
                    'El relato ubica el comercio en Argentina', '--clase-evidencia', 'direct']), 0)
            first = cli('informe', run)
            self.assertEqual(first, cli('informe', run))
            self.assertIn('reddit', first)
            self.assertIn('OAuth aprobado no disponible', first)
            self.assertIn('Cobertura argentina: **insuficiente**', first)

    def test_AR_R6_protocol_requires_opening_and_classifying_local_sources(self):
        guide = (ROOT / 'guias/descubrimiento.md').read_text(encoding='utf-8')
        agents = (ROOT / 'AGENTS.md').read_text(encoding='utf-8')
        for text in ('--mercado-pais AR', 'fundamento territorial', 'estadísticas agregadas', 'Reddit'):
            self.assertIn(text, guide)
        self.assertIn('mercado argentino', agents.lower())


class CheckRunners(unittest.TestCase):
    def setUp(self):
        spec = importlib.util.spec_from_file_location('discovery_ci_checks', ROOT / 'scripts/ci/check.py')
        self.check = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(self.check)

    def test_full_suite_calls_standalone_e2e_and_propagates_failure(self):
        with patch.object(self.check, 'run', side_effect=[0, 23]) as runner:
            self.assertEqual(self.check.main('full-suite'), 23)
        self.assertEqual(runner.call_args_list[-1].args[0], ['scripts/ci/e2e'])
        with patch.object(self.check, 'run', return_value=17) as runner:
            self.assertEqual(self.check.main('full-suite'), 17)
            self.assertEqual(runner.call_count, 1)

    def test_e2e_provisions_first_and_stops_on_failure(self):
        with patch.object(self.check, 'run', return_value=29) as runner:
            self.assertEqual(self.check.main('e2e'), 29)
        self.assertEqual(runner.call_count, 1)
        self.assertEqual(runner.call_args.args[0], ['scripts/ci/provision-e2e'])
        with patch.object(self.check, 'run', side_effect=[0, 31]) as runner:
            self.assertEqual(self.check.main('e2e'), 31)
        self.assertEqual(runner.call_count, 2)

    def test_provision_independent_environment_and_destination_guards(self):
        safe = ROOT / '.runtime/e2e'
        cases = [('production', str(safe)), ('prod', str(safe)),
                 ('local', str(ROOT / 'bitacora')), ('test', str(safe / 'production')),
                 ('e2e', str(safe / '..' / '..' / 'bitacora'))]
        for environment, destination in cases:
            with self.subTest(environment=environment, destination=destination):
                with patch.dict(os.environ, {'BITACORA_ENV': environment, 'BITACORA_E2E_ROOT': destination}):
                    with patch.object(Path, 'mkdir') as mkdir:
                        self.assertEqual(self.check.main('provision-e2e'), 1)
                        mkdir.assert_not_called()
        with patch.dict(os.environ, {'BITACORA_ENV': 'test', 'BITACORA_E2E_ROOT': str(safe)}):
            self.assertEqual(self.check.e2e_destination(), safe.resolve())


if __name__ == '__main__':
    unittest.main()
