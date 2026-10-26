"""產生弧形飾條（碳纖紋護片）的 STL。

依照片標示尺寸：外側弦長 38 mm、內側弦長 26 mm、高度 14 mm。
以半圓弧建模：外半徑 19 mm、內緣半徑 13 mm（徑向深度 6 mm）。
截面為 L 形：外壁 + 頂部向內的翻邊。所有尺寸皆可在下方調整。
"""
import math
import struct
import sys

OUTER_CHORD = 38.0   # 外側弦長 (mm)
INNER_CHORD = 26.0   # 內側弦長 (mm)
HEIGHT = 14.0        # 高度 (mm)
WALL = 1.5           # 外壁厚度 (mm)
LIP = 1.5            # 頂部翻邊厚度 (mm)
ARC_DEG = 180.0      # 弧角 (度)
SEGMENTS = 120       # 弧的細分數

half = math.radians(ARC_DEG) / 2
R_OUT = OUTER_CHORD / 2 / math.sin(half)
R_IN = INNER_CHORD / 2 / math.sin(half)
R_WALL = R_OUT - WALL

# L 形截面 (r, z)，逆時針
PROFILE = [
    (R_OUT, 0.0),
    (R_OUT, HEIGHT),
    (R_IN, HEIGHT),
    (R_IN, HEIGHT - LIP),
    (R_WALL, HEIGHT - LIP),
    (R_WALL, 0.0),
]
# 端蓋三角化（拆成兩個矩形）
CAP_TRIS = [(0, 1, 4), (0, 4, 5), (1, 2, 3), (1, 3, 4)]


def point(r, z, a):
    return (r * math.cos(a), r * math.sin(a), z)


def build():
    tris = []
    a0 = -half + math.pi / 2  # 讓弧對稱於 Y 軸
    angles = [a0 + 2 * half * i / SEGMENTS for i in range(SEGMENTS + 1)]
    n = len(PROFILE)
    for i in range(SEGMENTS):
        a, b = angles[i], angles[i + 1]
        for j in range(n):
            p, q = PROFILE[j], PROFILE[(j + 1) % n]
            pa, qa = point(*p, a), point(*q, a)
            pb, qb = point(*p, b), point(*q, b)
            tris.append((pa, pb, qb))
            tris.append((pa, qb, qa))
    for idx, a, flip in ((0, angles[0], False), (1, angles[-1], True)):
        for t in CAP_TRIS:
            pts = [point(*PROFILE[k], a) for k in t]
            tris.append((pts[0], pts[2], pts[1]) if flip else tuple(pts))
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
        f.write(b"arc_trim".ljust(80, b"\0"))
        f.write(struct.pack("<I", len(tris)))
        for t in tris:
            f.write(struct.pack("<3f", *normal(t)))
            for v in t:
                f.write(struct.pack("<3f", *v))
            f.write(b"\0\0")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "arc_trim.stl"
    tris = build()
    write_stl(out, tris)
    print(f"{out}: {len(tris)} triangles")
