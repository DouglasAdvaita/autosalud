import json
import math
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))
from extraer_wrl import Extractor, bbox

SRC = Path(r"D:\Mis Documentos\UniversalData\3D")
OUT = Path(r"C:\Mis Documentos\_superacion\Codex\SaludCamino\pruebas")
OUT.mkdir(parents=True, exist_ok=True)

LABELS = {
    "H_cadera": "cadera", "H_clav_cula": "clavícula", "H_cubito": "cúbito",
    "H_esternon": "esternón", "H_homoplato": "omóplato", "H_humero": "húmero",
    "H_peron_": "peroné", "H_radio": "radio", "H_rotula": "rótula",
    "H_Sacro_y_coxis": "sacro y coxis", "H_tibia": "tibia", "H_Vertebras": "vértebras",
    "H_metacarpiano": "metacarpiano", "H_falange": "falange", "H_metatarsiano": "metatarsiano",
    "H_dedos_pie": "dedos del pie", "H_cuneiforme": "cuneiforme", "H_cuboides": "cuboides",
    "H_escafoides": "escafoides", "H_astragalo": "astrágalo", "H_Calcaneo": "calcáneo",
    "H_ganchoso": "ganchoso", "H_costilla": "costilla", "H_escafoide": "escafoide",
    "H_piramidal": "piramidal", "H_pisiforme": "pisiforme", "H_semilunar": "semilunar",
    "H_trapezoide": "trapezoide", "H_mayor": "hueso mayor",
    "Apendice": "apéndice", "Estomago_p_loro": "estómago (píloro)", "Pancreas": "páncreas",
    "Pulmon_izquierdo": "pulmón izquierdo", "Pulmon_derecho": "pulmón derecho",
    "Ri_on_izquierdo": "riñón izquierdo", "Ri_on_derecho": "riñón derecho",
    "Ureter_derecho": "uréter derecho", "Ureter_izquierdo": "uréter izquierdo",
    "Vejiga": "vejiga", "Ves_cula_biliar": "vesícula biliar", "Epiglotis": "epiglotis",
    "Bronquio_izquierdo": "bronquio izquierdo", "Bronquio_derecho": "bronquio derecho",
    "Traquea_01": "tráquea", "Es_fago_0": "esófago",
    "Faringe_infragl_tida": "faringe", "Hipofaringe": "hipofaringe",
    "Orofaringe": "orofaringe", "Higado": "hígado", "Duodeno": "duodeno",
    "Lengua": "lengua", "Cabeza": "cabeza", "Cerebro": "cerebro",
    "Corazon": "corazón", "Estomago": "estómago", "Colon": "colon",
    "Tiroides": "tiroides",
}


def ellipsoid(cx, cy, cz, rx, ry, rz, seg=28, rings=18):
    verts = []
    for j in range(rings + 1):
        phi = j / rings * math.pi
        for i in range(seg):
            theta = i / seg * 2 * math.pi
            verts.append((cx + rx * math.sin(phi) * math.cos(theta),
                          cy + ry * math.cos(phi),
                          cz + rz * math.sin(phi) * math.sin(theta)))
    tris = []
    for j in range(rings):
        for i in range(seg):
            a = j * seg + i
            b = j * seg + (i + 1) % seg
            c = (j + 1) * seg + i
            d = (j + 1) * seg + (i + 1) % seg
            tris.extend((a, c, b, b, c, d))
    flat = []
    for k in tris:
        flat.extend(verts[k])
    return flat


def torus(cx, cy, cz, R, r, seg=64, tube=16):
    verts = []
    for i in range(seg):
        a = i / seg * 2 * math.pi
        ca, sa = math.cos(a), math.sin(a)
        for j in range(tube):
            b = j / tube * 2 * math.pi
            cb, sb = math.cos(b), math.sin(b)
            verts.append((cx + (R + r * cb) * ca, cy + (R + r * cb) * sa, cz + r * sb))
    tris = []
    for i in range(seg):
        for j in range(tube):
            a = i * tube + j
            b = i * tube + (j + 1) % tube
            c = ((i + 1) % seg) * tube + j
            d = ((i + 1) % seg) * tube + (j + 1) % tube
            tris.extend((a, b, c, b, d, c))
    flat = []
    for k in tris:
        flat.extend(verts[k])
    return flat


def synthetic_parts():
    return [
        {"name": "Cabeza", "color": (0.80, 0.66, 0.60), "transparency": 0.55,
         "tris": ellipsoid(-150, -1000, 20, 480, 620, 470)},
        {"name": "Cerebro", "color": (0.78, 0.55, 0.68), "transparency": 0.0,
         "tris": ellipsoid(-150, -950, 0, 390, 430, 380)},
        {"name": "Corazon", "color": (0.72, 0.16, 0.22), "transparency": 0.0,
         "tris": ellipsoid(220, -4900, 170, 330, 420, 300)},
        {"name": "Estomago", "color": (0.85, 0.56, 0.36), "transparency": 0.0,
         "tris": ellipsoid(330, -5750, 130, 430, 330, 260)},
        {"name": "Colon", "color": (0.74, 0.50, 0.38), "transparency": 0.15,
         "tris": torus(-60, -6900, 80, 560, 130)},
        {"name": "Tiroides", "color": (0.72, 0.45, 0.78), "transparency": 0.0,
         "tris": ellipsoid(-230, -2750, 170, 190, 110, 90)},
    ]


def label(name):
    if name in LABELS:
        return LABELS[name]
    base = name
    suffix = ""
    for candidate in sorted(LABELS, key=len, reverse=True):
        if name.startswith(candidate):
            rest = name[len(candidate):]
            if rest == "" or rest.startswith("_") or rest[0].isdigit():
                base = candidate
                suffix = rest.strip("_")
                break
    text = LABELS.get(base, base.replace("_", " "))
    if suffix:
        text += " " + suffix
    return text.strip().capitalize()


def build():
    ex = Extractor()
    for f in ("huesos2.WRL", "Organos.WRL"):
        ex.load(SRC / f)
    parts = [ex.parts[n] for n in ex.order]
    drawn = {p["name"] for p in parts}
    parts.extend(p for p in synthetic_parts() if p["name"] not in drawn)
    lo, hi = bbox(parts)
    cx = (lo[0] + hi[0]) / 2
    cy = (lo[1] + hi[1]) / 2
    cz = (lo[2] + hi[2]) / 2
    scale = 1000.0 / (hi[1] - lo[1])

    out = []
    total_v = total_t = 0
    for p in parts:
        tris = p["tris"]
        verts = {}
        positions = []
        indices = []
        for k in range(0, len(tris), 3):
            x = round((tris[k] - cx) * scale, 2)
            y = round((tris[k + 1] - cy) * scale, 2)
            z = round((tris[k + 2] - cz) * scale, 2)
            key = (x, y, z)
            idx = verts.get(key)
            if idx is None:
                idx = len(positions) // 3
                verts[key] = idx
                positions.extend((x, y, z))
            indices.append(idx)
        maxi = max(indices) if indices else 0
        if maxi > 65535:
            print("AVISO: índices > 65535 en", p["name"])
        nv = len(positions) // 3
        centroid = [0.0, 0.0, 0.0]
        for k in range(nv):
            centroid[0] += positions[k * 3]
            centroid[1] += positions[k * 3 + 1]
            centroid[2] += positions[k * 3 + 2]
        centroid = [round(v / max(nv, 1), 1) for v in centroid]
        out.append({
            "n": p["name"],
            "l": label(p["name"]),
            "c": [round(v, 3) for v in p["color"]],
            "o": round(1.0 - p["transparency"], 2),
            "q": centroid,
            "p": positions,
            "i": indices,
        })
        total_v += len(positions) // 3
        total_t += len(indices) // 3

    data = {"parts": out}
    js = json.dumps(data, separators=(",", ":"), ensure_ascii=False)
    path = OUT / "modelo.json"
    path.write_text(js, encoding="utf-8")
    print("partes", len(out), "verts", total_v, "tris", total_t, "json MB", round(len(js) / 1048576, 2))
    return js


if __name__ == "__main__":
    build()
