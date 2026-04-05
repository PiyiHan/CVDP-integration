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
./cvdp_benchmark.sh [--model <name>] [--api-base <url>] <command> [args...]
```

### 全局标志

| 标志 | 说明 | 默认值 |
|------|------|--------|
| `--model <name>` | 覆盖模型名（Copilot 和 Agentic 均生效） | `deepseek-v3-2-251201` |
| `--api-base <url>` | 覆盖 API endpoint | `$OPENAI_API_BASE` |

全局标志可出现在命令行的任意位置（命令前或命令后均可）：

```bash
# 用默认模型和API
./cvdp_benchmark.sh copilot-samples dataset.jsonl 5 1

# Copilot 模式指定模型
./cvdp_benchmark.sh --model kimi-k2.5 copilot-samples dataset.jsonl 5 1

# Copilot 模式指定模型和API
./cvdp_benchmark.sh --model glm-5 --api-base https://api.openai-proxy.org/v1 copilot-full dataset.jsonl

# Agentic 模式指定 agent 使用的 LLM 模型
./cvdp_benchmark.sh --model claude-sonnet-4-6 single dataset.jsonl problem_id
./cvdp_benchmark.sh --model claude-sonnet-4-6 full dataset.jsonl

# 只换API，模型用默认
./cvdp_benchmark.sh --api-base https://api.example.com/v1 copilot-single
```

### Agentic 模式的模型配置

Agentic 模式下，Agent 在 Docker 容器内运行，LLM 模型名通过环境变量链路传递：

```
--model claude-sonnet-4-6
  → cvdp_benchmark.sh 设置 LLM_MODEL shell 变量
    → dataset_processor.py 将 LLM_MODEL 写入 docker-compose-agent.yml environment
      → Docker 容器内 promptrtl/config/settings.py 从 os.environ.get("LLM_MODEL") 读取
        → LLMWrapper 自动检测模型类型，选择 ChatOpenAI 或 ChatAnthropic
```

**模型自动切换**（`promptrtl/utils/llm.py`）：
- 模型名以 `claude` 开头 → 使用 `langchain_anthropic.ChatAnthropic`，连接 `ANTHROPIC_API_BASE`（默认 `https://api.openai-proxy.org/anthropic`），API Key 优先读 `ANTHROPIC_API_KEY`，fallback 到 `OPENAI_USER_KEY`
- 其他模型 → 使用 `langchain_openai.ChatOpenAI`，连接 `OPENAI_API_BASE`
- Token 追踪通过 `_TokenTrackingChatModel` 包装器统一处理，兼容两种模型

Agent 容器内的关键环境变量（均通过 docker-compose environment 传入）：

| 变量 | 来源 | 用途 |
|------|------|------|
| `LLM_MODEL` | `--model` 标志 → `dataset_processor.py` | Agent 使用的 LLM 模型名 |
| `OPENAI_API_BASE` | 宿主机 `os.environ.get("OPENAI_API_BASE")` | OpenAI-compatible API endpoint |
| `OPENAI_USER_KEY` | `config.get("OPENAI_USER_KEY")`（`.env` 或环境变量） | API Key（OpenAI 和 Anthropic 共用） |
| `ANTHROPIC_API_KEY` | 宿主机 `os.environ.get("ANTHROPIC_API_KEY")`，fallback 到 `OPENAI_USER_KEY` | Anthropic API Key |
| `ANTHROPIC_API_BASE` | 宿主机 `os.environ.get("ANTHROPIC_API_BASE")`，默认 `https://api.openai-proxy.org/anthropic` | Anthropic API endpoint |

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

脚本顶部变量定义全局默认值（可通过 `--model`/`--api-base` 覆盖）：

```bash
AGENT_NAME="deco-meta-agent"              # Docker镜像名称
LLM_MODEL="deepseek-v3-2-251201"          # Copilot模型名（覆盖: --model kimi-k2.5）
FORCE_AGENTIC="--force-agentic"           # 强制agentic模式（VerilogEval等）
```

**API Key 配置**：
- 通过 `OPENAI_USER_KEY` 环境变量或 `cvdp_benchmark/.env` 文件设置
- `.env` 优先级低于环境变量
- 不同 API 可共用一个 key（如果 API 相同），也可通过环境变量切换

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
- 模型: `--model <name>` 标志（默认: `deepseek-v3-2-251201`）
- API endpoint: `--api-base <url>` 标志（默认: `$OPENAI_API_BASE`）
- API Key: `OPENAI_USER_KEY` 环境变量或 `.env` 文件
- 无需修改 CVDP 源码

**命令**:
```bash
# 单个问题调试
./cvdp_benchmark.sh copilot-single

# 指定模型
./cvdp_benchmark.sh --model gpt-4o copilot-single

# 指定模型和API
./cvdp_benchmark.sh --model kimi-k2.5 --api-base https://api.openai-proxy.org/v1 copilot-full

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

## ACE-RTL Agent

### 概述

`ace-rtl-agent` 是一个独立的 RTL 生成 Agent（Generator + Reflector + Coordinator + iverilog 仿真循环），与 `deco-meta-agent`（基于 promptrtl 框架）架构不同。

**源码**: `/Users/peiyihan/Codes/Temp_code/mage-cvdp-integration-20260317/ace-rtl/`
**Docker 构建文件**: `/Users/peiyihan/Codes/cvdp_integration/ace-rtl_agent/`

### 与 deco-meta-agent 的区别

| 特性 | ace-rtl-agent | deco-meta-agent |
|------|---------------|-----------------|
| 架构 | ACE 循环（Generator→Simulate→Reflector） | promptrtl ReAct（Thought→Action→Observation） |
| LLM SDK | `openai` SDK 直接调用 | `langchain`（ChatOpenAI / ChatAnthropic） |
| 模型配置 | `GENERATOR_MODEL`/`REFLECTOR_MODEL`/`SIMULATOR_MODEL`（fallback 到 `LLM_MODEL`） | `LLM_MODEL` |
| API Base | `OPENAI_API_BASE` 环境变量（fallback 到 `api.shubiaobiao.cn/v1`） | `OPENAI_API_BASE` 环境变量 |
| 测试台文件 | 必须在 `/code/verif/` 目录下 | 从 `context` 字段自动挂载 |
| 输出格式 | stdout 日志，直接写 `/code/rtl/` 文件 | Memory JSON 文件 |

### 数据集要求

`ace-rtl-agent` **只能用于 agentic 数据集**（ID 格式 `cvdp_agentic_xxx`），且数据集中测试台文件必须在 `context` 字段的 `verif/` 路径下：

```json
{
  "id": "cvdp_agentic_multiplexer_0001",
  "context": {
    "verif/multiplexer_tb.sv": "...",
    "docs/specification.md": "..."
  },
  "prompt": "Design a multiplexer..."
}
```

**不能用于 copilot 数据集**——即使加 `--force-agentic`，转换后的数据集仍将测试台放在 `harness.src/` 下，而 ace-rtl-agent 只在 `/code/verif/` 中查找。

可用的 agentic 数据集：
- `/Users/peiyihan/Codes/cvdp_benchmark/dataset/cvdp_v1.0.4_agentic_cid003.jsonl`（78 个问题）

### 环境变量配置

ace-rtl-agent 通过 `dataset_processor.py` 传入以下 Docker 容器环境变量：

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENAI_USER_KEY` | — | API Key（必须设置，否则容器启动报错） |
| `OPENAI_API_BASE` | `https://api.shubiaobiao.cn/v1` | OpenAI-compatible API endpoint |
| `LLM_MODEL` | `gpt-4o-mini` | 默认模型（未单独设置 `GENERATOR_MODEL` 时使用） |
| `GENERATOR_MODEL` | 同 `LLM_MODEL` | Generator 阶段使用的模型 |
| `REFLECTOR_MODEL` | 同 `LLM_MODEL` | Reflector 阶段使用的模型 |
| `SIMULATOR_MODEL` | 同 `LLM_MODEL` | Simulator 阶段使用的模型 |
| `MAX_ITERATIONS` | `30` | 最大迭代次数 |
| `GENERATOR_TEMP` | `1.2` | Generator 温度 |
| `REFLECTOR_TEMP` | `0.7` | Reflector 温度 |

**注意**: `OPENAI_API_BASE` 必须在宿主机上 `export`（不能只在 `.env` 中），因为 `dataset_processor.py` 用 `os.environ.get("OPENAI_API_BASE")` 读取。

### 构建与使用

```bash
# 构建 Docker 镜像（修改源码后需重新构建）
docker build --platform linux/arm64 \
  -f /Users/peiyihan/Codes/cvdp_integration/ace-rtl_agent/Dockerfile-agent \
  -t ace-rtl-agent \
  /Users/peiyihan/Codes/Temp_code/mage-cvdp-integration-20260317/ace-rtl/

# 单题测试
export MODEL_TIMEOUT=180
export OPENAI_API_BASE=https://api.openai-proxy.org/v1
export LLM_MODEL=kimi-k2.5
./cvdp_benchmark.sh --model kimi-k2.5 --api-base https://api.openai-proxy.org/v1 \
  single /path/to/cvdp_v1.0.4_agentic_cid003.jsonl cvdp_agentic_multiplexer_0001

# 注意：需先设置 AGENT_NAME="ace-rtl-agent"，或修改 cvdp_benchmark.sh 中的默认值
```

> **注意**: 当前 `cvdp_benchmark.sh` 中 `AGENT_NAME` 默认为 `deco-meta-agent`，使用 ace-rtl-agent 前需将其改为 `ace-rtl-agent`，或直接调用 `python3 run_benchmark.py`。

### 已知限制

1. **不支持 copilot 数据集**: `--force-agentic` 转换后测试台在 `harness.src/` 下，不在 agent 期望的 `/code/verif/` 路径
2. **不支持 Claude 模型**: ACE-RTL 只使用 OpenAI SDK，不支持 Anthropic API
3. **arch 不匹配警告**: Docker 仿真容器镜像是 linux/amd64，在 ARM Mac 上会打印平台警告，但通过 Rosetta 可正常运行
4. **无 token 追踪**: ACE-RTL 的 OpenAI SDK 调用不输出 `metrics.json`（与 promptrtl 的 TokenUsageCallback 不同）

## 配置与环境变量

### 关键环境变量

| 变量 | 默认值 | 说明 |
|------|--------|------|
| `OPENAI_API_BASE` | — | 自定义 API endpoint（copilot 模式自动同步到 `OPENAI_BASE_URL`） |
| `OPENAI_BASE_URL` | — | OpenAI SDK 读取的 endpoint |
| `OPENAI_USER_KEY` | — | API Key |
| `LLM_MODEL` | `gpt-4o-mini` | Copilot 模式使用的模型名 |
| `MODEL_TIMEOUT` | `60` | **LLM API 调用超时（秒）**。DeepSeek 等模型在 prompt 较长时可能需要更长时间，建议设为 `180` 或 `300` |
| `DOCKER_TIMEOUT` | `600` | Docker 容器运行超时（秒） |
| `TASK_TIMEOUT` | `300` | 单个任务超时（秒） |
| `QUEUE_TIMEOUT` | `disabled` | 整个队列超时（秒） |

**设置方式**（优先级从高到低）：
1. 命令行环境变量：`MODEL_TIMEOUT=180 ./cvdp_benchmark.sh copilot-full`
2. `.env` 文件：在 `cvdp_benchmark/.env` 中取消注释并修改
3. 代码默认值：`src/constants.py` 中的 `SCORING_CONFIG`

> **注意**: `MODEL_TIMEOUT` 过短会导致 LLM 调用超时失败（重试 3 次后放弃）。DeepSeek 等模型在 prompt 较长（>10K 字符）时响应可能超过 60 秒，建议设为 `180`。

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

**原理**: `LLMWrapper`同时使用两种token追踪：(1) `generate()`方法直接从`response.usage_metadata`提取；(2) `TokenUsageCallback`（LangChain `BaseCallbackHandler`）捕获agent通过`chat_model`发起的调用。此外`_TokenTrackingChatModel`包装器在每次`invoke()`调用时拦截`usage_metadata`，确保通过`create_agent()`框架的调用也能被追踪。Agent执行结束时（`main.py`），`llm.save_metrics()`将汇总数据写入`/code/rundir/metrics.json`，通过volume mount暴露给宿主机。

**模型支持**: `LLMWrapper`自动检测模型类型——`claude`开头的模型使用`langchain_anthropic.ChatAnthropic`，其他使用`langchain_openai.ChatOpenAI`。Token追踪对两种模型均生效。

**改动文件**:
- `promptrtl/utils/llm.py`: 新增`TokenUsageCallback`类 + `LLMWrapper`加累加器、`save_metrics()` + `_TokenTrackingChatModel`包装器 + Claude模型自动检测
- `promptrtl/main.py`: `generate_memories`模式结束后调`llm.save_metrics()`
- `deco-meta-agent/Dockerfile-agent`: 新增`langchain-anthropic>=0.3.0`依赖
- `cvdp_benchmark/src/dataset_processor.py`: docker-compose environment 新增`ANTHROPIC_API_KEY`和`ANTHROPIC_API_BASE`传入

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

输出包括: 总token数、成功率、按模式/agent分类统计、LLM调用时间、Harness执行时间等。

### 数据来源说明

`collect_metrics.py` 从**两个来源**收集数据：

1. **metrics.json**（每个问题目录下）：
   - Token 使用量（input/output/total）
   - 成功/失败状态
   - Agent名称和模式
   - 注意：Copilot 模式不写入 `time.elapsed_time`，所以 LLM 调用时间显示为 0

2. **raw_result.json**（每个 sample 目录下）：
   - Harness 执行时间（`tests[].execution`，iverilog/vvp 仿真时间）
   - 脚本自动递归查找所有 `raw_result.json` 并提取时间数据

输出中时间统计分两部分：
- **LLM调用时间**: 来自 `metrics.json` 的 `time.elapsed_time`（Copilot 模式未记录）
- **Harness执行时间**: 来自 `raw_result.json` 的 `tests[].execution`（所有模式均可用）

## 多样本采样测试 (samples)

### 输出结构

`copilot-samples` 和 `samples` 命令执行多次独立采样（n 次），每次产生一个子目录：

```
work_copilot-samples_<model>_<dataset>_n10/
├── run.log                    # 主运行日志
├── sample_1/
│   ├── run.log                # 本次 sample 的运行日志
│   ├── raw_result.json        # 汇总结果（用于判断是否已完成）
│   ├── report.json            # 结构化测试报告
│   ├── report.txt             # 人类可读报告
│   ├── cvdp_copilot_problem_1/
│   │   ├── metrics.json       # Token 使用量
│   │   ├── raw_result.json    # 单问题结果
│   │   ├── harness/           # Harness 执行目录
│   │   └── reports/           # 测试报告
│   ├── cvdp_copilot_problem_2/
│   │   └── ...
│   └── ...
├── sample_2/
│   └── ...
└── sample_n/
    └── ...
```

### 续跑机制

`run_samples.py` 通过检查 `sample_N/raw_result.json` 是否存在来判断是否已完成：
- **存在** → 跳过该 sample（即使重新运行也会跳过）
- **不存在** → 完整运行该 sample

因此中断后重新执行相同命令会从**第一个未完成的 sample** 继续，不会重复已完成的。

### 单独重跑失败问题

如果某个 sample 中个别问题因 API 超时等原因失败，可用 `-i <problem_id>` 单独重跑：

```bash
# 单独重跑某个问题到已有的 sample 目录
cd /Users/peiyihan/Codes/cvdp_benchmark
export OPENAI_BASE_URL="${OPENAI_API_BASE}"
export MODEL_TIMEOUT=180  # 增加超时时间
python3 run_benchmark.py \
  -f /path/to/dataset.jsonl \
  -i cvdp_copilot_problem_0001 \
  -l -m deepseek-v3-2-251201 --force-copilot \
  -p /path/to/work_copilot-samples_xxx_n10/sample_1
```

重跑后会更新该问题的 `metrics.json`、`raw_result.json` 和 `report.txt`。

### 数据收集流程

1. **每次 LLM 调用**：token 数据累加到模型实例的 `_token_usage`
2. **每个问题完成**：`dataset_processor.py` 将 token 数据写入 `{issue_dir}/metrics.json`，然后重置计数器
3. **每个 sample 完成**：`run_benchmark.py` 生成 `report.json` / `report.txt` 和 `raw_result.json`
4. **批量汇总**：使用 `collect_metrics.py` 递归扫描所有 `metrics.json` 并生成汇总报告

```bash
# 收集单个 sample 的数据
python3 scripts/collect_metrics.py work_copilot-samples_xxx_n10/sample_1/

# 收集所有 samples 的数据
python3 scripts/collect_metrics.py work_copilot-samples_xxx_n10/

# 导出为 JSON
python3 scripts/collect_metrics.py work_copilot-samples_xxx_n10/ --json summary.json
```

`collect_metrics.py` 输出：
- 总问题数、成功/失败数、成功率
- Input/Output/Total tokens 汇总
- 按 mode（copilot/agentic）分类统计
- 按 agent_name 分类统计
- 失败问题列表（如果有）

> **注意**: `report.txt` 中的 pass rate 基于 testbench 执行结果（Docker 退出码），与 token 无关。`metrics.json` 中的 `success` 字段表示 LLM 调用是否成功（非超时、非解析错误）。两者独立：LLM 调用成功 ≠ testbench 通过。

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

### 2026-04-01: 配置文档 + 多样本测试流程 + 数据收集说明

**新增**: 配置与环境变量章节，记录 `MODEL_TIMEOUT` 等关键变量。DeepSeek 等模型在 prompt 较长时需调大超时（建议 180s）。

**新增**: 多样本采样测试章节，记录：
- `samples` 命令的输出目录结构（`sample_1/`, `sample_2/`, ...）
- 续跑机制（通过 `raw_result.json` 判断是否跳过）
- 单独重跑失败问题的方法（`-i <problem_id>` + `-p <sample_dir>`）
- 数据收集流程：LLM 调用 → `metrics.json` → `collect_metrics.py` 汇总
- `report.txt`（testbench 结果）与 `metrics.json`（LLM 调用状态）的区别

**新增**: `collect_metrics.py` 数据来源说明：
- Token/状态来自 `metrics.json`（每个问题目录）
- Harness 执行时间来自 `raw_result.json`（每个 sample 目录）
- 输出分 LLM 调用时间和 Harness 执行时间两部分

### 2026-04-02: 脚本参数化 + 多模型支持

**重构**: `cvdp_benchmark.sh` 改用 `--model`/`--api-base` 全局标志替代硬编码和 `LLM_MODEL` 环境变量覆盖：
- `--model <name>` 覆盖模型名（可出现在命令任意位置）
- `--api-base <url>` 覆盖 API endpoint（默认回退到 `$OPENAI_API_BASE`）
- 输出目录前缀自动包含模型名，不同模型不会冲突
- 删除旧的 `LLM_MODEL=xxx ./cvdp_benchmark.sh ...` 用法，改为 `./cvdp_benchmark.sh --model xxx ...`

**更新**: 文档中所有 copilot 命令示例改为新语法

### 2026-04-02: Agentic 模式支持 `--model` 指定 LLM

**问题**: Agentic 模式下 Agent 容器内的 LLM 模型名硬编码在 `promptrtl/config/settings.py`（默认 `gpt-4o-mini`），无法通过命令行切换。

**改动**:
- `promptrtl/config/settings.py`: `LLM_MODEL` 改为从环境变量 `os.environ.get("LLM_MODEL", "gpt-4o-mini")` 读取
- `cvdp_benchmark/src/dataset_processor.py`: agentic docker-compose environment 中加入 `LLM_MODEL` 传入容器
- `cvdp_benchmark.sh`: agentic 命令（`single`/`full`/`samples`）加入 `export LLM_MODEL="$LLM_MODEL"` 确保 `--model` 标志生效

**变量传递链路**:
```
--model claude-sonnet-4-6
  → cvdp_benchmark.sh 设置 LLM_MODEL shell 变量并 export
    → dataset_processor.py 将 LLM_MODEL 写入 docker-compose-agent.yml environment
      → Docker 容器内 promptrtl/config/settings.py 从 os.environ.get("LLM_MODEL") 读取
        → LLMWrapper 使用 Settings.LLM_MODEL 创建 ChatOpenAI 实例
```

**用法**:
```bash
# Agentic 单题测试用 claude-sonnet-4-6
./cvdp_benchmark.sh --model claude-sonnet-4-6 single dataset.jsonl problem_id

# Agentic 全量运行
./cvdp_benchmark.sh --model claude-sonnet-4-6 full dataset.jsonl
```

**验证**: `--model claude-sonnet-4-6` 单题测试通过，docker-compose-agent.yml 中 `LLM_MODEL: claude-sonnet-4-6`，metrics.json 中 `model: "claude-sonnet-4-6"`，token 统计正常

### 2026-04-02: Claude 模型原生支持 (ChatAnthropic)

**问题**: 通过 OpenAI-compatible proxy (`api.openai-proxy.org/v1`) 调用 Claude 模型时，tool_use/tool_result 消息格式转换不正确，导致 `Error code: 400 - tool_use ids were found without tool_result blocks`。

**方案**: 对 Claude 模型使用 `langchain_anthropic.ChatAnthropic` 直接连接 Anthropic 原生 API (`api.openai-proxy.org/anthropic`)，绕过 OpenAI 格式转换。

**改动**:
- `promptrtl/utils/llm.py`:
  - 新增 `_is_claude_model()` 检测函数（模型名以 `claude` 开头）
  - Claude 模型使用 `ChatAnthropic`，`anthropic_api_url` 默认 `https://api.openai-proxy.org/anthropic`
  - API Key 优先读 `ANTHROPIC_API_KEY`，fallback 到 `OPENAI_USER_KEY`
  - 新增 `_TokenTrackingChatModel` 包装器，在 `invoke()`/`ainvoke()`/`bind_tools()` 层面拦截 token 使用量，兼容 agent 框架直接调用模型的场景
  - `TokenUsageCallback.on_llm_end` 新增检查 `generation.message.usage_metadata`（ChatAnthropic 的 token 数据位置）
- `deco-meta-agent/Dockerfile-agent`: pip install 新增 `langchain-anthropic>=0.3.0`
- `cvdp_benchmark/src/dataset_processor.py`: docker-compose environment 新增 `ANTHROPIC_API_KEY`（fallback 到 `OPENAI_USER_KEY`）和 `ANTHROPIC_API_BASE`（默认 `https://api.openai-proxy.org/anthropic`）

**验证**: `claude-sonnet-4-6` 单题测试通过——Agent 成功读取规格文档、写入 S1-S7 RTL 文件，无 API 错误。Token 统计: 252,430 total tokens (232,978 input / 19,452 output)，20 次 LLM 调用。

### 2026-04-05: ACE-RTL Agent 集成与配置修复

**问题**: `ace-rtl-agent` 的 `config.py` 硬编码 `api_base = "https://api.shubiaobiao.cn/v1"`，忽略 `OPENAI_API_BASE` 环境变量；模型名使用 `GENERATOR_MODEL`/`REFLECTOR_MODEL`/`SIMULATOR_MODEL` 三个独立变量，不读 `LLM_MODEL`。

**改动** (`ace-rtl/src/config.py`):
- `api_base` 改为 `os.getenv("OPENAI_API_BASE", "https://api.shubiaobiao.cn/v1")`，优先使用环境变量
- 新增 `default_model = os.getenv("LLM_MODEL", "gpt-4o-mini")`，三个模型变量的默认值从 `gpt-4o-mini` 改为 `default_model`
- 保持向后兼容：不设置环境变量时行为不变

**发现**:
- ACE-RTL 只能在 **agentic 数据集** 上运行（测试台在 `context.verif/` 中），不能用 `--force-agentic` 转 copilot 数据集
- ACE-RTL 不支持 Claude 模型（只用 OpenAI SDK）
- ACE-RTL 无 token 追踪（不输出 `metrics.json`）

**验证**: `kimi-k2.5` + `ace-rtl-agent` 在 `cvdp_agentic_multiplexer_0001` 上测试通过（1 次迭代生成成功，testbench 3/3 PASS）
