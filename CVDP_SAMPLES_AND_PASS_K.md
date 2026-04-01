# CVDP Samples 输出结构与 pass@k 计算

## 0. FAQ

**Q: report.txt 是谁生成的？**
`run_reporter.py`。单次运行和多次采样都是：先写 `report.json`/`composite_report.json` → 自动调用 `run_reporter.py` 生成 `.txt`。也可手动运行 `python run_reporter.py <report.json>`。

**Q: pass@k 的 k 在哪里指定？**
`run_samples.py -k` 参数，对应 `cvdp_benchmark.sh`：
```bash
./cvdp_benchmark.sh copilot-samples <dataset> <n> <k> [prefix]
#                                              ↑   ↑    ↑
#                                             n=5  k=1  prefix=work_copilot_samples
```
`n` = 每个 problem 采样次数，`k` = pass@k 中的 k（默认1），`prefix` = 输出目录。

**Q: 输出目录在哪里指定？**
`run_samples.py -p` / `--prefix` 参数，默认值在 `src/config_manager.py` 的 `BENCHMARK_PREFIX`（默认 `"work"`）。`run_samples.py` 会自动在 prefix 下创建 `sample_1/`, `sample_2/`, ... 子目录。

## 1. 输出目录结构

运行 `n=3` samples 后，目录结构如下：

```
work_test_samples/
├── sample_1/
│   ├── raw_result.json    # 每个sample的pass/fail (result: 0=pass)
│   ├── report.json        # 单次sample的测试报告
│   └── <problem_id>/      # harness执行细节（日志、生成文件等）
├── sample_2/
│   ├── raw_result.json
│   └── ...
├── sample_3/
│   ├── raw_result.json
│   └── ...
├── composite_report.json  # 合并所有samples，含每个sample的详细pass/fail
└── composite_report.txt   # 人类可读报告，含pass@k分布
```

### raw_result.json 格式（每个 sample）

```json
{
  "verilogeval_Prob001_zero_0001": {
    "category": "cid003",
    "difficulty": "easy",
    "tests": [
      {
        "result": 0,          // 0 = PASS, 非0 = FAIL
        "log": "/path/to/reports/1.txt",
        "error_msg": null,
        "execution": 1.72,    // 执行时间（秒）
        "pid": 93762
      }
    ],
    "errors": 0
  }
}
```

### composite_report.json 格式（合并报告）

```json
{
  "metadata": {
    "n_samples": 3,
    "k_threshold": 1,
    "composite": true,
    "model_agent": "gpt-4o-mini"
  },
  "samples": [
    {
      "cid003": { "easy": { "Passed Problems": 1, "Total Problems": 1, ... } },
      "test_details": {
        "passing_tests": [{ "test_id": "verilogeval_Prob001_zero_0001", "category": "cid003", "difficulty": "easy" }],
        "failing_tests": []
      },
      "sample_index": 0
    },
    // ... sample 2, 3 类似
  ]
}
```

## 2. pass@k 定义

来自 VerilogEval 论文：

> pass@k := E_Problems[ 1 − C(n−c, k) / C(n, k) ]

其中：
- `n` = 对每个问题的总采样次数（total trials）
- `c` = 通过功能验证的次数（correct trials）
- `k` = pass@k 中的 k

含义：在 k 个随机选取的样本中，至少有 1 个通过的概率（对所有问题取期望）。

## 3. CVDP 内置的 pass@k 计算

CVDP **已经内置了 pass@k 计算**，无需自己实现：

### 自动输出内容

`composite_report.txt` 包含：
- **Sample Statistics**: 每个 sample 的 pass rate
- **Pass@k Distribution**: 每个 problem 的 pass count（如 `3/3`）及对应的 pass@k 概率
- 按 category / difficulty 分组的统计

示例输出：
```
=== Pass@1 Distribution (n=3) ===
Pass@1 measures the probability of a problem passing in at least 1 of 3 randomly-selected samples
+--------------+------------+----------------+---------------------------+
| Pass Count   |   Problems | % of Dataset   | Pass@1, n=3 Probability   |
+==============+============+================+===========================+
| 3/3          |          1 | 100.00%        | 100.00%                   |
+--------------+------------+----------------+---------------------------+

Overall Pass@1, n=3 probability: 100.00%
```

### 计算公式差异

| 实现 | 公式 | 特点 |
|------|------|------|
| **VerilogEval** (精确) | `1 - C(n-c, k) / C(n, k)` | 组合数公式，无偏差 |
| **CVDP** (近似) | `1 - (1 - c/n)^k` | 独立概率近似，n 大时与精确公式等价 |

在 `n` 较大时两者结果一致，但 `n` 较小时 CVDP 的近似值会略偏高。

## 4. 如何从 composite_report.json 提取数据计算精确 pass@k

如果想用 VerilogEval 的精确公式，可以从 `composite_report.json` 中提取：

```python
import json
import numpy as np
from math import comb

def estimate_pass_at_k(n, c, k):
    """VerilogEval 精确公式: 1 - C(n-c, k) / C(n, k)"""
    if n - c < k:
        return 1.0
    return 1.0 - comb(n - c, k) / comb(n, k)

# 从 composite_report.json 提取
with open("composite_report.json") as f:
    data = json.load(f)

# 统计每个 problem 的 pass count
problem_results = {}  # problem_id -> [pass/fail per sample]
for sample in data["samples"]:
    passing_ids = {t["test_id"] for t in sample["test_details"]["passing_tests"]}
    failing_ids = {t["test_id"] for t in sample["test_details"]["failing_tests"]}
    all_ids = passing_ids | failing_ids
    for pid in all_ids:
        problem_results.setdefault(pid, []).append(1 if pid in passing_ids else 0)

# 计算 pass@k
n = len(data["samples"])
ks = [1, 5, 10]
for k in ks:
    if n >= k:
        pass_at_k = np.mean([estimate_pass_at_k(n, sum(results), k) for results in problem_results.values()])
        print(f"pass@{k} = {pass_at_k:.4f}")
```

## 5. 运行命令

```bash
# 参数: <dataset> [n=5] [k=1] [prefix=work_copilot_samples]
#   n = 每个 problem 采样次数
#   k = pass@k 中的 k
#   prefix = 输出目录

# 单个问题，n=5 samples，k=1
./cvdp_benchmark.sh copilot-samples dataset_verilogeval/verilogeval.jsonl 5 1

# 完整数据集，n=10 samples，k=5
./cvdp_benchmark.sh copilot-samples dataset_verilogeval/verilogeval.jsonl 10 5

# 指定输出目录
./cvdp_benchmark.sh copilot-samples dataset_verilogeval/verilogeval.jsonl 10 5 my_results

# 查看已有的 composite report（重新生成 report.txt）
python /Users/peiyihan/Codes/cvdp_benchmark/run_reporter.py work_test_samples/composite_report.json
```
