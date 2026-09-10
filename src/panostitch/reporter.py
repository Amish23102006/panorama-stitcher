"""
reporter.py
-----------
Turns a StitchRun into persisted artefacts: a machine-readable JSON
metrics file and a human-readable text summary. Kept separate from
stitcher.py so the core algorithm has no knowledge of how results
get reported (single-responsibility, maintainability).
"""

from __future__ import annotations

import json
import logging
import os
from datetime import datetime, timezone

from .stitcher import StitchRun

logger = logging.getLogger("panostitch")


def build_metrics_dict(run: StitchRun, config_dict: dict) -> dict:
    return {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "config": config_dict,
        "summary": {
            "images_used": run.images_used,
            "images_skipped": run.images_skipped,
            "total_time_seconds": round(run.total_time_seconds, 3),
            "panorama_resolution": {
                "width": int(run.panorama.shape[1]),
                "height": int(run.panorama.shape[0]),
            },
        },
        "pairs": [
            {
                "image_a": p.index_a,
                "image_b": p.index_b,
                "good_matches": p.good_matches,
                "inliers": p.inliers,
                "inlier_ratio": round(p.inlier_ratio, 4),
                "mean_reprojection_error_px": round(p.reprojection_error, 4),
            }
            for p in run.pair_reports
        ],
    }


def write_reports(run: StitchRun, config_dict: dict, output_dir: str) -> None:
    """Write metrics.json and summary.txt into output_dir."""
    os.makedirs(output_dir, exist_ok=True)
    metrics = build_metrics_dict(run, config_dict)

    json_path = os.path.join(output_dir, "metrics.json")
    with open(json_path, "w") as f:
        json.dump(metrics, f, indent=2)
    logger.info("Wrote metrics -> %s", json_path)

    summary_path = os.path.join(output_dir, "summary.txt")
    with open(summary_path, "w") as f:
        f.write("Panorama Stitching Run Summary\n")
        f.write("=" * 32 + "\n")
        f.write(f"Images used   : {run.images_used}\n")
        f.write(f"Images skipped: {run.images_skipped}\n")
        f.write(f"Total time    : {run.total_time_seconds:.2f}s\n")
        f.write(f"Output size   : {run.panorama.shape[1]}x{run.panorama.shape[0]}\n\n")
        f.write("Pairwise matching quality:\n")
        for p in run.pair_reports:
            f.write(
                f"  [{p.index_a} -> {p.index_b}] good_matches={p.good_matches} "
                f"inliers={p.inliers} ({p.inlier_ratio:.1%}) "
                f"reprojection_error={p.reprojection_error:.2f}px\n"
            )
    logger.info("Wrote summary -> %s", summary_path)