import json
import re
import html
import pathlib
import unicodedata

SRC = pathlib.Path(r"C:\Mis Documentos\Diccionario de las Enfermedades Emocionales.htm")
OUT = pathlib.Path(__file__).resolve().parent.parent / "datos" / "diccionario.json"

NAV = re.compile(r'^(ir al principio|ir al [ií]ndice)\b', re.I)


def clean(fragment):
    fragment = re.sub(r'(?is)<span[^>]*font-family:\s*Wingdings[^>]*>.*?</span>', ' ', fragment)
    fragment = re.sub(r'(?is)<(script|style)[^>]*>.*?</\1>', ' ', fragment)
    fragment = re.sub(r'(?is)<br\s*/?>', ' ', fragment)
    fragment = re.sub(r'(?is)</p\s*>', ' ', fragment)
    fragment = re.sub(r'(?is)<[^>]+>', '', fragment)
    fragment = html.unescape(fragment)
    fragment = fragment.replace('\xa0', ' ')
    fragment = re.sub(r'\s+', ' ', fragment)
    return fragment.strip()


def slug(text):
    text = unicodedata.normalize('NFD', text)
    text = ''.join(c for c in text if unicodedata.category(c) != 'Mn')
    text = re.sub(r'[^a-zA-Z0-9]+', '-', text).strip('-').lower()
    return text[:80] or 'entrada'


def split_title(full):
    """Separa titulo principal y referencia verde '(ver también: ...)'."""
    t = full.strip()
    t = re.sub(r'\s*\((?:ver|Ver)\s+tambi[eé]n\s*:.*\)[.\s]*$', '', t)
    t = re.sub(r'\s*\((?:ver|Ver)\s*:.*\)[.\s]*$', '', t)
    return re.sub(r'\s+', ' ', t).strip().rstrip('.')


def alias_target(title):
    m = re.search(r'\((?:ver|Ver)\s*:.*\)\s*[.\s]*$', title)
    if not m or 'tambi' in m.group(0).lower():
        return None
    target = re.sub(r'^\((?:ver|Ver)\s*:\s*', '', m.group(0))
    target = re.sub(r'\)\s*[.\s]*$', '', target)
    return re.sub(r'\s+', ' ', target).strip().rstrip('.')


raw = SRC.read_bytes().decode('cp1252', errors='replace')

heads = list(re.finditer(r'(?is)<h1[^>]*>(.*?)</h1>', raw))
entries = []
for n, h in enumerate(heads):
    inner = h.group(1)
    if not re.search(r'name="_[^"]*"', inner):
        continue
    if re.search(r'name="_Toc', inner) and not re.search(r'name="_(?!Toc)[^"]*"', inner):
        continue
    title = split_title(clean(inner))
    if not title:
        continue
    end = heads[n + 1].start() if n + 1 < len(heads) else len(raw)
    body = raw[h.end():end]

    blocks = {'texto': [], 'fisico': [], 'emocional': [], 'consejo': [], 'otros': []}
    for p in re.finditer(r'(?is)<p\b([^>]*)>(.*?)</p\s*>', body):
        attrs, content = p.group(1), p.group(2)
        cls = re.search(r'class="([^"]+)"', attrs)
        cls = cls.group(1) if cls else ''
        text = clean(content)
        if not text or NAV.match(text):
            continue
        if cls == 'Autor1':
            blocks['texto'].append(text)
        elif cls == 'Autor2-1':
            blocks['fisico'].append(text)
        elif cls == 'Autor2-2':
            blocks['emocional'].append(text)
        elif cls == 'Autor2-3':
            blocks['consejo'].append(text)
        elif len(text) > 120:
            blocks['otros'].append(text)

    target = alias_target(clean(inner))
    joined = {k: ' '.join(v).strip() for k, v in blocks.items()}
    has_content = any(joined[k] for k in ('texto', 'fisico', 'emocional', 'consejo'))
    entries.append({
        'titulo': title,
        'destino': target,
        'alias': bool(target) and not has_content,
        'texto': joined['texto'],
        'fisico': joined['fisico'],
        'emocional': joined['emocional'],
        'consejo': joined['consejo'],
        'otros': joined['otros'],
    })

organs = set()
for e in entries:
    if e['alias']:
        continue
    if ' - ' in e['titulo']:
        organs.add(e['titulo'].split(' - ', 1)[0].strip().rstrip('.').upper())


def organ_of(title):
    if ' - ' in title:
        base = title.split(' - ', 1)[0].strip().rstrip('.').upper()
    else:
        base = re.split(r'\s*[\(\[]', title, 1)[0].strip().rstrip('.').upper()
    if any(c in base for c in '()[]') or 'VER ' in base:
        return 'General'
    return base if base in organs else 'General'


result = []
seen = set()
for e in entries:
    title = e['titulo']
    organ = organ_of(e['destino']) if e['alias'] and e['destino'] else organ_of(title)
    e['organo'] = organ
    key = (title.upper(), e['texto'][:80], e['fisico'][:80])
    if key in seen:
        continue
    seen.add(key)
    e['id'] = slug(title)
    result.append(e)

counts = {}
for e in result:
    counts[e['organo']] = counts.get(e['organo'], 0) + 1

result.sort(key=lambda x: (x['organo'], x['titulo'].lower()))
organs_out = sorted(({'nombre': k, 'n': v} for k, v in counts.items()), key=lambda x: (-x['n'], x['nombre']))

data = {
    'fuente': SRC.name,
    'total': len(result),
    'contenido': sum(1 for e in result if not e['alias']),
    'alias': sum(1 for e in result if e['alias']),
    'organos': organs_out,
    'articulos': result,
}

OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

print('articulos:', data['total'])
print('con contenido:', data['contenido'])
print('alias:', data['alias'])
print('organos:', len(organs_out))
print('archivo:', OUT, round(OUT.stat().st_size / 1024), 'KB')
print('top organos:', ', '.join(f"{o['nombre']}({o['n']})" for o in organs_out[:12]))
