#!/usr/bin/env bash
set -euo pipefail

MODEL_DIR="${MODEL_DIR:-official/AI_model_and_files}"
MODEL_DIR="$(cd "${MODEL_DIR}" && pwd)"
DATA_FILE="${1:-Data/kinetics.txt}"
MODEL_FILE="${MODEL_FILE:-Data/M1_20_model.h5}"

if [[ ! -f "${MODEL_DIR}/predict.py" ]]; then
  echo "Missing official predict.py under ${MODEL_DIR}" >&2
  exit 2
fi

cd "${MODEL_DIR}"

if [[ ! -f "${MODEL_FILE}" ]]; then
  echo "Missing model file: ${MODEL_FILE}" >&2
  exit 3
fi

if [[ ! -f "${DATA_FILE}" ]]; then
  echo "Missing kinetic data file: ${DATA_FILE}" >&2
  exit 4
fi

python predict.py "${DATA_FILE}" --model "${MODEL_FILE}"
