"""Local checks; no dependency downloads, remote CI or network calls."""
import ast
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[2]


def run(args):
    return subprocess.run([sys.executable, *args], cwd=ROOT).returncode


def main(check):
    if check == 'full-suite':
        return run(['-m', 'unittest', 'discover', '-s', 'pruebas', '-v'])
    if check == 'e2e':
        return run(['-m', 'unittest', 'pruebas.test_descubrimiento.EndToEnd', '-v'])
    if check == 'provision-e2e':
        for path in (ROOT / 'pruebas/fixtures/fuentes').glob('*.json'):
            json.loads(path.read_text(encoding='utf-8'))
        print('Fixtures locales disponibles; E2E usa SQLite temporal, sin servicios ni red.')
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
