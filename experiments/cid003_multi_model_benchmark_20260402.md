# Experiment Record: CVDP cid003 Multi-Model Benchmark (n=5)

## Experiment Metadata

- **Date**: 2026-04-02
- **Dataset**: cvdp_v1.0.4_nonagentic_cid003.jsonl (78 problems, cid003 category)
- **Mode**: Copilot (LLM API direct, no Docker agent)
- **Configuration**: n=5, k=1 (Pass@5 evaluation)
- **API Endpoint**: https://api.openai-proxy.org/v1
- **API Key**: sk-tlouatg12FKqGzKPa8uwgJsLcu6W3Io1S7kpoSbo3zT1N3Sc
- **MODEL_TIMEOUT**: 180s

## Models Tested

| Model | Status | Samples | Output Directory |
|-------|--------|---------|-----------------|
| kimi-k2.5 | ✅ Completed | 5/5 | `work_copilot-samples_kimi_nonagentic_cid003_n5/` |
| qwen3.5-plus | ⏳ Running | - | `work_copilot-samples_qwen3.5_nonagentic_cid003_n5/` |
| deepseek-v3.2 | ⏳ Running | - | `work_copilot-samples_deepseek_nonagentic_cid003_n5/` |
| glm-5 | ❌ Skipped | - | - (too slow, replaced by qwen3.5-plus) |

---

## kimi-k2.5 Results

### Benchmark Results (Pass@1, n=5)

| Metric | Value |
|--------|-------|
| Total Problems | 78 |
| Passed Problems | 41.8 |
| Failed Problems | 36.2 |
| **Pass Rate** | **53.59%** |
| StdDev | 2.78% |

**By Difficulty**:

| Difficulty | Total | Pass | Rate | StdDev |
|------------|-------|------|------|--------|
| Easy | 41 | 29.4 | 71.71% | 4.43% |
| Medium | 37 | 12.4 | 33.51% | 1.48% |

**Per-Sample Pass Rates**:

| Sample | Passed | Total | Rate |
|--------|--------|-------|------|
| 1 | 40 | 78 | 51.28% |
| 2 | 43 | 78 | 55.13% |
| 3 | 39 | 78 | 50.00% |
| 4 | 43 | 78 | 55.13% |
| 5 | 44 | 78 | 56.41% |

**Pass@1 Distribution**:

| Pass Count | Problems | % of Dataset | Pass@1 Probability |
|------------|----------|--------------|-------------------|
| 0/5 | 24 | 30.77% | 0.00% |
| 1/5 | 7 | 8.97% | 20.00% |
| 2/5 | 4 | 5.13% | 40.00% |
| 3/5 | 8 | 10.26% | 60.00% |
| 4/5 | 5 | 6.41% | 80.00% |
| 5/5 | 30 | 38.46% | 100.00% |

### Token Usage (n=5, 370 problems total)

| Metric | Value |
|--------|-------|
| Input Tokens | 491,695 |
| Output Tokens | 413,004 |
| **Total Tokens** | **904,699** |
| Avg Tokens/Problem | 2,445 |
| Avg Input/Problem | 1,329 |
| Avg Output/Problem | 1,116 |

### Harness Execution Time

| Statistic | Value |
|-----------|-------|
| **Total Time** | **306.45s (5.11min)** |
| **Average** | **3.93s/problem** |
| Min | 0.00s |
| Max | 42.88s |
| Data Points | 78 |

### Cost Estimate

Pricing via openai-proxy.org (exact rates unknown, using DeepSeek reference):
- 1M Input Tokens: ~$0.28
- 1M Output Tokens: ~$0.42

| Scenario | Input Cost | Output Cost | Total |
|----------|-----------|-------------|-------|
| Estimated | $0.138 | $0.173 | ~$0.311 |

### Notes

1. kimi-k2.5 completed all 5 samples successfully in one run
2. Token overwrite issue persists (3 directories with multiple problem variants share output dirs, ~6% token underestimation)
3. glm-5 was tested but abandoned due to extremely slow API response times (each problem took 2-3+ minutes)
4. glm-5 replaced by qwen3.5-plus for the second model comparison

---

## Known Limitations

### Token Overwrite Issue

`dataset_processor.py:1398-1411` resets token usage after each problem and writes `metrics.json` in `"w"` mode. When multiple problem variants share a directory, the last variant overwrites previous token counts.

**Affected directories** (3 dirs, 7 variants total):
- `cvdp_copilot_16qam_mapper/` — 2 variants (_0001, _0006)
- `cvdp_copilot_configurable_digital_low_pass_filter/` — 3 variants (_0001, _0004, _0014)
- `cvdp_copilot_hamming_code_tx_and_rx/` — 2 variants (_0001, _0003)

**Impact**: ~4 variants' tokens overwritten, underestimates ~6%. Pass rates unaffected.
