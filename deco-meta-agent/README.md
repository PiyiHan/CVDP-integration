# DeCO-Meta-Agent Docker Integration

CVDP Docker integration for DeCO Meta-Agent that generates execution memories from RTL benchmarks using a ReAct agent.

## Overview

This integration provides:
- Docker container with full DeCO environment
- Pre-configured with Python 3.12.5 and OSVB simulator (via ace-rtl-base)
- Memory generation from RTL benchmarks
- Flexible configuration via CLI arguments and environment variables

**Note**: This Docker image handles **memory generation only**. KB updates are performed on the host machine. See `/Users/peiyihan/codes/promptrtl/README.md` for complete workflow.

## File Structure

```
/Users/peiyihan/Codes/cvdp_integration/deco-meta-agent/
├── Dockerfile-base       # Base image reference (ace-rtl-base)
├── Dockerfile-agent      # Full DeCO environment with dependencies
└── build_agent.sh        # Build script for agent image
```

## Building the Image

```bash
cd /Users/peiyihan/Codes
./cvdp_integration/deco-meta-agent/build_agent.sh \
  cvdp_integration/deco-meta-agent \
  codes/promptrtl
```

This creates the `deco-meta-agent` Docker image.

## Usage

### Generate Memories

Generate execution memories from RTL benchmarks:

```bash
docker run --rm \
  -e OPENAI_API_KEY="sk-LxJGbhqqaFvZQuzO8f0c6994757a40538e7342Fe4a2626E4" \
  -v $(pwd)/benchmarks:/app/data/benchmarks:ro \
  -v $(pwd)/memories:/app/data/memories \
  deco-meta-agent \
  --mode generate_memories \
  --bench /app/data/benchmarks \
  --output-dir /app/data/memories \
  --max-cases 50
```

**Output**: Memory files will be saved to the mounted volume:
```
/memories/
  ├── case_001_memory.json
  ├── case_002_memory.json
  └── ...
```

### Optimize Single Specification (Optional)

```bash
docker run --rm \
  -e OPENAI_API_KEY="your-key" \
  -v $(pwd)/specifications:/app/specifications:ro \
  -v $(pwd)/knowledge_base:/app/data/kb:ro \
  -v $(pwd)/outputs:/app/data/outputs \
  deco-meta-agent \
  --mode optimize \
  --spec /app/specifications/spec_001.txt \
  --kb-path /app/data/kb \
  --output-dir /app/data/outputs \
  --max-iterations 3
```

## Configuration

### Environment Variables

- `OPENAI_API_KEY` (required): Your OpenAI API key
- `OPENAI_API_BASE` (optional): API base URL (default: https://api.shubiaobiao.cn/v1)

### CLI Arguments

**Memory Generation Mode:**
- `--mode generate_memories`: Generate execution memories from benchmarks
- `--bench`: Benchmark directory path (required)
- `--max-cases`: Maximum number of cases to process (optional)
- `--output-dir`: Output directory for memory files (default: `./memories`)

**Optimization Mode (Optional):**
- `--spec`: Single specification file path OR `--bench` for full benchmark
- `--output-dir`: Output directory for generated ODCs
- `--max-iterations`: Maximum optimization iterations

**Update KB Mode:**
- `--spec`: Memory file path (JSON format)

## Volume Mounts

```bash
-v $(pwd)/benchmarks:/app/data/benchmarks:ro    # Input benchmarks (required)
-v $(pwd)/memories:/app/data/memories           # Output memories (required)
-v $(pwd)/kb:/app/data/kb                      # Knowledge base (optional, for optimization)
```

## Examples

### Example 1: Generate Memories (Primary Use Case)
```bash
docker run --rm \
  -e OPENAI_API_KEY="sk-LxJGbhqqaFvZQuzO8f0c6994757a40538e7342Fe4a2626E4" \
  -v $(pwd)/benchmarks:/app/data/benchmarks:ro \
  -v $(pwd)/memories:/app/data/memories \
  deco-meta-agent \
  --mode generate_memories \
  --bench /app/data/benchmarks \
  --output-dir /app/data/memories \
  --max-cases 100 \
  --llm-model gpt-4-turbo
```

### Example 2: Optimize Single Spec
```bash
docker run --rm \
  -e OPENAI_API_KEY="your-key" \
  -v $(pwd)/my_spec.txt:/app/my_spec.txt:ro \
  -v $(pwd)/kb:/app/data/kb:ro \
  -v $(pwd)/results:/app/data/outputs \
  deco-meta-agent \
  --mode optimize \
  --spec /app/my_spec.txt \
  --kb-path /app/data/kb \
  --output-dir /app/data/outputs \
  --max-iterations 5
```

### Example 3: Interactive Shell (Debugging)
```bash
docker run --rm -it \
  -e OPENAI_API_KEY="your-key" \
  --entrypoint /bin/bash \
  deco-meta-agent

# Inside container:
python3.12 /app/main.py --help
python3.12 /app/main.py --mode generate_memories --bench /app/data/benchmarks --output-dir /app/data/memories
```

### Example 4: Inspect Generated Memories
```bash
# After memory generation, inspect files on host
cat ./memories/case_001_memory.json | jq '.success'
cat ./memories/case_001_memory.json | jq '.spec'
cat ./memories/case_001_memory.json | jq '.thoughts[-1]'

# Count successful vs failed cases
find ./memories -name "*_memory.json" -exec jq -r '.success' {} \; | grep -c true
find ./memories -name "*_memory.json" -exec jq -r '.success' {} \; | grep -c false
```

**For KB update instructions, see `/Users/peiyihan/codes/promptrtl/README.md`**

## Architecture

### Base Image
- Uses `ace-rtl-base@sha256:6460b01f13fd1d7f3a334ec08273fd04ff3fee78c522174e91175b2ef70c4357`
- Includes Python 3.12.5
- Includes OSVB simulator (Icarus Verilog)

### Agent Image
- Extends ace-rtl-base
- Installs DeCO dependencies (LangGraph, LangChain, etc.)
- Copies all DeCO source code from promptrtl directory
- Includes main.py as the entrypoint
- Pre-creates data directories

### DeCO Components Included
- `models/`: Data models (context, entry, graph, memory)
- `knowledge/`: Knowledge Base implementation
- `agents/`: MAS agents (analysis, retrieval, synthesis, verification)
- `extraction/`: Knowledge extraction tools
- `meta/`: Meta-Agent (ReAct agent for KB construction)
- `mas/`: Multi-agent workflow system
- `utils/`: Utilities (LangGraph tools, LLM wrapper)
- `config/`: Configuration and prompt templates

## Troubleshooting

### Build Fails
- Ensure ace-rtl-base image exists: `docker images | grep ace-rtl-base`
- Check platform compatibility (ARM64)
- Verify promptrtl source code is accessible

### Runtime Errors
- Check OPENAI_API_KEY is set correctly
- Verify benchmark directory structure
- Ensure volume mounts have correct permissions

### Empty Knowledge Base
- Check that benchmark directory contains cases (subdirectories)
- Verify max-cases is not too restrictive
- Check logs for LLM API errors

## Integration with CVDP

The deco-meta-agent can be integrated into CVDP workflows:

### Standard Invocation
```bash
docker run --rm \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -v "$BENCHMARK_DIR:/app/data/benchmarks:ro" \
  -v "$MEMORY_DIR:/app/data/memories" \
  deco-meta-agent \
  --mode generate_memories \
  --bench /app/data/benchmarks \
  --output-dir /app/data/memories \
  --max-cases "${MAX_CASES:-50}"
```

### Environment Configuration
Set default values via `.env`:
```bash
OPENAI_API_KEY=your-key
OPENAI_API_BASE=https://api.shubiaobiao.cn/v1
MAX_CASES=100
LLM_MODEL=gpt-4-turbo
```

**For complete workflow including KB update, see `/Users/peiyihan/codes/promptrtl/README.md`**

### Convenience Script

A `kb_workflow.sh` script is provided for end-to-end KB construction:

```bash
export OPENAI_API_KEY="your-key"
export BENCHMARK_DIR="/path/to/benchmarks"
export MEMORY_DIR="/tmp/memories"
export KB_PATH="./data/kb"

# Run complete workflow
./kb_workflow.sh

# Or with filtering
export FILTER_FLAGS="--filter-failed"
./kb_workflow.sh
```

The script:
- Validates environment variables
- Generates memories using Docker
- Counts generated memory files
- Updates KB with all or filtered memories
- Provides colored output and status messages

### Shell Wrapper
Create a script `deco_kb_workflow.sh`:
```bash
#!/bin/sh
set -e

# Step 1: Generate memories
docker run --rm \
  -e OPENAI_API_KEY="$OPENAI_API_KEY" \
  -v "$BENCHMARK_DIR:/app/data/benchmarks:ro" \
  -v "$MEMORY_DIR:/app/data/memories" \
  deco-meta-agent \
  --mode generate_memories \
  --bench /app/data/benchmarks \
  --output-dir /app/data/memories \
  --max-cases "${MAX_CASES:-50}"

# Step 2: Update KB
python main.py \
  --mode update_kb_from_memories \
  --memory-dir "$MEMORY_DIR" \
  --kb-path "$KB_PATH" \
  "${FILTER_FLAGS}"
```

Usage:
```bash
export OPENAI_API_KEY="your-key"
export BENCHMARK_DIR="/path/to/benchmarks"
export MEMORY_DIR="/tmp/memories"
export KB_PATH="./data/kb"

# Update with all memories
./deco_kb_workflow.sh

# Update with only failed cases
export FILTER_FLAGS="--filter-failed"
./deco_kb_workflow.sh
```

### Environment Configuration
Set default values via `.env`:
```bash
OPENAI_API_KEY=your-key
OPENAI_API_BASE=https://api.shubiaobiao.cn/v1
MAX_CASES=100
LLM_MODEL=gpt-4-turbo
BENCHMARK_DIR=/path/to/benchmarks
MEMORY_DIR=/tmp/memories
KB_PATH=./data/kb
```

## Reference

- DeCO Specification: `/Users/peiyihan/codes/promptrtl/DECO_SPEC.md`
- Code Architecture: `/Users/peiyihan/codes/promptrtl/CODE_ARCHITECTURE.md`
- Promptrtl README: `/Users/peiyihan/codes/promptrtl/README.md`
- ACE-RTL Integration: `/Users/peiyihan/Codes/cvdp_integration/ace-rtl_agent/`
