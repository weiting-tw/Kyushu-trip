"""把 camera_visor.stl 渲染成預覽圖（需要 matplotlib），附鏡頭座示意。"""
import struct
import sys

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import numpy as np
from mpl_toolkits.mplot3d.art3d import Poly3DCollection

plt.rcParams["font.family"] = ["WenQuanYi Zen Hei", "DejaVu Sans"]
LIGHT = np.array([0.3, -0.8, 0.6]) / np.linalg.norm([0.3, -0.8, 0.6])


def load(path):
    d = open(path, "rb").read()
    a = np.frombuffer(d[84:], dtype=np.dtype([("n", "<3f4"), ("v", "<9f4"), ("x", "<u2")]))
    return to_view(a["v"].reshape(-1, 3, 3).astype(float))


def shade(tris, base):
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    k = np.abs(n @ LIGHT) * 0.7 + 0.25
    return np.column_stack([k * base[0], k * base[1], k * base[2], np.ones_like(k)])


def disc(r, seg=64, z=0.05):
    t = np.linspace(0, 2 * np.pi, seg + 1)
    c = np.stack([r * np.cos(t), r * np.sin(t), np.full_like(t, z)], 1)
    return np.array([[[0, 0, z], c[i], c[i + 1]] for i in range(seg)])


def box(x0, x1, y0, y1, z0, z1):
    p = np.array([[x, y, z] for x in (x0, x1) for y in (y0, y1) for z in (z0, z1)], float)
    quads = [(0, 1, 3, 2), (4, 6, 7, 5), (0, 4, 5, 1), (2, 3, 7, 6), (0, 2, 6, 4), (1, 5, 7, 3)]
    return np.array([t for q in quads for t in ((p[q[0]], p[q[1]], p[q[2]]), (p[q[0]], p[q[2]], p[q[3]]))])


def to_view(v):
    # 模型座標 (X, Y=上, Z=鏡頭朝向) → 顯示座標 (X, -Z 朝觀者, Y 朝上)
    return v[..., [0, 2, 1]] * [1, -1, 1]


def scene(ax, visor, with_car):
    if with_car:
        parts = [
            (box(-30, 30, 11, 14, -30, 4), (0.9, 0.9, 0.92)),       # 上方車身凸緣
            (box(-14.3, 14.3, -9, 11, -14, 0), (0.15, 0.15, 0.17)),  # 鏡頭座（量測 28.6 × 14 mm）
            (disc(6.75), (0.55, 0.57, 0.6)),                          # 鏡頭外圈
            (disc(4.0, z=0.1), (0.05, 0.05, 0.1)),                   # 鏡片
        ]
        for tris, col in parts:
            tv = to_view(tris)
            ax.add_collection3d(Poly3DCollection(tv, facecolors=shade(tv, col), edgecolor="none"))
    ax.add_collection3d(Poly3DCollection(visor, facecolors=shade(visor, (0.45, 0.47, 0.52)), edgecolor="none"))
    ax.set_xlim(-20, 20); ax.set_ylim(-25, 15); ax.set_zlim(-18, 22)
    ax.set_box_aspect((1, 1, 1))
    ax.set_axis_off()


def main(stl, out, heading="MG 倒車鏡頭遮雨眉 — 寬 28 mm（鏡頭座 28.6 mm）/ 外伸 10 mm"):
    visor = load(stl)
    views = [
        (20, -60, True, "安裝示意（黑色方塊為鏡頭座）"),
        (0, -90, True, "正視圖"),
        (25, -130, False, "等角視圖"),
        (0, 0, True, "側視圖（左側為鏡頭朝向）"),
    ]
    fig = plt.figure(figsize=(12, 11), facecolor="white")
    for i, (el, az, car, title) in enumerate(views):
        ax = fig.add_subplot(2, 2, i + 1, projection="3d")
        scene(ax, visor, car)
        ax.view_init(el, az)
        ax.set_title(title, fontsize=13)
    fig.suptitle(heading, fontsize=15)
    plt.tight_layout()
    plt.savefig(out, dpi=110)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "camera_visor.stl",
         sys.argv[2] if len(sys.argv) > 2 else "camera_visor_preview.png",
         *sys.argv[3:4])
