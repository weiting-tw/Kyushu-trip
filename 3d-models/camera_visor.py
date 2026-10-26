"""產生倒車鏡頭遮雨眉（碳纖紋護片）的 STL。

依商品圖標示尺寸：
- 貼車身的後緣：弦長 38 mm
- 外伸的前緣：弦長 26 mm
- 外伸深度（離車身）：14 mm
形狀為一段向外微凸的圓錐殼（像眼皮），以鏡頭軸為中心繞成半圓拱。
座標：Z 軸為鏡頭軸，Z=0 為車身貼合面，拱頂朝 +Y。
"""
import math
import struct
import sys

BACK_CHORD = 38.0    # 後緣（貼車身）弦長 (mm)
FRONT_CHORD = 26.0   # 前緣（外伸端）弦長 (mm)
DEPTH = 14.0         # 外伸深度 (mm)
THICK = 1.5          # 殼厚 (mm)
BULGE = 2.0          # 殼面向外凸起量 (mm)，0 為直圓錐
ARC_DEG = 180.0      # 拱的角度 (度)
ARC_SEG = 120        # 拱方向細分
PROF_SEG = 24        # 截面方向細分

half = math.radians(ARC_DEG) / 2
R_BACK = BACK_CHORD / 2 / math.sin(half)
R_FRONT = FRONT_CHORD / 2 / math.sin(half)


def outer_curve():
    """外表面截面曲線 (r, z)，由後緣到前緣，帶外凸弧度。"""
    dr, dz = R_FRONT - R_BACK, DEPTH
    L = math.hypot(dr, dz)
    nr, nz = dz / L, -dr / L  # 朝外法向
    pts = []
    for i in range(PROF_SEG + 1):
        s = i / PROF_SEG
        b = BULGE * math.sin(math.pi * s)
        pts.append((R_BACK + dr * s + nr * b, dz * s + nz * b))
    return pts


def inner_curve(outer):
    """沿法向往內偏移 THICK 得內表面，並把端點拉回 z=0 / z=DEPTH 平面。"""
    pts = []
    n = len(outer)
    for i, (r, z) in enumerate(outer):
        r0, z0 = outer[max(i - 1, 0)]
        r1, z1 = outer[min(i + 1, n - 1)]
        tr, tz = r1 - r0, z1 - z0
        L = math.hypot(tr, tz)
        nr, nz = tz / L, -tr / L
        ri, zi = r - nr * THICK, z - nz * THICK
        if i == 0 or i == n - 1:
            zt = 0.0 if i == 0 else DEPTH
            ri += (zt - zi) * (tr / tz)
            zi = zt
        pts.append((ri, zi))
    return pts


def point(r, z, a):
    return (r * math.cos(a), r * math.sin(a), z)


def build():
    outer = outer_curve()
    inner = inner_curve(outer)
    n = len(outer)
    profile = outer + inner[::-1]
    m = len(profile)
    a0 = math.pi / 2 - half
    angles = [a0 + 2 * half * i / ARC_SEG for i in range(ARC_SEG + 1)]
    tris = []
    for i in range(ARC_SEG):
        a, b = angles[i], angles[i + 1]
        for j in range(m):
            p, q = profile[j], profile[(j + 1) % m]
            pa, qa = point(*p, a), point(*q, a)
            pb, qb = point(*p, b), point(*q, b)
            tris.append((pa, pb, qb))
            tris.append((pa, qb, qa))
    # 端蓋：外/內曲線之間的細長帶
    for a, flip in ((angles[0], False), (angles[-1], True)):
        for i in range(n - 1):
            o0, o1 = point(*outer[i], a), point(*outer[i + 1], a)
            i0, i1 = point(*inner[i], a), point(*inner[i + 1], a)
            for t in ((o0, o1, i1), (o0, i1, i0)):
                tris.append((t[0], t[2], t[1]) if flip else t)
    return tris


def normal(t):
    (ax, ay, az), (bx, by, bz), (cx, cy, cz) = t
    ux, uy, uz = bx - ax, by - ay, bz - az
    vx, vy, vz = cx - ax, cy - ay, cz - az
    nx, ny, nz = uy * vz - uz * vy, uz * vx - ux * vz, ux * vy - uy * vx
    l = math.sqrt(nx * nx + ny * ny + nz * nz) or 1.0
    return nx / l, ny / l, nz / l


def write_stl(path, tris):
    with open(path, "wb") as f:
        f.write(b"camera_visor".ljust(80, b"\0"))
        f.write(struct.pack("<I", len(tris)))
        for t in tris:
            f.write(struct.pack("<3f", *normal(t)))
            for v in t:
                f.write(struct.pack("<3f", *v))
            f.write(b"\0\0")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "camera_visor.stl"
    tris = build()
    write_stl(out, tris)
    print(f"{out}: {len(tris)} triangles")
