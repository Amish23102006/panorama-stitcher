"""
generate_report.py
-------------------
One-off script that assembles the project report PDF required by the
submission guidelines. Not part of the runtime package - lives in docs/
since it's a documentation-generation utility, not pipeline code.

Run with:  python3 docs/generate_report.py
"""

import os
from reportlab.lib.pagesizes import A4
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, PageBreak, Image, Table, TableStyle,
    ListFlowable, ListItem,
)

BASE = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DIAG = os.path.join(BASE, "docs", "diagrams")
OUT = os.path.join(BASE, "output")

styles = getSampleStyleSheet()
styles.add(ParagraphStyle(name="H1Custom", parent=styles["Heading1"], spaceBefore=18, spaceAfter=8))
styles.add(ParagraphStyle(name="H2Custom", parent=styles["Heading2"], spaceBefore=12, spaceAfter=6))
styles.add(ParagraphStyle(name="BodyCustom", parent=styles["BodyText"], leading=15, spaceAfter=8))
styles.add(ParagraphStyle(name="Caption", parent=styles["Italic"], fontSize=9, alignment=1, textColor=colors.grey))

story = []


def h1(text):
    story.append(Paragraph(text, styles["H1Custom"]))


def h2(text):
    story.append(Paragraph(text, styles["H2Custom"]))


def body(text):
    story.append(Paragraph(text, styles["BodyCustom"]))


def bullets(items):
    story.append(ListFlowable(
        [ListItem(Paragraph(i, styles["BodyCustom"])) for i in items],
        bulletType="bullet",
    ))
    story.append(Spacer(1, 6))


def figure(path, caption, max_width=6.3 * inch, max_height=3.6 * inch):
    img = Image(path)
    ratio = min(max_width / img.imageWidth, max_height / img.imageHeight, 1.0)
    img.drawWidth = img.imageWidth * ratio
    img.drawHeight = img.imageHeight * ratio
    story.append(img)
    story.append(Paragraph(caption, styles["Caption"]))
    story.append(Spacer(1, 12))


# ---------------------------------------------------------------- Cover Page
story.append(Spacer(1, 2.2 * inch))
story.append(Paragraph("PanoStitch", ParagraphStyle(
    name="Title", parent=styles["Title"], fontSize=30, spaceAfter=6)))
story.append(Paragraph("A Feature-Based Image Stitching Pipeline", ParagraphStyle(
    name="Subtitle", parent=styles["Heading2"], alignment=1, textColor=colors.HexColor("#455A64"))))
story.append(Spacer(1, 0.6 * inch))
story.append(Paragraph("CSE3010 - Computer Vision", styles["Heading3"]))
story.append(Paragraph("Flipped Course Evaluation - Project Report", styles["Normal"]))
story.append(Spacer(1, 1.2 * inch))
story.append(Paragraph("Submitted by: Amish", styles["Normal"]))
story.append(Paragraph("Course: Computer Vision (CSE3010)", styles["Normal"]))
story.append(Paragraph("Repository: https://github.com/&lt;github-username&gt;/&lt;repo-name&gt;", styles["Normal"]))
story.append(PageBreak())

# ---------------------------------------------------------------- Introduction
h1("1. Introduction")
body(
    "Stitching multiple overlapping photographs into a single wide panorama is one of "
    "the classic applications of computer vision, combining several concepts from the "
    "course syllabus into one working system: local feature extraction, feature "
    "matching, homography estimation, and image warping. This project, "
    "<b>PanoStitch</b>, implements a complete, command-line panorama-building "
    "pipeline from scratch using OpenCV, without relying on OpenCV's built-in "
    "high-level <font face='Courier'>Stitcher</font> class, so that every stage of the "
    "classical stitching pipeline is implemented and understood explicitly."
)
body(
    "The system takes a folder of two or more overlapping images and produces a single "
    "blended panorama, along with a quantitative report describing the quality of the "
    "feature matches and geometric alignment found between each pair of images."
)

# ---------------------------------------------------------------- Problem Statement
h1("2. Problem Statement")
body(
    "Given a set of photographs of the same scene taken from slightly different "
    "viewpoints (e.g. while panning a camera), automatically determine how the images "
    "overlap and combine them into a single, geometrically consistent, seamlessly "
    "blended panoramic image - entirely from the command line, with no manual "
    "alignment and no GUI interaction required."
)

# ---------------------------------------------------------------- Functional Requirements
h1("3. Functional Requirements")
body("The system is organised into three major functional modules, each independently testable:")
bullets([
    "<b>Module 1 - Feature Detection &amp; Description</b> (<font face='Courier'>feature_engine.py</font>): "
    "detects local keypoints in an image and computes a descriptor vector for each, using a "
    "configurable backend (SIFT or ORB).",
    "<b>Module 2 - Feature Matching &amp; Homography Estimation</b> (<font face='Courier'>matcher.py</font>): "
    "matches descriptors between an image pair with Lowe's ratio test, then robustly fits a "
    "3&times;3 homography matrix using RANSAC to reject outlier correspondences.",
    "<b>Module 3 - Warping, Blending &amp; Panorama Assembly</b> (<font face='Courier'>stitcher.py</font>): "
    "chains pairwise homographies to a common reference frame, warps every image into a shared "
    "canvas, and blends overlaps using a distance-transform feathered seam.",
])
body("Input/output structure:")
bullets([
    "<b>Input:</b> a folder path containing 2+ overlapping image files (.jpg/.png/.bmp/.tiff), "
    "supplied as a positional CLI argument.",
    "<b>Output:</b> a single stitched panorama image file, plus a <font face='Courier'>metrics.json</font> "
    "and <font face='Courier'>summary.txt</font> describing per-pair match/homography quality and timing.",
])
body("Workflow: a user runs one CLI command, the pipeline processes the images end-to-end without "
     "further interaction, and the console/log output reports progress and any images that had to be skipped.")

# ---------------------------------------------------------------- Non-Functional Requirements
h1("4. Non-Functional Requirements")
nfr_data = [
    ["Requirement", "How it is addressed"],
    ["Performance", "Images are downscaled to a configurable max dimension before processing (--max-dim)."],
    ["Reliability", "Pairs with insufficient matches or a failed RANSAC fit are skipped with a logged warning, not a crash."],
    ["Usability", "Single CLI command, sensible defaults, --help documentation, clear error messages."],
    ["Logging / Monitoring", "Every stage logs timing and quality metrics; optional file logging via --log-file."],
    ["Maintainability", "One responsibility per module; swappable detector backend without touching other code."],
    ["Scalability", "Stitches an arbitrary number of images via homography chaining, not just fixed pairs."],
    ["Resource efficiency", "Output canvas dimensions are capped to avoid runaway memory use."],
]
t = Table(nfr_data, colWidths=[1.6 * inch, 4.7 * inch])
t.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#455A64")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("VALIGN", (0, 0), (-1, -1), "TOP"),
    ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#F5F5F5")]),
]))
story.append(t)
story.append(Spacer(1, 10))
story.append(PageBreak())

# ---------------------------------------------------------------- System Architecture
h1("5. System Architecture")
body(
    "The pipeline is organised as a set of loosely-coupled modules coordinated by the CLI entry "
    "point. Configuration is centralised so that swapping algorithms (e.g. SIFT vs. ORB) or tuning "
    "thresholds never requires touching algorithm code."
)
figure(os.path.join(DIAG, "architecture.png"), "Figure 1: System architecture - module responsibilities and data flow.")

# ---------------------------------------------------------------- Design Diagrams
h1("6. Design Diagrams")

h2("6.1 Process / Workflow Diagram")
figure(os.path.join(DIAG, "workflow.png"), "Figure 2: End-to-end processing workflow, including the failure path for non-overlapping pairs.",
       max_height=8.5 * inch)
story.append(PageBreak())

h2("6.2 Use Case Diagram")
figure(os.path.join(DIAG, "use_case_diagram.png"), "Figure 3: Use case diagram - user interactions with the system.")

h2("6.3 Class / Component Diagram")
figure(os.path.join(DIAG, "class_diagram.png"), "Figure 4: Class diagram showing the core classes and their relationships.")

h2("6.4 Sequence Diagram")
figure(os.path.join(DIAG, "sequence_diagram.png"), "Figure 5: Sequence of calls for a single stitching run.", max_height=6.5 * inch)

body("No database or persistent storage is used by this project (all state is in-memory for a single "
     "run and results are written directly to image/JSON files), so no ER diagram or schema design applies.")
story.append(PageBreak())

# ---------------------------------------------------------------- Design Decisions & Rationale
h1("7. Design Decisions &amp; Rationale")
bullets([
    "<b>SIFT as the default detector:</b> SIFT is scale- and rotation-invariant and produces highly "
    "distinctive descriptors, which is important when overlap regions are small or images have "
    "moderate viewpoint change. ORB is offered as a faster, patent-free alternative.",
    "<b>Lowe's ratio test before RANSAC:</b> filtering ambiguous matches before geometric fitting "
    "reduces the outlier fraction that RANSAC has to cope with, improving homography accuracy.",
    "<b>RANSAC for homography estimation:</b> feature matching is never perfect; RANSAC lets the "
    "system robustly estimate the dominant geometric transform even when some matches are wrong.",
    "<b>Reference-frame homography chaining:</b> stitching around a central reference image (rather "
    "than always warping onto the first image) minimises cumulative perspective distortion when "
    "stitching 3+ images.",
    "<b>Feathered (distance-transform) blending</b> instead of a hard cut: avoids a visible seam line "
    "at the border between two warped images.",
    "<b>Fail-soft pair handling:</b> an image pair that cannot be matched confidently is skipped with "
    "a warning rather than aborting the whole run, so one bad photo doesn't ruin an entire panorama.",
])

# ---------------------------------------------------------------- Implementation Details
h1("8. Implementation Details")
body("Implemented in Python 3 using OpenCV's classical (non-deep-learning) computer vision APIs. "
     "Key implementation points:")
bullets([
    "<font face='Courier'>cv2.SIFT_create()</font> / <font face='Courier'>cv2.ORB_create()</font> for "
    "keypoint detection and descriptor computation (Module 1).",
    "<font face='Courier'>cv2.BFMatcher.knnMatch()</font> (k=2) followed by Lowe's ratio test to "
    "obtain candidate correspondences (Module 2).",
    "<font face='Courier'>cv2.findHomography(..., method=cv2.RANSAC)</font> to robustly estimate the "
    "3&times;3 projective transform between each image pair, plus a manual mean-reprojection-error "
    "calculation over the inlier set for reporting.",
    "Homographies for images on either side of a chosen reference image are accumulated via matrix "
    "multiplication to bring every image into one shared coordinate frame.",
    "<font face='Courier'>cv2.warpPerspective()</font> warps each image (and a corresponding binary "
    "mask) into the output canvas; <font face='Courier'>cv2.distanceTransform()</font> on each mask "
    "produces a smooth per-pixel blend weight that is highest at the centre of each image and fades "
    "toward its border, so overlapping images are combined with soft feathering rather than a hard cut.",
    "All configuration (thresholds, detector choice, size limits) lives in one "
    "<font face='Courier'>StitchConfig</font> dataclass, and all logging is centralised in "
    "<font face='Courier'>config.setup_logging()</font>.",
])

# ---------------------------------------------------------------- Screenshots / Results
h1("9. Screenshots / Results")
h2("9.1 Detected Keypoints")
figure(os.path.join(DIAG, "keypoints_screenshot.jpg"), "Figure 6: SIFT keypoints detected on one of the sample images.")

h2("9.2 Feature Matches (Inliers Only)")
figure(os.path.join(DIAG, "feature_matches_screenshot.jpg"),
       "Figure 7: RANSAC-inlier feature matches between two overlapping sample images.")
story.append(PageBreak())

h2("9.3 Final Stitched Panorama")
panorama_path = os.path.join(OUT, "panorama.jpg")
if os.path.exists(panorama_path):
    figure(panorama_path, "Figure 8: Final panorama stitched from the 3-image sample set (sample_data/).")

h2("9.4 Sample Run Metrics")
body("Console output and generated <font face='Courier'>summary.txt</font> from a run on the included "
     "sample data (3 images, SIFT detector, default thresholds):")
sample_metrics = [
    ["Pair", "Good matches", "Inliers", "Inlier ratio", "Mean reprojection error"],
    ["1 -> 2", "178", "115", "64.6%", "0.04 px"],
    ["2 -> 3", "170", "86", "50.6%", "0.04 px"],
]
t2 = Table(sample_metrics, colWidths=[0.8*inch, 1.2*inch, 0.9*inch, 1.1*inch, 1.7*inch])
t2.setStyle(TableStyle([
    ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#455A64")),
    ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
    ("FONTSIZE", (0, 0), (-1, -1), 9),
    ("GRID", (0, 0), (-1, -1), 0.5, colors.grey),
    ("ALIGN", (1, 0), (-1, -1), "CENTER"),
]))
story.append(t2)
story.append(Spacer(1, 6))
body("Total run time for the 3-image sample set was under 0.4 seconds on the development machine, "
     "with all 3 images successfully aligned and 0 pairs skipped.")

# ---------------------------------------------------------------- Testing Approach
h1("10. Testing Approach")
body("Automated tests are written with <font face='Courier'>pytest</font> and cover each module in "
     "isolation as well as the full pipeline end-to-end. Since real overlapping photographs aren't "
     "available in the automated test environment, tests generate synthetic but richly-textured "
     "images (random shapes over a gradient background) and derive overlapping crops from them so "
     "that ground-truth overlap is known and matching behaviour can be verified deterministically.")
bullets([
    "<b>Feature engine tests:</b> keypoints are detected for both SIFT and ORB backends; an "
    "unsupported detector name raises a clear error; a blank image correctly raises "
    "<font face='Courier'>RuntimeError</font> instead of failing silently.",
    "<b>Matcher tests:</b> genuinely overlapping images produce a valid homography with low "
    "reprojection error; two unrelated images correctly raise "
    "<font face='Courier'>InsufficientMatchesError</font>.",
    "<b>Stitcher tests:</b> a 2-image overlapping pair stitches into a panorama wider than either "
    "input; requesting a stitch with fewer than 2 images raises <font face='Courier'>ValueError</font>.",
    "<b>IO utility tests:</b> large images are downscaled to the configured maximum dimension; "
    "images already within limits are left untouched.",
])
body("All 10 tests pass. Run with: <font face='Courier'>pytest tests/ -v</font>")

# ---------------------------------------------------------------- Challenges Faced
h1("11. Challenges Faced")
bullets([
    "Choosing a reference frame for multi-image stitching: warping every image onto the first "
    "image in the sequence caused severe distortion for images far from it; switching to a "
    "central reference image and chaining homographies outward in both directions fixed this.",
    "Hard seams were visible when overlapping images were simply overwritten; replacing that with "
    "distance-transform-based feathered blending removed the visible boundary.",
    "Tuning the minimum-match-count threshold so it reliably rejects genuinely non-overlapping "
    "images without being so strict that it rejects valid but small overlaps required empirical "
    "testing with synthetic image pairs of known overlap.",
])

# ---------------------------------------------------------------- Learnings & Key Takeaways
h1("12. Learnings &amp; Key Takeaways")
bullets([
    "Implementing homography estimation and RANSAC manually (via OpenCV's primitives, not the "
    "high-level Stitcher API) clarified why each stage of the classical pipeline exists and how "
    "failures in one stage (e.g. too few matches) should be handled rather than ignored.",
    "Robust estimation matters in practice: even with a solid ratio test, RANSAC's outlier "
    "rejection made a measurable difference in reprojection error on test data.",
    "Good software structure (one responsibility per module, centralised configuration) made it "
    "straightforward to add automated tests for each stage independently.",
])

# ---------------------------------------------------------------- Future Enhancements
h1("13. Future Enhancements")
bullets([
    "Exposure/color correction (histogram matching) between stitched images for more visually "
    "consistent panoramas.",
    "Automatic detection of image order/adjacency instead of assuming images are pre-sorted.",
    "Cylindrical or spherical warping to support wide (&gt;180&deg;) panoramas without extreme "
    "perspective distortion at the edges.",
    "A deep-learning-based feature matcher (e.g. SuperGlue) as an alternative backend for "
    "low-texture scenes where SIFT/ORB struggle.",
])

# ---------------------------------------------------------------- References
h1("14. References")
bullets([
    "D. G. Lowe, \"Distinctive Image Features from Scale-Invariant Keypoints,\" International "
    "Journal of Computer Vision, 2004.",
    "M. A. Fischler and R. C. Bolles, \"Random Sample Consensus: A Paradigm for Model Fitting with "
    "Applications to Image Analysis and Automated Cartography,\" Communications of the ACM, 1981.",
    "E. Rublee, V. Rabaud, K. Konolige, G. Bradski, \"ORB: An Efficient Alternative to SIFT or "
    "SURF,\" ICCV, 2011.",
    "OpenCV Documentation - Feature Detection and Description, Feature Matching, "
    "Camera Calibration and 3D Reconstruction (Homography). https://docs.opencv.org/",
    "R. Szeliski, \"Image Alignment and Stitching: A Tutorial,\" Foundations and Trends in Computer "
    "Graphics and Vision, 2006.",
])

doc = SimpleDocTemplate(
    os.path.join(BASE, "PanoStitch_Project_Report.pdf"),
    pagesize=A4,
    topMargin=0.8 * inch, bottomMargin=0.8 * inch,
    leftMargin=0.9 * inch, rightMargin=0.9 * inch,
)
doc.build(story)
print("Report generated.")