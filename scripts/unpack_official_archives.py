#!/usr/bin/env python3
from __future__ import annotations

import argparse
import shutil
import subprocess
import zipfile
from pathlib import Path
from typing import List

from nature613_repro.resources import missing_expected_contents, resources_from_manifest


def unpack_zip(archive: Path, destination: Path) -> None:
    destination.mkdir(parents=True, exist_ok=True)
    try:
        with zipfile.ZipFile(archive) as zf:
            zf.extractall(destination)
    except NotImplementedError as exc:
        unzip = shutil.which("unzip")
        if not unzip:
            raise RuntimeError(
                "Archive uses a compression method unsupported by Python zipfile; install unzip."
            ) from exc
        subprocess.run([unzip, "-q", "-o", str(archive), "-d", str(destination)], check=True)


def find_archive(official_dir: Path, expected_name: str, aliases: List[str]) -> Path:
    for archive_name in [expected_name] + list(aliases):
        archive = official_dir / archive_name
        if archive.exists():
            return archive
    return official_dir / expected_name


def main() -> int:
    parser = argparse.ArgumentParser(description="Unpack and lightly verify official Nature 613 archives.")
    parser.add_argument("--manifest", default="manifests/official_resources.yml")
    parser.add_argument("--official-dir", default="official")
    parser.add_argument("--resource", help="Only unpack one manifest resource key, for example model_package.")
    args = parser.parse_args()

    official_dir = Path(args.official_dir)
    exit_code = 0
    for resource in resources_from_manifest(Path(args.manifest)):
        if args.resource and resource.key != args.resource:
            continue
        archive = find_archive(official_dir, resource.expected_archive_name, resource.archive_aliases)
        destination = official_dir / resource.expected_archive_name.replace(".zip", "")
        print(f"{resource.key}: {archive}")
        if not archive.exists():
            print(f"  Missing archive. Download it from {resource.landing_url}")
            exit_code = 2
            continue
        print(f"  Unpacking to {destination}")
        unpack_zip(archive, destination)
        missing = missing_expected_contents(destination, resource.expected_contents)
        if missing:
            print(f"  Missing expected entries after unpack: {', '.join(missing)}")
            exit_code = 3
        else:
            print("  Expected entries found")
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
