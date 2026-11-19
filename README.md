# Grok Bot 多开工具

跨平台桌面程序（PySide6）：用两栏布局管理多个账号，每个账号使用独立的浏览器配置，互不串号。

## 功能特性

- 左侧管理账号：添加、重命名、删除。
- 右侧查看状态、启动 / 停止实例、打开配置目录、填写备注。
- 每个账号对应独立的 Edge / Chrome / Chromium 用户数据目录（`profiles/<账号>/`）。
- 关闭启动器不会结束已启动的浏览器。账号列表保存在 `accounts.json`。

## 技术栈

- Python 3.10+
- PySide6
- Windows 优先 Edge，其次 Chrome；Linux 需 Chrome / Chromium

## 从源码运行

源码在仓库根目录（`main.py`、`requirements.txt`、`run.bat`、`run.sh`）。

Windows：双击 `run.bat`（首次会创建虚拟环境并安装依赖）。

Linux：

```bash
chmod +x run.sh
./run.sh
```

或手动：

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

删除账号不会自动删除 `profiles` 下的配置文件夹。

---

## English

# GrokBot MultiOpen

A cross-platform PySide6 desktop app for managing multiple accounts in a two-pane layout. Each account gets its own browser profile so sessions stay isolated.

## Features

- Left pane: add, rename, and delete accounts.
- Right pane: status, start / stop instances, open the profile folder, and notes.
- Each account uses a separate Edge / Chrome / Chromium user-data directory (`profiles/<account>/`).
- Closing the launcher does not quit browsers that are already running. Accounts are stored in `accounts.json`.

## Tech stack

- Python 3.10+
- PySide6
- Windows 优先 Edge，其次 Chrome；Linux 需 Chrome / Chromium

## Getting started

Source files are at the repository root (`main.py`, `requirements.txt`, `run.bat`, `run.sh`).

Windows: double-click `run.bat` (it creates a venv and installs dependencies on first run).

Linux:

```bash
chmod +x run.sh
./run.sh
```

Or manually:

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

Deleting an account does not automatically remove its folder under `profiles`.

