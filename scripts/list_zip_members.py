#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import zipfile
from pathlib import Path


def list_members(archive: Path) -> None:
    try:
        with zipfile.ZipFile(archive) as zf:
            for name in zf.namelist():
                print(name)
    except NotImplementedError:
        unzip = shutil.which("unzip")
        if not unzip:
            raise SystemExit("Archive member listing requires unzip when Python zipfile cannot read the archive.")
        result = subprocess.run(
            [unzip, "-Z1", str(archive)],
            check=True,
            text=True,
            capture_output=True,
        )
        print(result.stdout, end="")


def main() -> int:
    parser = argparse.ArgumentParser(description="List ZIP members, including Deflate64 archives.")
    parser.add_argument("archive")
    args = parser.parse_args()
    list_members(Path(args.archive))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
