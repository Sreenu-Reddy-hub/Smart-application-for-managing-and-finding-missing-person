"""Run a repeatable face-identification benchmark on the Olivetti Faces dataset.

This is a research/demo benchmark only.  It must not be represented as a
missing-person identification result or used to make decisions about people.
"""

from __future__ import annotations

import csv
import json
from pathlib import Path
from time import perf_counter

import numpy as np
from sklearn.datasets import fetch_olivetti_faces
from sklearn.decomposition import PCA
from sklearn.model_selection import StratifiedShuffleSplit
from sklearn.neighbors import KNeighborsClassifier
from sklearn.pipeline import Pipeline


PROJECT_ROOT = Path(__file__).resolve().parents[1]
DATA_HOME = PROJECT_ROOT / "data" / "benchmark"
REPORT_PATH = PROJECT_ROOT / "data" / "benchmark" / "olivetti_benchmark_report.json"
PREDICTIONS_PATH = PROJECT_ROOT / "data" / "benchmark" / "olivetti_test_predictions.csv"
RANDOM_SEED = 2026


def main() -> None:
    dataset = fetch_olivetti_faces(data_home=DATA_HOME, download_if_missing=False)
    splitter = StratifiedShuffleSplit(n_splits=1, test_size=0.5, random_state=RANDOM_SEED)
    train_index, test_index = next(splitter.split(dataset.data, dataset.target))
    x_train, x_test = dataset.data[train_index], dataset.data[test_index]
    y_train, y_test = dataset.target[train_index], dataset.target[test_index]

    model = Pipeline(
        [
            ("pca", PCA(n_components=80, whiten=True, random_state=RANDOM_SEED)),
            ("classifier", KNeighborsClassifier(n_neighbors=1, metric="euclidean")),
        ]
    )

    fit_start = perf_counter()
    model.fit(x_train, y_train)
    fit_time_ms = (perf_counter() - fit_start) * 1000

    # Warm up the pipeline once, then measure each held-out image separately.
    model.predict(x_test[:1])
    predictions: list[int] = []
    inference_times_ms: list[float] = []
    for image in x_test:
        start = perf_counter()
        prediction = int(model.predict(image.reshape(1, -1))[0])
        inference_times_ms.append((perf_counter() - start) * 1000)
        predictions.append(prediction)

    correct = int(np.sum(np.asarray(predictions) == y_test))
    total = int(len(y_test))
    with PREDICTIONS_PATH.open("w", newline="", encoding="utf-8") as prediction_file:
        writer = csv.writer(prediction_file)
        writer.writerow(["dataset_index", "test_image", "expected_person_id", "predicted_person_id", "is_correct", "inference_time_ms"])
        for dataset_index, expected, predicted, time_ms in zip(test_index, y_test, predictions, inference_times_ms, strict=True):
            person_id = int(dataset_index) // 10
            image_number = int(dataset_index) % 10 + 1
            writer.writerow([
                int(dataset_index),
                f"person_{person_id:02d}/image_{image_number:02d}.png",
                f"person_{int(expected):02d}",
                f"person_{predicted:02d}",
                predicted == int(expected),
                round(time_ms, 3),
            ])
    report = {
        "benchmark": "Olivetti Faces held-out identification benchmark",
        "purpose": "research/demo only; not a missing-person performance claim",
        "model": "PCA (80 components) + 1-nearest-neighbour classifier",
        "split": {
            "method": "stratified 50/50 train-test split",
            "random_seed": RANDOM_SEED,
            "enrolled_images": int(len(x_train)),
            "held_out_test_images": total,
            "identities": int(len(np.unique(dataset.target))),
        },
        "identification": {
            "correct_matches": correct,
            "total_test_images": total,
            "top_1_accuracy_percent": round((correct / total) * 100, 2),
        },
        "timing_milliseconds": {
            "model_fit": round(fit_time_ms, 3),
            "average_per_image": round(float(np.mean(inference_times_ms)), 3),
            "median_per_image": round(float(np.median(inference_times_ms)), 3),
            "p95_per_image": round(float(np.percentile(inference_times_ms, 95)), 3),
        },
    }
    REPORT_PATH.write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(report, indent=2))
    print(f"\nSaved report: {REPORT_PATH}")
    print(f"Saved per-image predictions: {PREDICTIONS_PATH}")


if __name__ == "__main__":
    main()
