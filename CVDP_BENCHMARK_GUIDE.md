# CVDP Benchmark集成指南

## 概述

本文档说明如何在CVDP (Chip Verification and Design Practices) 基准测试框架中集成和测试AI Agents。

## 测试环境

- **CVDP版本**: v1.0.4
- **Python版本**: 3.12 (Docker容器内)
- **工作目录**: `/Users/peiyihan/Codes/cvdp_benchmark`

## 数据集模式

CVDP通过检查数据集中`id`字段自动识别模式：

| 模式 | ID格式 | 参数 | 适用场景 |
|-------|----------|--------|----------|
| **Agentic** | 包含`'agentic'` (如`cvdp_agentic_xxx_0001`) | `-g <agent_name>` | 多步骤硬件设计任务 |
| **Non-Agentic** | 不包含`'agentic'` (如`verilogeval_Prob001_zero_0001`) | `-m <model_name>` | 单轮代码补全任务 |
| **强制Agentic** | 任意ID，使用`--force-agentic` | `-g <agent_name>` | 自定义数据集（如VerilogEval） |

## Agent集成流程

### 架构

```
CVDP Benchmark Framework
  ↓
Docker容器运行Agent
  ↓
ReAct循环: Thought → Action → Observation
  ↓
工具调用: read_file, write_file, compile_and_simulate
  ↓
输出Memory: /code/rundir/memory/_memory.json
  ↓
CVDP解析Memory并生成测试报告
```

### 执行阶段

1. **准备阶段**
   - CVDP创建Docker网络
   - 生成测试harness环境
   - 创建docker-compose配置

2. **执行阶段**
   - 启动agent容器
   - 挂载volume: docs/, rtl/, verif/, rundir/
   - 监控执行日志
   - 记录memory文件

3. **清理阶段**
   - 停止容器
   - 生成测试报告
   - 清理Docker资源

### Volume映射

| 宿主机路径 | 容器路径 | 用途 |
|------------|-----------|------|
| `./docs/` | `/code/docs/` | 规格文档 |
| `./rtl/` | `/code/rtl/` | RTL源文件（读写） |
| `./verif/` | `/code/verif/` | 测试台文件 |
| `./rundir/` | `/code/rundir/` | Agent输出和Memory |

## cvdp_benchmark.sh用法

### 命令格式

```bash
cd /Users/peiyihan/Codes/cvdp_integration
./cvdp_benchmark.sh <command> [args...]
```

### 输出目录自动命名

默认输出前缀由**模式、模型/agent、数据集、问题ID、样本数**拼接生成：

```
work_{mode}_{model|agent}_{dataset}[_{problem_id}][_n{samples}]
```

| 命令 | 自动生成前缀示例 |
|------|-----------------|
| `copilot-single` | `work_copilot-single_deepseek_verilogeval_Prob001_zero` |
| `single` | `work_single_deco_verilogeval_Prob001_zero` |
| `copilot-full` | `work_copilot-full_deepseek_verilogeval` |
| `copilot-samples` | `work_copilot-samples_deepseek_verilogeval_n5` |
| `full` | `work_full_deco_verilogeval` |

- **模型名**: 取第一段（`deepseek-v3-2-251201` → `deepseek`）
- **Agent名**: 取第一段（`deco-meta-agent` → `deco`）
- **数据集名**: 取basename，去扩展名和版本前缀，截断至20字符
- **问题ID**: 去尾`_NNNN`迭代后缀，去与数据集重复的前缀，截断至30字符

可通过`[prefix]`参数覆盖默认值。

### 配置变量

编辑脚本顶部的变量以配置测试环境：

```bash
AGENT_NAME="deco-meta-agent"              # Docker镜像名称
LLM_MODEL="deepseek-v3-2-251201"          # Copilot模型名（可环境变量覆盖）
FORCE_AGENTIC="--force-agentic"           # 强制agentic模式（VerilogEval等）
```

### 可用命令

#### 1. build - 构建Agent镜像

```bash
./cvdp_benchmark.sh build
```

#### 2. golden - 测试Golden参考

```bash
./cvdp_benchmark.sh golden [dataset] [prefix]
```

**作用**: 只运行test harness，不涉及agent

#### 3. single - 单个问题调试

```bash
./cvdp_benchmark.sh single [dataset] [problem_id] [prefix]
```

**作用**: 快速调试单个问题
**输出**:
- 详细执行日志
- Memory文件: `work_single/<id>/harness/1/rundir/memory/_memory.json`
- 测试报告: `work_single/report.json`

#### 4. samples - 多样本Pass@k评估

```bash
./cvdp_benchmark.sh samples <dataset> <n> <k> [prefix]
```

**参数**:
- `dataset`: 数据集路径
- `n`: 样本数量（默认：5）
- `k`: Pass@k阈值（默认：1）
- `prefix`: 输出前缀

**作用**: 评估代码生成多样性和稳定性
**指标**: Pass@k = 1 - (1 - c/n)^k，其中c是成功样本数

#### 5. full - 完整基准测试

```bash
./cvdp_benchmark.sh full <dataset> [prefix]
```

**作用**: 运行完整数据集评估
**执行时间**: 完整数据集约20-30分钟

## VerilogEval数据集集成

### 数据集特点

- **文件位置**: `/Users/peiyihan/Codes/cvdp_benchmark/datase_verilogeval/verilogeval.jsonl`
- **问题数量**: 157个
- **难度**: easy（所有问题）
- **分类**: cid003（VerilogEval，作为 Specification-to-RTL category）
- **模块名**: 统一使用`TopModule`

### 转换脚本

**位置**: `/Users/peiyihan/Codes/cvdp_integration/scripts/verilogeval_to_cvdp.py`

**功能**: 将VerilogEval格式转换为CVDP JSONL格式

**关键转换**:
1. 添加`system_message`（包含工具说明）
2. 优化`prompt`（添加文件路径和集成说明）
3. 统一文件扩展名（`.sv`）
4. 使用`--force-agentic`标志
5. **Testbench位置**: `verif/testbench.sv` 放在 `context` 中（agent可见），而非 `harness.files` 中
6. **RefModule内联**: 参考实现（ref.sv）自动内联拼接到testbench开头，使testbench自包含，无需额外引用
7. **Iverilog兼容性修复**（VerilogEval转换脚本特有）: VerilogEval原始testbench的`$dumpvars`引用了未声明的`tb_mismatch`，iverilog 13.0 (devel) 不兼容。自动在`$dumpvars`所在`initial begin`前插入`tb_match`/`tb_mismatch`的前向声明

### Non-Agentic (Copilot) 模式

CVDP 直接调用 LLM API 生成代码，无需 Docker 容器。通过 `-m <model>` 指定模型名，通过 `--force-copilot` 标志让 agentic 数据集以 copilot 模式运行。

**执行流程**:
1. CVDP 将 prompt 发送到 OpenAI API（通过 `OPENAI_BASE_URL` 连接自定义 endpoint）
2. LLM 返回 JSON，CVDP 解析后写入 `output.context` 中列出的文件（如 `rtl/TopModule.sv`）
3. CVDP 启动 harness Docker 容器运行 iverilog/vvp 测试
4. Docker 退出码 0 = PASS，非 0 = FAIL

**配置**:
- 模型: `LLM_MODEL` 环境变量（默认: `gpt-4o-mini`）
- API endpoint: `OPENAI_BASE_URL` 环境变量（copilot 命令自动从 `OPENAI_API_BASE` 同步）
- API Key: `OPENAI_USER_KEY` 环境变量
- 无需修改 CVDP 源码

**命令**:
```bash
# 单个问题调试
./cvdp_benchmark.sh copilot-single

# 指定模型
LLM_MODEL=gpt-4o ./cvdp_benchmark.sh copilot-single

# 完整基准测试
./cvdp_benchmark.sh copilot-full

# Pass@k 评估
./cvdp_benchmark.sh copilot-samples datase_verilogeval/verilogeval.jsonl 5 1
```

**输出目录**: `work_copilot_single/`（或指定的 prefix），包含:
- `report.json` / `report.txt` — 测试结果汇总
- `<problem_id>/raw_result.json` — 每个问题的详细结果
- `<problem_id>/harness/` — harness 执行日志和临时文件

## Memory文件结构

CVDP从Agent的stdout解析并保存Memory文件：

```json
{
  "case_id": "/code/",
  "spec": "完整的RTL规格说明",
  "thoughts": ["AI推理过程和总结"],
  "actions": [
    "TOOL_CALL: read_file(path=docs/specification.md)",
    "Successfully wrote to rtl/module.v",
    "Compilation: SUCCESS (exit code 0)",
    "Exit Code: 0"
  ],
  "observations": ["用户输入"],
  "success": true/false,
  "messages": [...]
}
```

### Actions数组说明

- **工具调用**（`TOOL_CALL:`前缀）: 记录AI调用的工具和参数
- **工具结果**: 原始返回文本（编译输出、文件内容等）

CVDP通过解析这些actions跟踪Agent行为并生成报告。

## 测试报告

### JSON报告 (`report.json`)

```json
{
  "cid003": {
    "easy": {
      "Passed Tests": 0,
      "Failed Tests": 1,
      "Total Tests": 1,
      "Passed Tests (%)": 0.0
    }
  }
}
```

### 文本报告 (`report.txt`)

人类可读的测试总结，包括：
- 总体统计
- 分类统计
- 失败问题列表和日志路径

## 常见问题

### 1. 数据集模式错误

**症状**: `Error: Cannot specify both --model and --agent together`

**原因**: CVDP检测到数据集模式不匹配
**解决**: 检查`FORCE_AGENTIC`变量，自定义数据集需要`--force-agentic`

### 2. Agent容器启动失败

**症状**: `Error response from daemon: no suitable node (not your CPU)`

**原因**: Docker架构不匹配
**解决**: 重新构建Docker镜像：`./cvdp_benchmark.sh build`

### 3. Memory文件未生成

**症状**: `/rundir/memory/_memory.json`不存在

**原因**: Agent执行失败或格式错误
**解决**:
1. 检查Agent日志（work目录下reports/1.txt）
2. 验证volume挂载是否正常
3. 检查环境变量（OPENAI_API_KEY）

### 4. 编译失败

**症状**: Memory中显示`Compilation: FAILED`

**原因**: RTL代码语法错误或文件路径问题
**解决**:
1. 读取Memory文件查看详细错误
2. 检查生成的RTL代码
3. 验证文件扩展名（`.sv` vs `.v`）

## 执行时间估算

| 模式 | 问题数 | 预计时间 |
|-------|--------|----------|
| Single | 1 | ~1分钟 |
| Samples (小集) | 1-5 | ~2分钟 |
| Samples (大集) | 92 | ~100-150分钟 |
| Full | 157 | ~20-30分钟 |

**影响因素**: 问题复杂度、k值、并行度、网络速度

## 性能优化

### 短期（1周内）

1. 减少不必要的工具调用
2. 优化LLM调用（使用缓存）
3. 分析失败案例改进prompt

### 中期（1-2个月）

1. 实现增量处理
2. 优化并发处理（问题级别并行）
3. 添加静态代码检查

### 长期（1个月+）

1. 知识库优化（语义检索）
2. 自适应测试策略（动态调整k值）
3. 多模态支持（波形分析、形式化验证）

## 相关文档

- **CVDP文档**: `[CVDP Documentation](https://github.com/YourRepo/CVDP)`
- **转换脚本**: `/Users/peiyihan/Codes/cvdp_integration/scripts/verilogeval_to_cvdp.py`
- **测试脚本**: `/Users/peiyihan/Codes/cvdp_integration/cvdp_benchmark.sh`

## Token使用量追踪

### 概述

Copilot和Agentic两种模式均支持自动统计LLM token使用量，生成`metrics.json`文件，可通过`collect_metrics.py`汇总。

### Copilot模式

**原理**: `OpenAI_Instance`和`OpenAI_Responses_Instance`在每次`prompt()`调用后，从API响应的`response.usage`中提取`prompt_tokens`/`completion_tokens`/`total_tokens`并累加。`CopilotProcessor.create_context()`在LLM调用成功后将累计值写入`{issue_dir}/metrics.json`，然后重置计数器。

**模型支持**: `model_factory.py`采用fallback机制——任何未在注册表中的模型名自动使用`OpenAI_Instance`，因此任何OpenAI-compatible API（DeepSeek、Qwen、GLM等）均可直接通过`-m <model_name>`或`LLM_MODEL`环境变量指定，无需修改代码。

**改动文件**:
- `cvdp_benchmark/src/llm_lib/openai_llm.py`: 加`_token_usage`累加器、`get_token_usage()`、`reset_token_usage()`
- `cvdp_benchmark/src/llm_lib/openai_llm_responses.py`: 同上
- `cvdp_benchmark/src/dataset_processor.py`: `CopilotProcessor.create_context()`写`metrics.json`
- `cvdp_benchmark/src/llm_lib/model_factory.py`: 移除硬编码模型列表，未识别模型fallback到`OpenAI_Instance`

**输出位置**: 每个问题的issue目录下，如：
```
work_copilot_single/cvdp_verilogeval/metrics.json
work_copilot_full/cvdp_verilogeval/metrics.json
```

**metrics.json格式**:
```json
{
  "success": true,
  "tokens": {
    "input_tokens": 1234,
    "output_tokens": 567,
    "total_tokens": 1801
  },
  "agent_name": "deepseek-v3-2-251201",
  "mode": "copilot"
}
```

### Agentic模式

**原理**: `LLMWrapper`同时使用两种token追踪：(1) `generate()`方法直接从`response.usage_metadata`提取；(2) `TokenUsageCallback`（LangChain `BaseCallbackHandler`）捕获agent通过`chat_model`发起的调用（ReAct循环中的tool call等），这些调用不经过`generate()`。Agent执行结束时（`main.py`），`llm.save_metrics()`将汇总数据写入`/code/rundir/metrics.json`，通过volume mount暴露给宿主机。

**改动文件**:
- `promptrtl/utils/llm.py`: 新增`TokenUsageCallback`类 + `LLMWrapper`加累加器、`save_metrics()`
- `promptrtl/main.py`: `generate_memories`模式结束后调`llm.save_metrics()`

**输出位置**: Agent的rundir目录下，如：
```
work_single/deco-meta-agent/harness/1/rundir/metrics.json
work_full/deco-meta-agent/harness/<id>/rundir/metrics.json
```

**metrics.json格式**:
```json
{
  "success": true,
  "tokens": {
    "input_tokens": 5000,
    "output_tokens": 2000,
    "total_tokens": 7000
  },
  "llm_call_count": 8,
  "model": "deepseek-chat",
  "mode": "agentic"
}
```

### 汇总统计

使用`collect_metrics.py`汇总所有`metrics.json`:
```bash
python3 scripts/collect_metrics.py work_copilot_full/
python3 scripts/collect_metrics.py work_single/ --json summary.json
```

输出包括: 总token数、成功率、按模式/agent分类统计、平均时间等。

## 更新日志

- **最后更新**: 2026-03-29
- **文档状态**: 已清理并更新
- **测试覆盖**: Agentic (single/samples/full/golden) + Non-Agentic (copilot-single) 均已测试
- **功能验证**: CVDP集成流程正常，VerilogEval数据集可用

### 变更记录

- testbench从`harness.files`移至`context`（agent可见）
- RefModule内联拼接到testbench开头
- 修复iverilog 13.0 (devel) 对`$dumpvars`前向引用`tb_mismatch`的elaboration报错（VerilogEval转换脚本特有，VerilogEval原始testbench的`$dumpvars`在`tb_mismatch`声明之前，iverilog devel版本不兼容）

### 2026-03-28: VerilogEval真实功能测试集成

**问题**: `verilogeval_to_cvdp.py` 生成的 cocotb 测试（`test_{problem_id}.py`）仅为占位代码，只验证模块能实例化（等10ns后声明pass），不验证功能正确性。而 VerilogEval 的真实 testbench（`verif/testbench.sv`）已包含 RefModule + tb 的比较逻辑，输出 `Mismatches: X in Y samples`，但从未被 harness 调用。

**方案**: 修改 `generate_cocotb_test()` 函数，在 cocotb test 中通过 subprocess 调用 iverilog/vvp 编译运行完整的 testbench，解析 `Mismatches` 输出来判定 pass/fail。

**执行流程**:
1. Phase 1 (Agent): `docker-compose-agent.yml` 运行 Agent，生成 `TopModule.sv` 到 `/code/rtl/`
2. Phase 2 (Harness): `docker-compose.yml` 运行 pytest → cocotb test → subprocess 调用 `iverilog` 编译 `testbench.sv` + `TopModule.sv`，`vvp` 运行仿真，解析 `Mismatches: X in Y samples` 输出
3. Docker 退出码 0 = PASS，非0 = FAIL，CVDP 框架直接复用

**测试验证**:
- 4个不同问题（Prob001_zero, Prob002_m2014_q4i, Prob003_step_one, Prob005_notgate）的正确答案 → 全部 PASS
- 4个不同问题的错误答案 → 全部 FAIL（正确报告 mismatch 数量）
- 157个问题的完整数据集转换 → 全部成功

**修改文件**: 仅 `scripts/verilogeval_to_cvdp.py` 中的 `generate_cocotb_test()` 函数，未修改 CVDP 框架源码

### 2026-03-29: Copilot 模式集成与数据集格式修复

**新增**: `cvdp_benchmark.sh` 新增 `copilot-single`、`copilot-full`、`copilot-samples` 子命令，支持通过 LLM API 直接生成代码（无需 Docker agent）

**修复**:
1. `categories` 从 `cid999` 改为 `cid003`（Spec-to-RTL category），修复 copilot 模式下的 assertion 错误
2. `output.context` 和 `patch` 中的文件路径从 `rtl/{problem_id}.sv` 改为 `rtl/TopModule.sv`，匹配 harness `.env` 中的 `VERILOG_SOURCES`
3. `cvdp_benchmark.sh` copilot 命令自动 `export OPENAI_BASE_URL="${OPENAI_API_BASE}"`，无需手动设置

**验证**: `copilot-single` 端到端测试通过，gpt-4o-mini 生成的 TopModule.sv 正确，Mismatches: 0 in 20 samples

### 2026-03-31: Token使用量追踪 + 通用模型支持 + 自动输出目录

**新增**: Copilot和Agentic模式均自动统计LLM token使用量，输出`metrics.json`，可通过`collect_metrics.py`汇总。

**新增**: 输出目录自动命名，格式`work_{mode}_{model|agent}_{dataset}[_{problem_id}][_n{samples}]`，无需手动指定prefix。

**新增**: `model_factory.py`通用模型支持——未识别的模型名自动fallback到`OpenAI_Instance`，任何OpenAI-compatible API（DeepSeek、Qwen、GLM等）均可直接用`-m <model_name>`。

**Copilot模式改动** (`cvdp_benchmark`):
- `src/llm_lib/openai_llm.py`: `OpenAI_Instance`加`_token_usage`累加器，`prompt()`从`response.usage`提取token
- `src/llm_lib/openai_llm_responses.py`: 同上，从`resp.usage`提取
- `src/dataset_processor.py`: `CopilotProcessor.create_context()`写`{issue_dir}/metrics.json`
- `src/llm_lib/model_factory.py`: 移除硬编码模型列表，未识别模型fallback到`OpenAI_Instance`

**Agentic模式改动** (`promptrtl`):
- `utils/llm.py`: 新增`TokenUsageCallback`（LangChain `BaseCallbackHandler`），捕获agent通过`chat_model`发起的LLM调用token。`LLMWrapper.generate()`从`response.usage_metadata`提取token。`save_metrics()`写`/code/rundir/metrics.json`
- `main.py`: `generate_memories`结束后调`llm.save_metrics()`

**脚本改动** (`cvdp_integration`):
- `cvdp_benchmark.sh`: 所有命令的`[prefix]`参数改为可选，默认由`make_prefix()`自动生成。格式示例：
  - `work_copilot-single_deepseek_verilogeval_Prob001_zero`
  - `work_single_deco_verilogeval_Prob001_zero`
  - `work_copilot-full_deepseek_verilogeval`

**端到端验证**:
- Copilot (`deepseek-v3-2-251201`): 1,269 tokens (1249 input / 20 output)
- Agentic (`gpt-4o-mini`, 4 LLM calls): 4,952 tokens (4733 input / 219 output)
- `collect_metrics.py`正确按mode/agent分类汇总
