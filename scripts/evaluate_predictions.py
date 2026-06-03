#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

import numpy as np

from nature613_repro.evaluate import summarize_probabilities


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate saved model probabilities against official Nature 613 labels."
    )
    parser.add_argument("--probabilities", required=True, help=".npy file with model probabilities.")
    parser.add_argument("--labels", required=True, help=".npy file with labels or one-hot labels.")
    args = parser.parse_args()

    probabilities_path = Path(args.probabilities)
    labels_path = Path(args.labels)
    if not probabilities_path.exists():
        raise SystemExit(f"Missing probabilities file: {probabilities_path}")
    if not labels_path.exists():
        raise SystemExit(f"Missing labels file: {labels_path}")

    probabilities = np.load(probabilities_path, allow_pickle=False)
    labels = np.load(labels_path, allow_pickle=False)
    summary = summarize_probabilities(probabilities, labels)

    print(f"samples: {summary.samples}")
    print(f"top1_accuracy: {summary.top1_accuracy:.6f}")
    print(f"top3_accuracy: {summary.top3_accuracy:.6f}")
    print(f"grouped_99_accuracy: {summary.grouped_99_accuracy:.6f}")
    print(f"mean_group_size_99: {summary.mean_group_size_99:.6f}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
