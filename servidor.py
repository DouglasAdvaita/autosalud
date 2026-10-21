import argparse
import json
import subprocess
import sys
import threading
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

BASE = Path(__file__).resolve().parent
APP = BASE / "app"
CONF = BASE / "cuaderno.json"
PY = sys.executable
PUERTO = 8767

if hasattr(sys.stdout, "reconfigure"):
    sys.stdout.reconfigure(encoding="utf-8")
if hasattr(sys.stderr, "reconfigure"):
    sys.stderr.reconfigure(encoding="utf-8")


def cargar_config():
    try:
        return json.loads(CONF.read_text(encoding="utf-8"))
    except Exception:
        return {
            "id": "582dd138-4238-461e-9e1f-262665967ac8",
            "titulo": "Salud - enfermedad y creencias",
            "fuentes": {},
        }


CFG = cargar_config()


def consultar(pregunta, nueva=False):
    pregunta = " ".join(str(pregunta or "").split())
    if not pregunta:
        return {"ok": False, "error": "Escribí una pregunta."}
    if len(pregunta) > 1500:
        return {"ok": False, "error": "La pregunta es demasiado larga."}

    cmd = [
        PY, "-m", "notebooklm", "ask", pregunta,
        "-n", str(CFG.get("id", "")),
    ]
    if nueva:
        cmd.append("--new")
    cmd.extend(["--json", "--timeout", "120"])
    try:
        proc = subprocess.run(
            cmd, cwd=str(BASE), capture_output=True, text=True,
            encoding="utf-8", errors="replace", timeout=150,
        )
    except subprocess.TimeoutExpired:
        return {"ok": False, "error": "NotebookLM tardó demasiado en responder. Probá de nuevo."}
    except Exception:
        return {"ok": False, "error": "No se pudo ejecutar el cliente de NotebookLM."}

    salida = (proc.stdout or "").strip()
    detalle = ((proc.stderr or "") + "\n" + (proc.stdout or "")).strip()
    if proc.returncode != 0:
        if any(x in detalle for x in ("Authentication expired", "signed-out", "Token fetch failed")):
            return {
                "ok": False,
                "auth": True,
                "error": "La sesión de NotebookLM venció. Ejecutá: python -m notebooklm login --browser chrome",
            }
        return {"ok": False, "error": "NotebookLM no respondió. Revisá la consola del servidor."}

    inicio = salida.find("{")
    fin = salida.rfind("}")
    if inicio < 0 or fin < inicio:
        return {"ok": False, "error": "NotebookLM devolvió una respuesta inesperada."}
    try:
        data = json.loads(salida[inicio:fin + 1])
    except Exception:
        return {"ok": False, "error": "No se pudo leer la respuesta de NotebookLM."}

    respuesta = (data.get("answer") or "").strip()
    if not respuesta:
        return {"ok": False, "error": "NotebookLM no devolvió texto."}
    if len(respuesta) > 9000:
        respuesta = respuesta[:9000].rstrip() + "\n\n[Respuesta recortada]"

    nombres = CFG.get("fuentes") or {}
    fuentes = []
    vistos = set()
    for ref in data.get("references") or []:
        n = ref.get("citation_number")
        if n in vistos:
            continue
        vistos.add(n)
        texto = " ".join((ref.get("cited_text") or "").split())
        if len(texto) > 280:
            texto = texto[:277].rstrip() + "..."
        fuentes.append({
            "n": n,
            "libro": nombres.get(ref.get("source_id"), "Fuente"),
            "texto": texto,
        })
        if len(fuentes) >= 12:
            break
    fuentes.sort(key=lambda x: (x.get("n") is None, x.get("n")))

    siguientes = []
    for item in data.get("next_steps") or []:
        q = (item.get("question") or "").strip()
        if q:
            siguientes.append(q)
        if len(siguientes) >= 3:
            break

    return {"ok": True, "respuesta": respuesta, "fuentes": fuentes, "siguientes": siguientes}


class Handler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(APP), **kwargs)

    def _origen_permitido(self):
        origen = self.headers.get("Origin")
        puerto = self.server.server_address[1]
        permitidos = {"null", f"http://127.0.0.1:{puerto}", f"http://localhost:{puerto}"}
        return origen if origen in permitidos else None

    def end_headers(self):
        origen = self._origen_permitido()
        if origen:
            self.send_header("Access-Control-Allow-Origin", origen)
            self.send_header("Vary", "Origin")
        self.send_header("Cache-Control", "no-store")
        super().end_headers()

    def _json(self, codigo, obj):
        data = json.dumps(obj, ensure_ascii=False).encode("utf-8")
        self.send_response(codigo)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_OPTIONS(self):
        self.send_response(204)
        self.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def do_GET(self):
        if self.path.split("?")[0] == "/api/estado":
            self._json(200, {
                "ok": True,
                "cuaderno": CFG.get("titulo", "Salud - enfermedad y creencias"),
                "servidor": True,
            })
            return
        super().do_GET()

    def do_POST(self):
        if self.path.split("?")[0] != "/api/consultar":
            self._json(404, {"ok": False, "error": "No encontrado."})
            return
        try:
            largo = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            largo = 0
        if largo <= 0 or largo > 20000:
            self._json(400, {"ok": False, "error": "Consulta inválida."})
            return
        try:
            data = json.loads(self.rfile.read(largo).decode("utf-8"))
        except Exception:
            self._json(400, {"ok": False, "error": "JSON inválido."})
            return
        pregunta = (data.get("pregunta") or "").strip()
        if not pregunta:
            self._json(400, {"ok": False, "error": "Escribí una pregunta."})
            return
        resultado = consultar(pregunta, nueva=bool(data.get("nueva")))
        codigo = 200 if resultado.get("ok") else (401 if resultado.get("auth") else 502)
        self._json(codigo, resultado)


def main():
    parser = argparse.ArgumentParser(description="Servidor local de Salud + consulta a NotebookLM.")
    parser.add_argument("--pregunta", nargs="+", help="Consulta directa por consola, sin abrir el servidor.")
    parser.add_argument("--puerto", type=int, default=PUERTO)
    parser.add_argument("--no-abrir", action="store_true", help="No abrir el navegador al iniciar.")
    args = parser.parse_args()

    if args.pregunta:
        resultado = consultar(" ".join(args.pregunta), nueva=True)
        if not resultado.get("ok"):
            print(resultado.get("error", "Error."), file=sys.stderr)
            return 1
        print(resultado["respuesta"])
        if resultado.get("fuentes"):
            print("\nFuentes:")
            for f in resultado["fuentes"]:
                print(f"[{f['n']}] {f['libro']}")
        return 0

    try:
        servidor = ThreadingHTTPServer(("127.0.0.1", args.puerto), Handler)
    except OSError as e:
        print(f"No se pudo abrir el puerto {args.puerto}: {e}", file=sys.stderr)
        return 1

    url = f"http://127.0.0.1:{args.puerto}/"
    print(f"Servidor en {url}")
    print("Cerrá esta ventana para detenerlo.")
    if not args.no_abrir:
        threading.Timer(0.8, lambda: webbrowser.open(url)).start()
    try:
        servidor.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        servidor.server_close()
    return 0


if __name__ == "__main__":
    sys.exit(main())
