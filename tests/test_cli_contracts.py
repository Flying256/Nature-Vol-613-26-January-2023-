from pathlib import Path


def test_predict_test_set_script_exposes_explicit_array_inputs():
    text = Path("scripts/predict_test_set.py").read_text()

    assert "--model" in text
    assert "--input-1" in text
    assert "--input-2" in text
    assert "--labels" in text
    assert "--data-dir" in text
    assert "--dataset-stem" in text
    assert "--timepoints" in text
    assert "--noise" in text
    assert "x1_test_" in text
    assert "pickle.load" in text
    assert "--output" in text


def test_text_probability_export_script_exposes_official_text_inputs():
    text = Path("scripts/export_text_probabilities.py").read_text()

    assert "--model-dir" in text
    assert "--data" in text
    assert "--model" in text
    assert "--output" in text
    assert "--s0" in text
    assert "M20" in text


def test_evaluate_variants_script_exposes_variant_manifest_and_output_dir():
    text = Path("scripts/evaluate_variants.py").read_text()

    assert "--manifest" in text
    assert "--output-dir" in text
    assert "confusion_matrix" in text


def test_download_script_prefers_manifest_direct_download_url():
    text = Path("scripts/download_or_explain.py").read_text()

    assert "resource.direct_download_url" in text
    assert "--continue-at" in text
    assert "resource.archive_aliases" in text
    assert "resource.md5" in text


def test_inspect_resources_reports_figshare_file_id_when_available():
    text = Path("scripts/inspect_resources.py").read_text()

    assert "resource.file_id" in text
    assert "resource.direct_download_url" in text
    assert "resource.archive_aliases" in text
    assert "resource.md5" in text


def test_unpack_script_can_filter_to_one_resource():
    text = Path("scripts/unpack_official_archives.py").read_text()

    assert "--resource" in text
    assert "resource.key" in text
    assert "NotImplementedError" in text
    assert 'shutil.which("unzip")' in text


def test_zip_member_listing_supports_python_and_unzip_fallback():
    text = Path("scripts/list_zip_members.py").read_text()

    assert "zipfile.ZipFile" in text
    assert 'shutil.which("unzip")' in text
    assert '"-Z1"' in text


def test_fetch_test_subset_script_exposes_range_fetching_and_selected_members():
    text = Path("scripts/fetch_test_subset.py").read_text()

    assert "--archive" in text
    assert "--url" in text
    assert "--output-zip" in text
    assert "x1_test_" in text
    assert "x2_test_" in text
    assert "y_test_" in text
    assert "Range" in text


def test_case_studies_use_official_lowercase_experiments_directory():
    text = Path("scripts/run_case_studies.sh").read_text()

    assert "experiments/Kinetic_data_Case_study_1.txt" in text
    assert "/Experiments/" not in text


def test_prediction_wrappers_run_from_official_model_directory():
    prediction = Path("scripts/run_official_prediction.sh").read_text()
    case_studies = Path("scripts/run_case_studies.sh").read_text()

    assert "cd \"${MODEL_DIR}\"" in prediction
    assert "python predict.py" in prediction
    assert "cd \"${MODEL_DIR}\"" in case_studies
    assert "python predict.py" in case_studies
