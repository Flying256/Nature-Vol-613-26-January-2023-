#!/usr/bin/env python3
from __future__ import annotations

import argparse
from pathlib import Path

from nature613_repro.resources import Resource, resources_from_manifest
from nature613_repro.zip_subset import (
    FileRangeReader,
    HttpRangeReader,
    HybridRangeReader,
    build_subset_zip,
    read_zip_central_directory,
)


def resolve_dataset_resource(manifest_path: Path) -> Resource:
    for resource in resources_from_manifest(manifest_path):
        if resource.key == "dataset_package":
            if not resource.direct_download_url:
                raise SystemExit("dataset_package direct_download_url not found in manifest")
            return resource
    raise SystemExit("dataset_package not found in manifest")


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Fetch only the official Nature 613 standard test-set members into a smaller ZIP."
    )
    parser.add_argument("--archive", required=True, help="Partially or fully downloaded official ZIP archive.")
    parser.add_argument("--url", help="Direct download URL used for HTTP Range requests.")
    parser.add_argument("--manifest", default="manifests/official_resources.yml")
    parser.add_argument("--dataset-stem", default="M1_M20_train_val_test_set")
    parser.add_argument("--output-zip", required=True, help="Output ZIP containing README and x1/x2/y test members.")
    args = parser.parse_args()

    archive_path = Path(args.archive)
    if not archive_path.exists():
        raise SystemExit("Missing archive: {}".format(archive_path))

    local_size = archive_path.stat().st_size
    resource = resolve_dataset_resource(Path(args.manifest))
    url = args.url or resource.direct_download_url
    local_reader = FileRangeReader(archive_path)
    remote_reader = HttpRangeReader(url)
    combined_reader = HybridRangeReader(local_reader, local_size, remote_reader)
    entries = read_zip_central_directory(combined_reader, resource.size_bytes)
    subset_names = [
        "README",
        "x1_test_{}.pkl".format(args.dataset_stem),
        "x2_test_{}.pkl".format(args.dataset_stem),
        "y_test_{}.pkl".format(args.dataset_stem),
    ]
    output_zip = Path(args.output_zip)
    build_subset_zip(combined_reader, entries, subset_names, output_zip)
    print("saved_subset_zip: {}".format(output_zip))
    for name in subset_names:
        print("included_member: {}".format(name))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
