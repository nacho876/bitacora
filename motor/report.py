"""Stable Markdown output, with source text treated as data."""
import html


def text(value):
    return html.escape(str(value)).replace('\n', ' ').replace('[', '\\[').replace(']', '\\]').replace('*', '\\*').replace('|', '\\|')


def provenance_sections(signals):
    sections = {
        'Relatos argentinos': [],
        'Contexto argentino': [],
        'Señales argentinas no acreditadas': [],
        'Señales globales': [],
        'Procedencia desconocida': [],
    }
    for signal in signals:
        if (signal['country'] == 'AR' and signal['access'] == 'verified'
                and signal['evidence_class'] == 'direct'):
            sections['Relatos argentinos'].append(signal)
        elif (signal['country'] == 'AR' and signal['access'] == 'verified'
              and signal['evidence_class'] == 'context'):
            sections['Contexto argentino'].append(signal)
        elif signal['country'] == 'AR':
            sections['Señales argentinas no acreditadas'].append(signal)
        elif signal['country'] and signal['country'] != 'AR':
            sections['Señales globales'].append(signal)
        else:
            sections['Procedencia desconocida'].append(signal)
    return sections


def render_signal(lines, signal):
    duplicate = f" · duplicada de S{signal['duplicate_of']}" if signal['duplicate_of'] else ''
    lines += [f"- S{signal['id']} · {text(signal['source'])}/{text(signal['native_id'])} · {signal['access']}{duplicate}",
              f"  Fuente: <{signal['url'].replace('>', '%3E').replace('<', '%3C')}> · publicada: {text(signal['published_at'] or 'desconocida')} · consultada: {text(signal['accessed_at'])}",
              f"  Procedencia: {text(signal['country'] or 'desconocida')} · clase: {text(signal['evidence_class'])} · fundamento: {text(signal['territorial_basis'] or 'desconocido')}",
              f"  {text(signal['summary'] or 'Sin extracción interpretativa; abrir y parafrasear antes de proponer un problema.')} "]
    for field in ('actor', 'problem', 'consequence', 'alternative', 'audience_access', 'counterevidence'):
        lines.append(f"  {field}: {text(signal[field] or 'desconocida')};")


def render(data):
    scope = data['scope']
    lines = ['# Investigación de problemas', '', f"Búsqueda: {data['run']} · {data['created']}"]
    if data['synthetic']:
        lines += ['', '**SINTÉTICO: datos de prueba, no evidencia de mercado.**']
    lines += ['', '## Alcance', '', f"- Objetivo: {text(scope['objective'])}", f"- Tema o actor: {text(scope['topic'])}",
              f"- Mercado o idioma: {text(scope['market_language'])}", f"- Fuentes: {text(', '.join(scope['sources']))}",
              f"- País de mercado: {text(scope.get('market_country') or 'desconocido')}",
              f"- Límite por fuente: {scope['limit']}",
              '- Muestra acotada; no representa todo internet ni demuestra demanda o disposición a pagar.', '', '## Consultas', '']
    for q in data['queries']:
        reason = f" · motivo: {text(q.get('reason', ''))}" if q.get('reason') else ''
        lines.append(f"- {text(q['source'])}: {text(q['query'])} · {text(q['status'])}{reason} · {text(q['at'])} · {text(q['url'])}")
    if scope.get('market_country') == 'AR':
        local_roots = {(s['duplicate_of'] or s['id']) for s in data['signals']
                       if s['access'] == 'verified' and s['country'] == 'AR'
                       and s['evidence_class'] == 'direct' and s['independence']}
        coverage = 'mínima alcanzada' if len(local_roots) >= 2 else 'insuficiente'
        lines += ['', '## Cobertura argentina', '',
                  f"Relatos argentinos verificados e independientes: **{len(local_roots)}**.",
                  f"Cobertura argentina: **{coverage}**.",
                  'El umbral mínimo permite comparar relatos; no representa al mercado ni demuestra demanda.']
    lines += ['', '## Señales', '']
    for heading, signals in provenance_sections(data['signals']).items():
        lines += [f'### {heading}', '']
        if not signals:
            lines.append('- Ninguna.')
        for signal in signals:
            render_signal(lines, signal)
        lines.append('')
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
