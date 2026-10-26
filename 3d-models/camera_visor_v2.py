"""倒車鏡頭遮雨眉 v2：依安裝照與 Meshy 重建結果修正外形的參數化 STL。

和 v1（camera_visor.py）的差異：
- 前緣不再大幅內縮：Meshy 量到殼半徑前後幾乎一樣，只保留輕微收口
- 前緣斜切：拱頂外伸最多（14 mm），兩端貼近車身（像眼皮）
- 拱角略大於 180°，兩端垂到鏡頭中心以下，雨水沿末端滴落
- 後緣為 Z=0 平面，並往內加一圈貼合腳（45° 倒角免支撐），貼膠面寬 THICK + FOOT_W
座標同 v1：Z 軸為鏡頭軸，Z=0 為車身貼合面，拱頂朝 +Y。
"""
import math
import sys

from camera_visor import write_stl

BACK_CHORD = 38.0    # 後緣外側最寬處 (mm)
FRONT_TAPER = 1.5    # 前緣半徑比後緣小多少 (mm)
DEPTH_APEX = 14.0    # 拱頂外伸深度 (mm)
DEPTH_END = 8.0      # 兩端外伸深度 (mm)
THICK = 1.6          # 殼厚 (mm)
FOOT_W = 4.0         # 後緣往內加寬的貼合腳寬度 (mm)，貼膠面寬 = THICK + FOOT_W
FOOT_T = 1.2         # 貼合腳垂直段高度 (mm)，之上以 45° 倒角接回殼（免支撐）
BULGE = 1.5          # 殼面向外凸起量 (mm)
ARC_DEG = 196.0      # 拱的角度 (度)
ARC_SEG = 160        # 拱方向細分
PROF_SEG = 24        # 截面方向細分

half = math.radians(ARC_DEG) / 2
R_BACK = BACK_CHORD / 2


def depth(phi):
    """phi 為離拱頂的角度，回傳該處外伸深度。"""
    return DEPTH_END + (DEPTH_APEX - DEPTH_END) * math.cos(phi / half * math.pi / 2)


def profile(phi):
    """某角度的截面 (r, z)：外表面由後到前，再接內表面由前到後。"""
    d = depth(phi)
    z1 = FOOT_T + FOOT_W  # 倒角結束高度
    zs = [FOOT_T * i / 2 for i in range(2)]
    zs += [FOOT_T + FOOT_W * i / 8 for i in range(8)]
    zs += [z1 + (d - z1) * i / PROF_SEG for i in range(PROF_SEG + 1)]
    outer, inner = [], []
    for z in zs:
        s = z / d
        r = R_BACK - FRONT_TAPER * s + BULGE * math.sin(math.pi * s)
        foot = FOOT_W - max(0.0, min(z - FOOT_T, FOOT_W))
        outer.append((r, z))
        inner.append((r - THICK - foot, z))
    return outer, inner


def point(r, z, a):
    return (r * math.cos(a), r * math.sin(a), z)


def build():
    angles = [math.pi / 2 - half + 2 * half * i / ARC_SEG for i in range(ARC_SEG + 1)]
    rings = []
    for a in angles:
        outer, inner = profile(a - math.pi / 2)
        rings.append([point(r, z, a) for r, z in outer + inner[::-1]])
    m = len(rings[0])
    n = m // 2
    tris = []
    for ra, rb in zip(rings, rings[1:]):
        for j in range(m):
            pa, qa = ra[j], ra[(j + 1) % m]
            pb, qb = rb[j], rb[(j + 1) % m]
            tris.append((pa, pb, qb))
            tris.append((pa, qb, qa))
    # 端蓋：外/內曲線之間的細長帶
    for ring, flip in ((rings[0], False), (rings[-1], True)):
        for i in range(n - 1):
            o0, o1 = ring[i], ring[i + 1]
            i0, i1 = ring[m - 1 - i], ring[m - 2 - i]
            for t in ((o0, o1, i1), (o0, i1, i0)):
                tris.append((t[0], t[2], t[1]) if flip else t)
    return tris


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "camera_visor_v2.stl"
    tris = build()
    write_stl(out, tris)
    print(f"{out}: {len(tris)} triangles")
