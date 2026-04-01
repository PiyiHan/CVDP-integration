#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

set -e

# Agent configuration
# AGENT_BUILD_DIR="/Users/peiyihan/Codes/cvdp_integration/ace-rtl_agent"
# AGENT_SOURCE_DIR="/Users/peiyihan/Codes/ACE-RTL"
# AGENT_NAME="ace-rtl-agent"

# AGENT_BUILD_DIR="/Users/peiyihan/Codes/cvdp_integration/mage_agent"
# AGENT_SOURCE_DIR="/Users/peiyihan/Codes/MAGE"
# AGENT_NAME="mage-agent"

AGENT_BUILD_DIR="/Users/peiyihan/Codes/cvdp_integration/deco-meta-agent"
AGENT_SOURCE_DIR="/Users/peiyihan/Codes/promptrtl"
AGENT_NAME="deco-meta-agent"

SCRIPTS_DIR="/Users/peiyihan/Codes/cvdp_integration/scripts"
CVDP_DIR="/Users/peiyihan/Codes/cvdp_benchmark"

# Default dataset configuration
DATASET_DIR="/Users/peiyihan/Codes/cvdp_benchmark/dataset_verilogeval/verilogeval.jsonl"
DATASET_PROBLEM_ID="verilogeval_Prob001_zero_0001"

# Force agentic mode for custom datasets (VerilogEval etc.)
FORCE_AGENTIC="--force-agentic"

# Non-agentic (copilot) mode: default LLM model, override via LLM_MODEL env var
LLM_MODEL="deepseek-v3-2-251201"

# ----------------------------------------
# Prefix helpers
# Format: work_{mode}_{model|agent}_{dataset}[_{problem_id}][_n{samples}]
# ----------------------------------------

_shorten_dataset() {
    local name="$1"
    name="${name##*/}"
    name="${name%.jsonl}"
    name="${name%.json}"
    name="${name#cvdp_v[0-9]*.[0-9]*_}"
    name="${name#cvdp_}"
    if [ ${#name} -gt 20 ]; then
        name="${name:0:20}"
    fi
    echo "$name"
}

_shorten_model() {
    echo "${1%%-*}"
}

_shorten_problem() {
    local pid="$1" ds_short="$2"
    pid="${pid%_[0-9][0-9][0-9][0-9]}"
    if [[ "$pid" == "${ds_short}_"* ]]; then
        pid="${pid#"${ds_short}"_}"
    fi
    if [ ${#pid} -gt 30 ]; then
        pid="${pid:0:30}"
    fi
    echo "$pid"
}

make_prefix() {
    local mode="$1" identity="$2" dataset="$3"
    shift 3
    local ds_short
    ds_short=$(_shorten_dataset "$dataset")
    local p="work_${mode}_$(_shorten_model "$identity")_${ds_short}"
    while [ $# -gt 0 ]; do
        case "$1" in
            pid=*) p="${p}_$(_shorten_problem "${1#pid=}" "$ds_short")" ;;
            n=*)   p="${p}_n${1#n=}" ;;
        esac
        shift
    done
    echo "$p"
}

case "$1" in
convert-verilogeval)
  if [ $# -lt 3 ]; then
    echo "Usage: $0 convert-verilogeval <verilogeval_dataset_dir> <output.jsonl> [dataset_name]"
    exit 1
  fi
  python3 "$SCRIPTS_DIR/verilogeval_to_cvdp.py" "$2" "$3" "${4:-verilogeval}"
  ;;
download-cvdp)
  mkdir -p "$CVDP_DIR/dataset"
  if [ $# -eq 1 ]; then
    python3 "$SCRIPTS_DIR/download_cvdp_dataset.py" --output-dir "$CVDP_DIR/dataset"
  else
    python3 "$SCRIPTS_DIR/download_cvdp_dataset.py" --subset "$2" --output-dir "$CVDP_DIR/dataset"
  fi
  ;;
build)
  cd "$AGENT_BUILD_DIR"
  ./build_agent.sh "$AGENT_BUILD_DIR" "$AGENT_SOURCE_DIR"
  ;;
golden)
  cd "$CVDP_DIR"
  DATASET="${2:-example_dataset/cvdp_v1.0.4_example_agentic_code_generation_no_commercial_with_solutions.jsonl}"
  PREFIX=$(make_prefix golden golden "$DATASET")
  python run_benchmark.py -f "$DATASET" -p "${3:-$PREFIX}"
  echo "Golden results in ${3:-$PREFIX}/report.txt"
  ;;
full)
  cd "$CVDP_DIR"
  DATASET="${2:-$DATASET_DIR}"
  PREFIX=$(make_prefix full "$AGENT_NAME" "$DATASET")
  python run_benchmark.py -f "$DATASET" -l -g $AGENT_NAME -p "${3:-$PREFIX}"
  ;;
samples)
  DATASET="$2"
  N="${3:-5}"
  K="${4:-1}"
  PREFIX=$(make_prefix samples "$AGENT_NAME" "$DATASET" n=$N)
  cd "$CVDP_DIR"
  python run_samples.py -f "$DATASET" -l -g $AGENT_NAME -n "$N" -k "$K" -p "${5:-$PREFIX}"
  ;;
single)
  cd "$CVDP_DIR"
  DATASET="${2:-$DATASET_DIR}"
  PID="${3:-$DATASET_PROBLEM_ID}"
  PREFIX=$(make_prefix single "$AGENT_NAME" "$DATASET" pid="$PID")
  python run_benchmark.py -f "$DATASET" -i "$PID" -l -g $AGENT_NAME $FORCE_AGENTIC -p "${4:-$PREFIX}"
  ;;
copilot-single)
  cd "$CVDP_DIR"
  DATASET="${2:-$DATASET_DIR}"
  PID="${3:-$DATASET_PROBLEM_ID}"
  PREFIX=$(make_prefix copilot-single "$LLM_MODEL" "$DATASET" pid="$PID")
  export OPENAI_BASE_URL="${OPENAI_API_BASE}"
  python run_benchmark.py -f "$DATASET" -i "$PID" -l -m $LLM_MODEL --force-copilot -p "${4:-$PREFIX}"
  ;;
copilot-full)
  cd "$CVDP_DIR"
  DATASET="${2:-$DATASET_DIR}"
  PREFIX=$(make_prefix copilot-full "$LLM_MODEL" "$DATASET")
  export OPENAI_BASE_URL="${OPENAI_API_BASE}"
  python run_benchmark.py -f "$DATASET" -l -m $LLM_MODEL --force-copilot -p "${3:-$PREFIX}"
  ;;
copilot-samples)
  DATASET="$2"
  N="${3:-5}"
  K="${4:-1}"
  PREFIX=$(make_prefix copilot-samples "$LLM_MODEL" "$DATASET" n=$N)
  cd "$CVDP_DIR"
  export OPENAI_BASE_URL="${OPENAI_API_BASE}"
  python run_samples.py -f "$DATASET" -l -m $LLM_MODEL --force-copilot -n "$N" -k "$K" -p "${5:-$PREFIX}"
  ;;
*)
  echo "Usage: $0 {build|golden|full|samples|single|copilot-single|copilot-full|copilot-samples|convert-verilogeval|download-cvdp}"
  echo ""
  echo "Agentic Commands (Docker container-based agents):"
  echo "  build                                Build agent Docker image"
  echo "  golden [dataset] [prefix]            Test golden reference solutions"
<<<<<<< HEAD
  echo "  full [dataset] [prefix]              Run full benchmark with agent"
=======
  echo "  full <dataset> [prefix]              Run full benchmark with agent"
>>>>>>> d288c7f2b3acc5a776e8ebab22a27ee4abe1e211
  echo "  samples <dataset> [n=5] [k=1] [prefix]"
  echo "                                       Run Pass@k evaluation with agent"
  echo "  single [dataset] [problem_id] [prefix]"
  echo "                                       Run single problem with agent (debug)"
  echo ""
  echo "Non-Agentic (Copilot) Commands (LLM API, no Docker agent):"
  echo "  copilot-single [dataset] [problem_id] [prefix]"
  echo "                                       Run single problem with LLM (debug)"
  echo "  copilot-full [dataset] [prefix]      Run full benchmark with LLM"
  echo "  copilot-samples <dataset> [n=5] [k=1] [prefix]"
  echo "                                       Run Pass@k evaluation with LLM"
  echo ""
  echo "Other Commands:"
  echo "  convert-verilogeval <dir> <out.jsonl>"
  echo "                                       Convert VerilogEval to CVDP JSONL"
  echo "  download-cvdp [subset]               Download CVDP datasets"
  echo ""
  echo "Configuration:"
  echo "  AGENT_NAME       = $AGENT_NAME"
  echo "  LLM_MODEL        = $LLM_MODEL (override: LLM_MODEL=gpt-4o $0 copilot-single)"
  echo "  FORCE_AGENTIC    = $FORCE_AGENTIC"
  echo "  OPENAI_API_BASE  = Custom API endpoint (agentic Docker env)"
  echo "  OPENAI_BASE_URL  = Custom API endpoint (copilot, read by OpenAI SDK)"
  echo ""
  echo "Default output prefix: work_{mode}_{model|agent}_{dataset}[_{problem_id}][_n{samples}]"
  echo "Examples:"
  echo "  work_copilot-single_deepseek_verilogeval_Prob001_zero"
  echo "  work_single_deco_verilogeval_Prob001_zero"
  echo "  work_copilot-full_deepseek_verilogeval"
  echo "  work_copilot-samples_deepseek_verilogeval_n5"
  echo ""
  echo "Usage examples:"
  echo "  $0 single"
  echo "  $0 copilot-single"
  echo "  LLM_MODEL=gpt-4o $0 copilot-single"
  echo "  $0 copilot-full dataset_verilogeval/verilogeval.jsonl"
  exit 1
  ;;
esac
