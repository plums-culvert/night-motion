#!/usr/bin/env python3
"""
Composite annotated frames to analyze motion vs. stationary lights.
Config-driven. Edit CONFIG and run.
"""
import json
from pathlib import Path

import cv2
import numpy as np

# ---------- CONFIG ----------
CONFIG = {
    "ANNOTATED_DIR": "./annotated",
    "REPORT_JSON": "./detection_report.json",
    "OUT_DIR": "./composite_out",

    "MAKE_MAX_PROJECTION": True,
    "MAKE_MEAN_STACK": True,
    "MAKE_DET_HEATMAP": True,

    "OUT_MAX": "composite_max.png",
    "OUT_MEAN": "composite_mean.png",
    "OUT_HEATMAP": "composite_heatmap.png",
    "OUT_OVERLAY": "composite_overlay.png",

    "OVERLAY_ALPHA": 0.6,
    "HEATMAP_COLORMAP": cv2.COLORMAP_JET,
}
# ---------------------------

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def load_annotated_images(ann_dir: Path):
    img_paths = sorted([p for p in ann_dir.iterdir() if p.suffix.lower() in (".png", ".jpg", ".jpeg")])
    imgs = []
    for p in img_paths:
        img = cv2.imread(str(p), cv2.IMREAD_COLOR)
        if img is None:
            continue
        imgs.append((p.name, img))
    return imgs

def max_projection(images):
    # images: list of np.ndarray BGR
    stack = np.stack(images, axis=0).astype(np.uint8)
    return np.max(stack, axis=0)

def mean_stack(images):
    stack = np.stack(images, axis=0).astype(np.float32)
    mean = np.mean(stack, axis=0)
    return np.clip(mean, 0, 255).astype(np.uint8)

def heatmap_from_boxes(report_path: Path, shape_hw):
    H, W = shape_hw
    acc = np.zeros((H, W), dtype=np.float32)
    with open(report_path, "r", encoding="utf-8") as f:
        data = json.load(f)
    for item in data:
        for b in item.get("boxes", []):
            x, y, w, h = int(b["x"]), int(b["y"]), int(b["w"]), int(b["h"])
            x2 = min(W, x + w)
            y2 = min(H, y + h)
            x1 = max(0, x)
            y1 = max(0, y)
            if x1 < x2 and y1 < y2:
                acc[y1:y2, x1:x2] += 1.0

    # --- higher-contrast normalization over non-zero counts ---
    
    # Change lo and hi values for better contrast in the heat map. 
    # For more dim objects, try 10/90. For Bright lights, try 1/99.
    
    nz = acc[acc > 0]
    if nz.size:
        lo = float(np.percentile(nz, 1.0))
        hi = float(np.percentile(nz, 99.0))
        if hi <= lo:
            hi = lo + 1e-6
        acc_clip = np.clip(acc, lo, hi)
        acc_norm01 = (acc_clip - lo) / (hi - lo)
        acc_norm = (np.sqrt(acc_norm01) * 255.0)
    else:
        acc_norm = acc

    acc_uint8 = np.clip(acc_norm, 0, 255).astype(np.uint8)
    acc_uint8 = cv2.medianBlur(acc_uint8, 3)  # suppress salt noise
    return acc_uint8

def colorize_heatmap(gray_heat, colormap):
    return cv2.applyColorMap(gray_heat, colormap)

def overlay_heatmap(base_bgr, heatmap_bgr, alpha: float):
    # correct alpha blend: alpha * heat + (1 - alpha) * base
    base = base_bgr.astype(np.float32)
    heat = heatmap_bgr.astype(np.float32)
    out = alpha * heat + (1.0 - alpha) * base
    return np.clip(out, 0, 255).astype(np.uint8)

def main():
    cfg = CONFIG
    ann_dir = Path(cfg["ANNOTATED_DIR"])
    out_dir = Path(cfg["OUT_DIR"])
    ensure_dir(out_dir)

    annotated = load_annotated_images(ann_dir)
    if not annotated:
        print("No annotated images found.")
        return

    names, imgs = zip(*annotated)
    H, W = imgs[0].shape[:2]

    if cfg["MAKE_MAX_PROJECTION"]:
        comp_max = max_projection(list(imgs))
        cv2.imwrite(str(out_dir / cfg["OUT_MAX"]), comp_max)

    if cfg["MAKE_MEAN_STACK"]:
        comp_mean = mean_stack(list(imgs))
        cv2.imwrite(str(out_dir / cfg["OUT_MEAN"]), comp_mean)

    if cfg["MAKE_DET_HEATMAP"]:
        heat_gray = heatmap_from_boxes(Path(cfg["REPORT_JSON"]), (H, W))
        heat_bgr = colorize_heatmap(heat_gray, cfg["HEATMAP_COLORMAP"])
        cv2.imwrite(str(out_dir / cfg["OUT_HEATMAP"]), heat_bgr)

        base = comp_mean if cfg["MAKE_MEAN_STACK"] else imgs[0]
        overlay = overlay_heatmap(base, heat_bgr, float(cfg["OVERLAY_ALPHA"]))
        cv2.imwrite(str(out_dir / cfg["OUT_OVERLAY"]), overlay)

if __name__ == "__main__":
    main()
