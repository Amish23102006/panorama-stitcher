# Project Statement: Panorama-Stitcher

## Problem Statement

Creating high-quality panoramic images from multiple overlapping photographs is a non-trivial task. Manual composition in image editing software is time-consuming, error-prone, and requires significant user expertise. Users capture sequences of overlapping photos (e.g., landscape sweeps, architectural documentation, wide-angle scenes) but lack automated tools that reliably register and composite them into seamless panoramas.

**Core Challenge**: Algorithmically detect corresponding features across images, establish geometric relationships (homography), reject outliers, and blend images to produce a single coherent panoramic output—all without manual alignment or GUI interaction.

**Real-World Context**:
- Photographers need automated panorama creation to handle high-volume photo sets
- Computer vision applications (drone imagery, medical imaging, 3D reconstruction) require robust image alignment
- Mobile and embedded systems demand CPU-efficient algorithms (SIFT vs. ORB trade-offs)

## Scope of the Project

### In Scope

1. **Multi-image registration**: Automatically detect and match keypoints across 2 or more overlapping images
2. **Homography estimation**: Compute geometric transformation matrices using RANSAC to robustly estimate alignment
3. **Sequential stitching**: Register images in order (left-to-right or front-to-back) without user intervention
4. **Image blending**: Composite aligned images into a single panoramic output
5. **Modular architecture**: Separate concerns (detection, matching, stitching, I/O) for testability and reuse
6. **CLI interface**: Command-line entry point with configurable parameters (detector, thresholds, logging)
7. **Comprehensive testing**: Unit tests and integration tests for each module
8. **Logging & metrics**: Detailed per-pair statistics (keypoints, matches, inliers, errors) for debugging and validation
9. **Performance optimization**: Automatic image downscaling to balance speed vs. quality

### Out of Scope

- **Interactive GUI**: No graphical user interface for manual adjustment or preview
- **Real-time video stitching**: No continuous frame processing from live camera feeds
- **Advanced projections**: No cylindrical, spherical, or fisheye models (affine homography only)
- **AI-based refinement**: No deep learning for learned feature descriptors or semantic alignment
- **Multi-band seam finding**: No sophisticated gradient-domain blending or seam optimization
- **Batch processing framework**: No worker pools or distributed stitching across multiple machines

## Target Users

### Primary Users

1. **Photographers & Content Creators**: Professionals who shoot panoramic sequences and need rapid, hands-off compositing
2. **Computer Vision Practitioners**: Students and researchers implementing classical stitching pipelines as reference implementations
3. **Automation Engineers**: Teams integrating image processing into headless/CI/CD pipelines where GUI tools are impractical

### Secondary Users

- Educators teaching feature detection, geometric transformations, and RANSAC
- GIS & remote sensing analysts compositing aerial or satellite image mosaics
- Developers building mobile or embedded vision applications who need an open-source baseline

## High-Level Features

### Core Functionality

| Feature | Description |
|---------|-------------|
| **Dual-Detector Support** | Choose between SIFT (high-quality keypoints) and ORB (fast approximation) via CLI |
| **Lowe's Ratio Test** | Automatic false-match filtering; configurable threshold for strict vs. permissive matching |
| **RANSAC Homography** | Robust geometric estimation that rejects outlier correspondences; reprojection error tracking |
| **Automatic Scaling** | Images downscaled intelligently to maximize speed without losing alignment precision |
| **Per-Pair Metrics** | Detailed statistics: keypoint counts, raw matches, good matches, inliers, reprojection error, execution time |
| **Error Handling** | Graceful degradation: reports insufficient matches, malformed inputs, missing files with clear logging |
| **Comprehensive Logging** | Structured logs at DEBUG/INFO/WARNING/ERROR levels; optional file output for auditing |

### Non-Functional Attributes

| Attribute | Target |
|-----------|--------|
| **Performance** | 2-image stitching in < 0.1s on modern hardware (CPU only, no GPU required) |
| **Scalability** | Handles image sequences with 2–10+ images; memory usage proportional to `max_dim` parameter |
| **Usability** | Zero GUI dependencies; fully CLI-driven and shell-scriptable for batch operations |
| **Robustness** | Gracefully handles mismatched overlaps, texture-poor regions, and occlusions via RANSAC |
| **Maintainability** | Modular codebase; 5–10 files with clear responsibilities; comprehensive unit tests (80%+ coverage target) |
| **Portability** | macOS, Linux, Windows; Python 3.8+; standard library dependencies only (OpenCV, NumPy) |

### CLI Interface

```bash
panostitch INPUT_DIR [OPTIONS]

Arguments:
  input_dir                    Folder of overlapping images (in order)

Options:
  -o, --output                 Output panorama path (default: output/panorama.jpg)
  --detector {sift,orb}        Feature detector (default: sift)
  --ratio                      Lowe's ratio threshold (default: 0.75)
  --ransac-thresh              RANSAC error threshold in pixels (default: 4.0)
  --max-dim                    Max dimension for downscaling (default: 1600)
  --log-file                   Optional log file path
  --log-level {DEBUG,INFO,WARNING,ERROR}  Logging verbosity (default: INFO)
```

### Output Artifacts

1. **Panorama Image**: `output/panorama.jpg` (or custom path) — final stitched photograph
2. **Metrics JSON**: `output/metrics.json` — per-pair statistics for validation & debugging
3. **Summary Text**: `output/summary.txt` — human-readable report of stitching process

## Alignment with Course Concepts

This project demonstrates mastery of **Computer Vision** fundamentals:

- **Feature Detection**: Scale-Invariant Feature Transform (SIFT) and Oriented FAST Rotated BRIEF (ORB) keypoint extraction
- **Descriptors**: Computing and storing local feature descriptors for matching
- **Matching**: Correspondence finding via descriptor distance; Lowe's ratio test for outlier rejection
- **Geometric Transformation**: Homography matrix computation and application
- **Robust Estimation**: RANSAC algorithm for outlier-resistant model fitting
- **Image Blending**: Alpha compositing and overlap handling for seamless panoramas
- **Computational Efficiency**: Image pyramid, multi-scale processing, and performance tuning

## Success Criteria

✅ **Functional Requirements**:
- Detects keypoints in overlapping images
- Establishes robust correspondences between image pairs
- Computes homography transformations
- Produces a composite panorama image
- Runs entirely from CLI without GUI

✅ **Non-Functional Requirements**:
- Executes in < 1 second for typical 2-image stitching
- Handles images up to 4K resolution (with auto-scaling)
- Provides detailed logging & metrics for validation
- Modular design with ≥ 5 meaningful modules
- Comprehensive test coverage (unit + integration tests)

✅ **Code Quality**:
- Proper error handling (FileNotFoundError, ValueError, InsufficientMatchesError)
- Clean, documented code with docstrings
- Git version control with meaningful commit history
- Public GitHub repository with clear README

---

**Version**: 1.0  
**Status**: Complete & ready for evaluation  
**Submission Date**: September 18, 2026