from pathlib import Path

import yaml


def test_official_resource_manifest_contains_model_and_dataset_dois():
    manifest = yaml.safe_load(Path("manifests/official_resources.yml").read_text())

    assert manifest["model_package"]["doi"] == "10.48420/16965271"
    assert manifest["dataset_package"]["doi"] == "10.48420/16965292"


def test_training_dataset_is_marked_as_external_volume():
    manifest = yaml.safe_load(Path("manifests/official_resources.yml").read_text())

    assert manifest["dataset_package"]["size_bytes"] > 7_000_000_000
    assert manifest["dataset_package"]["docker_policy"] == "mount_as_volume"
    assert manifest["dataset_package"]["file_id"] == "38936666"
    assert manifest["dataset_package"]["direct_download_url"].endswith("/files/38936666")
    assert manifest["dataset_package"]["expected_archive_name"] == "M1_M20_train_val_test_set.zip"
    assert "TrainValTest.zip" in manifest["dataset_package"]["archive_aliases"]
    assert manifest["dataset_package"]["md5"] == "9c52b6f31aaf450be570663cfb283f2a"


def test_model_package_records_figshare_file_download_url():
    manifest = yaml.safe_load(Path("manifests/official_resources.yml").read_text())

    assert manifest["model_package"]["file_id"] == "38936852"
    assert manifest["model_package"]["direct_download_url"].endswith("/ndownloader/files/38936852")


def test_model_package_expected_contents_match_observed_official_archive():
    manifest = yaml.safe_load(Path("manifests/official_resources.yml").read_text())
    expected = manifest["model_package"]["expected_contents"]

    assert "predict.py" in expected
    assert "train.py" in expected
    assert "utils.py" in expected
    assert "predict_reduced.py" not in expected
