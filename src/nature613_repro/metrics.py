from __future__ import annotations

from typing import List, Optional

import numpy as np


def top_k_accuracy(probabilities: np.ndarray, labels: np.ndarray, k: int) -> float:
    """Return the fraction of labels contained in the top-k predicted classes."""
    if k < 1:
        raise ValueError("k must be at least 1")
    probs = np.asarray(probabilities)
    truth = np.asarray(labels)
    if probs.ndim != 2:
        raise ValueError("probabilities must be a 2D array")
    if truth.ndim != 1 or truth.shape[0] != probs.shape[0]:
        raise ValueError("labels must be a 1D array matching probability rows")

    top = np.argsort(probs, axis=1)[:, -k:]
    return float(np.mean([label in row for label, row in zip(truth, top)]))


def grouped_predictions(probabilities: np.ndarray, threshold: float = 0.99) -> List[List[int]]:
    """Group descending-probability mechanisms until cumulative confidence is met."""
    if not 0 < threshold <= 1:
        raise ValueError("threshold must be in the interval (0, 1]")
    probs = np.asarray(probabilities)
    if probs.ndim != 2:
        raise ValueError("probabilities must be a 2D array")

    groups: List[List[int]] = []
    for row in probs:
        order = np.argsort(row)[::-1]
        cumulative = 0.0
        group: List[int] = []
        for index in order:
            group.append(int(index))
            cumulative += float(row[index])
            if cumulative + 1e-12 >= threshold:
                break
        groups.append(group)
    return groups


def grouped_accuracy(probabilities: np.ndarray, labels: np.ndarray, threshold: float = 0.99) -> float:
    groups = grouped_predictions(probabilities, threshold=threshold)
    truth = np.asarray(labels)
    if truth.ndim != 1 or truth.shape[0] != len(groups):
        raise ValueError("labels must be a 1D array matching probability rows")
    return float(np.mean([int(label) in group for label, group in zip(truth, groups)]))


def mean_group_size(probabilities: np.ndarray, threshold: float = 0.99) -> float:
    groups = grouped_predictions(probabilities, threshold=threshold)
    return float(np.mean([len(group) for group in groups]))


def confusion_matrix(labels: np.ndarray, predictions: np.ndarray, num_classes: Optional[int] = None) -> np.ndarray:
    truth = np.asarray(labels)
    pred = np.asarray(predictions)
    if truth.ndim != 1 or pred.ndim != 1 or truth.shape[0] != pred.shape[0]:
        raise ValueError("labels and predictions must be matching 1D arrays")
    if num_classes is None:
        num_classes = int(max(np.max(truth), np.max(pred))) + 1
    matrix = np.zeros((num_classes, num_classes), dtype=int)
    for label, prediction in zip(truth.astype(int), pred.astype(int)):
        matrix[label, prediction] += 1
    return matrix
