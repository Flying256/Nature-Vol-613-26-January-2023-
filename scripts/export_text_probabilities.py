#!/usr/bin/env python3
from __future__ import annotations

import argparse
import csv
import os
import sys
from pathlib import Path


MECHANISMS = ["M{}".format(index) for index in range(1, 21)]


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Export M1-M20 probabilities for an official Nature 613 text kinetics file."
    )
    parser.add_argument("--model-dir", default="official/AI_model_and_files")
    parser.add_argument("--data", default="Data/kinetics.txt")
    parser.add_argument("--model", default="Data/M1_20_model.h5")
    parser.add_argument("--output", required=True)
    parser.add_argument("--s0", type=float, help="Initial substrate concentration for P-only models.")
    parser.add_argument("--columns", nargs="+", help="Override official model input columns.")
    args = parser.parse_args()

    model_dir = Path(args.model_dir).resolve()
    output_path = Path(args.output).resolve()
    if not (model_dir / "utils.py").exists():
        raise SystemExit("Missing official utils.py under {}".format(model_dir))

    os.environ.setdefault("TF_CPP_MIN_LOG_LEVEL", "1")
    os.environ.setdefault("CUDA_VISIBLE_DEVICES", "-1")
    os.environ.setdefault("MPLBACKEND", "Agg")
    os.chdir(str(model_dir))
    sys.path.insert(0, str(model_dir))

    from tensorflow.keras.models import load_model
    from utils import (
        generate_predicted_grouping,
        grouping_index_to_names,
        model_columns,
        predict_from_file,
    )

    model_name = Path(args.model).name
    if args.columns:
        columns = args.columns
    elif model_name in model_columns:
        columns = model_columns[model_name]
    else:
        raise SystemExit("Unknown model columns for {}; pass --columns.".format(model_name))

    model = load_model(args.model, compile=False)
    a0 = args.s0 if args.s0 is not None else False
    probabilities, _, _ = predict_from_file(model, args.data, columns=columns, A0=a0)
    grouping = generate_predicted_grouping(probabilities)
    grouping_names = grouping_index_to_names(sorted(grouping))
    ranked = sorted(range(len(probabilities)), key=lambda index: probabilities[index], reverse=True)

    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=["mechanism", "probability", "rank", "in_group_99"])
        writer.writeheader()
        for mechanism_index, mechanism in enumerate(MECHANISMS):
            writer.writerow(
                {
                    "mechanism": mechanism,
                    "probability": "{:.12g}".format(float(probabilities[mechanism_index])),
                    "rank": ranked.index(mechanism_index) + 1,
                    "in_group_99": str(mechanism_index in grouping).lower(),
                }
            )

    print("saved_probabilities: {}".format(output_path))
    print("top1: {}".format(MECHANISMS[ranked[0]]))
    print("grouped_99: {}".format(" ".join(grouping_names)))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
