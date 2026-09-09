# Bitácora

[Español](README.md) · [English](README.en.md) · [Português](README.pt-BR.md)

**Una guía conversacional para explorar oportunidades de emprendimiento con un asistente de IA, sin entregar la decisión a la IA.**

Bitácora ayuda a transformar una experiencia, una curiosidad, una idea ajena —o el simple “no sé por dónde empezar”— en posibilidades que vale la pena entender mejor. Su objetivo no es prometer un negocio validado: es ayudarte a aprender qué investigar, qué sigue siendo una hipótesis y cuál podría ser tu próximo experimento.

Está pensada para quien quiere emprender pero todavía no tiene una dirección clara, o quiere contrastar una que ya tiene. Vos marcás el ritmo: podés abrir opciones, profundizar en varias, elegir una, volver atrás o pausar.

## Cómo funciona

1. **Partí de donde estás.** Contá una experiencia, una curiosidad, una idea que viste o decí que no tenés tema. La guía aporta posibilidades y preguntas que puedan cambiar una decisión, sin exigirte un cuestionario ni una idea previa.
2. **Abrí el mapa.** Separá lo observado, las pistas externas, los hechos, las hipótesis y las dudas. Podés seguir explorando sin comprometerte con una oportunidad.
3. **Elegí qué contrastar.** Cuando quieras, priorizá uno o varios candidatos. La guía compara evidencia, alternativas, acceso y objeciones; una tendencia o un competidor no se presentan como validación.
4. **Decidí el próximo experimento.** Con tus objetivos, tiempo y recursos a la vista, recibís una recomendación razonada y su principal objeción. Solo vos decidís profundizar, descartar, mantener opciones abiertas o pausar. Si elegís una oportunidad, la guía puede proponerte un experimento pequeño; no lo ejecuta por vos.

## Empezá en tres pasos

Necesitás un asistente de código con IA capaz de leer `AGENTS.md` —por ejemplo, [Claude Code](https://claude.com/claude-code) o [Cursor](https://cursor.com)—; la mayoría de estos asistentes requieren una suscripción de pago. Python **no** hace falta para usar Bitácora: solo lo necesitás si querés correr las comprobaciones del protocolo (sección más abajo).

1. Cloná o descargá este repositorio en tu computadora.
2. Abrí la carpeta con un asistente de código con IA que pueda leer [`AGENTS.md`](AGENTS.md).
3. Empezá una conversación como hablarías con alguien. Por ejemplo: *“Quiero aprender a emprender, pero no sé por dónde empezar.”*

No hace falta instalar una aplicación ni completar un formulario. Bitácora es un repositorio de instrucciones para usar con un asistente compatible; funciona sobre tu copia local.

## Privacidad y límites

- Tu conversación viaja al proveedor de IA del asistente que uses (por ejemplo, Anthropic si usás Claude Code); revisá su política de privacidad antes de compartir algo sensible.
- Trabajá en tu copia del repositorio. La guía no debe guardar ni repetir nombres, contactos, empleador, dirección u otros identificadores; ante un dato sensible, propone una versión general y pide confirmación antes de guardarla.
- Tu bitácora personal vive en `bitacora/` y el `.gitignore` la deja fuera de git: no se sube sola cuando hacés un commit. Tampoco se comparte con otra persona salvo cocreación explícita en el mismo repositorio. Bitácora no envía mensajes, no publica, no compra ni hace gastos en tu nombre.
- Distingue evidencia de hipótesis. Una fuente no leída, un ejemplo, una tendencia o la existencia de competencia no prueba por sí sola que haya demanda ni que una oportunidad vaya a funcionar.
- Los materiales de [`pruebas/`](pruebas/) son ejemplos ficticios: sirven para verificar el protocolo y no son recuerdos reales ni evidencia de mercado. Podés leer [una conversación completa de ejemplo](pruebas/conversacion-01.md) para ver cómo se ve en la práctica.
- No reemplaza investigación, validación con personas, asesoramiento profesional ni ejecución. No hace un plan de negocio completo, no crea una empresa y no garantiza resultados.

## Dentro del repositorio

| Archivo o carpeta | Para qué sirve |
| --- | --- |
| [`AGENTS.md`](AGENTS.md) | El protocolo que sigue el asistente durante la conversación. |
| [`bitacora/PLANTILLA.md`](bitacora/PLANTILLA.md) | El punto de partida para tu bitácora personal. |
| [`guias/`](guias/) | Guías de contraste y memoria que se consultan cuando hacen falta. |
| [`pruebas/`](pruebas/) | Ejemplos ficticios y comprobaciones del comportamiento esperado. |
| [`scripts/`](scripts/) | Utilidades para revisar el protocolo y evaluar conversaciones. |
| [`LICENSE`](LICENSE) | La licencia MIT bajo la que se publica este repositorio. |

## Comprobaciones locales

```text
python3 scripts/lint_protocolo.py
python3 -m unittest discover -s pruebas
python3 scripts/evaluar_conversaciones.py --help
```

En Windows, donde `python3` suele no existir, usá `python` en su lugar.

## Licencia y contribuciones

Bitácora se publica bajo la licencia [MIT](LICENSE): podés usarla, copiarla y modificarla libremente, incluso con fines comerciales, siempre citando la licencia original. Si vas a cambiar el protocolo, leé primero [`AGENTS.md`](AGENTS.md), conservá la distinción entre evidencia e hipótesis y no conviertas una sugerencia en una promesa de resultado.
