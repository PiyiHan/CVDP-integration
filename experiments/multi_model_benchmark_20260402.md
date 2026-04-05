# Experiment Record: CVDP Multi-Model Benchmark (n=5)

## Experiment Metadata

- **Date**: 2026-04-02 ~ 2026-04-03
- **Datasets**:
  - cvdp_v1.0.4_nonagentic_cid003.jsonl (78 problems, cid003 category)
  - verilogeval.jsonl (157 problems, all easy difficulty)
- **Mode**: Copilot (LLM API direct, no Docker agent)
- **Configuration**: n=5, k=1 (Pass@5 evaluation)
- **API Endpoint**: https://api.openai-proxy.org/v1
- **API Key**: <see ~/.zshrc and .env>
- **MODEL_TIMEOUT**: 180s

## Data Collection & Analysis Pipeline

```
cvdp_benchmark.sh
  └─> run_samples.py
        ├─> sample_N/raw_result.json     (per-sample raw output)
        ├─> sample_N/*/metrics.json      (per-problem token usage)
        └─> composite_report.json        (combined pass/fail per problem)

Analysis scripts (in cvdp_integration/scripts/):
  collect_metrics.py <work_dir> --json <model>_summary.json
    Source: sample_N/*/metrics.json
    Output: token counts, harness execution times, costs

  compute_pass_at_k.py <work_dir> [--json output.json]
    Source: composite_report.json
    Output: pass@1, pass@3, pass@5 using Codex formula
    Formula: pass@k = 1 - C(n-c, k) / C(n, k), averaged over all problems
    Can accept multiple work dirs at once for batch computation
```

**Example commands**:
```bash
# Collect token/time metrics
python3 scripts/collect_metrics.py <work_dir>/ --json <model>_summary.json

# Compute pass@k (single model)
python3 scripts/compute_pass_at_k.py <work_dir>/

# Compute pass@k (multiple models, save to JSON)
python3 scripts/compute_pass_at_k.py <dir1> <dir2> <dir3> --json experiments/pass_at_k_results.json
```

## Models Tested

| Model | Status | Samples | Output Directory |
|-------|--------|---------|-----------------|
| kimi-k2.5 | ✅ Completed | 5/5 | `work_copilot-samples_kimi_nonagentic_cid003_n5/` |
| gpt-5.4 | ✅ Completed | 5/5 | `work_copilot-samples_gpt_nonagentic_cid003_n5/` |
| qwen3.5-plus | ✅ Completed | 5/5 | `work_copilot-samples_qwen3.5_nonagentic_cid003_n5/` |
| deepseek-v3.2 | ✅ Completed | 5/5 | `work_copilot-samples_deepseek_nonagentic_cid003_n5/` |
| glm-5 | ❌ Skipped | - | - (too slow, replaced by qwen3.5-plus) |

### VerilogEval Dataset

| Model | cid003 Status | VerilogEval Status | VerilogEval Output Directory |
|-------|--------------|-------------------|------------------------------|
| kimi-k2.5 | ✅ Completed | ✅ Completed | `work_copilot-samples_kimi_verilogeval_n5/` |
| gpt-5.4 | ✅ Completed | 🔲 Not started | - |
| qwen3.5-plus | ✅ Completed | ✅ Completed | `work_copilot-samples_qwen3.5_verilogeval_n5/` |
| deepseek-v3.2 | ✅ Completed | ✅ Completed | `work_copilot-samples_deepseek_verilogeval_n5/` |

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

## deepseek-v3.2 Results

### Benchmark Results (Pass@1, n=5)

| Metric | Value |
|--------|-------|
| Total Problems | 78 |
| Passed Problems | 31.2 |
| Failed Problems | 46.8 |
| **Pass Rate** | **40.00%** |
| StdDev | 5.24% |

**By Difficulty**:

| Difficulty | Total | Pass | Rate | StdDev |
|------------|-------|------|------|--------|
| Easy | 41 | 22.6 | 55.12% | 7.83% |
| Medium | 37 | 8.6 | 23.24% | 5.60% |

**Per-Sample Pass Rates**:

| Sample | Passed | Total | Rate |
|--------|--------|-------|------|
| 1 | 35 | 78 | 44.87% |
| 2 | 35 | 78 | 44.87% |
| 3 | 32 | 78 | 41.03% |
| 4 | 28 | 78 | 35.90% |
| 5 | 26 | 78 | 33.33% |

**Pass@1 Distribution**:

| Pass Count | Problems | % of Dataset | Pass@1 Probability |
|------------|----------|--------------|-------------------|
| 0/5 | 30 | 38.46% | 0.00% |
| 1/5 | 13 | 16.67% | 20.00% |
| 2/5 | 5 | 6.41% | 40.00% |
| 3/5 | 4 | 5.13% | 60.00% |
| 4/5 | 9 | 11.54% | 80.00% |
| 5/5 | 17 | 21.79% | 100.00% |

### Token Usage (n=5, 296 problems total)

| Metric | Value |
|--------|-------|
| Input Tokens | 408,144 |
| Output Tokens | 314,832 |
| **Total Tokens** | **722,976** |
| Avg Tokens/Problem | 2,443 |
| Avg Input/Problem | 1,379 |
| Avg Output/Problem | 1,064 |

### Harness Execution Time

| Statistic | Value |
|-----------|-------|
| **Total Time** | **259.50s (4.33min)** |
| **Average** | **3.33s/problem** |
| Min | 1.08s |
| Max | 42.51s |
| Data Points | 78 |

### Cost Estimate

Pricing via openai-proxy.org (exact rates unknown, using DeepSeek reference):
- 1M Input Tokens: ~$0.28
- 1M Output Tokens: ~$0.42

| Scenario | Input Cost | Output Cost | Total |
|----------|-----------|-------------|-------|
| Estimated | $0.114 | $0.132 | ~$0.247 |

### Notes

1. deepseek-v3.2 samples 1-4 completed initially, sample_5 crashed with `ValueError: Unsupported model type: deepseek-v3.2` in `model_factory.py`
2. Fixed by changing `model_factory.py` else branch from `raise ValueError` to `return self._create_openai_instance()`
3. Sample_5 resumed and completed successfully
4. Noticeable performance decline across samples (44.87% → 33.33%), suggesting potential temperature or prompt variability sensitivity

---

## qwen3.5-plus Results

### Benchmark Results (Pass@1, n=5)

| Metric | Value |
|--------|-------|
| Total Problems | 78 |
| **Pass Rate** | **37.44%** |
| Pass@3 | **57.05%** |
| Pass@5 | **62.82%** |

**Per-Sample Pass Rates**:

| Sample | Passed | Total | Rate |
|--------|--------|-------|------|
| 1 | 23 | 78 | 29.49% |
| 2 | 31 | 78 | 39.74% |
| 3 | 33 | 78 | 42.31% |
| 4 | 31 | 78 | 39.74% |
| 5 | 28 | 78 | 35.90% |

**Pass@1 Distribution**:

| Pass Count | Problems | % of Dataset |
|------------|----------|--------------|
| 0/5 | 29 | 37.18% |
| 1/5 | 9 | 11.54% |
| 2/5 | 9 | 11.54% |
| 3/5 | 12 | 15.38% |
| 4/5 | 12 | 15.38% |
| 5/5 | 7 | 8.97% |

### Token Usage (n=5, 295 problems total)

| Metric | Value |
|--------|-------|
| Input Tokens | 417,349 |
| Output Tokens | 2,376,261 |
| **Total Tokens** | **2,793,610** |
| Avg Tokens/Problem | 9,472 |

### Harness Execution Time

| Statistic | Value |
|-----------|-------|
| **Total Time** | **234.59s (3.91min)** |
| **Average** | **3.01s/problem** |
| Min | 0.00s |
| Max | 40.03s |

### Notes

1. qwen3.5-plus has the lowest pass@1 (37.44%) among all 4 models on cid003
2. Pass@3 (57.05%) and pass@5 (62.82%) are close to deepseek-v3.2, suggesting it solves different problems per sample but is inconsistent
3. Notably highest token usage (2.79M) — ~3x more than other models, despite similar problem count (295 vs 296-370)
4. Output tokens dominate (2.38M vs 417K input), suggesting very verbose code generation
5. sample_1 significantly underperformed (29.49%), samples 2-4 were more consistent (39-42%)
6. Proxy timeouts were frequent during the run, especially on sample_4 (sorter_0001 stalled ~20 min)

---

## Cross-Model Comparison (cid003, n=5)

| Model | Pass@1 | Pass@3 | Pass@5 | Easy | Medium | Total Tokens | Harness Time |
|-------|--------|--------|--------|------|--------|-------------|-------------|
| **kimi-k2.5** | **53.59%** | **65.13%** | **69.23%** | 71.71% | 33.51% | 904,699 | 3.93s |
| gpt-5.4 | 53.85% | 63.59% | 66.67% | - | - | 755,738 | 4.04s |
| deepseek-v3.2 | 40.00% | 54.23% | 61.54% | 55.12% | 23.24% | 722,976 | 3.33s |
| qwen3.5-plus | 37.44% | 57.05% | 62.82% | - | - | 2,793,610 | 3.01s |

pass@k uses the Codex formula: `pass@k = 1 - C(n-c, k) / C(n, k)` averaged over all problems, where n=5 and c is the number of correct samples per problem. gpt-5.4 matches kimi-k2.5 at pass@1 (+0.26pp) but falls behind at pass@3 (-1.54pp) and pass@5 (-2.56pp). qwen3.5-plus has the lowest pass@1 (37.44%) but competitive pass@3/5, with notably the highest token usage (2.79M). See `gpt54_cid003_benchmark_20260403.md` for full details.

---

## VerilogEval Dataset Results

### kimi-k2.5 VerilogEval Results (Pass@1, n=5)

| Metric | Value |
|--------|-------|
| Total Problems | 157 |
| Passed Problems | 138.4 |
| Failed Problems | 18.6 |
| **Pass Rate** | **88.15%** |
| StdDev | 1.24% |

**Per-Sample Pass Rates**:

| Sample | Passed | Total | Rate |
|--------|--------|-------|------|
| 1 | 141 | 157 | 89.81% |
| 2 | 136 | 157 | 86.62% |
| 3 | 139 | 157 | 88.54% |
| 4 | 137 | 157 | 87.26% |
| 5 | 139 | 157 | 88.54% |

**Pass@1 Distribution**:

| Pass Count | Problems | % of Dataset | Pass@1 Probability |
|------------|----------|--------------|-------------------|
| 0/5 | 9 | 5.73% | 0.00% |
| 1/5 | 8 | 5.10% | 20.00% |
| 2/5 | 2 | 1.27% | 40.00% |
| 3/5 | 3 | 1.91% | 60.00% |
| 4/5 | 4 | 2.55% | 80.00% |
| 5/5 | 131 | 83.44% | 100.00% |

**Token Usage** (n=5, 628 problems total):

| Metric | Value |
|--------|-------|
| Input Tokens | 1,155,600 |
| Output Tokens | 239,410 |
| **Total Tokens** | **1,395,010** |
| Avg Tokens/Problem | 2,221 |

**Harness Execution Time**:

| Statistic | Value |
|-----------|-------|
| **Total Time** | **257.50s (4.29min)** |
| **Average** | **1.64s/problem** |
| Min | 0.99s |
| Max | 11.85s |

### deepseek-v3.2 VerilogEval Results (Pass@1, n=5)

| Metric | Value |
|--------|-------|
| Total Problems | 157 |
| Passed Problems | 132.0 |
| Failed Problems | 25.0 |
| **Pass Rate** | **84.08%** |
| StdDev | 1.74% |

**Per-Sample Pass Rates**:

| Sample | Passed | Total | Rate |
|--------|--------|-------|------|
| 1 | 132 | 157 | 84.08% |
| 2 | 128 | 157 | 81.53% |
| 3 | 135 | 157 | 85.99% |
| 4 | 131 | 157 | 83.44% |
| 5 | 134 | 157 | 85.35% |

**Pass@1 Distribution**:

| Pass Count | Problems | % of Dataset | Pass@1 Probability |
|------------|----------|--------------|-------------------|
| 0/5 | 8 | 5.10% | 0.00% |
| 1/5 | 5 | 3.18% | 20.00% |
| 2/5 | 8 | 5.10% | 40.00% |
| 3/5 | 11 | 7.01% | 60.00% |
| 4/5 | 19 | 12.10% | 80.00% |
| 5/5 | 106 | 67.52% | 100.00% |

**Token Usage** (n=5, 628 problems total):

| Metric | Value |
|--------|-------|
| Input Tokens | 1,212,852 |
| Output Tokens | 174,468 |
| **Total Tokens** | **1,387,320** |
| Avg Tokens/Problem | 2,210 |

**Harness Execution Time**:

| Statistic | Value |
|-----------|-------|
| **Total Time** | **268.68s (4.48min)** |
| **Average** | **1.71s/problem** |
| Min | 1.29s |
| Max | 6.97s |

### qwen3.5-plus VerilogEval Results (Pass@1, n=5)

| Metric | Value |
|--------|-------|
| Total Problems | 157 |
| **Pass Rate** | **87.26%** |
| Pass@3 | **97.01%** |
| Pass@5 | **97.45%** |

**Per-Sample Pass Rates**:

| Sample | Passed | Total | Rate |
|--------|--------|-------|------|
| 1 | 139 | 157 | 88.54% |
| 2 | 139 | 157 | 88.54% |
| 3 | 136 | 157 | 86.62% |
| 4 | 135 | 157 | 85.99% |
| 5 | 136 | 157 | 86.62% |

**Pass@1 Distribution**:

| Pass Count | Problems | % of Dataset |
|------------|----------|--------------|
| 0/5 | 4 | 2.55% |
| 1/5 | 1 | 0.64% |
| 2/5 | 3 | 1.91% |
| 3/5 | 10 | 6.37% |
| 4/5 | 47 | 29.94% |
| 5/5 | 92 | 58.60% |

**Token Usage** (n=5, 785 problems total):

| Metric | Value |
|--------|-------|
| Input Tokens | 1,587,855 |
| Output Tokens | 3,206,140 |
| **Total Tokens** | **4,793,995** |
| Avg Tokens/Problem | 3,054 |

**Harness Execution Time**:

| Statistic | Value |
|-----------|-------|
| **Total Time** | **220.98s (3.68min)** |
| **Average** | **1.41s/problem** |
| Min | 1.01s |
| Max | 2.54s |

### Notes

1. qwen3.5-plus has outstanding pass@3 (97.01%) and pass@5 (97.45%) on VerilogEval — best among all models
2. pass@1 (87.26%) is slightly below kimi-k2.5 (88.15%) but well above deepseek-v3.2 (84.08%)
3. The large gap between pass@1 (87.26%) and pass@5 (97.45%) means many problems are solved by at least 1 out of 5 samples but not consistently
4. Only 4 problems (2.55%) are never solved (0/5), compared to 9 for kimi and 8 for deepseek
5. Token usage is ~3.4x higher than other models (4.79M vs ~1.39M), consistent with cid003 behavior
6. Output tokens (3.21M) are 2x the input (1.59M), suggesting verbose Verilog generation

### VerilogEval Cross-Model Comparison

| Model | Pass@1 | Pass@3 | Pass@5 | Total Tokens | Avg Tokens/Problem | Harness Time |
|-------|--------|--------|--------|-------------|-------------------|-------------|
| kimi-k2.5 | **88.15%** | 92.10% | 94.27% | 1,395,010 | 2,221 | 1.64s |
| qwen3.5-plus | 87.26% | **97.01%** | **97.45%** | 4,793,995 | 3,054 | 1.41s |
| deepseek-v3.2 | 84.08% | 93.12% | 94.90% | 1,387,320 | 2,210 | 1.71s |

qwen3.5-plus dominates VerilogEval at pass@3 (97.01%) and pass@5 (97.45%), far surpassing kimi-k2.5 (92.10%/94.27%) and deepseek-v3.2 (93.12%/94.90%). Its pass@1 (87.26%) is comparable to kimi-k2.5 (88.15%). The high pass@3/5 gap over pass@1 suggests it solves different problems per sample. However, it uses ~3.4x more tokens than other models.

---

## Known Limitations

### Token Overwrite Issue

`dataset_processor.py:1398-1411` resets token usage after each problem and writes `metrics.json` in `"w"` mode. When multiple problem variants share a directory, the last variant overwrites previous token counts.

**Affected directories** (3 dirs, 7 variants total):
- `cvdp_copilot_16qam_mapper/` — 2 variants (_0001, _0006)
- `cvdp_copilot_configurable_digital_low_pass_filter/` — 3 variants (_0001, _0004, _0014)
- `cvdp_copilot_hamming_code_tx_and_rx/` — 2 variants (_0001, _0003)

**Impact**: ~4 variants' tokens overwritten, underestimates ~6%. Pass rates unaffected.
