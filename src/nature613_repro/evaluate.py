from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Dict

import numpy as np

from nature613_repro.metrics import confusion_matrix, grouped_accuracy, mean_group_size, top_k_accuracy


@dataclass(frozen=True)
class EvaluationSummary:
    samples: int
    top1_accuracy: float
    top3_accuracy: float
    grouped_99_accuracy: float
    mean_group_size_99: float
    confusion_matrix: np.ndarray


def labels_from_one_hot(one_hot: np.ndarray) -> np.ndarray:
    arr = np.asarray(one_hot)
    if arr.ndim == 1:
        return arr.astype(int)
    if arr.ndim == 2 and arr.shape[1] == 1:
        return arr[:, 0].astype(int)
    if arr.ndim != 2:
        raise ValueError("labels must be a 1D class array or 2D one-hot array")
    return np.argmax(arr, axis=1)


def summarize_probabilities(probabilities: np.ndarray, labels: np.ndarray) -> EvaluationSummary:
    probs = np.asarray(probabilities)
    truth = labels_from_one_hot(labels)
    predictions = np.argmax(probs, axis=1)
    return EvaluationSummary(
        samples=int(probs.shape[0]),
        top1_accuracy=top_k_accuracy(probs, truth, k=1),
        top3_accuracy=top_k_accuracy(probs, truth, k=3),
        grouped_99_accuracy=grouped_accuracy(probs, truth, threshold=0.99),
        mean_group_size_99=mean_group_size(probs, threshold=0.99),
        confusion_matrix=confusion_matrix(truth, predictions, num_classes=probs.shape[1]),
    )


def load_npz_arrays(path: Path) -> Dict[str, np.ndarray]:
    with np.load(path, allow_pickle=False) as data:
        return {key: data[key] for key in data.files}
