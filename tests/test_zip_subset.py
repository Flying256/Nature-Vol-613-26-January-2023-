import zipfile
from pathlib import Path

from nature613_repro.zip_subset import (
    FileRangeReader,
    HybridRangeReader,
    build_curl_range_command,
    build_subset_zip,
    read_zip_central_directory,
)


def create_sample_archive(path: Path) -> None:
    with zipfile.ZipFile(path, "w", compression=zipfile.ZIP_DEFLATED) as zf:
        zf.writestr("README", "sample readme")
        zf.writestr("x1_test_sample.pkl", b"x1 test bytes")
        zf.writestr("x1_train_sample.pkl", b"x1 train bytes")
        zf.writestr("x2_test_sample.pkl", b"x2 test bytes")
        zf.writestr("y_test_sample.pkl", b"y test bytes")
        zf.writestr("y_train_sample.pkl", b"y train bytes")


def test_read_zip_central_directory_reports_member_names_in_archive_order(tmp_path):
    archive = tmp_path / "sample.zip"
    create_sample_archive(archive)

    entries = read_zip_central_directory(FileRangeReader(archive), archive.stat().st_size)

    assert [entry.name for entry in entries] == [
        "README",
        "x1_test_sample.pkl",
        "x1_train_sample.pkl",
        "x2_test_sample.pkl",
        "y_test_sample.pkl",
        "y_train_sample.pkl",
    ]
    assert entries[0].local_header_offset < entries[1].local_header_offset
    assert entries[1].local_header_offset < entries[2].local_header_offset


def test_build_subset_zip_keeps_only_selected_members_and_contents(tmp_path):
    archive = tmp_path / "sample.zip"
    create_sample_archive(archive)
    output = tmp_path / "subset.zip"
    reader = FileRangeReader(archive)
    entries = read_zip_central_directory(reader, archive.stat().st_size)

    build_subset_zip(
        reader,
        entries,
        [
            "README",
            "x1_test_sample.pkl",
            "x2_test_sample.pkl",
            "y_test_sample.pkl",
        ],
        output,
    )

    with zipfile.ZipFile(output) as zf:
        assert zf.namelist() == [
            "README",
            "x1_test_sample.pkl",
            "x2_test_sample.pkl",
            "y_test_sample.pkl",
        ]
        assert zf.read("README") == b"sample readme"
        assert zf.read("x1_test_sample.pkl") == b"x1 test bytes"
        assert zf.read("x2_test_sample.pkl") == b"x2 test bytes"
        assert zf.read("y_test_sample.pkl") == b"y test bytes"


def test_hybrid_range_reader_combines_local_and_remote_ranges(tmp_path):
    local_path = tmp_path / "partial.bin"
    local_path.write_bytes(b"abcdefgh")

    class FakeRemote:
        def read_range(self, start, length):
            full = b"abcdefghijklmnop"
            return full[start : start + length]

    reader = HybridRangeReader(FileRangeReader(local_path), local_path.stat().st_size, FakeRemote())

    assert reader.read_range(2, 4) == b"cdef"
    assert reader.read_range(6, 6) == b"ghijkl"
    assert reader.read_range(10, 4) == b"klmn"


def test_build_curl_range_command_uses_inclusive_byte_range():
    command = build_curl_range_command("https://example.com/archive.zip", 10, 5)

    assert command[:6] == [
        "curl",
        "-L",
        "--fail",
        "--silent",
        "--show-error",
        "--user-agent",
    ]
    assert "Mozilla/5.0" in command
    assert "--range" in command
    assert "10-14" in command
    assert command[-2:] == ["-o", "-"]
