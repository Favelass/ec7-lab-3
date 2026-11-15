"""HSV marker detection: closing, shape filter and ordered band reader."""

from __future__ import annotations

import math

import cv2

import numpy as np

from harness import show


FOCAL_PX = 530.0

CYLINDER_HEIGHT_M = 201.5 / 1000


PATTERNS: dict[str, str | None] = {
    "sheet-1": "krk",
    "sheet-2": "kgk",
    "sheet-3": "krgk",
    "sheet-4": "kgrk",
    "sheet-5": "kwk",
    "sheet-6": "kwkwk",
    "sheet-7": "kwkwkwk",
    "sheet-8": "kwkwkwkwk",
    "sheet-9": "k",
}


def pixel_colour(hsv_pixel: np.ndarray) -> str:
    h, s, v = hsv_pixel
    if v < 90:
        return "k"
    if s > 90 and v > 60:
        if h < 12 or h > 168:
            return "r"
        if 40 < h < 90:
            return "g"
    return "w"


def read_bands(labels: list[str], min_run: int) -> str:
    out = []                 # the letters kept, one per band
    current = None           # the letter of the current run
    count = 0                # how many rows the current run has so far
    for label in labels + [None]:
        if label == current:
            count += 1
            continue
        if current is not None and count >= min_run and (not out or out[-1] != current):
            out.append(current)
        current, count = label, 1
    return "".join(out).strip("w")


CLOSE_HEIGHT_PX = 81


def detect_marker(image: np.ndarray) -> tuple[str, float | None, float | None, float]:

    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    s, v = hsv[..., 1], hsv[..., 2]

    ink = (v < 95) | ((s > 95) & (v > 55))

    mask = cv2.morphologyEx(ink.astype(np.uint8), cv2.MORPH_CLOSE,
                            np.ones((CLOSE_HEIGHT_PX, 3), np.uint8))
    show("marker-mask", mask * 255)

    contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    boxes = [cv2.boundingRect(c) for c in contours]

    boxes = [b for b in boxes if b[3] >= 24 and b[2] >= 8
             and 0.9 <= b[3] / b[2] <= 2.6]
    if not boxes:
        return "unknown", None, None, 0.0

    x, y, w, height = max(boxes, key=lambda b: b[3])

    half = max(1, w // 8)
    column = hsv[y:y + height, x + w // 2 - half: x + w // 2 + half + 1]
    labels = [pixel_colour(np.median(column[row], axis=0))
              for row in range(height)]
    word = read_bands(labels, max(3, height // 20))

    sheet = next((name for name, pattern in PATTERNS.items()
                  if pattern == word), None)
    if sheet is None:
        return "unknown", None, None, 0.0

    distance = FOCAL_PX * CYLINDER_HEIGHT_M / height

    offset = x + w / 2 - image.shape[1] / 2
    bearing = math.degrees(math.atan(offset / FOCAL_PX))

    ink_fraction = float(ink[y:y + height, x:x + w].mean())
    return sheet, distance, bearing, float(np.clip(0.40 + 0.9 * ink_fraction, 0, 1))
