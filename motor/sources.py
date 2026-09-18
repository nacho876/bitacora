"""Small bounded clients for official public APIs; no credentials or bypasses."""
from datetime import datetime, timezone
import hashlib
import html
import ipaddress
import json
import re
import socket
import time
from urllib.error import HTTPError
from urllib.parse import urlencode, urlsplit
from urllib.request import Request, HTTPRedirectHandler, build_opener

from motor.core import Signal, canonical_url, now


def public_url(url):
    canonical_url(url)
    host = urlsplit(url).hostname
    addresses = socket.getaddrinfo(host, urlsplit(url).port or 443, type=socket.SOCK_STREAM)
    if not addresses or any(not ipaddress.ip_address(item[4][0]).is_global for item in addresses):
        raise ValueError('Solo fuentes públicas; no se consultan servicios privados o locales.')


class PublicRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        public_url(newurl)
        return super().redirect_request(req, fp, code, msg, headers, newurl)


class HTTPClient:
    def pause(self, seconds):
        if not 0 <= seconds <= 120:
            raise ValueError('Backoff superior al límite local; reintentar más tarde.')
        time.sleep(seconds)

    def get(self, url):
        public_url(url)
        self.pause(0.1)
        request = Request(url, headers={'User-Agent': 'Bitacora-Local/1.0 (public research)', 'Accept': 'application/json,text/html'})
        try:
            with build_opener(PublicRedirect()).open(request, timeout=20) as response:
                raw = response.read(2_000_001)
                if len(raw) > 2_000_000:
                    raise ValueError('Respuesta demasiado grande para esta consulta acotada.')
                decoded = raw.decode('utf-8')
                return json.loads(decoded) if 'json' in response.headers.get('Content-Type', '') else decoded
        except HTTPError as error:
            # Preserve the failure, do not retry past server limits or bypass a block.
            if error.code == 429:
                raise OSError('Fuente limitada (429); reintentar más tarde.') from error
            raise


def digest(content):
    normalized = ' '.join(html.unescape(re.sub('<[^>]*>', ' ', str(content))).casefold().split())
    return hashlib.sha256(normalized.encode('utf-8')).hexdigest() if normalized else ''


def date(value):
    return datetime.fromtimestamp(value, timezone.utc).isoformat() if isinstance(value, (int, float)) else str(value or '')


def import_url(url, summary, client):
    url = canonical_url(url)
    try:
        content = client.get(url)
        if not content:
            raise ValueError('Fuente vacía')
        return Signal('url', url, url, now(), access='verified', content_hash=digest(content), summary=summary)
    except (OSError, ValueError):
        return Signal('url', url, url, now(), access='blocked')


def collect(scope, source, client):
    scope.validate()
    if source not in scope.sources:
        raise ValueError('La fuente no forma parte del alcance declarado.')
    rows, queries = [], []
    def get(url):
        entry = dict(source=source, query=scope.topic, url=url, status='ok')
        queries.append(entry)
        try:
            return client.get(url)
        except (OSError, ValueError):
            entry['status'] = 'failed'
            raise
    try:
        if source == 'hn':
            base = 'https://hacker-news.firebaseio.com/v0/'
            pending = list(get(base + 'askstories.json')[:100])
            visited = set()
            while pending and len(visited) < 100 and len(rows) < scope.limit:
                item_id = pending.pop(0)
                if item_id in visited:
                    continue
                visited.add(item_id)
                item = get(base + f'item/{item_id}.json')
                if not item or item.get('deleted') or item.get('dead'):
                    continue
                pending.extend(item.get('kids', [])[:5])
                content = item.get('title', '') + ' ' + item.get('text', '')
                if not any(word.casefold() in content.casefold() for word in scope.topic.split()):
                    continue
                rows.append(Signal(source, str(item['id']), f"https://news.ycombinator.com/item?id={item['id']}",
                                   now(), date(item.get('time')), 'verified', digest(content)))
        elif source == 'se' or source.startswith('se:'):
            site = source.split(':', 1)[1] if ':' in source else 'stackoverflow'
            for page in range(1, 11):
                params = urlencode(dict(page=page, pagesize=min(scope.limit - len(rows), 100), order='desc',
                                        sort='relevance', q=scope.topic, site=site, filter='withbody'))
                response = get('https://api.stackexchange.com/2.3/search/advanced?' + params)
                if response.get('error_id'):
                    raise ValueError('La API rechazó la consulta; revisar sitio y alcance.')
                for item in response.get('items', []):
                    rows.append(Signal(source, str(item['question_id']), canonical_url(item['link']), now(),
                                       date(item.get('creation_date')), 'verified', digest(item.get('title', '') + ' ' + item.get('body', ''))))
                    if len(rows) == scope.limit:
                        break
                if len(rows) >= scope.limit or not response.get('has_more') or response.get('quota_remaining', 1) <= 0:
                    break
                if response.get('backoff'):
                    client.pause(response['backoff'])
        elif source.startswith('discourse:'):
            base = source.split(':', 1)[1].rstrip('/')
            for page in range(1, 11):
                response = get(base + '/search.json?' + urlencode(dict(q=scope.topic, page=page)))
                topics = {t['id']: t.get('slug', 'topic') for t in response.get('topics', [])}
                for item in response.get('posts', []):
                    # A search blurb is not the underlying publication: open the post itself.
                    post = get(base + f"/posts/{item['id']}.json")
                    url = base + f"/t/{topics.get(post['topic_id'], 'topic')}/{post['topic_id']}/{post['post_number']}"
                    rows.append(Signal(source, str(post['id']), url, now(), date(post.get('created_at')), 'verified', digest(post.get('cooked', ''))))
                    if len(rows) == scope.limit:
                        break
                if len(rows) >= scope.limit or not response.get('grouped_search_result', {}).get('more_full_page_results'):
                    break
        else:
            raise ValueError('Fuente no admitida.')
    except (OSError, ValueError, KeyError, TypeError):
        if queries:
            queries[-1]['status'] = 'failed'
        else:
            queries.append(dict(source=source, query=scope.topic, url='', status='failed'))
    return rows, queries


class FixtureHTTP:
    """Explicit synthetic transport for reproducible offline examples."""
    def __init__(self, folder, source):
        from pathlib import Path
        name = source.split(':', 1)[0]
        self.responses = json.loads((Path(folder) / f'{name}.json').read_text(encoding='utf-8'))

    def get(self, url):
        for fragment, response in self.responses.items():
            if fragment in url:
                return response
        raise ValueError('No existe respuesta sintética para esta URL.')

    def pause(self, seconds):
        pass
