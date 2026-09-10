# Evaluación local — 2026-09-09

Esta evaluación combina tests de software con conversaciones reales de Claude Code sobre
entradas sintéticas. La conversación de `conversacion-01.md` es una ilustración redactada;
no forma parte de la evidencia real. Un proceso terminado no equivale a una aprobación de
conducta. No se probaron Cursor ni otras plataformas.

## Comprobaciones técnicas

El defecto original era reproducible: un archivo JSONL vacío terminaba con éxito y algunos
tipos JSON nulos provocaban excepciones. Se escribieron los tests antes de corregirlo:
12 tests, 5 fallos y 11 errores (incluidos subcasos). Los mismos tests quedaron verdes. La suite local final ejecutó 34 tests con resultado
OK; el linter estructural dio 0 FAIL y la ayuda del evaluador terminó correctamente.

La cobertura ampliada comprueba final con respuesta no vacía, tipos inesperados, cero real
y datos desconocidos, ausencia de doble cómputo, ejecutables portables, ruta explícita,
esfuerzo válido, versión y huellas, errores de arranque, timeout y conservación de archivos.
Una contraprueba con el módulo de la base `5ff417e` volvió a fallar: 17 tests, 6 fallos y
16 errores. No se reemplazó el código candidato para hacer esa contraprueba.

La revisión añadió una regresión por bytes no UTF-8: el extractor ahora informa estado
`error`, la CLI termina con salida distinta de cero sin traceback y el archivo original
permanece intacto. Los dos tests fallaron sobre `af98b82` y pasan con la corrección; no se
reemplazan bytes inválidos para aceptar una respuesta corrompida.

El humo real del runner detectó un flag heredado no admitido por Claude Code 2.1.236:
`--restricted`. Se retiró ese flag, conservando safe-mode, permisos y herramientas
acotadas; la regresión de argumentos pasó de un fallo a verde. Una repetición real de
`--run sin_tema --model sonnet` sin `--effort`, en un directorio de salida nuevo, terminó
con código 0, respuesta completa y esfuerzo registrado `medium`.

## Recorridos conversacionales observados

Entorno: Claude Code **2.1.236**, modelo efectivo **claude-sonnet-5**, esfuerzo **medium**.
Fueron pruebas por fases, con snapshots y huellas por archivo; no una sesión monolítica
ni una comparación de ahorro. El AGENTS final tiene SHA-256
`7560ba9d5dffca1e4908079cf1c8bc876baa3ce4b5f78a1230148719c954e889`.

Las pruebas se ejecutaron por CLI sin interfaz interactiva (headless), con `--print`
y salida `--output-format stream-json`; no se probó la interfaz interactiva del editor.
El inicio usa carga nativa de `CLAUDE.md` y su referencia a `AGENTS.md`, sin inyección por
`--append-system-prompt`. Se ejecuta en una carpeta limpia con memoria automática, hooks,
skills y MCP desactivados, herramientas acotadas y archivos persistidos entre sesiones.
Esta prueba controlada no equivale a todas las configuraciones posibles del editor.

En `recorrido-01` (snapshot previo), el inicio aportó tres candidatos y una pregunta. El contraste hizo
búsquedas, pero no leyó la guía ni abrió las páginas antes de inferir cobertura. La
advertencia de privacidad repitió identificadores sintéticos. Ambos incumplimientos se
conservaron como resultados observados, y motivaron instrucciones más explícitas.

`recorrido-02` (otro snapshot previo) repitió el contraste y leyó la guía, hizo dos búsquedas e intentó abrir cuatro URLs:
un dominio `.invalid` falló, una página solo devolvió el título y dos devolvieron contenido.
Mejoró la distinción entre búsqueda y acceso, pero el razonamiento comercial siguió siendo
parcial: estimó acceso sin datos, relacionó las opciones como un único negocio, comparó una
alternativa no abierta y omitió fechas visibles por fuente. No se declara aprobado todo el
contraste ni se presenta esa comparación como validación de mercado.

`memoria-03` (snapshot previo al AGENTS final) conservó las opciones y la plantilla, pero la retomada leyó el
archivo completo sin límite de líneas y sin consultar primero la guía de memoria. No
se declara aprobada esa lectura: se explicitó el disparador y el límite de la herramienta
antes de repetir únicamente la retomada sobre una copia byte por byte del mismo archivo
sintético. Esa nueva sesión, `retomada-05`, usó el AGENTS final y leyó primero la guía y luego ACTUAL.md con `offset: 1,
limit: 20`: conservó las dos opciones y las cuatro horas semanales. La plantilla siguió
intacta y el archivo personal quedó excluido de Git.

Entre los recorridos de carga nativa, solo `retomada-05` y sus turnos de idiomas usaron
el AGENTS final de la huella indicada
arriba. El guardado inicial y el caso de abstracción sensible se observaron con snapshots
anteriores: no se vuelven a atribuir sus resultados a una ejecución con el protocolo final.

| Fase y snapshot | Evidencia observada | Resultado acotado |
| --- | --- | --- |
| Guardado — `memoria-03`, previo | ACTUAL.md creado sin identificadores; conserva ambas opciones; plantilla intacta | Guardado comprobado con ese snapshot |
| Abstracción sensible — `privacidad-04`, previo | Antes de confirmar no creó ACTUAL.md ni repitió valores; después guardó solo la versión general confirmada, marcada ficticia | Privacidad y confirmación comprobadas en ese caso sintético y snapshot |
| Retomada — `retomada-05`, AGENTS final, turno 1 | Copia idéntica del archivo de memoria-03; guía leída y Read limitado a 20 líneas; ambas opciones conservadas | Lectura selectiva comprobada en la repetición |
| Inglés — `retomada-05`, AGENTS final, turno 2 | Respondió en inglés y mantuvo las opciones | Idioma observado; hizo una afirmación de costo no comprobada |
| Portugués y pausa — `retomada-05`, AGENTS final, turno 3 | Respondió y actualizó el resumen en portugués mediante Edit; ambas opciones conservadas | Idioma y persistencia observados |

Los archivos finales no incluyeron los identificadores sintéticos probados y quedaron
ignorados por Git; sus plantillas conservaron la misma huella. Esto no demuestra aislamiento
técnico, eliminación del historial del proveedor ni obediencia universal del modelo.
Persisten límites de rigor al inferir costo, acceso o cobertura comercial: revisar esos
supuestos antes de tomar decisiones. No se declara aprobación integral del protocolo.

## Reproducir sin publicar datos

Seguí el inicio del README en una copia limpia y con Claude Code autenticado. Usá una idea
ficticia, pedí mantener opciones y pausar, verificá `bitacora/ACTUAL.md` y que la plantilla
no cambió. Cerrá la sesión y abrí otra en la misma carpeta; pedí retomar y observá que se
lea únicamente el resumen activo. Para privacidad usá identificadores sintéticos y
comprobá respuesta, herramientas y archivo antes y después de confirmar una abstracción.

Los fixtures de `casos.json` permiten nuevas pruebas aisladas. El runner copia archivos
seleccionados e inyecta el protocolo, por lo que sus resultados no acreditan por sí solos
la carga nativa. `CONTRIBUTING.md` describe ambas vías y los comandos locales. No publiques
logs, rutas personales ni identificadores; conservá localmente las huellas y salidas.
