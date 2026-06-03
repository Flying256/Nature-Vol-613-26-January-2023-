from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional

import yaml


@dataclass(frozen=True)
class Resource:
    key: str
    doi: str
    title: str
    landing_url: str
    file_id: Optional[str]
    direct_download_url: Optional[str]
    expected_archive_name: str
    archive_aliases: List[str]
    md5: Optional[str]
    size_bytes: int
    docker_policy: str
    expected_contents: List[str]


def load_manifest(path: Path) -> Dict[str, Any]:
    return yaml.safe_load(path.read_text())


def resources_from_manifest(path: Path) -> List[Resource]:
    manifest = load_manifest(path)
    resources: List[Resource] = []
    for key, data in manifest.items():
        resources.append(
            Resource(
                key=key,
                doi=data["doi"],
                title=data["title"],
                landing_url=data["landing_url"],
                file_id=data.get("file_id"),
                direct_download_url=data.get("direct_download_url"),
                expected_archive_name=data["expected_archive_name"],
                archive_aliases=list(data.get("archive_aliases", [])),
                md5=data.get("md5"),
                size_bytes=int(data["size_bytes"]),
                docker_policy=data["docker_policy"],
                expected_contents=list(data["expected_contents"]),
            )
        )
    return resources


def missing_expected_contents(root: Path, expected_contents: Iterable[str]) -> List[str]:
    missing: List[str] = []
    existing_names = {path.name for path in root.rglob("*") if path.is_file()}
    for expected in expected_contents:
        if expected in existing_names:
            continue
        if any(path.match(expected) for path in root.rglob("*")):
            continue
        missing.append(expected)
    return missing
