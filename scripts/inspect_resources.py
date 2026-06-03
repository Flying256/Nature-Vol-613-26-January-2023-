#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from nature613_repro.resources import missing_expected_contents, resources_from_manifest


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect Nature 613 official resource state.")
    parser.add_argument("--manifest", default="manifests/official_resources.yml")
    parser.add_argument("--official-dir", default="official")
    args = parser.parse_args()

    root = Path(args.official_dir)
    for resource in resources_from_manifest(Path(args.manifest)):
        archive = root / resource.expected_archive_name
        aliases = [root / alias for alias in resource.archive_aliases]
        present_archive = next((path for path in [archive] + aliases if path.exists()), None)
        unpacked = root / resource.expected_archive_name.replace(".zip", "")
        print(f"{resource.key}: {resource.title}")
        print(f"  DOI: {resource.doi}")
        print(f"  Landing URL: {resource.landing_url}")
        if resource.file_id:
            print(f"  Figshare file id: {resource.file_id}")
        if resource.direct_download_url:
            print(f"  Direct download URL: {resource.direct_download_url}")
        if resource.md5:
            print(f"  Expected MD5: {resource.md5}")
        print(f"  Expected archive: {archive}")
        if resource.archive_aliases:
            print(f"  Accepted aliases: {', '.join(resource.archive_aliases)}")
        print(f"  Expected size: {resource.size_bytes} bytes")
        print(f"  Docker policy: {resource.docker_policy}")
        if present_archive:
            print(f"  Archive present: yes ({present_archive.stat().st_size} bytes at {present_archive})")
        else:
            print("  Archive present: no")
        if unpacked.exists():
            missing = missing_expected_contents(unpacked, resource.expected_contents)
            if missing:
                print(f"  Unpacked directory present, missing expected entries: {', '.join(missing)}")
            else:
                print("  Unpacked directory present, expected entries found")
        else:
            print(f"  Unpacked directory present: no ({unpacked})")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
