#!/usr/bin/env python3
from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Guarded entrypoint for Nature 613 full training."
    )
    parser.add_argument("--dry-run", action="store_true", help="Validate paths without launching training.")
    parser.add_argument("--train-script", default="official/train.py", help="Path to the official train.py.")
    parser.add_argument("--data-dir", default="Data", help="Mounted training/validation/test data directory.")
    parser.add_argument("--output-dir", default="outputs", help="Directory for training outputs.")
    args, passthrough = parser.parse_known_args()

    if os.environ.get("NATURE613_ALLOW_TRAINING") != "1":
        print(
            "Refusing to launch training. Set NATURE613_ALLOW_TRAINING=1 explicitly "
            "on the GPU machine after mounting the official TrainValTest data.",
            file=sys.stderr,
        )
        return 2

    train_script = Path(args.train_script)
    data_dir = Path(args.data_dir)
    output_dir = Path(args.output_dir)
    output_dir.mkdir(parents=True, exist_ok=True)

    if args.dry_run:
        print("Dry run: training guard passed.")
        print(f"Train script: {train_script}")
        print(f"Data directory: {data_dir}")
        print(f"Output directory: {output_dir}")
        return 0

    if not train_script.exists():
        print(f"Missing train script: {train_script}", file=sys.stderr)
        return 3
    if not data_dir.exists():
        print(f"Missing mounted data directory: {data_dir}", file=sys.stderr)
        return 4

    command = [sys.executable, str(train_script), *passthrough]
    return subprocess.call(command)


if __name__ == "__main__":
    raise SystemExit(main())
