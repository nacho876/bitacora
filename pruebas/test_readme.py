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


def _git_toplevel_de_repo_root():
    """Raíz del árbol de trabajo git que contiene REPO_ROOT, o None si no hay ninguno.

    Descargar el repositorio como ZIP no trae `.git`: `git rev-parse` falla y
    devolvemos None. Descomprimirlo DENTRO de otro repositorio git sí da un árbol,
    pero su raíz no es REPO_ROOT: lo distinguimos comparando toplevels.
    """
    try:
        dentro = subprocess.run(
            ["git", "rev-parse", "--is-inside-work-tree"],
            cwd=REPO_ROOT,
            capture_output=True,
            text=True,
        )
    except OSError:
        return None
    if dentro.returncode != 0 or dentro.stdout.strip() != "true":
        return None
    top = subprocess.run(
        ["git", "rev-parse", "--show-toplevel"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    if top.returncode != 0 or not top.stdout.strip():
        return None
    return Path(top.stdout.strip()).resolve()


def _exigir_arbol_git_propio(test):
    """Salta el test EXPLÍCITAMENTE si REPO_ROOT no es la raíz de su propio árbol git."""
    top = _git_toplevel_de_repo_root()
    if top is None:
        test.skipTest(
            "sin árbol de trabajo git (repositorio descargado como ZIP): esta "
            "comprobación necesita git y se omite a propósito, no en silencio"
        )
    if top != REPO_ROOT:
        test.skipTest(
            f"el repositorio está descomprimido dentro de OTRO árbol git ({top}): "
            "git respondería por el .gitignore del repositorio padre, así que esta "
            "comprobación se omite a propósito"
        )


def _ficheros_versionados():
    resultado = subprocess.run(
        ["git", "ls-files", "-z"],
        cwd=REPO_ROOT,
        capture_output=True,
        text=True,
    )
    return [p for p in resultado.stdout.split("\0") if p]


# R4, tercera cláusula: "Python solo para las comprobaciones, no para usar Bitácora".
# Por README, la negación que debe acompañar a "python" y una palabra que ate la frase
# a las comprobaciones. Que aparezca la palabra "python" no basta: el bloque de
# comandos ya la trae.
FRASE_PYTHON_OPCIONAL = {
    "README.md": (["no"], ["comprobacion"]),
    "README.en.md": (["not"], ["check"]),
    "README.pt-BR.md": (["não", "nao"], ["verificaç", "verificac"]),
}

# Encabezado de la sección de los tres pasos de inicio, por README.
HEADING_TRES_PASOS = {
    "README.md": "## Empezá en tres pasos",
    "README.en.md": "## Start in three steps",
    "README.pt-BR.md": "## Comece em três passos",
}


def _sin_bloques_de_codigo(texto):
    return re.sub(r"```.*?```", "", texto, flags=re.DOTALL)


def _sin_linea_conmutador(texto):
    """El texto sin la línea del conmutador de idiomas de la cabecera.

    Esa línea (`[Español](README.md) · [English](README.en.md) · ...`) mete la
    palabra "Español" en los tres README y haría pasar en vano cualquier búsqueda
    del aviso de idioma de R8.
    """
    return "\n".join(
        linea
        for linea in texto.splitlines()
        if not ("(README.md)" in linea and "(README.en.md)" in linea and "(README.pt-BR.md)" in linea)
    )


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

        # El disco no es el árbol publicado: un enlace a un fichero ignorado por
        # git pasaría lo anterior y daría 404 en GitHub. Exigimos que cada destino
        # esté versionado.
        _exigir_arbol_git_propio(self)
        versionados = _ficheros_versionados()
        no_publicados = []
        for readme in README_FILES:
            for destino in _enlaces_relativos(_leer(readme)):
                d = destino.rstrip("/")
                if not any(p == d or p.startswith(d + "/") for p in versionados):
                    no_publicados.append(f"{readme} -> {destino}")
        self.assertEqual(
            [],
            no_publicados,
            f"enlaces a ficheros no versionados (404 en GitHub): {no_publicados}",
        )

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
        _exigir_arbol_git_propio(self)
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
        _exigir_arbol_git_propio(self)
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
        licencia_texto = licencia.read_text(encoding="utf-8")
        self.assertIn("MIT", licencia_texto)
        # R3: "a nombre de Nacho" — el titular del copyright, no solo el tipo.
        self.assertRegex(
            licencia_texto,
            r"Copyright \(c\) \d{4} Nacho",
            "el LICENSE no lleva el copyright a nombre de Nacho",
        )
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

            # R4: no basta con que "python" aparezca (el bloque de comandos ya la
            # trae). Tiene que estar la afirmación de que solo hace falta para las
            # comprobaciones, negación incluida, fuera del bloque de código.
            prosa_low = _sin_bloques_de_codigo(texto).lower()
            negaciones, palabras_chequeo = FRASE_PYTHON_OPCIONAL[readme]
            frases_python = [
                frase for frase in re.split(r"[.\n]+", prosa_low) if "python" in frase
            ]
            afirma_opcional = any(
                _contiene_alguna(frase, negaciones)
                and _contiene_alguna(frase, palabras_chequeo)
                for frase in frases_python
            )
            self.assertTrue(
                afirma_opcional,
                f"{readme} no dice que Python solo se necesita para las "
                "comprobaciones, no para usar Bitácora",
            )

            # El nombre de este test promete un orden: los requisitos van ANTES del
            # primer paso de la sección de inicio.
            pos_requisitos = prosa_low.find("python")
            idx_heading = prosa_low.find(HEADING_TRES_PASOS[readme].lower())
            self.assertNotEqual(
                -1, idx_heading, f"{readme} no tiene la sección de los tres pasos"
            )
            paso_uno = re.search(r"\n\s*1\.\s", prosa_low[idx_heading:])
            self.assertIsNotNone(
                paso_uno, f"{readme} no tiene una lista numerada de pasos de inicio"
            )
            self.assertLess(
                pos_requisitos,
                idx_heading + paso_uno.start(),
                f"{readme}: el párrafo de requisitos aparece después del primer "
                "paso de inicio, no antes",
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
            # Sin la línea del conmutador: si no, "Español" se cuela por
            # `[Español](README.md)` y la mitad de R8 pasaría en vano.
            cuerpo = _sin_linea_conmutador(_leer(readme))
            cuerpo_low = cuerpo.lower()
            parrafos = re.split(r"\n\s*\n", cuerpo_low)
            avisa_del_espanol = any(
                _contiene_alguna(parrafo, palabras)
                and ("agents.md" in parrafo or "guias/" in parrafo)
                for parrafo in parrafos
            )
            self.assertTrue(
                avisa_del_espanol,
                f"{readme} no avisa de que AGENTS.md y guias/ están redactados en "
                "español (idioma que le falta nombrar junto al protocolo)",
            )
            self.assertTrue(
                "idioma" in cuerpo_low or "language" in cuerpo_low,
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


class TestConversacionDeEjemplo(unittest.TestCase):
    """R11: pruebas/conversacion-01.md es una conversación, y nada más."""

    EJEMPLO = "pruebas/conversacion-01.md"

    # Marcadores del informe interno de evaluación que NO deben publicarse.
    MARCADORES_INFORME_INTERNO = [
        "No acreditado",
        "USD",
        ".runtime/",
        "002-exploracion-problemas",
        "FAIL R1",
        "No apto",
    ]

    def test_sin_el_informe_interno_de_evaluacion(self):
        texto = _leer(self.EJEMPLO)
        presentes = [m for m in self.MARCADORES_INFORME_INTERNO if m in texto]
        self.assertEqual(
            [],
            presentes,
            f"{self.EJEMPLO} conserva marcadores del informe interno: {presentes}",
        )
        titulo = texto.splitlines()[0].lower()
        self.assertNotIn(
            "reales",
            titulo,
            f"el título de {self.EJEMPLO} sigue anunciando ejecuciones «reales»",
        )

    def test_conserva_la_transcripcion_y_el_aviso_de_ficcion(self):
        texto_low = _leer(self.EJEMPLO).lower()
        self.assertIn(
            "ficticia",
            texto_low,
            f"{self.EJEMPLO} no conserva el aviso de que la conversación es ficticia",
        )
        self.assertIn(
            "**guía:**",
            texto_low,
            f"{self.EJEMPLO} no conserva la transcripción de la conversación",
        )


if __name__ == "__main__":
    unittest.main()
