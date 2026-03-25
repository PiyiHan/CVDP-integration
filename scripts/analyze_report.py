#!/usr/bin/env python3
"""
CVDP报告分析脚本
解析CVDP生成的report.txt文件，提供详细的统计和分析
"""
import json
import re
import sys
from pathlib import Path
from typing import Dict, List, Any, Optional
from collections import defaultdict
from datetime import datetime

class CVDPReportAnalyzer:
    """CVDP报告分析器"""
    
    def __init__(self, report_file: Path):
        self.report_file = Path(report_file)
        self.report_dir = self.report_file.parent
        self.raw_data = {}
        self.summary = {}
        
    def load_report(self) -> Dict[str, Any]:
        """加载报告文件"""
        if not self.report_file.exists():
            raise FileNotFoundError(f"报告文件不存在: {self.report_file}")
        
        with open(self.report_file) as f:
            content = f.read()
        
        # 尝试解析JSON格式的报告
        json_match = re.search(r'\{.*\}', content, re.DOTALL)
        if json_match:
            try:
                self.raw_data = json.loads(json_match.group(0))
                return self.raw_data
            except json.JSONDecodeError:
                pass
        
        # 解析文本格式的报告
        self.summary = self._parse_text_report(content)
        return self.summary
    
    def _parse_text_report(self, content: str) -> Dict[str, Any]:
        """解析文本格式的报告"""
        summary = {
            'total_tests': 0,
            'passed_tests': 0,
            'failed_tests': 0,
            'total_problems': 0,
            'passed_problems': 0,
            'failed_problems': 0,
            'test_pass_rate': 0.0,
            'problem_pass_rate': 0.0,
            'by_category': {},
            'by_difficulty': {},
            'failing_problems': [],
            'passing_problems': [],
            'metadata': {}
        }
        
        # 提取测试统计
        test_match = re.search(r'Total Tests\s+\|\s+(\d+)', content)
        if test_match:
            summary['total_tests'] = int(test_match.group(1))
        
        passed_match = re.search(r'Passed Tests\s+\|\s+(\d+)', content)
        if passed_match:
            summary['passed_tests'] = int(passed_match.group(1))
        
        failed_match = re.search(r'Failed Tests\s+\|\s+(\d+)', content)
        if failed_match:
            summary['failed_tests'] = int(failed_match.group(1))
        
        # 提取问题统计
        problem_match = re.search(r'Total Problems\s+\|\s+(\d+)', content)
        if problem_match:
            summary['total_problems'] = int(problem_match.group(1))
        
        passed_problem_match = re.search(r'Passed Problems\s+\|\s+(\d+)', content)
        if passed_problem_match:
            summary['passed_problems'] = int(passed_problem_match.group(1))
        
        failed_problem_match = re.search(r'Failed Problems\s+\|\s+(\d+)', content)
        if failed_problem_match:
            summary['failed_problems'] = int(failed_problem_match.group(1))
        
        # 提取通过率
        test_rate_match = re.search(r'Test Pass Rate\s+\|\s+([\d.]+)%', content)
        if test_rate_match:
            summary['test_pass_rate'] = float(test_rate_match.group(1))
        
        problem_rate_match = re.search(r'Problem Pass Rate\s+\|\s+([\d.]+)%', content)
        if problem_rate_match:
            summary['problem_pass_rate'] = float(problem_rate_match.group(1))
        
        # 提取失败问题列表
        failing_section = re.search(r'=== Failing Problems ===(.*?)=== Passing Problems ===', content, re.DOTALL)
        if failing_section:
            failing_text = failing_section.group(1)
            problem_matches = re.finditer(r'(\w+_\w+_\d+)', failing_text)
            summary['failing_problems'] = [m.group(1) for m in problem_matches]
        
        # 提取通过问题列表
        passing_section = re.search(r'=== Passing Problems ===(.*?)(?:=== |$)', content, re.DOTALL)
        if passing_section:
            passing_text = passing_section.group(1)
            problem_matches = re.finditer(r'(\w+_\w+_\d+)', passing_text)
            summary['passing_problems'] = [m.group(1) for m in problem_matches]
        
        # 提取元数据
        metadata_match = re.search(r'"metadata":\s*(\{[^}]+\})', content)
        if metadata_match:
            try:
                summary['metadata'] = json.loads(metadata_match.group(1))
            except:
                pass
        
        return summary
    
    def analyze(self) -> Dict[str, Any]:
        """分析报告"""
        if self.raw_data:
            return self._analyze_json_report()
        else:
            return self._analyze_text_report()
    
    def _analyze_json_report(self) -> Dict[str, Any]:
        """分析JSON格式的报告"""
        analysis = {
            'summary': {
                'total_tests': len(self.raw_data.get('tests', [])),
                'passed_tests': sum(1 for t in self.raw_data.get('tests', []) if t.get('result') == 0),
                'failed_tests': sum(1 for t in self.raw_data.get('tests', []) if t.get('result') == 1),
                'errors': self.raw_data.get('errors', 0),
                'category': self.raw_data.get('category', 'unknown'),
                'difficulty': self.raw_data.get('difficulty', 'unknown'),
            },
            'metadata': self.raw_data.get('metadata', {}),
            'tests': self.raw_data.get('tests', [])
        }
        
        if analysis['summary']['total_tests'] > 0:
            analysis['summary']['pass_rate'] = (
                analysis['summary']['passed_tests'] / analysis['summary']['total_tests'] * 100
            )
        else:
            analysis['summary']['pass_rate'] = 0.0
        
        return analysis
    
    def _analyze_text_report(self) -> Dict[str, Any]:
        """分析文本格式的报告"""
        return self.summary
    
    def print_summary(self):
        """打印摘要"""
        data = self.analyze()
        
        print("=" * 80)
        print("📊 CVDP测试报告分析")
        print("=" * 80)
        print(f"报告文件: {self.report_file}")
        print(f"报告目录: {self.report_dir}")
        print()
        
        if 'summary' in data:
            # JSON格式报告
            summary = data['summary']
            print("📈 测试统计")
            print("-" * 80)
            print(f"  总测试数:     {summary.get('total_tests', 0)}")
            print(f"  通过测试:     {summary.get('passed_tests', 0)} ✅")
            print(f"  失败测试:     {summary.get('failed_tests', 0)} ❌")
            print(f"  错误数:       {summary.get('errors', 0)}")
            print(f"  测试通过率:   {summary.get('pass_rate', 0):.2f}%")
            print()
            
            if 'category' in summary:
                print(f"  类别:         {summary['category']}")
            if 'difficulty' in summary:
                print(f"  难度:         {summary['difficulty']}")
            print()
            
            # 显示测试详情
            if 'tests' in data and data['tests']:
                print("📋 测试详情")
                print("-" * 80)
                for i, test in enumerate(data['tests'], 1):
                    result = "✅ PASS" if test.get('result') == 0 else "❌ FAIL"
                    exec_time = test.get('execution', 0)
                    print(f"  测试 {i}: {result} (执行时间: {exec_time:.2f}s)")
                    if test.get('error_msg'):
                        print(f"          错误: {test['error_msg']}")
                    if test.get('log'):
                        print(f"          日志: {test['log']}")
                print()
            
            # 显示元数据
            if 'metadata' in data and data['metadata']:
                print("⚙️  配置信息")
                print("-" * 80)
                metadata = data['metadata']
                print(f"  Agent:        {metadata.get('model_agent', 'N/A')}")
                print(f"  Agentic模式: {'是' if metadata.get('force_agentic') else '否'}")
                print(f"  Golden模式:   {'是' if metadata.get('golden_mode') else '否'}")
                print()
        else:
            # 文本格式报告
            print("📈 测试统计")
            print("-" * 80)
            print(f"  总测试数:       {data.get('total_tests', 0)}")
            print(f"  通过测试:       {data.get('passed_tests', 0)} ✅")
            print(f"  失败测试:       {data.get('failed_tests', 0)} ❌")
            print(f"  测试通过率:     {data.get('test_pass_rate', 0):.2f}%")
            print()
            print(f"  总问题数:       {data.get('total_problems', 0)}")
            print(f"  通过问题:       {data.get('passed_problems', 0)} ✅")
            print(f"  失败问题:       {data.get('failed_problems', 0)} ❌")
            print(f"  问题通过率:     {data.get('problem_pass_rate', 0):.2f}%")
            print()
            
            # 显示失败问题
            if data.get('failing_problems'):
                print("❌ 失败问题")
                print("-" * 80)
                for problem_id in data['failing_problems']:
                    print(f"  - {problem_id}")
                print()
            
            # 显示通过问题
            if data.get('passing_problems'):
                print("✅ 通过问题")
                print("-" * 80)
                for problem_id in data['passing_problems']:
                    print(f"  - {problem_id}")
                print()
        
        print("=" * 80)
    
    def export_json(self, output_file: Optional[Path] = None):
        """导出为JSON格式"""
        if output_file is None:
            output_file = self.report_dir / "analysis.json"
        
        data = self.analyze()
        with open(output_file, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        
        print(f"✅ 分析结果已导出: {output_file}")
    
    def compare_reports(self, other_report: Path):
        """比较两个报告"""
        other_analyzer = CVDPReportAnalyzer(other_report)
        other_analyzer.load_report()
        other_data = other_analyzer.analyze()
        
        self_data = self.analyze()
        
        print("=" * 80)
        print("📊 报告对比")
        print("=" * 80)
        print(f"报告1: {self.report_file}")
        print(f"报告2: {other_report}")
        print()
        
        # 对比统计
        if 'summary' in self_data and 'summary' in other_data:
            s1 = self_data['summary']
            s2 = other_data['summary']
            
            print("📈 统计对比")
            print("-" * 80)
            print(f"{'指标':<20} {'报告1':<15} {'报告2':<15} {'差异':<15}")
            print("-" * 80)
            
            for key in ['total_tests', 'passed_tests', 'failed_tests']:
                v1 = s1.get(key, 0)
                v2 = s2.get(key, 0)
                diff = v2 - v1
                sign = "+" if diff > 0 else "" if diff == 0 else ""
                print(f"{key:<20} {v1:<15} {v2:<15} {sign}{diff:<15}")
            
            print()
            
            # 通过率对比
            rate1 = s1.get('pass_rate', 0)
            rate2 = s2.get('pass_rate', 0)
            rate_diff = rate2 - rate1
            sign = "+" if rate_diff > 0 else "" if rate_diff == 0 else ""
            print(f"{'测试通过率':<20} {rate1:.2f}%{'':<10} {rate2:.2f}%{'':<10} {sign}{rate_diff:.2f}%")
            print()
        
        print("=" * 80)

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(
        description="CVDP报告分析工具",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 分析报告
  python3 analyze_report.py report.txt

  # 导出JSON
  python3 analyze_report.py report.txt --json analysis.json

  # 对比两个报告
  python3 analyze_report.py report1.txt --compare report2.txt

  # 分析多个报告
  python3 analyze_report.py work_*/report.txt
        """
    )
    
    parser.add_argument(
        'reports',
        nargs='+',
        help='报告文件路径（可以是多个）'
    )
    
    parser.add_argument(
        '--json',
        metavar='FILE',
        help='导出为JSON文件'
    )
    
    parser.add_argument(
        '--compare',
        metavar='FILE',
        help='与另一个报告对比'
    )
    
    parser.add_argument(
        '--summary',
        action='store_true',
        help='只显示摘要'
    )
    
    args = parser.parse_args()
    
    # 处理多个报告
    if len(args.reports) > 1:
        print("=" * 80)
        print("📊 批量报告分析")
        print("=" * 80)
        print()
        
        all_summaries = []
        for report_file in args.reports:
            report_path = Path(report_file)
            if not report_path.exists():
                print(f"⚠️  跳过不存在的文件: {report_path}")
                continue
            
            analyzer = CVDPReportAnalyzer(report_path)
            analyzer.load_report()
            data = analyzer.analyze()
            
            if 'summary' in data:
                summary = data['summary']
                summary['report_file'] = str(report_path)
                all_summaries.append(summary)
            
            if not args.summary:
                print(f"\n📄 {report_path.name}")
                print("-" * 80)
                analyzer.print_summary()
        
        # 汇总统计
        if all_summaries:
            print("\n" + "=" * 80)
            print("📊 汇总统计")
            print("=" * 80)
            total_tests = sum(s.get('total_tests', 0) for s in all_summaries)
            total_passed = sum(s.get('passed_tests', 0) for s in all_summaries)
            total_failed = sum(s.get('failed_tests', 0) for s in all_summaries)
            
            print(f"  总报告数:     {len(all_summaries)}")
            print(f"  总测试数:     {total_tests}")
            print(f"  总通过数:     {total_passed} ✅")
            print(f"  总失败数:     {total_failed} ❌")
            if total_tests > 0:
                print(f"  总体通过率:   {total_passed/total_tests*100:.2f}%")
            print()
    else:
        # 单个报告分析
        report_file = Path(args.reports[0])
        
        if not report_file.exists():
            print(f"❌ 报告文件不存在: {report_file}")
            sys.exit(1)
        
        analyzer = CVDPReportAnalyzer(report_file)
        analyzer.load_report()
        
        if args.compare:
            # 对比模式
            other_report = Path(args.compare)
            if not other_report.exists():
                print(f"❌ 对比报告文件不存在: {other_report}")
                sys.exit(1)
            analyzer.compare_reports(other_report)
        else:
            # 正常分析
            analyzer.print_summary()
            
            if args.json:
                analyzer.export_json(Path(args.json))

if __name__ == '__main__':
    main()
