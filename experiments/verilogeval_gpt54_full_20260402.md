# Experiment Record: VerilogEval GPT-5.4 Full Benchmark

## Experiment Metadata

- **Date**: 2026-04-02
- **Dataset**: verilogeval.jsonl (157 problems, cid003 category, all easy)
- **Model**: gpt-5.4
- **Mode**: Copilot (LLM API direct via OpenAI-compatible proxy)
- **Configuration**: n=1, k=1 (single run, Pass@1)
- **Output Directory**: `work_copilot-full_gpt_verilogeval/`
- **Total Runtime**: ~10 minutes
- **API Endpoint**: `https://api.openai-proxy.org/v1` (OpenAI-compatible)

## Run Status

✅ **Run completed successfully** — all 157 problems processed.

## Benchmark Results

| Metric | Value |
|--------|-------|
| Total Problems | 157 |
| Passed | 145 |
| Failed | 12 |
| **Pass Rate** | **92.36%** |

**By Difficulty**:
- Easy: 145/157 (92.36%)

## Token Usage (157 problems)

| Metric | Value |
|--------|-------|
| Input Tokens | 289,722 |
| Output Tokens | 23,354 |
| **Total Tokens** | **313,076** |
| Avg Tokens/Problem | 1,994 |

## Harness Execution Time

| 统计 | 值 |
|------|-----|
| **总时间** | **228.82s (3.81min)** |
| **平均时间** | **1.46s/problem** |
| 最小 | 1.08s |
| 最大 | 3.59s |

## Failing Problems (12)

| # | Problem ID |
|---|-----------|
| 1 | verilogeval_Prob062_bugs_0001 |
| 2 | verilogeval_Prob082_lfsr32_0001 |
| 3-12 | (see full report in output directory) |

## Comparison: Claude Sonnet 4.6 vs GPT-5.4 on VerilogEval

| Metric | Claude Sonnet 4.6 | GPT-5.4 |
|--------|-------------------|---------|
| Pass Rate | **92.99%** (146/157) | 92.36% (145/157) |
| Total Tokens | 384,758 | **313,076** |
| Avg Tokens/Problem | 2,451 | **1,994** |
| Avg Harness Time | 1.57s | **1.46s** |
| Runtime | ~19min | **~10min** |

Both models perform nearly identically on VerilogEval (~93% pass rate). Claude passes 1 more problem but uses ~23% more tokens.
