from __future__ import annotations

import json
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "outputs" / "report_assets"


def main() -> None:
    probabilities = np.load(OUT_DIR / "retrained_test_probabilities.npy", allow_pickle=False)
    labels = np.load(OUT_DIR / "retrained_test_labels.npy", allow_pickle=False).reshape(-1)
    predictions = probabilities.argmax(axis=1)
    classes = [f"M{i}" for i in range(1, 21)]

    matrix = np.zeros((20, 20), dtype=int)
    for truth, pred in zip(labels, predictions):
        matrix[int(truth), int(pred)] += 1
    np.savetxt(OUT_DIR / "confusion_matrix.csv", matrix, delimiter=",", fmt="%d")

    row_sums = matrix.sum(axis=1, keepdims=True)
    normalized = np.divide(matrix, row_sums, out=np.zeros_like(matrix, dtype=float), where=row_sums != 0)

    plt.style.use("seaborn-v0_8-white")
    fig, ax = plt.subplots(figsize=(7.2, 6.4), dpi=180)
    im = ax.imshow(normalized, cmap="Blues", vmin=0, vmax=1)
    ax.set_xticks(np.arange(20))
    ax.set_yticks(np.arange(20))
    ax.set_xticklabels(classes, rotation=45, ha="right", fontsize=7)
    ax.set_yticklabels(classes, fontsize=7)
    ax.set_xlabel("Predicted mechanism")
    ax.set_ylabel("True mechanism")
    ax.set_title("Normalized confusion matrix on 100,000 test examples")
    cbar = fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    cbar.ax.set_ylabel("Class-normalized fraction", rotation=-90, va="bottom")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "confusion_matrix.png")
    plt.close(fig)

    per_class = []
    for i, class_name in enumerate(classes):
        total = int(matrix[i].sum())
        correct = int(matrix[i, i])
        per_class.append(
            {
                "class": class_name,
                "samples": total,
                "correct": correct,
                "accuracy": correct / total if total else 0.0,
            }
        )

    with (OUT_DIR / "per_class_accuracy.json").open("w", encoding="utf-8") as handle:
        json.dump(per_class, handle, indent=2)

    sorted_by_acc = sorted(per_class, key=lambda item: item["accuracy"])
    with (OUT_DIR / "lowest_per_class_accuracy.json").open("w", encoding="utf-8") as handle:
        json.dump(sorted_by_acc[:5], handle, indent=2)
    print(json.dumps({"lowest": sorted_by_acc[:5], "highest": sorted_by_acc[-5:]}, indent=2))


if __name__ == "__main__":
    main()
