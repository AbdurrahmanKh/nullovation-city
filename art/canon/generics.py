"""The Nullovation City generic buildings. Each returns (frames, delays): 8 index frames at native size."""
import math
from kit import (Layer, P, T, W, H, ground, std_lawns, box, win_left, win_right, cylinder, wall_y, dome, blob,
                 steam, composite)

N = 8
WHITE_CYL = [(-1.0, 'lsteel'), (-0.84, 'white'), (-0.52, 'pave'), (0.22, 'lsteel'), (0.58, 'slab'), (0.84, 'slabShade')]


def pod_shape(L, cx, cy, rx, ry, h, bands, dome_h, dome_fill):
    cylinder(L, cx, cy, rx, ry, h, bands)
    dome(L, cx, cy - h, rx, ry, dome_h, dome_fill)


# ============ 1. City hall (medium): the dome holds a tiny city; a drone pad beside it ============
def city_hall(f):
    lift = [0, 0, 2, 5, 8, 8, 5, 2][f]
    g = ground(lawns=std_lawns(), paths=[(2.05, 3.1, 2.7, 4)], frame=f)
    for (a, b) in ((0.5, 3.55), (1.3, 3.6), (3.2, 3.55), (0.45, 1.2), (0.5, 2.2)):
        x, y = P(a, b)
        for dx, dy, c in ((0, -1, 'leaf'), (-1, 0, 'leaf'), (1, 0, 'leaf'), (0, 0, 'leaf'), (-1, -1, 'lawn'), (0, -2, 'lawn')):
            g.px(x + dx, y + dy, c)
    t = Layer()
    CX, CYB, RX, RY, HT = 54, T + 30, 24, 12, 54
    CYT = CYB - HT
    cylinder(t, CX, CYB, RX, RY, HT, WHITE_CYL)
    for x in range(CX - RX, CX + RX + 1):
        nx = (x + 0.5 - CX) / RX
        if abs(nx) >= 1:
            continue
        yt, yb = round(wall_y(CX, CYT, RX, RY, x)), round(wall_y(CX, CYB, RX, RY, x))
        for y in range(yt, yt + 5):
            t.px(x, y, 'rose' if nx > 0.45 else ('white' if y == yt + 1 and nx < -0.4 else 'pink'))
        for y in range(yb - 5, yb):
            t.px(x, y, 'rose' if nx > 0.35 or y == yb - 1 else 'pink')
        t.px(x, yt + 5, 'rose' if nx > -0.2 else 'lsteel')
    lit = {1: (1, 3, 5, 7), 3: (0, 2, 4, 6)}
    for i, ang in enumerate((-62, -31, 0, 31, 62)):
        s = math.sin(math.radians(ang))
        ww = max(3, round(8 * math.cos(math.radians(ang))))
        x0 = round(CX + RX * s - ww / 2)
        on = f in lit.get(i, ())
        for x in range(x0, x0 + ww):
            if abs((x + 0.5 - CX) / RX) >= 0.97:
                continue
            y0 = round(wall_y(CX, CYT, RX, RY, x)) + 10
            for y in range(y0, y0 + 17):
                edge = x in (x0, x0 + ww - 1) or y in (y0, y0 + 16)
                rel = (x - x0) / max(1, ww - 1)
                col = 'butter' if edge else (('butter' if (x + y) % 3 else 'white') if on else
                                             ('iteal' if (rel < 0.34 and y < y0 + 6) else ('dteal' if rel > 0.66 else 'teal')))
                t.px(x, y, col)
    for x in range(CX - 6, CX + 6):
        yb = round(wall_y(CX, CYB, RX, RY, x))
        for y in range(yb - 20, yb - 5):
            fr = x in (CX - 6, CX + 5) or y == yb - 20
            t.px(x, y, ('rose' if x > CX else 'pink') if fr else ('asphalt' if x in (CX - 1, CX) else 'outline'))
        for y in range(yb - 27, yb - 22):
            border = y in (yb - 27, yb - 23) or x in (CX - 6, CX + 5)
            glow = (not border) and ((x - CX + 6) % 3 != 2) and y == yb - 25
            t.px(x, y, 'outline' if border else ('neon' if glow else ('rose' if y == yb - 24 else 'asphalt')))
    t.ellipse(CX, CYT, RX, RY, lambda x, y: 'white' if (x - CX) < -RX * 0.35 else ('pave' if (x - CX) < RX * 0.45 else 'lsteel'))
    t.ellipse(CX, CYT + 1, RX - 2, RY - 1, 'lsteel')
    t.outlined()
    d = Layer()
    DRX, DRY, DH = 20, 10, 21
    dome(d, CX, CYT, DRX, DRY, DH, lambda x, y, nx: 'teal' if nx > 0.55 else 'iteal', highlight=None)
    d.ellipse(CX, CYT + 1, DRX - 2, DRY - 2, 'dteal')
    city = [(-9, -2, 4, 13, 'teal'), (0, -4, 4, 17, 'pink'), (8, -1, 4, 10, 'white'),
            (-4, 3, 3, 9, 'white'), (5, 4, 3, 12, 'teal'), (-12, 4, 3, 6, 'pink'), (12, 4, 3, 7, 'pink')]
    cols = {'teal': ('teal', 'dteal', 'iteal'), 'pink': ('pink', 'rose', 'white'), 'white': ('pave', 'lsteel', 'white')}
    for i, (ox, oy, hw, hgt, c) in enumerate(city):
        bx, by = CX + ox, CYT + oy + 2
        l, r, tp = cols[c]
        d.poly([(bx - hw, by - hw / 2), (bx, by), (bx, by - hgt), (bx - hw, by - hw / 2 - hgt)], l)
        d.poly([(bx, by), (bx + hw, by - hw / 2), (bx + hw, by - hw / 2 - hgt), (bx, by - hgt)], r)
        d.poly([(bx, by - hw - hgt), (bx + hw, by - hw / 2 - hgt), (bx, by - hgt), (bx - hw, by - hw / 2 - hgt)], tp)
        for k in range(2, hgt - 1, 3):
            on = (i * 3 + k + f) % 4 != 0
            d.px(bx - hw + 1 + (k % 2), by - hw // 2 - k, 'butter' if on else r)
            d.px(bx + 1 + (k % 2), by - hw // 2 - k + 1, 'butter' if (on and (i + f) % 2) else r)
    for k in range(9):
        ang = math.radians(200 + k * 7)
        x, y = CX + (DRX - 4) * math.cos(ang), CYT + (DH - 4) * math.sin(ang)
        d.px(x, y, 'white')
        if k < 5:
            d.px(x + 1, y, 'white')
    for x in range(CX - DRX, CX + DRX):
        nx = (x + 0.5 - CX) / DRX
        if abs(nx) < 1:
            y = round(CYT + DRY * math.sqrt(1 - nx * nx) * 0.95)
            d.px(x, y, 'rose' if nx > 0.3 else 'pink'); d.px(x, y - 1, 'rose' if nx > 0.3 else 'pink')
    d.outlined()
    p = Layer()
    PCX, PCY, PRX, PRY, PHT = 99, T + 36, 15, 7.5, 5
    cylinder(p, PCX, PCY, PRX, PRY, PHT, [(-1, 'slab'), (-0.3, 'lsteel'), (0.4, 'slabShade')])
    p.ellipse(PCX, PCY - PHT, PRX, PRY, 'asphalt')
    p.ellipse(PCX, PCY - PHT, PRX - 3, PRY - 1.5, 'pink')
    p.ellipse(PCX, PCY - PHT, PRX - 4, PRY - 2.5, 'asphalt')
    hx, hy = PCX, PCY - PHT
    for dx, dy in ((-4, -1), (-4, 0), (-4, 1), (4, -1), (4, 0), (4, 1), (-3, 0), (-2, 0), (-1, 0), (0, 0), (1, 0), (2, 0), (3, 0)):
        p.px(hx + dx, hy + dy, 'white')
    if lift > 0:
        sr = max(2, 5 - lift // 3)
        for dx in range(-sr, sr + 1):
            p.px(hx + dx, hy + 2, 'outline' if abs(dx) < sr else 'asphalt')
    p.outlined()
    dr = Layer()
    bx, by = PCX, PCY - PHT - 4 - lift
    for ax, ay in ((-7, -3), (7, -3), (-7, 2), (7, 2)):
        dr.line(bx, by, bx + ax, by + ay, 'asphalt')
        rw = 3 if f % 2 else 2
        for dx in range(-rw, rw + 1):
            dr.px(bx + ax + dx, by + ay - 1, 'white' if abs(dx) == rw else 'lsteel')
    for dx in range(-4, 5):
        dr.px(bx + dx, by - 1, 'white' if dx < -1 else 'pave')
        dr.px(bx + dx, by, 'pave' if dx < 1 else 'lsteel')
        dr.px(bx + dx, by + 1, 'slab' if dx < 1 else 'slabShade')
    for dx in range(-2, 3):
        dr.px(bx + dx, by - 2, 'pave' if dx < 1 else 'lsteel')
    dr.px(bx + 1, by, 'neon' if f % 4 < 2 else 'rose'); dr.px(bx + 2, by, 'neon' if f % 4 < 2 else 'rose')
    dr.outlined()
    return composite([g, t, d, p, dr])


# ============ 2. Habitat pod (small): a rounded low module with portholes ============
def habitat_pod(f):
    g = ground(lawns=std_lawns(), paths=[(1.75, 3.1, 2.25, 4)], shrubs=[(0.45, 1.3), (3.3, 3.5), (0.6, 3.6)], frame=f, seed=2)
    L = Layer()
    cx, cy = P(2.15, 1.95)
    cx, cy = round(cx), round(cy)
    bands = [(-1.0, 'lavender'), (-0.84, 'white'), (-0.5, 'lilac'), (0.2, 'lavender'), (0.62, 'violet')]
    cylinder(L, cx, cy, 22, 11, 15, bands)
    dome(L, cx, cy - 15, 22, 11, 15, lambda x, y, nx: 'white' if nx < -0.55 else ('lilac' if nx < 0.25 else ('lavender' if nx < 0.7 else 'violet')))
    for x in range(cx - 22, cx + 23):              # a violet belt where the dome meets the wall
        nx = (x + 0.5 - cx) / 22
        if abs(nx) < 1:
            y = round(wall_y(cx, cy - 15, 22, 11, x))
            L.px(x, y, 'violet'); L.px(x, y - 1, 'lavender' if nx < 0.5 else 'violet')
    for i, ang in enumerate((-52, -18, 16, 50)):   # portholes that glow on and off
        px_ = round(cx + 22 * math.sin(math.radians(ang)))
        py_ = round(wall_y(cx, cy - 8, 22, 11, px_))
        on = (i + f // 2) % 3 != 0
        for dx in range(-2, 2):
            for dy in range(-2, 2):
                ring = dx in (-2, 1) or dy in (-2, 1)
                corner = dx in (-2, 1) and dy in (-2, 1)
                if corner:
                    continue
                L.px(px_ + dx, py_ + dy, 'violet' if ring else ('butter' if on else 'teal'))
    box(L, 1.55, 2.75, 2.25, 3.15, 0, 10, 'lilac', 'lavender', 'white')   # the airlock
    win_left(L, 1.75, 2.05, 3.15, 0, 8, 'violet')
    win_left(L, 1.8, 2.0, 3.15, 1, 7, 'teal')
    L.outlined()
    top = Layer()
    tx, ty = cx, cy - 15 - 15
    top.line(tx, ty, tx, ty - 5, 'violet')
    top.px(tx, ty - 6, 'neon' if f % 4 < 2 else 'violet'); top.px(tx + 1, ty - 6, 'neon' if f % 4 < 2 else 'violet')
    top.outlined()
    sp = Layer()                                    # a small solar panel on a post
    sx, sy = P(3.35, 1.05)
    sp.line(sx, sy, sx, sy - 7, 'violet')
    sp.poly([(sx - 7, sy - 9), (sx + 1, sy - 13), (sx + 7, sy - 10), (sx - 1, sy - 6)], 'dteal')
    for k in range(-5, 6, 3):
        sp.line(sx + k - 1, sy - 8 - k * 0.3, sx + k + 1, sy - 11 - k * 0.3, 'teal')
    sp.outlined()
    return composite([g, L, top, sp])


# ============ 3. Research lab (medium): a flat block with a dish on the roof ============
def research_lab(f):
    g = ground(lawns=std_lawns(), paths=[(1.25, 3.1, 1.8, 4)], shrubs=[(0.45, 1.0), (0.5, 2.3), (2.7, 3.55), (3.5, 3.5)], frame=f, seed=3)
    L = Layer()
    a0, b0, a1, b1, h = 1.0, 0.9, 3.15, 2.95, 30
    box(L, a0, b0, a1, b1, 0, h, 'pave', 'lsteel', 'white')
    L.poly([P(a0, b1, 0), P(a1, b1, 0), P(a1, b1, 3), P(a0, b1, 3)], 'psky')   # plinth, left face
    L.poly([P(a1, b1, 0), P(a1, b0, 0), P(a1, b0, 3), P(a1, b1, 3)], 'sky')    # plinth, right face
    L.poly([P(a0, b1, h), P(a1, b1, h), P(a1, b1, h - 4), P(a0, b1, h - 4)], 'psky')   # top trim, left face
    L.poly([P(a1, b1, h), P(a1, b0, h), P(a1, b0, h - 4), P(a1, b1, h - 4)], 'sky')    # top trim, right face
    L.poly([P(a0 + 0.12, b0 + 0.12, h), P(a1 - 0.12, b0 + 0.12, h), P(a1 - 0.12, b1 - 0.12, h), P(a0 + 0.12, b1 - 0.12, h)], 'lsteel')
    for row, (z0, z1) in enumerate(((8, 13), (17, 22))):              # ribbon windows
        for k in range(4):
            aa = 1.85 + k * 0.33
            on = (k + row + f // 2) % 5 == 0
            win_left(L, aa, aa + 0.26, b1, z0, z1, 'butter' if on else 'teal')
            L.poly([P(aa, b1, z1), P(aa + 0.1, b1, z1), P(aa + 0.1, b1, z1 - 2), P(aa, b1, z1 - 2)], 'iteal')
        for k in range(5):
            bb = 1.05 + k * 0.36
            win_right(L, bb, bb + 0.27, a1, z0, z1, 'butter' if (k + row + f) % 7 == 0 else 'dteal')
    win_left(L, 1.2, 1.65, b1, 0, 12, 'sky')                          # the door and its sign
    win_left(L, 1.27, 1.58, b1, 1, 11, 'outline')
    win_left(L, 1.15, 1.7, b1, 14, 18, 'outline')
    for k in range(3):
        if (k + f) % 3 != 2:
            win_left(L, 1.22 + k * 0.15, 1.32 + k * 0.15, b1, 15, 17, 'cyan')
    L.outlined()
    D = Layer()                                                        # the dish sweeps round
    mx, my = P(2.2, 1.6, h)
    D.line(mx, my, mx, my - 6, 'slabShade'); D.line(mx + 1, my, mx + 1, my - 6, 'lsteel')
    ang = f * (2 * math.pi / N)
    ox, oy = math.cos(ang) * 3.5, math.sin(ang) * 1.6
    D.ellipse(mx + 0.5, my - 11, 9, 5.5, lambda x, y: 'white' if x < mx - 3 else ('lsteel' if x < mx + 4 else 'slab'))
    D.ellipse(mx + 0.5 + ox, my - 11 + oy, 5.5, 3.2, 'slab')
    D.ellipse(mx + 0.5 + ox * 1.2, my - 11 + oy * 1.2, 2.5, 1.5, 'lsteel')
    D.line(mx + 0.5 + ox, my - 11 + oy, mx + 0.5 + ox * 2.4, my - 11 + oy * 2.4 - 3, 'slabShade')
    D.px(mx + 0.5 + ox * 2.4, my - 11 + oy * 2.4 - 4, 'cyan')
    D.outlined()
    return composite([g, L, D])


# ============ 4. Data tower (small, tall): a slim tower with light strips up its corners ============
def data_tower(f):
    g = ground(lawns=std_lawns(), paths=[(1.85, 3.1, 2.35, 4)], shrubs=[(0.5, 1.4), (0.45, 2.5), (1.2, 3.6)], frame=f, seed=4)
    L = Layer()
    a0, b0, a1, b1, h = 1.45, 1.35, 2.65, 2.55, 86
    box(L, a0, b0, a1, b1, 0, h, 'pave', 'lsteel', 'white')
    for z in range(10, h - 4, 13):                                     # floor bands
        L.poly([P(a0, b1, z + 2), P(a1, b1, z + 2), P(a1, b1, z), P(a0, b1, z)], 'teal')
        L.poly([P(a1, b1, z + 2), P(a1, b0, z + 2), P(a1, b0, z), P(a1, b1, z)], 'dteal')
        for k in range(3):                                             # little windows between the bands
            aa = a0 + 0.18 + k * 0.33
            on = (k + z // 13 + f) % 6 == 0
            win_left(L, aa, aa + 0.19, b1, z + 5, z + 10, 'butter' if on else 'teal')
            bb = b0 + 0.18 + k * 0.33
            win_right(L, bb, bb + 0.19, a1, z + 5, z + 10, 'butter' if (k + z // 13 + f + 3) % 6 == 0 else 'dteal')
    win_left(L, 1.85, 2.25, b1, 0, 9, 'teal')
    win_left(L, 1.9, 2.2, b1, 1, 8, 'outline')
    L.poly([P(a0, b0, h), P(a1, b0, h), P(a1, b1, h), P(a0, b1, h)], 'white')
    L.poly([P(a0 + 0.1, b0 + 0.1, h), P(a1 - 0.1, b0 + 0.1, h), P(a1 - 0.1, b1 - 0.1, h), P(a0 + 0.1, b1 - 0.1, h)], 'lsteel')
    # light strips on the three visible corners: a bright pulse climbs each one
    for (ca, cb) in ((a0, b1), (a1, b1), (a1, b0)):
        x, y0 = P(ca, cb, 0)
        x = round(x)
        for z in range(1, h):
            phase = ((z / h) * N - f) % N
            col = 'white' if phase < 0.5 else ('cyan' if phase < 1.6 else 'dteal')
            if (ca, cb) == (a1, b1):
                L.px(x - 1, y0 - z, col); L.px(x, y0 - z, col)
            elif (ca, cb) == (a0, b1):
                L.px(x, y0 - z - 0.5, col)
            else:
                L.px(x - 1, y0 - z - 0.5, col)
    L.outlined()
    A = Layer()
    tx, ty = P(2.05, 1.95, h)
    A.line(tx, ty, tx, ty - 9, 'dteal')
    A.px(tx, ty - 10, 'cyan' if f % 4 < 2 else 'teal'); A.px(tx - 1, ty - 10, 'cyan' if f % 4 < 2 else 'teal')
    A.outlined()
    U = Layer()                                                        # a cooling unit with a spinning fan
    box(U, 2.95, 2.3, 3.55, 2.9, 0, 9, 'pave', 'lsteel', 'white')
    fx, fy = P(3.25, 2.6, 9)
    U.ellipse(fx, fy, 6, 3, 'slab')
    for k in range(3):
        ang = f * (math.pi / 6) + k * (2 * math.pi / 3)
        U.line(fx, fy, fx + math.cos(ang) * 5, fy + math.sin(ang) * 2.5, 'slabShade')
    U.px(fx, fy, 'dteal')
    U.outlined()
    return composite([g, L, A, U])


# ============ 5. Hangar (medium): a wide low building with a big bay door ============
def hangar(f):
    g = ground(lawns=[(0, 0, 0.6, 3.2), (3.6, 0, 4, 4)], paths=[(0.6, 3.2, 3.6, 4)], shrubs=[(0.3, 1.2), (3.8, 1.5), (3.8, 3.0)], tiles=True, frame=f, seed=5)
    g.poly([P(0.9, 3.15, 0), P(3.1, 3.15, 0), P(3.1, 3.95, 0), P(0.9, 3.95, 0)], 'asphalt')   # apron
    for k in range(4):
        aa = 1.1 + k * 0.5
        g.poly([P(aa, 3.5), P(aa + 0.25, 3.5), P(aa + 0.25, 3.58), P(aa, 3.58)], 'white')
    L = Layer()
    a0, a1, b0, b1, zw, R = 0.75, 3.25, 0.7, 3.0, 11, 17
    ac, ra = (a0 + a1) / 2, (a1 - a0) / 2
    zf = lambda a: zw + R * math.sqrt(max(0.0, 1 - ((a - ac) / ra) ** 2))
    # right side wall, then the vaulted roof, strip by strip across a
    L.poly([P(a1, b1, 0), P(a1, b0, 0), P(a1, b0, zw), P(a1, b1, zw)], 'lsteel')
    for k in range(4):
        bb = b0 + 0.3 + k * 0.5
        win_right(L, bb, bb + 0.3, a1, 4, 8, 'dteal')
    steps = 64
    for i in range(steps):
        aa, ab = a0 + (a1 - a0) * i / steps, a0 + (a1 - a0) * (i + 1) / steps
        slope = zf(ab) - zf(aa)
        col = 'white' if abs(slope) < 0.18 else ('peach' if slope > 0 else 'coral')
        L.poly([P(aa, b0, zf(aa)), P(ab, b0, zf(ab)), P(ab, b1, zf(ab)), P(aa, b1, zf(aa))], col)
    for k in range(1, 6):                                              # roof ribs
        bb = b0 + k * (b1 - b0) / 6
        for i in range(steps):
            aa = a0 + (a1 - a0) * i / steps
            x, y = P(aa, bb, zf(aa))
            L.px(x, y, 'coral' if zf(aa + 0.02) - zf(aa) > 0 else 'outline')
    # the gable end facing us, with the bay door
    arch = [P(a0, b1, 0)] + [P(a0 + (a1 - a0) * i / 48, b1, zf(a0 + (a1 - a0) * i / 48)) for i in range(49)] + [P(a1, b1, 0)]
    L.poly(arch, 'pave')
    for i in range(49):
        aa = a0 + (a1 - a0) * i / 48
        x, y = P(aa, b1, zf(aa))
        L.px(x, y, 'peach'); L.px(x, y + 1, 'peach')
    win_left(L, 1.15, 2.85, b1, 0, 18, 'coral')
    for z in range(1, 17):
        L.poly([P(1.22, b1, z + 1), P(2.78, b1, z + 1), P(2.78, b1, z), P(1.22, b1, z)], 'asphalt' if z % 3 == 0 else 'lsteel')
    L.poly([P(1.85, b1, 25), P(2.15, b1, 25), P(2.15, b1, 21), P(1.85, b1, 21)], 'teal')          # round window
    L.px(*P(2.0, b1, 19.5), 'butter' if f % 4 < 2 else 'coral')                                    # warning light
    L.px(*P(2.06, b1, 19.5), 'butter' if f % 4 < 2 else 'coral')
    L.outlined()
    C = Layer()                                                        # a little tug going back and forth
    u = [0, 0.1, 0.25, 0.4, 0.5, 0.4, 0.25, 0.1][f]
    ca = 1.3 + u * 1.3
    box(C, ca, 3.35, ca + 0.45, 3.65, 1, 6, 'pave', 'lsteel', 'white')
    C.poly([P(ca, 3.65, 3), P(ca + 0.45, 3.65, 3), P(ca + 0.45, 3.65, 1.5), P(ca, 3.65, 1.5)], 'coral')
    for wa in (ca + 0.08, ca + 0.33):
        C.px(*P(wa, 3.65, 0.5), 'outline'); C.px(*P(wa + 0.06, 3.65, 0.5), 'outline')
    C.px(*P(ca + 0.45, 3.5, 4), 'butter')
    C.outlined()
    return composite([g, L, C])


# ============ 6. Greenhouse dome (medium): a glass dome over plants ============
def greenhouse(f):
    g = ground(lawns=[(0, 3.1, 4, 4), (0, 0, 0.8, 3.1)], pools=[(3.0, 0.7, 3.8, 1.9)], shrubs=[(0.4, 1.2), (0.45, 2.4), (1.2, 3.6), (2.8, 3.6)], frame=f, seed=6)
    L = Layer()
    cx, cy = P(1.95, 2.05)
    cx, cy = round(cx), round(cy)
    rx, ry = 29, 14.5
    cylinder(L, cx, cy, rx, ry, 5, [(-1, 'lsteel'), (-0.8, 'white'), (-0.45, 'pave'), (0.3, 'lsteel'), (0.7, 'slab')])
    for x in range(cx - rx, cx + rx + 1):
        if abs((x + 0.5 - cx) / rx) < 1:
            y = round(wall_y(cx, cy - 5, rx, ry, x))
            L.px(x, y + 1, 'dleaf')
    dome(L, cx, cy - 5, rx - 1, ry - 0.5, 31, lambda x, y, nx: 'teal' if nx > 0.5 else 'iteal', highlight=None)
    # plants inside, seen through the glass
    for (ox, oy, r) in ((-14, -8, 6), (-4, -12, 7), (8, -9, 6), (16, -5, 4), (-18, -3, 4), (2, -4, 5), (-9, -2, 4)):
        blob(L, cx + ox, cy - 5 + oy, r, 'leaf', 'lawn', 'dleaf')
    for (ox, oy) in ((-12, -12), (-2, -16), (9, -12), (3, -7), (-16, -6), (14, -8)):
        L.px(cx + ox, cy - 5 + oy, 'pink')
    # glass frame: meridians and a latitude ring, drawn over the plants
    for k in range(-2, 3):
        nx0 = k * 0.36
        for z in range(0, 31):
            s = math.sqrt(max(0.0, 1 - (z / 31) ** 2))
            x = cx + nx0 * (rx - 1) * s
            y = cy - 5 - z + (ry - 0.5) * math.sqrt(max(0.0, 1 - nx0 ** 2)) * s * 0.9
            L.px(x, y, 'white' if k < 1 else 'lsteel')
    for x in range(cx - rx + 4, cx + rx - 3):
        nx = (x + 0.5 - cx) / (rx - 4)
        if abs(nx) < 1:
            y = cy - 5 - 16 + (ry - 4) * math.sqrt(1 - nx * nx) * 0.8
            L.px(x, y, 'white' if nx < 0.4 else 'lsteel')
    for k in range(7):
        ang = math.radians(208 + k * 9)
        L.px(cx + (rx - 6) * math.cos(ang), cy - 5 + 26 * math.sin(ang), 'white')
    L.outlined()
    E = Layer()                                                        # the entrance
    box(E, 1.7, 3.1, 2.25, 3.45, 0, 11, 'pave', 'lsteel', 'white')
    win_left(E, 1.8, 2.15, 3.45, 0, 9, 'dleaf')
    win_left(E, 1.86, 2.09, 3.45, 1, 8, 'teal')
    E.outlined()
    return composite([g, L, E])


# ============ 7. Power station (medium): a squat block with cooling fins and a glowing core ============
def power_station(f):
    g = ground(lawns=std_lawns(), paths=[(2.1, 3.1, 2.6, 4)], shrubs=[(0.45, 1.1), (0.45, 2.5), (3.4, 3.55)], frame=f, seed=7)
    L = Layer()
    a0, b0, a1, b1, h = 0.95, 1.05, 3.05, 3.0, 21
    box(L, a0, b0, a1, b1, 0, h, 'pave', 'lsteel', 'white')
    for k in range(10):                                                # fins along the left face
        aa = a0 + 0.12 + k * 0.19
        L.poly([P(aa, b1, h - 4), P(aa + 0.06, b1, h - 4), P(aa + 0.06, b1, 3), P(aa, b1, 3)], 'white')
        L.poly([P(aa + 0.06, b1, h - 4), P(aa + 0.12, b1, h - 4), P(aa + 0.12, b1, 3), P(aa + 0.06, b1, 3)], 'slab')
    L.poly([P(a0, b1, h), P(a1, b1, h), P(a1, b1, h - 3), P(a0, b1, h - 3)], 'gold')
    L.poly([P(a1, b1, h), P(a1, b0, h), P(a1, b0, h - 3), P(a1, b1, h - 3)], 'gold')
    L.poly([P(a1, b1, 3), P(a1, b0, 3), P(a1, b0, 0), P(a1, b1, 0)], 'asphalt')
    for k in range(5):                                                 # hazard stripes on the right plinth
        bb = b0 + 0.2 + k * 0.37
        L.poly([P(a1, bb, 3), P(a1, bb + 0.15, 3), P(a1, bb + 0.15, 0), P(a1, bb, 0)], 'butter')
    win_right(L, 1.4, 2.0, a1, 5, 15, 'steel')
    win_right(L, 1.46, 1.94, a1, 6, 14, 'asphalt')
    L.outlined()
    C = Layer()                                                        # the core in its cage, pulsing
    cx, cy = P(2.0, 2.0, h)
    cx, cy = round(cx), round(cy) - 9
    pulse = [0, 1, 2, 3, 3, 2, 1, 0][f]
    for dy in range(-9, 10):
        for dx in range(-9, 10):
            d2 = dx * dx + dy * dy
            if d2 <= 81:
                col = 'cyan' if d2 <= (12 + pulse * 6) else ('iteal' if d2 <= 52 + pulse * 4 else 'steel')
                if d2 <= 3 + pulse:
                    col = 'white'
                C.px(cx + dx, cy + dy, col)
    for k in (-9, -3, 3, 9):                                           # cage bars
        for dy in range(-9, 11):
            if abs(k) < 9 or abs(dy) < 6:
                C.px(cx + k, cy + dy, 'steel')
    C.ellipse(cx, cy + 9, 11, 4, 'gold')
    C.ellipse(cx, cy + 9, 8, 2.5, 'asphalt')
    C.outlined()
    V = Layer()                                                        # two vents that puff steam
    for (va, vb, ph) in ((1.2, 1.3, 0), (2.7, 1.3, 4)):
        box(V, va, vb, va + 0.3, vb + 0.3, h, h + 7, 'lsteel', 'slab', 'asphalt')
        vx, vy = P(va + 0.15, vb + 0.15, h + 8)
        steam(V, vx, vy, f + ph, height=11)
    V.outlined()
    return composite([g, L, V, C])


# ============ 8. Comms spire (small, the tallest): a needle tower with an antenna ring ============
def comms_spire(f):
    g = ground(lawns=[(0, 3.1, 4, 4), (0, 0, 0.9, 3.1), (3.2, 0, 4, 1.2)], paths=[(1.85, 3.1, 2.35, 4)], shrubs=[(0.45, 1.4), (0.5, 2.6), (3.6, 0.6), (2.9, 3.6)], frame=f, seed=8)
    B = Layer()
    cx, cy = P(2.0, 2.0)
    cx, cy = round(cx), round(cy)
    cylinder(B, cx, cy, 17, 8.5, 7, [(-1, 'lilac'), (-0.8, 'white'), (-0.45, 'lilac'), (0.25, 'lavender'), (0.65, 'violet')], top='lilac')
    B.ellipse(cx, cy - 7, 13, 6.5, 'lavender')
    B.outlined()
    ring_z = 104
    R = Layer()                                                        # back half of the antenna ring
    for x in range(cx - 12, cx + 13):
        nx = (x + 0.5 - cx) / 12
        if abs(nx) < 1:
            R.px(x, cy - 7 - ring_z - 5 * math.sqrt(1 - nx * nx), 'violet')
    S = Layer()                                                        # the needle, tapering to a point
    top_h = 128
    for z in range(0, top_h):
        w = max(1.0, 6.5 - z / 22)
        y = cy - 7 - z
        for x in range(round(cx - w), round(cx + w)):
            rel = (x + 0.5 - (cx - w)) / (2 * w)
            S.px(x, y, 'white' if rel < 0.3 else ('lilac' if rel < 0.6 else ('lavender' if rel < 0.85 else 'violet')))
        if z % 20 == 10 and z < 100:
            for x in range(round(cx - w), round(cx + w)):
                S.px(x, y, 'violet')
    for i, z in enumerate((22, 46, 70, 94, top_h)):                    # beacons blink up the needle, in turn
        on = (f % 5) == i or (i == 4 and f % 2 == 0)
        S.px(cx - 1, cy - 7 - z, 'neon' if on else 'violet'); S.px(cx, cy - 7 - z, 'neon' if on else 'violet')
        if i == 4:
            S.px(cx - 1, cy - 8 - z, 'neon' if on else 'violet'); S.px(cx, cy - 8 - z, 'neon' if on else 'violet')
    S.outlined()
    F = Layer()                                                        # front half of the ring, glowing in turn
    for x in range(cx - 12, cx + 13):
        nx = (x + 0.5 - cx) / 12
        if abs(nx) < 1:
            y = cy - 7 - ring_z + 5 * math.sqrt(1 - nx * nx)
            lit = ((x - cx + 12) // 4 + f) % 6 == 0
            F.px(x, y, 'neon' if lit else ('lilac' if nx < 0.3 else 'lavender'))
            F.px(x, y + 1, 'violet')
    for sx in (-12, 12):
        F.line(cx + sx * 0.5, cy - 7 - ring_z + 2, cx, cy - 7 - ring_z - 3, 'violet')
    F.outlined()
    Sh = Layer()                                                       # an equipment shed
    box(Sh, 2.85, 2.5, 3.35, 3.0, 0, 8, 'lilac', 'lavender', 'white')
    win_left(Sh, 2.97, 3.2, 3.0, 0, 6, 'violet')
    Sh.outlined()
    return composite([g, B, R, S, F, Sh])


# ============ 9. Workshop (medium): a garage bay with a crane arm ============
def workshop(f):
    g = ground(lawns=[(0, 0, 0.7, 3.2), (3.3, 0, 4, 1.4)], paths=[], shrubs=[(0.35, 1.3), (0.4, 2.6), (3.7, 0.7)], frame=f, seed=9)
    g.poly([P(0.7, 3.1), P(3.3, 3.1), P(3.3, 4), P(0.7, 4)], 'asphalt')   # yard in front of the bay
    for k in range(3):
        g.poly([P(1.2 + k * 0.5, 3.8), P(1.4 + k * 0.5, 3.8), P(1.4 + k * 0.5, 3.88), P(1.2 + k * 0.5, 3.88)], 'butter')
    L = Layer()
    a0, b0, a1, b1, h = 0.8, 1.15, 3.05, 3.0, 24
    box(L, a0, b0, a1, b1, 0, h, 'pave', 'lsteel', 'white')
    L.poly([P(a0, b1, h), P(a1, b1, h), P(a1, b1, h - 3), P(a0, b1, h - 3)], 'coral')
    L.poly([P(a1, b1, h), P(a1, b0, h), P(a1, b0, h - 3), P(a1, b1, h - 3)], 'coral')
    win_left(L, 1.05, 2.45, b1, 0, 17, 'coral')                       # roll-up door, half open
    for z in range(5, 16):
        L.poly([P(1.12, b1, z + 1), P(2.38, b1, z + 1), P(2.38, b1, z), P(1.12, b1, z)], 'slab' if z % 2 else 'lsteel')
    L.poly([P(1.12, b1, 5), P(2.38, b1, 5), P(2.38, b1, 0), P(1.12, b1, 0)], 'outline')
    win_left(L, 2.6, 2.9, b1, 9, 15, 'teal')
    for k in range(3):
        win_right(L, b0 + 0.3 + k * 0.5, b0 + 0.6 + k * 0.5, a1, 9, 15, 'butter' if (k + f // 2) % 4 == 0 else 'asphalt')
    L.outlined()
    K = Layer()                                                        # the crane on the roof
    mx, my = P(2.7, 1.45, h)
    K.line(mx, my, mx, my - 16, 'steel'); K.line(mx + 1, my, mx + 1, my - 16, 'asphalt')
    jx, jy = P(1.45, 2.65, h + 27)                                     # the jib angles up and out
    K.line(mx, my - 16, jx, jy, 'steel'); K.line(mx, my - 15, jx, jy + 1, 'coral')
    K.line(mx, my - 16, mx + 7, my - 19, 'steel')                      # back arm with a counterweight
    for dx in range(0, 4):
        for dy in range(0, 3):
            K.px(mx + 5 + dx, my - 20 + dy - dx // 2, 'asphalt' if dy else 'steel')
    K.line(mx, my - 16, mx, my - 22, 'steel')
    hx, hy = round(jx + 2), round(jy + 1)
    K.line(hx, hy, hx, hy + 9, 'asphalt')
    K.px(hx - 1, hy + 10, 'steel'); K.px(hx, hy + 10, 'steel'); K.px(hx + 1, hy + 9, 'steel')
    K.px(mx, my - 23, 'butter' if f % 4 < 2 else 'coral'); K.px(mx + 1, my - 23, 'butter' if f % 4 < 2 else 'coral')
    K.outlined()
    V = Layer()                                                        # a little cart rolls out of the bay and back
    u = [0, 0.08, 0.2, 0.32, 0.4, 0.32, 0.2, 0.08][f]
    vb = 3.1 + u
    box(V, 1.45, vb, 1.9, vb + 0.35, 1, 6, 'peach', 'coral', 'white')
    V.px(*P(1.52, vb + 0.35, 0.5), 'outline'); V.px(*P(1.83, vb + 0.35, 0.5), 'outline')
    V.px(*P(1.9, vb + 0.15, 4), 'butter')
    V.outlined()
    Cr = Layer()                                                       # crates by the door
    box(Cr, 2.55, 3.25, 2.9, 3.6, 0, 6, 'peach', 'wood', 'peach')
    box(Cr, 2.62, 3.3, 2.88, 3.56, 6, 11, 'peach', 'wood', 'peach')
    Cr.outlined()
    return composite([g, L, K, V, Cr])


# ============ 10. Kiosk (small): a tiny stall with an awning ============
def kiosk(f):
    g = ground(lawns=std_lawns(), paths=[], shrubs=[(0.45, 1.3), (0.5, 2.5), (1.1, 3.6), (3.4, 3.55)], frame=f, seed=10)
    L = Layer()
    a0, b0, a1, b1, h = 1.45, 1.45, 2.55, 2.5, 20
    box(L, a0, b0, a1, b1, 0, h, 'pave', 'lsteel', 'white')
    win_left(L, 1.6, 2.4, b1, 3, 11, 'teal')                          # the counter window
    win_left(L, 1.66, 2.34, b1, 4, 10, 'butter')
    L.poly([P(1.55, b1 + 0.12, 5), P(2.45, b1 + 0.12, 5), P(2.45, b1 + 0.12, 4), P(1.55, b1 + 0.12, 4)], 'wood')
    for k in range(9):                                                 # striped awning, sloping out
        aa = a0 + k * (a1 - a0) / 9
        ab = a0 + (k + 1) * (a1 - a0) / 9
        col = 'pink' if k % 2 == 0 else 'white'
        L.poly([P(aa, b1, h - 2), P(ab, b1, h - 2), P(ab, b1 + 0.32, h - 6), P(aa, b1 + 0.32, h - 6)], col)
    L.poly([P(a0, b1 + 0.32, h - 6), P(a1, b1 + 0.32, h - 6), P(a1, b1 + 0.32, h - 7), P(a0, b1 + 0.32, h - 7)], 'rose')
    for (za, zb, col) in ((h + 1, h + 7, 'outline'),):                 # the sign on the roof, cycling
        L.poly([P(1.6, 1.9, zb), P(2.4, 1.9, zb), P(2.4, 1.9, za), P(1.6, 1.9, za)], col)
    for k in range(5):
        on = (k + f) % 5 < 3
        L.poly([P(1.68 + k * 0.14, 1.9, h + 5), P(1.76 + k * 0.14, 1.9, h + 5), P(1.76 + k * 0.14, 1.9, h + 3), P(1.68 + k * 0.14, 1.9, h + 3)], 'neon' if on else 'rose')
    L.outlined()
    S = Layer()
    sx, sy = P(2.35, 1.7, h + 1)
    steam(S, sx, sy, f, height=9)
    S.px(sx, sy + 1, 'wood'); S.px(sx + 1, sy + 1, 'wood')
    U = Layer()                                                        # a table under a striped umbrella
    ux, uy = P(3.15, 2.95)
    ux, uy = round(ux), round(uy)
    U.ellipse(ux, uy - 5, 5, 2.5, 'white')                             # table top
    U.line(ux, uy - 4, ux, uy, 'wood')
    U.line(ux, uy - 5, ux, uy - 15, 'wood')                            # umbrella pole
    for dy in range(0, 5):                                             # a low cone, pink and white panels
        half = 1 + dy * 2.2
        for dx in range(-round(half), round(half) + 1):
            seg = int((dx + 11) // 3.5) % 2
            col = ('pink' if seg == 0 else 'white') if dx < half * 0.4 else ('rose' if seg == 0 else 'lsteel')
            U.px(ux + dx, uy - 18 + dy, col)
    for dx in range(-9, 10, 2):                                        # scalloped rim
        U.px(ux + dx, uy - 13, 'rose' if dx > 3 else 'pink')
    U.outlined()
    return composite([g, L, S, U])


# ============ 11. Home (small): just a home ============
def home(f):
    g = ground(lawns=[(0, 2.9, 4, 4), (0, 0, 1.1, 2.9), (3.1, 0, 4, 1.1)], paths=[(1.9, 2.9, 2.3, 4)], shrubs=[(0.5, 1.1), (0.55, 2.4), (1.3, 3.5), (3.0, 3.5), (3.6, 0.6)], frame=f, seed=11)
    for (a, b) in ((0.45, 1.7), (0.6, 1.95), (0.35, 2.2), (2.8, 3.3), (3.3, 3.4), (3.55, 3.2)):
        x, y = P(a, b)
        g.px(x, y, 'pink'); g.px(x + 1, y - 1, 'white')
    L = Layer()
    a0, b0, a1, b1, h = 1.35, 1.4, 2.7, 2.65, 17
    box(L, a0, b0, a1, b1, 0, h, 'pave', 'lsteel', 'white')
    L.poly([P(a0, b1, 3), P(a1, b1, 3), P(a1, b1, 0), P(a0, b1, 0)], 'peach')
    L.poly([P(a1, b1, 3), P(a1, b0, 3), P(a1, b0, 0), P(a1, b1, 0)], 'coral')
    win_left(L, 1.95, 2.25, b1, 0, 11, 'wood')                       # door
    L.px(*P(2.19, b1, 5), 'butter')
    for i, aa in enumerate((1.5, 2.38)):                              # windows with warm light
        on = (i + f // 3) % 3 != 2
        win_left(L, aa, aa + 0.22, b1, 6, 12, 'butter' if on else 'teal', frame_col='wood')
    win_right(L, 1.75, 2.05, a1, 6, 12, 'butter' if f % 4 else 'teal', frame_col='wood')
    # a rounded roof: a barrel vault running along a
    bc, rb, zr = (b0 + b1) / 2, (b1 - b0) / 2 + 0.1, 9
    zf = lambda b: h + zr * math.sqrt(max(0.0, 1 - ((b - bc) / rb) ** 2))
    steps = 40
    for i in range(steps):
        ba, bb = (b0 - 0.1) + (rb * 2) * i / steps, (b0 - 0.1) + (rb * 2) * (i + 1) / steps
        slope = zf(bb) - zf(ba)
        col = 'white' if abs(slope) < 0.2 else ('coral' if slope > 0 else 'peach')
        L.poly([P(a0 - 0.08, ba, zf(ba)), P(a1 + 0.08, ba, zf(ba)), P(a1 + 0.08, bb, zf(bb)), P(a0 - 0.08, bb, zf(bb))], col)
    gable = [P(a1 + 0.08, b0 - 0.1, h)] + [P(a1 + 0.08, (b0 - 0.1) + (rb * 2) * i / 30, zf((b0 - 0.1) + (rb * 2) * i / 30)) for i in range(31)] + [P(a1 + 0.08, b1 + 0.1, h)]
    L.poly(gable, 'coral')
    L.outlined()
    C = Layer()                                                        # a chimney vent with a curl of steam
    box(C, 1.75, 1.65, 2.0, 1.9, h + 6, h + 13, 'lsteel', 'slab', 'steel')
    cx, cy = P(1.87, 1.77, h + 14)
    steam(C, cx, cy, f, height=10)
    C.outlined()
    return composite([g, L, C])


BUILDINGS = [
    ('city-hall', 'City hall', 'Medium', city_hall, [420, 160, 130, 130, 260, 160, 130, 130]),
    ('habitat-pod', 'Habitat pod', 'Small', habitat_pod, [160] * N),
    ('research-lab', 'Research lab', 'Medium', research_lab, [150] * N),
    ('data-tower', 'Data tower', 'Small, tall', data_tower, [110] * N),
    ('hangar', 'Hangar', 'Medium', hangar, [170] * N),
    ('greenhouse-dome', 'Greenhouse dome', 'Medium', greenhouse, [170] * N),
    ('power-station', 'Power station', 'Medium', power_station, [140] * N),
    ('comms-spire', 'Comms spire', 'Small, the tallest', comms_spire, [180] * N),
    ('workshop', 'Workshop', 'Medium', workshop, [170] * N),
    ('kiosk', 'Kiosk', 'Small', kiosk, [180] * N),
    ('home', 'Home', 'Small', home, [190] * N),
]
