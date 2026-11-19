#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""Grok Bot 多开工具 — 跨平台桌面启动器 (PySide6)

两栏布局：左侧账号管理，右侧程序面板。
每个账号使用独立 Edge/Chrome 用户数据目录，互不串号。
关闭启动器不会结束已启动的浏览器。
"""

from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
import sys
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any


def _die_import(msg: str) -> None:
    print(msg, file=sys.stderr)
    if sys.platform == "win32":
        try:
            input("按回车键退出...")
        except EOFError:
            pass
    sys.exit(1)


try:
    from PySide6.QtCore import Qt, QTimer
    from PySide6.QtGui import QColor, QFont, QPalette
    from PySide6.QtWidgets import (
        QApplication,
        QDialog,
        QDialogButtonBox,
        QFormLayout,
        QFrame,
        QHBoxLayout,
        QInputDialog,
        QLabel,
        QLineEdit,
        QListWidget,
        QListWidgetItem,
        QMainWindow,
        QMessageBox,
        QPushButton,
        QSplitter,
        QTextEdit,
        QVBoxLayout,
        QWidget,
    )
except ImportError:
    _die_import(
        "缺少 PySide6。\n"
        "请先运行 run.bat / run.sh，或执行：\n"
        "  pip install -r requirements.txt"
    )


# ---------------------------------------------------------------------------
# Paths & constants
# ---------------------------------------------------------------------------

APP_DIR = Path(__file__).resolve().parent
ACCOUNTS_FILE = APP_DIR / "accounts.json"
PROFILES_DIR = APP_DIR / "profiles"
START_URL = "https://cursor.com"

EDGE_CANDIDATES_WIN = [
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Microsoft\Edge\Application\msedge.exe"),
]
CHROME_CANDIDATES_WIN = [
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    os.path.expandvars(r"%LOCALAPPDATA%\Google\Chrome\Application\chrome.exe"),
]
LINUX_BROWSER_NAMES = [
    ("google-chrome-stable", "Google Chrome"),
    ("google-chrome", "Google Chrome"),
    ("chromium-browser", "Chromium"),
    ("chromium", "Chromium"),
]
LINUX_BROWSER_PATHS = [
    ("/usr/bin/google-chrome-stable", "Google Chrome"),
    ("/usr/bin/google-chrome", "Google Chrome"),
    ("/usr/bin/chromium-browser", "Chromium"),
    ("/usr/bin/chromium", "Chromium"),
    ("/snap/bin/chromium", "Chromium"),
]


def safe_name(name: str) -> str:
    """Make a filesystem-safe folder name from account display name."""
    s = re.sub(r'[<>:"/\\|?*\x00-\x1f]', "_", name.strip())
    s = s.strip(" .") or "account"
    return s[:80]


def now_iso() -> str:
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")


def find_browser() -> tuple[str | None, str]:
    """Return (exe_path, browser_name) or (None, ''). Prefer Edge on Windows."""
    if sys.platform == "win32":
        for p in EDGE_CANDIDATES_WIN:
            if p and Path(p).is_file():
                return p, "Microsoft Edge"
        for p in CHROME_CANDIDATES_WIN:
            if p and Path(p).is_file():
                return p, "Google Chrome"
        for cmd, label in (("msedge", "Microsoft Edge"), ("chrome", "Google Chrome")):
            try:
                r = subprocess.run(
                    ["where", cmd], capture_output=True, text=True, timeout=5
                )
                if r.returncode == 0 and r.stdout.strip():
                    return r.stdout.strip().splitlines()[0].strip(), label
            except Exception:
                pass
        return None, ""

    # Linux / other: Chrome / Chromium
    for path, label in LINUX_BROWSER_PATHS:
        if Path(path).is_file():
            return path, label
    for cmd, label in LINUX_BROWSER_NAMES:
        found = shutil.which(cmd)
        if found:
            return found, label
    return None, ""


# ---------------------------------------------------------------------------
# Data layer
# ---------------------------------------------------------------------------


class AccountStore:
    def __init__(self, path: Path, profiles_dir: Path | None = None) -> None:
        self.path = path
        self.profiles_dir = profiles_dir or PROFILES_DIR
        self.accounts: list[dict[str, Any]] = []
        self.profiles_dir.mkdir(parents=True, exist_ok=True)
        self.load()

    def load(self) -> None:
        if not self.path.exists():
            self.accounts = []
            self.save()
            return
        try:
            data = json.loads(self.path.read_text(encoding="utf-8"))
            self.accounts = data.get("accounts", [])
        except Exception:
            self.accounts = []

    def save(self) -> None:
        payload = {"accounts": self.accounts, "updated_at": now_iso()}
        self.path.write_text(
            json.dumps(payload, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def get(self, account_id: str) -> dict[str, Any] | None:
        for a in self.accounts:
            if a["id"] == account_id:
                return a
        return None

    def add(self, name: str, notes: str = "") -> dict[str, Any]:
        folder = safe_name(name)
        base = folder
        n = 1
        while (self.profiles_dir / folder).exists():
            folder = f"{base}_{n}"
            n += 1
        profile_dir = self.profiles_dir / folder
        profile_dir.mkdir(parents=True, exist_ok=True)
        acc = {
            "id": str(uuid.uuid4()),
            "name": name.strip(),
            "notes": notes,
            "profile_dir": str(profile_dir),
            "created_at": now_iso(),
        }
        self.accounts.append(acc)
        self.save()
        return acc

    def rename(self, account_id: str, new_name: str) -> bool:
        acc = self.get(account_id)
        if not acc:
            return False
        acc["name"] = new_name.strip()
        self.save()
        return True

    def update_notes(self, account_id: str, notes: str) -> bool:
        acc = self.get(account_id)
        if not acc:
            return False
        acc["notes"] = notes
        self.save()
        return True

    def delete(self, account_id: str) -> bool:
        before = len(self.accounts)
        self.accounts = [a for a in self.accounts if a["id"] != account_id]
        if len(self.accounts) < before:
            self.save()
            return True
        return False


# ---------------------------------------------------------------------------
# Process manager
# ---------------------------------------------------------------------------


class InstanceManager:
    """Track launched browser processes per account id."""

    def __init__(self) -> None:
        self._procs: dict[str, subprocess.Popen] = {}

    def is_running(self, account_id: str) -> bool:
        proc = self._procs.get(account_id)
        if proc is None:
            return False
        if proc.poll() is not None:
            self._procs.pop(account_id, None)
            return False
        return True

    def start(self, account_id: str, profile_dir: str) -> tuple[bool, str]:
        if self.is_running(account_id):
            return False, "该账号已在运行中"

        browser, label = find_browser()
        if not browser:
            return (
                False,
                "未找到可用浏览器。\n"
                "Windows 请安装 Microsoft Edge 或 Google Chrome；\n"
                "Linux 请安装 Google Chrome 或 Chromium。",
            )

        Path(profile_dir).mkdir(parents=True, exist_ok=True)
        args = [
            browser,
            f"--user-data-dir={profile_dir}",
            "--no-first-run",
            "--no-default-browser-check",
            "--new-window",
            f"--app={START_URL}",
        ]
        try:
            kwargs: dict[str, Any] = {
                "stdout": subprocess.DEVNULL,
                "stderr": subprocess.DEVNULL,
            }
            if sys.platform == "win32":
                # Detach so closing the launcher does not kill the browser.
                flags = 0
                flags |= getattr(subprocess, "CREATE_NEW_PROCESS_GROUP", 0)
                flags |= getattr(subprocess, "DETACHED_PROCESS", 0)
                kwargs["creationflags"] = flags
            else:
                kwargs["start_new_session"] = True
            proc = subprocess.Popen(args, **kwargs)
            self._procs[account_id] = proc
            return True, f"已用 {label} 启动"
        except Exception as e:
            return False, f"启动失败：{e}"

    def stop(self, account_id: str) -> tuple[bool, str]:
        proc = self._procs.get(account_id)
        if proc is None or proc.poll() is not None:
            self._procs.pop(account_id, None)
            return False, "该账号未在运行"
        try:
            proc.terminate()
            try:
                proc.wait(timeout=5)
            except subprocess.TimeoutExpired:
                proc.kill()
                proc.wait(timeout=3)
            self._procs.pop(account_id, None)
            return True, "已停止"
        except Exception as e:
            return False, f"停止失败：{e}"


# ---------------------------------------------------------------------------
# Styles
# ---------------------------------------------------------------------------

DARK_STYLESHEET = """
QMainWindow, QWidget#central {
    background-color: #1e1e1e;
    color: #e8e8e8;
}
QLabel {
    color: #e8e8e8;
}
QLabel#muted {
    color: #9a9a9a;
}
QLabel#title {
    font-size: 18px;
    font-weight: 700;
}
QLabel#nameValue {
    font-size: 20px;
    font-weight: 700;
}
QLabel#statusRunning {
    color: #3dd68c;
    font-size: 15px;
}
QLabel#statusIdle {
    color: #a0a0a0;
    font-size: 15px;
}
QFrame#leftPane, QFrame#rightPane, QFrame#detailCard {
    background-color: #252526;
    border: none;
}
QListWidget {
    background-color: #2b2b2b;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
    padding: 4px;
    outline: none;
}
QListWidget::item {
    padding: 10px 12px;
    border-radius: 6px;
    margin: 2px;
}
QListWidget::item:selected {
    background-color: #1f6aa5;
    color: white;
}
QListWidget::item:hover:!selected {
    background-color: #333333;
}
QPushButton {
    background-color: #1f6aa5;
    color: white;
    border: none;
    border-radius: 6px;
    padding: 8px 14px;
    font-weight: 600;
}
QPushButton:hover {
    background-color: #2578b8;
}
QPushButton:pressed {
    background-color: #185a8a;
}
QPushButton:disabled {
    background-color: #3a3a3a;
    color: #777777;
}
QPushButton#secondary {
    background-color: #3a3a3a;
}
QPushButton#secondary:hover {
    background-color: #505050;
}
QPushButton#danger {
    background-color: #8b2942;
}
QPushButton#danger:hover {
    background-color: #a8334f;
}
QTextEdit {
    background-color: #1e1e1e;
    color: #e8e8e8;
    border: 1px solid #3a3a3a;
    border-radius: 8px;
    padding: 8px;
}
QSplitter::handle {
    background-color: #1e1e1e;
    width: 2px;
}
QInputDialog, QMessageBox {
    background-color: #2b2b2b;
}
"""


# ---------------------------------------------------------------------------
# Main window
# ---------------------------------------------------------------------------


class MainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.setWindowTitle("Grok Bot 多开")
        self.resize(860, 540)
        self.setMinimumSize(720, 440)

        self.store = AccountStore(ACCOUNTS_FILE)
        self.instances = InstanceManager()
        self.selected_id: str | None = None

        self._build_ui()
        self._refresh_account_list()
        self._show_empty()

        self._poll_timer = QTimer(self)
        self._poll_timer.timeout.connect(self._poll_status)
        self._poll_timer.start(2000)

    def _build_ui(self) -> None:
        central = QWidget()
        central.setObjectName("central")
        self.setCentralWidget(central)
        root = QHBoxLayout(central)
        root.setContentsMargins(0, 0, 0, 0)
        root.setSpacing(0)

        splitter = QSplitter(Qt.Orientation.Horizontal)
        root.addWidget(splitter)

        # ---- Left: 账号 ----
        left = QFrame()
        left.setObjectName("leftPane")
        left.setMinimumWidth(260)
        left_layout = QVBoxLayout(left)
        left_layout.setContentsMargins(16, 16, 16, 16)
        left_layout.setSpacing(10)

        left_title = QLabel("账号")
        left_title.setObjectName("title")
        left_layout.addWidget(left_title)

        self.account_list = QListWidget()
        self.account_list.currentItemChanged.connect(self._on_list_selection)
        left_layout.addWidget(self.account_list, stretch=1)

        btn_row = QHBoxLayout()
        btn_row.setSpacing(6)
        self.btn_add = QPushButton("添加")
        self.btn_rename = QPushButton("重命名")
        self.btn_rename.setObjectName("secondary")
        self.btn_delete = QPushButton("删除")
        self.btn_delete.setObjectName("danger")
        self.btn_add.clicked.connect(self._add_account)
        self.btn_rename.clicked.connect(self._rename_account)
        self.btn_delete.clicked.connect(self._delete_account)
        btn_row.addWidget(self.btn_add)
        btn_row.addWidget(self.btn_rename)
        btn_row.addWidget(self.btn_delete)
        left_layout.addLayout(btn_row)

        # ---- Right: 程序面板 ----
        right = QFrame()
        right.setObjectName("rightPane")
        right_layout = QVBoxLayout(right)
        right_layout.setContentsMargins(24, 16, 24, 24)
        right_layout.setSpacing(10)

        right_title = QLabel("程序面板")
        right_title.setObjectName("title")
        right_layout.addWidget(right_title)

        self.detail_card = QFrame()
        self.detail_card.setObjectName("detailCard")
        detail = QVBoxLayout(self.detail_card)
        detail.setContentsMargins(20, 20, 20, 20)
        detail.setSpacing(10)

        self.empty_label = QLabel("请在左侧选择或添加一个账号")
        self.empty_label.setObjectName("muted")
        self.empty_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        detail.addWidget(self.empty_label)

        self.detail_body = QWidget()
        form = QVBoxLayout(self.detail_body)
        form.setContentsMargins(0, 0, 0, 0)
        form.setSpacing(8)

        name_row = QHBoxLayout()
        lbl_name_k = QLabel("账号名称")
        lbl_name_k.setObjectName("muted")
        lbl_name_k.setFixedWidth(72)
        self.lbl_name_v = QLabel("")
        self.lbl_name_v.setObjectName("nameValue")
        name_row.addWidget(lbl_name_k)
        name_row.addWidget(self.lbl_name_v, stretch=1)
        form.addLayout(name_row)

        status_row = QHBoxLayout()
        lbl_status_k = QLabel("状态")
        lbl_status_k.setObjectName("muted")
        lbl_status_k.setFixedWidth(72)
        self.lbl_status_v = QLabel("")
        status_row.addWidget(lbl_status_k)
        status_row.addWidget(self.lbl_status_v, stretch=1)
        form.addLayout(status_row)

        profile_row = QHBoxLayout()
        lbl_profile_k = QLabel("配置目录")
        lbl_profile_k.setObjectName("muted")
        lbl_profile_k.setFixedWidth(72)
        self.lbl_profile_v = QLabel("")
        self.lbl_profile_v.setObjectName("muted")
        self.lbl_profile_v.setWordWrap(True)
        profile_row.addWidget(lbl_profile_k, alignment=Qt.AlignmentFlag.AlignTop)
        profile_row.addWidget(self.lbl_profile_v, stretch=1)
        form.addLayout(profile_row)

        notes_k = QLabel("备注")
        notes_k.setObjectName("muted")
        form.addWidget(notes_k)
        self.notes_box = QTextEdit()
        self.notes_box.setFixedHeight(100)
        form.addWidget(self.notes_box)

        notes_btn_row = QHBoxLayout()
        notes_btn_row.addStretch(1)
        self.btn_save_notes = QPushButton("保存备注")
        self.btn_save_notes.setObjectName("secondary")
        self.btn_save_notes.clicked.connect(self._save_notes)
        notes_btn_row.addWidget(self.btn_save_notes)
        form.addLayout(notes_btn_row)

        action_row = QHBoxLayout()
        action_row.setSpacing(8)
        self.btn_start = QPushButton("启动")
        self.btn_stop = QPushButton("停止")
        self.btn_stop.setObjectName("danger")
        self.btn_folder = QPushButton("打开目录")
        self.btn_folder.setObjectName("secondary")
        self.btn_start.clicked.connect(self._start_instance)
        self.btn_stop.clicked.connect(self._stop_instance)
        self.btn_folder.clicked.connect(self._open_profile_dir)
        action_row.addWidget(self.btn_start)
        action_row.addWidget(self.btn_stop)
        action_row.addWidget(self.btn_folder)
        form.addLayout(action_row)
        form.addStretch(1)

        detail.addWidget(self.detail_body)
        self.detail_body.hide()
        right_layout.addWidget(self.detail_card, stretch=1)

        splitter.addWidget(left)
        splitter.addWidget(right)
        splitter.setStretchFactor(0, 0)
        splitter.setStretchFactor(1, 1)
        splitter.setSizes([280, 580])

    # ---- list / selection ----

    def _refresh_account_list(self) -> None:
        current_id = self.selected_id
        self.account_list.blockSignals(True)
        self.account_list.clear()
        for acc in self.store.accounts:
            running = self.instances.is_running(acc["id"])
            suffix = "  ●" if running else ""
            item = QListWidgetItem(f"{acc['name']}{suffix}")
            item.setData(Qt.ItemDataRole.UserRole, acc["id"])
            self.account_list.addItem(item)
            if acc["id"] == current_id:
                self.account_list.setCurrentItem(item)
        self.account_list.blockSignals(False)

        if current_id and self.store.get(current_id):
            self._show_detail(self.store.get(current_id))  # type: ignore[arg-type]
        elif self.store.accounts:
            # keep empty until user selects
            if not current_id:
                self._show_empty()
            else:
                self.selected_id = None
                self._show_empty()
        else:
            self.selected_id = None
            self._show_empty()

    def _on_list_selection(
        self, current: QListWidgetItem | None, _previous: QListWidgetItem | None
    ) -> None:
        if current is None:
            self.selected_id = None
            self._show_empty()
            return
        aid = current.data(Qt.ItemDataRole.UserRole)
        self.selected_id = aid
        acc = self.store.get(aid)
        if acc:
            self._show_detail(acc)
        else:
            self._show_empty()

    def _show_empty(self) -> None:
        self.empty_label.show()
        self.detail_body.hide()

    def _show_detail(self, acc: dict[str, Any]) -> None:
        self.empty_label.hide()
        self.detail_body.show()
        running = self.instances.is_running(acc["id"])
        self.lbl_name_v.setText(acc["name"])
        self._set_status_label(running)
        self.lbl_profile_v.setText(acc.get("profile_dir", ""))
        self.notes_box.blockSignals(True)
        self.notes_box.setPlainText(acc.get("notes") or "")
        self.notes_box.blockSignals(False)
        self.btn_start.setEnabled(not running)
        self.btn_stop.setEnabled(running)

    def _set_status_label(self, running: bool) -> None:
        if running:
            self.lbl_status_v.setText("运行中")
            self.lbl_status_v.setObjectName("statusRunning")
        else:
            self.lbl_status_v.setText("未启动")
            self.lbl_status_v.setObjectName("statusIdle")
        # Force style re-apply after objectName change
        self.lbl_status_v.style().unpolish(self.lbl_status_v)
        self.lbl_status_v.style().polish(self.lbl_status_v)

    # ---- account actions ----

    def _add_account(self) -> None:
        name, ok = QInputDialog.getText(self, "添加账号", "请输入账号名称：")
        if not ok:
            return
        name = name.strip()
        if not name:
            return
        acc = self.store.add(name)
        self.selected_id = acc["id"]
        self._refresh_account_list()

    def _rename_account(self) -> None:
        if not self.selected_id:
            QMessageBox.information(self, "提示", "请先选择一个账号")
            return
        acc = self.store.get(self.selected_id)
        if not acc:
            return
        new_name, ok = QInputDialog.getText(
            self, "重命名", f"新名称（当前：{acc['name']}）：", text=acc["name"]
        )
        if not ok:
            return
        new_name = new_name.strip()
        if not new_name:
            return
        self.store.rename(self.selected_id, new_name)
        self._refresh_account_list()

    def _delete_account(self) -> None:
        if not self.selected_id:
            QMessageBox.information(self, "提示", "请先选择一个账号")
            return
        acc = self.store.get(self.selected_id)
        if not acc:
            return
        if self.instances.is_running(self.selected_id):
            QMessageBox.warning(self, "提示", "请先停止该账号的实例，再删除")
            return
        reply = QMessageBox.question(
            self,
            "确认删除",
            f"确定删除账号「{acc['name']}」？\n"
            "（浏览器配置文件夹会保留在 profiles 目录，可手动清理）",
        )
        if reply != QMessageBox.StandardButton.Yes:
            return
        self.store.delete(self.selected_id)
        self.selected_id = None
        self._refresh_account_list()

    def _save_notes(self) -> None:
        if not self.selected_id:
            return
        notes = self.notes_box.toPlainText()
        self.store.update_notes(self.selected_id, notes)
        QMessageBox.information(self, "提示", "备注已保存")

    def _start_instance(self) -> None:
        if not self.selected_id:
            return
        acc = self.store.get(self.selected_id)
        if not acc:
            return
        ok, msg = self.instances.start(acc["id"], acc["profile_dir"])
        if not ok:
            QMessageBox.critical(self, "启动失败", msg)
        self._refresh_account_list()

    def _stop_instance(self) -> None:
        if not self.selected_id:
            return
        ok, msg = self.instances.stop(self.selected_id)
        if not ok and msg != "该账号未在运行":
            QMessageBox.critical(self, "停止失败", msg)
        self._refresh_account_list()

    def _open_profile_dir(self) -> None:
        if not self.selected_id:
            return
        acc = self.store.get(self.selected_id)
        if not acc:
            return
        path = Path(acc["profile_dir"])
        path.mkdir(parents=True, exist_ok=True)
        try:
            if sys.platform == "win32":
                # Explorer must open the folder (not a browser)
                subprocess.Popen(["explorer", str(path)])
            elif sys.platform == "darwin":
                subprocess.Popen(["open", str(path)])
            else:
                # Prefer a real file manager; xdg-open may hand directories to Chrome
                opened = False
                for cmd in (
                    ["thunar", str(path)],
                    ["nautilus", str(path)],
                    ["dolphin", str(path)],
                    ["pcmanfm", str(path)],
                    ["xdg-open", str(path)],
                ):
                    if shutil.which(cmd[0]):
                        subprocess.Popen(cmd)
                        opened = True
                        break
                if not opened:
                    raise RuntimeError("未找到可用的文件管理器")
        except Exception as e:
            QMessageBox.critical(self, "错误", f"无法打开目录：{e}")

    def _poll_status(self) -> None:
        for aid, proc in list(self.instances._procs.items()):
            if proc.poll() is not None:
                self.instances._procs.pop(aid, None)

        # Refresh list indicators without clearing selection
        for i in range(self.account_list.count()):
            item = self.account_list.item(i)
            aid = item.data(Qt.ItemDataRole.UserRole)
            acc = self.store.get(aid)
            if not acc:
                continue
            running = self.instances.is_running(aid)
            suffix = "  ●" if running else ""
            item.setText(f"{acc['name']}{suffix}")

        if self.selected_id:
            acc = self.store.get(self.selected_id)
            if acc and self.detail_body.isVisible():
                running = self.instances.is_running(acc["id"])
                self._set_status_label(running)
                self.btn_start.setEnabled(not running)
                self.btn_stop.setEnabled(running)

    def closeEvent(self, event) -> None:  # noqa: N802
        # Leave browser instances running when closing the launcher.
        event.accept()


def main() -> None:
    # High-DPI friendly defaults
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    app.setStyleSheet(DARK_STYLESHEET)

    # Dark palette fallback for native dialogs
    palette = QPalette()
    palette.setColor(QPalette.ColorRole.Window, QColor("#1e1e1e"))
    palette.setColor(QPalette.ColorRole.WindowText, QColor("#e8e8e8"))
    palette.setColor(QPalette.ColorRole.Base, QColor("#2b2b2b"))
    palette.setColor(QPalette.ColorRole.AlternateBase, QColor("#252526"))
    palette.setColor(QPalette.ColorRole.Text, QColor("#e8e8e8"))
    palette.setColor(QPalette.ColorRole.Button, QColor("#3a3a3a"))
    palette.setColor(QPalette.ColorRole.ButtonText, QColor("#e8e8e8"))
    palette.setColor(QPalette.ColorRole.Highlight, QColor("#1f6aa5"))
    palette.setColor(QPalette.ColorRole.HighlightedText, QColor("#ffffff"))
    app.setPalette(palette)

    win = MainWindow()
    win.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
