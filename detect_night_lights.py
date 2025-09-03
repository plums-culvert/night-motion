#!/usr/bin/env python3
"""
Night light detector — config-driven (no CLI flags). Edit CONFIG below.
"""
import json
from pathlib import Path

import cv2
import numpy as np

# ---------- CONFIG ----------
CONFIG = {
    "INPUT_DIR": "./frames",
    "OUT_ANN": "./annotated",
    "OUT_CROP": "./cropped",
    "REPORT": "./detection_report.json",
    "EXT": "png",

    "MIN_AREA": 12,
    "MAX_AREA": 20000,
    "MIN_BRIGHTNESS": 12,
    "KERNEL_SIZE": 9,
    "DILATE_ITER": 0,
    "THRESHOLD": "fixed",
    "FIXED_THRESH": 20,
    "INVERT": False,
    "ASPECT_RATIO_MAX": 10.0,
    "PADDING": 30,
    "REMOVE_HOT_PIXELS": True,

    "GAMMA": 1.4,
    "CLAHE": False,

    "BOX_GROW": 20,          # enlarge each bbox (pixels per side)
    "RECT_THICKNESS": 3     # thicker red rectangle
}
# ---------------------------

def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)

def apply_gamma(img_gray: np.ndarray, gamma: float) -> np.ndarray:
    if gamma <= 0 or abs(gamma - 1.0) < 1e-3:
        return img_gray
    inv = 1.0 / gamma
    lut = np.array([((i / 255.0) ** inv) * 255 for i in range(256)]).astype("uint8")
    return cv2.LUT(img_gray, lut)

def detect_points(img_bgr: np.ndarray, cfg: dict):
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)

    gray = apply_gamma(gray, cfg["GAMMA"])

    if cfg["CLAHE"]:
        clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
        gray = clahe.apply(gray)

    gray_blur = cv2.GaussianBlur(gray, (0, 0), sigmaX=1.0, sigmaY=1.0)

    k = max(3, int(cfg["KERNEL_SIZE"]) | 1)
    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (k, k))
    tophat = cv2.morphologyEx(gray_blur, cv2.MORPH_TOPHAT, kernel)

    mode = cfg["THRESHOLD"].lower()
    if mode == "adaptive":
        block = max(11, (k * 3) | 1)
        th = cv2.adaptiveThreshold(
            tophat, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY, block, 2
        )
    elif mode == "otsu":
        _, th = cv2.threshold(tophat, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    else:
        v = max(1, min(254, int(cfg["FIXED_THRESH"])))
        _, th = cv2.threshold(tophat, v, 255, cv2.THRESH_BINARY)

    if cfg["INVERT"]:
        th = cv2.bitwise_not(th)

    if cfg["REMOVE_HOT_PIXELS"]:
        th = cv2.medianBlur(th, 3)

    if int(cfg["DILATE_ITER"]) > 0:
        kernel2 = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
        th = cv2.dilate(th, kernel2, iterations=int(cfg["DILATE_ITER"]))

    cnts, _ = cv2.findContours(th, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)

    boxes = []
    for c in cnts:
        x, y, bw, bh = cv2.boundingRect(c)
        area = bw * bh
        if area < int(cfg["MIN_AREA"]) or area > int(cfg["MAX_AREA"]):
            continue
        ar = max(bw, bh) / max(1, min(bw, bh))
        if ar > float(cfg["ASPECT_RATIO_MAX"]):
            continue
        roi = gray[y : y + bh, x : x + bw]
        if int(np.mean(roi)) < int(cfg["MIN_BRIGHTNESS"]):
            continue
        boxes.append((x, y, bw, bh))

    boxes.sort(key=lambda b: (b[1], b[0]))
    return boxes

def draw_and_crop(img_bgr, boxes, pad, grow, thickness):
    H, W = img_bgr.shape[:2]
    annotated = img_bgr.copy()

    grown_boxes = []
    for (x, y, w, h) in boxes:
        x1 = max(0, x - grow)
        y1 = max(0, y - grow)
        x2 = min(W, x + w + grow)
        y2 = min(H, y + h + grow)
        grown_boxes.append((x1, y1, x2 - x1, y2 - y1))
        cv2.rectangle(annotated, (x1, y1), (x2, y2), (0, 0, 255), thickness)

    if grown_boxes:
        xs  = [b[0] for b in grown_boxes]
        ys  = [b[1] for b in grown_boxes]
        x2s = [b[0] + b[2] for b in grown_boxes]
        y2s = [b[1] + b[3] for b in grown_boxes]
        cx1 = max(0, min(xs) - pad)
        cy1 = max(0, min(ys) - pad)
        cx2 = min(W, max(x2s) + pad)
        cy2 = min(H, max(y2s) + pad)
        cropped = img_bgr[cy1:cy2, cx1:cx2]
        crop_box = (int(cx1), int(cy1), int(cx2 - cx1), int(cy2 - cy1))
    else:
        cropped = img_bgr.copy()
        crop_box = (0, 0, W, H)

    return annotated, cropped, crop_box

def process(cfg: dict):
    input_dir = Path(cfg["INPUT_DIR"])
    out_ann = Path(cfg["OUT_ANN"])
    out_crop = Path(cfg["OUT_CROP"])
    report_path = Path(cfg["REPORT"])
    ext = cfg["EXT"].lower().lstrip(".")

    out_ann.mkdir(parents=True, exist_ok=True)
    out_crop.mkdir(parents=True, exist_ok=True)

    results = []
    images = sorted(input_dir.glob(f"*.{ext}"))
    for img_path in images:
        img = cv2.imread(str(img_path), cv2.IMREAD_COLOR)
        if img is None:
            continue

        boxes = detect_points(img, cfg)
        annotated, cropped, crop_box = draw_and_crop(
            img, boxes,
            pad=int(cfg["PADDING"]),
            grow=int(cfg["BOX_GROW"]),
            thickness=int(cfg["RECT_THICKNESS"])
        )

        ann_name = img_path.stem + "_ann.png"
        crop_name = img_path.stem + "_crop.png"

        cv2.imwrite(str(out_ann / ann_name), annotated)
        cv2.imwrite(str(out_crop / crop_name), cropped)

        results.append({
            "file": img_path.name,
            "detections": len(boxes),
            "boxes": [{"x": int(x), "y": int(y), "w": int(w), "h": int(h)} for (x, y, w, h) in boxes],
            "crop_box": {"x": crop_box[0], "y": crop_box[1], "w": crop_box[2], "h": crop_box[3]},
            "annotated_out": ann_name,
            "cropped_out": crop_name,
        })

    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(results, f, indent=2)

if __name__ == "__main__":
    process(CONFIG)
