ARG BASE_IMAGE=python:3.7-slim-bullseye
FROM ${BASE_IMAGE}

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    MPLBACKEND=Agg \
    NATURE613_RUNTIME_PLATFORM=linux/amd64

WORKDIR /workspace

RUN apt-get update \
    && apt-get install -y --no-install-recommends \
        bash \
        ca-certificates \
        curl \
        libgl1 \
        libglib2.0-0 \
        libgomp1 \
        unzip \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml /workspace/pyproject.toml
COPY src /workspace/src

RUN python -m pip install --upgrade "pip<24" "setuptools>=61,<68" wheel \
    && python -m pip install \
        "tensorflow==2.1.0" \
        "h5py==2.10.0" \
        "numpy==1.19.2" \
        "pandas==1.2.3" \
        "scipy==1.4.1" \
        "scikit-learn==1.0.2" \
        "matplotlib==3.5.3" \
        "protobuf==3.20.3" \
        "pycm==3.7" \
        "pyyaml==6.0.1" \
    && python -m pip install --no-deps -e .

COPY scripts /workspace/scripts
COPY manifests /workspace/manifests
COPY docs /workspace/docs
COPY official/AI_model_and_files/train.py /workspace/official/AI_model_and_files/train.py
COPY official/AI_model_and_files/predict.py /workspace/official/AI_model_and_files/predict.py
COPY official/AI_model_and_files/utils.py /workspace/official/AI_model_and_files/utils.py
COPY official/AI_model_and_files/README /workspace/official/AI_model_and_files/README
COPY official/AI_model_and_files/environment.yml /workspace/official/AI_model_and_files/environment.yml

RUN chmod +x /workspace/scripts/*.py

VOLUME ["/workspace/Data", "/workspace/official", "/workspace/outputs"]

CMD ["python", "scripts/inspect_environment.py"]
