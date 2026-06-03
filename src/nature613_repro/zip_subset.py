from __future__ import annotations

import struct
import subprocess
import zlib
from dataclasses import dataclass
from pathlib import Path
from typing import List, Optional, Sequence


EOCD_SIGNATURE = 0x06054B50
ZIP64_EOCD_SIGNATURE = 0x06064B50
ZIP64_LOCATOR_SIGNATURE = 0x07064B50
CENTRAL_DIRECTORY_SIGNATURE = 0x02014B50
LOCAL_FILE_HEADER_SIGNATURE = 0x04034B50


@dataclass(frozen=True)
class CentralDirectoryEntry:
    name: str
    compression_method: int
    crc32: int
    compressed_size: int
    uncompressed_size: int
    local_header_offset: int
    filename_length: int
    extra_field_length: int
    comment_length: int
    disk_number_start: int
    internal_attributes: int
    external_attributes: int
    local_header_length: int
    local_file_record_length: int
    central_directory_bytes: bytes


class FileRangeReader:
    def __init__(self, path: Path):
        self.path = Path(path)

    def read_range(self, start: int, length: int) -> bytes:
        with self.path.open("rb") as handle:
            handle.seek(start)
            return handle.read(length)


def build_curl_range_command(url: str, start: int, length: int, user_agent: str = "Mozilla/5.0") -> List[str]:
    if length <= 0:
        raise ValueError("length must be positive")
    end = start + length - 1
    return [
        "curl",
        "-L",
        "--fail",
        "--silent",
        "--show-error",
        "--user-agent",
        user_agent,
        "--range",
        "{}-{}".format(start, end),
        url,
        "-o",
        "-",
    ]


class HttpRangeReader:
    def __init__(self, url: str, user_agent: str = "Mozilla/5.0"):
        self.url = url
        self.user_agent = user_agent

    def read_range(self, start: int, length: int) -> bytes:
        if length <= 0:
            return b""
        command = build_curl_range_command(self.url, start, length, self.user_agent)
        return subprocess.check_output(command)


class HybridRangeReader:
    def __init__(self, local: FileRangeReader, local_size: int, remote: Optional[HttpRangeReader] = None):
        self.local = local
        self.local_size = local_size
        self.remote = remote

    def read_range(self, start: int, length: int) -> bytes:
        if length <= 0:
            return b""
        end = start + length
        if end <= self.local_size:
            return self.local.read_range(start, length)
        if start >= self.local_size:
            if not self.remote:
                raise ValueError("Requested remote-only byte range but no remote reader is configured")
            return self.remote.read_range(start, length)
        local_blob = self.local.read_range(start, self.local_size - start)
        if not self.remote:
            raise ValueError("Requested split byte range but no remote reader is configured")
        remote_blob = self.remote.read_range(self.local_size, end - self.local_size)
        return local_blob + remote_blob


def _find_eocd(reader: FileRangeReader, size: int) -> int:
    search_size = min(size, 65535 + 22)
    start = size - search_size
    blob = reader.read_range(start, search_size)
    signature = struct.pack("<I", EOCD_SIGNATURE)
    index = blob.rfind(signature)
    if index < 0:
        raise ValueError("Could not locate ZIP end of central directory")
    return start + index


def _parse_zip64_locator(reader: FileRangeReader, locator_offset: int) -> int:
    blob = reader.read_range(locator_offset, 20)
    signature, _disk_number, zip64_eocd_offset, _total_disks = struct.unpack("<IIQI", blob)
    if signature != ZIP64_LOCATOR_SIGNATURE:
        raise ValueError("Invalid ZIP64 locator signature")
    return zip64_eocd_offset


def _parse_zip64_eocd(reader: FileRangeReader, offset: int) -> tuple[int, int, int]:
    blob = reader.read_range(offset, 56)
    unpacked = struct.unpack("<IQHHIIQQQQ", blob)
    signature = unpacked[0]
    if signature != ZIP64_EOCD_SIGNATURE:
        raise ValueError("Invalid ZIP64 EOCD signature")
    total_entries = unpacked[7]
    central_directory_size = unpacked[8]
    central_directory_offset = unpacked[9]
    return int(total_entries), int(central_directory_size), int(central_directory_offset)


def _parse_eocd(reader: FileRangeReader, offset: int) -> tuple[int, int, int]:
    blob = reader.read_range(offset, 22)
    (
        signature,
        _disk_number,
        _central_directory_disk,
        _entries_on_disk,
        total_entries,
        central_directory_size,
        central_directory_offset,
        comment_length,
    ) = struct.unpack("<IHHHHIIH", blob)
    if signature != EOCD_SIGNATURE:
        raise ValueError("Invalid EOCD signature")
    if comment_length:
        blob = reader.read_range(offset, 22 + comment_length)
        if len(blob) != 22 + comment_length:
            raise ValueError("Truncated EOCD comment")
    if (
        total_entries == 0xFFFF
        or central_directory_size == 0xFFFFFFFF
        or central_directory_offset == 0xFFFFFFFF
    ):
        locator_offset = offset - 20
        zip64_eocd_offset = _parse_zip64_locator(reader, locator_offset)
        return _parse_zip64_eocd(reader, zip64_eocd_offset)
    return int(total_entries), int(central_directory_size), int(central_directory_offset)


def _parse_local_header_length(reader: FileRangeReader, offset: int) -> int:
    blob = reader.read_range(offset, 30)
    if len(blob) != 30:
        raise ValueError("Truncated local file header")
    unpacked = struct.unpack("<IHHHHHIIIHH", blob)
    signature = unpacked[0]
    if signature != LOCAL_FILE_HEADER_SIGNATURE:
        raise ValueError("Invalid local file header signature")
    filename_length = unpacked[9]
    extra_field_length = unpacked[10]
    return 30 + filename_length + extra_field_length


def read_zip_central_directory(reader: FileRangeReader, size: int) -> List[CentralDirectoryEntry]:
    eocd_offset = _find_eocd(reader, size)
    total_entries, central_directory_size, central_directory_offset = _parse_eocd(reader, eocd_offset)
    blob = reader.read_range(central_directory_offset, central_directory_size)
    entries: List[CentralDirectoryEntry] = []
    cursor = 0
    for _ in range(total_entries):
        fixed = blob[cursor : cursor + 46]
        if len(fixed) != 46:
            raise ValueError("Truncated central directory entry")
        unpacked = struct.unpack("<IHHHHHHIIIHHHHHII", fixed)
        signature = unpacked[0]
        if signature != CENTRAL_DIRECTORY_SIGNATURE:
            raise ValueError("Invalid central directory signature")
        compression_method = unpacked[4]
        crc32 = unpacked[7]
        compressed_size = unpacked[8]
        uncompressed_size = unpacked[9]
        filename_length = unpacked[10]
        extra_field_length = unpacked[11]
        comment_length = unpacked[12]
        disk_number_start = unpacked[13]
        internal_attributes = unpacked[14]
        external_attributes = unpacked[15]
        local_header_offset = unpacked[16]
        end = cursor + 46 + filename_length + extra_field_length + comment_length
        entry_bytes = blob[cursor:end]
        name_bytes = blob[cursor + 46 : cursor + 46 + filename_length]
        if compressed_size == 0xFFFFFFFF or uncompressed_size == 0xFFFFFFFF or local_header_offset == 0xFFFFFFFF:
            extra = blob[
                cursor + 46 + filename_length : cursor + 46 + filename_length + extra_field_length
            ]
            compressed_size, uncompressed_size, local_header_offset = _read_zip64_sizes(
                extra,
                compressed_size,
                uncompressed_size,
                local_header_offset,
            )
        local_header_length = _parse_local_header_length(reader, local_header_offset)
        entries.append(
            CentralDirectoryEntry(
                name=name_bytes.decode("utf-8"),
                compression_method=int(compression_method),
                crc32=int(crc32),
                compressed_size=int(compressed_size),
                uncompressed_size=int(uncompressed_size),
                local_header_offset=int(local_header_offset),
                filename_length=int(filename_length),
                extra_field_length=int(extra_field_length),
                comment_length=int(comment_length),
                disk_number_start=int(disk_number_start),
                internal_attributes=int(internal_attributes),
                external_attributes=int(external_attributes),
                local_header_length=int(local_header_length),
                local_file_record_length=int(local_header_length + compressed_size),
                central_directory_bytes=entry_bytes,
            )
        )
        cursor = end
    return entries


def _read_zip64_sizes(
    extra: bytes,
    compressed_size: int,
    uncompressed_size: int,
    local_header_offset: int,
) -> tuple[int, int, int]:
    cursor = 0
    while cursor + 4 <= len(extra):
        header_id, data_size = struct.unpack("<HH", extra[cursor : cursor + 4])
        data = extra[cursor + 4 : cursor + 4 + data_size]
        if header_id == 0x0001:
            data_cursor = 0
            if uncompressed_size == 0xFFFFFFFF:
                uncompressed_size = struct.unpack("<Q", data[data_cursor : data_cursor + 8])[0]
                data_cursor += 8
            if compressed_size == 0xFFFFFFFF:
                compressed_size = struct.unpack("<Q", data[data_cursor : data_cursor + 8])[0]
                data_cursor += 8
            if local_header_offset == 0xFFFFFFFF:
                local_header_offset = struct.unpack("<Q", data[data_cursor : data_cursor + 8])[0]
            return int(compressed_size), int(uncompressed_size), int(local_header_offset)
        cursor += 4 + data_size
    raise ValueError("ZIP64 extra field missing required values")


def _patch_local_header(local_header: bytes, entry: CentralDirectoryEntry) -> bytes:
    header = bytearray(local_header)
    struct.pack_into("<I", header, 14, entry.crc32)
    if entry.compressed_size <= 0xFFFFFFFF and entry.uncompressed_size <= 0xFFFFFFFF:
        struct.pack_into("<I", header, 18, entry.compressed_size)
        struct.pack_into("<I", header, 22, entry.uncompressed_size)
    else:
        struct.pack_into("<I", header, 18, 0xFFFFFFFF)
        struct.pack_into("<I", header, 22, 0xFFFFFFFF)
    return bytes(header)


def _patch_central_directory(entry: CentralDirectoryEntry, new_offset: int) -> bytes:
    record = bytearray(entry.central_directory_bytes)
    needs_zip64 = (
        entry.compressed_size > 0xFFFFFFFF
        or entry.uncompressed_size > 0xFFFFFFFF
        or new_offset > 0xFFFFFFFF
    )
    if needs_zip64:
        raise ValueError("ZIP64 subset output is not implemented")
    struct.pack_into("<I", record, 16, entry.crc32)
    struct.pack_into("<I", record, 20, entry.compressed_size)
    struct.pack_into("<I", record, 24, entry.uncompressed_size)
    struct.pack_into("<I", record, 42, new_offset)
    return bytes(record)


def build_subset_zip(
    reader: FileRangeReader,
    entries: Sequence[CentralDirectoryEntry],
    selected_names: Sequence[str],
    output_path: Path,
) -> None:
    selected = [entry for entry in entries if entry.name in selected_names]
    if len(selected) != len(selected_names):
        missing = [name for name in selected_names if name not in {entry.name for entry in selected}]
        raise ValueError("Missing selected ZIP member(s): {}".format(", ".join(missing)))

    central_records: List[bytes] = []
    cursor = 0
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as handle:
        for entry in selected:
            local_record = reader.read_range(entry.local_header_offset, entry.local_file_record_length)
            header = local_record[: entry.local_header_length]
            payload = local_record[entry.local_header_length :]
            handle.write(_patch_local_header(header, entry))
            handle.write(payload)
            central_records.append(_patch_central_directory(entry, cursor))
            cursor += len(local_record)

        central_directory_offset = cursor
        central_directory_blob = b"".join(central_records)
        handle.write(central_directory_blob)
        cursor += len(central_directory_blob)
        eocd = struct.pack(
            "<IHHHHIIH",
            EOCD_SIGNATURE,
            0,
            0,
            len(selected),
            len(selected),
            len(central_directory_blob),
            central_directory_offset,
            0,
        )
        handle.write(eocd)


def write_stored_zip(members: Sequence[tuple[str, bytes]], output_path: Path) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("wb") as handle:
        central_records: List[bytes] = []
        cursor = 0
        for name, payload in members:
            encoded_name = name.encode("utf-8")
            crc32 = zlib.crc32(payload) & 0xFFFFFFFF
            local_header = struct.pack(
                "<IHHHHHIIIHH",
                LOCAL_FILE_HEADER_SIGNATURE,
                20,
                0,
                0,
                0,
                0,
                crc32,
                len(payload),
                len(payload),
                len(encoded_name),
                0,
            )
            handle.write(local_header)
            handle.write(encoded_name)
            handle.write(payload)
            central_header = struct.pack(
                "<IHHHHHHIIIHHHHHII",
                CENTRAL_DIRECTORY_SIGNATURE,
                20,
                20,
                0,
                0,
                0,
                0,
                crc32,
                len(payload),
                len(payload),
                len(encoded_name),
                0,
                0,
                0,
                0,
                0,
                cursor,
            )
            central_records.append(central_header + encoded_name)
            cursor += len(local_header) + len(encoded_name) + len(payload)

        central_directory_offset = cursor
        central_directory_blob = b"".join(central_records)
        handle.write(central_directory_blob)
        eocd = struct.pack(
            "<IHHHHIIH",
            EOCD_SIGNATURE,
            0,
            0,
            len(members),
            len(members),
            len(central_directory_blob),
            central_directory_offset,
            0,
        )
        handle.write(eocd)
