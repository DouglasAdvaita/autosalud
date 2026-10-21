import json
import math
import re
import sys
from pathlib import Path

TOK = re.compile(r"[A-Za-z_][\w\-]*|[-+]?(?:\d+\.?\d*|\.\d+)(?:[eE][-+]?\d+)?|[{}\[\],]")


def tokenize(text):
    text = re.sub(r"#[^\n]*", " ", text)
    return TOK.findall(text)


def mat_identity():
    return [1.0, 0.0, 0.0, 0.0,
            0.0, 1.0, 0.0, 0.0,
            0.0, 0.0, 1.0, 0.0,
            0.0, 0.0, 0.0, 1.0]


def mat_mul(a, b):
    out = [0.0] * 16
    for r in range(4):
        for c in range(4):
            out[r * 4 + c] = (a[r * 4 + 0] * b[0 * 4 + c] +
                              a[r * 4 + 1] * b[1 * 4 + c] +
                              a[r * 4 + 2] * b[2 * 4 + c] +
                              a[r * 4 + 3] * b[3 * 4 + c])
    return out


def mat_from_trs(t, r, s):
    tx, ty, tz = t
    ax, ay, az, ang = r
    sx, sy, sz = s
    n = math.sqrt(ax * ax + ay * ay + az * az)
    if n == 0:
        rmat = mat_identity()
    else:
        ax, ay, az = ax / n, ay / n, az / n
        c, sn = math.cos(ang), math.sin(ang)
        C = 1 - c
        rmat = [
            ax * ax * C + c, ax * ay * C - az * sn, ax * az * C + ay * sn, 0.0,
            ay * ax * C + az * sn, ay * ay * C + c, ay * az * C - ax * sn, 0.0,
            az * ax * C - ay * sn, az * ay * C + ax * sn, az * az * C + c, 0.0,
            0.0, 0.0, 0.0, 1.0,
        ]
    smat = [sx, 0, 0, 0, 0, sy, 0, 0, 0, 0, sz, 0, 0, 0, 0, 1]
    tmat = mat_identity()
    tmat[3], tmat[7], tmat[11] = tx, ty, tz
    return mat_mul(tmat, mat_mul(rmat, smat))


def apply(m, p):
    x, y, z = p
    return (m[0] * x + m[1] * y + m[2] * z + m[3],
            m[4] * x + m[5] * y + m[6] * z + m[7],
            m[8] * x + m[9] * y + m[10] * z + m[11])


def read_numbers(tokens, i, count):
    out = []
    while len(out) < count and i < len(tokens):
        try:
            out.append(float(tokens[i]))
            i += 1
        except ValueError:
            break
    while len(out) < count:
        out.append(0.0)
    return out, i


def read_array(tokens, i):
    if tokens[i] != "[":
        return [], i
    i += 1
    vals = []
    while i < len(tokens) and tokens[i] != "]":
        t = tokens[i]
        if t != ",":
            try:
                vals.append(float(t))
            except ValueError:
                pass
        i += 1
    return vals, i + 1


class Extractor:
    def __init__(self):
        self.parts = {}
        self.order = []

    def add_triangles(self, name, color, transparency, tris):
        if not name:
            return
        part = self.parts.get(name)
        if part is None:
            part = {"name": name, "color": color, "transparency": transparency, "tris": []}
            self.parts[name] = part
            self.order.append(name)
        part["tris"].extend(tris)

    def parse_shape(self, tokens, i, matrix, part_name):
        start = i
        depth = 0
        while i < len(tokens):
            if tokens[i] == "{":
                depth += 1
            elif tokens[i] == "}":
                depth -= 1
                if depth == 0:
                    break
            i += 1
        body = tokens[start:i + 1]
        color = (0.70, 0.72, 0.75)
        transparency = 0.0
        for k, t in enumerate(body):
            if t == "diffuseColor":
                vals, _ = read_numbers(body, k + 1, 3)
                color = tuple(vals)
            elif t == "transparency":
                vals, _ = read_numbers(body, k + 1, 1)
                transparency = vals[0]
        points = []
        indices = []
        for k, t in enumerate(body):
            if t == "point":
                vals, _ = read_array(body, k + 1)
                points = [(vals[j], vals[j + 1], vals[j + 2]) for j in range(0, len(vals) - 2, 3)]
            elif t == "coordIndex":
                vals, _ = read_array(body, k + 1)
                indices = vals
        if not points or not indices:
            return i + 1
        world = [apply(matrix, p) for p in points]
        face = []
        tris = []
        for v in indices:
            if v < 0:
                if len(face) >= 3:
                    for k in range(1, len(face) - 1):
                        tris.append((face[0], face[k], face[k + 1]))
                face = []
            else:
                face.append(int(v))
        if len(face) >= 3:
            for k in range(1, len(face) - 1):
                tris.append((face[0], face[k], face[k + 1]))
        flat = []
        for a, b, c in tris:
            try:
                flat.extend(world[a])
                flat.extend(world[b])
                flat.extend(world[c])
            except IndexError:
                pass
        self.add_triangles(part_name, color, transparency, flat)
        return i + 1

    def parse_node(self, tokens, i, matrix, part_name):
        name = None
        if tokens[i] == "DEF":
            name = tokens[i + 1]
            i += 2
        ntype = tokens[i]
        if ntype == "Transform":
            i += 1
            if tokens[i] != "{":
                return i
            i += 1
            t = [0.0, 0.0, 0.0]
            r = [0.0, 1.0, 0.0, 0.0]
            s = [1.0, 1.0, 1.0]
            while i < len(tokens) and tokens[i] not in ("children", "}"):
                f = tokens[i]
                i += 1
                if f == "translation":
                    t, i = read_numbers(tokens, i, 3)
                elif f == "rotation":
                    r, i = read_numbers(tokens, i, 4)
                elif f == "scale":
                    s, i = read_numbers(tokens, i, 3)
                elif f == "center":
                    _, i = read_numbers(tokens, i, 3)
                elif f == "scaleOrientation":
                    _, i = read_numbers(tokens, i, 4)
            local = mat_mul(matrix, mat_from_trs(t, r, s))
            current = name or part_name
            if i < len(tokens) and tokens[i] == "children":
                i += 1
                if tokens[i] == "[":
                    i += 1
                    while i < len(tokens) and tokens[i] != "]":
                        if tokens[i] == ",":
                            i += 1
                            continue
                        i = self.parse_node(tokens, i, local, current)
                    i += 1
                else:
                    i = self.parse_node(tokens, i, local, current)
            if i < len(tokens) and tokens[i] == "}":
                i += 1
            return i
        if ntype == "Shape":
            return self.parse_shape(tokens, i + 1, matrix, part_name)
        depth = 0
        while i < len(tokens):
            if tokens[i] == "{":
                depth += 1
            elif tokens[i] == "}":
                depth -= 1
                if depth == 0:
                    return i + 1
            i += 1
        return i

    def load(self, path):
        tokens = tokenize(Path(path).read_text(encoding="latin-1", errors="replace"))
        i = 0
        while i < len(tokens):
            if tokens[i] in ("DEF", "Transform", "Shape"):
                i = self.parse_node(tokens, i, mat_identity(), None)
            else:
                i += 1
        return self


def bbox(parts):
    lo = [1e18, 1e18, 1e18]
    hi = [-1e18, -1e18, -1e18]
    for p in parts:
        t = p["tris"]
        for k in range(0, len(t), 3):
            for a in range(3):
                v = t[k + a]
                lo[a] = min(lo[a], v)
                hi[a] = max(hi[a], v)
    return lo, hi


def main():
    src = Path(r"D:\Mis Documentos\UniversalData\3D")
    ex = Extractor()
    for f in ("huesos2.WRL", "Organos.WRL"):
        ex.load(src / f)
    parts = [ex.parts[n] for n in ex.order]
    print("partes", len(parts))
    total = 0
    for p in parts:
        n = len(p["tris"]) // 9
        total += n
        print(f'{p["name"]:<34} tris={n:<6} color={p["color"]}')
    print("triangulos", total)
    lo, hi = bbox(parts)
    print("bbox", [round(v, 1) for v in lo], [round(v, 1) for v in hi])
    print("tam", [round(hi[k] - lo[k], 1) for k in range(3)])


if __name__ == "__main__":
    main()
