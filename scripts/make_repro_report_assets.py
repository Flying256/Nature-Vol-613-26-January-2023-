from __future__ import annotations

import csv
import json
import re
from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np


ROOT = Path(__file__).resolve().parents[1]
LOG_PATH = ROOT / "outputs" / "full_train.log"
OUT_DIR = ROOT / "outputs" / "report_assets"

EPOCH_RE = re.compile(r"Epoch\s+(\d+)/(\d+)")
ANSI_RE = re.compile(r"\x1b\[[0-9;?]*[A-Za-z]")
METRIC_RE = re.compile(
    r"(?P<seconds>\d+)s\s+[^-]*?step\s+-\s+"
    r"categorical_accuracy:\s+(?P<acc>[0-9.]+)\s+-\s+"
    r"loss:\s+(?P<loss>[0-9.]+)\s+-\s+"
    r"val_categorical_accuracy:\s+(?P<val_acc>[0-9.]+)\s+-\s+"
    r"val_loss:\s+(?P<val_loss>[0-9.]+)"
)


def parse_training_log() -> list[dict[str, float]]:
    records: list[dict[str, float]] = []
    current_epoch: int | None = None
    total_epochs: int | None = None

    with LOG_PATH.open("r", encoding="utf-8", errors="ignore") as handle:
        for raw_line in handle:
            line = ANSI_RE.sub("", raw_line).replace("\b", "").replace("\r", "").strip()
            epoch_match = EPOCH_RE.search(line)
            if epoch_match:
                current_epoch = int(epoch_match.group(1))
                total_epochs = int(epoch_match.group(2))

            metric_match = METRIC_RE.search(line)
            if metric_match and current_epoch is not None:
                records.append(
                    {
                        "epoch": float(current_epoch),
                        "target_epochs": float(total_epochs or 0),
                        "seconds": float(metric_match.group("seconds")),
                        "categorical_accuracy": float(metric_match.group("acc")),
                        "loss": float(metric_match.group("loss")),
                        "val_categorical_accuracy": float(metric_match.group("val_acc")),
                        "val_loss": float(metric_match.group("val_loss")),
                    }
                )
    return records


def save_records(records: list[dict[str, float]]) -> dict[str, float | int]:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    csv_path = OUT_DIR / "training_metrics.csv"
    with csv_path.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.DictWriter(handle, fieldnames=list(records[0]))
        writer.writeheader()
        writer.writerows(records)

    val_accs = np.array([r["val_categorical_accuracy"] for r in records])
    val_losses = np.array([r["val_loss"] for r in records])
    best_acc_idx = int(np.argmax(val_accs))
    best_loss_idx = int(np.argmin(val_losses))
    summary = {
        "epochs_recorded": len(records),
        "final_epoch": int(records[-1]["epoch"]),
        "final_train_accuracy": records[-1]["categorical_accuracy"],
        "final_train_loss": records[-1]["loss"],
        "final_val_accuracy": records[-1]["val_categorical_accuracy"],
        "final_val_loss": records[-1]["val_loss"],
        "best_val_accuracy_epoch": int(records[best_acc_idx]["epoch"]),
        "best_val_accuracy": float(val_accs[best_acc_idx]),
        "best_val_loss_epoch": int(records[best_loss_idx]["epoch"]),
        "best_val_loss": float(val_losses[best_loss_idx]),
        "mean_epoch_seconds": float(np.mean([r["seconds"] for r in records])),
        "total_training_hours_from_logged_epochs": float(np.sum([r["seconds"] for r in records]) / 3600),
    }
    with (OUT_DIR / "training_summary.json").open("w", encoding="utf-8") as handle:
        json.dump(summary, handle, ensure_ascii=False, indent=2)
    return summary


def plot_curves(records: list[dict[str, float]]) -> None:
    epochs = np.array([r["epoch"] for r in records])
    train_acc = np.array([r["categorical_accuracy"] for r in records])
    val_acc = np.array([r["val_categorical_accuracy"] for r in records])
    train_loss = np.array([r["loss"] for r in records])
    val_loss = np.array([r["val_loss"] for r in records])

    plt.style.use("seaborn-v0_8-whitegrid")

    fig, ax = plt.subplots(figsize=(8.2, 4.6), dpi=180)
    ax.plot(epochs, train_acc, color="#2563eb", linewidth=1.3, label="Training accuracy")
    ax.plot(epochs, val_acc, color="#dc2626", linewidth=1.3, label="Validation accuracy")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Categorical accuracy")
    ax.set_title("Nature 613 reproduction: accuracy by epoch")
    ax.legend(frameon=False, loc="lower right")
    ax.set_ylim(0, max(0.9, float(val_acc.max()) + 0.03))
    fig.tight_layout()
    fig.savefig(OUT_DIR / "accuracy_curve.png")
    plt.close(fig)

    fig, ax = plt.subplots(figsize=(8.2, 4.6), dpi=180)
    ax.plot(epochs, train_loss, color="#2563eb", linewidth=1.3, label="Training loss")
    ax.plot(epochs, val_loss, color="#dc2626", linewidth=1.3, label="Validation loss")
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Categorical cross-entropy")
    ax.set_title("Nature 613 reproduction: loss by epoch")
    ax.legend(frameon=False, loc="upper right")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "loss_curve.png")
    plt.close(fig)

    window = min(50, len(records))
    kernel = np.ones(window) / window
    smooth_val = np.convolve(val_acc, kernel, mode="valid")
    smooth_epochs = epochs[window - 1 :]
    fig, ax = plt.subplots(figsize=(8.2, 4.6), dpi=180)
    ax.plot(epochs, val_acc, color="#94a3b8", linewidth=0.7, label="Validation accuracy")
    ax.plot(smooth_epochs, smooth_val, color="#0f766e", linewidth=1.8, label=f"{window}-epoch moving average")
    best_idx = int(np.argmax(val_acc))
    ax.scatter([epochs[best_idx]], [val_acc[best_idx]], color="#dc2626", s=28, zorder=4)
    ax.annotate(
        f"Best: epoch {int(epochs[best_idx])}, {val_acc[best_idx]:.4f}",
        xy=(epochs[best_idx], val_acc[best_idx]),
        xytext=(epochs[best_idx] - 520, val_acc[best_idx] + 0.025),
        arrowprops={"arrowstyle": "->", "color": "#334155", "lw": 0.8},
        fontsize=8.5,
    )
    ax.set_xlabel("Epoch")
    ax.set_ylabel("Validation accuracy")
    ax.set_title("Validation accuracy trend and best checkpoint")
    ax.legend(frameon=False, loc="lower right")
    fig.tight_layout()
    fig.savefig(OUT_DIR / "validation_accuracy_trend.png")
    plt.close(fig)


def main() -> None:
    records = parse_training_log()
    if not records:
        raise SystemExit(f"No epoch metrics parsed from {LOG_PATH}")
    summary = save_records(records)
    plot_curves(records)
    print(json.dumps(summary, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
