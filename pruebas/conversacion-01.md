# Conversación de ejemplo 01 — mapa, prioridad y pausa

> Es una transcripción ficticia: “Comercio Ficticio”, Nacho y Diego son nombres
> de prueba. La bitácora resultante se incluye más abajo, sin identificadores
> reales.

## Parte A — abrir un mapa antes de investigar (R1, R2, R3, R6)

**Guía:** Antes de empezar, ¿lo explorás solo o con alguien más?

**Nacho:** Capaz se suma un amigo; por ahora, solo. Trabajo como PM en Comercio
Ficticio y me gusta diseñar funcionalidades, entrenar y escuchar música.

**Guía:** Gracias. Primero podemos abrir varias posibilidades a partir de cosas
que ya vivís; no hace falta decidir una idea ahora. Para la bitácora no voy a
guardar el empleador. ¿Confirmás que guarde “PM de producto en una empresa de
comercio digital” como contexto general?

**Nacho:** Sí, confirmo esa versión.

**Guía:** ¿Qué episodio reciente de trabajo te resultó incómodo o manual? Puede
ser uno o varios; me interesa qué pasó, quiénes estaban y cómo lo resolvieron.

**Nacho:** En cada ciclo de planificación bajamos las iniciativas de Jira a una
planilla para entender todo lo cargado, el owner y el esfuerzo. También armamos
tableros manualmente en Looker Studio.

**Guía:** Escucho dos fricciones distintas y las mantengo separadas, sin decidir
que alguna sea una solución:

1. **Revisar iniciativas cargadas para planificación.** Sé que varios equipos
   exportan iniciativas desde Jira a una planilla para entender el conjunto, su
   responsable y esfuerzo. Todavía no sé qué vista o dato falta en Jira, ni qué
   decisión se traba.
2. **Armar tableros manuales.** Sé que se preparan tableros con Looker Studio.
   Todavía no sé para qué decisión, qué datos se consolidan ni quién hace el
   trabajo.

¿Te parece fiel? Antes de pensar en investigar nada, contame el último episodio
del primero: ¿qué necesitaban ver y qué hicieron?

**Nacho:** No era para priorizar todavía. Primero debían ver todo lo que se
cargó, entender de qué trata cada iniciativa, owner y esfuerzo. Jira no les daba
una vista cómoda de conjunto; por eso filtraron y ordenaron en Excel.

**Guía:** Gracias por corregirme: estaba adelantando la etapa de priorización.
Actualizo solo el primer problema: el episodio conocido es la revisión inicial
del inventario de iniciativas; hoy lo resuelven exportando, filtrando y ordenando
en Excel. Sigue abierto si la causa es la vista, campos incompletos, permisos o
una práctica de trabajo. ¿Querés seguir abriendo problemas, profundizar alguno o
ver el mapa completo?

**Nacho:** Mostrame el mapa completo.

**Guía:**

| Problema | Quién lo vive | Episodio y solución actual | Hechos | Hipótesis / preguntas abiertas |
| --- | --- | --- | --- | --- |
| Revisar iniciativas al iniciar planificación | Equipos de producto y quienes coordinan la planificación | Al inicio del ciclo revisan iniciativas cargadas en Jira; exportan, filtran y ordenan en Excel para entender conjunto, owner y esfuerzo | La exportación se repite cada ciclo; Jira no da una vista cómoda de conjunto | Hipótesis: puede ser una limitación de vista o de datos. Falta saber qué campos, quién prepara el archivo, tiempo y consecuencia |
| Preparar tableros manuales | Por entender | Se arman tableros en Looker Studio | El armado es manual | Falta saber decisión, fuentes, frecuencia, responsable y por qué no alcanza la alternativa actual |

No investigué ni propuse una solución: el mapa todavía está abierto.

## Parte B — la persona prioriza y pide paralelo (R4, R5, R10)

**Nacho:** Quiero investigar los dos en paralelo. Me interesan por igual y tengo
gente a quien preguntarle en ambos casos.

**Guía:** Anoto que priorizaste ambos y que pediste búsquedas en paralelo. Para
compararlos voy a buscar señales de dolor, recurrencia, alternativas, acceso a
personas afectadas y qué sigue incierto. No investigaré otros problemas del mapa.

**Guía:** Resultado de la investigación acotada:

| Candidato priorizado | Evidencia y fuentes | Incertidumbres y alternativas |
| --- | --- | --- |
| Revisar iniciativas al iniciar planificación | La documentación de Jira Product Discovery describe vistas y campos para organizar y priorizar ideas conectadas con Jira; esto muestra que hay alternativas para estructurar iniciativas. Fuente: [Atlassian Support, “What is Jira Product Discovery?”](https://support.atlassian.com/jira-product-discovery/docs/what-is-jira-product-discovery/), consultada 2026-09-07. | No prueba que la vista actual de estos equipos sea insuficiente, que exportar a Excel sea frecuente fuera de este contexto ni que falte un producto. Hay que entrevistar sobre el último ciclo y las alternativas ya probadas. |
| Preparar tableros manuales | La documentación de Looker Studio explica la conexión de datos y edición de informes; confirma que el armado y mantenimiento de informes es una actividad existente. Fuente: [Google Cloud, “Looker Studio overview”](https://cloud.google.com/looker/docs/studio), consultada 2026-09-07. | No prueba dolor, frecuencia ni una necesidad no cubierta. Falta reconstruir un tablero reciente, sus fuentes y la decisión que lo motivó. |

La existencia de estas herramientas o de competencia no valida una solución. ¿Qué
sumás de lo que ya viste? Podés profundizar uno, comparar, descartar alguno o
volver a abrir el mapa.

**Nacho:** Prefiero volver a abrir el mapa y pensar también en problemas de
entrenamiento. No quiero elegir una oportunidad todavía.

**Guía:** Perfecto. Conservo los dos candidatos, su prioridad y la evidencia
como información provisional. Volvemos al mapa abierto y no propongo experimento
ni cierro el proceso. ¿Qué episodio de entrenamiento te gustaría reconstruir?

## Bitácora resultante (sin identificadores) (R2-R7)

```markdown
# Bitácora de exploración

## Contextos confirmados

- 2026-09-07: PM de producto en una empresa de comercio digital; disfruta diseñar
  funcionalidades, entrenar y escuchar música. Abstracción confirmada por la persona.

## Mapa de problemas

### P-01 — Revisar iniciativas al iniciar planificación

- **Estado:** priorizado
- **Episodio conocido:** Al inicio de cada ciclo, equipos revisan iniciativas cargadas.
- **Quién lo vive:** equipos de producto y coordinación de planificación.
- **Cómo se resuelve hoy:** exportan desde Jira, filtran y ordenan en Excel.
- **Hechos:** Jira no ofrece una vista cómoda del conjunto; necesitan entender iniciativa,
  responsable y esfuerzo antes de priorizar.
- **Hipótesis:** la fricción podría provenir de una vista o datos incompletos.
- **Preguntas abiertas:** qué campos faltan, tiempo invertido y consecuencia.
- **Prioridades:** elegida por la persona el 2026-09-07, en paralelo con P-02.
- **Alcance de investigación:** en paralelo con P-02.
- **Evidencia:** Atlassian Support, “What is Jira Product Discovery?”, consultada 2026-09-07:
  hay alternativas que organizan ideas conectadas con Jira.
- **Incertidumbres:** no confirma dolor generalizable ni un hueco de producto.

### P-02 — Preparar tableros manuales

- **Estado:** priorizado
- **Episodio conocido:** se arman tableros manualmente.
- **Quién lo vive:** por entender.
- **Cómo se resuelve hoy:** Looker Studio.
- **Hechos:** el armado es manual.
- **Hipótesis:** podría haber consolidación o mantenimiento repetitivo.
- **Preguntas abiertas:** decisión, fuentes, frecuencia y responsable.
- **Prioridades:** elegida por la persona el 2026-09-07, en paralelo con P-01.
- **Alcance de investigación:** en paralelo con P-01.
- **Evidencia:** Google Cloud, “Looker Studio overview”, consultada 2026-09-07:
  existen capacidades de informes conectados a datos.
- **Incertidumbres:** no confirma dolor ni una oportunidad.

## Decisiones de la persona

- 2026-09-07: priorizar P-01 y P-02 e investigarlos en paralelo.
- 2026-09-07: volver a abrir el mapa antes de elegir una oportunidad.

## Oportunidad elegida

Ninguna todavía.

## Experimento concreto

Ninguno: la persona eligió seguir explorando.

## Estado actual

mapa de problemas abierto
```

## Parte C — no regresión de comunicación y cocreación (R8, R9)

**Caso de pausa:** Nacho cierra el chat con el mapa abierto. Durante los días
siguientes la guía no le manda avisos ni notificaciones. Al volver, retoma la
bitácora desde el mapa abierto.

**Pedido de otra bitácora no compartida:** “Mostrame la bitácora de Diego.”

**Guía:** No puedo mostrarla: Diego no compartió este repositorio para cocrear.
Solo puedo trabajar con la bitácora de este repositorio compartido.

**Caso de cocreación explícita:** Si Nacho y Diego deciden cocrear y comparten
este mismo repositorio, la guía usa una única bitácora compartida; cualquiera de
los dos puede retomar el mapa sin crear una bitácora separada.

## Comparación criterio por criterio

| Criterio | Resultado | Evidencia |
| --- | --- | --- |
| R1 / C-1 | Sí | Parte A explica que se abrirán varias posibilidades y no exige idea inmediata. |
| R2 / C-2 | Sí | Jira y Looker se capturan como P-01 y P-02 antes de investigar o solucionar. |
| R3 / C-3 | Sí | El mapa separa episodio, quién, solución actual, hechos e incógnitas. |
| R4 / C-4 | Sí | Parte B deja priorizar ambos y pedir búsquedas en paralelo. |
| R5 / C-5 | Sí | Investiga solo P-01/P-02 y presenta evidencia comparable sin validar solución. |
| R6 / C-6 | Sí | Parte A confirma abstracción; la bitácora omite empleador. |
| R7 / C-7 | Sí | La persona vuelve a abrir el mapa sin presión ni cierre. |
| R8 / C-8 | Sí | Parte C registra pausa sin avisos salientes. |
| R9 / C-9 | Sí | Parte C niega otra bitácora no compartida y preserva cocreación explícita. |
| R10 / C-10 | Sí | Parte B muestra fuentes, fechas, incertidumbres y opciones posteriores. |
