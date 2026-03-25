#!/bin/sh

# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

AGENT_BUILD_DIR=$1
AGENT_SOURCE_DIR=$2

cd "$AGENT_SOURCE_DIR"

# Build both base and agent images
# docker build --platform linux/arm64 -f $AGENT_BUILD_DIR/Dockerfile-base -t mage-base .
docker build --platform linux/arm64 -f $AGENT_BUILD_DIR/Dockerfile-mage-agent -t mage-agent . #--no-cache .

echo "Build complete!"
echo "Available images:"
docker images | grep mage

# set -e
# # 检测系统架构
# ARCH=$(uname -m)
# if [ "$ARCH" = "x86_64" ]; then
#     PLATFORM="linux/amd64"
# elif [ "$ARCH" = "aarch64" ] || [ "$ARCH" = "arm64" ]; then
#     PLATFORM="linux/arm64"
# else
#     echo "警告: 未知架构 $ARCH，使用默认平台"
#     PLATFORM=""
# fi
#
# # 构建函数
# build_image() {
#     local dockerfile=$1
#     local imagename=$2
#     local use_cache=${3:-"--no-cache"}
#
#     echo "构建镜像: $imagename"
#     if [ -n "$PLATFORM" ]; then
#         docker build --platform $PLATFORM -f "$dockerfile" -t "$imagename" $use_cache .
#     else
#         docker build -f "$dockerfile" -t "$imagename" $use_cache .
#     fi
# }
#
# # 构建unified-base镜像（如果不存在）
# if ! docker images | grep -q "ace-rtl-unified-base"; then
#     echo "构建unified-base镜像..."
#     # 检查是否有docker-deps目录（使用COPY版本）
#     if [ -d "cvdp-integration/agent/docker-deps/Python-3.12.5.tgz" ] || [ -f "cvdp-integration/agent/docker-deps/Python-3.12.5.tgz" ]; then
#         echo "使用COPY版本的Dockerfile（docker-deps已准备）"
#         build_image "cvdp-integration/agent/Dockerfile-unified-base-copy" "ace-rtl-unified-base" ""
#     else
#         echo "使用网络下载版本的Dockerfile"
#         build_image "cvdp-integration/agent/Dockerfile-unified-base" "ace-rtl-unified-base" ""
#     fi
# else
#     echo "Unified-base镜像已存在，跳过构建"
# fi
#
# # 构建MAGE agent镜像（如果MAGE代码存在）
# MAGE_DEPS_DIR="cvdp-integration/agent/docker-deps/MAGE"
# if [ -d "$MAGE_DEPS_DIR" ]; then
#     echo "构建MAGE agent镜像..."
#     # 从.env文件读取OPENAI_API_BASE（如果存在）
#     ENV_FILE=".env"
#     if [ -f "$ENV_FILE" ]; then
#         API_BASE=$(grep "^OPENAI_API_BASE=" "$ENV_FILE" | cut -d'=' -f2 | tr -d '"' | tr -d "'")
#         if [ -n "$API_BASE" ]; then
#             echo "使用API base: $API_BASE"
#             docker build --build-arg OPENAI_API_BASE="$API_BASE" \
#                 -f "cvdp-integration/agent/Dockerfile-mage-agent" \
#                 -t ace-rtl-mage-agent .
#         else
#             build_image "cvdp-integration/agent/Dockerfile-mage-agent" "ace-rtl-mage-agent" "--no-cache"
#         fi
#     else
#         build_image "cvdp-integration/agent/Dockerfile-mage-agent" "ace-rtl-mage-agent" "--no-cache"
#     fi
# else
#     echo "警告: MAGE代码未找到在 $MAGE_DEPS_DIR"
#     echo "提示: 请先运行 ./download_dependencies.sh 下载MAGE代码"
#     echo "或者确保MAGE代码在 cvdp-integration/agent/docker-deps/MAGE"
# fi
#
# echo "构建完成！"
# echo "可用镜像:"
# docker images | grep ace-rtl
