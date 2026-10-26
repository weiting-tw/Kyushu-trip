"""MG 倒車鏡頭遮雨眉（貼在鏡頭座後表面、罩住鏡頭上半部）。

依實車量測：鏡頭座寬約 28.6 mm、鏡頭座外凸約 14 mm、鏡頭外圈直徑約 13.5 mm。
造型：扁橢圓拱殼，後緣黏貼在鏡頭座的鏡頭面上，向後外伸並微微外擴，
避免進入廣角鏡頭視野；後緣有一圈向內的貼合邊增加黏膠面積。
座標：鏡頭中心為原點，Z 為鏡頭朝向（外伸方向），Y 朝上，Z=0 為貼合面。
"""
import math
import struct
import sys

import numpy as np
import trimesh
from manifold3d import CrossSection, Manifold

HALF_W_BACK = 14.0   # 後緣外側半寬 (mm)，總寬 28 mm，不超過鏡頭座 28.6 mm
RISE_BACK = 9.0      # 後緣外側拱高，自鏡頭中心起算 (mm)
FLARE = 1.5          # 前緣相對後緣的外擴量 (mm)
DEPTH = 10.0         # 外伸深度 (mm)
THICK = 1.2          # 殼厚 (mm)
FLANGE_W = 1.8       # 後緣向內貼合邊寬 (mm)
FLANGE_T = 1.2       # 貼合邊厚 (mm)
DROP = 2.0           # 兩端延伸到鏡頭中心以下的距離 (mm)，當滴水尖
SEG = 160


def arch(a, b, t=0.0):
    """橢圓拱外輪廓往內偏移 t 的封閉區域（只取 y >= -DROP）。"""
    th = np.linspace(0, 2 * np.pi, SEG, endpoint=False)
    ell = CrossSection([np.column_stack([(a - t) * np.cos(th), (b - t) * np.sin(th)])])
    cut = CrossSection.square([4 * a, 4 * b]).translate([-2 * a, -DROP])
    return ell ^ cut


def shell(a, b):
    return arch(a, b) - arch(a, b, THICK)


def build():
    # 前緣外擴：以 scale_top 讓殼面從後到前平滑放大
    scale = [(HALF_W_BACK + FLARE) / HALF_W_BACK, (RISE_BACK + FLARE) / RISE_BACK]
    body = Manifold.extrude(shell(HALF_W_BACK, RISE_BACK), DEPTH, 1, 0.0, scale)
    flange = arch(HALF_W_BACK, RISE_BACK, THICK) - arch(HALF_W_BACK, RISE_BACK, THICK + FLANGE_W)
    return body + Manifold.extrude(flange, FLANGE_T)


def to_trimesh(m):
    mesh = m.to_mesh()
    t = trimesh.Trimesh(np.asarray(mesh.vert_properties)[:, :3], np.asarray(mesh.tri_verts))
    t.merge_vertices()
    return t


def write_stl(path, tris):
    """以三角形清單寫出 binary STL（camera_visor_v2.py 共用）。"""
    with open(path, "wb") as f:
        f.write(b"camera_visor".ljust(80, b"\0"))
        f.write(struct.pack("<I", len(tris)))
        for a, b, c in tris:
            u = [b[i] - a[i] for i in range(3)]
            v = [c[i] - a[i] for i in range(3)]
            n = [u[1] * v[2] - u[2] * v[1], u[2] * v[0] - u[0] * v[2], u[0] * v[1] - u[1] * v[0]]
            l = math.sqrt(sum(x * x for x in n)) or 1.0
            f.write(struct.pack("<3f", *(x / l for x in n)))
            for p in (a, b, c):
                f.write(struct.pack("<3f", *p))
            f.write(b"\0\0")


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "camera_visor.stl"
    solid = build()
    mesh = to_trimesh(solid)
    mesh.export(out)
    print(f"{out}: {len(mesh.faces)} tris, extents {mesh.extents.round(2)} mm, "
          f"manifold={solid.status().name}, volume={solid.volume():.1f} mm3")
