#!/usr/bin/env bash

set -e

echo "======================================="
echo " Moses Runtime Environment Detection "
echo "======================================="
echo

if ! command -v docker >/dev/null 2>&1; then
    echo "[FAIL] Docker is not installed."
    exit 1
fi

echo "[PASS] Docker detected"

if command -v nvidia-smi >/dev/null 2>&1; then
    echo "[PASS] NVIDIA GPU detected"
    GPU_AVAILABLE=true
else
    echo "[WARN] NVIDIA GPU not detected"
    GPU_AVAILABLE=false
fi

echo

echo "Running runtime detection..."
python utils/runtime_gpu_detect.py

echo

if [ "$GPU_AVAILABLE" = true ]; then
    echo "Recommended startup command:"
    echo "docker compose up --build"
else
    echo "Recommended startup command:"
    echo "docker compose -f docker/docker-compose.cpu.yml up --build"
fi
