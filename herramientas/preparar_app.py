import json
import pathlib

BASE = pathlib.Path(__file__).resolve().parent.parent
APP = BASE / "app" / "datos"
APP.mkdir(parents=True, exist_ok=True)

fuentes = [
    (BASE / "datos" / "diccionario.json", "DICCIONARIO", APP / "diccionario.js"),
    (BASE / "datos" / "libros.json", "LIBROS", APP / "libros.js"),
    (BASE / "pruebas" / "modelo.json", "MODELO", APP / "modelo.js"),
]

for src, var, dst in fuentes:
    data = json.loads(src.read_text(encoding="utf-8"))
    dst.write_text("window." + var + "=" + json.dumps(data, ensure_ascii=False, separators=(",", ":")) + ";\n", encoding="utf-8")
    print(var, round(dst.stat().st_size / 1024), "KB", dst)
