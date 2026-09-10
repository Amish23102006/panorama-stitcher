"""
test_pipeline.py
-----------------
Validation tests for each module plus one end-to-end integration test.
Run with:  pytest tests/ -v
"""

import numpy as np
import pytest
import cv2

from panostitch.config import StitchConfig
from panostitch.feature_engine import FeatureEngine
from panostitch.matcher import Matcher, InsufficientMatchesError
from panostitch.stitcher import PanoramaStitcher
from panostitch.io_utils import resize_max_dim


def make_textured_image(width=500, height=400, seed=0) -> np.ndarray:
    """Generate a synthetic but richly-textured image so SIFT/ORB have real keypoints to find."""
    rng = np.random.default_rng(seed)
    img = np.zeros((height, width, 3), dtype=np.uint8)

    # random background gradient
    for c in range(3):
        img[:, :, c] = np.linspace(40, 200, width, dtype=np.uint8)[None, :]

    # scatter shapes with varied size/color so there's plenty of texture to key on
    for _ in range(60):
        x, y = rng.integers(0, width), rng.integers(0, height)
        r = rng.integers(5, 25)
        color = tuple(int(v) for v in rng.integers(0, 255, size=3))
        shape = rng.integers(0, 3)
        if shape == 0:
            cv2.circle(img, (x, y), r, color, -1)
        elif shape == 1:
            cv2.rectangle(img, (x, y), (x + r, y + r), color, -1)
        else:
            cv2.line(img, (x, y), (x + r, y - r), color, 3)

    return img


def make_overlapping_pair(overlap_fraction=0.4):
    """Slice two overlapping crops out of one large synthetic image (known ground-truth overlap)."""
    big = make_textured_image(width=900, height=400, seed=42)
    w = big.shape[1]
    crop_w = 600
    step = int(crop_w * (1 - overlap_fraction))
    left = big[:, 0:crop_w]
    right = big[:, step:step + crop_w]
    return left, right


class TestFeatureEngine:
    def test_detects_keypoints_on_textured_image(self):
        config = StitchConfig(detector="sift")
        engine = FeatureEngine(config)
        img = make_textured_image()
        features = engine.detect_and_describe(img)
        assert len(features.keypoints) > 0
        assert features.descriptors.shape[0] == len(features.keypoints)

    def test_orb_detector_also_works(self):
        config = StitchConfig(detector="orb")
        engine = FeatureEngine(config)
        img = make_textured_image()
        features = engine.detect_and_describe(img)
        assert len(features.keypoints) > 0

    def test_unsupported_detector_raises(self):
        with pytest.raises(ValueError):
            FeatureEngine(StitchConfig(detector="not_a_real_detector"))

    def test_blank_image_raises_runtime_error(self):
        config = StitchConfig(detector="sift")
        engine = FeatureEngine(config)
        blank = np.zeros((200, 200, 3), dtype=np.uint8)
        with pytest.raises(RuntimeError):
            engine.detect_and_describe(blank)


class TestMatcher:
    def test_matches_overlapping_images(self):
        config = StitchConfig(detector="sift")
        engine = FeatureEngine(config)
        matcher = Matcher(config)

        img_a, img_b = make_overlapping_pair()
        feats_a = engine.detect_and_describe(img_a)
        feats_b = engine.detect_and_describe(img_b)

        result = matcher.match(feats_a, feats_b)
        assert result.inlier_count >= config.min_match_count // 2
        assert result.homography.shape == (3, 3)
        assert result.reprojection_error < 10.0  # should be geometrically consistent

    def test_non_overlapping_images_raise(self):
        # A strict min_match_count models the real-world "these photos don't overlap
        # enough" rejection case, since two independently-random synthetic images
        # will always share a handful of spurious matches by chance.
        config = StitchConfig(detector="sift", min_match_count=500)
        engine = FeatureEngine(config)
        matcher = Matcher(config)

        img_a = make_textured_image(seed=1)
        img_b = make_textured_image(seed=999)  # unrelated content -> should not match well

        feats_a = engine.detect_and_describe(img_a)
        feats_b = engine.detect_and_describe(img_b)

        with pytest.raises(InsufficientMatchesError):
            matcher.match(feats_a, feats_b)


class TestStitcher:
    def test_end_to_end_stitch_produces_wider_panorama(self):
        config = StitchConfig(detector="sift")
        stitcher = PanoramaStitcher(config)

        img_a, img_b = make_overlapping_pair(overlap_fraction=0.4)
        run = stitcher.stitch([img_a, img_b])

        assert run.images_used == 2
        assert run.images_skipped == 0
        # panorama should be wider than either single input (they were joined side by side)
        assert run.panorama.shape[1] > img_a.shape[1]
        assert len(run.pair_reports) == 1

    def test_too_few_images_raises(self):
        config = StitchConfig()
        stitcher = PanoramaStitcher(config)
        with pytest.raises(ValueError):
            stitcher.stitch([make_textured_image()])


class TestIoUtils:
    def test_resize_max_dim_downscales_large_image(self):
        img = np.zeros((2000, 3000, 3), dtype=np.uint8)
        resized, scale = resize_max_dim(img, max_dim=1500)
        assert max(resized.shape[:2]) <= 1500
        assert scale < 1.0

    def test_resize_max_dim_leaves_small_image_untouched(self):
        img = np.zeros((300, 400, 3), dtype=np.uint8)
        resized, scale = resize_max_dim(img, max_dim=1500)
        assert scale == 1.0
        assert resized.shape == img.shape