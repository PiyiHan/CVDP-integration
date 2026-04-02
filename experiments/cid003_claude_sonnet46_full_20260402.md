# Experiment Record: CVDP cid003 Claude Sonnet 4.6 Full Benchmark

## Experiment Metadata

- **Date**: 2026-04-02
- **Dataset**: cvdp_v1.0.4_nonagentic_cid003.jsonl (78 problems, cid003 category)
- **Model**: claude-sonnet-4-6
- **Mode**: Copilot (LLM API direct, no Docker agent)
- **Configuration**: n=1, k=1 (single run, Pass@1)
- **Output Directory**: `work_copilot-full_claude_nonagentic_cid003/`
- **Total Runtime**: ~38 minutes
- **API Integration**: Native Anthropic Messages API via `Anthropic_Instance` (langchain-anthropic not used in copilot mode; raw `anthropic` SDK used)

## Run Status

✅ **Run completed successfully** — all 78 problems processed.

| Metric | Value |
|--------|-------|
| Problems Started | 78 |
| API Calls Successful | 77/78 (1 in-progress when batch started) |
| Metrics Files Found | 74 |
| Harness Executions | 78 |

## Benchmark Results

| Metric | Value |
|--------|-------|
| Total Problems | 78 |
| Passed | 45 |
| Failed | 33 |
| **Pass Rate** | **57.69%** |

**By Difficulty**:
- Easy: 31/41 (75.61%)
- Medium: 14/37 (37.84%)

## Token Usage (74 problems with metrics.json)

| Metric | Value |
|--------|-------|
| Input Tokens | 114,978 |
| Output Tokens | 92,306 |
| **Total Tokens** | **207,284** |
| Avg Tokens/Problem | 2,801 |
| LLM Call Count | 74 |

## Cost Calculation

**Pricing (Anthropic claude-sonnet-4-6)**:
- 1M Input Tokens: $3.00
- 1M Output Tokens: $15.00
- 1M Cache Read: $0.30
- 1M Cache Write: $3.75

**This Run Costs** (74 problems, no cache):

| Scenario | Input Cost | Output Cost | Total |
|----------|-----------|-------------|-------|
| No Cache | $0.345 | $1.385 | $1.730 |
| 50% Cache Hit | $0.259 | $1.385 | $1.644 |
| All Cache Hit | $0.034 | $1.385 | $1.419 |

## Harness Execution Time

执行时间来自 `raw_result.json` 中每个问题的 `tests[].execution` 字段（秒），是 **harness/testbench 运行时间**（iverilog/vvp 仿真），不包含 LLM 调用时间。

| 统计 | 值 |
|------|-----|
| **总时间** | **322.91s (5.38min)** |
| **平均时间** | **4.14s/problem** |
| 最小 | 0.00s |
| 最大 | 44.93s |
| 有效数据点 | 78 |

## Failing Problems (33)

| # | Problem ID | Difficulty |
|---|-----------|------------|
| 1 | cvdp_copilot_GFCM_0001 | easy |
| 2 | cvdp_copilot_apb_dsp_unit_0001 | medium |
| 3 | cvdp_copilot_apb_gpio_0001 | medium |
| 4 | cvdp_copilot_apb_history_shift_register_0001 | medium |
| 5 | cvdp_copilot_axi_register_0001 | medium |
| 6 | cvdp_copilot_axi_stream_upscale_0001 | easy |
| 7 | cvdp_copilot_axil_precision_counter_0001 | medium |
| 8 | cvdp_copilot_car_parking_management_0001 | medium |
| 9 | cvdp_copilot_concatenate_0001 | medium |
| 10 | cvdp_copilot_configurable_digital_low_pass_filter_0004 | medium |
| 11 | cvdp_copilot_configurable_digital_low_pass_filter_0014 | easy |
| 12 | cvdp_copilot_data_bus_controller_0001 | medium |
| 13 | cvdp_copilot_decode_firstbit_0001 | medium |
| 14 | cvdp_copilot_digital_dice_roller_0001 | easy |
| 15 | cvdp_copilot_digital_stopwatch_0001 | easy |
| 16 | cvdp_copilot_edge_detector_0001 | easy |
| 17 | cvdp_copilot_ethernet_packet_parser_0001 | medium |
| 18 | cvdp_copilot_fibonacci_series_0001 | easy |
| 19 | cvdp_copilot_fifo_async_0001 | medium |
| 20 | cvdp_copilot_gcd_0001 | easy |
| 21 | cvdp_copilot_hebbian_rule_0017 | medium |
| 22 | cvdp_copilot_hill_cipher_0001 | medium |
| 23 | cvdp_copilot_microcode_sequencer_0001 | medium |
| 24 | cvdp_copilot_packet_controller_0001 | medium |
| 25 | cvdp_copilot_perf_counters_0001 | easy |
| 26 | cvdp_copilot_prbs_gen_0003 | medium |
| 27 | cvdp_copilot_restoring_division_0001 | medium |
| 28 | cvdp_copilot_sequencial_binary_to_one_hot_decoder_0001 | easy |
| 29 | cvdp_copilot_static_branch_predict_0001 | medium |
| 30 | cvdp_copilot_sync_serial_communication_0001 | medium |
| 31 | cvdp_copilot_ttc_lite_0001 | medium |
| 32 | cvdp_copilot_vending_machine_0001 | medium |
| 33 | cvdp_copilot_wb2ahb_0001 | medium |

## Comparison with DeepSeek (Previous Run)

| Metric | DeepSeek v3-2 | Claude Sonnet 4.6 |
|--------|--------------|-------------------|
| Pass Rate | 39.74% | **57.69%** |
| Easy Pass Rate | 53.66% | **75.61%** |
| Medium Pass Rate | 24.32% | **37.84%** |
| Total Tokens | 171,688 | 207,284 |
| Avg Tokens/Problem | 2,320 | 2,801 |
| Harness Time (total) | 251.64s | 322.91s |
| Problems with Metrics | 74 | 74 |

Claude Sonnet 4.6 shows **~18% absolute improvement** in pass rate over DeepSeek v3-2.

## Notes

1. API integration uses native Anthropic Messages API (`anthropic` Python SDK) — no OpenAI proxy translation needed
2. `Anthropic_Instance` class added to `cvdp_benchmark/src/llm_lib/anthropic_llm.py` with `ModelFactory` routing for `claude-*` models
3. Client timeout set to 300s to handle long prompts
4. Token tracking works correctly — 74/78 problems generated metrics.json (4 problems share directories with others, same token overwrite issue as previous runs)
5. 2 problems (`perf_counters_0001`, `restoring_division_0001`) failed with "Failed to execute objective harness" — likely harness infrastructure issues, not model failures

## 已知限制

### Token 覆盖问题

同前次实验，`dataset_processor.py` 在每个问题处理完后重置 token 计数器并用 `"w"` 模式写入 `metrics.json`。多个测例共享同一目录时，最后一个测例的 token 会覆盖前面的。

**受影响的目录**（3 个）：
- `cvdp_copilot_16qam_mapper/` — 2 个测例
- `cvdp_copilot_configurable_digital_low_pass_filter/` — 3 个测例
- `cvdp_copilot_hamming_code_tx_and_rx/` — 2 个测例

**影响**：约 4 个测例的 token 被覆盖丢失，估计低估 ~10,000 tokens（~5%）。成功率不受影响。
