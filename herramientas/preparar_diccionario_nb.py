import html
import json
import re
import unicodedata
from pathlib import Path

BASE = Path(__file__).resolve().parent.parent
ORIGEN = BASE / "datos" / "diccionario.json"
DESTINO = BASE / "datos" / "diccionario_emocional.md"

CAMPOS = [
    ("texto", "Texto"),
    ("fisico", "Físico"),
    ("emocional", "Emocional"),
    ("consejo", "Consejo"),
    ("otros", "Otros"),
]


def norm(s):
    s = unicodedata.normalize("NFD", s or "")
    s = s.encode("ascii", "ignore").decode()
    return " ".join(s.upper().split())


def limpiar(s):
    s = html.unescape(s or "")
    s = re.sub(r"<br\s*/?>", "\n", s, flags=re.I)
    s = re.sub(r"<[^>]+>", "", s)
    s = s.replace("\r\n", "\n").replace("\r", "\n").replace("\xa0", " ")
    s = re.sub(r"[ \t]+", " ", s)
    s = re.sub(r"\n{3,}", "\n\n", s)
    return s.strip()


def main():
    d = json.loads(ORIGEN.read_text(encoding="utf-8"))
    arts = d["articulos"]
    con_texto = [a for a in arts if any(limpiar(a.get(c)) for c, _ in CAMPOS)]
    por_titulo = {norm(a["titulo"]): a for a in con_texto}

    alias_por_destino = {}
    alias_sueltos = []
    for a in arts:
        if not a.get("alias"):
            continue
        destino = norm(a.get("destino"))
        if destino and destino in por_titulo:
            alias_por_destino.setdefault(destino, []).append(a["titulo"])
        else:
            alias_sueltos.append((a["titulo"], a.get("destino") or ""))

    conteo_organo = {}
    for a in con_texto:
        org = (a.get("organo") or "General").strip() or "General"
        conteo_organo[org] = conteo_organo.get(org, 0) + 1

    partes = [
        "# Diccionario de las Enfermedades Emocionales",
        "",
        f"**Fuente:** {d.get('fuente', 'Diccionario de las Enfermedades Emocionales.htm')}  ",
        f"**Artículos con contenido:** {len(con_texto)}  ",
        f"**Alias y remisiones:** {sum(1 for a in arts if a.get('alias'))}",
        "",
        "# Índice por órgano",
        "",
    ]
    for org in sorted(conteo_organo, key=lambda x: norm(x)):
        partes.append(f"- **{org}**: {conteo_organo[org]} artículos")
    partes.extend(["", "# Artículos", ""])

    for a in con_texto:
        titulo = limpiar(a["titulo"])
        partes.append(f"## {titulo}")
        partes.append("")
        org = limpiar(a.get("organo"))
        if org:
            partes.append(f"**Órgano:** {org}")
        alias = alias_por_destino.get(norm(a["titulo"]))
        if alias:
            partes.append("**También conocido como:** " + "; ".join(alias))
        for campo, etiqueta in CAMPOS:
            texto = limpiar(a.get(campo))
            if texto:
                partes.append(f"**{etiqueta}:** {texto}")
        partes.append("")

    if alias_sueltos:
        partes.extend(["# Alias y remisiones", ""])
        for titulo, destino in alias_sueltos:
            if destino:
                partes.append(f"- **{limpiar(titulo)}** → {limpiar(destino)}")
            else:
                partes.append(f"- **{limpiar(titulo)}**")
        partes.append("")

    salida = "\n".join(partes).strip() + "\n"
    DESTINO.write_text(salida, encoding="utf-8")
    palabras = len(re.findall(r"\S+", salida))
    print(f"escrito: {DESTINO}")
    print(f"artículos: {len(con_texto)}; alias con destino: {sum(len(v) for v in alias_por_destino.values())}; alias sueltos: {len(alias_sueltos)}")
    print(f"caracteres: {len(salida)}; palabras: {palabras}")


if __name__ == "__main__":
    main()
