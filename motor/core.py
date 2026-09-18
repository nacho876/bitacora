"""Persist evidence and compute transparent, conservative evidence levels."""
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
import json
from pathlib import Path
import sqlite3
from urllib.parse import parse_qsl, urlencode, urlsplit, urlunsplit
import uuid


def now():
    return datetime.now(timezone.utc).isoformat()


def canonical_url(value):
    parsed = urlsplit(value)
    if parsed.scheme not in ('http', 'https') or not parsed.hostname or parsed.username or parsed.password:
        raise ValueError('La fuente requiere URL pública HTTP(S), sin credenciales.')
    query = sorted((k, v) for k, v in parse_qsl(parsed.query, keep_blank_values=True)
                   if not k.lower().startswith('utm_') and k not in ('fbclid', 'gclid'))
    return urlunsplit((parsed.scheme.lower(), parsed.netloc.lower(), parsed.path or '/', urlencode(query), ''))


@dataclass
class Scope:
    objective: str
    topic: str
    market_language: str
    sources: list
    limit: int
    market_country: str = ''

    def validate(self):
        if not all(isinstance(x, str) and x.strip() for x in (self.objective, self.topic, self.market_language)):
            raise ValueError('Antes de buscar, definí objetivo, tema o actor y mercado o idioma.')
        if not self.sources or not isinstance(self.limit, int) or not 1 <= self.limit <= 100:
            raise ValueError('Declarar fuentes y un límite entre 1 y 100 por fuente.')
        if self.market_country and (len(self.market_country) != 2 or not self.market_country.isupper()
                                    or not self.market_country.isalpha()):
            raise ValueError('El país de mercado usa un código ISO 3166-1 alfa-2, por ejemplo AR.')
        for source in self.sources:
            if source not in ('hn', 'se') and not source.startswith(('se:', 'discourse:')):
                raise ValueError(f'Fuente no admitida: {source}')
            if source.startswith('discourse:'):
                canonical_url(source.split(':', 1)[1])


@dataclass
class Signal:
    source: str
    native_id: str
    url: str
    accessed_at: str
    published_at: str = ''
    access: str = 'unverified'
    content_hash: str = ''
    summary: str = ''
    actor: str = ''
    problem: str = ''
    consequence: str = ''
    alternative: str = ''
    audience_access: str = ''
    counterevidence: str = ''
    independence: str = ''
    country: str = ''
    territorial_basis: str = ''
    evidence_class: str = 'unknown'


DIMENSIONS = {'consequence': 'consequence', 'alternative': 'alternative',
              'access': 'audience_access', 'counterevidence': 'counterevidence'}
VALUES = {'fuerte', 'parcial', 'ausente', 'desconocida'}
EVIDENCE_CLASSES = {'unknown', 'direct', 'context'}


def normalized_signal(data):
    """Load current and historical JSON with conservative provenance defaults."""
    data = dict(data)
    data.setdefault('country', '')
    data.setdefault('territorial_basis', '')
    data.setdefault('evidence_class', 'unknown')
    country = data['country']
    if country and (not isinstance(country, str) or len(country) != 2 or not country.isupper()
                    or not country.isalpha()):
        raise ValueError('El país de una señal usa un código ISO 3166-1 alfa-2.')
    if country and not isinstance(data['territorial_basis'], str):
        raise ValueError('El fundamento territorial debe ser texto.')
    if country and not data['territorial_basis'].strip():
        raise ValueError('Marcar un país exige un fundamento territorial observado.')
    if data['evidence_class'] not in EVIDENCE_CLASSES:
        raise ValueError('Clase de evidencia inválida: usar unknown, direct o context.')
    return data


class Store:
    def __init__(self, path):
        path = Path(path)
        path.parent.mkdir(parents=True, exist_ok=True)
        self.db = sqlite3.connect(path)
        self.db.row_factory = sqlite3.Row
        self.db.executescript('''
            PRAGMA foreign_keys=ON;
            CREATE TABLE IF NOT EXISTS runs(id TEXT PRIMARY KEY, scope TEXT NOT NULL,
                created TEXT NOT NULL, synthetic INTEGER NOT NULL DEFAULT 0, groups_json TEXT NOT NULL DEFAULT '[]');
            CREATE TABLE IF NOT EXISTS signals(id INTEGER PRIMARY KEY, run TEXT NOT NULL REFERENCES runs(id),
                source TEXT NOT NULL, native_id TEXT NOT NULL, data TEXT NOT NULL, UNIQUE(run,source,native_id));
            CREATE TABLE IF NOT EXISTS queries(id INTEGER PRIMARY KEY, run TEXT NOT NULL REFERENCES runs(id), data TEXT NOT NULL);
            CREATE TABLE IF NOT EXISTS relations(run TEXT NOT NULL REFERENCES runs(id), a INTEGER NOT NULL REFERENCES signals(id),
                b INTEGER NOT NULL REFERENCES signals(id), kind TEXT NOT NULL, UNIQUE(run,a,b,kind));
        ''')

    def close(self):
        self.db.close()

    def _run(self, run):
        row = self.db.execute('SELECT * FROM runs WHERE id=?', (run,)).fetchone()
        if row is None:
            raise ValueError('Búsqueda inexistente; consultá el identificador devuelto por iniciar.')
        return row

    def start(self, scope):
        scope.validate()
        run = uuid.uuid4().hex[:12]
        with self.db:
            self.db.execute('INSERT INTO runs(id,scope,created) VALUES(?,?,?)',
                            (run, json.dumps(asdict(scope), ensure_ascii=False), now()))
        return run

    def synthetic(self, run):
        self._run(run)
        with self.db:
            self.db.execute('UPDATE runs SET synthetic=1 WHERE id=?', (run,))

    def add(self, run, signal):
        self._run(run)
        canonical_url(signal.url)
        if signal.access not in ('verified', 'blocked', 'unverified', 'invalid'):
            raise ValueError('Estado de acceso inválido.')
        if not signal.source or not signal.native_id or not signal.accessed_at:
            raise ValueError('La señal necesita fuente, identificador y fecha de consulta.')
        data = normalized_signal(asdict(signal))
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO signals(run,source,native_id,data) VALUES(?,?,?,?)',
                            (run, signal.source, signal.native_id, json.dumps(data, ensure_ascii=False)))
        return self.db.execute('SELECT id FROM signals WHERE run=? AND source=? AND native_id=?',
                               (run, signal.source, signal.native_id)).fetchone()[0]

    def signals(self, run):
        self._run(run)
        return [normalized_signal(json.loads(row['data'])) | {'id': row['id']} for row in
                self.db.execute('SELECT id,data FROM signals WHERE run=? ORDER BY id', (run,))]

    def annotate(self, run, sid, fields):
        allowed = {'summary', 'actor', 'problem', 'consequence', 'alternative', 'audience_access',
                   'counterevidence', 'independence', 'country', 'territorial_basis', 'evidence_class'}
        if not fields or set(fields) - allowed or any(not isinstance(v, str) or len(v) > 1000 for v in fields.values()):
            raise ValueError('Solo paráfrasis breves y campos de interpretación; no identidad ni estado de acceso.')
        row = next((s for s in self.signals(run) if s['id'] == sid), None)
        if row is None:
            raise ValueError('Señal ajena o inexistente.')
        row.pop('id')
        row.update(fields)
        row = normalized_signal(row)
        with self.db:
            self.db.execute('UPDATE signals SET data=? WHERE run=? AND id=?', (json.dumps(row, ensure_ascii=False), run, sid))

    def query(self, run, source, query, url, status, reason=''):
        self._run(run)
        data = dict(source=source, query=query, url=url, status=status, reason=reason, at=now())
        with self.db:
            self.db.execute('INSERT INTO queries(run,data) VALUES(?,?)', (run, json.dumps(data, ensure_ascii=False)))

    def relate(self, run, a, b, kind):
        ids = {s['id'] for s in self.signals(run)}
        if a not in ids or b not in ids or a == b or kind not in ('duplicates_of', 'derived_from'):
            raise ValueError('La relación necesita dos señales distintas de esta búsqueda y un tipo admitido.')
        with self.db:
            self.db.execute('INSERT OR IGNORE INTO relations VALUES(?,?,?,?)', (run, a, b, kind))

    def _roots(self, run, signals):
        parents = {s['id']: s['id'] for s in signals}
        def root(a):
            while parents[a] != a:
                a = parents[a]
            return a
        def union(a, b):
            a, b = root(a), root(b)
            parents[max(a, b)] = min(a, b)
        identities = {}
        for s in signals:
            keys = [('url', canonical_url(s['url']))]
            if s['content_hash']:
                keys.append(('hash', s['content_hash']))
            if s['independence']:
                keys.append(('observation', s['independence']))
            for key in keys:
                if key in identities:
                    union(s['id'], identities[key])
                identities[key] = s['id']
        for row in self.db.execute('SELECT a,b FROM relations WHERE run=?', (run,)):
            union(row['a'], row['b'])
        return {sid: root(sid) for sid in parents}

    def _evaluate(self, run, proposals):
        signals = self.signals(run)
        by_id = {s['id']: s for s in signals}
        roots = self._roots(run, signals)
        groups = []
        if not isinstance(proposals, list):
            raise ValueError('La propuesta debe ser una lista de grupos.')
        for proposal in proposals:
            if not isinstance(proposal, dict):
                raise ValueError('Grupo inválido.')
            ids = proposal.get('signal_ids', [])
            if not ids or len(set(ids)) != len(ids) or any(i not in by_id or by_id[i]['access'] != 'verified' for i in ids):
                raise ValueError('Un grupo solo admite señales verificadas, distintas y de esta búsqueda.')
            for field in ('title', 'hypothesis', 'objection'):
                if not isinstance(proposal.get(field), str) or not proposal[field].strip():
                    raise ValueError(f'El grupo necesita {field}.')
            observations = len({roots[i] for i in ids if by_id[i]['independence']})
            level = 'incipiente' if any(by_id[i]['problem'] for i in ids) else 'pista'
            supplied = proposal.get('dimensions', {})
            if not isinstance(supplied, dict) or set(supplied) - set(DIMENSIONS):
                raise ValueError('Dimensión desconocida; independencia y recurrencia se calculan.')
            dims = {}
            for dimension, field in DIMENSIONS.items():
                rating = supplied.get(dimension, {'value': 'desconocida', 'evidence': []})
                if not isinstance(rating, dict) or rating.get('value') not in VALUES:
                    raise ValueError('Valoración inválida.')
                evidence = rating.get('evidence', [])
                if not isinstance(evidence, list) or any(i not in ids for i in evidence):
                    raise ValueError('La valoración cita evidencia ajena al grupo.')
                if rating['value'] != 'desconocida' and (not evidence or any(not by_id[i][field] for i in evidence)):
                    raise ValueError('La valoración necesita evidencia explícita del campo; ausencia de datos es desconocida.')
                dims[dimension] = dict(value=rating['value'], evidence=evidence)
            independent_ids = [i for i in ids if by_id[i]['independence']]
            dims['independence'] = dict(value='fuerte' if observations >= 2 else 'parcial' if observations else 'desconocida', evidence=independent_ids)
            dims['recurrence'] = dict(value='fuerte' if observations >= 3 else 'parcial' if observations >= 2 else 'desconocida', evidence=independent_ids if observations >= 2 else [])
            if observations >= 2 and level != 'pista' and any(by_id[i]['consequence'] or by_id[i]['alternative'] for i in ids):
                level = 'sustentado'
            groups.append({k: proposal[k] for k in ('title', 'hypothesis', 'objection')} |
                          dict(signal_ids=ids, observations=observations, dimensions=dims, level=level))
        return groups

    def set_groups(self, run, proposals):
        self._evaluate(run, proposals)
        with self.db:
            self.db.execute('UPDATE runs SET groups_json=? WHERE id=?', (json.dumps(proposals, ensure_ascii=False), run))

    def result(self, run):
        row = self._run(run)
        signals = self.signals(run)
        roots = self._roots(run, signals)
        groups = self._evaluate(run, json.loads(row['groups_json']))
        candidates = [g for g in groups if g['level'] != 'pista']
        candidates.sort(key=lambda g: (g['level'] != 'sustentado', -g['observations'], g['title']))
        hypotheses, used_observations = [], set()
        for candidate in candidates:
            observations = {roots[i] for i in candidate['signal_ids']}
            if observations - used_observations:
                hypotheses.append(candidate)
                used_observations.update(observations)
            if len(hypotheses) == 5:
                break
        scope = json.loads(row['scope'])
        scope.setdefault('market_country', '')
        return dict(run=run, scope=scope, created=row['created'], synthetic=bool(row['synthetic']),
                    signals=[s | {'duplicate_of': roots[s['id']] if roots[s['id']] != s['id'] else None} for s in signals],
                    queries=[json.loads(q[0]) for q in self.db.execute('SELECT data FROM queries WHERE run=? ORDER BY id', (run,))],
                    relations=[dict(r) for r in self.db.execute('SELECT a,b,kind FROM relations WHERE run=? ORDER BY a,b,kind', (run,))],
                    groups=groups, hypotheses=hypotheses)

    def report(self, run):
        from motor.report import render
        return render(self.result(run))
