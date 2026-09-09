"""Comprobaciones sobre el repositorio publicado (unidad 008-publicar-bitacora).

Cubre los casos límite y de aceptación que un README roto o incompleto ya dejó pasar una
vez: enlaces que no llevan a ningún sitio, un .gitignore que sube la bitácora personal de
alguien, y README que prometen cosas (licencia, requisitos, privacidad, idioma) que el
contenido no dice de verdad.
"""

import re
import subprocess
import unittest
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
README_FILES = ["README.md", "README.en.md", "README.pt-BR.md"]

LINK_PATTERN = re.compile(r"\[[^\]]*\]\(([^)]+)\)")

# Nombres de asistentes de código con IA capaces de leer AGENTS.md. R4 pide nombrar al
# menos dos concretos; esta lista es el universo del que deben salir.
ASISTENTES_CONOCIDOS = [
    "Claude Code",
    "Cursor",
    "GitHub Copilot",
    "Codex",
    "Windsurf",
    "Cline",
]

# R4: palabras que deben aparecer indicando que suele requerir pago.
PALABRAS_PAGO = {
    "README.md": ["suscripción", "pago"],
    "README.en.md": ["subscription", "paid"],
    "README.pt-BR.md": ["assinatura", "paga"],
}

# R5: quién recibe la conversación.
PALABRAS_PROVEEDOR = {
    "README.md": ["proveedor"],
    "README.en.md": ["provider"],
    "README.pt-BR.md": ["provedor"],
}

# R8: aviso de idioma, solo en las traducciones.
PALABRAS_AVISO_IDIOMA = {
    "README.en.md": ["spanish", "español"],
    "README.pt-BR.md": ["espanhol", "español"],
}


def _leer(relpath):
    return (REPO_ROOT / relpath).read_text(encoding="utf-8")


def _enlaces_relativos(texto):
    """Devuelve los destinos de enlaces markdown que no son http(s)/mailto/anclas."""
    destinos = []
    for target in LINK_PATTERN.findall(texto):
        target = target.strip()
        if target.startswith(("http://", "https://", "mailto:")):
            continue
        target = target.split("#", 1)[0].strip()
        if not target:
            continue
        destinos.append(target)
    return destinos


def _contiene_alguna(texto_low, palabras):
    return any(p.lower() in texto_low for p in palabras)


def _contiene_todas(texto_low, palabras):
    return all(p.lower() in texto_low for p in palabras)


class TestEnlacesREADME(unittest.TestCase):
    """R1, R9, C-24: todo enlace relativo de los tres README lleva a algo que existe."""

    def test_enlaces_relativos_existen(self):
        rotos = []
        for readme in README_FILES:
            texto = _leer(readme)
            for destino in _enlaces_relativos(texto):
                if not (REPO_ROOT / destino).exists():
                    rotos.append(f"{readme} -> {destino}")
        self.assertEqual([], rotos, f"enlaces rotos encontrados: {rotos}")

    def test_enlaza_ejemplo_de_conversacion_real(self):
        # R9 (caso límite): el ejemplo de conversación real está enlazado y existe.
        ejemplo = REPO_ROOT / "pruebas" / "conversacion-01.md"
        self.assertTrue(ejemplo.exists(), "falta pruebas/conversacion-01.md en el repo")
        for readme in README_FILES:
            texto = _leer(readme)
            self.assertIn(
                "pruebas/conversacion-01.md",
                texto,
                f"{readme} no enlaza pruebas/conversacion-01.md",
            )


class TestGitignore(unittest.TestCase):
    """R6: .gitignore ignora bitácoras personales y respeta la plantilla.

    R10 (caso límite): en el repositorio solo se publica bitacora/PLANTILLA.md.
    """

    def test_ignora_bitacora_personal_pero_no_la_plantilla(self):
        bitacora_dir = REPO_ROOT / "bitacora"
        bitacora_dir.mkdir(exist_ok=True)
        prueba = bitacora_dir / "__prueba-git-status.md"
        prueba.write_text("bitácora de mentira para el test\n", encoding="utf-8")
        try:
            ignorada = subprocess.run(
                ["git", "check-ignore", "-q", str(prueba)],
                cwd=REPO_ROOT,
                capture_output=True,
            )
            self.assertEqual(
                0,
                ignorada.returncode,
                "una bitácora personal nueva en bitacora/ debería quedar ignorada por git",
            )

            plantilla = subprocess.run(
                ["git", "check-ignore", "-q", str(bitacora_dir / "PLANTILLA.md")],
                cwd=REPO_ROOT,
                capture_output=True,
            )
            self.assertNotEqual(
                0,
                plantilla.returncode,
                "PLANTILLA.md no debería quedar ignorada por .gitignore",
            )
        finally:
            prueba.unlink(missing_ok=True)

    def test_pycache_y_runtime_ignorados(self):
        gitignore = _leer(".gitignore")
        self.assertIn("__pycache__/", gitignore)
        self.assertIn(".runtime/", gitignore)

    def test_bitacora_publicada_solo_tiene_plantilla(self):
        resultado = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", "HEAD", "--", "bitacora"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
        archivos = [linea for linea in resultado.stdout.splitlines() if linea.strip()]
        self.assertEqual(
            ["bitacora/PLANTILLA.md"],
            archivos,
            "bitacora/ solo debe publicar PLANTILLA.md (R10)",
        )


class TestREADMEsCoherentes(unittest.TestCase):
    """R3, R4, R5, R8: los tres README nombran licencia, requisitos y destino real."""

    def test_licencia_mit_enlazada(self):
        licencia = REPO_ROOT / "LICENSE"
        self.assertTrue(licencia.exists(), "falta el fichero LICENSE")
        self.assertIn("MIT", licencia.read_text(encoding="utf-8"))
        for readme in README_FILES:
            texto = _leer(readme)
            self.assertIn("MIT", texto, f"{readme} no nombra la licencia MIT")
            self.assertIn(
                "](LICENSE)",
                texto,
                f"{readme} no enlaza el fichero LICENSE",
            )

    def test_requisitos_antes_de_empezar(self):
        for readme in README_FILES:
            texto = _leer(readme)
            texto_low = texto.lower()
            nombrados = sum(
                1 for a in ASISTENTES_CONOCIDOS if a.lower() in texto_low
            )
            self.assertGreaterEqual(
                nombrados,
                2,
                f"{readme} debe nombrar al menos dos asistentes de IA concretos",
            )
            self.assertTrue(
                _contiene_todas(texto_low, PALABRAS_PAGO[readme]),
                f"{readme} no avisa de que los asistentes suelen requerir pago",
            )
            self.assertIn(
                "python",
                texto_low,
                f"{readme} no menciona Python",
            )

    def test_privacidad_honesta(self):
        for readme in README_FILES:
            texto = _leer(readme)
            texto_low = texto.lower()
            self.assertTrue(
                _contiene_alguna(texto_low, PALABRAS_PROVEEDOR[readme]),
                f"{readme} no dice que la conversación va al proveedor de IA",
            )
            self.assertIn(
                ".gitignore",
                texto,
                f"{readme} no explica que la bitácora personal queda fuera de git",
            )

    def test_aviso_de_idioma_en_traducciones(self):
        for readme, palabras in PALABRAS_AVISO_IDIOMA.items():
            texto_low = _leer(readme).lower()
            self.assertTrue(
                _contiene_alguna(texto_low, palabras),
                f"{readme} no avisa de que AGENTS.md y guias/ están en español",
            )
            self.assertTrue(
                "idioma" in texto_low or "language" in texto_low,
                f"{readme} no dice que la guía responde en el idioma de quien lee",
            )


VERBOS_CONVERSAR = ("responde", "responder", "conversa", "recomend", "escrib")


class TestInstruccionDeIdioma(unittest.TestCase):
    """R7, R-20, C-25: AGENTS.md instruye responder en el idioma de la persona."""

    def test_agents_instruye_idioma_sin_deducir_pais_ni_mercado(self):
        texto_low = _leer("AGENTS.md").lower().replace("\n", " ")

        # Debe ligar explícitamente "idioma" con conversar/recomendar/escribir la
        # bitácora, no solo mencionar "idioma" de pasada (eso ya ocurre hoy al hablar de
        # no deducir país/mercado al investigar, que es una regla distinta).
        liga_idioma_con_conversar = any(
            re.search(rf"{verbo}\w*.{{0,150}}idioma", texto_low)
            or re.search(rf"idioma.{{0,150}}{verbo}\w*", texto_low)
            for verbo in VERBOS_CONVERSAR
        )
        self.assertTrue(
            liga_idioma_con_conversar,
            "AGENTS.md no liga 'idioma' con conversar/recomendar/escribir",
        )

        liga_idioma_con_bitacora = re.search(
            r"idioma.{0,300}bitácora|bitácora.{0,300}idioma", texto_low
        )
        self.assertTrue(
            liga_idioma_con_bitacora,
            "AGENTS.md no dice que la bitácora se escribe en el idioma de la persona",
        )

        self.assertTrue(
            "país" in texto_low or "pais" in texto_low,
            "AGENTS.md no aclara que el idioma no revela el país",
        )
        self.assertIn(
            "mercado",
            texto_low,
            "AGENTS.md no aclara que el idioma no revela el mercado objetivo",
        )


if __name__ == "__main__":
    unittest.main()
