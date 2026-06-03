#!/usr/bin/env python3
from __future__ import annotations

import importlib
import sys


def main() -> int:
    print(f"python: {sys.version.split()[0]}")
    missing = []
    for module_name in ["tensorflow", "numpy", "scipy", "pandas", "sklearn"]:
        try:
            module = importlib.import_module(module_name)
        except ModuleNotFoundError:
            missing.append(module_name)
            print(f"{module_name}: missing")
            continue
        version = getattr(module, "__version__", "unknown")
        print(f"{module_name}: {version}")

    if missing:
        print(f"missing modules: {', '.join(missing)}", file=sys.stderr)
        return 5

    import tensorflow as tf

    gpus = tf.config.list_physical_devices("GPU")
    if gpus:
        print("gpu: available")
        for gpu in gpus:
            print(f"  {gpu}")
    else:
        print("gpu: not detected")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
