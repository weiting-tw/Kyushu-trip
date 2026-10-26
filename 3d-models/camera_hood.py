"""MG 倒車鏡頭方形套罩：U 形套筒從後方套在鏡頭座外側，向外延伸一段頂蓋遮雨。

依實車量測：鏡頭座寬約 28.6 mm、外凸約 14 mm；鏡頭座高度先以 16 mm 估計。
結構：
- 兩側側壁夾住鏡頭座（內寬 = 鏡頭座寬 + 間隙），內側有防滑凸條，建議再加雙面膠
- 鏡頭面之外延伸 EXT，由頂板 + 兩側壁組成方形遮簷
- 遮簷前緣斜切：上緣伸最長、下緣較短，避免擋到廣角鏡頭下方視野
座標：鏡頭中心為原點，Y 朝上，Z 為鏡頭朝向，Z=0 為鏡頭面。
"""
import math
import sys

from manifold3d import Manifold

from camera_visor import to_trimesh

HOUSING_W = 28.6     # 鏡頭座寬 (mm)，卡尺實測
HOUSING_H = 16.0     # 鏡頭座高 (mm)，估計值，請實測
CLEAR = 0.3          # 單側間隙 (mm)
WALL = 1.5           # 側壁厚 (mm)
TOP = 1.5            # 頂板厚 (mm)
GRIP = 10.0          # 側壁套住鏡頭座的長度 (mm)，鏡頭座外凸 14 mm
EXT = 8.0            # 遮簷伸出鏡頭面的長度（上緣）(mm)
EXT_BOTTOM = 2.0     # 遮簷下緣伸出長度 (mm)
RIB = 0.3            # 內側防滑凸條高度 (mm)


def box(x0, x1, y0, y1, z0, z1):
    return Manifold.cube([x1 - x0, y1 - y0, z1 - z0]).translate([x0, y0, z0])


def build():
    wi = HOUSING_W / 2 + CLEAR
    wo = wi + WALL
    h = HOUSING_H / 2
    walls = box(-wo, -wi, -h, h + TOP, -GRIP, EXT) + box(wi, wo, -h, h + TOP, -GRIP, EXT)
    top = box(-wo, wo, h, h + TOP, 0, EXT)
    body = walls + top
    # 防滑凸條：兩側內壁各兩條直立凸條
    for z in (-7.0, -3.0):
        for x0, x1 in ((-wi, -wi + RIB), (wi - RIB, wi)):
            body = body + box(x0, x1, -h + 1, h - 1, z - 0.5, z + 0.5)
    # 前緣斜切：上緣伸 EXT、下緣伸 EXT_BOTTOM
    span = HOUSING_H + TOP
    cut = Manifold.cube([200, 200, 200]).translate([-100, 0, 0])
    ang = math.degrees(math.atan2(EXT - EXT_BOTTOM, span))
    cut = cut.translate([0, -100, 0]).rotate([ang, 0, 0]).translate([0, -h, EXT_BOTTOM])
    return body - cut


if __name__ == "__main__":
    out = sys.argv[1] if len(sys.argv) > 1 else "camera_hood.stl"
    solid = build()
    mesh = to_trimesh(solid)
    mesh.export(out)
    print(f"{out}: {len(mesh.faces)} tris, extents {mesh.extents.round(2)} mm, "
          f"manifold={solid.status().name}, volume={solid.volume():.1f} mm3")
