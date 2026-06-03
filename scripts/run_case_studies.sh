#!/usr/bin/env bash
set -euo pipefail

MODEL_DIR="${MODEL_DIR:-official/AI_model_and_files}"
MODEL_DIR="$(cd "${MODEL_DIR}" && pwd)"
PREDICT="${MODEL_DIR}/predict.py"

if [[ ! -f "${PREDICT}" ]]; then
  echo "Missing official predict.py under ${MODEL_DIR}" >&2
  exit 2
fi

cd "${MODEL_DIR}"

run_case() {
  local name="$1"
  local data_file="$2"
  local model_file="$3"
  shift 3

  if [[ ! -f "${data_file}" ]]; then
    echo "Missing ${name} data file: ${data_file}" >&2
    return 3
  fi
  if [[ ! -f "${model_file}" ]]; then
    echo "Missing ${name} model file: ${model_file}" >&2
    return 4
  fi

  echo "===== ${name} ====="
  python predict.py "${data_file}" "$@" --model "${model_file}"
}

run_case \
  "Case 1 ring-closing metathesis" \
  "experiments/Kinetic_data_Case_study_1.txt" \
  "Data/M1_20_model_P_noXS.h5" \
  --S0 100

run_case \
  "Case 2 iron-catalyzed cycloaddition" \
  "experiments/Kinetic_data_Case_study_2.txt" \
  "Data/M1_20_model_P_noPXS.h5"

run_case \
  "Case 3 iridium alkene isomerization" \
  "experiments/Kinetic_data_Case_study_3.txt" \
  "Data/M1_20_model_S_noXS_01to5.h5"

run_case \
  "Case 4 C-H amination" \
  "experiments/Kinetic_data_Case_study_4.txt" \
  "Data/M1_20_model_P_noPXS_01to5.h5"

run_case \
  "Case 5 hydroalkoxylation" \
  "experiments/Kinetic_data_Case_study_5.txt" \
  "Data/M1_20_model_S_noPXS_01to5.h5"

run_case \
  "Case 6 Ph carbonyl-olefin metathesis" \
  "experiments/Kinetic_data_Case_study_6_Ph.txt" \
  "Data/M1_20_model_S_noXS.h5"

run_case \
  "Case 6 Me carbonyl-olefin metathesis" \
  "experiments/Kinetic_data_Case_study_6_Me.txt" \
  "Data/M1_20_model_S_noXS.h5"
