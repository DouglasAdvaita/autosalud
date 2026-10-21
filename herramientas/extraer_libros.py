import json
import re
import pathlib

import pymupdf

BASE = pathlib.Path(__file__).resolve().parent.parent
OUT = BASE / "datos" / "libros.json"

CAMINO = pathlib.Path(r"C:\Mis Documentos\_superacion\Libros PDF\SALUD\La enfermedad como camino\la_enfermedad_como_camino.txt")
CREENCIA = pathlib.Path(r"C:\Mis Documentos\_superacion\Libros PDF\SALUD\la-biología-de-la-creencia.pdf")

ROMAN = r'(?:I|II|III|IV|V|VI|VII|VIII|IX|X|XI|XII|XIII|XIV|XV|XVI)'


def limpiar(texto):
    texto = texto.replace('\r', '')
    texto = re.sub(r'[ \t]+', ' ', texto)
    texto = re.sub(r'\n{3,}', '\n\n', texto)
    return texto.strip()


def extraer_camino():
    raw = CAMINO.read_bytes().decode('cp1252', errors='replace')
    lines = raw.split('\n')
    n = len(lines)
    idx = None
    for i, line in enumerate(lines):
        if re.match(r'^\s*I\.\s+ENFERMEDAD Y.*\.{4,}', line):
            idx = i
            break
    if idx is None:
        raise SystemExit('No se encontro el indice del libro camino')

    inicios = []
    for i in range(idx):
        line = lines[i].strip()
        m = re.match(r'^(' + ROMAN + r')\.\s+(.+)$', line)
        if m:
            inicios.append((i, m.group(1), m.group(2).strip()))
    if not inicios:
        raise SystemExit('No se encontraron capitulos del libro camino')

    partes = []
    for i, line in enumerate(lines[:idx]):
        m = re.match(r'^(Primera|Segunda|Tercera)\s+parte\s*$', line.strip(), re.I)
        if m:
            partes.append((i, m.group(1).capitalize() + ' parte'))

    def parte_de(pos):
        nombre = ''
        for i, p in partes:
            if i <= pos:
                nombre = p
        return nombre

    prologo = ''
    for i, line in enumerate(lines[:idx]):
        if line.strip().upper().startswith('PRÓLOGO') or line.strip().upper().startswith('PROLOGO'):
            fin = inicios[0][0] if inicios else idx
            prologo = limpiar('\n'.join(lines[i + 1:fin]))
            break

    caps = []
    orden = 0
    for k, (i, num, titulo) in enumerate(inicios):
        fin = inicios[k + 1][0] if k + 1 < len(inicios) else idx
        texto = limpiar('\n'.join(lines[i + 1:fin]))
        if not texto:
            continue
        orden += 1
        caps.append({
            'id': f'camino-{orden}',
            'parte': parte_de(i),
            'numero': num,
            'titulo': titulo,
            'texto': texto,
        })

    return {
        'titulo': 'La enfermedad como camino',
        'autor': 'Thorwald Dethlefsen y Rüdiger Dahlke',
        'prologo': prologo,
        'partes': [p for _, p in partes],
        'capitulos': caps,
    }


JEFES = [
    (4, 'PRÓLOGO', 'Prólogo de Ángel Llamas'),
    (7, 'PREFACIO', 'Prefacio'),
    (20, 'CAPÍTULO 1', 'Lecciones de la placa Petri: elogio a las células y a los alumnos inteligentes'),
    (34, 'CAPÍTULO 2', 'Es el ambiente, ¡estúpido!'),
    (55, 'CAPÍTULO 3', 'La membrana mágica'),
    (71, 'CAPÍTULO 4', 'La nueva física: con los pies bien plantados en el vacío'),
    (111, 'CAPÍTULO 6', 'Crecimiento y protección'),
    (119, 'CAPÍTULO 7', 'Paternidad responsable: los padres como ingenieros genéticos'),
    (151, 'EPÍLOGO', 'Ciencia y espíritu'),
    (158, 'AGRADECIMIENTOS', 'Agradecimientos'),
]


def extraer_creencia():
    doc = pymupdf.open(CREENCIA)
    total = doc.page_count
    caps = []
    for k, (pag, tipo, titulo) in enumerate(JEFES):
        fin = JEFES[k + 1][0] - 1 if k + 1 < len(JEFES) else total
        paginas = []
        for p in range(pag - 1, min(fin, total)):
            texto = doc[p].get_text()
            texto = re.sub(r'^\s*\d{1,3}\s*\n', '', texto)
            paginas.append(texto)
        texto = limpiar('\n'.join(paginas))
        lineas = texto.split('\n')
        i = 0
        while i < min(6, len(lineas)):
            l = lineas[i].strip()
            if not l:
                i += 1
                continue
            letras = [c for c in l if c.isalpha()]
            mayus = sum(1 for c in letras if c.isupper()) / max(1, len(letras))
            jefe = l.upper().startswith(('CAPÍTULO', 'CA PÍTULO', 'PRÓLOGO', 'PREFACIO', 'EPÍLOGO', 'AGRADECIMIENTOS'))
            if len(l) < 110 and (jefe or mayus > 0.7):
                i += 1
                continue
            break
        caps.append({
            'id': 'creencia-' + re.sub(r'[^a-z0-9]+', '-', tipo.lower()).strip('-'),
            'tipo': tipo,
            'titulo': titulo,
            'texto': limpiar('\n'.join(lineas[i:])),
            'desde': pag,
            'hasta': min(fin, total),
        })
    return {
        'titulo': 'La biología de la creencia',
        'autor': 'Bruce H. Lipton',
        'nota': 'Esta edición digital no incluye la Introducción ni el capítulo 5 (Biología y creencias); faltan también el apéndice y la bibliografía.',
        'capitulos': caps,
    }


data = {'camino': extraer_camino(), 'creencia': extraer_creencia()}
OUT.parent.mkdir(parents=True, exist_ok=True)
OUT.write_text(json.dumps(data, ensure_ascii=False, separators=(',', ':')), encoding='utf-8')

print('camino capitulos:', len(data['camino']['capitulos']))
for c in data['camino']['capitulos']:
    print(' ', c['parte'], c['numero'], c['titulo'][:60], len(c['texto']))
print('creencia capitulos:', len(data['creencia']['capitulos']))
for c in data['creencia']['capitulos']:
    print(' ', c['tipo'], c['titulo'][:60], len(c['texto']))
print('archivo:', OUT, round(OUT.stat().st_size / 1024), 'KB')
