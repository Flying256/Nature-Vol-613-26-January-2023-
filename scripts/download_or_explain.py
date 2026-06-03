#!/usr/bin/env python3
from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

from nature613_repro.resources import resources_from_manifest


def run_curl(url: str, output: Path) -> int:
    command = [
        "curl",
        "-L",
        "--continue-at",
        "-",
        "--fail",
        "--retry",
        "3",
        "--retry-delay",
        "5",
        "--show-error",
        "--user-agent",
        "Mozilla/5.0",
        "-o",
        str(output),
        url,
    ]
    return subprocess.call(command)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Attempt official downloads, then print manual placement instructions if blocked."
    )
    parser.add_argument("--manifest", default="manifests/official_resources.yml")
    parser.add_argument("--official-dir", default="official")
    parser.add_argument("--attempt", action="store_true", help="Try curl download endpoints.")
    args = parser.parse_args()

    official_dir = Path(args.official_dir)
    official_dir.mkdir(parents=True, exist_ok=True)

    resources = resources_from_manifest(Path(args.manifest))
    for resource in resources:
        archive = official_dir / resource.expected_archive_name
        aliases = [official_dir / alias for alias in resource.archive_aliases]
        present_archive = next((path for path in [archive] + aliases if path.exists()), None)
        print(f"{resource.key}: {resource.title}")
        print(f"  DOI: {resource.doi}")
        print(f"  Landing page: {resource.landing_url}")
        if resource.file_id:
            print(f"  Figshare file id: {resource.file_id}")
        if resource.direct_download_url:
            print(f"  Direct download URL: {resource.direct_download_url}")
        if resource.md5:
            print(f"  Expected MD5: {resource.md5}")
        print(f"  Expected local archive: {archive}")
        if resource.archive_aliases:
            print(f"  Accepted aliases: {', '.join(resource.archive_aliases)}")
        if present_archive:
            print(f"  Present: yes ({present_archive.stat().st_size} bytes at {present_archive})")
            continue
        print("  Present: no")
        if args.attempt:
            endpoint = (
                resource.direct_download_url
                or f"https://figshare.manchester.ac.uk/ndownloader/articles/{resource.doi.split('/')[-1]}/versions/1"
            )
            print(f"  Trying endpoint: {endpoint}")
            code = run_curl(endpoint, archive)
            if code == 0 and archive.exists() and archive.stat().st_size > 1024:
                print(f"  Downloaded: {archive}")
                continue
            if archive.exists() and archive.stat().st_size <= 1024:
                archive.unlink()
            print("  Automatic download failed or was blocked.")
        print("  Manual step: open the landing page in a browser, download the archive,")
        print(f"  then place it at {archive}.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
