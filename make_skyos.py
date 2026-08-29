#!/usr/bin/env python3
import os
import sys
import subprocess

def run_build():
    print("==================================================")
    print("🚀 SkyOS 1.0 - Full Automated Build & Core System")
    print("==================================================")

    # 1. Verzeichnisse anlegen
    dirs = [
        "skyos/assets",
        "skyos/config/plymouth",
        "skyos/media-center",
        "skyos/scripts",
        "skyos/output"
    ]
    for d in dirs:
        os.makedirs(d, exist_ok=True)

    # 2. Main Media Center Application
    main_py = '''import sys
import os
import sqlite3
import urllib.request
import json
import mpv
from PySide6.QtCore import Qt
from PySide6.QtWidgets import (QApplication, QMainWindow, QWidget, QVBoxLayout, 
                             QHBoxLayout, QLabel, QPushButton, QStackedWidget, 
                             QGridLayout, QScrollArea, QFrame)
from PySide6.QtGui import QPixmap, QKeyEvent, QFont

DB_PATH = os.path.expanduser("~/.config/skyos/media.db")

def init_db():
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()
    c.execute(\'\'\'CREATE TABLE IF NOT EXISTS media 
                 (id INTEGER PRIMARY KEY, title TEXT, path TEXT, type TEXT, 
                  year TEXT, overview TEXT, poster_path TEXT, backdrop_path TEXT, 
                  progress INTEGER DEFAULT 0)\'\'\')
    conn.commit()
    conn.close()

class VideoPlayerWindow(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setAttribute(Qt.WA_NativeWindow, True)
        self.layout = QVBoxLayout(self)
        self.layout.setContentsMargins(0, 0, 0, 0)
        self.player = mpv.MPV(wid=str(int(self.winId())), vo=\'gpu\', hwdec=\'auto\')
        
    def play_file(self, filepath):
        self.player.play(filepath)

class SkyOSMainWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("SkyOS Media Center")
        self.setWindowState(Qt.WindowFullScreen)
        init_db()
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

    def keyPressEvent(self, event: QKeyEvent):
        if event.key() == Qt.Key_Escape:
            if hasattr(self, 'player_win') and self.player_win.isVisible():
                self.player_win.player.stop()
                self.player_win.close()
        super().keyPressEvent(event)

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SkyOSMainWindow()
    window.show()
    sys.exit(app.exec())
'''
    with open("skyos/media-center/main.py", "w") as f:
        f.write(main_py)

    # 3. Bootscreen (Plymouth)
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

    # 4. Openbox & Picom
    with open("skyos/config/picom.conf", "w") as f:
        f.write('backend = "glx"; vsync = true; fading = true; corner-radius = 10; shadow = true;\n')

    with open("skyos/config/openbox-rc.xml", "w") as f:
        f.write('<?xml version="1.0"?><openbox_config xmlns="http://openbox.org/3.4/rc"><applications><application class="*"><decor>no</decor><maximized>yes</maximized></application></applications></openbox_config>\n')

    # 5. Session & Installer Skripte
    with open("skyos/scripts/skyos-session.sh", "w") as f:
        f.write('#!/bin/bash\npicom --config /etc/skyos/picom.conf -b\nwhile true; do\n    python3 /usr/share/skyos/media-center/main.py\n    openbox-session\ndone\n')

    with open("skyos/scripts/install-skyos.sh", "w") as f:
        f.write('#!/bin/bash\nset -e\necho "=== SkyOS Installer ==="\nlsblk\nread -p "Ziel-Laufwerk (z.B. /dev/sda): " T\nparted -s "$T" mklabel gpt\nparted -s "$T" mkpart ESP fat32 1MiB 512MiB\nparted -s "$T" set 1 esp on\nparted -s "$T" mkpart primary ext4 512MiB 100%\nmkfs.vfat -F32 "${T}1"\nmkfs.ext4 -F "${T}2"\nM="/mnt/skyos_target"\nmkdir -p "$M"\nmount "${T}2" "$M"\nmkdir -p "$M/boot/efi"\nmount "${T}1" "$M/boot/efi"\ncp -ax / "$M"\ngrub-install --target=x86_64-efi --efi-directory="$M/boot/efi" --bootloader-id=SkyOS --root-directory="$M"\nchroot "$M" update-grub\necho "SkyOS wurde erfolgreich installiert!"\n')

    # 6. Build Master Script
    build_sh = '''#!/bin/bash
set -e

if [ "$EUID" -ne 0 ]; then
  echo "Bitte starte das Skript mit sudo!"
  exit 1
fi

BUILD_DIR="$(pwd)/build_env"
OUTPUT_DIR="$(pwd)/output"
ISO_NAME="SkyOS-1.0-amd64.iso"

echo "=== 1/5: Vorbereitung & Werkzeuge ==="
apt-get update
apt-get install -y debootstrap xorriso isolinux mtools grub-pc-bin grub-efi-amd64-bin squashfs-tools

echo "=== 2/5: Erstelle Linux-Unterbau (Debian 12) ==="
mkdir -p "$BUILD_DIR/chroot"
debootstrap --arch=amd64 --variant=minbase bookworm "$BUILD_DIR/chroot" http://deb.debian.org/debian/

mount --bind /dev "$BUILD_DIR/chroot/dev"
mount --bind /proc "$BUILD_DIR/chroot/proc"
mount --bind /sys "$BUILD_DIR/chroot/sys"

cat << 'EOF' > "$BUILD_DIR/chroot/setup.sh"
#!/bin/bash
export DEBIAN_FRONTEND=noninteractive
apt-get update
apt-get install -y --no-install-recommends \
    linux-image-amd64 grub-efi-amd64-signed grub-pc-bin \
    xserver-xorg-core xserver-xorg-video-all xinit openbox picom \
    python3-pyside6 libmpv-dev python3-mpv sqlite3 \
    cifs-utils nfs-common network-manager bluetooth bluez \
    firefox-esr pcmanfm lxterminal plymouth plymouth-themes \
    xdotool parted sudo

useradd -m -s /bin/bash skyos
echo "skyos:skyos" | chpasswd
usermod -aG sudo,video,audio,input skyos
mkdir -p /home/skyos/.config/openbox /etc/skyos /usr/share/skyos/assets
EOF

chmod +x "$BUILD_DIR/chroot/setup.sh"
chroot "$BUILD_DIR/chroot" /setup.sh
rm "$BUILD_DIR/chroot/setup.sh"

echo "=== 3/5: Integration von SkyOS ==="
cp assets/logo.png "$BUILD_DIR/chroot/usr/share/skyos/assets/" 2>/dev/null || true
cp media-center/* "$BUILD_DIR/chroot/usr/share/skyos/media-center/"
cp config/picom.conf "$BUILD_DIR/chroot/etc/skyos/"
cp config/openbox-rc.xml "$BUILD_DIR/chroot/home/skyos/.config/openbox/rc.xml"
cp scripts/install-skyos.sh "$BUILD_DIR/chroot/usr/local/bin/skyos-install"
cp scripts/skyos-session.sh "$BUILD_DIR/chroot/usr/local/bin/skyos-session"

chmod +x "$BUILD_DIR/chroot/usr/local/bin/skyos-install"
chmod +x "$BUILD_DIR/chroot/usr/local/bin/skyos-session"

mkdir -p "$BUILD_DIR/chroot/usr/share/plymouth/themes/skyos"
cp assets/logo.png "$BUILD_DIR/chroot/usr/share/plymouth/themes/skyos/" 2>/dev/null || true
cp config/plymouth/skyos.script "$BUILD_DIR/chroot/usr/share/plymouth/themes/skyos/"
cp config/plymouth/skyos.plymouth "$BUILD_DIR/chroot/usr/share/plymouth/themes/skyos/"

chroot "$BUILD_DIR/chroot" plymouth-set-default-theme skyos

mkdir -p "$BUILD_DIR/chroot/etc/systemd/system/getty@tty1.service.d"
cat << 'EOF' > "$BUILD_DIR/chroot/etc/systemd/system/getty@tty1.service.d/override.conf"
[Service]
ExecStart=
ExecStart=-/sbin/agetty --autologin skyos --noclear %I $TERM
EOF

cat << 'EOF' > "$BUILD_DIR/chroot/home/skyos/.bash_profile"
if [ -z "$DISPLAY" ] && [ "$(tty)" = "/dev/tty1" ]; then
  exec startx /usr/local/bin/skyos-session
fi
EOF

chroot "$BUILD_DIR/chroot" chown -R skyos:skyos /home/skyos

umount "$BUILD_DIR/chroot/dev"
umount "$BUILD_DIR/chroot/proc"
umount "$BUILD_DIR/chroot/sys"

echo "=== 4/5: Generiere Bootstruktur ==="
mkdir -p "$BUILD_DIR/iso/live" "$OUTPUT_DIR"
mksquashfs "$BUILD_DIR/chroot" "$BUILD_DIR/iso/live/filesystem.squashfs" -e boot

cp "$BUILD_DIR/chroot/boot/vmlinuz-"* "$BUILD_DIR/iso/live/vmlinuz"
cp "$BUILD_DIR/chroot/boot/initrd.img-"* "$BUILD_DIR/iso/live/initrd.img"

mkdir -p "$BUILD_DIR/iso/boot/grub"
cat << 'EOF' > "$BUILD_DIR/iso/boot/grub/grub.cfg"
set default=0
set timeout=3

menuentry "SkyOS 1.0 Live" {
    linux /live/vmlinuz boot=live quiet splash loglevel=0 dynamic
    initrd /live/initrd.img
}

menuentry "SkyOS 1.0 Installieren" {
    linux /live/vmlinuz boot=live quiet splash script=skyos-install
    initrd /live/initrd.img
}
EOF

echo "=== 5/5: Erstelle Hybrid-ISO Datei ==="
grub-mkrescue -o "$OUTPUT_DIR/$ISO_NAME" "$BUILD_DIR/iso"

echo "================================================="
echo "🎉 ERFOLG: SkyOS ISO ist fertig gebaut!"
echo "Pfad: $OUTPUT_DIR/$ISO_NAME"
echo "================================================="
'''
    with open("skyos/build-skyos.sh", "w") as f:
        f.write(build_sh)

    print("📁 Projektstruktur generiert. Starte automatischen ISO-Build...")

    # 7. Automatischer Start des Build-Skripts
    os.chdir("skyos")
    os.chmod("scripts/install-skyos.sh", 0o755)
    os.chmod("scripts/skyos-session.sh", 0o755)
    os.chmod("build-skyos.sh", 0o755)
    
    subprocess.run(["sudo", "./build-skyos.sh"], check=True)

if __name__ == "__main__":
    run_build()
