import numpy as np

from nature613_repro.metrics import confusion_matrix, grouped_predictions, mean_group_size, top_k_accuracy


def test_top_k_accuracy_counts_expected_label_within_k_predictions():
    probabilities = np.array(
        [
            [0.80, 0.10, 0.10],
            [0.20, 0.70, 0.10],
            [0.60, 0.30, 0.10],
        ]
    )
    labels = np.array([0, 2, 1])

    assert top_k_accuracy(probabilities, labels, k=1) == 1 / 3
    assert top_k_accuracy(probabilities, labels, k=2) == 2 / 3


def test_grouped_predictions_accumulates_until_confidence_threshold():
    probabilities = np.array(
        [
            [0.70, 0.20, 0.10],
            [0.40, 0.35, 0.25],
            [0.991, 0.005, 0.004],
        ]
    )

    groups = grouped_predictions(probabilities, threshold=0.90)

    assert groups == [[0, 1], [0, 1, 2], [0]]


def test_grouped_prediction_keeps_true_label_when_covered_by_threshold():
    probabilities = np.array(
        [
            [0.55, 0.44, 0.01],
            [0.34, 0.33, 0.33],
        ]
    )
    labels = np.array([1, 2])

    groups = grouped_predictions(probabilities, threshold=0.99)
    covered = [label in group for label, group in zip(labels, groups)]

    assert covered == [True, True]


def test_mean_group_size_reports_average_candidate_count():
    probabilities = np.array(
        [
            [0.991, 0.005, 0.004],
            [0.40, 0.35, 0.25],
        ]
    )

    assert mean_group_size(probabilities, threshold=0.99) == 2.0


def test_confusion_matrix_counts_true_rows_and_predicted_columns():
    labels = np.array([0, 0, 1, 2])
    predictions = np.array([0, 1, 1, 0])

    matrix = confusion_matrix(labels, predictions, num_classes=3)

    assert matrix.tolist() == [
        [1, 1, 0],
        [0, 1, 0],
        [1, 0, 0],
    ]
