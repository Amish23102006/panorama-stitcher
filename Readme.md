# Panorama-Stitcher

Feature-based image stitching pipeline that detects keypoints, matches them across overlapping photos, estimates geometric alignment using RANSAC homography, and blends the images into a single panoramic output.

## Overview
Panorama-Stitcher is a command-line tool for automated panoramic image creation from a sequence of overlapping photographs. It applies classical computer vision techniques (SIFT/ORB feature detection, Lowe's ratio matching, RANSAC homography estimation, and image blending) to register and composite multiple images into one wide-field photograph.

The pipeline automatically downscales large inputs, detects geometric inconsistencies, and provides detailed logging and metrics for each stitching operation.

<!--
## Results  (uncomment after uploading images to an images/ folder)
| Input 1 | Input 2 | Input 3 |
|---|---|---|
| ![](images/in1.jpg) | ![](images/in2.jpg) | ![](images/in3.jpg) |

**Stitched panorama:**
![](images/panorama.jpg)
-->

## Features
- **Dual detector support:** SIFT (high quality, slower) or ORB (fast, approximate)
- **Robust matching:** Lowe's ratio test filters false correspondences; RANSAC removes geometric outliers
- **Automatic image scaling:** downscales inputs to speed up processing
- **Detailed logging & metrics:** per-pair keypoints, matches, inliers, and reprojection error
- **CLI-only execution:** no GUI dependencies; fully scriptable and headless
- **Test suite:** unit and integration tests for the core pipeline
- **Modular architecture:** clean separation across 8 core modules

## Technologies & Tools
| Component | Technology |
|---|---|
| Language | Python 3.8+ |
| Core libraries | OpenCV 4.8+, NumPy 1.24+ |
| Feature detection | SIFT (OpenCV contrib), ORB (OpenCV) |
| Homography estimation | RANSAC (OpenCV) |
| Testing | pytest |
| Logging | Python `logging` module |
| Version control | Git |

## Installation

### Prerequisites
- Python 3.8 or later
- macOS, Linux, or Windows with a terminal

### Step 1: Clone the repository
```bash
git clone https://github.com/Amish23102006/panorama-stitcher
cd panorama-stitcher
```

### Step 2: Create a virtual environment
macOS/Linux:
```bash
python3 -m venv venv
source venv/bin/activate
```
Windows:
```bash
python -m venv venv
venv\Scripts\activate
```

### Step 3: Install dependencies
```bash
pip install --upgrade pip
pip install -e .
```
This installs `opencv-contrib-python>=4.8.0`, `numpy>=1.24.0`, and `pytest>=6.0`.

### Step 4: Verify installation
```bash
panostitch --help
```

## Quick Start

### Generate sample images (for testing)
```bash
python3 << 'PYEOF'
import cv2
import numpy as np
from pathlib import Path

Path("sample_data").mkdir(exist_ok=True)

def make_test_image(seed=0):
    rng = np.random.default_rng(seed)
    img = np.zeros((400, 900, 3), dtype=np.uint8)
    for c in range(3):
        img[:, :, c] = np.linspace(40, 200, 900, dtype=np.uint8)[None, :]
    for _ in range(80):
        x, y = rng.integers(0, 900), rng.integers(0, 400)
        r = rng.integers(8, 30)
        color = tuple(int(v) for v in rng.integers(50, 200, size=3))
        cv2.circle(img, (x, y), r, color, -1)
    return img

big = make_test_image(seed=42)
crop_w, step = 600, 360
cv2.imwrite("sample_data/img_01.jpg", big[:, 0:crop_w])
cv2.imwrite("sample_data/img_02.jpg", big[:, step:step+crop_w])
print("Sample images created")
PYEOF
```

### Run the stitcher
```bash
panostitch sample_data -o output/panorama.jpg --log-level INFO
```
Example output:
```
Found 2 input images in sample_data
Feature detection (SIFT): 91 keypoints in 0.033s
Feature detection (SIFT): 63 keypoints in 0.029s
Matching: 91 raw pairs -> 33 good matches after ratio test (0.000s)
Homography: 19/33 inliers (57.6%), mean reprojection error 0.09px
Stitching complete: 2/2 images used, 0 skipped, 0.09s total
Saved image -> output/panorama.jpg
```
Files generated: `output/panorama.jpg` (stitched image), `output/metrics.json` (per-pair statistics), `output/summary.txt` (readable summary).

## Usage
```bash
panostitch INPUT_DIR -o OUTPUT_PATH [OPTIONS]
```
`INPUT_DIR` is a folder of overlapping images in order (left-to-right). Supports `.jpg`, `.png`, `.bmp`.

| Flag | Default | Description |
|---|---|---|
| `-o, --output` | `output/panorama.jpg` | Output path |
| `--detector` | `sift` | `sift` (quality) or `orb` (fast) |
| `--ratio` | `0.75` | Lowe's ratio threshold; lower is stricter |
| `--ransac-thresh` | `4.0` | RANSAC reprojection threshold (pixels) |
| `--max-dim` | `1600` | Downscale so longest side ≤ this value |
| `--log-file` | none | Write logs to a file |
| `--log-level` | `INFO` | `DEBUG`, `INFO`, `WARNING`, `ERROR` |

Examples:
```bash
panostitch sample_data -o output/panorama_orb.jpg --detector orb
panostitch sample_data --ratio 0.7 -o output/strict.jpg
panostitch sample_data --max-dim 2048 --ransac-thresh 8.0
panostitch sample_data --log-level DEBUG --log-file debug.log
```

## Testing
```bash
pytest tests/ -v
pytest tests/test_pipeline.py::TestFeatureEngine -v
```
Test classes: `TestFeatureEngine`, `TestMatcher`, `TestStitcher`, `TestIoUtils`.

## Project Architecture
```
panorama-stitcher/
├── src/panostitch/
│   ├── cli.py             # Command-line entry point
│   ├── config.py          # Configuration & logging setup
│   ├── feature_engine.py  # Keypoint detection & description
│   ├── matcher.py         # Feature matching & homography
│   ├── stitcher.py        # Multi-image composition
│   ├── reporter.py        # Metrics & logging output
│   └── io_utils.py        # Image I/O & preprocessing
├── tests/
│   └── test_pipeline.py
├── sample_data/
├── requirements.txt
├── setup.py
├── README.md
└── statement.md
```

### Data flow
```
INPUT_DIR → load & resize → detect features → match (ratio test) → RANSAC homography → blend → panorama + metrics
```

## Troubleshooting
- **`panostitch: command not found`:** activate the virtual environment (`source venv/bin/activate`).
- **No images found:** check the folder exists and contains `.jpg`/`.png`/`.bmp` files in alphabetical order.
- **Insufficient matches:** images may not overlap enough. Try `--ratio 0.8 --ransac-thresh 6.0` or use `--detector sift`.
- **RANSAC failed / few inliers:** make sure images overlap by 30–50%, have rich texture, and are in sequential order.
- **Slow performance:** use `--max-dim 800` or `--detector orb`.

## Performance Notes
- SIFT: about 33 ms per image; ORB: about 10 ms per image (on the sample images)
- Full 2-image pipeline: about 0.09 s
- Memory scales with `--max-dim`

## Future Enhancements
- GPU-accelerated feature detection
- Multi-band blending for smoother seams
- Cylindrical/spherical projection for ultra-wide panoramas
- Video frame extraction and stitching

## References
- Lowe, D. G. (2004). "Distinctive image features from scale-invariant keypoints." IJCV.
- Fischler, M. A., & Bolles, R. C. (1981). "Random Sample Consensus." CACM.
- Brown, M., & Lowe, D. G. (2007). "Automatic panoramic image stitching." IJCV.

## Acknowledgements
Built as a project for VIT's Computer Vision course (CSE3010).

**Author:** Amish Chaturvedi · [GitHub](https://github.com/Amish23102006) · [LinkedIn](https://linkedin.com/in/amish-chaturvedi-756606333)
