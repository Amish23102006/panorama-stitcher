from setuptools import setup, find_packages

setup(
    name="panostitch",
    version="1.0.0",
    description="Feature-based image stitching pipeline (SIFT/ORB + RANSAC homography).",
    package_dir={"": "src"},
    packages=find_packages(where="src"),
    install_requires=[
        "opencv-contrib-python>=4.8.0",
        "numpy>=1.24.0",
    ],
    entry_points={
        "console_scripts": [
            "panostitch=panostitch.cli:main",
        ],
    },
    python_requires=">=3.9",
)