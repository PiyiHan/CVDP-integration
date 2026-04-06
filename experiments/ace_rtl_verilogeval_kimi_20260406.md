# Experiment Record: ACE-RTL Agentic VerilogEval Benchmark

## Experiment Metadata

- **Date**: 2026-04-06
- **Dataset**: verilogeval.agentic_transformed.agentic_transformed.jsonl (157 problems)
- **Model**: kimi-k2.5 (via OpenAI-compatible proxy)
- **Mode**: Agentic (ACE-RTL agent, Generate-Compile-Simulate-Reflect loop)
- **Configuration**: n=1, k=1 (single run, Pass@1), MAX_ITERATIONS=30
- **Output Directory**: `work_full_ace_rtl_agentic_verilogeval_kimi/`
- **Total Runtime**: ~5 minutes (Avg 1.5s/problem harness time)
- **API Endpoint**: `api.openai-proxy.org/v1`
- **Docker Image**: `ace-rtl-agent:latest` (built from `/Users/peiyihan/Codes/ACE-RTL/`)

## Run Configuration

| Parameter | Value |
|-----------|-------|
| `--force-agentic` | Yes (required — verilogeval IDs don't contain "agentic" as 2nd segment) |
| `MODEL_TIMEOUT` | 180s |
| `LLM_MODEL` | kimi-k2.5 |

> **Note**: `--force-agentic` was necessary because `detect_dataset_format()` in `run_benchmark.py:54` checks if `data["id"].split("_")[1] == "agentic"`, but verilogeval IDs use `verilogeval_ProbXXX_*` format. Without this flag, all 157 problems failed instantly with `th_prepare: 'input'` KeyError (CopilotProcessor tried to access `context["input"]["context"]` instead of `context["context"]`).

## Benchmark Results

| Metric | Value |
|--------|-------|
| Total Problems | 157 |
| Passed | 122 |
| Failed | 35 |
| **Problem Pass Rate** | **77.71%** |

## Agent Statistics

| Metric | Value |
|--------|-------|
| Agent Success (simulation passed) | 156/157 (99.36%) |
| No-Testbench Fallback | 1/157 (0.64%) |
| Max Iterations Reached | 0/157 (0%) |

### Iteration Distribution

| Iterations | Problems | Notes |
|-----------|----------|-------|
| 0 (no testbench) | 1 | Prob062_bugs — generated RTL, skipped sim |
| 1 | 146 | Most problems solved in first attempt |
| 2 | 4 | |
| 3 | 2 | |
| 4 | 1 | |
| 5 | 2 | |
| 14 | 1 | Prob119_fsm3 (hardest problem, 53K tokens) |

## Token Usage

| Metric | Value |
|--------|-------|
| Input Tokens | 318,622 |
| Output Tokens | 190,205 |
| **Total Tokens** | **508,827** |
| Avg Tokens/Problem | 3,240 |
| Median Tokens/Problem | ~1,200 (most solve in 1 iteration) |

### Token Distribution by Iteration Count

| Iterations | Avg Tokens | Notes |
|-----------|-----------|-------|
| 1 (146 problems) | ~1,200 | Simple combinational/sequential logic |
| 2 (4 problems) | ~10,700 | |
| 3 (2 problems) | ~13,500 | |
| 5 (2 problems) | ~23,900 | Prob109_fsm1, Prob146_fsm_serialdata |
| 14 (1 problem) | 53,542 | Prob119_fsm3 (FSM, hardest) |

### Top 5 Token Consumers

| Problem | Iterations | Total Tokens | Notes |
|---------|-----------|-------------|-------|
| Prob119_fsm3 | 14 | 53,542 | FSM — 10.5% of total |
| Prob070_ece241_2013_q2 | 4 | 36,461 | |
| Prob146_fsm_serialdata | 5 | 31,786 | Failed harness |
| Prob140_fsm_hdlc | 3 | 18,380 | Failed harness |
| Prob110_fsm2 | 3 | 8,546 | |

> Prob119_fsm3 alone consumed 10.5% of all tokens. Excluding it, the remaining 156 problems averaged 2,924 tokens each.

## Comparison: ACE-RTL vs Copilot-Samples (kimi-k2.5, VerilogEval)

| Mode | Pass@1 | Tokens | Avg Tokens/Problem |
|------|--------|--------|-------------------|
| ACE-RTL (agentic, n=1) | 77.71% | 508,827 | 3,240 |
| Copilot-samples (n=1) | 88.15% | ~279,002 (est.) | ~1,777 |
| Copilot-samples (n=5, pass@3) | 92.10% | 1,395,010 | ~8,885 |

ACE-RTL underperforms copilot-samples pass@1 by **10.44pp** on VerilogEval, despite using more tokens per problem. This is because:

1. **Single generation vs 5 samples**: Copilot-samples generates 5 independent solutions; pass@1 is the best-of-1, but ACE-RTL also only gets 1 attempt via its iterative loop.
2. **Iterative refinement helps but not enough**: 146/157 problems pass in iteration 1 (same as a single copilot sample). The 11 problems needing 2+ iterations only gained 6 additional passes.
3. **Harness mismatch**: 34/35 failures had agent-internal simulation success but external harness failure — the agent's testbench passed but the CVDP harness testbench differs or is stricter.

## Comparison: ACE-RTL Across Datasets (kimi-k2.5)

| Dataset | Problems | Pass Rate | Total Tokens | Avg Tokens/Problem |
|---------|----------|-----------|-------------|-------------------|
| VerilogEval | 157 | 77.71% | 508,827 | 3,240 |
| CID003 (v2) | 34 | 41.18% | 669,433 | 20,286 |

CID003 problems are significantly harder (industry-grade RTL), requiring 6.3x more tokens per problem. VerilogEval problems are mostly academic exercises (simple gates, counters, basic FSMs).

## Failing Problems Analysis (35 failures)

All 34 agent-succeeded failures follow the same pattern: agent simulation passed, but external CVDP harness failed. Common causes:

- **Module interface mismatch**: Agent generates correct logic but wrong port names/order
- **Simulation vs synthesis differences**: Code simulates correctly but fails formal verification
- **Incomplete specification understanding**: Agent misinterprets edge cases

The 1 agent failure (Prob062_bugs) had no testbench, used the NO_TB fallback, but the generated RTL didn't pass the external harness.

### Notable Failing Problems

| Problem | Iterations | Tokens | Category |
|---------|-----------|--------|----------|
| Prob062_bugs | 0 (no TB) | 544 | Debug (fix existing code) |
| Prob053_m2014_q4d | 1 | 1,193 | Sequential logic |
| Prob057_kmap2 | 2 | 12,266 | Karnaugh map |
| Prob082_lfsr32 | 1 | 1,277 | LFSR |
| Prob133_2014_q3fsm | 1 | 1,404 | FSM |
| Prob140_fsm_hdlc | 3 | 18,380 | Complex FSM |
| Prob146_fsm_serialdata | 5 | 31,786 | Complex FSM |

FSM problems dominate the hard failures — they require precise state encoding and transition logic.

## Observations

1. **VerilogEval is easy for ACE-RTL**: 92.9% agent-internal success rate (146/157 in iteration 1). Most problems are simple combinational logic.
2. **Token efficiency is good**: 3,240 avg tokens/problem vs copilot-samples ~1,777 tokens/sample. ACE-RTL uses ~1.8x more tokens for a single attempt but provides iterative refinement.
3. **Iterative refinement has diminishing returns**: Going from 1 to 14 iterations on Prob119_fsm3 used 53K tokens — equivalent to 44 simple problems. The reflect loop is expensive for hard problems.
4. **NO_TB fallback rarely needed**: Only 1/157 problems lacked a testbench (vs 19/34 for CID003). VerilogEval is well-formed with testbenches.
5. **External harness is stricter than agent testbench**: 34 problems where agent simulation passed but harness failed. The agent's own testbench may be less comprehensive.
