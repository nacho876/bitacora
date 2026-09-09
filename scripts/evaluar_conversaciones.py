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


def usage_from(event):
    """Acepta formatos stream-json comunes; `None` significa que el anfitrión no lo expuso."""
    candidates = [event, event.get("usage", {}), event.get("message", {}).get("usage", {})]
    found = {}
    aliases = {
        "input_tokens": ("input_tokens", "input"), "output_tokens": ("output_tokens", "output"),
        "cache_read_tokens": ("cache_read_input_tokens", "cache_read_tokens"),
        "cache_creation_tokens": ("cache_creation_input_tokens", "cache_creation_tokens"),
    }
    for key, names in aliases.items():
        for item in candidates:
            if isinstance(item, dict):
                value = next((number(item.get(name)) for name in names if number(item.get(name)) is not None), None)
                if value is not None:
                    found[key] = value
                    break
    return found


def extract_jsonl(path):
    events, errors, models, tools, model_usage, thinking = [], [], [], [], [], None
    for raw in path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(raw)
        except json.JSONDecodeError:
            errors.append("línea JSON inválida")
            continue
        if not isinstance(event, dict):
            continue
        events.append(event)
        for candidate in (event.get("model"), event.get("message", {}).get("model"), event.get("modelUsage", {}).get("model")):
            if isinstance(candidate, str) and candidate not in models:
                models.append(candidate)
        if event.get("type") == "error" or event.get("error"):
            errors.append(str(event.get("error") or event.get("message") or "error del anfitrión"))
        if event.get("type") == "result" and event.get("is_error"):
            errors.append(str(event.get("result") or event.get("error") or "result is_error"))
        if event.get("type") == "result":
            if isinstance(event.get("modelUsage"), dict):
                model_usage.append(event["modelUsage"])
            detail = event.get("usage", {}).get("output_tokens_details", {})
            if number(detail.get("thinking_tokens")) is not None:
                thinking = detail["thinking_tokens"]
        for block in event.get("message", {}).get("content", []):
            if isinstance(block, dict) and block.get("type") == "tool_use" and isinstance(block.get("name"), str):
                tools.append(block["name"])
    # En stream-json `result` es el total final; sumar también mensajes lo duplicaría.
    totals = [event for event in events if event.get("type") == "result" and usage_from(event)]
    if not totals:
        # Mensajes parciales pueden repetir el mismo usage. Sin total final no se inventa suma.
        totals = []
    usage = {key: None for key in ("input_tokens", "output_tokens", "cache_read_tokens", "cache_creation_tokens")}
    for event in totals:
        for key, value in usage_from(event).items():
            usage[key] = (usage[key] or 0) + value
    return {"usage": usage, "thinking_tokens": thinking, "model_usage": model_usage,
            "tools": {"count": len(tools), "names": tools}, "errors": errors, "models": models}


def find_executable(explicit=None):
    if explicit:
        path = Path(explicit)
        if path.is_file(): return path
    for base in (os.environ.get("LOCALAPPDATA"), os.environ.get("APPDATA")):
        if base:
            path = Path(base) / "npm/node_modules/@anthropic-ai/claude-code/bin/claude.exe"
            if path.is_file(): return path
    found = shutil.which("claude.exe")
    return Path(found) if found else None


def run_fixture(case_id, model, effort, output, protocol_dir, executable=None):
    """Lanza una sesión aislada; no lee memorias ni configuración de personas reales."""
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
    with tempfile.TemporaryDirectory(prefix="bitacora-fixture-") as temp:
        fixture = Path(temp)
        source_root = protocol_dir.resolve()
        for relative in ("AGENTS.md", "bitacora/PLANTILLA.md", "guias/contraste.md", "guias/memoria.md"):
            source = source_root / relative
            if relative == "bitacora/PLANTILLA.md" and not source.exists():
                source = source_root / "PLANTILLA.md"  # snapshot histórico plano
            if not source.is_file():
                continue  # la base histórica no tenía guías; no se las añade.
            target = fixture / relative
            target.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, target)
        if case.get("fixture"):
            fixture_file = fixture / case["fixture"]["path"]
            fixture_file.write_text(case["fixture"]["content"], encoding="utf-8")
        subprocess.run(["git", "init", "--quiet"], cwd=fixture, check=True, capture_output=True)
        manifest = {"case": case_id, "model_requested": model, "model_effective": "unknown", "effort": effort,
                    "protocol_dir": str(source_root), "protocol_hash": sha(source_root / "AGENTS.md"), "turns": []}
        def save():
            (output / "manifest.json").write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding="utf-8")
        def invoke(prompt, index, session, resume, phase):
            target = output / f"turn-{index:02d}.jsonl"
            args = [str(claude_exe), "--print", "--output-format", "stream-json", "--verbose", "--model", model,
                    "--effort", effort, "--safe-mode", "--restricted", "--strict-mcp-config", "--permission-mode", "dontAsk",
                    "--tools", "Read,Write,Edit,Glob,WebSearch,WebFetch", "--allowedTools", "Read,Write,Edit,Glob,WebSearch,WebFetch",
                    "--append-system-prompt-file", str(fixture / "AGENTS.md"), "--resume" if resume else "--session-id", session]
            record = {"turn": index, "phase": phase, "session": session, "resume": resume, "input": prompt,
                      "jsonl": target.name, "status": "started"}
            manifest["turns"].append(record); save()
            stderr_path = output / f"turn-{index:02d}-stderr.txt"
            with target.open("w", encoding="utf-8") as stdout, stderr_path.open("w", encoding="utf-8") as stderr:
                process = subprocess.Popen(args, stdin=subprocess.PIPE, stdout=stdout, stderr=stderr,
                                           text=True, encoding="utf-8", errors="replace", cwd=fixture, env=os.environ.copy())
                try:
                    process.communicate(prompt, timeout=240)
                    record.update({"status": "finished", "exit_code": process.returncode})
                except subprocess.TimeoutExpired:
                    process.kill(); process.communicate()
                    record.update({"status": "timeout", "exit_code": None})
            parsed = extract_jsonl(target)
            record["usage"] = parsed["usage"]; record["thinking_tokens"] = parsed["thinking_tokens"]
            record["model_usage"] = parsed["model_usage"]; record["tools"] = parsed["tools"]; record["errors"] = parsed["errors"]
            if parsed["models"]: manifest["model_effective"] = parsed["models"][-1]
            if parsed["errors"]: record["status"] = "error"
            save(); return record["status"] == "finished" and process.returncode == 0
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
    parser.add_argument("--effort", default="unknown")
    parser.add_argument("--run", choices=[item["id"] for item in json.loads((ROOT / "pruebas/casos.json").read_text(encoding="utf-8"))["cases"]])
    parser.add_argument("--output", type=Path, help="Directorio .runtime para --run")
    parser.add_argument("--protocol-dir", type=Path, default=ROOT, help="Protocolo candidato o snapshot base")
    parser.add_argument("--executable", help="Ruta explícita de claude.exe")
    args = parser.parse_args()
    if args.run:
        if not args.output or not args.model:
            parser.error("--run requiere --model y --output")
        return run_fixture(args.run, args.model, args.effort, args.output, args.protocol_dir, args.executable)
    if not args.jsonl:
        parser.error("--jsonl es obligatorio: este runner no fabrica respuestas ni credenciales")
    if not args.jsonl.is_file():
        parser.error("--jsonl no existe")
    result = extract_jsonl(args.jsonl)
    result.update({"recorded_at": datetime.now(timezone.utc).isoformat(), "model_requested": args.model or "unknown",
                   "effort": args.effort, "source": str(args.jsonl), "sha256": sha(args.jsonl)})
    print(json.dumps(result, ensure_ascii=False, indent=2))
    return 1 if result["errors"] else 0


if __name__ == "__main__":
    raise SystemExit(main())
