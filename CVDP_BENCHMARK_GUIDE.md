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

### 配置变量

编辑脚本顶部的变量以配置测试环境：

```bash
# Agent配置
AGENT_NAME="deco-meta-agent"              # Docker镜像名称
AGENT_BUILD_DIR="/path/to/agent"         # Agent构建目录
AGENT_SOURCE_DIR="/path/to/source"        # Agent源代码目录

# 数据集配置
DATASET_DIR="/path/to/dataset.jsonl"    # 默认数据集路径
DATASET_PROBLEM_ID="problem_id"           # 默认问题ID

# 模式控制
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
**参数**:
- `dataset`: 数据集路径（默认：example_dataset/...）
- `prefix`: 输出目录前缀（默认：work_golden）

#### 3. single - 单个问题调试

```bash
# 使用默认数据集（VerilogEval）
./cvdp_benchmark.sh single

# 指定数据集和问题
./cvdp_benchmark.sh single datase_verilogeval/verilogeval.jsonl verilogeval_Prob001_zero_0001

# 指定输出前缀
./cvdp_benchmark.sh single dataset.jsonl problem_id work_debug
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
- **分类**: cid999（VerilogEval专用）
- **模块名**: 统一使用`TopModule`

### 转换脚本

**位置**: `/Users/peiyihan/Codes/cvdp_integration/scripts/verilogeval_to_cvdp.py`

**功能**: 将VerilogEval格式转换为CVDP JSONL格式

**关键转换**:
1. 添加`system_message`（包含工具说明）
2. 优化`prompt`（添加文件路径和集成说明）
3. 统一文件扩展名（`.sv`）
4. 使用`--force-agentic`标志

### 测试流程

```bash
# 1. 转换数据集（如果需要）
python3 scripts/verilogeval_to_cvdp.py <verilogeval_dir> <output.jsonl>

# 2. 运行single模式测试
./cvdp_benchmark.sh single

# 3. 运行samples模式（Pass@k评估）
./cvdp_benchmark.sh samples datase_verilogeval/verilogeval.jsonl 5 1 work_samples
```

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
  "cid999": {
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

## 更新日志

- **最后更新**: 2026-03-27
- **文档状态**: 已清理并更新
- **测试覆盖**: Single, Samples, Full, Golden模式均已测试
- **功能验证**: CVDP集成流程正常，VerilogEval数据集可用
