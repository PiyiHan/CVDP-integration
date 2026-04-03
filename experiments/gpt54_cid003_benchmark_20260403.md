# Experiment Record: GPT-5.4 CVDP Benchmark on cid003 (n=5)

## Experiment Metadata

- **Date**: 2026-04-03
- **Dataset**: cvdp_v1.0.4_nonagentic_cid003.jsonl (78 problems, cid003 category)
- **Mode**: Copilot (LLM API direct, no Docker agent)
- **Configuration**: n=5, k=1 (Pass@5 evaluation)
- **API Endpoint**: https://api.openai-proxy.org/v1
- **API Key**: <see ~/.zshrc and .env>
- **MODEL_TIMEOUT**: 180s

## Setup Notes

1. **Reused copilot-full run as sample_1**: The existing `work_copilot-full_gpt_nonagentic_cid003/` (single-shot run) was copied into `work_copilot-samples_gpt_nonagentic_cid003_n5/sample_1/` to avoid re-running 78 problems already completed.
2. **Partial resume**: Added resume logic to `run_benchmark.py` so that when `raw_result.json` exists with partial results, it identifies missing problems from the dataset and only runs those, then merges.
3. **Sample_2 recovery**: The first run attempt failed partway through sample_2 (72/78 problems completed). Built a partial `raw_result.json` from the 72 completed problem report files, then the resume logic completed the remaining 6 problems.
4. **Proxy flakiness**: Intermittent 401 errors from api.openai-proxy.org caused multiple failed run attempts. The retry logic in the benchmark handled them, but some runs failed entirely. The successful run completed with mostly 200 OK responses.

## Pass@k Results

| Metric | Value |
|--------|-------|
| pass@1 | **53.85%** |
| pass@3 | **63.59%** |
| pass@5 | **66.67%** |

**Pass Count Distribution**:

| Pass Count | Problems | % of Dataset |
|------------|----------|--------------|
| 0/5 | 26 | 33.33% |
| 1/5 | 5 | 6.41% |
| 2/5 | 4 | 5.13% |
| 3/5 | 5 | 6.41% |
| 4/5 | 8 | 10.26% |
| 5/5 | 30 | 38.46% |

## Per-Sample Pass Rates

| Sample | Passed | Total | Rate |
|--------|--------|-------|------|
| 1 | 37 | 78 | 47.44% |
| 2 | 37 | 78 | 47.44% |
| 3 | 36 | 78 | 46.15% |
| 4 | 33 | 78 | 42.31% |
| 5 | 37 | 78 | 47.44% |
| **Mean** | **36.0** | **78** | **46.15%** |

Note: Sample 1 was the reused copilot-full run. Samples 2-5 are fresh copilot-samples runs.

## Token Usage (n=5, 364 problems from metrics.json)

| Metric | Value |
|--------|-------|
| Input Tokens | 493,072 |
| Output Tokens | 262,666 |
| **Total Tokens** | **755,738** |
| Avg Tokens/Problem | 2,076 |
| Avg Input/Problem | 1,355 |
| Avg Output/Problem | 722 |

Note: Token counts from `collect_metrics.py` aggregate all 364 metrics.json files (5 samples x ~73 problems/sample). Sample_1 was a copilot-full run with slightly different structure, so the token count may be an underestimate.

## Harness Execution Time

| Statistic | Value |
|-----------|-------|
| **Total Time** | **314.79s (5.25min)** |
| **Average** | **4.04s/problem** |
| Min | 0.00s |
| Max | 41.29s |
| Data Points | 78 |

## Output Files

| File | Description |
|------|-------------|
| `work_copilot-samples_gpt_nonagentic_cid003_n5/` | Full work directory |
| `work_copilot-samples_gpt_nonagentic_cid003_n5/composite_report.json` | Combined results |
| `work_copilot-samples_gpt_nonagentic_cid003_n5/sample_N/raw_result.json` | Per-sample raw results |
| `gpt54_cid003_summary.json` | Token/time/cost metrics |
| `experiments/pass_at_k_gpt54_cid003.json` | Pass@k JSON results |

## Cross-Model Comparison (cid003, n=5)

| Model | Pass@1 | Pass@3 | Pass@5 | Total Tokens | Harness Time |
|-------|--------|--------|--------|-------------|-------------|
| **kimi-k2.5** | **53.59%** | **65.13%** | **69.23%** | 904,699 | 3.93s |
| **gpt-5.4** | 53.85% | 63.59% | 66.67% | 755,738 | 4.04s |
| deepseek-v3.2 | 40.00% | 54.23% | 61.54% | 722,976 | 3.33s |

### Key Observations

1. **gpt-5.4 vs kimi-k2.5**: Nearly identical pass@1 (53.85% vs 53.59%, +0.26pp). However, kimi-k2.5 pulls ahead at pass@3 (+1.54pp) and pass@5 (+2.56pp), indicating better consistency across multiple attempts for the problems it can solve.
2. **gpt-5.4 vs deepseek-v3.2**: gpt-5.4 leads by +13.85pp at pass@1, +9.36pp at pass@3, and +5.13pp at pass@5.
3. **Token efficiency**: gpt-5.4 uses the fewest tokens (755K vs 905K for kimi, 723K for deepseek), with notably lower output tokens (263K vs 413K for kimi), suggesting more concise code generation.
4. **Pass@5/Pass@1 ratio**: gpt-5.4 has 1.24x (66.67/53.85), kimi-k2.5 has 1.29x (69.23/53.59), deepseek-v3.2 has 1.54x (61.54/40.00). Higher ratios indicate more problems are solvable with enough attempts. Deepseek-v3.2 benefits most from multiple attempts.
