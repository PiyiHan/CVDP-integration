# Experiment Record: Kimi-K2.5 Agentic CID003 Full Benchmark

## Experiment Metadata

- **Date**: 2026-04-05
- **Dataset**: cvdp_v1.0.4_agentic_cid003.jsonl (34 problems, cid003 category, easy/medium/hard)
- **Model**: kimi-k2.5 (via OpenAI-compatible proxy)
- **Mode**: Agentic (deco-meta-agent, Docker container with ReAct agent, tool calls)
- **Configuration**: n=1, k=1 (single run, Pass@1), REACT_MAX_STEPS=10
- **Output Directory**: `work_full_deco_agentic_cid003/`
- **Total Runtime**: ~60 minutes
- **API Integration**: OpenAI-compatible API via `ChatOpenAI` (langchain_openai)

## Run Status

**Run completed successfully** -- all 34 problems processed.

| Metric | Value |
|--------|-------|
| Problems Started | 34 |
| Agent Executions | 34/34 |
| Metrics Files Found | 34 |
| Harness Executions | 35 (one problem has 2 test cases) |

## Benchmark Results

| Metric | Value |
|--------|-------|
| Total Problems | 34 |
| Passed | 13 |
| Failed | 21 |
| **Problem Pass Rate** | **38.24%** |
| Test Pass Rate | 37.14% (13/35) |

**By Difficulty**:

| Difficulty | Total | Pass | Fail | Rate |
|-----------|-------|------|------|------|
| Easy | 5 | 4 | 1 | 80.00% |
| Medium | 25 | 9 | 16 | 36.00% |
| Hard | 4 | 0 | 4 | 0.00% |

## Token Usage (34 problems)

| Metric | Value |
|--------|-------|
| Input Tokens | 2,572,602 |
| Output Tokens | 236,882 |
| **Total Tokens** | **2,809,484** |
| Avg Tokens/Problem | 82,632 |

## Harness Execution Time

| Metric | Value |
|--------|-------|
| Total Time | 101.59s |
| Avg Time | 2.99s/problem |
| Min | 0.00s |
| Max | 14.72s |
| Data Points | 34 |

## Failing Problems (21)

### Hard (4/4 failed)
1. cvdp_agentic_DES_0001 - Agent error: Agent process exited with non-zero status: 1
2. cvdp_agentic_dynamic_equalizer_0001
3. cvdp_agentic_ethernet_mii_0006
4. cvdp_agentic_rc5_0001

### Medium (16/25 failed)
5. cvdp_agentic_PCIe_endpoint_0001
6. cvdp_agentic_async_fifo_compute_ram_application_0001
7. cvdp_agentic_axis_to_uart_0001
8. cvdp_agentic_cache_controller_0001
9. cvdp_agentic_cipher_0001
10. cvdp_agentic_csr_using_apb_interface_0001
11. cvdp_agentic_dma_xfer_engine_0001
12. cvdp_agentic_door_lock_0001
13. cvdp_agentic_ethernet_mii_0004
14. cvdp_agentic_phase_rotation_0038
15. cvdp_agentic_queue_0001
16. cvdp_agentic_rgb_color_space_conversion_0001
17. cvdp_agentic_sigma_delta_audio_0001
18. cvdp_agentic_spi_flash_interface_0001
19. cvdp_agentic_sync_serial_communication_0001
20. cvdp_agentic_traffic_light_controller_0001
21. cvdp_agentic_uart_0001

### Easy (1/5 failed)
22. cvdp_agentic_cic_decimator_0001

## Passing Problems (13)

### Easy (4/5)
1. cvdp_agentic_4bit_down_counter_0001
2. cvdp_agentic_alarm_clock_0001
3. cvdp_agentic_binary_to_gray_0001
4. cvdp_agentic_pwm_generator_0001

### Medium (9/25)
5. cvdp_agentic_direct_map_cache_0001
6. cvdp_agentic_gray_to_binary_0001
7. cvdp_agentic_i2c_master_0001
8. cvdp_agentic_lfsr_0001
9. cvdp_agentic_neural_network_mac_0001
10. cvdp_agentic_shift_register_srl_0001
11. cvdp_agentic_uart_tx_0001
12. cvdp_agentic_up_down_counter_0001
13. cvdp_agentic_axis_to_uart_0004

## Comparison: Agentic vs Copilot on CID003

| Metric | DeepSeek v3-2 (Copilot) | GPT-5.4 (Copilot) | Claude 4.6 (Copilot) | **Kimi-K2.5 (Agentic)** |
|--------|------------------------|-------------------|---------------------|------------------------|
| Pass Rate | 39.74% | 52.56% | 57.69% | **38.24%** |
| Problems | 78 (non-agentic) | 78 (non-agentic) | 78 (non-agentic) | 34 (agentic) |

Note: The copilot results are on the 78-problem non-agentic CID003 dataset, while this agentic run is on the 34-problem agentic CID003 dataset. The problems are different (agentic problems tend to be more complex, multi-file tasks), so direct comparison is not apples-to-apples.

## Key Observations

1. **38.24% pass rate** on CID003 agentic problems -- these are significantly harder than VerilogEval (99.36%)
2. All 4 hard problems failed (DES, dynamic_equalizer, ethernet_mii, rc5)
3. Easy problems have 80% pass rate, medium 36%, hard 0%
4. Token usage per problem (~82K) is ~3x VerilogEval (~27K) due to more complex, multi-step tasks
5. DES problem had an agent crash (non-zero exit code), possibly hitting the REACT_MAX_STEPS=10 limit
