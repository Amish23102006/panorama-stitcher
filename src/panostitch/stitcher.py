"""
stitcher.py
-----------
MODULE 3 - Warping, Blending & Panorama Assembly

Given a sequence of images, this module orchestrates Modules 1 and 2
across consecutive pairs, chains the resulting homographies into a
single reference frame, warps every image into that frame, and blends
the overlapping regions with a distance-based feathered seam so joins
aren't hard edges.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import List

import cv2
import numpy as np

from .config import StitchConfig
from .feature_engine import FeatureEngine, FeatureSet
from .matcher import Matcher, MatchResult, InsufficientMatchesError

logger = logging.getLogger("panostitch")


@dataclass
class PairReport:
    """Metrics for one consecutive image pair, used later by the reporter module."""
    index_a: int
    index_b: int
    good_matches: int
    inliers: int
    inlier_ratio: float
    reprojection_error: float


@dataclass
class StitchRun:
    """Full result of a stitching run: the panorama plus everything needed to report on it."""
    panorama: np.ndarray
    pair_reports: List[PairReport] = field(default_factory=list)
    total_time_seconds: float = 0.0
    images_used: int = 0
    images_skipped: int = 0


class PanoramaStitcher:
    """
    Orchestrates the full pipeline: feature detection -> matching ->
    homography chaining -> warping -> blending.
    """

    def __init__(self, config: StitchConfig):
        self.config = config
        self.feature_engine = FeatureEngine(config)
        self.matcher = Matcher(config)

    def stitch(self, images: List[np.ndarray]) -> StitchRun:
        if len(images) < 2:
            raise ValueError("Need at least 2 images to build a panorama.")

        start = time.perf_counter()

        # --- Module 1: extract features for every image up front ---
        feature_sets: List[FeatureSet] = []
        for i, img in enumerate(images):
            try:
                feature_sets.append(self.feature_engine.detect_and_describe(img))
            except RuntimeError as exc:
                logger.warning("Image %d skipped during feature detection: %s", i, exc)
                feature_sets.append(None)  # placeholder, handled below

        # --- Module 2: match consecutive pairs & chain homographies to a common frame ---
        # Reference frame = the middle image, to minimise cumulative warp distortion.
        ref_idx = len(images) // 2
        homographies = [None] * len(images)
        homographies[ref_idx] = np.eye(3)

        pair_reports: List[PairReport] = []
        skipped = 0

        # walk outward from the reference image in both directions
        for direction in (-1, 1):
            acc_h = np.eye(3)
            idx = ref_idx
            while 0 <= idx + direction < len(images):
                nxt = idx + direction
                if feature_sets[idx] is None or feature_sets[nxt] is None:
                    logger.warning("Skipping pair (%d, %d): missing features.", idx, nxt)
                    skipped += 1
                    idx = nxt
                    continue
                try:
                    # match "next" image onto "idx" (which is already in a known frame)
                    result: MatchResult = self.matcher.match(feature_sets[nxt], feature_sets[idx])
                except InsufficientMatchesError as exc:
                    logger.warning("Skipping pair (%d, %d): %s", nxt, idx, exc)
                    skipped += 1
                    idx = nxt
                    continue

                acc_h = homographies[idx] @ result.homography
                homographies[nxt] = acc_h

                pair_reports.append(PairReport(
                    index_a=nxt, index_b=idx,
                    good_matches=len(result.good_matches),
                    inliers=result.inlier_count,
                    inlier_ratio=result.inlier_ratio,
                    reprojection_error=result.reprojection_error,
                ))
                idx = nxt

        used_indices = [i for i in range(len(images)) if homographies[i] is not None]
        if len(used_indices) < 2:
            raise InsufficientMatchesError(
                "Fewer than 2 images could be aligned - check that your photos overlap "
                "by at least ~30% and are in a roughly left-to-right (or top-to-bottom) order."
            )

        # --- Module 3: warp every alignable image into the panorama canvas & blend ---
        panorama = self._warp_and_blend(
            [images[i] for i in used_indices],
            [homographies[i] for i in used_indices],
        )

        elapsed = time.perf_counter() - start
        logger.info(
            "Stitching complete: %d/%d images used, %d skipped, %.2fs total",
            len(used_indices), len(images), skipped, elapsed,
        )

        return StitchRun(
            panorama=panorama,
            pair_reports=pair_reports,
            total_time_seconds=elapsed,
            images_used=len(used_indices),
            images_skipped=skipped,
        )

    def _warp_and_blend(self, images: List[np.ndarray], homographies: List[np.ndarray]) -> np.ndarray:
        """
        Compute the bounding canvas for all warped images, then blend them
        with a distance-transform feathered seam so overlaps aren't visible hard edges.
        """
        corners_all = []
        for img, H in zip(images, homographies):
            h, w = img.shape[:2]
            corners = np.float32([[0, 0], [w, 0], [w, h], [0, h]]).reshape(-1, 1, 2)
            corners_all.append(cv2.perspectiveTransform(corners, H))

        all_corners = np.concatenate(corners_all, axis=0)
        x_min, y_min = np.floor(all_corners.min(axis=0).ravel()).astype(int)
        x_max, y_max = np.ceil(all_corners.max(axis=0).ravel()).astype(int)

        # cap canvas size for resource efficiency / safety (non-functional requirement)
        canvas_w = min(x_max - x_min, self.config.max_output_dimension)
        canvas_h = min(y_max - y_min, self.config.max_output_dimension)

        translation = np.array([[1, 0, -x_min], [0, 1, -y_min], [0, 0, 1]], dtype=np.float64)

        acc_color = np.zeros((canvas_h, canvas_w, 3), dtype=np.float64)
        acc_weight = np.zeros((canvas_h, canvas_w), dtype=np.float64)

        for img, H in zip(images, homographies):
            full_h = translation @ H
            warped = cv2.warpPerspective(img, full_h, (canvas_w, canvas_h))

            mask = np.ones(img.shape[:2], dtype=np.uint8) * 255
            warped_mask = cv2.warpPerspective(mask, full_h, (canvas_w, canvas_h))

            # distance transform -> smooth feathered weight, higher in the middle of each image
            weight = cv2.distanceTransform(warped_mask, cv2.DIST_L2, 5)
            weight = np.clip(weight / max(self.config.blend_feather_width, 1), 0, 1)

            acc_color += warped.astype(np.float64) * weight[..., None]
            acc_weight += weight

        acc_weight[acc_weight == 0] = 1e-6  # avoid divide-by-zero on empty canvas regions
        blended = (acc_color / acc_weight[..., None]).astype(np.uint8)
        return blended