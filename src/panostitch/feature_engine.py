"""
feature_engine.py
------------------
MODULE 1 - Feature Detection & Description

Responsible for turning a raw image into a set of keypoints and their
descriptors. This is the classical "local feature extraction" stage of
the computer vision pipeline (SIFT / ORB), and everything downstream
(matching, homography) depends on the quality of what happens here.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import List, Tuple

import cv2
import numpy as np

from .config import StitchConfig

logger = logging.getLogger("panostitch")


@dataclass
class FeatureSet:
    """Container for one image's detected keypoints and descriptors."""
    keypoints: List[cv2.KeyPoint]
    descriptors: np.ndarray
    image_shape: Tuple[int, int]  # (height, width) of the image the features came from


class FeatureEngine:
    """
    Wraps OpenCV's feature detectors behind a single, swappable interface.

    Swapping `detector` in StitchConfig between "sift" and "orb" changes
    the algorithm without touching any other module - this is the
    maintainability / extensibility contract of the class.
    """

    def __init__(self, config: StitchConfig):
        self.config = config
        self._detector = self._build_detector(config)

    @staticmethod
    def _build_detector(config: StitchConfig):
        name = config.detector.lower()
        if name == "sift":
            return cv2.SIFT_create(nfeatures=config.max_features)
        if name == "orb":
            return cv2.ORB_create(nfeatures=config.max_features)
        raise ValueError(f"Unsupported detector '{config.detector}'. Use 'sift' or 'orb'.")

    def detect_and_describe(self, image: np.ndarray) -> FeatureSet:
        """Detect keypoints and compute descriptors for a single (grayscale-converted) image."""
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY) if image.ndim == 3 else image

        start = time.perf_counter()
        keypoints, descriptors = self._detector.detectAndCompute(gray, None)
        elapsed = time.perf_counter() - start

        if descriptors is None or len(keypoints) == 0:
            raise RuntimeError(
                "No keypoints detected in image - it may be blank, too low-contrast, "
                "or too small for the configured detector."
            )

        logger.info(
            "Feature detection (%s): %d keypoints in %.3fs",
            self.config.detector.upper(), len(keypoints), elapsed,
        )
        return FeatureSet(keypoints=keypoints, descriptors=descriptors, image_shape=gray.shape[:2])

    def draw_keypoints(self, image: np.ndarray, features: FeatureSet) -> np.ndarray:
        """Return a visualisation image with detected keypoints drawn on it (for reports/screenshots)."""
        return cv2.drawKeypoints(
            image, features.keypoints, None,
            flags=cv2.DRAW_MATCHES_FLAGS_DRAW_RICH_KEYPOINTS,
        )