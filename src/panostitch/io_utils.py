"""
io_utils.py
-----------
Image loading, saving, resizing and validation helpers shared by every
stage of the pipeline. Kept separate from the CV logic so the algorithm
modules stay focused and testable in isolation.
"""

from __future__ import annotations

import logging
import os
from pathlib import Path
from typing import List, Tuple

import cv2
import numpy as np

logger = logging.getLogger("panostitch")

SUPPORTED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".tiff"}


def list_images(folder: str) -> List[str]:
    """Return a sorted list of image file paths inside `folder`."""
    folder_path = Path(folder)
    if not folder_path.is_dir():
        raise FileNotFoundError(f"Input folder does not exist: {folder}")

    paths = sorted(
        str(p) for p in folder_path.iterdir()
        if p.suffix.lower() in SUPPORTED_EXTENSIONS
    )
    if len(paths) < 2:
        raise ValueError(
            f"Need at least 2 images to stitch a panorama, found {len(paths)} in {folder}"
        )
    return paths


def load_image(path: str) -> np.ndarray:
    """Load an image from disk in BGR format, raising a clear error if it fails."""
    img = cv2.imread(path, cv2.IMREAD_COLOR)
    if img is None:
        raise IOError(f"Could not read image (corrupt or unsupported format): {path}")
    return img


def resize_max_dim(img: np.ndarray, max_dim: int) -> Tuple[np.ndarray, float]:
    """
    Downscale `img` so its longer side is at most `max_dim` pixels.

    Returns the resized image and the scale factor applied (1.0 if no
    resize was needed). Working on downscaled images is the project's main
    performance / resource-efficiency measure for large photos.
    """
    h, w = img.shape[:2]
    longer_side = max(h, w)
    if longer_side <= max_dim:
        return img, 1.0

    scale = max_dim / float(longer_side)
    resized = cv2.resize(img, (int(w * scale), int(h * scale)), interpolation=cv2.INTER_AREA)
    return resized, scale


def save_image(img: np.ndarray, path: str) -> None:
    """Save an image, creating parent directories if needed."""
    out_dir = os.path.dirname(path)
    if out_dir:
        os.makedirs(out_dir, exist_ok=True)
    ok = cv2.imwrite(path, img)
    if not ok:
        raise IOError(f"Failed to write image to {path}")
    logger.info("Saved image -> %s", path)