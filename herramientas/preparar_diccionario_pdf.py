import textwrap
from pathlib import Path

import pymupdf


BASE = Path(__file__).resolve().parent.parent
ENTRADA = BASE / "datos" / "diccionario_emocional.md"
SALIDA = BASE / "datos" / "diccionario_emocional.pdf"
FUENTE = Path(r"C:\Windows\Fonts\arial.ttf")

ANCHO, ALTO = 595, 842
MARGEN = 36
TAMANO = 8.5
INTERLINEA = 11
CARACTERES = 108


def main():
    lineas = ENTRADA.read_text(encoding="utf-8").splitlines()
    documento = pymupdf.open()
    pagina = None
    y = 0

    def nueva_pagina():
        p = documento.new_page(width=ANCHO, height=ALTO)
        p.insert_font(fontname="F0", fontfile=str(FUENTE))
        return p, MARGEN + TAMANO

    pagina, y = nueva_pagina()
    for linea in lineas:
        if not linea.strip():
            y += INTERLINEA / 2
            continue
        partes = textwrap.wrap(
            linea.rstrip(),
            width=CARACTERES,
            break_long_words=True,
            break_on_hyphens=False,
        )
        for parte in partes or [""]:
            if y + INTERLINEA > ALTO - MARGEN:
                pagina, y = nueva_pagina()
            pagina.insert_text((MARGEN, y), parte, fontname="F0", fontsize=TAMANO)
            y += INTERLINEA

    documento.save(SALIDA, garbage=3, deflate=True)
    documento.close()
    print(SALIDA)
    print(SALIDA.stat().st_size)


if __name__ == "__main__":
    main()
