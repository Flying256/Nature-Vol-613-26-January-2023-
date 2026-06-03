import numpy as np

from nature613_repro.evaluate import labels_from_one_hot, summarize_probabilities
from scripts.predict_test_set import select_test_variant


def test_labels_from_one_hot_converts_to_class_indices():
    labels = np.array([[1, 0, 0], [0, 0, 1], [0, 1, 0]])

    assert labels_from_one_hot(labels).tolist() == [0, 2, 1]


def test_labels_from_column_vector_keeps_scalar_class_ids():
    labels = np.array([[9], [3], [0]])

    assert labels_from_one_hot(labels).tolist() == [9, 3, 0]


def test_summarize_probabilities_reports_expected_metrics():
    probabilities = np.array(
        [
            [0.995, 0.003, 0.002],
            [0.005, 0.600, 0.395],
            [0.50, 0.30, 0.20],
        ]
    )
    labels = np.array([0, 2, 1])

    summary = summarize_probabilities(probabilities, labels)

    assert summary.samples == 3
    assert summary.top1_accuracy == 1 / 3
    assert summary.top3_accuracy == 1.0
    assert summary.grouped_99_accuracy == 1.0
    assert summary.mean_group_size_99 == 2.0
    assert summary.confusion_matrix.tolist() == [
        [1, 0, 0],
        [1, 0, 0],
        [0, 1, 0],
    ]


def test_select_test_variant_uses_standard_branch_by_default():
    standard = np.ones((2, 21, 12))
    noisy = np.ones((2, 7, 12)) * 2
    short = np.ones((2, 3, 12)) * 3
    nested = {
        20: {1: standard},
        6: {0: noisy},
        2: {1: short},
    }

    selected = select_test_variant(nested, None, None)

    assert selected is standard


def test_select_test_variant_can_choose_explicit_timepoints_and_noise():
    standard = np.ones((2, 21, 12))
    noisy = np.ones((2, 7, 12)) * 2
    short = np.ones((2, 3, 12)) * 3
    nested = {
        20: {1: standard},
        6: {0: noisy},
        2: {1: short},
    }

    selected = select_test_variant(nested, 6, 0)

    assert selected is noisy
