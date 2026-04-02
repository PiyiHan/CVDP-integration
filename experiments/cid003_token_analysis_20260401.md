# Experiment Record: CVDP cid003 Token Usage & Cost Analysis

## Experiment Metadata

- **Date**: 2026-04-01
- **Dataset**: cvdp_v1.0.4_nonagentic_cid003.jsonl (78 problems, cid003 category)
- **Model**: deepseek-v3-2-251201
- **Mode**: Copilot (LLM API direct, no Docker agent)
- **Configuration**: n=10, k=1 (Pass@10 evaluation)
- **Output Directory**: `work_copilot-samples_deepseek_nonagentic_cid003_n10/`
- **MODEL_TIMEOUT**: 180s (前 71 个用默认 60s，3 个超时问题重跑时设为 180s)

## Run Status

⚠️ **Run interrupted** - Only 1 out of 10 samples completed successfully.

| Sample | Status | Problems Completed | Metrics Files |
|--------|--------|-------------------|---------------|
| sample_1 | ✅ Completed | 74/78 (3 re-run) | 74 |
| sample_2-10 | ❌ Not completed | 6 (partial) | 6 |

**3 problems re-run** due to API timeout during initial run (MODEL_TIMEOUT=60s → 180s):
- `cvdp_copilot_apb_gpio_0001` — 4,388 tokens, harness 2.90s
- `cvdp_copilot_axi_register_0001` — 4,703 tokens, harness 4.00s
- `cvdp_copilot_axil_precision_counter_0001` — 6,379 tokens, harness 3.97s

## Token Usage (Sample 1 - 74 problems, after re-run)

| Metric | Value |
|--------|-------|
| Input Tokens | 102,036 |
| Output Tokens | 69,652 |
| **Total Tokens** | **171,688** |
| Avg Tokens/Problem | 2,320 |

## Cost Calculation

**Pricing (DeepSeek via shubiaobiao.cn)**:
- 1M Input Tokens (Cache Hit): $0.028
- 1M Input Tokens (Cache Miss): $0.28
- 1M Output Tokens: $0.42

**Sample 1 Costs** (74 problems):

| Scenario | Input Cost | Output Cost | Total |
|----------|-----------|-------------|-------|
| All Cache Hit | $0.0029 | $0.0293 | $0.0321 |
| All Cache Miss | $0.0286 | $0.0293 | $0.0578 |
| 50% Cache Hit | $0.0157 | $0.0293 | $0.0450 |

**Estimated Full Run Costs** (n=10, ~740 problems, extrapolated):

| Scenario | Input Cost | Output Cost | Total |
|----------|-----------|-------------|-------|
| All Cache Hit | $0.029 | $0.293 | $0.321 |
| All Cache Miss | $0.286 | $0.293 | $0.578 |
| 50% Cache Hit | $0.157 | $0.293 | $0.450 |

## Benchmark Results (Sample 1)

| Metric | Value |
|--------|-------|
| Total Problems | 78 |
| Passed | 31 |
| Failed | 47 |
| **Pass Rate** | **39.74%** |

**By Difficulty**:
- Easy: 22/41 (53.66%)
- Medium: 9/37 (24.32%)

## Harness Execution Time (Sample 1)

执行时间来自 `raw_result.json` 中每个问题的 `tests[].execution` 字段（秒），是 **harness/testbench 运行时间**（iverilog/vvp 仿真），不包含 LLM 调用时间。

| 统计 | 值 |
|------|-----|
| **总时间** | **251.64s (4.19min)** |
| **平均时间** | **3.23s/problem** |
| 最小 | 1.14s |
| 最大 | 13.74s |
| 有效数据点 | 78 |

耗时最长的 5 个问题：
1. `cascaded_adder_0001` — 13.74s
2. `configurable_digital_low_pass_filter_0014` — 12.22s
3. `configurable_digital_low_pass_filter_0004` — 11.43s
4. `configurable_digital_low_pass_filter_0001` — 10.73s
5. `bcd_counter_0001` — 7.32s

## Notes

1. 初始运行有 3 个问题因 `MODEL_TIMEOUT=60s` 超时失败，设为 180s 后重跑成功
2. Run 中断后 sample_2-10 未完成（sample_1 有 `raw_result.json`，续跑会跳过）
3. Token tracking 正常工作 — 所有 74 个问题均生成 metrics.json
4. `report.txt` 中无运行时间信息，需从 `raw_result.json` 提取
5. 完成实验需重跑：`bash cvdp_benchmark.sh copilot-samples /Users/peiyihan/Codes/cvdp_benchmark/dataset/cvdp_v1.0.4_nonagentic_cid003.jsonl 10 1`

## 已知限制

### Token 覆盖问题

`dataset_processor.py:1398-1411` 在每个问题处理完后调用 `reset_token_usage()` 重置计数器，然后用 `"w"` 模式写入 `metrics.json`。当多个测例共享同一目录时，最后一个测例的 token 会覆盖前面的。

**受影响的目录**（3 个，共 7 个测例）：
- `cvdp_copilot_16qam_mapper/` — 2 个测例（_0001, _0006）
- `cvdp_copilot_configurable_digital_low_pass_filter/` — 3 个测例（_0001, _0004, _0014）
- `cvdp_copilot_hamming_code_tx_and_rx/` — 2 个测例（_0001, _0003）

**影响**：约 4 个测例的 token 被覆盖丢失，估计低估 ~10,000 tokens（~6%）。成功率不受影响（pass rate 基于 testbench 结果，每个测例独立记录在 `raw_result.json`）。
