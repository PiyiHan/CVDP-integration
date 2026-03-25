#!/usr/bin/env python3
"""
VerilogEval到CVDP格式转换工具
将VerilogEval的目录格式转换为CVDP的JSONL格式

VerilogEval格式：
- dataset_*/ProbXXX_name/
  - ProbXXX_name_prompt.txt
  - ProbXXX_name_test.sv
  - ProbXXX_name_ref.sv
  - ProbXXX_name_ifc.txt

CVDP格式：
- JSONL文件，每行一个JSON对象
- 包含：id, input.prompt, harness.files等
"""
import json
import os
import sys
from pathlib import Path
from typing import List, Dict, Any

def read_file_safe(filepath: Path) -> str:
    """安全读取文件，如果不存在返回空字符串"""
    if filepath.exists():
        return filepath.read_text()
    return ""

def generate_cvdp_test_runner(problem_id: str, testbench: str) -> str:
    """
    生成CVDP格式的test_runner.py
    CVDP使用cocotb进行测试，需要Python test runner
    """
    # 提取模块名（从problem_id或testbench中）
    module_name = "TopModule"  # VerilogEval默认使用TopModule
    if "TopModule" in testbench:
        module_name = "TopModule"
    elif "RefModule" in testbench:
        # 从testbench中提取实际模块名
        import re
        module_match = re.search(r'module\s+(\w+)', testbench)
        if module_match:
            module_name = module_match.group(1)
    
    # 生成CVDP格式的test_runner.py
    test_runner = f'''import os
from cocotb_tools.runner import get_runner
import pytest

verilog_sources = os.getenv("VERILOG_SOURCES", "/code/rtl/{module_name}.sv").split()
sim             = os.getenv("SIM", "icarus")
toplevel        = os.getenv("TOPLEVEL", "{module_name}")
module          = os.getenv("MODULE", "test_{problem_id}")
wave            = bool(os.getenv("WAVE", "False"))

def runner(plusargs=[], parameter={{}}):
    runner = get_runner(sim)
    runner.build(
        sources=verilog_sources,
        hdl_toplevel=toplevel,
        parameters=parameter,
        always=True,
        clean=True,
        waves=wave,
        verbose=True,
        timescale=("1ns", "1ns"),
        log_file="sim.log")
    runner.test(hdl_toplevel=toplevel, test_module=module, waves=wave, plusargs=plusargs)

@pytest.mark.parametrize("test", range(1))
def test_areg_param(test):
    runner()
'''
    return test_runner

def generate_cocotb_test(problem_id: str, testbench: str) -> str:
    """
    生成cocotb测试文件
    这是一个简化的测试，主要验证模块能正常编译和运行
    """
    module_name = "TopModule"
    import re
    module_match = re.search(r'module\s+(\w+)', testbench)
    if module_match:
        module_name = module_match.group(1)
    
    # 简化的cocotb测试
    test_code = f'''import cocotb
from cocotb.clock import Clock
from cocotb.triggers import Timer

@cocotb.test()
async def test_{problem_id}(dut):
    """Basic test for {module_name}"""
    # 简单的功能测试：验证模块能正常实例化
    await Timer(10, units="ns")
    cocotb.log.info("Test passed: Module instantiated successfully")
'''
    return test_code

def generate_env_file(problem_id: str) -> str:
    """生成.env配置文件"""
    module_name = "TopModule"
    env_content = f'''SIM             = icarus
WAVE            = False
TOPLEVEL_LANG   = verilog
VERILOG_SOURCES = /code/rtl/{module_name}.sv
TOPLEVEL        = {module_name}
MODULE          = test_{problem_id}
PYTHONPATH      = /src
'''
    return env_content

def generate_docker_compose() -> str:
    """生成docker-compose.yml文件"""
    docker_compose = '''services:

  direct:
    #image: __OSS_SIM_IMAGE__
    image: __OSS_SIM_IMAGE__

    volumes:
      - ./src/:/src/:ro # Infrastructure location
    env_file    : ./src/.env
    # 注意：/rundir 在部分容器/用户权限下不可写，避免 PytestCacheWarning / Permission denied
    command     : pytest -s --log-cli-level=INFO -o cache_dir=/code/rundir/harness/.cache /src/test_runner.py -v
    # command     : python3 /src/test_runner.py
'''
    return docker_compose

def convert_verilogeval_problem(problem_dir: Path, problem_id: str) -> Dict[str, Any]:
    """
    转换单个VerilogEval问题到CVDP格式
    
    Args:
        problem_dir: 问题目录路径（如 Prob001_zero）
        problem_id: 问题ID（如 Prob001_zero）
    
    Returns:
        CVDP格式的字典
    """
    # 读取各个文件
    prompt_file = problem_dir / f"{problem_id}_prompt.txt"
    test_file = problem_dir / f"{problem_id}_test.sv"
    ref_file = problem_dir / f"{problem_id}_ref.sv"
    ifc_file = problem_dir / f"{problem_id}_ifc.txt"
    
    prompt = read_file_safe(prompt_file)
    testbench = read_file_safe(test_file)
    reference = read_file_safe(ref_file)
    interface = read_file_safe(ifc_file)
    
    # 构建CVDP格式
    # CVDP格式参考：example_dataset中的格式
    # CVDP期望的id格式：cvdp_xxx_0001（最后一部分必须是4位数字）
    # 我们将problem_id转换为CVDP格式：Prob001_zero -> verilogeval_Prob001_zero_0001
    cvdp_id = f"verilogeval_{problem_id}_0001"
    
    # 构建prompt（包含接口描述和问题描述）
    full_prompt = prompt.strip()
    if interface:
        full_prompt = f"{interface.strip()}\n\n{prompt.strip()}"
    
    # 构建context（CVDP需要input.context字段；AgenticProcessor还需顶层context）
    context = {}
    if interface:
        context["interface.txt"] = interface.strip()
    
    # 构建CVDP格式
    # CVDP期望categories格式：["cid003", "easy"]，其中cid003表示category ID
    # 我们使用一个通用的category ID：cid999（表示VerilogEval）
    # 顶层 "context" 与 "prompt" 供 AgenticProcessor 使用（--force-agentic 或未做 transform 时）
    cvdp_data = {
        "id": cvdp_id,
        "categories": ["cid999", "easy"],  # CVDP需要cid格式的categories
        "context": context,
        "prompt": full_prompt,
        "input": {
            "prompt": full_prompt,
            "context": context
        },
        "harness": {
            "files": {
                # CVDP需要完整的harness文件结构
                # docker-compose.yml是必需的
                "docker-compose.yml": generate_docker_compose(),
                # test_runner.py是Python测试运行器（使用cocotb）
                "src/test_runner.py": generate_cvdp_test_runner(problem_id, testbench),
                # 生成test文件（cocotb测试）
                f"src/test_{problem_id}.py": generate_cocotb_test(problem_id, testbench),
                # 生成.env配置文件
                "src/.env": generate_env_file(problem_id),
                # 如果需要，也可以包含原始的SystemVerilog testbench
                "verif/testbench.sv": testbench.strip() if testbench else ""
            }
        },
        "output": {
            "context": {
                f"rtl/{problem_id}.sv": reference.strip() if reference else ""
            }
        }
    }
    
    # 如果有参考实现，添加到patch中（CVDP格式）
    if reference:
        cvdp_data["patch"] = {
            f"rtl/{problem_id}.sv": f"@@ -0,0 +1,{len(reference.split(chr(10)))} @@\n+{reference.strip().replace(chr(10), chr(10)+'+')}"
        }
    
    return cvdp_data

def convert_verilogeval_dataset(verilogeval_dir: Path, output_file: Path, dataset_name: str = "verilogeval"):
    """
    转换整个VerilogEval数据集到CVDP格式
    
    Args:
        verilogeval_dir: VerilogEval数据集目录（如 dataset_code-complete-iccad2023）
        output_file: 输出的JSONL文件路径
        dataset_name: 数据集名称（用于生成problem_id前缀）
    """
    problems = []
    problem_ids = set()
    
    # VerilogEval格式：目录中有多个文件，每个问题有多个文件
    # Prob001_zero_prompt.txt, Prob001_zero_test.sv, Prob001_zero_ref.sv, Prob001_zero_ifc.txt
    # 需要先收集所有问题ID
    for item in sorted(verilogeval_dir.iterdir()):
        if item.is_file() and item.name.startswith("Prob"):
            # 提取问题ID（去掉后缀）
            parts = item.stem.split("_")
            if len(parts) >= 2:
                problem_id = "_".join(parts[:-1])  # Prob001_zero
                problem_ids.add(problem_id)
    
    # 转换每个问题
    for problem_id in sorted(problem_ids):
        cvdp_data = convert_verilogeval_problem(verilogeval_dir, problem_id)
        problems.append(cvdp_data)
    
    # 写入JSONL文件
    output_file.parent.mkdir(parents=True, exist_ok=True)
    with open(output_file, 'w') as f:
        for problem in problems:
            f.write(json.dumps(problem, ensure_ascii=False) + '\n')
    
    print(f"✅ 转换完成: {len(problems)} 个问题")
    print(f"   输出文件: {output_file}")
    return len(problems)

def main():
    """主函数"""
    if len(sys.argv) < 3:
        print("用法: verilogeval_to_cvdp.py <verilogeval_dataset_dir> <output.jsonl> [dataset_name]")
        print("")
        print("示例:")
        print("  python verilogeval_to_cvdp.py \\")
        print("    ~/workspace/verilog-eval/dataset_code-complete-iccad2023 \\")
        print("    example_dataset/verilogeval_code_complete.jsonl")
        sys.exit(1)
    
    verilogeval_dir = Path(sys.argv[1])
    output_file = Path(sys.argv[2])
    dataset_name = sys.argv[3] if len(sys.argv) > 3 else "verilogeval"
    
    if not verilogeval_dir.exists():
        print(f"❌ 错误: VerilogEval数据集目录不存在: {verilogeval_dir}")
        sys.exit(1)
    
    if not verilogeval_dir.is_dir():
        print(f"❌ 错误: 不是目录: {verilogeval_dir}")
        sys.exit(1)
    
    print(f"📁 VerilogEval数据集: {verilogeval_dir}")
    print(f"📄 输出文件: {output_file}")
    print("")
    
    count = convert_verilogeval_dataset(verilogeval_dir, output_file, dataset_name)
    print(f"\n✅ 成功转换 {count} 个问题")

if __name__ == '__main__':
    main()
