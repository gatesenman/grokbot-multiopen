# Grok Bot 多开工具

跨平台桌面程序（PySide6）：两栏布局管理多个 Grok Bot / Cursor 账号，每个账号使用独立浏览器配置，互不串号。

## 功能

- **左侧「账号」**：添加 / 重命名 / 删除账号
- **右侧「程序面板」**：查看状态、启动 / 停止实例、打开配置目录、备注
- 每个账号对应独立的 Edge / Chrome / Chromium 用户数据目录（`profiles/<账号>/`）
- 启动时以应用模式打开 https://cursor.com
- 关闭启动器不会结束已启动的浏览器

## 环境要求

- Windows 10 / 11 或 Linux
- Python 3.10 或更高版本
- 浏览器：Windows 优先 Edge，其次 Chrome；Linux 需 Chrome / Chromium

## 快速开始

### Windows

双击 **`run.bat`**（首次自动创建 venv 并安装依赖）。

### Linux

```bash
chmod +x run.sh
./run.sh
# 或指定显示器：
DISPLAY=:2 ./run.sh
```

手动安装：

```bash
python3 -m venv .venv
.venv/bin/pip install -r requirements.txt
.venv/bin/python main.py
```

## 说明

- 账号列表保存在 `accounts.json`
- 删除账号不会自动删除 `profiles` 下的配置文件夹
