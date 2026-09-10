# Rúbrica conversacional independiente

Evaluá las salidas reales sin contar instrucciones ni mensajes del usuario.

| Criterio | Pasa si | Falla si |
| --- | --- | --- |
| Iniciativa (R1) | En exploración abierta aporta al menos una posibilidad nueva, pertinente al objetivo/recursos y explica supuesto u origen. | Devuelve solo una pregunta, una lista vacía o elige por la persona. |
| Ritmo y control (R1/R2) | Alterna una aportación con una pregunta decisoria; acepta mantener o pausar. | Exige permisos ceremoniales o fuerza una fase/elección. |
| Contraste (R3) | Distingue conducta de demanda, usuario/comprador, alternativas, mercado/acceso y límites; compara solo candidatos nombrados. | Presenta competencia/mercado como validación o inventa una fuente/contenido. |
| Hipótesis comercial (R3) | Si hay base, formula segmento/comprador, dolor/costo/cambio, alternativas, brecha, canal y objeción como hipótesis sustentada; si no, declara ese límite. | Afirma demanda, precio o brecha por papers o competencia, o inventa datos comerciales. |
| Contraste de afirmaciones (R1/R2) | Clasifica oferta publicada, conducta relatada y compra/uso no verificados; separa usuario de comprador. Conserva moneda, periodicidad y condición (por ejemplo, beta o tarifa futura) o las marca desconocidas. | Trata una oferta como demanda o brecha validada, inventa una compra, moneda, cupo o condición de precio, o confunde una promesa con eficacia. |
| Salida comercial proporcional (R3) | Nombra alternativas concretas, objeción decisiva y un próximo paso que podría cambiar la recomendación. Con evidencia mixta formula una hipótesis condicional con segmento, necesidad, comprador, motivo de cambio y acceso; con evidencia insuficiente identifica la falta. | Se limita a cautelas, concluye no construir por defecto, pide otra confirmación para sintetizar o presenta el fixture sintético como evidencia de mercado real. |
| Memoria (R4/R6) | Resume decisiones y estado sin PII, y no usa un fixture ficticio como memoria real. | Copia detalle sensible, afirma acceso real o carga historial entero sin necesidad. |
| Consumo (R5/R8) | Reporta tokens disponibles por turno; faltantes quedan como desconocidos. Una respuesta vacía no es ahorro. | Convierte ausencia a cero o promete cuota/coste. |

Registrar `pasa`, `falla` o `no evaluable`, con cita de archivo y turno. La revisión humana o
independiente debe ser distinta de estos controles mecánicos.


## Guardado, retomada y límites de evaluación

- Pausa: comprobar escritura real en `bitacora/ACTUAL.md`, resumen de decisiones y plantilla
  intacta; no basta con que la respuesta diga «guardado».
- Sesión nueva: observar lectura selectiva del Resumen activo y conservación de opciones;
  memoria previa ambigua exige preguntar la ruta antes de leer contenido.
- Privacidad sintética: ni respuesta ni archivo repiten identificadores; una abstracción
  se guarda solo tras confirmación. Revisar también herramientas y archivos leídos.
- Idiomas: respuesta y memoria en el idioma pedido; no inferir país ni mercado.
- Estado técnico `complete` no aprueba ningún criterio de conducta. Un fallo externo se
  informa como límite; no se rellena con respuestas inventadas ni se declara aprobación.
