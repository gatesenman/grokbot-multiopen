#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"

if [[ ! -x .venv/bin/python ]]; then
  echo "[Grok Bot 多开] 正在创建虚拟环境..."
  python3 -m venv .venv
fi

if ! .venv/bin/python -c "import PySide6" 2>/dev/null; then
  echo "[Grok Bot 多开] 正在安装依赖..."
  .venv/bin/python -m pip install --upgrade pip
  .venv/bin/python -m pip install -r requirements.txt
fi

export DISPLAY="${DISPLAY:-:2}"
echo "[Grok Bot 多开] 启动中 (DISPLAY=$DISPLAY)..."
exec .venv/bin/python main.py
