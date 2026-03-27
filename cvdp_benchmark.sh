#!/bin/bash

# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

set -e

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

# DATASET_DIR="example_dataset/cvdp_v1.0.4_example_agentic_code_generation_no_commercial_with_solutions.jsonl"
# DATASET_PROBLEM_ID="cvdp_agentic_fixed_arbiter_0001"

# Force agentic mode for custom datasets
# CVDP detects dataset format by checking if ID contains 'agentic' (e.g., cvdp_agentic_xxx_0001)
# Custom datasets like VerilogEval have IDs like verilogeval_Prob001_zero_0001 and require force-agentic
# Set to 'true' for custom datasets, 'false' for standard CVDP datasets
FORCE_AGENTIC="--force-agentic"

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
*)
  echo "Usage: $0 {build|golden|full|samples|single}"
  echo ""
  echo "Commands:"
  echo "  build                     Build ace-rtl-agent Docker image"
  echo "  golden [dataset] [prefix]  Test golden reference solutions (verify test harness)"
  echo "  full <dataset> [prefix]   Run full benchmark on dataset with agent"
  echo "  samples <dataset> [n] [k] [prefix]"
  echo "                            Run multi-sample Pass@k evaluation with agent"
  echo "  single <dataset> <problem_id> [prefix]"
  echo "                            Run single problem with agent (for debugging)"
  echo "                            Default dataset: $DATASET_DIR"
  echo "                            Default problem: $DATASET_PROBLEM_ID"
  echo ""
  echo "Dataset Mode Detection:"
  echo "  CVDP detects agentic mode by checking if ID contains 'agentic' (e.g., cvdp_agentic_xxx_0001)"
  echo "  - Agentic mode: Use -g <agent_name> flag (Docker container-based)"
  echo "  - Non-agentic mode: Use -m <model_name> flag (LLM API-based)"
  echo "  - Custom datasets: FORCE_AGENTIC variable (default: --force-agentic)"
  echo ""
  echo "Agentic Workflow:"
  echo "  1. Run golden test: $0 golden"
  echo "  2. Build agent: $0 build"
  echo "  3. Run samples: $0 samples example_dataset/cvdp_v1.0.4_example_agentic_code_generation_no_commercial_with_solutions.jsonl 5 1"
  echo "  4. Run full: $0 full example_dataset/cvdp_v1.0.4_example_agentic_code_generation_no_commercial_with_solutions.jsonl"
  echo "  5. Debug single (uses defaults): $0 single"
  echo "  6. Debug single (explicit): $0 single datase_verilogeval/verilogeval.jsonl verilogeval_Prob001_zero_0001"
  exit 1
  ;;
esac
