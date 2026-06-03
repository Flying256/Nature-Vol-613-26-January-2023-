#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
from pathlib import Path

import numpy as np
import yaml

from nature613_repro.evaluate import summarize_probabilities


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Evaluate standard, noise, and time-point Nature 613 probability variants."
    )
    parser.add_argument(
        "--manifest",
        required=True,
        help="YAML file listing variants with name, probabilities, labels, and optional category.",
    )
    parser.add_argument("--output-dir", required=True, help="Directory for CSV summary and matrices.")
    args = parser.parse_args()

    manifest_path = Path(args.manifest)
    output_dir = Path(args.output_dir)
    if not manifest_path.exists():
        raise SystemExit(f"Missing variant manifest: {manifest_path}")
    output_dir.mkdir(parents=True, exist_ok=True)

    with manifest_path.open("r", encoding="utf-8") as handle:
        manifest = yaml.safe_load(handle) or {}
    variants = manifest.get("variants", [])
    if not variants:
        raise SystemExit("Variant manifest must contain a non-empty variants list.")

    rows = []
    for variant in variants:
        name = variant["name"]
        category = variant.get("category", "standard")
        probabilities_path = Path(variant["probabilities"])
        labels_path = Path(variant["labels"])
        if not probabilities_path.exists():
            raise SystemExit(f"Missing probabilities for {name}: {probabilities_path}")
        if not labels_path.exists():
            raise SystemExit(f"Missing labels for {name}: {labels_path}")

        probabilities = np.load(probabilities_path, allow_pickle=False)
        labels = np.load(labels_path, allow_pickle=False)
        summary = summarize_probabilities(probabilities, labels)
        matrix_path = output_dir / f"{name}_confusion_matrix.csv"
        np.savetxt(matrix_path, summary.confusion_matrix, delimiter=",", fmt="%d")
        rows.append(
            {
                "name": name,
                "category": category,
                "samples": summary.samples,
                "top1_accuracy": f"{summary.top1_accuracy:.6f}",
                "top3_accuracy": f"{summary.top3_accuracy:.6f}",
                "grouped_99_accuracy": f"{summary.grouped_99_accuracy:.6f}",
                "mean_group_size_99": f"{summary.mean_group_size_99:.6f}",
                "confusion_matrix": str(matrix_path),
            }
        )

    summary_path = output_dir / "variant_summary.csv"
    fieldnames = [
        "name",
        "category",
        "samples",
        "top1_accuracy",
        "top3_accuracy",
        "grouped_99_accuracy",
        "mean_group_size_99",
        "confusion_matrix",
    ]
    with summary_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)

    print(f"Wrote summary: {summary_path}")
    print(f"Wrote {len(rows)} confusion_matrix file(s) to: {output_dir}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
