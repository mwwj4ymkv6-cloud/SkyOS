#!/usr/bin/env python3
import os

def create_project_structure():
    print("==================================================")
    print("🚀 SkyOS 1.0 - Generiere Systemstruktur...")
    print("==================================================")

    # Ordnerstrukturen anlegen
    dirs = [
        "skyos/assets",
        "skyos/config/plymouth",
        "skyos/media-center",
        "skyos/scripts",
        "skyos/output"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # 1. Media Center App
    main_py = '''import sys
import os
import sqlite3
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QStackedWidget, 
                             QGridLayout, QScrollArea, QFrame)
from PySide6.QtGui import QPixmap, QKeyEvent, QFont

class SkyOSMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SkyOS Media Center")
        self.setWindowState(Qt.WindowFullScreen)
        self.init_ui()

    def init_ui(self):
        main_widget = QWidget()
        main_widget.setStyleSheet("background-color: #0d0e12; color: #ffffff;")
        self.setCentralWidget(main_widget)
        
        layout = QHBoxLayout(main_widget)
        layout.setContentsMargins(0, 0, 0, 0)
        layout.setSpacing(0)

        # Sidebar
        sidebar = QFrame()
        sidebar.setFixedWidth(240)
        sidebar.setStyleSheet("background-color: #14161d; border-right: 1px solid #1f232d;")
        sb_layout = QVBoxLayout(sidebar)
        
        logo_label = QLabel()
        logo_path = "/usr/share/skyos/assets/logo.png"
        if os.path.exists(logo_path):
            logo_label.setPixmap(QPixmap(logo_path).scaledToWidth(140, Qt.SmoothTransformation))
        else:
            logo_label.setText("SkyOS")
            logo_label.setFont(QFont("sans-serif", 22, QFont.Bold))
        logo_label.setAlignment(Qt.AlignCenter)
        sb_layout.addWidget(logo_label)
        sb_layout.addSpacing(30)

        nav_items = ["Startseite", "Filme", "Serien", "Zuletzt gesehen", "Browser", "Desktop", "Einstellungen"]
        for idx, item in enumerate(nav_items):
            btn = QPushButton(item)
            btn.setFont(QFont("sans-serif", 12))
            btn.setStyleSheet("""
                QPushButton {
                    background: transparent; color: #a0a5b5; border: none; 
                    padding: 14px 20px; text-align: left; border-radius: 8px;
                }
                QPushButton:focus, QPushButton:hover {
                    background-color: #222734; color: #ffffff; font-weight: bold;
                }
            """)
            btn.setFocusPolicy(Qt.StrongFocus)
            sb_layout.addWidget(btn)
            if idx == 0:
                btn.setFocus()

        sb_layout.addStretch()
        layout.addWidget(sidebar)

        self.stack = QStackedWidget()
        layout.addWidget(self.stack)

        dash_view = QWidget()
        dash_layout = QVBoxLayout(dash_view)
        dash_title = QLabel("SkyOS Media Center")
        dash_title.setFont(QFont("sans-serif", 24, QFont.Bold))
        dash_layout.addWidget(dash_title)
        
        scroll = QScrollArea()
        scroll.setWidgetResizable(True)
        scroll.setStyleSheet("border: none; background: transparent;")
        grid_widget = QWidget()
        self.grid = QGridLayout(grid_widget)
        scroll.setWidget(grid_widget)
        dash_layout.addWidget(scroll)

        self.stack.addWidget(dash_view)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SkyOSMainWindow()
    window.show()
    sys.exit(app.exec())
'''
    with open("skyos/media-center/main.py", "w") as f:
        f.write(main_py)

    # 2. Plymouth Bootscreen
    with open("skyos/config/plymouth/skyos.script", "w") as f:
        f.write('''logo.image = Image("logo.png");
logo.sprite = Sprite(logo.image);
logo.sprite.SetX(Window.GetWidth() / 2 - logo.image.GetWidth() / 2);
logo.sprite.SetY(Window.GetHeight() / 2 - logo.image.GetHeight() / 2);

fun refresh_callback () {
  time = Math.Pi * 2 * (System.GetTime() % 2);
  opacity = (Math.Sin(time) + 1) / 2 * 0.4 + 0.6;
  logo.sprite.SetOpacity(opacity);
}
Plymouth.SetRefreshFunction(refresh_callback);
''')

    with open("skyos/config/plymouth/skyos.plymouth", "w") as f:
        f.write('''[Plymouth Theme]
Name=SkyOS Boot
Description=Cineastischer SkyOS Systemstart
ModuleName=script

[script]
ImageDir=/usr/share/plymouth/themes/skyos
ScriptFile=/usr/share/plymouth/themes/skyos/skyos.script
''')

    # 3. Autostart Skript
    with open("skyos/scripts/skyos-session.sh", "w") as f:
        f.write('#!/bin/bash\npicom -b 2>/dev/null || true\nwhile true; do\n    python3 /usr/share/skyos/media-center/main.py\n    sleep 1\ndone\n')

    print("✅ Dateistruktur und Media Center erfolgreich erstellt!")

if __name__ == "__main__":
    create_project_structure()
