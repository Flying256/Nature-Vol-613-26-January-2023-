from pathlib import Path


def test_dockerfile_contains_training_runtime_contract():
    text = Path("docker/Dockerfile").read_text()

    assert "ARG BASE_IMAGE=" in text
    assert "FROM ${BASE_IMAGE}" in text
    assert "python:3.7-slim-bullseye" in text
    assert "tensorflow==2.1.0" in text
    assert "protobuf==3.20.3" in text
    assert "h5py==2.10.0" in text
    assert "COPY official/AI_model_and_files/train.py" in text
    assert "COPY official/AI_model_and_files/predict.py" in text
    assert "COPY official/AI_model_and_files/utils.py" in text
    assert 'VOLUME ["/workspace/Data", "/workspace/official", "/workspace/outputs"]' in text
    assert 'CMD ["python", "scripts/inspect_environment.py"]' in text


def test_package_metadata_allows_official_python37_runtime():
    text = Path("pyproject.toml").read_text()

    assert 'requires-python = ">=3.7"' in text
    assert "setuptools>=61,<68" in text


def test_dockerignore_excludes_caches_and_large_official_artifacts():
    text = Path(".dockerignore").read_text().splitlines()

    assert "__pycache__" in text
    assert ".pytest_cache" in text
    assert "official/*" in text
    assert "!official/AI_model_and_files/train.py" in text
    assert "!official/AI_model_and_files/predict.py" in text
    assert "!official/AI_model_and_files/utils.py" in text
    assert "Data" in text
    assert "outputs" in text
    assert "*.zip" in text
    assert "*.h5" in text
    assert "*.pkl" in text


def test_h800_ngc_dockerfile_uses_stable_tensorflow_gpu_stack():
    text = Path("docker/Dockerfile.h800-ngc").read_text()

    assert "nvcr.io/nvidia/tensorflow:24.05-tf2-py3" in text
    assert "NVIDIA_VISIBLE_DEVICES=all" in text
    assert "NVIDIA_DRIVER_CAPABILITIES=compute,utility" in text
    assert "COPY official/AI_model_and_files/train.py" in text
    assert "COPY official/AI_model_and_files/utils.py" in text
    assert "VOLUME" in text
    assert "scripts/inspect_environment.py" in text


def test_h800_training_notes_document_python314_boundary_and_run_command():
    text = Path("docs/H800训练镜像配置.md").read_text()

    assert "Python 3.14" in text
    assert "不作为 TensorFlow GPU 训练主环境" in text
    assert "nvcr.io/nvidia/tensorflow:24.05-tf2-py3" in text
    assert "docker build" in text
    assert "--gpus all" in text
    assert "H800" in text
