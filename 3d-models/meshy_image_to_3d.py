"""用 Meshy Image-to-3D API 從商品照產生遮雨眉模型，並縮放成實際尺寸輸出 STL。

用法：
    export MESHY_API_KEY=...        # 在雲端環境設定中加入，不要寫進程式
    pip install trimesh
    python3 meshy_image_to_3d.py ref/visor_dimensions.jpg camera_visor_meshy.stl

照片裡標示的外側弦長為 38 mm，因此輸出時把模型最長邊縮放成 TARGET_SPAN。
"""
import base64
import json
import mimetypes
import os
import sys
import time
import urllib.request

import trimesh

API = "https://api.meshy.ai/openapi/v1/image-to-3d"
TARGET_SPAN = 38.0  # mm，最長邊


def call(method, url, body=None):
    req = urllib.request.Request(url, method=method, data=json.dumps(body).encode() if body else None)
    req.add_header("Authorization", f"Bearer {os.environ['MESHY_API_KEY']}")
    req.add_header("Content-Type", "application/json")
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def main(image, out):
    mime = mimetypes.guess_type(image)[0] or "image/jpeg"
    data = base64.b64encode(open(image, "rb").read()).decode()
    task = call("POST", API, {
        "image_url": f"data:{mime};base64,{data}",
        "ai_model": "latest",
        "topology": "triangle",
        "target_polycount": 100000,
        "should_remesh": True,
        "should_texture": False,
    })["result"]
    print("task", task)
    while True:
        t = call("GET", f"{API}/{task}")
        print(t["status"], t.get("progress"))
        if t["status"] == "SUCCEEDED":
            break
        if t["status"] in ("FAILED", "CANCELED", "EXPIRED"):
            sys.exit(f"Meshy task {t['status']}: {t.get('task_error')}")
        time.sleep(10)

    glb = out.rsplit(".", 1)[0] + ".glb"
    urllib.request.urlretrieve(t["model_urls"]["glb"], glb)
    mesh = trimesh.load(glb, force="mesh")
    mesh.apply_translation(-mesh.bounds[0])
    mesh.apply_scale(TARGET_SPAN / max(mesh.extents))
    mesh.export(out)
    print(f"{out}: extents {mesh.extents.round(2)} mm, watertight={mesh.is_watertight}")


if __name__ == "__main__":
    main(sys.argv[1], sys.argv[2])
