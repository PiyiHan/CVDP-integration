#!/usr/bin/env python3
"""
从Hugging Face直接下载CVDP数据集（使用requests，不依赖datasets库）

数据集URL: https://huggingface.co/datasets/nvidia/cvdp-benchmark-dataset
"""
import json
import sys
from pathlib import Path

try:
    import requests
except ImportError:
    print("错误: 请先安装requests库")
    print("运行: pip install requests")
    sys.exit(1)

# Hugging Face数据集文件URL
HF_DATASET_BASE = "https://huggingface.co/datasets/nvidia/cvdp-benchmark-dataset/resolve/main"

# 数据集文件列表（JSONL格式，从Hugging Face API获取）
DATASET_FILES = {
    "cvdp_agentic_code_generation_commercial": "cvdp_v1.0.4_agentic_code_generation_commercial.jsonl",
    "cvdp_agentic_code_generation_no_commercial": "cvdp_v1.0.4_agentic_code_generation_no_commercial.jsonl",
    "cvdp_nonagentic_code_generation_commercial": "cvdp_v1.0.4_nonagentic_code_generation_commercial.jsonl",
    "cvdp_nonagentic_code_generation_no_commercial": "cvdp_v1.0.4_nonagentic_code_generation_no_commercial.jsonl",
    "cvdp_nonagentic_code_comprehension": "cvdp_v1.0.4_nonagentic_code_comprehension.jsonl",
}

def download_file(url: str, output_path: Path, chunk_size: int = 8192):
    """下载文件"""
    print(f"📥 下载: {url}")
    try:
        response = requests.get(url, stream=True)
        response.raise_for_status()
        
        total_size = int(response.headers.get('content-length', 0))
        downloaded = 0
        
        with open(output_path, 'wb') as f:
            for chunk in response.iter_content(chunk_size=chunk_size):
                if chunk:
                    f.write(chunk)
                    downloaded += len(chunk)
                    if total_size > 0:
                        percent = (downloaded / total_size) * 100
                        print(f"\r   进度: {percent:.1f}% ({downloaded}/{total_size} bytes)", end='', flush=True)
        
        print()  # 换行
        return True
    except Exception as e:
        print(f"\n❌ 下载失败: {e}")
        return False

def count_jsonl_lines(jsonl_path: Path):
    """统计JSONL文件的行数"""
    try:
        with open(jsonl_path, 'r', encoding='utf-8') as f:
            return sum(1 for _ in f)
    except:
        return 0

def download_cvdp_dataset(subset_name: str = None, output_dir: Path = None):
    """
    下载CVDP数据集
    
    Args:
        subset_name: 子集名称，可选值见DATASET_FILES.keys()
        output_dir: 输出目录
    """
    if output_dir is None:
        output_dir = Path(__file__).parent.parent / "example_dataset"
    else:
        output_dir = Path(output_dir)
    
    output_dir.mkdir(parents=True, exist_ok=True)
    
    if subset_name:
        if subset_name not in DATASET_FILES:
            print(f"❌ 错误: 未知的子集名称 '{subset_name}'")
            print(f"可用子集: {', '.join(DATASET_FILES.keys())}")
            return None
        
        # 下载单个子集
        file_path = DATASET_FILES[subset_name]
        url = f"{HF_DATASET_BASE}/{file_path}"
        
        jsonl_file = output_dir / file_path  # 使用原始文件名
        
        if download_file(url, jsonl_file):
            count = count_jsonl_lines(jsonl_file)
            print(f"✅ 完成: {jsonl_file} ({count} 个问题)")
            return jsonl_file
        
        return None
    else:
        # 下载所有子集
        downloaded_files = []
        total_problems = 0
        
        for subset, file_path in DATASET_FILES.items():
            print(f"\n{'='*60}")
            print(f"📥 下载子集: {subset}")
            print(f"{'='*60}")
            
            url = f"{HF_DATASET_BASE}/{file_path}"
            jsonl_file = output_dir / file_path  # 使用原始文件名
            
            if download_file(url, jsonl_file):
                count = count_jsonl_lines(jsonl_file)
                downloaded_files.append(jsonl_file)
                total_problems += count
                print(f"✅ 完成: {jsonl_file} ({count} 个问题)")
        
        print(f"\n{'='*60}")
        print(f"📊 下载总结")
        print(f"{'='*60}")
        print(f"总问题数: {total_problems}")
        print(f"下载文件数: {len(downloaded_files)}")
        print(f"\n下载的文件:")
        for f in downloaded_files:
            print(f"  - {f}")
        
        return downloaded_files

def main():
    import argparse
    
    parser = argparse.ArgumentParser(description="从Hugging Face下载CVDP数据集")
    parser.add_argument(
        "--subset",
        choices=list(DATASET_FILES.keys()),
        help="要下载的子集名称（不指定则下载所有）"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="输出目录（默认: example_dataset/）"
    )
    
    args = parser.parse_args()
    
    print("="*60)
    print("CVDP数据集下载工具")
    print("="*60)
    print(f"数据集: nvidia/cvdp-benchmark-dataset")
    if args.subset:
        print(f"子集: {args.subset}")
    else:
        print("子集: 所有（4个子集）")
    print("="*60)
    
    result = download_cvdp_dataset(args.subset, args.output_dir)
    
    if result:
        print("\n✅ 下载完成！")
    else:
        print("\n❌ 下载失败")
        sys.exit(1)

if __name__ == "__main__":
    main()
