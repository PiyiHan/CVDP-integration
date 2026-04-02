# Experiment Record: VerilogEval Claude Sonnet 4.6 Full Benchmark

## Experiment Metadata

- **Date**: 2026-04-02
- **Dataset**: verilogeval.jsonl (157 problems, cid003 category, all easy)
- **Model**: claude-sonnet-4-6
- **Mode**: Copilot (LLM API direct, no Docker agent)
- **Configuration**: n=1, k=1 (single run, Pass@1)
- **Output Directory**: `work_copilot-full_claude_verilogeval/`
- **Total Runtime**: ~19 minutes
- **API Integration**: Native Anthropic Messages API via `Anthropic_Instance`

## Run Status

✅ **Run completed successfully** — all 157 problems processed.

| Metric | Value |
|--------|-------|
| Problems Started | 157 |
| API Calls Successful | 157/157 |
| Metrics Files Found | 157 |
| Harness Executions | 157 |

## Benchmark Results

| Metric | Value |
|--------|-------|
| Total Problems | 157 |
| Passed | 146 |
| Failed | 11 |
| **Pass Rate** | **92.99%** |

**By Difficulty**:
- Easy: 146/157 (92.99%)

## Token Usage (157 problems)

| Metric | Value |
|--------|-------|
| Input Tokens | 352,847 |
| Output Tokens | 31,911 |
| **Total Tokens** | **384,758** |
| Avg Tokens/Problem | 2,451 |
| LLM Call Count | 157 |

## Cost Calculation

**Pricing (Anthropic claude-sonnet-4-6)**:
- 1M Input Tokens: $3.00
- 1M Output Tokens: $15.00

**This Run Costs** (157 problems, no cache):

| Scenario | Input Cost | Output Cost | Total |
|----------|-----------|-------------|-------|
| No Cache | $1.059 | $0.479 | $1.537 |

## Harness Execution Time

| 统计 | 值 |
|------|-----|
| **总时间** | **246.35s (4.11min)** |
| **平均时间** | **1.57s/problem** |
| 最小 | 1.08s |
| 最大 | 5.47s |
| 有效数据点 | 157 |

## Failing Problems (11)

| # | Problem ID |
|---|-----------|
| 1 | verilogeval_Prob062_bugs_0001 |
| 2 | verilogeval_Prob074_ece241_2014_q4_0001 |
| 3 | verilogeval_Prob079_ece241_2013_q7_0001 |
| 4 | verilogeval_Prob080_ece241_2014_q3_0001 |
| 5 | verilogeval_Prob083_ece241_2013_q8_0001 |
| 6 | verilogeval_Prob084_ece241_2014_q5a_0001 |
| 7 | verilogeval_Prob086_ece241_2014_q5b_0001 |
| 8 | verilogeval_Prob088_ece241_2013_q6b_0001 |
| 9 | verilogeval_Prob090_ece241_2013_q6c_0001 |
| 10 | verilogeval_Prob091_ece241_2013_q6d_0001 |
| 11 | verilogeval_Prob092_ece241_2013_q6e_0001 |

## Comparison: Claude vs DeepSeek on VerilogEval

| Metric | DeepSeek v3-2 | Claude Sonnet 4.6 |
|--------|--------------|-------------------|
| Pass Rate | ~70% (estimated) | **92.99%** |
| Total Tokens | ~250K (estimated) | 384,758 |
| Avg Tokens/Problem | ~1,600 | 2,451 |
| Harness Time (total) | ~200s | 246.35s |
| Avg Harness Time | ~1.3s | 1.57s |

## Notes

1. All 157 API calls succeeded — no timeouts or errors
2. Claude Sonnet 4.6 achieves excellent 92.99% pass rate on VerilogEval
3. Most failures are in sequential logic / FSM problems (Prob074-Prob092 are exam-style questions from ECE courses)
4. Token usage is higher than DeepSeek but pass rate is significantly better
5. Average harness time (1.57s) is very fast — problems are simple combinational/sequential circuits
