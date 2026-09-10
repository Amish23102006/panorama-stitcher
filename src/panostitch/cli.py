"""
cli.py
------
Command-line entry point. Ties the modules together into a single
`panostitch` command that can be run entirely from a terminal, with no
GUI dependency, satisfying the project's CLI-executability requirement.
"""

from __future__ import annotations

import argparse
import dataclasses
import logging
import sys

from .config import StitchConfig, setup_logging
from .io_utils import list_images, load_image, resize_max_dim, save_image
from .matcher import InsufficientMatchesError
from .stitcher import PanoramaStitcher
from .reporter import write_reports


def build_arg_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="panostitch",
        description=(
            "Feature-based image stitching: detects keypoints, matches them, "
            "estimates homography with RANSAC, and blends overlapping photos "
            "into a single panorama."
        ),
    )
    parser.add_argument(
        "input_dir", help="Folder containing overlapping images to stitch, in order."
    )
    parser.add_argument(
        "-o", "--output", default="output/panorama.jpg",
        help="Path to write the final panorama image (default: output/panorama.jpg)",
    )
    parser.add_argument(
        "--detector", choices=["sift", "orb"], default="sift",
        help="Feature detector to use (default: sift).",
    )
    parser.add_argument(
        "--ratio", type=float, default=0.75,
        help="Lowe's ratio test threshold (default: 0.75).",
    )
    parser.add_argument(
        "--ransac-thresh", type=float, default=4.0,
        help="RANSAC reprojection threshold in pixels (default: 4.0).",
    )
    parser.add_argument(
        "--max-dim", type=int, default=1600,
        help="Images are downscaled so their longer side is at most this many pixels "
             "before processing, for speed (default: 1600).",
    )
    parser.add_argument(
        "--log-file", default=None,
        help="Optional path to also write logs to a file.",
    )
    parser.add_argument(
        "--log-level", default="INFO",
        choices=["DEBUG", "INFO", "WARNING", "ERROR"],
        help="Logging verbosity (default: INFO).",
    )
    return parser


def main(argv=None) -> int:
    args = build_arg_parser().parse_args(argv)
    logger = setup_logging(args.log_file, args.log_level)

    config = StitchConfig(
        detector=args.detector,
        lowe_ratio=args.ratio,
        ransac_reproj_threshold=args.ransac_thresh,
        working_max_dim=args.max_dim,
        log_level=args.log_level,
    )

    try:
        paths = list_images(args.input_dir)
        logger.info("Found %d input images in %s", len(paths), args.input_dir)

        images = []
        for p in paths:
            img = load_image(p)
            img, scale = resize_max_dim(img, config.working_max_dim)
            if scale != 1.0:
                logger.info("Resized %s by factor %.3f for performance", p, scale)
            images.append(img)

        stitcher = PanoramaStitcher(config)
        run = stitcher.stitch(images)

        save_image(run.panorama, args.output)
        write_reports(run, dataclasses.asdict(config), output_dir="output")

        logger.info("Done. Panorama written to %s", args.output)
        return 0

    except (FileNotFoundError, ValueError, IOError) as exc:
        logger.error("Input error: %s", exc)
        return 1
    except InsufficientMatchesError as exc:
        logger.error("Stitching failed: %s", exc)
        return 2
    except Exception as exc:  # pragma: no cover - safety net, still logged clearly
        logger.exception("Unexpected error: %s", exc)
        return 3


if __name__ == "__main__":
    sys.exit(main())