# Grok Bot 多开工具

跨平台桌面程序（PySide6）：用两栏布局管理多个账号，每个账号使用独立的浏览器配置，互不串号。

## 功能特性

- 左侧管理账号：添加、重命名、删除。
- 右侧查看状态、启动 / 停止实例、打开配置目录、填写备注。
- 每个账号对应独立的 Edge / Chrome / Chromium 用户数据目录（`profiles/<账号>/`）。
- 关闭启动器不会结束已启动的浏览器。账号列表保存在 `accounts.json`。

## 下载

本仓库目前没有已发布的 GitHub Release 安装包。请从源码运行。GitHub 自动生成的 Source code zip/tar 不算安装包。

## 界面截图

仓库里目前还没有已提交的真实产品界面截图（图标、logo 或品牌图不算）。请不要把下列预留路径当成已经存在的图片去引用（避免破链）。待在真实运行窗口中截取后放入：

- `docs/screenshots/01-workbench.png`
- `docs/screenshots/02-main-or-result.png`

截图说明必须写明操作系统、软件版本、是否示例/演示数据，以及是否在 Windows 安装后截取。

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

## 贡献

欢迎通过 Issue 和 Pull Request 参与，详见 [CONTRIBUTING.md](CONTRIBUTING.md)。安全问题请按 [SECURITY.md](SECURITY.md) 私下报告。参与时请遵守 [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md)。

## 许可证

本仓库尚未附带 LICENSE 文件，许可证未指定。

---

## English

# GrokBot MultiOpen

A cross-platform PySide6 desktop app for managing multiple accounts in a two-pane layout. Each account gets its own browser profile so sessions stay isolated.

## Features

- Left pane: add, rename, and delete accounts.
- Right pane: status, start / stop instances, open the profile folder, and notes.
- Each account uses a separate Edge / Chrome / Chromium user-data directory (`profiles/<account>/`).
- Closing the launcher does not quit browsers that are already running. Accounts are stored in `accounts.json`.

## Downloads

This repository has no published GitHub Release installer. Run it from source. The automatic Source code zip/tar from GitHub is not an installer.

## Screenshots

No real product-window screenshot has been committed yet (icons, logos, and brand art do not count). Do not add markdown image links to the reserved paths below until the files exist (that would be a broken link). After a live capture, place:

- `docs/screenshots/01-workbench.png`
- `docs/screenshots/02-main-or-result.png`

Captions must state the OS, version, whether the data is sample/demo, and whether the shot was taken after a Windows install.

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

## Contributing

Issues and pull requests are welcome. See [CONTRIBUTING.md](CONTRIBUTING.md). Please report vulnerabilities privately via [SECURITY.md](SECURITY.md). This project follows [CODE_OF_CONDUCT.md](CODE_OF_CONDUCT.md).

## License

No LICENSE file is included in this repository; the license is unspecified.
