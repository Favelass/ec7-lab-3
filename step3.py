"""HSV sign detection: shape, arrow orientation and corrected apparent size."""

from __future__ import annotations

from step2 import *

import math
import cv2
import numpy as np


SIGN_DIAMETER_M = 70 / 1000

RED_OF_SHEET = 57 / 70
BLUE_OF_SHEET = 67.9 / 70


FILL_MIN = 0.72
FILL_MAX = 0.88

CIRCULARITY_MIN = 0.80


def shape_of(contour: np.ndarray, w: int, height: int) -> tuple[float, float]:
    """How much of its box the region fills, and its circularity."""
    area = cv2.contourArea(contour)
    perimeter = cv2.arcLength(contour, True)
    fill = area / max(1, w * height)

    circularity = 4 * math.pi * area / max(1.0, perimeter ** 2)
    return fill, circularity


def extract_arrow(contour: np.ndarray, mask: np.ndarray,
                                x: int, y: int, w: int, height: int) -> np.ndarray:
    filled = np.zeros(mask.shape, np.uint8)
    cv2.drawContours(filled, [contour], -1, 1, cv2.FILLED)
    hole = filled & (1 - mask)
    patch = hole[y:y + height, x:x + w]
    # Keep the largest white component; JPEG speckles must not set the axis.
    n, labels, stats, _ = cv2.connectedComponentsWithStats(patch, connectivity=8)
    if n <= 1:
        return patch.astype(bool)
    largest = 1 + int(np.argmax(stats[1:, cv2.CC_STAT_AREA]))
    return labels == largest


def arrow_direction(white: np.ndarray) -> str | None:
    """"up", "down", "left" or "right", or None if there is no arrow.

    The head of the arrow is its wide part; the shaft is the thin part.
    """
    show("sign-arrow", white.astype(np.uint8) * 255)
    rows, cols = white.sum(axis=1), white.sum(axis=0)
    if white.sum() < 20:
        return None
    vertical = np.count_nonzero(rows > 0) >= np.count_nonzero(cols > 0)
    profile = rows if vertical else cols
    live = np.where(profile > 0)[0]
    if len(live) < 5:
        return None
    head = live[profile[live] >= 0.80 * profile[live].max()]
    middle = (live[0] + live[-1]) / 2


    if vertical:
        return "up" if head.mean() < middle else "down"
    return "left" if head.mean() < middle else "right"


def detect_free(hsv: np.ndarray, image: np.ndarray) -> tuple[str, float | None, float | None, float]:
    """The end of restrictions: pale, bright, with a dark bar across it."""
    s, v = hsv[..., 1], hsv[..., 2]

    pale = ((s < 70) & (v > 170)).astype(np.uint8)
    pale = cv2.morphologyEx(pale, cv2.MORPH_CLOSE, np.ones((7, 7), np.uint8))
    contours, _ = cv2.findContours(pale, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:3]:
        x, y, w, height = cv2.boundingRect(contour)
        if height < 20 or w < 16 or not 0.70 <= w / height <= 1.45:
            continue
        patch = v[y:y + height, x:x + w]
        dark = patch < 110


        if not 0.05 <= dark.mean() <= 0.32:
            continue
        ys, xs = np.nonzero(dark)
        if len(xs) < 12 or np.std(xs) < 0.10 * w:    # a bar, not a corner
            continue

        distance = FOCAL_PX * SIGN_DIAMETER_M / height

        offset = x + w / 2 - image.shape[1] / 2
        bearing = math.degrees(math.atan(offset / FOCAL_PX))
        return "sign-free", distance, bearing, 0.58
    return "unknown", None, None, 0.0


def detect_sign(image: np.ndarray) -> tuple[str, float | None, float | None, float]:

    hsv = cv2.cvtColor(image, cv2.COLOR_RGB2HSV)
    h, s, v = hsv[..., 0], hsv[..., 1], hsv[..., 2]

    red = ((h < 10) | (h > 170)) & (s > 100) & (v > 55)
    blue = (h > 95) & (h < 130) & (s > 100) & (v > 40)

    for name, mask in (("red", red), ("blue", blue)):
        colour_mask = mask.astype(np.uint8)
        mask = cv2.morphologyEx(colour_mask, cv2.MORPH_CLOSE,
                                np.ones((5, 5), np.uint8))
        show(f"sign-{name}", mask * 255)
        contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
        for contour in sorted(contours, key=cv2.contourArea, reverse=True)[:3]:
            x, y, w, height = cv2.boundingRect(contour)
            if height < 18 or w < 14 or not 0.62 <= w / height <= 1.55:
                continue
            fill, circularity = shape_of(contour, w, height)


            if not FILL_MIN <= fill <= FILL_MAX or circularity < CIRCULARITY_MIN:
                continue

            seen = SIGN_DIAMETER_M * (RED_OF_SHEET if name == "red" else BLUE_OF_SHEET)

            distance = FOCAL_PX * seen / height

            offset = x + w / 2 - image.shape[1] / 2
            bearing = math.degrees(math.atan(offset / FOCAL_PX))

            if name == "red":
                return "sign-stop", distance, bearing, float(np.clip(circularity, 0, 1))
            arrow = arrow_direction(extract_arrow(contour, colour_mask, x, y, w, height))
            if arrow is None:
                continue
            return f"sign-{arrow}", distance, bearing, 0.70

    return detect_free(hsv, image)
