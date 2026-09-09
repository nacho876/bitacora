#!/usr/bin/env python3
"""Comprobación estructural del núcleo y sus lecturas bajo demanda; no prueba conducta."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FAIL = []


def require(path, fragments):
    text = path.read_text(encoding="utf-8") if path.is_file() else ""
    for fragment in fragments:
        if fragment.casefold() not in text.casefold():
            FAIL.append(f"{path.relative_to(ROOT)}: falta {fragment!r}")


def main():
    require(ROOT / "AGENTS.md", ["Bitácora", "experiencia, curiosidad", "no tener tema", "primera respuesta aportá 2–3", "como máximo una pregunta", "pausar",
            "sin contenido verificado", "no acreditan acceso real", "no pidas permiso por cada consulta",
            "no reconfirmación", "guias/contraste.md", "guias/memoria.md", "resumen activo"])
    require(ROOT / "guias/contraste.md", ["conducta", "usuario y comprador", "mercado objetivo",
            "entrevistas u observaciones separadas", "independientes aunque", "señal directa", "contexto indirecto",
            "Hipótesis de oportunidad", "objeción decisiva", "no hay hipótesis de oportunidad sustentada"])
    require(ROOT / "guias/memoria.md", ["abstracciones confirmadas", "ficticias", "retomar"])
    require(ROOT / "bitacora/PLANTILLA.md", ["REGLA DURA", "Resumen activo", "problema observado",
            "pista externa", "Hipótesis y objeciones", "sin contenido verificado", "no acreditan acceso real"])
    require(ROOT / "README.md", ["Bitácora", "ficticios", "AGENTS.md"])
    for redirect in (ROOT / "CLAUDE.md", ROOT / ".cursor/rules/burbuja.mdc"):
        require(redirect, ["AGENTS.md", "Bitácora"])
    if FAIL:
        print("Comprobación estructural; no acredita comportamiento.")
        print("\n".join("FAIL " + item for item in FAIL))
        return 1
    print("Comprobación estructural; no acredita comportamiento.\n0 FAIL")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
