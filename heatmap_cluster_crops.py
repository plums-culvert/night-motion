#!/usr/bin/env python3
"""
Cluster crops from composite heatmap.
Config-driven. Edit CONFIG and run: python3 heatmap_cluster_crops.py
"""
from pathlib import Path

import cv2
import numpy as np

# -------- CONFIG --------
CONFIG = {
    "HEATMAP_PATH": "./composite_out/composite_heatmap.png",  # input heatmap (color)
    "OUT_DIR": "./composite_out/crops",                       # where to write crops
    "DEBUG_OVERLAY": "./composite_out/heatmap_boxes.png",     # boxes drawn on heatmap

    # Thresholding: keep strongest pixels
    "MODE": "percentile",     # "percentile" | "otsu" | "fixed"
    "PERCENTILE": 92.0,       # keep pixels >= this percentile (0-100)
    "FIXED_THRESH": 30,       # used if MODE = "fixed" on 0..255 gray

    # Morphology
    "BLUR": 3,                # Gaussian blur kernel (odd). 0 disables.
    "OPEN_SIZE": 3,           # morphology open to remove specks (0 disables)
    "CLOSE_SIZE": 5,          # morphology close to fill gaps (0 disables)

    # Cluster filtering
    "MIN_AREA": 80,           # reject tiny blobs (pixels)
    "MAX_AREA": 10_000_000,   # keep very large by default
    "PADDING": 24,            # px padding around each bbox

    # Output sizing
    "SCALE_FACTOR": 3.0,      # multiply each crop by this factor
    "MAX_OUTPUT_LONG": 1024,  # resize down if longer side exceeds this
}
# ------------------------

def to_gray(img_bgr):
    if img_bgr.ndim == 2:
        return img_bgr
    return cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

def threshold_heat(gray, cfg):
    mode = cfg["MODE"].lower()
    if cfg["BLUR"] and cfg["BLUR"] >= 3 and (cfg["BLUR"] % 2 == 1):
        gray = cv2.GaussianBlur(gray, (cfg["BLUR"], cfg["BLUR"]), 0)

    if mode == "otsu":
        _, th = cv2.threshold(gray, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    elif mode == "fixed":
        v = int(cfg["FIXED_THRESH"])
        _, th = cv2.threshold(gray, v, 255, cv2.THRESH_BINARY)
    else:
        # percentile
        p = np.percentile(gray, float(cfg["PERCENTILE"]))
        _, th = cv2.threshold(gray, int(p), 255, cv2.THRESH_BINARY)
    return th

def morph(mask, cfg):
    out = mask.copy()
    if cfg["OPEN_SIZE"] and cfg["OPEN_SIZE"] >= 3:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (cfg["OPEN_SIZE"], cfg["OPEN_SIZE"]))
        out = cv2.morphologyEx(out, cv2.MORPH_OPEN, k, iterations=1)
    if cfg["CLOSE_SIZE"] and cfg["CLOSE_SIZE"] >= 3:
        k = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (cfg["CLOSE_SIZE"], cfg["CLOSE_SIZE"]))
        out = cv2.morphologyEx(out, cv2.MORPH_CLOSE, k, iterations=1)
    return out

def grow_bbox(x, y, w, h, pad, W, H):
    x1 = max(0, x - pad)
    y1 = max(0, y - pad)
    x2 = min(W, x + w + pad)
    y2 = min(H, y + h + pad)
    return x1, y1, x2 - x1, y2 - y1

def resize_crop(img, scale, max_long):
    H, W = img.shape[:2]
    # scale up
    up = cv2.resize(img, (int(W*scale), int(H*scale)), interpolation=cv2.INTER_CUBIC)
    h, w = up.shape[:2]
    # limit maximum long side
    long = max(h, w)
    if long > max_long:
        if h >= w:
            nh, nw = max_long, int(w * (max_long / h))
        else:
            nw, nh = max_long, int(h * (max_long / w))
        up = cv2.resize(up, (nw, nh), interpolation=cv2.INTER_AREA)
    return up

def main():
    cfg = CONFIG
    heat_path = Path(cfg["HEATMAP_PATH"])
    out_dir = Path(cfg["OUT_DIR"])
    out_dir.mkdir(parents=True, exist_ok=True)

    heat_bgr = cv2.imread(str(heat_path), cv2.IMREAD_COLOR)
    if heat_bgr is None:
        raise SystemExit(f"Cannot read {heat_path}")

    H, W = heat_bgr.shape[:2]
    gray = to_gray(heat_bgr)

    # 1) Threshold + morph
    mask = threshold_heat(gray, cfg)
    mask = morph(mask, cfg)

    # 2) Connected components (contours)
    cnts, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    # 3) Filter and crop
    debug = heat_bgr.copy()
    crops = 0
    idx = 1
    for c in cnts:
        x, y, w, h = cv2.boundingRect(c)
        area = w * h
        if area < cfg["MIN_AREA"] or area > cfg["MAX_AREA"]:
            continue
        gx, gy, gw, gh = grow_bbox(x, y, w, h, cfg["PADDING"], W, H)
        cv2.rectangle(debug, (gx, gy), (gx+gw, gy+gh), (0, 0, 255), 2)
        crop = heat_bgr[gy:gy+gh, gx:gx+gw]
        crop = resize_crop(crop, cfg["SCALE_FACTOR"], cfg["MAX_OUTPUT_LONG"])
        out_name = out_dir / f"cluster_{idx:03d}.png"
        cv2.imwrite(str(out_name), crop)
        idx += 1
        crops += 1

    cv2.imwrite(str(Path(cfg["DEBUG_OVERLAY"])), debug)
    print(f"Saved {crops} crops to {out_dir} and overlay to {cfg['DEBUG_OVERLAY']}")

if __name__ == "__main__":
    main()
