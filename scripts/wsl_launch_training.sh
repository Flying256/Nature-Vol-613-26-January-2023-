#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/.."
. .venv-wsl-tf/bin/activate

export NATURE613_ALLOW_TRAINING=1
export TF_CPP_MIN_LOG_LEVEL=0
mkdir -p outputs

python official/AI_model_and_files/train.py 2>&1 | tee outputs/training_wsl.log
