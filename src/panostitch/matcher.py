"""
matcher.py
----------
MODULE 2 - Feature Matching & Homography Estimation

Takes the FeatureSets produced by Module 1 for a pair of images, finds
correspondences between them (with Lowe's ratio test to filter
ambiguous matches), and fits a homography matrix with RANSAC so
outlier matches don't corrupt the geometric transform.
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass
from typing import List, Optional

import cv2
import numpy as np

from .config import StitchConfig
from .feature_engine import FeatureSet

logger = logging.getLogger("panostitch")


class InsufficientMatchesError(Exception):
    """Raised when two images don't share enough reliable matches to stitch."""


@dataclass
class MatchResult:
    """Everything the report needs to know about how two images were related."""
    good_matches: List[cv2.DMatch]
    homography: np.ndarray          # 3x3 matrix mapping image A -> image B's plane
    inlier_mask: np.ndarray         # RANSAC inlier/outlier mask, one entry per good match
    reprojection_error: float       # mean reprojection error over inliers (pixels)

    @property
    def inlier_count(self) -> int:
        return int(self.inlier_mask.sum())

    @property
    def inlier_ratio(self) -> float:
        return self.inlier_count / max(1, len(self.good_matches))


class Matcher:
    """Matches feature sets and estimates homographies between image pairs."""

    def __init__(self, config: StitchConfig):
        self.config = config
        norm = cv2.NORM_L2 if config.detector.lower() == "sift" else cv2.NORM_HAMMING
        self._bf = cv2.BFMatcher(norm)

    def match(self, features_a: FeatureSet, features_b: FeatureSet) -> MatchResult:
        """
        Match descriptors from image A against image B, apply Lowe's ratio
        test, then robustly fit a homography with RANSAC.
        """
        start = time.perf_counter()
        knn_matches = self._bf.knnMatch(features_a.descriptors, features_b.descriptors, k=2)

        good_matches = [
            m for m, n in knn_matches
            if m.distance < self.config.lowe_ratio * n.distance
        ]
        elapsed = time.perf_counter() - start
        logger.info(
            "Matching: %d raw pairs -> %d good matches after ratio test (%.3fs)",
            len(knn_matches), len(good_matches), elapsed,
        )

        if len(good_matches) < self.config.min_match_count:
            raise InsufficientMatchesError(
                f"Only {len(good_matches)} good matches found "
                f"(need >= {self.config.min_match_count}). "
                "These images may not overlap enough to stitch."
            )

        src_pts = np.float32(
            [features_a.keypoints[m.queryIdx].pt for m in good_matches]
        ).reshape(-1, 1, 2)
        dst_pts = np.float32(
            [features_b.keypoints[m.trainIdx].pt for m in good_matches]
        ).reshape(-1, 1, 2)

        homography, mask = cv2.findHomography(
            src_pts, dst_pts,
            method=cv2.RANSAC,
            ransacReprojThreshold=self.config.ransac_reproj_threshold,
            maxIters=self.config.ransac_max_iters,
        )

        if homography is None:
            raise InsufficientMatchesError(
                "RANSAC failed to find a consistent homography for this image pair."
            )

        inlier_mask = mask.ravel().astype(bool)
        reproj_error = self._mean_reprojection_error(src_pts, dst_pts, homography, inlier_mask)

        logger.info(
            "Homography: %d/%d inliers (%.1f%%), mean reprojection error %.2fpx",
            inlier_mask.sum(), len(good_matches), 100 * inlier_mask.mean(), reproj_error,
        )

        return MatchResult(
            good_matches=good_matches,
            homography=homography,
            inlier_mask=inlier_mask,
            reprojection_error=reproj_error,
        )

    @staticmethod
    def _mean_reprojection_error(
        src_pts: np.ndarray, dst_pts: np.ndarray, H: np.ndarray, inlier_mask: np.ndarray
    ) -> float:
        """Average pixel distance between projected source points and their matched destination points."""
        projected = cv2.perspectiveTransform(src_pts[inlier_mask], H)
        diffs = projected.reshape(-1, 2) - dst_pts[inlier_mask].reshape(-1, 2)
        return float(np.mean(np.linalg.norm(diffs, axis=1))) if len(diffs) else float("nan")

    def draw_matches(
        self, img_a: np.ndarray, features_a: FeatureSet,
        img_b: np.ndarray, features_b: FeatureSet, result: MatchResult,
        inliers_only: bool = True,
    ) -> np.ndarray:
        """Return a side-by-side visualisation of matched keypoints (for reports/screenshots)."""
        matches_to_draw = (
            [m for m, keep in zip(result.good_matches, result.inlier_mask) if keep]
            if inliers_only else result.good_matches
        )
        return cv2.drawMatches(
            img_a, features_a.keypoints, img_b, features_b.keypoints,
            matches_to_draw, None,
            flags=cv2.DrawMatchesFlags_NOT_DRAW_SINGLE_POINTS,
        )