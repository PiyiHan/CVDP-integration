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
LLM_MODEL="${LLM_MODEL:-gpt-4o-mini}"

case "$1" in
convert-verilogeval)
  if [ $# -lt 3 ]; then
    echo "Usage: $0 convert-verilogeval <verilogeval_dataset_dir> <output.jsonl> [dataset_name]"
    echo ""
    echo "Example:"
    echo "  $0 convert-verilogeval \\"
    echo "    /Users/peiyihan/Codes/verilog-eval/dataset_spec-to-rtl \\"
    echo "    ~/Codes/cvdp_benchmark/dataset_verilogeval/verilogeval.jsonl"
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
  python run_benchmark.py -f ${2:-example_dataset/cvdp_v1.0.4_example_agentic_code_generation_no_commercial_with_solutions.jsonl} -p ${3:-work_golden}
  echo "Golden results in ${3:-work_golden}/report.txt"
  ;;
full)
  cd "$CVDP_DIR"
  python run_benchmark.py -f ${2:-example_dataset/cvdp_v1.0.4_example_agentic_code_generation_no_commercial_with_solutions.jsonl} -l -g $AGENT_NAME -p ${3:-work_full}
  ;;
samples)
  cd "$CVDP_DIR"
  python run_samples.py -f $2 -l -g $AGENT_NAME -n ${3:-5} -k ${4:-1} -p ${5:-work_samples}
  ;;
single)
  cd "$CVDP_DIR"
  python run_benchmark.py -f ${2:-$DATASET_DIR} -i ${3:-$DATASET_PROBLEM_ID} -l -g $AGENT_NAME $FORCE_AGENTIC -p ${4:-work_single}
  ;;
copilot-single)
  cd "$CVDP_DIR"
  export OPENAI_BASE_URL="${OPENAI_API_BASE}"
  python run_benchmark.py -f ${2:-$DATASET_DIR} -i ${3:-$DATASET_PROBLEM_ID} -l -m $LLM_MODEL --force-copilot -p ${4:-work_copilot_single}
  ;;
copilot-full)
  cd "$CVDP_DIR"
  export OPENAI_BASE_URL="${OPENAI_API_BASE}"
  python run_benchmark.py -f ${2:-$DATASET_DIR} -l -m $LLM_MODEL --force-copilot -p ${3:-work_copilot_full}
  ;;
copilot-samples)
  cd "$CVDP_DIR"
  export OPENAI_BASE_URL="${OPENAI_API_BASE}"
  python run_samples.py -f $2 -l -m $LLM_MODEL --force-copilot -n ${3:-5} -k ${4:-1} -p ${5:-work_copilot_samples}
  ;;
*)
  echo "Usage: $0 {build|golden|full|samples|single|copilot-single|copilot-full|copilot-samples|convert-verilogeval|download-cvdp}"
  echo ""
  echo "Agentic Commands (Docker container-based agents):"
  echo "  build                                Build agent Docker image"
  echo "  golden [dataset] [prefix]            Test golden reference solutions"
  echo "  full <dataset> [prefix]              Run full benchmark with agent"
  echo "  samples <dataset> [n] [k] [prefix]   Run Pass@k evaluation with agent"
  echo "  single [dataset] [problem_id] [prefix]"
  echo "                                       Run single problem with agent (debug)"
  echo ""
  echo "Non-Agentic (Copilot) Commands (LLM API, no Docker agent):"
  echo "  copilot-single [dataset] [problem_id] [prefix]"
  echo "                                       Run single problem with LLM (debug)"
  echo "  copilot-full [dataset] [prefix]      Run full benchmark with LLM"
  echo "  copilot-samples <dataset> [n] [k] [prefix]"
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
  echo "Examples:"
  echo "  # Agentic (default VerilogEval)"
  echo "  $0 single"
  echo "  # Agentic (explicit dataset/problem)"
  echo "  $0 single datase_verilogeval/verilogeval.jsonl verilogeval_Prob001_zero_0001"
  echo "  # Non-agentic single"
  echo "  $0 copilot-single"
  echo "  # Non-agentic with different model"
  echo "  LLM_MODEL=gpt-4o $0 copilot-single"
  echo "  # Non-agentic full"
  echo "  $0 copilot-full datase_verilogeval/verilogeval.jsonl"
  exit 1
  ;;
esac
