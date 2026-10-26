"""把 camera_visor.stl 渲染成預覽圖（需要 matplotlib）。"""
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
    v = a["v"].reshape(-1, 3, 3).astype(float)
    # 模型座標 (X, Y=上, Z=外伸) → 顯示座標 (X, -Z 朝觀者, Y 朝上)
    return v[..., [0, 2, 1]] * [1, -1, 1]


def shade(tris, base):
    n = np.cross(tris[:, 1] - tris[:, 0], tris[:, 2] - tris[:, 0])
    n /= np.linalg.norm(n, axis=1, keepdims=True) + 1e-12
    k = np.abs(n @ LIGHT) * 0.7 + 0.25
    return np.column_stack([k * base[0], k * base[1], k * base[2], np.ones_like(k)])


def disc(r, y, seg=64):
    t = np.linspace(0, 2 * np.pi, seg + 1)
    c = np.stack([r * np.cos(t), np.full_like(t, y), r * np.sin(t)], 1)
    return [np.array([[0, y, 0], c[i], c[i + 1]]) for i in range(seg)]


def scene(ax, visor, with_car):
    if with_car:
        plate = np.array([[[-30, 0.01, -15], [30, 0.01, -15], [30, 0.01, 30]],
                          [[-30, 0.01, -15], [30, 0.01, 30], [-30, 0.01, 30]]])
        ax.add_collection3d(Poly3DCollection(plate, facecolors=(0.93, 0.93, 0.95, 1), edgecolor="none"))
        ring = np.array(disc(9, -0.5))
        ax.add_collection3d(Poly3DCollection(ring, facecolors=(0.75, 0.77, 0.8, 1), edgecolor="none"))
        lens = np.array(disc(5.5, -1.0))
        ax.add_collection3d(Poly3DCollection(lens, facecolors=(0.1, 0.1, 0.15, 1), edgecolor="none"))
    ax.add_collection3d(Poly3DCollection(visor, facecolors=shade(visor, (0.32, 0.34, 0.38)), edgecolor="none"))
    ax.set_xlim(-22, 22); ax.set_ylim(-30, 14); ax.set_zlim(-14, 30)
    ax.set_box_aspect((1, 1, 1))
    ax.set_axis_off()


def main(stl, out):
    visor = load(stl)
    views = [
        (15, -70, True, "安裝示意（鏡頭上方）"),
        (0, -90, True, "正視圖"),
        (25, -130, False, "等角視圖"),
        (0, 0, False, "側視圖（左：車身，右：外伸 14 mm）"),
    ]
    fig = plt.figure(figsize=(12, 11), facecolor="white")
    for i, (el, az, car, title) in enumerate(views):
        ax = fig.add_subplot(2, 2, i + 1, projection="3d")
        scene(ax, visor, car)
        ax.view_init(el, az)
        ax.set_title(title, fontsize=13)
    fig.suptitle("倒車鏡頭遮雨眉 — 後緣弦 38 mm / 前緣弦 26 mm / 外伸 14 mm", fontsize=15)
    plt.tight_layout()
    plt.savefig(out, dpi=110)


if __name__ == "__main__":
    main(sys.argv[1] if len(sys.argv) > 1 else "camera_visor.stl",
         sys.argv[2] if len(sys.argv) > 2 else "camera_visor_preview.png")
