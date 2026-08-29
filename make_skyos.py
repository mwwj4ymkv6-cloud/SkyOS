#!/usr/bin/env python3
from __future__ import annotations

import json
import os
import shutil
import stat
import subprocess
import sys
import textwrap
from pathlib import Path

PROJECT_NAME = "skyos"


def log(message: str) -> None:
    print(message, flush=True)


def write_text(path: Path, content: str, *, executable: bool = False) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(textwrap.dedent(content).lstrip(), encoding="utf-8")
    if executable:
        path.chmod(path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH)


def copy_logo(project_root: Path, logo_source: str | None) -> None:
    target = project_root / "assets" / "logo.png"
    if not logo_source:
        return

    source = Path(logo_source).expanduser().resolve()
    if not source.is_file():
        log(f"⚠️ Logo nicht gefunden: {source}")
        return
    if source.suffix.lower() != ".png":
        log("⚠️ Das Logo muss als PNG vorliegen.")
        return

    shutil.copy2(source, target)
    log(f"✅ Logo kopiert: {target}")


def create_project_structure(base_dir: Path, logo_source: str | None = None) -> Path:
    project_root = (base_dir / PROJECT_NAME).resolve()

    log("=" * 58)
    log("🚀 SkyOS 1.0 - Generiere optimierte Systemstruktur")
    log("=" * 58)

    directories = [
        project_root / "assets",
        project_root / "config" / "plymouth",
        project_root / "config" / "systemd",
        project_root / "media-center",
        project_root / "scripts",
        project_root / "output",
        project_root / "data",
    ]
    for directory in directories:
        directory.mkdir(parents=True, exist_ok=True)

    copy_logo(project_root, logo_source)

    main_py = r'''
import json
import os
import shutil
import sqlite3
import subprocess
import sys
from pathlib import Path

from PySide6.QtCore import Qt, QSize
from PySide6.QtGui import QFont, QKeySequence, QPixmap, QShortcut
from PySide6.QtWidgets import (
    QApplication,
    QFrame,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QMainWindow,
    QMessageBox,
    QPushButton,
    QScrollArea,
    QStackedWidget,
    QVBoxLayout,
    QWidget,
)

APP_NAME = "SkyOS Media Center"
INSTALL_ROOT = Path(os.environ.get("SKYOS_ROOT", "/usr/share/skyos"))
APP_DIR = INSTALL_ROOT / "media-center"
ASSET_DIR = INSTALL_ROOT / "assets"
CONFIG_FILE = INSTALL_ROOT / "config" / "skyos.json"

USER_DATA_DIR = Path.home() / ".local" / "share" / "skyos"
USER_DATA_DIR.mkdir(parents=True, exist_ok=True)
DATABASE_FILE = USER_DATA_DIR / "library.db"

DEFAULT_CONFIG = {
    "media_paths": [str(Path.home() / "Videos")],
    "browser_commands": [
        "google-chrome",
        "chromium",
        "chromium-browser",
        "firefox",
        "sensible-browser",
        "xdg-open",
    ],
}

def load_config() -> dict:
    config = DEFAULT_CONFIG.copy()
    try:
        if CONFIG_FILE.is_file():
            loaded = json.loads(CONFIG_FILE.read_text(encoding="utf-8"))
            if isinstance(loaded, dict):
                config.update(loaded)
    except (OSError, json.JSONDecodeError) as exc:
        print(f"SkyOS: Konfiguration konnte nicht geladen werden: {exc}", file=sys.stderr)
    return config

def init_database() -> None:
    with sqlite3.connect(DATABASE_FILE) as conn:
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS media (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                path TEXT NOT NULL UNIQUE,
                title TEXT NOT NULL,
                media_type TEXT NOT NULL DEFAULT 'movie',
                year INTEGER,
                description TEXT NOT NULL DEFAULT '',
                poster_path TEXT NOT NULL DEFAULT '',
                last_seen INTEGER NOT NULL DEFAULT 0,
                added_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
            )
            """
        )
        conn.commit()

class MediaCard(QFrame):
    def __init__(self, title: str, subtitle: str = "", parent: QWidget | None = None) -> None:
        super().__init__(parent)
        self.setObjectName("mediaCard")
        self.setFixedSize(210, 300)

        layout = QVBoxLayout(self)
        layout.setContentsMargins(12, 12, 12, 12)
        layout.setSpacing(8)

        poster = QLabel("🎬")
        poster.setAlignment(Qt.AlignmentFlag.AlignCenter)
        poster.setObjectName("posterPlaceholder")
        poster.setMinimumHeight(220)
        layout.addWidget(poster)

        title_label = QLabel(title)
        title_label.setWordWrap(True)
        title_label.setFont(QFont("Sans Serif", 11, QFont.Weight.DemiBold))
        layout.addWidget(title_label)

        if subtitle:
            subtitle_label = QLabel(subtitle)
            subtitle_label.setObjectName("mutedText")
            layout.addWidget(subtitle_label)

class SkyOSMainWindow(QMainWindow):
    def __init__(self) -> None:
        super().__init__()
        self.config = load_config()
        self.nav_buttons: list[QPushButton] = []

        self.setWindowTitle(APP_NAME)
        self.setMinimumSize(QSize(1100, 650))
        self.setStyleSheet(self.stylesheet())

        self._build_ui()
        self._install_shortcuts()
        self.showFullScreen()

    @staticmethod
    def stylesheet() -> str:
        return """
            QMainWindow, QWidget {
                background-color: #0d0e12;
                color: #ffffff;
                font-family: "Sans Serif";
            }
            QFrame#sidebar {
                background-color: #14161d;
                border-right: 1px solid #20242e;
            }
            QPushButton#navButton {
                background: transparent;
                color: #a0a5b5;
                border: none;
                padding: 14px 18px;
                text-align: left;
                border-radius: 10px;
            }
            QPushButton#navButton:hover,
            QPushButton#navButton:focus,
            QPushButton#navButton[active="true"] {
                background-color: #232936;
                color: #ffffff;
                font-weight: 700;
            }
            QScrollArea {
                border: none;
                background: transparent;
            }
            QFrame#mediaCard {
                background-color: #171a22;
                border: 1px solid #242936;
                border-radius: 14px;
            }
            QFrame#mediaCard:hover {
                border: 1px solid #4f67ff;
                background-color: #1c202a;
            }
            QLabel#posterPlaceholder {
                background-color: #222734;
                border-radius: 10px;
                font-size: 48px;
            }
            QLabel#mutedText {
                color: #8e95a8;
            }
            QPushButton#actionButton {
                background-color: #4f67ff;
                border: none;
                border-radius: 10px;
                padding: 10px 16px;
                color: white;
                font-weight: 700;
            }
            QPushButton#actionButton:hover,
            QPushButton#actionButton:focus {
                background-color: #6377ff;
            }
        """

    def _build_ui(self) -> None:
        root = QWidget()
        self.setCentralWidget(root)

        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(0, 0, 0, 0)
        root_layout.setSpacing(0)

        root_layout.addWidget(self._build_sidebar())

        self.stack = QStackedWidget()
        self.stack.addWidget(self._build_home_page())
        self.stack.addWidget(self._build_simple_page("Filme", "Deine Film-Bibliothek wird hier angezeigt."))
        self.stack.addWidget(self._build_simple_page("Serien", "Deine Serien-Bibliothek wird hier angezeigt."))
        self.stack.addWidget(self._build_simple_page("Zuletzt gesehen", "Hier erscheinen zuletzt abgespielte Inhalte."))
        self.stack.addWidget(self._build_simple_page("Browser", "Browser wird in einem separaten Fenster geöffnet."))
        self.stack.addWidget(self._build_simple_page("Desktop", "Mit diesem Punkt kannst du SkyOS minimieren."))
        self.stack.addWidget(self._build_simple_page("Einstellungen", "SkyOS-Konfiguration und NAS-Pfade."))
        root_layout.addWidget(self.stack, 1)

    def _build_sidebar(self) -> QWidget:
        sidebar = QFrame()
        sidebar.setObjectName("sidebar")
        sidebar.setFixedWidth(250)

        layout = QVBoxLayout(sidebar)
        layout.setContentsMargins(16, 24, 16, 20)
        layout.setSpacing(8)

        logo_label = QLabel()
        logo_path = ASSET_DIR / "logo.png"
        if logo_path.is_file():
            pixmap = QPixmap(str(logo_path))
            if not pixmap.isNull():
                logo_label.setPixmap(
                    pixmap.scaledToWidth(
                        145,
                        Qt.TransformationMode.SmoothTransformation,
                    )
                )
        if logo_label.pixmap() is None:
            logo_label.setText("SkyOS")
            logo_label.setFont(QFont("Sans Serif", 24, QFont.Weight.Bold))

        logo_label.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(logo_label)
        layout.addSpacing(28)

        nav_items = [
            ("Startseite", self.show_home),
            ("Filme", lambda: self.show_page(1)),
            ("Serien", lambda: self.show_page(2)),
            ("Zuletzt gesehen", lambda: self.show_page(3)),
            ("Browser", self.open_browser),
            ("Desktop", self.show_desktop),
            ("Einstellungen", lambda: self.show_page(6)),
        ]

        for index, (label, callback) in enumerate(nav_items):
            button = QPushButton(label)
            button.setObjectName("navButton")
            button.setProperty("active", index == 0)
            button.setFont(QFont("Sans Serif", 11))
            button.setFocusPolicy(Qt.FocusPolicy.StrongFocus)
            button.clicked.connect(callback)
            layout.addWidget(button)
            self.nav_buttons.append(button)

        layout.addStretch(1)

        version = QLabel("SkyOS 1.0")
        version.setObjectName("mutedText")
        version.setAlignment(Qt.AlignmentFlag.AlignCenter)
        layout.addWidget(version)
        return sidebar

    def _build_home_page(self) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(34, 28, 34, 28)
        layout.setSpacing(18)

        title = QLabel("SkyOS Media Center")
        title.setFont(QFont("Sans Serif", 26, QFont.Weight.Bold))
        layout.addWidget(title)

        subtitle = QLabel("Deine Filme und Serien – schnell, lokal und NAS-bereit.")
        subtitle.setObjectName("mutedText")
        layout.addWidget(subtitle)

        scroll = QScrollArea()
        scroll.setWidgetResizable(True)

        content = QWidget()
        grid = QGridLayout(content)
        grid.setContentsMargins(0, 10, 0, 10)
        grid.setHorizontalSpacing(18)
        grid.setVerticalSpacing(18)

        demo_items = [
            ("Film hinzufügen", "Bibliothek"),
            ("NAS verbinden", "Netzwerk"),
            ("Zuletzt gesehen", "Fortsetzen"),
            ("Serien", "Bibliothek"),
        ]
        for index, (name, info) in enumerate(demo_items):
            grid.addWidget(MediaCard(name, info), index // 4, index % 4)

        grid.setColumnStretch(4, 1)
        grid.setRowStretch(1, 1)
        scroll.setWidget(content)
        layout.addWidget(scroll, 1)
        return page

    def _build_simple_page(self, title_text: str, body_text: str) -> QWidget:
        page = QWidget()
        layout = QVBoxLayout(page)
        layout.setContentsMargins(34, 28, 34, 28)
        layout.setSpacing(14)

        title = QLabel(title_text)
        title.setFont(QFont("Sans Serif", 26, QFont.Weight.Bold))
        layout.addWidget(title)

        body = QLabel(body_text)
        body.setObjectName("mutedText")
        body.setWordWrap(True)
        layout.addWidget(body)

        if title_text == "Browser":
            button = QPushButton("Browser öffnen")
            button.setObjectName("actionButton")
            button.clicked.connect(self.launch_external_browser)
            layout.addWidget(button, 0, Qt.AlignmentFlag.AlignLeft)
        elif title_text == "Desktop":
            button = QPushButton("SkyOS minimieren")
            button.setObjectName("actionButton")
            button.clicked.connect(self.showMinimized)
            layout.addWidget(button, 0, Qt.AlignmentFlag.AlignLeft)

        layout.addStretch(1)
        return page

    def _install_shortcuts(self) -> None:
        QShortcut(QKeySequence("F11"), self, activated=self.toggle_fullscreen)
        QShortcut(QKeySequence("Ctrl+Alt+Q"), self, activated=self.close)
        QShortcut(QKeySequence("Escape"), self, activated=self.show_home)

    def set_active_nav(self, index: int) -> None:
        for button_index, button in enumerate(self.nav_buttons):
            button.setProperty("active", button_index == index)
            button.style().unpolish(button)
            button.style().polish(button)

    def show_page(self, index: int) -> None:
        self.stack.setCurrentIndex(index)
        self.set_active_nav(index)

    def show_home(self) -> None:
        self.show_page(0)

    def open_browser(self) -> None:
        self.show_page(4)
        self.launch_external_browser()

    def launch_external_browser(self) -> None:
        commands = self.config.get("browser_commands", DEFAULT_CONFIG["browser_commands"])
        for command in commands:
            executable = shutil.which(command)
            if not executable:
                continue
            try:
                if command == "xdg-open":
                    subprocess.Popen([executable, "https://www.google.com"], start_new_session=True)
                else:
                    subprocess.Popen([executable], start_new_session=True)
                return
            except OSError:
                continue

        QMessageBox.warning(
            self,
            "Browser nicht gefunden",
            "Es wurde kein unterstützter Browser gefunden. Installiere z. B. Chromium oder Firefox.",
        )

    def show_desktop(self) -> None:
        self.show_page(5)
        self.showMinimized()

    def toggle_fullscreen(self) -> None:
        if self.isFullScreen():
            self.showNormal()
        else:
            self.showFullScreen()

def main() -> int:
    init_database()
    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName("SkyOS")
    window = SkyOSMainWindow()
    window.show()
    return app.exec()

if __name__ == "__main__":
    raise SystemExit(main())
'''
    write_text(project_root / "media-center" / "main.py", main_py, executable=True)

    config = {
        "media_paths": ["/mnt/media", "/mnt/nas"],
        "browser_commands": [
            "google-chrome",
            "chromium",
            "chromium-browser",
            "firefox",
            "sensible-browser",
            "xdg-open",
        ],
    }
    write_text(
        project_root / "config" / "skyos.json",
        json.dumps(config, ensure_ascii=False, indent=2) + "\n",
    )

    plymouth_script = r'''
    logo.image = Image("logo.png");
    logo.sprite = Sprite(logo.image);
    logo.sprite.SetX(Window.GetWidth() / 2 - logo.image.GetWidth() / 2);
    logo.sprite.SetY(Window.GetHeight() / 2 - logo.image.GetHeight() / 2);

    fun refresh_callback () {
        t = System.GetTime();
        opacity = 0.80 + Math.Sin(t * 3.0) * 0.20;
        logo.sprite.SetOpacity(opacity);
    }

    Plymouth.SetRefreshFunction(refresh_callback);
    '''
    write_text(project_root / "config" / "plymouth" / "skyos.script", plymouth_script)

    plymouth_theme = r'''
    [Plymouth Theme]
    Name=SkyOS Boot
    Description=Cineastischer SkyOS Systemstart
    ModuleName=script

    [script]
    ImageDir=/usr/share/plymouth/themes/skyos
    ScriptFile=/usr/share/plymouth/themes/skyos/skyos.script
    '''
    write_text(project_root / "config" / "plymouth" / "skyos.plymouth", plymouth_theme)

    session_script = r'''
    #!/usr/bin/env bash
    set -u

    export QT_QPA_PLATFORM="${QT_QPA_PLATFORM:-xcb}"
    export SKYOS_ROOT="${SKYOS_ROOT:-/usr/share/skyos}"

    if command -v picom >/dev/null 2>&1; then
        picom -b >/dev/null 2>&1 || true
    fi

    exec python3 "$SKYOS_ROOT/media-center/main.py"
    '''
    write_text(project_root / "scripts" / "skyos-session.sh", session_script, executable=True)

    service_file = r'''
    [Unit]
    Description=SkyOS Media Center
    After=graphical-session.target network-online.target
    Wants=network-online.target

    [Service]
    Type=simple
    ExecStart=/usr/share/skyos/scripts/skyos-session.sh
    Restart=on-failure
    RestartSec=2
    Environment=PYTHONUNBUFFERED=1

    [Install]
    WantedBy=default.target
    '''
    write_text(project_root / "config" / "systemd" / "skyos-media-center.service", service_file)

    requirements = "PySide6>=6.7,<7\n"
    write_text(project_root / "requirements.txt", requirements)

    log("✅ Dateistruktur erstellt.")
    log(f"📁 Projekt: {project_root}")
    return project_root


def validate_project(project_root: Path) -> None:
    errors: list[str] = []

    main_file = project_root / "media-center" / "main.py"
    try:
        subprocess.run(
            [sys.executable, "-m", "py_compile", str(main_file)],
            check=True,
            capture_output=True,
            text=True,
        )
        log("✅ Python-Syntax geprüft.")
    except subprocess.CalledProcessError as exc:
        errors.append(exc.stderr.strip() or "Unbekannter Python-Syntaxfehler")

    if shutil.which("bash"):
        for shell_file in [
            project_root / "scripts" / "skyos-session.sh",
        ]:
            if shell_file.is_file():
                result = subprocess.run(
                    ["bash", "-n", str(shell_file)],
                    capture_output=True,
                    text=True,
                )
                if result.returncode != 0:
                    errors.append(f"{shell_file.name}: {result.stderr.strip()}")
        if not errors:
            log("✅ Bash-Syntax geprüft.")

    try:
        json.loads((project_root / "config" / "skyos.json").read_text(encoding="utf-8"))
        log("✅ JSON-Konfiguration geprüft.")
    except (OSError, json.JSONDecodeError) as exc:
        errors.append(f"skyos.json: {exc}")

    if errors:
        log("❌ Validierung fehlgeschlagen:")
        for error in errors:
            log(f"   - {error}")
        raise SystemExit(1)


def main() -> int:
    base_dir = Path.cwd()
    logo_source = sys.argv[1] if len(sys.argv) > 1 else None

    try:
        project_root = create_project_structure(base_dir, logo_source)
        validate_project(project_root)
    except (OSError, ValueError) as exc:
        print(f"❌ Fehler: {exc}", file=sys.stderr)
        return 1

    log("=" * 58)
    log("🎉 SkyOS 1.0 Projekt erfolgreich generiert und validiert.")
    log("=" * 58)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
