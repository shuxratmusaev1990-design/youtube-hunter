#!/usr/bin/env bash
# YouTube Hunter — Mac / Linux o'rnatuvchi
# Ishlatish: bash install.sh
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
HH="${HUNTER_HOME:-$HOME/youtube-hunter}"
echo "===== YouTube Hunter o'rnatilyapti -> $HH ====="

# 1) Python 3.10+ va FFmpeg
need_pkg() { command -v "$1" >/dev/null 2>&1; }
install_pkgs() {
  if [[ "$OSTYPE" == darwin* ]]; then
    need_pkg brew || { echo "Homebrew yo'q: https://brew.sh dan o'rnating"; exit 1; }
    brew install "$@"
  elif need_pkg apt-get; then sudo apt-get update -y && sudo apt-get install -y "$@"
  elif need_pkg dnf; then sudo dnf install -y "$@"
  elif need_pkg pacman; then sudo pacman -S --noconfirm "$@"
  else echo "Paket menejeri topilmadi. $* ni qo'lda o'rnating."; exit 1; fi
}
if ! need_pkg python3; then
  echo "[1/5] Python o'rnatilyapti..."
  if [[ "$OSTYPE" == darwin* ]]; then install_pkgs python; else install_pkgs python3 python3-venv python3-pip; fi
else echo "[1/5] Python bor: $(python3 --version)"; fi
python3 -c 'import sys; sys.exit(0 if sys.version_info >= (3,10) else 1)' || { echo "Python 3.10+ kerak"; exit 1; }
python3 -m venv --help >/dev/null 2>&1 || install_pkgs python3-venv
if ! need_pkg ffmpeg; then echo "[2/5] FFmpeg o'rnatilyapti..."; install_pkgs ffmpeg; else echo "[2/5] FFmpeg bor."; fi

# 2) Papka va skriptlar
echo "[3/5] Skriptlar ko'chirilyapti..."
mkdir -p "$HH/scripts"
cp "$HERE"/scripts/*.py "$HERE"/scripts/requirements.txt "$HH/scripts/"
[ -f "$HH/config.json" ] || cp "$HERE/config.example.json" "$HH/config.json"
[ -f "$HH/.env" ] || cp "$HERE/.env.example" "$HH/.env"

# 3) Alohida Python muhiti (venv) va kutubxonalar
echo "[4/5] Python kutubxonalari o'rnatilyapti (bir necha daqiqa)..."
python3 -m venv "$HH/.venv"
"$HH/.venv/bin/python" -m pip install -q --upgrade pip
"$HH/.venv/bin/python" -m pip install -q -r "$HH/scripts/requirements.txt"
"$HH/.venv/bin/python" -m pip install -q -U yt-dlp

# 4) Qisqa buyruq: hunter <buyruq> ...
cp "$HERE/hunter" "$HH/hunter" && chmod +x "$HH/hunter"

echo "[5/5] Tekshiruv..."
"$HH/.venv/bin/python" -m yt_dlp --version
"$HH/.venv/bin/python" -c "import faster_whisper, googleapiclient, anthropic; print('kutubxonalar OK')"
ffmpeg -version | head -1
echo
echo "TAYYOR! Papka: $HH"
echo "Keyingi qadam: README.md -> 'YouTube'ga ulash' bo'limi (client_secret.json)."
echo "Sinov: $HH/hunter auto process VIDEO.mp4 --no-upload"
