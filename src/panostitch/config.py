"""
config.py
---------
Central configuration and logging setup.

Keeping all tunable parameters in one place is what lets the rest of the
pipeline stay modular and maintainable (a non-functional requirement):
changing the matching ratio or RANSAC threshold never requires touching
algorithm code.
"""

from __future__ import annotations

import logging
import sys
from dataclasses import dataclass


@dataclass(frozen=True)
class StitchConfig:
    """All tunable parameters for the pipeline, gathered in one place."""

    # --- Module 1: feature detection ---
    detector: str = "sift"          # "sift" or "orb"
    max_features: int = 4000        # cap for resource efficiency on large images

    # --- Module 2: matching & homography ---
    lowe_ratio: float = 0.75        # Lowe's ratio test threshold
    min_match_count: int = 10       # below this, reject the pair (reliability)
    ransac_reproj_threshold: float = 4.0
    ransac_max_iters: int = 2000

    # --- Module 3: warping & blending ---
    blend_feather_width: int = 40   # pixels used for feathered seam blending
    max_output_dimension: int = 6000  # safety cap so panoramas can't explode in size

    # --- performance / resource efficiency ---
    working_max_dim: int = 1600     # images are downscaled to this before processing

    # --- logging / monitoring ---
    log_level: str = "INFO"


def setup_logging(log_path: str | None, level: str = "INFO") -> logging.Logger:
    """
    Configure a logger that writes to stdout and, optionally, to a log file.

    Centralised logging is the project's monitoring/observability mechanism
    (non-functional requirement): every stage of the pipeline reports what
    it did, how long it took, and any recoverable errors it hit.
    """
    logger = logging.getLogger("panostitch")
    logger.setLevel(getattr(logging, level.upper(), logging.INFO))
    logger.handlers.clear()

    fmt = logging.Formatter(
        "%(asctime)s | %(levelname)-7s | %(name)s | %(message)s",
        datefmt="%H:%M:%S",
    )

    stream_handler = logging.StreamHandler(sys.stdout)
    stream_handler.setFormatter(fmt)
    logger.addHandler(stream_handler)

    if log_path:
        file_handler = logging.FileHandler(log_path)
        file_handler.setFormatter(fmt)
        logger.addHandler(file_handler)

    return logger