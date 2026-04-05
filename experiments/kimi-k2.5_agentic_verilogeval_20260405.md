# Experiment Record: Kimi-K2.5 Agentic VerilogEval Full Benchmark

## Experiment Metadata

- **Date**: 2026-04-05
- **Dataset**: verilogeval.agentic_transformed.jsonl (157 problems, cid003 category, all easy)
- **Model**: kimi-k2.5 (via OpenAI-compatible proxy)
- **Mode**: Agentic (deco-meta-agent, Docker container with ReAct agent, tool calls)
- **Configuration**: n=1, k=1 (single run, Pass@1), REACT_MAX_STEPS=10
- **Output Directory**: `work_full_deco_verilogeval.agentic_/`
- **Total Runtime**: ~90 minutes (agent phase ~85 min, harness phase ~5 min)
- **API Integration**: OpenAI-compatible API via `ChatOpenAI` (langchain_openai)

## Run Status

**Run completed successfully** -- all 157 problems processed.

| Metric | Value |
|--------|-------|
| Problems Started | 157 |
| Agent Executions | 157/157 |
| Metrics Files Found | 157 |
| Harness Executions | 157 |

## Benchmark Results

| Metric | Value |
|--------|-------|
| Total Problems | 157 |
| Passed | 156 |
| Failed | 1 |
| **Pass Rate** | **99.36%** |

**By Difficulty**:
- Easy: 156/157 (99.36%)

## Token Usage (157 problems)

| Metric | Value |
|--------|-------|
| Input Tokens | 4,058,280 |
| Output Tokens | 270,812 |
| **Total Tokens** | **4,329,092** |
| Avg Tokens/Problem | 27,574 |
| LLM Call Count | 157 |

## Cost Calculation

Cost not tracked (proxy-based API, pricing not available).

## Harness Execution Time

| Metric | Value |
|--------|-------|
| **Total Time** | **234.71s (3.91min)** |
| **Avg Time** | **1.49s/problem** |
| Min | 1.10s |
| Max | 5.13s |
| Data Points | 157 |

## Failing Problems (1)

| # | Problem ID |
|---|-----------|
| 1 | verilogeval_Prob062_bugs_0001 |

Note: This same problem also fails in Claude Sonnet 4.6 copilot mode, suggesting a dataset/testbench issue rather than a model issue.

## Comparison: Agentic vs Copilot on VerilogEval

| Metric | DeepSeek v3-2 (Copilot) | GPT-5.4 (Copilot) | Claude 4.6 (Copilot) | **Kimi-K2.5 (Agentic)** |
|--------|------------------------|-------------------|---------------------|------------------------|
| Pass Rate | ~70% | 92.36% | 92.99% | **99.36%** |
| Total Tokens | ~250K | ~350K | 384,758 | 4,329,092 |
| Avg Tokens/Problem | ~1,600 | ~2,200 | 2,451 | 27,574 |
| Harness Time (total) | ~200s | ~230s | 246.35s | 234.71s |
| Avg Harness Time | ~1.3s | ~1.5s | 1.57s | 1.49s |

## Key Observations

1. **99.36% pass rate** -- highest among all tested configurations (copilot and agentic)
2. The agentic mode's iterative tool-use approach (read files, write code, compile, simulate, debug) enables near-perfect results
3. Token usage is ~11x higher than copilot mode due to multi-step agent interactions
4. Only 1 failure (Prob062_bugs) which also fails in Claude copilot mode
5. Average harness time (1.49s) is consistent with other models

## Technical Notes

1. **Bug fix applied**: The `cvdp_benchmark.sh` `full` command was missing `--force-agentic` flag for non-CVDP-native agentic datasets. Without it, VerilogEval data was routed to `CopilotProcessor` which expected `context["input"]["context"]` but VerilogEval uses `context["context"]`. Fixed by adding `$FORCE_AGENTIC` to `full` and `samples` commands.
2. Agent tool calls: list_directory, read_file, write_file, compile_and_simulate
3. Each problem involves: context setup -> agent Docker container -> LLM generates patch -> harness verification
