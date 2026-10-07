"""Export the locally downloaded Olivetti Faces dataset as labelled image files.

Research/demo data only. Do not use it as a missing-person dataset or for
operational identification.
"""

from __future__ import annotations

import csv
from pathlib import Path

import numpy as np
from sklearn.datasets import fetch_olivetti_faces


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_HOME = PROJECT_ROOT / "data" / "benchmark"
OUTPUT_DIR = DATA_HOME / "olivetti_images"
MANIFEST_PATH = OUTPUT_DIR / "manifest.csv"


def write_pgm(path: Path, image: np.ndarray) -> None:
    """Write an 8-bit grayscale Portable Graymap without extra packages."""
    pixels = np.clip(image * 255, 0, 255).astype(np.uint8)
    height, width = pixels.shape
    path.write_bytes(f"P5\n{width} {height}\n255\n".encode("ascii") + pixels.tobytes())


def main() -> None:
    dataset = fetch_olivetti_faces(data_home=DATA_HOME, download_if_missing=False)
    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

    with MANIFEST_PATH.open("w", newline="", encoding="utf-8") as manifest:
        writer = csv.writer(manifest)
        writer.writerow(["image_path", "person_id", "image_number"])
        for index, (image, person_id) in enumerate(zip(dataset.images, dataset.target, strict=True)):
            image_number = index % 10 + 1
            relative_path = Path(f"person_{person_id:02d}") / f"image_{image_number:02d}.pgm"
            destination = OUTPUT_DIR / relative_path
            destination.parent.mkdir(exist_ok=True)
            write_pgm(destination, image)
            writer.writerow([relative_path.as_posix(), f"person_{person_id:02d}", image_number])

    print(f"Exported {len(dataset.images)} labelled images to: {OUTPUT_DIR}")
    print(f"Manifest: {MANIFEST_PATH}")


if __name__ == "__main__":
    main()
