#!/usr/bin/env python3
from __future__ import annotations

from pathlib import Path


REQUIRED_SNIPPETS = [
    "ARG BASE_IMAGE=",
    "FROM ${BASE_IMAGE}",
    "python:3.7-slim-bullseye",
    "python -m pip install --no-deps -e .",
    "tensorflow==2.1.0",
    "protobuf==3.20.3",
    "h5py==2.10.0",
    'VOLUME ["/workspace/Data", "/workspace/official", "/workspace/outputs"]',
    'CMD ["python", "scripts/inspect_environment.py"]',
]


def main() -> int:
    dockerfile = Path("docker/Dockerfile")
    text = dockerfile.read_text()
    missing = [snippet for snippet in REQUIRED_SNIPPETS if snippet not in text]
    if missing:
        print("Dockerfile static check failed. Missing snippets:")
        for snippet in missing:
            print(f"  - {snippet}")
        return 2
    print("Dockerfile static check passed.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
