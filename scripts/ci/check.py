"""Local checks; no dependency downloads, remote CI or network calls."""
import ast
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def run(args, env=None):
    return subprocess.run([sys.executable, *args], cwd=ROOT, env=env).returncode


def e2e_destination():
    """Reject production by environment AND by the independently resolved destination."""
    environment = os.environ.get('BITACORA_ENV', 'local').casefold()
    if environment in ('prod', 'production'):
        raise ValueError('E2E rechaza explícitamente producción; usar entorno local, test o e2e.')
    if environment not in ('local', 'test', 'e2e'):
        raise ValueError('Entorno E2E desconocido; usar local, test o e2e.')
    allowed = ROOT.resolve() / '.runtime' / 'e2e'
    destination = Path(os.environ.get('BITACORA_E2E_ROOT', str(allowed))).resolve()
    if any(part.casefold() in ('prod', 'production') for part in destination.parts):
        raise ValueError('E2E rechaza explícitamente un destino de producción.')
    if not destination.is_relative_to(allowed):
        raise ValueError('Destino E2E fuera de .runtime/e2e; no se toca la base personal ni otros destinos.')
    return destination


def main(check):
    if check == 'full-suite':
        status = run(['-m', 'unittest', 'discover', '-s', 'pruebas', '-v'])
        if status:
            return status
        return run(['scripts/ci/e2e'])
    if check == 'e2e':
        status = run(['scripts/ci/provision-e2e'])
        if status:
            return status
        destination = str(e2e_destination())
        env = os.environ | {name: destination for name in ('TEMP', 'TMP', 'TMPDIR')}
        return run(['-m', 'unittest', 'pruebas.test_descubrimiento.EndToEnd', '-v'], env=env)
    if check == 'provision-e2e':
        try:
            destination = e2e_destination()
        except ValueError as error:
            print(error, file=sys.stderr)
            return 1
        for path in (ROOT / 'pruebas/fixtures/fuentes').glob('*.json'):
            json.loads(path.read_text(encoding='utf-8'))
        destination.mkdir(parents=True, exist_ok=True)
        print(f'Fixtures locales disponibles; SQLite temporal bajo {destination}, sin servicios ni red.')
        return 0
    if check == 'lint':
        for folder in ('motor', 'scripts', 'pruebas'):
            for path in (ROOT / folder).rglob('*.py'):
                ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        for path in (ROOT / 'scripts/ci').iterdir():
            if path.is_file() and path.suffix == '':
                ast.parse(path.read_text(encoding='utf-8'), filename=str(path))
        return run(['scripts/lint_protocolo.py'])
    if check == 'security':
        failures = []
        for path in (ROOT / 'motor').glob('*.py'):
            tree = ast.parse(path.read_text(encoding='utf-8'))
            for node in ast.walk(tree):
                if isinstance(node, ast.Call) and isinstance(node.func, ast.Name) and node.func.id in ('eval', 'exec'):
                    failures.append(f'{path.name}:{node.lineno}: dynamic execution')
                if isinstance(node, ast.Call) and any(k.arg == 'shell' and isinstance(k.value, ast.Constant) and k.value.value for k in node.keywords):
                    failures.append(f'{path.name}:{node.lineno}: shell execution')
        if failures:
            print('\n'.join(failures))
            return 1
        return run(['-m', 'unittest', 'pruebas.test_descubrimiento.Security', 'pruebas.test_readme.TestGitignore', '-v'])
    raise ValueError(check)
