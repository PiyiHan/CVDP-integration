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
import re
import sys
from pathlib import Path
from typing import List, Dict, Any

# VerilogEval数据集统一使用TopModule作为模块名
MODULE_NAME = "TopModule"


def generate_system_message() -> str:
    """
    生成CVDP agentic模式所需的system_message
    告诉Agent可用的工具和工作方式
    """
    system_msg = """You are a language model that has the following file operations available at your disposal:
  - **List files in a directory** by running one of the following commands: 
    - `ls`
    - `tree`
  - **Read files** by using:
    - `cat <filename>`
  - **Write files** by using:
    - `echo <content> > <filename>`
  - **Compile Verilog** by using `iverilog` such as:
    - `iverilog -o <output_filename>.out -g2012 <verilog_code_file> <verilog_testbench_file>`
  - **Run Simulation** by using:
    - `vvp <output_filename>.out`
  - **Find current working directory** by using:
    - `pwd`

  Your task is to create a Verilog module based on the provided specifications and integrate it into an existing system using proper module instantiation and connections. At the end, please prepare a Linux patch file for me to finalize the request.

  You will solve the problem step by step using the following approach of 
  - thought (thinking process of the step you're going to take)
  - action (the command you will be running to get more details/context that's helpful to solve the problem)
  - observation (the output from the action you will observe based on which you will take your next step)

  The last step will be the final output summary and the patch itself in the following format:
  - thought (the summary of what you did and some introduction of the patch file itself)
  - patch (a Linux-based patch that needs to be applied to reach the relevant solution)

  The patch file should only be applied to a single file to reach the required solution."""
    return system_msg


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
    # 使用统一的MODULE_NAME常量
    module_name = MODULE_NAME

    # 生成CVDP格式的test_runner.py（统一使用.sv扩展名）
    test_runner = f'''import os
from cocotb_tools.runner import get_runner
import pytest

# Fetch environment variables for Verilog source setup
# VERILOG_SOURCES可以包含多个源文件（用空格分隔）
verilog_sources = os.getenv("VERILOG_SOURCES", f"/code/rtl/{module_name}.sv").split()
toplevel_lang   = os.getenv("TOPLEVEL_LANG", "verilog")
sim             = os.getenv("SIM", "icarus")
toplevel        = os.getenv("TOPLEVEL", f"{module_name}")
module          = os.getenv("MODULE", f"test_{problem_id}")
wave            = bool(os.getenv("WAVE", "False"))

# Runner to execute tests
def runner():
    runner = get_runner(sim)
    runner.build(
        sources=verilog_sources,
        hdl_toplevel=toplevel,
        always=True,
        clean=True,
        waves=wave,
        verbose=True,
        timescale=("1ns", "1ns"),
        log_file="sim.log")
    runner.test(hdl_toplevel=toplevel, test_module=module, waves=wave)

@pytest.mark.parametrize("test", range(1))
def test_areg_param(test):
    runner()
'''
    return test_runner


def generate_cocotb_test(problem_id: str, testbench: str) -> str:
    """
    生成cocotb测试文件，通过iverilog/vvp运行VerilogEval的testbench
    验证Agent生成的TopModule与RefModule的行为是否一致
    """
    test_code = f'''import cocotb
import subprocess
import re

@cocotb.test()
async def test_{problem_id}(dut):
    """Functional correctness test via iverilog/vvp testbench simulation"""
    rtl_source = "/code/rtl/TopModule.sv"
    testbench_source = "/code/verif/testbench.sv"
    output_vvp = "/code/rundir/test.vvp"

    compile_cmd = [
        "iverilog", "-Wall", "-Winfloop", "-Wno-timescale",
        "-g2012", "-s", "tb", "-o", output_vvp,
        testbench_source, rtl_source
    ]

    comp = subprocess.run(compile_cmd, capture_output=True, text=True, timeout=30)

    if comp.returncode != 0:
        assert False, f"iverilog compilation failed: {{comp.stderr}}"
    if "syntax error" in comp.stderr:
        assert False, f"Syntax error: {{comp.stderr}}"

    sim = subprocess.run(
        ["vvp", "-n", output_vvp],
        capture_output=True, text=True, timeout=30
    )

    output = sim.stdout
    match = re.search(r"Mismatches: (\\d+) in (\\d+) samples", output)

    if match:
        mismatches, total = int(match.group(1)), int(match.group(2))
        assert mismatches == 0, (
            f"Test failed: {{mismatches}} out of {{total}} samples mismatched"
        )
    else:
        assert False, (
            f"Testbench output not matched. stdout: {{output}}, stderr: {{sim.stderr}}"
        )
'''
    return test_code


def generate_env_file(problem_id: str) -> str:
    """生成.env配置文件"""
    # 使用统一的MODULE_NAME常量，统一使用.sv扩展名
    module_name = MODULE_NAME
    env_content = f"""SIM             = icarus
WAVE            = False
TOPLEVEL_LANG   = verilog
VERILOG_SOURCES = /code/rtl/{module_name}.sv
TOPLEVEL        = {module_name}
MODULE          = test_{problem_id}
PYTHONPATH      = /src
"""
    return env_content


def generate_docker_compose() -> str:
    """生成docker-compose.yml文件"""
    docker_compose = """services:

  direct:
    #image: __OSS_SIM_IMAGE__
    image: __OSS_SIM_IMAGE__

    volumes:
      - ./src/:/src/:ro # Infrastructure location
    env_file    : ./src/.env
    # 注意：/rundir 在部分容器/用户权限下不可写，避免 PytestCacheWarning / Permission denied
    command     : pytest -s --log-cli-level=INFO -o cache_dir=/code/rundir/harness/.cache /src/test_runner.py -v
    # command     : python3 /src/test_runner.py
"""
    return docker_compose


def fix_testbench_declaration_order(testbench: str) -> str:
    """
    Fix iverilog compatibility: insert forward declarations of tb_match/tb_mismatch
    before the initial block that contains $dumpvars.

    VerilogEval testbenches have this pattern inside module tb:
        initial begin
            $dumpfile(...);
            $dumpvars(1, ..., tb_mismatch, ...);
        end
        ...
        wire tb_match;
        wire tb_mismatch = ~tb_match;

    iverilog requires declarations before use. We insert forward declarations
    just before the 'initial begin' that contains $dumpvars.
    """
    dumpvars_pattern = re.compile(r"\$dumpvars\(", re.MULTILINE)
    wire_match = re.compile(r"^\s*wire\s+tb_match\s*;", re.MULTILINE)
    wire_mismatch = re.compile(
        r"^\s*wire\s+tb_mismatch\s*=\s*~\s*tb_match\s*;", re.MULTILINE
    )

    wire_match_obj = wire_match.search(testbench)
    wire_mismatch_obj = wire_mismatch.search(testbench)
    dumpvars_match = dumpvars_pattern.search(testbench)

    if not wire_match_obj or not wire_mismatch_obj or not dumpvars_match:
        return testbench

    testbench_before_dumpvars = testbench[: dumpvars_match.start()]
    initial_pattern = re.compile(r"^(\s*)initial\s+begin", re.MULTILINE)

    all_initials = list(initial_pattern.finditer(testbench_before_dumpvars))
    if not all_initials:
        return testbench

    initial_match = all_initials[-1]

    indent = initial_match.group(1)

    forward_decls = f"{indent}wire tb_match;\n{indent}wire tb_mismatch;\n"

    tb_with_forwards = (
        testbench[: initial_match.start()]
        + forward_decls
        + testbench[initial_match.start() :]
    )
    tb_final = wire_match.sub("", tb_with_forwards, count=1)
    tb_final = wire_mismatch.sub("", tb_final, count=1)

    return tb_final


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

    # 改进prompt：添加文件路径和工具说明
    prompt_content = prompt.strip()
    if interface:
        prompt_content = f"{interface.strip()}\n\n{prompt_content}"
    else:
        prompt_content = prompt_content

    # 构建详细的prompt（包含文件路径和工具说明）
    full_prompt = f"""{prompt_content}

**File Requirements:**
- Output file must be saved as: `/code/rtl/{MODULE_NAME}.sv`
- All ports are 1-bit unless otherwise specified
- The module must always output the specified signal

**Available Tools:**
You can use the following tools during development:
- `iverilog` - Compile and simulate Verilog code
- `vvp` - Run simulation
- `ls` - List directory contents
- `cat` - Read file contents

**Integration Notes:**
- Test harness is located at `/code/verif/testbench.sv`
- You must ensure your generated code compiles and passes the provided testbench"""

    # 将RefModule内联拼接到testbench中，使testbench自包含
    combined_testbench = testbench.strip() if testbench else ""
    combined_testbench = fix_testbench_declaration_order(combined_testbench)
    if reference:
        combined_testbench = reference.strip() + "\n\n" + combined_testbench

    # 构建context（agent运行时能看到的文件）
    context = {}
    if interface:
        context["interface.txt"] = interface.strip()

    # 构建CVDP格式
    cvdp_data = {
        "id": cvdp_id,
        "categories": ["cid999", "easy"],
        "system_message": generate_system_message(),
        "context": context,
        "prompt": full_prompt,
        "input": {"prompt": full_prompt, "context": context},
        "harness": {
            "files": {
                "docker-compose.yml": generate_docker_compose(),
                "src/test_runner.py": generate_cvdp_test_runner(problem_id, testbench),
                f"src/test_{problem_id}.py": generate_cocotb_test(
                    problem_id, testbench
                ),
                "src/.env": generate_env_file(problem_id),
            }
        },
        "output": {
            "context": {f"rtl/{problem_id}.sv": reference.strip() if reference else ""}
        },
    }

    # testbench放到context中（agent可见），而非harness.files中（CVDP验证用）
    if combined_testbench:
        cvdp_data["context"]["verif/testbench.sv"] = combined_testbench

    # 如果有参考实现，添加到patch中（CVDP格式）
    if reference:
        cvdp_data["patch"] = {
            f"rtl/{problem_id}.sv": f"@@ -0,0 +1,{len(reference.split(chr(10)))} @@\n+{reference.strip().replace(chr(10), chr(10) + '+')}"
        }

    return cvdp_data


def convert_verilogeval_dataset(
    verilogeval_dir: Path, output_file: Path, dataset_name: str = "verilogeval"
):
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
    with open(output_file, "w") as f:
        for problem in problems:
            f.write(json.dumps(problem, ensure_ascii=False) + "\n")

    print(f"✅ 转换完成: {len(problems)} 个问题")
    print(f"   输出文件: {output_file}")
    return len(problems)


def main():
    """主函数"""
    if len(sys.argv) < 3:
        print(
            "用法: verilogeval_to_cvdp.py <verilogeval_dataset_dir> <output.jsonl> [dataset_name]"
        )
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


if __name__ == "__main__":
    main()
