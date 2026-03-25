#!/bin/sh

# SPDX-FileCopyrightText: Copyright (c) 2026 NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

AGENT_BUILD_DIR=$1
AGENT_SOURCE_DIR=$2

cd "$AGENT_SOURCE_DIR"

# Build agent image
docker build --platform linux/arm64 -f $AGENT_BUILD_DIR/Dockerfile-agent -t deco-meta-agent . #--no-cache

echo "Build complete!"
echo "Available images:"
docker images | grep deco-meta
