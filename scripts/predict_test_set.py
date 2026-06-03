#!/usr/bin/env python3
from __future__ import annotations

import argparse
import pickle
from pathlib import Path
from typing import Any, Optional, Tuple

import numpy as np

from nature613_repro.evaluate import summarize_probabilities


def load_pickle(path: Path) -> np.ndarray:
    with path.open("rb") as handle:
        return pickle.load(handle)


def select_test_variant(x2_payload: Any, timepoints: Optional[int], noise: Optional[int]) -> np.ndarray:
    if isinstance(x2_payload, np.ndarray):
        return x2_payload
    if not isinstance(x2_payload, dict):
        raise SystemExit("Unsupported x2_test payload type: {}".format(type(x2_payload).__name__))

    selected_timepoints = 20 if timepoints is None else timepoints
    if selected_timepoints not in x2_payload:
        raise SystemExit(
            "Requested timepoints {} not found in x2_test. Available: {}".format(
                selected_timepoints,
                sorted(x2_payload),
            )
        )
    branch = x2_payload[selected_timepoints]
    if isinstance(branch, np.ndarray):
        return branch
    if not isinstance(branch, dict):
        raise SystemExit(
            "Unsupported x2_test branch type for timepoints {}: {}".format(
                selected_timepoints,
                type(branch).__name__,
            )
        )
    selected_noise = 1 if noise is None else noise
    if selected_noise not in branch:
        raise SystemExit(
            "Requested noise {} not found for timepoints {}. Available: {}".format(
                selected_noise,
                selected_timepoints,
                sorted(branch),
            )
        )
    return branch[selected_noise]
def load_inputs_from_pickle_dir(
    data_dir: Path,
    dataset_stem: str,
    timepoints: Optional[int],
    noise: Optional[int],
) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    input_1_path = data_dir / "x1_test_{}.pkl".format(dataset_stem)
    input_2_path = data_dir / "x2_test_{}.pkl".format(dataset_stem)
    labels_path = data_dir / "y_test_{}.pkl".format(dataset_stem)
    for path in [input_1_path, input_2_path, labels_path]:
        if not path.exists():
            raise SystemExit("Missing required file: {}".format(path))
    x2_payload = load_pickle(input_2_path)
    return load_pickle(input_1_path), select_test_variant(x2_payload, timepoints, noise), load_pickle(labels_path)


def load_inputs_from_npy(input_1_path: Path, input_2_path: Path, labels_path: Path) -> Tuple[np.ndarray, np.ndarray, np.ndarray]:
    for path in [input_1_path, input_2_path, labels_path]:
        if not path.exists():
            raise SystemExit("Missing required file: {}".format(path))
    return (
        np.load(input_1_path, allow_pickle=False),
        np.load(input_2_path, allow_pickle=False),
        np.load(labels_path, allow_pickle=False),
    )


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Run an official Keras model on explicit Nature 613 test arrays."
    )
    parser.add_argument("--model", required=True, help="Path to an official .h5 model.")
    parser.add_argument("--input-1", help=".npy file for input_1 catalyst loadings.")
    parser.add_argument("--input-2", help=".npy file for input_2 kinetic profiles.")
    parser.add_argument("--labels", help=".npy file for class labels or one-hot labels.")
    parser.add_argument("--data-dir", help="Official directory containing x1_test_*.pkl, x2_test_*.pkl, y_test_*.pkl.")
    parser.add_argument("--dataset-stem", default="M1_M20_train_val_test_set")
    parser.add_argument("--timepoints", type=int, help="Select official x2_test[timepoints][noise] branch, default 20.")
    parser.add_argument("--noise", type=int, help="Select official x2_test[timepoints][noise] branch, default 1.")
    parser.add_argument("--output", required=True, help="Where to save predicted probabilities as .npy.")
    parser.add_argument("--labels-output", help="Optional .npy path where loaded labels should be saved.")
    parser.add_argument("--batch-size", type=int, default=2048)
    args = parser.parse_args()

    model_path = Path(args.model)
    output_path = Path(args.output)
    if not model_path.exists():
        raise SystemExit("Missing required file: {}".format(model_path))
    if args.data_dir:
        input_1, input_2, labels = load_inputs_from_pickle_dir(
            Path(args.data_dir),
            args.dataset_stem,
            args.timepoints,
            args.noise,
        )
    else:
        if not (args.input_1 and args.input_2 and args.labels):
            raise SystemExit("Provide either --data-dir or all of --input-1, --input-2, and --labels.")
        input_1, input_2, labels = load_inputs_from_npy(
            Path(args.input_1), Path(args.input_2), Path(args.labels)
        )

    from tensorflow.keras.models import load_model

    model = load_model(model_path, compile=False)

    probabilities = model.predict([input_1, input_2], batch_size=args.batch_size)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    np.save(output_path, probabilities)
    if args.labels_output:
        labels_output_path = Path(args.labels_output)
        labels_output_path.parent.mkdir(parents=True, exist_ok=True)
        np.save(labels_output_path, labels)

    summary = summarize_probabilities(probabilities, labels)
    print("samples: {}".format(summary.samples))
    print("top1_accuracy: {:.6f}".format(summary.top1_accuracy))
    print("top3_accuracy: {:.6f}".format(summary.top3_accuracy))
    print("grouped_99_accuracy: {:.6f}".format(summary.grouped_99_accuracy))
    print("mean_group_size_99: {:.6f}".format(summary.mean_group_size_99))
    print("saved_probabilities: {}".format(output_path))
    if args.labels_output:
        print("saved_labels: {}".format(args.labels_output))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
