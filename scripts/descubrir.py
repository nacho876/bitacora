#!/usr/bin/env python3
"""On-demand research, with a durable corpus and no implicit model calls."""
import argparse
from dataclasses import asdict
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from motor.core import Scope, Store
from motor.sources import HTTPClient, FixtureHTTP, collect, import_url


def parser():
    p = argparse.ArgumentParser(description=__doc__)
    p.add_argument('--db', default=str(ROOT / '.runtime/descubrimiento/corpus.sqlite'))
    commands = p.add_subparsers(dest='command', required=True)
    start = commands.add_parser('iniciar', help='Guardar alcance antes de consultar fuentes')
    for flag in ('objetivo', 'tema', 'mercado-idioma'):
        start.add_argument('--' + flag, required=True)
    start.add_argument('--mercado-pais', default='', help='Código ISO alfa-2 separado del idioma, por ejemplo AR')
    start.add_argument('--fuentes', required=True, nargs='+', help='hn, se[:sitio], discourse:https://foro')
    start.add_argument('--limite', type=int, required=True, help='1–100 resultados por fuente')
    fetch = commands.add_parser('recopilar')
    fetch.add_argument('run')
    fetch.add_argument('--fixtures', help='Carpeta sintética: marca toda la búsqueda como prueba')
    for name in ('corpus', 'informe'):
        cmd = commands.add_parser(name)
        cmd.add_argument('run')
        if name == 'informe':
            cmd.add_argument('--salida', help='Archivo Markdown; por defecto salida estándar')
    imp = commands.add_parser('importar-url', help='Abrir URL pública y guardar paráfrasis; no acepta estados autodeclarados')
    imp.add_argument('run')
    imp.add_argument('url')
    imp.add_argument('--resumen', default='')
    imp.add_argument('--pais', default='', help='País observado; exige fundamento territorial')
    imp.add_argument('--fundamento-territorial', default='')
    imp.add_argument('--clase-evidencia', choices=['unknown', 'direct', 'context'], default='unknown')
    unavailable = commands.add_parser('registrar-fuente', help='Conservar una fuente pertinente que no pudo consultarse')
    unavailable.add_argument('run')
    unavailable.add_argument('source')
    unavailable.add_argument('--motivo', required=True)
    annotate = commands.add_parser('anotar')
    annotate.add_argument('run')
    annotate.add_argument('signal', type=int)
    annotate.add_argument('file', help='JSON con campos interpretativos breves')
    group = commands.add_parser('agrupar')
    group.add_argument('run')
    group.add_argument('file', help='JSON con una lista de grupos propuestos por el asistente')
    relate = commands.add_parser('relacionar')
    relate.add_argument('run')
    relate.add_argument('a', type=int)
    relate.add_argument('b', type=int)
    relate.add_argument('kind', choices=['duplicates_of', 'derived_from'])
    return p


def main(argv=None):
    args = parser().parse_args(argv)
    store = Store(args.db)
    try:
        result = {'ok': True}
        if args.command == 'iniciar':
            result = {'run': store.start(Scope(args.objetivo, args.tema, args.mercado_idioma, args.fuentes,
                                               args.limite, args.mercado_pais))}
        elif args.command == 'recopilar':
            scope = Scope(**store.result(args.run)['scope'])
            if args.fixtures:
                store.synthetic(args.run)
            for source in scope.sources:
                client = FixtureHTTP(args.fixtures, source) if args.fixtures else HTTPClient()
                rows, queries = collect(scope, source, client)
                for query in queries:
                    store.query(args.run, **query)
                for row in rows:
                    store.add(args.run, row)
            result = store.result(args.run)
        elif args.command == 'importar-url':
            store._run(args.run)
            row = import_url(args.url, args.resumen, HTTPClient(), args.pais, args.fundamento_territorial,
                             args.clase_evidencia)
            sid = store.add(args.run, row)
            store.query(args.run, 'url', 'URL añadida explícitamente', row.url, row.access)
            result = asdict(row) | {'id': sid}
        elif args.command == 'registrar-fuente':
            if not args.source.strip() or not args.motivo.strip():
                raise ValueError('La fuente inaccesible necesita nombre y motivo.')
            store.query(args.run, args.source, 'Fuente pertinente prevista', '', 'unavailable', args.motivo)
        elif args.command == 'anotar':
            store.annotate(args.run, args.signal, json.loads(Path(args.file).read_text(encoding='utf-8-sig')))
        elif args.command == 'agrupar':
            store.set_groups(args.run, json.loads(Path(args.file).read_text(encoding='utf-8-sig')))
        elif args.command == 'relacionar':
            store.relate(args.run, args.a, args.b, args.kind)
        elif args.command == 'corpus':
            result = store.result(args.run)
        elif args.command == 'informe':
            report = store.report(args.run)
            if args.salida:
                path = Path(args.salida)
                if path.exists():
                    raise ValueError('El informe destino ya existe; elegí otro nombre para conservarlo.')
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(report, encoding='utf-8')
                result = {'report': str(path)}
            else:
                print(report, end='')
                return 0
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (ValueError, OSError, TypeError, KeyError) as error:
        print(f'No se completó la operación: {error}', file=sys.stderr)
        return 1
    finally:
        store.close()


if __name__ == '__main__':
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8')
        sys.stderr.reconfigure(encoding='utf-8')
    raise SystemExit(main())
