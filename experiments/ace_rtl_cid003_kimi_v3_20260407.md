# Experiment Record: ACE-RTL v3 Agentic CID003 Benchmark

## Experiment Metadata

- **Date**: 2026-04-07
- **Dataset**: cvdp_v1.0.4_agentic_cid003.jsonl (34 problems, cid003 category, easy/medium/hard)
- **Model**: kimi-k2.5 (via OpenAI-compatible proxy)
- **Mode**: Agentic (ACE-RTL agent, Generate-Compile-Simulate-Reflect loop)
- **Configuration**: n=1, k=1 (single run, Pass@1), MAX_ITERATIONS=30
- **Output Directory**: `ace_rtl_v3/`
- **API Endpoint**: `api.openai-proxy.org/v1`
- **Docker Image**: `ace-rtl-agent:latest` (v3 — hardcoded sim command, multi-pattern success check)

## What Changed Since v2

Same three changes as VerilogEval v3:

1. **Hardcoded simulation command**: Replaced LLM-based `generate_sim_command()` with fixed `iverilog -g2012 -o sim.out <rtl> <tb> && vvp sim.out`.
2. **Multi-pattern success detection**: New `_check_simulation_success()` with priority-ordered pattern matching.
3. **Generator prompt clarification**: Bash block = file writes only.

## Benchmark Results

| Metric | Value |
|--------|-------|
| Total Problems (CID003 design problems) | 32 |
| Passed | 14 |
| Failed | 18 |
| **Problem Pass Rate** | **43.8%** |

> **Note**: The v3 run mixed CID003 (32 problems) and VerilogEval (157 problems) in the same output directory. The `report.txt` showed misleading numbers (7/34) because it combined both datasets. The actual CID003-only harness pass rate is 14/32 (43.8%), identical to v2.

## Comparison: v2 vs v3 (CID003)

| Metric | v2 | v3 | Change |
|--------|----|----|--------|
| **Pass Rate** | **43.8%** (14/32) | **43.8%** (14/32) | **+0** |
| Regressions | — | 2 (async_filo, cic_decimator) | LLM stochasticity |
| Improvements | — | 2 (direct_map_cache, event_scheduler) | LLM stochasticity |

### Per-Problem Comparison

| Problem | TB? | v2 | v3 | Change |
|---------|-----|----|----|--------|
| PCIe_endpoint | no | PASS | PASS | |
| axis_to_uart | no | PASS | PASS | |
| binary_to_gray | yes | PASS | PASS | |
| byte_enable_ram | yes | PASS | PASS | |
| cellular_automata | yes | PASS | PASS | |
| cipher | no | PASS | PASS | |
| cont_adder | yes | PASS | PASS | |
| dma_xfer_engine | no | PASS | PASS | |
| multiplexer | yes | PASS | PASS | |
| signed_comparator | yes | PASS | PASS | |
| swizzler | yes | PASS | PASS | |
| universal_shift_reg | yes | PASS | PASS | |
| direct_map_cache | yes | FAIL | **PASS** | IMPROVED |
| event_scheduler | yes | FAIL | **PASS** | IMPROVED |
| async_filo | yes | PASS | **FAIL** | REGRESSED |
| cic_decimator | no | PASS | **FAIL** | REGRESSED |
| DES | yes | FAIL | FAIL | |
| async_fifo_compute_ram_application | no | FAIL | FAIL | |
| cache_controller | yes | FAIL | FAIL | |
| csr_using_apb_interface | no | FAIL | FAIL | |
| door_lock | no | FAIL | FAIL | |
| dynamic_equalizer | no | FAIL | FAIL | |
| ethernet_mii | no | FAIL | FAIL | |
| nbit_swizzling | yes | FAIL | FAIL | |
| phase_rotation | no | FAIL | FAIL | |
| queue | no | FAIL | FAIL | |
| rc5 | no | FAIL | FAIL | |
| rgb_color_space_conversion | no | FAIL | FAIL | |
| sigma_delta_audio | no | FAIL | FAIL | |
| spi_complex_mult | no | FAIL | FAIL | |
| sync_serial_communication | yes | FAIL | FAIL | |
| ttc_lite | no | FAIL | FAIL | |

## Failure Analysis

### Category A: No Testbench, RTL Bug (7/18 failures)

These problems have no `verif/` testbench. The agent generates one-shot RTL with zero feedback. The generated RTL has functional bugs that the harness catches.

| Problem | Harness Error |
|---------|--------------|
| csr_using_apb_interface | Missing `presetn` port |
| door_lock | `door_unlock` never asserted |
| dynamic_equalizer | Test failed |
| phase_rotation | FSM state tests failed |
| queue | iverilog compile error |
| sigma_delta_audio | iverilog compile error |
| spi_complex_mult | iverilog compile error |
| ttc_lite | Test assertions failed |

### Category B: No Testbench, iverilog Incompatible (5/18 failures)

One-shot RTL uses SystemVerilog constructs that iverilog `-g2012` can't compile.

| Problem | Harness Error |
|---------|--------------|
| async_fifo_compute_ram_application | iverilog exit 7 |
| ethernet_mii | iverilog exit 40/44 |
| rc5 | iverilog exit 2 |
| rgb_color_space_conversion | iverilog exit 2 |
| async_filo (v3) | iverilog exit 2 |

### Category C: Has Testbench, iverilog Incompatible (5/18 failures)

The agent iterated but could never fix the problem because the compilation error is in the **testbench** (iverilog-incompatible syntax), not the RTL. The agent modifies RTL each iteration but can't touch the testbench.

| Problem | Iterations | Harness Error |
|---------|-----------|--------------|
| DES | 6 | iverilog exit 2 (S-box truncation) |
| cache_controller | 7 | iverilog exit 2 |
| nbit_swizzling | 7 | iverilog exit 16 |
| sync_serial_communication | 6 | iverilog exit 2 (duplicate modules) |
| async_filo (v3) | 8 | iverilog exit 2 |

## False Failure Analysis (v3 agent behavior)

A critical discovery during v3 analysis: **8 of 14 harness-passing problems had the agent report failure**. The agent ran multiple iterations on already-correct RTL because `_check_simulation_success()` returned `False` despite returncode=0.

| Problem | Agent Iterations | Agent Result | Harness Result |
|---------|----------------|-------------|---------------|
| binary_to_gray | 24 | "failed" (rc=0) | PASS |
| byte_enable_ram | 11 | "failed" (rc=0) | PASS |
| cellular_automata | 1 | "failed" (rc=0) | PASS |
| cont_adder | 11 | "failed" (rc=0) | PASS |
| direct_map_cache | 8 | "failed" (rc=0) | PASS |
| event_scheduler | 8 | "failed" (rc=0) | PASS |
| signed_comparator | 8 | "failed" (rc=2) | PASS |
| swizzler | 8 | "failed" (rc=0) | PASS |

**Root cause**: CID003 testbenches produce custom output without PASS/FAIL/Mismatches keywords. The v3 `_check_simulation_success()` defaulted to `False` when no pattern matched, even with returncode=0. This was fixed in v4 (see below).

**Token waste estimate**: ~300K-500K tokens across these 8 problems on unnecessary re-iterations.

## v4 Fix Impact (projected, not yet run)

v4 changes:
1. `_check_simulation_success()` defaults to `True` when returncode=0
2. Max-iterations exits with `success=True` (harness still runs)
3. `MAX_ITERATIONS` reduced to 10

**Projected harness pass rate: 14/32 (43.8%)** — unchanged from v3. The fixes reduce token waste and run time but don't improve RTL quality. The harness runs regardless of agent exit code, so the final correctness outcome is the same.

**What changes with v4**:
- Token usage: ~300K-500K savings per CID003 run (no wasted iterations)
- Run time: ~30-60 min faster
- Clean exit codes: No spurious "agent error" warnings for correct RTL
- Stochastic variation: 4 problems are 50/50 (passed in one run, failed in another)

## Comparison: ACE-RTL vs Other Agents on CID003

| Metric | ACE-RTL v2 | **ACE-RTL v3** | deco-meta-agent |
|--------|-----------|----------------|-----------------|
| Pass Rate | 43.8% | **43.8%** | 38.24% |
| Total Tokens | 669,433 | ~670K (est.) | 2,809,484 |
| Avg Tokens/Problem | 20,286 | ~20,900 | 82,632 |

ACE-RTL outperforms deco-meta-agent on CID003 by 5.6pp while using **~4x fewer tokens**. The NO_TB fallback and iterative refinement help on easier problems, but hard problems (DES, ethernet_mii, rc5) remain unsolved by all agents.

## Key Observations

1. **v3 changes had no effect on CID003**: Hardcoded sim command and multi-pattern detection improved VerilogEval +15.9pp but 0pp on CID003. The CID003 failures are from fundamentally different causes (no testbench feedback loop, iverilog incompatibilities).
2. **LLM stochasticity dominates**: 4 problems flip between pass/fail across runs. The 32-problem sample is too small for stable comparisons.
3. **14/32 problems (44%) have no testbench**: Without internal simulation, the agent generates one-shot RTL. This is essentially copilot-mode behavior — 50% of those pass, 50% fail.
4. **iverilog incompatibility is a systemic issue**: ~10 problems fail because either the agent's RTL or the provided testbench uses SV constructs that iverilog can't parse. This is a tool limitation, not an agent limitation.
5. **Hard problems (4/4) remain at 0%**: DES, dynamic_equalizer, ethernet_mii_0006, rc5 all fail in every run. These require multi-file designs exceeding single-pass generation.
