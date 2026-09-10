# Contribuir a Bitácora

El producto es un protocolo conversacional. `AGENTS.md` describe la conducta de la guía;
no convierte a quien revisa el código en una persona emprendedora. Conservá la separación
entre hipótesis, fuentes verificadas y decisiones de la persona.

Para probar el inicio habitual, seguí los tres pasos del README: Claude Code instalado y
autenticado, terminal dentro de una copia limpia, `claude`, lectura de `CLAUDE.md` y su
referencia a `AGENTS.md`. Se necesitan lectura del protocolo, escritura para la memoria y
navegación para fuentes verificadas. Los permisos, historial y memoria del anfitrión siguen
sus propias reglas. Los límites de privacidad y de no ejecutar contactos, publicaciones
o gastos son instrucciones, no un aislamiento técnico. Cursor tiene una regla de entrada,
pero su retomada y lectura selectiva están pendientes de prueba.

Usá únicamente datos sintéticos. Pedí una pausa, comprobá que existe `bitacora/ACTUAL.md`
y que la plantilla no cambió; iniciá una conversación nueva en la misma carpeta y pedí
retomar. Comprobá en las lecturas que solo se cargó el resumen activo. Si hay memorias
previas, la guía debe preguntar la ruta antes de leerlas o migrarlas. No publiques archivos
personales ni logs: `.runtime/` y las bitácoras personales quedan fuera de Git.

Desde la raíz, con Python y Git disponibles:

```text
python scripts/lint_protocolo.py
python -m unittest discover -s pruebas -v
python scripts/evaluar_conversaciones.py --help
```

Para extraer una ejecución existente sin inferencias:

```text
python scripts/evaluar_conversaciones.py --jsonl .runtime/turno.jsonl
```

Un JSONL representa un turno. Estado `complete` exige evento `result` final con respuesta
no vacía; uso cero se conserva y lo no expuesto queda desconocido. Un stream incompleto,
error o fallo técnico sale con código distinto de cero. La rúbrica sigue sin evaluar:
terminar correctamente no prueba que la guía haya seguido el protocolo.

Para ejecutar un fixture sintético aislado (consume el servicio de IA autenticado):

```text
python scripts/evaluar_conversaciones.py --run sin_tema --model sonnet --effort medium --output .runtime/ensayo-nuevo
```

El lanzador busca `claude` o `claude.exe`; `--executable` acepta una ruta explícita existente.
El esfuerzo predeterminado al ejecutar es `medium`; al extraer historia desconocida es
`unknown`, que no se transmite al modelo. Se registran versión del ejecutable, huellas de
los archivos copiados, estado por turno, uso, errores, stderr y archivo final de prueba.
El último total final se usa sin sumar mensajes parciales ni repetir totales.

Esta ejecución aislada copia solo los archivos enumerados del protocolo, inyecta AGENTS
explícitamente y limita herramientas/configuración. No copia configuraciones privadas,
pero usa la autenticación y entorno del proceso. No equivale al inicio habitual ni prueba
que un editor cargue `CLAUDE.md` o lea archivos ignorados. Para acreditar integración real,
registrá aparte una ejecución con carga nativa sin inyección, herramientas disponibles,
modelo efectivo, guardado y nueva sesión; publicá solo una síntesis revisada y anónima.

Las conversaciones redactadas de `pruebas/` son ilustraciones ficticias, no resultados
observados. Los informes de evaluación deben distinguir tests locales, respuestas reales,
fallos del servicio y plataformas pendientes. Nunca conviertas una ilustración en una
prueba aprobada ni presentes fuentes inaccesibles como leídas.
