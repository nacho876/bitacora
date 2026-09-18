"""Stable Markdown output, with source text treated as data."""
import html


def text(value):
    return html.escape(str(value)).replace('\n', ' ').replace('[', '\\[').replace(']', '\\]').replace('*', '\\*').replace('|', '\\|')


def render(data):
    scope = data['scope']
    lines = ['# Investigación de problemas', '', f"Búsqueda: {data['run']} · {data['created']}"]
    if data['synthetic']:
        lines += ['', '**SINTÉTICO: datos de prueba, no evidencia de mercado.**']
    lines += ['', '## Alcance', '', f"- Objetivo: {text(scope['objective'])}", f"- Tema o actor: {text(scope['topic'])}",
              f"- Mercado o idioma: {text(scope['market_language'])}", f"- Fuentes: {text(', '.join(scope['sources']))}",
              f"- Límite por fuente: {scope['limit']}",
              '- Muestra acotada; no representa todo internet ni demuestra demanda o disposición a pagar.', '', '## Consultas', '']
    for q in data['queries']:
        lines.append(f"- {text(q['source'])}: {text(q['query'])} · {text(q['status'])} · {text(q['at'])} · {text(q['url'])}")
    lines += ['', '## Señales', '']
    for s in data['signals']:
        duplicate = f" · duplicada de S{s['duplicate_of']}" if s['duplicate_of'] else ''
        lines += [f"- S{s['id']} · {text(s['source'])}/{text(s['native_id'])} · {s['access']}{duplicate}",
                  f"  Fuente: <{s['url'].replace('>', '%3E').replace('<', '%3C')}> · publicada: {text(s['published_at'] or 'desconocida')} · consultada: {text(s['accessed_at'])}",
                  f"  {text(s['summary'] or 'Sin extracción interpretativa; abrir y parafrasear antes de proponer un problema.')} "]
        for field in ('actor', 'problem', 'consequence', 'alternative', 'audience_access', 'counterevidence'):
            lines.append(f"  {field}: {text(s[field] or 'desconocida')};")
    lines += ['', '## Grupos de problemas', '']
    for g in data['groups']:
        lines += [f"### {text(g['title'])}", '', f"Nivel: **{g['level']}**. Hallazgos: {len(g['signal_ids'])}; observaciones independientes: {g['observations']}.",
                  'Señales: ' + ', '.join(f'S{i}' for i in g['signal_ids'])]
        for dimension, rating in g['dimensions'].items():
            refs = ', '.join(f'S{i}' for i in rating['evidence']) or 'sin respaldo observado'
            lines.append(f"- {dimension}: {rating['value']} ({refs})")
        lines += [f"- Objeción: {text(g['objection'])}", '']
    lines += ['## Hipótesis para explorar', '']
    for g in data['hypotheses']:
        lines.append(f"- {text(g['hypothesis'])} · {g['level']} · " + ', '.join(f'S{i}' for i in g['signal_ids']))
    if len(data['hypotheses']) < 3:
        lines += ['', 'La evidencia no alcanza para tres hipótesis. Faltan relatos de problemas verificados e independientes; no se agregan opciones de relleno.']
    lines += ['', 'Los valores desconocidos no suman puntuación. La independencia es una interpretación revisable del asistente, no una identidad comprobada de personas.', '']
    return '\n'.join(lines)
