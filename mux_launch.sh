#!/bin/sh
# HELP: AlexPDF — программа для чтения PDF-документов на консоли muOS
# ICON: alexpdf
# GRID: AlexPDF

. /opt/muos/script/var/func.sh
SETUP_STAGE_OVERLAY

APP_DIR="$1"
SETUP_APP "python3" "none"

export PYTHONPATH="$APP_DIR/site-packages:$PYTHONPATH"
export SDL_GAMECONTROLLERCONFIG_FILE="/usr/lib/gamecontrollerdb.txt"
export PYGAME_HIDE_SUPPORT_PROMPT=1

cd "$APP_DIR" || exit

PDF_DIR="/mnt/mmc/ROMS/PDF"
mkdir -p "$PDF_DIR"

python3 "$APP_DIR/main.py" "$PDF_DIR" > "$APP_DIR/alexpdf.log" 2>&1
exit 0
