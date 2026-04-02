#!/usr/bin/env python3
"""
批量收集和分析agent的metric数据
从CVDP工作目录中收集所有metrics.json文件并生成汇总报告
同时从raw_result.json中提取harness执行时间
"""

import json
import sys
from pathlib import Path
from typing import List, Dict, Any, Optional
from collections import defaultdict
from datetime import datetime


def find_metrics_files(work_dir: Path) -> List[Path]:
    """查找所有metrics.json文件"""
    metrics_files = []
    for metrics_file in work_dir.rglob("metrics.json"):
        if metrics_file.is_file():
            metrics_files.append(metrics_file)
    return sorted(metrics_files)


def find_raw_results(work_dir: Path) -> List[Path]:
    """查找所有raw_result.json文件"""
    results = []
    for result_file in work_dir.rglob("raw_result.json"):
        if result_file.is_file():
            results.append(result_file)
    return sorted(results)


def extract_harness_times(raw_results: List[Path]) -> Dict[str, float]:
    """从raw_result.json中提取每个问题的harness执行时间"""
    times = {}
    for result_file in raw_results:
        try:
            with open(result_file) as f:
                data = json.load(f)
            for pid, pdata in data.items():
                if isinstance(pdata, dict) and "tests" in pdata:
                    for t in pdata.get("tests", []):
                        if "execution" in t:
                            times[pid] = t["execution"]
        except Exception as e:
            print(f"⚠️  无法解析 {result_file}: {e}", file=sys.stderr)
    return times


def load_metrics(metrics_file: Path) -> Optional[Dict[str, Any]]:
    """加载metric文件"""
    try:
        with open(metrics_file) as f:
            return json.load(f)
    except Exception as e:
        print(f"⚠️  无法加载 {metrics_file}: {e}", file=sys.stderr)
        return None


def aggregate_metrics(
    metrics_list: List[Dict[str, Any]],
    harness_times: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """聚合所有metric数据"""
    if not metrics_list:
        return {}

    if harness_times is None:
        harness_times = {}

    aggregated = {
        "total_problems": len(metrics_list),
        "successful": sum(1 for m in metrics_list if m.get("success", False)),
        "failed": sum(1 for m in metrics_list if not m.get("success", False)),
        "total_tokens": {
            "input": sum(
                m.get("tokens", {}).get("input_tokens", 0) for m in metrics_list
            ),
            "output": sum(
                m.get("tokens", {}).get("output_tokens", 0) for m in metrics_list
            ),
            "total": sum(
                m.get("tokens", {}).get("total_tokens", 0) for m in metrics_list
            ),
        },
        "total_cost": {
            "input": sum(m.get("cost", {}).get("input_cost", 0) for m in metrics_list),
            "output": sum(
                m.get("cost", {}).get("output_cost", 0) for m in metrics_list
            ),
            "total": sum(m.get("cost", {}).get("total_cost", 0) for m in metrics_list),
        },
        "total_time": sum(
            m.get("time", {}).get("elapsed_time", 0) for m in metrics_list
        ),
        "avg_time": 0,
        "harness_time": {
            "total": sum(harness_times.values()),
            "avg": 0,
            "min": min(harness_times.values()) if harness_times else 0,
            "max": max(harness_times.values()) if harness_times else 0,
            "count": len(harness_times),
        },
        "by_mode": defaultdict(
            lambda: {"count": 0, "success": 0, "tokens": 0, "cost": 0, "time": 0}
        ),
        "by_agent": defaultdict(
            lambda: {"count": 0, "success": 0, "tokens": 0, "cost": 0, "time": 0}
        ),
    }

    if aggregated["total_problems"] > 0:
        aggregated["avg_time"] = aggregated["total_time"] / aggregated["total_problems"]
        aggregated["success_rate"] = (
            aggregated["successful"] / aggregated["total_problems"] * 100
        )

    if harness_times:
        aggregated["harness_time"]["avg"] = aggregated["harness_time"]["total"] / len(
            harness_times
        )

    # 按模式和agent分类统计
    for metrics in metrics_list:
        mode = metrics.get("mode", "unknown")
        agent = metrics.get("agent_name", "unknown")

        aggregated["by_mode"][mode]["count"] += 1
        if metrics.get("success", False):
            aggregated["by_mode"][mode]["success"] += 1
        aggregated["by_mode"][mode]["tokens"] += metrics.get("tokens", {}).get(
            "total_tokens", 0
        )
        aggregated["by_mode"][mode]["cost"] += metrics.get("cost", {}).get(
            "total_cost", 0
        )
        aggregated["by_mode"][mode]["time"] += metrics.get("time", {}).get(
            "elapsed_time", 0
        )

        aggregated["by_agent"][agent]["count"] += 1
        if metrics.get("success", False):
            aggregated["by_agent"][agent]["success"] += 1
        aggregated["by_agent"][agent]["tokens"] += metrics.get("tokens", {}).get(
            "total_tokens", 0
        )
        aggregated["by_agent"][agent]["cost"] += metrics.get("cost", {}).get(
            "total_cost", 0
        )
        aggregated["by_agent"][agent]["time"] += metrics.get("time", {}).get(
            "elapsed_time", 0
        )

    # 转换defaultdict为普通dict
    aggregated["by_mode"] = dict(aggregated["by_mode"])
    aggregated["by_agent"] = dict(aggregated["by_agent"])

    return aggregated


def print_summary(
    aggregated: Dict[str, Any],
    metrics_list: List[Dict[str, Any]],
    harness_times: Optional[Dict[str, float]] = None,
):
    """打印汇总报告"""
    print("=" * 80)
    print("📊 Metric数据汇总报告")
    print("=" * 80)
    print(f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    print("📈 总体统计")
    print("-" * 80)
    print(f"  总问题数:       {aggregated.get('total_problems', 0)}")
    print(f"  成功:           {aggregated.get('successful', 0)} ✅")
    print(f"  失败:           {aggregated.get('failed', 0)} ❌")
    if aggregated.get("total_problems", 0) > 0:
        print(f"  成功率:         {aggregated.get('success_rate', 0):.2f}%")
    print()

    print("💰 Token使用")
    print("-" * 80)
    tokens = aggregated.get("total_tokens", {})
    print(f"  Input Tokens:   {tokens.get('input', 0):,}")
    print(f"  Output Tokens:  {tokens.get('output', 0):,}")
    print(f"  Total Tokens:   {tokens.get('total', 0):,}")
    print()

    print("💵 成本统计")
    print("-" * 80)
    cost = aggregated.get("total_cost", {})
    print(f"  Input Cost:     ${cost.get('input', 0):.4f}")
    print(f"  Output Cost:    ${cost.get('output', 0):.4f}")
    print(f"  Total Cost:     ${cost.get('total', 0):.4f} USD")
    print()

    print("⏱️  时间统计")
    print("-" * 80)
    total_time = aggregated.get("total_time", 0)
    avg_time = aggregated.get("avg_time", 0)
    print(f"  LLM调用总时间:   {total_time:.2f}s ({total_time / 60:.2f}分钟)")
    print(f"  LLM调用平均时间: {avg_time:.2f}s")
    print()

    ht = aggregated.get("harness_time", {})
    if ht and ht.get("count", 0) > 0:
        print("🔧 Harness执行时间 (testbench运行)")
        print("-" * 80)
        print(f"  总时间:         {ht['total']:.2f}s ({ht['total'] / 60:.2f}分钟)")
        print(f"  平均时间:       {ht['avg']:.2f}s")
        print(f"  最小时间:       {ht['min']:.2f}s")
        print(f"  最大时间:       {ht['max']:.2f}s")
        print(f"  有效数据点:     {ht['count']}")
        print()

    # 按模式统计
    if aggregated.get("by_mode"):
        print("📊 按模式统计")
        print("-" * 80)
        for mode, stats in aggregated["by_mode"].items():
            success_rate = (
                (stats["success"] / stats["count"] * 100) if stats["count"] > 0 else 0
            )
            print(f"  {mode}:")
            print(f"    问题数:       {stats['count']}")
            print(f"    成功:         {stats['success']} ({success_rate:.1f}%)")
            print(f"    Tokens:       {stats['tokens']:,}")
            print(f"    Cost:         ${stats['cost']:.4f}")
            print(f"    Time:         {stats['time']:.2f}s")
        print()

    # 按Agent统计
    if aggregated.get("by_agent"):
        print("🤖 按Agent统计")
        print("-" * 80)
        for agent, stats in aggregated["by_agent"].items():
            success_rate = (
                (stats["success"] / stats["count"] * 100) if stats["count"] > 0 else 0
            )
            print(f"  {agent}:")
            print(f"    问题数:       {stats['count']}")
            print(f"    成功:         {stats['success']} ({success_rate:.1f}%)")
            print(f"    Tokens:       {stats['tokens']:,}")
            print(f"    Cost:         ${stats['cost']:.4f}")
            print(f"    Time:         {stats['time']:.2f}s")
        print()

    # 失败问题列表
    failed_problems = [m for m in metrics_list if not m.get("success", False)]
    if failed_problems:
        print("❌ 失败问题")
        print("-" * 80)
        for metrics in failed_problems:
            problem_id = metrics.get("problem_id", "unknown")
            error = metrics.get("error_message", "Unknown error")
            print(f"  - {problem_id}: {error}")
        print()

    print("=" * 80)


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(
        description="批量收集和分析agent的metric数据",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 从工作目录收集metric
  python3 collect_metrics.py ~/workspace/cvdp_benchmark/work_verilogeval_full

  # 导出为JSON
  python3 collect_metrics.py ~/workspace/cvdp_benchmark/work_verilogeval_full --json summary.json
        """,
    )

    parser.add_argument("work_dir", help="CVDP工作目录（包含harness子目录）")

    parser.add_argument("--json", metavar="FILE", help="导出汇总结果为JSON文件")

    parser.add_argument(
        "--output-dir",
        metavar="DIR",
        help="输出目录（用于保存所有metric文件的副本）",
    )

    args = parser.parse_args()

    work_dir = Path(args.work_dir)
    if not work_dir.exists():
        print(f"❌ 工作目录不存在: {work_dir}")
        sys.exit(1)

    print(f"🔍 搜索metric文件: {work_dir}")
    metrics_files = find_metrics_files(work_dir)

    if not metrics_files:
        print(f"⚠️  未找到任何metrics.json文件")
        sys.exit(1)

    print(f"✅ 找到 {len(metrics_files)} 个metric文件")

    # 搜索raw_result.json提取harness时间
    raw_results = find_raw_results(work_dir)
    harness_times = extract_harness_times(raw_results)
    if harness_times:
        print(
            f"✅ 从 {len(raw_results)} 个raw_result.json中提取了 {len(harness_times)} 个harness执行时间"
        )
    print()

    # 加载所有metric
    metrics_list = []
    for metrics_file in metrics_files:
        metrics = load_metrics(metrics_file)
        if metrics:
            metrics_list.append(metrics)

    if not metrics_list:
        print("❌ 无法加载任何metric数据")
        sys.exit(1)

    # 聚合数据
    aggregated = aggregate_metrics(metrics_list, harness_times)

    # 打印汇总
    print_summary(aggregated, metrics_list, harness_times)

    # 导出JSON
    if args.json:
        output_file = Path(args.json)
        output_data = {
            "summary": aggregated,
            "individual_metrics": metrics_list,
            "harness_times": harness_times,
            "generated_at": datetime.now().isoformat(),
        }
        with open(output_file, "w") as f:
            json.dump(output_data, f, indent=2, ensure_ascii=False)
        print(f"✅ 汇总结果已导出: {output_file}")

    # 复制metric文件到输出目录
    if args.output_dir:
        output_dir = Path(args.output_dir)
        output_dir.mkdir(parents=True, exist_ok=True)
        for metrics_file in metrics_files:
            problem_id = (
                metrics_file.parent.parent.name
                if metrics_file.parent.parent.name.startswith("cvdp_")
                else "unknown"
            )
            dest_file = output_dir / f"{problem_id}_metrics.json"
            import shutil

            shutil.copy2(metrics_file, dest_file)
        print(f"✅ Metric文件已复制到: {output_dir}")


if __name__ == "__main__":
    main()
