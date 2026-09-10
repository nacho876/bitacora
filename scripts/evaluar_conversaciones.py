#!/usr/bin/env python3
"""Ejecuta fixtures aislados y extrae uso sin transformar ausencias en cero."""
import argparse
import hashlib
import json
import os
import shutil
import subprocess
import tempfile
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def number(value):
    return value if isinstance(value, (int, float)) and not isinstance(value, bool) else None


def mapping(value):
    return value if isinstance(value, dict) else {}


def usage_from(event):
    event = mapping(event)
    candidates = [event, mapping(event.get("usage")), mapping(mapping(event.get("message")).get("usage"))]
    aliases = {
        "input_tokens": ("input_tokens", "input"), "output_tokens": ("output_tokens", "output"),
        "cache_read_tokens": ("cache_read_input_tokens", "cache_read_tokens"),
        "cache_creation_tokens": ("cache_creation_input_tokens", "cache_creation_tokens"),
    }
    found = {}
    for key, names in aliases.items():
        for item in candidates:
            value = next((number(item.get(name)) for name in names if number(item.get(name)) is not None), None)
            if value is not None:
                found[key] = value
                break
    return found


def extract_jsonl(path):
    events, errors, models, tools, model_usage, thinking = [], [], [], [], [], None
    try:
        lines = path.read_text(encoding="utf-8").splitlines()
    except UnicodeDecodeError:
        errors.append("error de decodificación: el archivo no es UTF-8 válido")
        lines = []
    for raw in lines:
        if not raw.strip():
            continue
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            errors.append("línea JSON inválida")
            continue
        if not isinstance(event, dict):
            errors.append("evento JSON debe ser objeto")
            continue
        events.append(event)
        for container, key, expected in ((event, "message", dict), (event, "usage", dict),
                (event, "modelUsage", dict), (event, "type", str), (event, "is_error", bool),
                (event, "result", str), (mapping(event.get("message")), "content", list),
                (mapping(event.get("message")), "usage", dict),
                (mapping(event.get("usage")), "output_tokens_details", dict)):
            if key in container and not isinstance(container[key], expected):
                errors.append(f"tipo inesperado en {key}")
        message = mapping(event.get("message"))
        for candidate in (event.get("model"), message.get("model")):
            if isinstance(candidate, str) and candidate not in models:
                models.append(candidate)
        if event.get("type") == "error" or event.get("error"):
            errors.append(str(event.get("error") or event.get("message") or "error del anfitrión"))
        if event.get("type") == "result" and (event.get("is_error") or event.get("subtype", "success") != "success"):
            errors.append(str(event.get("result") or event.get("error") or "result error"))
        content = message.get("content")
        for block in content if isinstance(content, list) else []:
            if not isinstance(block, dict):
                errors.append("bloque de contenido debe ser objeto")
            elif block.get("type") == "tool_use" and isinstance(block.get("name"), str):
                tools.append(block["name"])
    finals = [event for event in events if event.get("type") == "result"]
    # Un JSONL representa un turno: el último total reemplaza parciales/repetidos.
    final = finals[-1] if finals else {}
    usage = {key: None for key in ("input_tokens", "output_tokens", "cache_read_tokens", "cache_creation_tokens")}
    usage.update(usage_from(final))
    if isinstance(final.get("modelUsage"), dict):
        model_usage.append(final["modelUsage"])
    thinking = number(mapping(mapping(final.get("usage")).get("output_tokens_details")).get("thinking_tokens"))
    response = final.get("result")
    complete = bool(finals and events[-1] is final and isinstance(response, str) and response.strip())
    status = "error" if errors else "complete" if complete else "incomplete"
    return {"status": status, "incomplete_reason": ("falta evento final o respuesta no vacía" if status == "incomplete" else None),
            "rubric": "not_evaluated", "usage": usage,
            "thinking_tokens": thinking, "model_usage": model_usage,
            "tools": {"count": len(tools), "names": tools}, "errors": errors, "models": models}


def find_executable(explicit=None):
    if explicit:
        path = Path(explicit).resolve()
        if not path.is_file():
            raise ValueError("--executable no es un archivo existente")
        return path
    for name in ("claude", "claude.exe"):
        found = shutil.which(name)
        if found:
            return Path(found)
    for base in (os.environ.get("LOCALAPPDATA"), os.environ.get("APPDATA")):
        if base:
            path = Path(base) / "npm/node_modules/@anthropic-ai/claude-code/bin/claude.exe"
            if path.is_file():
                return path
    return None


def run_fixture(case_id, model, effort, output, protocol_dir, executable=None):
    """Lanza una sesión aislada; no lee memorias ni configuración de personas reales."""
    if effort not in ("low", "medium", "high", "max"):
        raise ValueError("--run requiere esfuerzo low, medium, high o max")
    cases = json.loads((ROOT / "pruebas/casos.json").read_text(encoding="utf-8"))["cases"]
    case = next((item for item in cases if item["id"] == case_id), None)
    if not case:
        raise ValueError("caso inexistente")
    claude_exe = find_executable(executable)
    if not claude_exe:
        raise RuntimeError("Claude CLI no está disponible; use --jsonl con una ejecución real")
    if output.exists():
        raise RuntimeError("--output ya existe; elegí un directorio nuevo para no mezclar ejecuciones")
    output.mkdir(parents=True)
    exit_code = 0
    version = "unknown"
    version_error = None
    try:
        version_process = subprocess.Popen([str(claude_exe), "--version"], stdout=subprocess.PIPE,
                                           stderr=subprocess.PIPE, text=True, encoding="utf-8", errors="replace")
        try:
            version_stdout, version_stderr = version_process.communicate(timeout=15)
            if version_process.returncode == 0 and version_stdout and version_stdout.strip():
                version = version_stdout.strip()
            else:
                version_error = version_stderr or "versión no disponible"
        except subprocess.TimeoutExpired:
            version_process.kill()
            version_stdout, version_stderr = version_process.communicate()
            version_error = "timeout consultando versión"
    except OSError as exc:
        version_error = str(exc)
    with tempfile.TemporaryDirectory(prefix="bitacora-fixture-") as temp:
        fixture = Path(temp)
        source_root = protocol_dir.resolve()
        fingerprints = {}
        for relative in ("AGENTS.md", "CLAUDE.md", ".cursor/rules/burbuja.mdc", "bitacora/PLANTILLA.md", "guias/contraste.md", "guias/memoria.md"):
            source = source_root / relative
            if relative == "bitacora/PLANTILLA.md" and not source.exists():
                source = source_root / "PLANTILLA.md"  # snapshot histórico plano
            if not source.is_file():
                continue  # la base histórica no tenía guías; no se las añade.
            target = fixture / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
            fingerprints[relative] = sha(target)
        if case.get("fixture"):
            fixture_file = fixture / case["fixture"]["path"]
            fixture_file.parent.mkdir(parents=True, exist_ok=True)
            fixture_file.write_text(case["fixture"]["content"], encoding="utf-8")
        subprocess.run(["git", "init", "--quiet"], cwd=fixture, check=True, capture_output=True)
        manifest = {"case": case_id, "model_requested": model, "model_effective": "unknown", "effort": effort,
                    "protocol_dir": str(source_root), "protocol_hash": sha(source_root / "AGENTS.md"),
                    "protocol_hashes": fingerprints, "executable": str(claude_exe),
                    "executable_version": version, "version_error": version_error,
                    "mode": "isolated_explicit_protocol", "rubric": "not_evaluated", "turns": []}
        def save():
            (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        def invoke(prompt, index, session, resume, phase):
            target = output / f"turn-{index:02d}.jsonl"
            args = [str(claude_exe), "--print", "--output-format", "stream-json", "--verbose", "--model", model,
                    "--effort", effort, "--safe-mode", "--strict-mcp-config", "--permission-mode", "dontAsk",
                    "--tools", "Read,Write,Edit,Glob,WebSearch,WebFetch", "--allowedTools", "Read,Write,Edit,Glob,WebSearch,WebFetch",
                    "--append-system-prompt-file", str(fixture / "AGENTS.md"), "--resume" if resume else "--session-id", session]
            record = {"turn": index, "phase": phase, "session": session, "resume": resume, "input": prompt,
                      "jsonl": target.name, "status": "started"}
            manifest["turns"].append(record); save()
            stderr_path = output / f"turn-{index:02d}-stderr.txt"
            with target.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
                try:
                    process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                                               text=True, encoding="utf-8", errors="replace", cwd=fixture, env=os.environ.copy())
                    try:
                        process.communicate(prompt, timeout=240)
                        record.update({"status": "finished" if process.returncode == 0 else "error", "exit_code": process.returncode})
                    except subprocess.TimeoutExpired:
                        process.kill(); process.communicate()
                        record.update({"status": "timeout", "exit_code": None})
                except OSError as exc:
                    stderr.write(str(exc))
                    record.update({"status": "startup_error", "exit_code": None, "startup_error": str(exc)})
            record["stderr"] = stderr_path.name
            parsed = extract_jsonl(target)
            record["usage"] = parsed["usage"]; record["thinking_tokens"] = parsed["thinking_tokens"]
            record["model_usage"] = parsed["model_usage"]; record["tools"] = parsed["tools"]; record["errors"] = parsed["errors"]
            if parsed["models"]: manifest["model_effective"] = parsed["models"][-1]
            record["parse_status"] = parsed["status"]
            if record["status"] == "finished" and parsed["status"] != "complete":
                record["status"] = parsed["status"]
            save(); return record["status"] == "finished" and record["exit_code"] == 0
        setup = next((item for item in cases if item["id"] == case.get("setup")), None)
        index, session, session_turn = 1, str(uuid.uuid4()), 0
        if setup:
            for prompt in setup["turns"]:
                if not invoke(prompt, index, session, session_turn > 0, "setup"):
                    exit_code = 1; break
                index += 1; session_turn += 1
            if exit_code:
                shutil.copytree(fixture, output / "fixture-final", dirs_exist_ok=True)
                manifest["fixture_final"] = "fixture-final"; save(); return exit_code
            session = str(uuid.uuid4())  # retomada: sesión nueva, archivos persistidos.
            session_turn = 0
        for prompt in case["turns"]:
            if not invoke(prompt, index, session, session_turn > 0, "case"):
                exit_code = 1; break
            index += 1; session_turn += 1
        shutil.copytree(fixture, output / "fixture-final", dirs_exist_ok=True)
        manifest["fixture_final"] = "fixture-final"; save()
    return exit_code


def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jsonl", type=Path, help="Salida stream-json ya obtenida del modelo")
    parser.add_argument("--model", help="Modelo solicitado; el efectivo se extrae de JSONL")
    parser.add_argument("--effort", choices=["low", "medium", "high", "max", "unknown"],
                        help="--run: medium por defecto; extracción histórica: unknown")
    parser.add_argument("--run", choices=[item["id"] for item in json.loads((ROOT / "pruebas/casos.json").read_text(encoding="utf-8"))["cases"]])
    parser.add_argument("--output", type=Path, help="Directorio .runtime para --run")
    parser.add_argument("--protocol-dir", type=Path, default=ROOT, help="Protocolo candidato o snapshot base")
    parser.add_argument("--executable", help="Ruta explícita de claude o claude.exe")
    args = parser.parse_args()
    if args.run:
        if not args.output or not args.model:
            parser.error("--run requiere --model y --output")
        try:
            code = run_fixture(args.run, args.model, args.effort or "medium", args.output, args.protocol_dir, args.executable)
            print(f"{'COMPLETO (rúbrica pendiente)' if code == 0 else 'ERROR/INCOMPLETO'}: {args.output / 'manifest.json'}")
            if code:
                print(f"Diagnóstico y stderr por turno: {args.output}")
            return code
        except (ValueError, OSError, RuntimeError, subprocess.SubprocessError) as exc:
            parser.error(str(exc))
    if not args.jsonl:
        parser.error("--jsonl es obligatorio: este runner no fabrica respuestas ni credenciales")
    if not args.jsonl.is_file():
        parser.error("--jsonl no existe")
    result = extract_jsonl(args.jsonl)
    result.update({"recorded_at": datetime.now(timezone.utc).isoformat(), "model_requested": args.model or "unknown",
                   "effort": args.effort or "unknown", "source": str(args.jsonl), "sha256": sha(args.jsonl)})
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 0 if result["status"] == "complete" else 1


if __name__ == "__main__":
    raise SystemExit(main())
