"""
panostitch
==========

A feature-based image stitching pipeline built from classical computer
vision concepts: keypoint detection & description, feature matching,
homography estimation with RANSAC, perspective warping and blending.

Modules
-------
- config           : central configuration & logging setup (non-functional: maintainability)
- io_utils         : image loading / saving / resizing helpers
- feature_engine   : Module 1 - keypoint detection & description
- matcher          : Module 2 - feature matching + homography estimation (RANSAC)
- stitcher         : Module 3 - warping, blending and multi-image panorama assembly
- reporter         : run-report / metrics generation (JSON + human-readable summary)
- cli              : command-line entry point tying the modules together
"""

__version__ = "1.0.0"