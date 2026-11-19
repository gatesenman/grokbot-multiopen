@echo off
chcp 65001 >nul
cd /d "%~dp0"

if not exist ".venv\Scripts\python.exe" (
    echo [Grok Bot 多开] 正在创建虚拟环境...
    python -m venv .venv
    if errorlevel 1 (
        echo 错误: 未找到 Python。请先安装 Python 3.10+ 并勾选 Add to PATH。
        pause
        exit /b 1
    )
)

".venv\Scripts\python.exe" -c "import PySide6" 2>nul
if errorlevel 1 (
    echo [Grok Bot 多开] 正在安装依赖...
    ".venv\Scripts\python.exe" -m pip install --upgrade pip
    ".venv\Scripts\python.exe" -m pip install -r requirements.txt
    if errorlevel 1 (
        echo 错误: 依赖安装失败。
        pause
        exit /b 1
    )
)

echo [Grok Bot 多开] 启动中...
".venv\Scripts\python.exe" main.py
if errorlevel 1 pause
