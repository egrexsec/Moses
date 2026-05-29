#!/bin/bash

set -e

echo "[Moses] Running bootstrap diagnostics..."
python utils/bootstrap.py

echo "[Moses] Starting application..."
python app.py
