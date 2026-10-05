"""Curved surfaces for the new standard: every pixel is traced to the surface it shows, then shaded
by the city's light (from the top left: left faces lit, right faces in shade)."""
import math
from kit import HX, HY

ZS = 30.0                                  # map pixels of height per tile, so domes read round
LIGHT = (-0.35, 0.55, 0.76)
_n = math.sqrt(sum(c * c for c in LIGHT)); LIGHT = tuple(c / _n for c in LIGHT)


def lit(n):
    """0 for a face turned to the light, 1 for one turned away."""
    d = n[0] * LIGHT[0] + n[1] * LIGHT[1] + n[2] * LIGHT[2]
    return max(0.0, min(1.0, (1 - d) / 2 * 1.25 - 0.08))


def _box(cv, pts):
    xs, ys = [p[0] for p in pts], [p[1] for p in pts]
    return int(min(xs)) - 1, int(max(xs)) + 2, int(min(ys)) - 1, int(max(ys)) + 2


def dome(L, cv, ca, cb, z0, R, color, zs=ZS):
    """A dome on the plane z0: color(normal, (a, b, z), x, y) paints each pixel it shows."""
    P = cv.P
    x0, x1, y0, y1 = _box(cv, [P(ca - R, cb + R, z0), P(ca + R, cb - R, z0), P(ca + R, cb + R, z0), P(ca - R, cb - R, z0), P(ca, cb, z0 + R * zs)])
    y0 = min(y0, int(P(ca, cb, z0)[1] - R * math.sqrt(zs * zs + 2 * HY * HY)) - 2)   # the outline tops out above the peak, where the back of the curve shows
    for y in range(y0, y1):
        for x in range(x0, x1):
            u, Y = (x + 0.5 - cv.cx) / HX, y + 0.5 - cv.top
            k1, k2 = u / 2 - ca, -u / 2 - cb
            A = 2 + 4 * HY * HY / (zs * zs)
            B = 2 * (k1 + k2) - 4 * HY * (Y + z0) / (zs * zs)
            C = k1 * k1 + k2 * k2 + (Y + z0) ** 2 / (zs * zs) - R * R
            disc = B * B - 4 * A * C
            if disc < 0:
                continue
            p = (-B + math.sqrt(disc)) / (2 * A)
            a, b, z = p + u / 2, p - u / 2, 2 * HY * p - Y
            if z < z0:
                continue
            n = ((a - ca) / R, (b - cb) / R, (z - z0) / zs / R)
            col = color(n, (a, b, z), x, y)
            if col:
                L.px(x, y, col)


def vault(L, cv, ca, b0, b1, z0, R, roof, end, zs=ZS):
    """A half-cylinder roof along b, from b0 to b1, on the plane z0, with its front end (at b1) as a flat face.
    roof(normal, point, x, y) paints the curve; end(point, x, y) paints the front end."""
    P = cv.P
    x0, x1, y0, y1 = _box(cv, [P(ca - R, b1, z0), P(ca + R, b0, z0), P(ca + R, b1, z0), P(ca - R, b0, z0), P(ca, b0, z0 + R * zs), P(ca, b1, z0 + R * zs)])
    y0 = min(y0, int(P(ca, b0, z0)[1] - R * math.sqrt(zs * zs + HY * HY)) - 2)
    for y in range(y0, y1):
        for x in range(x0, x1):
            u, Y = (x + 0.5 - cv.cx) / HX, y + 0.5 - cv.top
            k = u / 2 - ca
            A = 1 + 4 * HY * HY / (zs * zs)
            B = 2 * k - 4 * HY * (Y + z0) / (zs * zs)
            C = k * k + (Y + z0) ** 2 / (zs * zs) - R * R
            disc = B * B - 4 * A * C
            hit = None
            if disc >= 0:
                p = (-B + math.sqrt(disc)) / (2 * A)
                a, b, z = p + u / 2, p - u / 2, 2 * HY * p - Y
                if z >= z0 and b0 <= b <= b1:
                    hit = ('roof', (a, b, z), ((a - ca) / R, 0.0, (z - z0) / zs / R))
                elif b > b1:                                   # past the front end: it is the end face that shows
                    p = b1 + u / 2
                    a, z = p + u / 2, 2 * HY * p - Y
                    if z >= z0 and (a - ca) ** 2 + ((z - z0) / zs) ** 2 <= R * R:
                        hit = ('end', (a, b1, z), None)
            if not hit:
                continue
            col = roof(hit[2], hit[1], x, y) if hit[0] == 'roof' else end(hit[1], x, y)
            if col:
                L.px(x, y, col)
