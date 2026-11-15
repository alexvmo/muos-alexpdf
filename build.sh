#!/usr/bin/env bash
set -e

PY_VER="${1:-3.11}"
BUILD_DIR="build"
APP_NAME="AlexPDF"
OUT_FILE="${APP_NAME}.muxapp"

echo "=== Сборка ${OUT_FILE} для Python ${PY_VER} (aarch64) ==="

rm -rf "$BUILD_DIR" "$OUT_FILE"
mkdir -p "$BUILD_DIR/$APP_NAME/site-packages" "$BUILD_DIR/$APP_NAME/glyph"

cp main.py mux_launch.sh "$BUILD_DIR/$APP_NAME/"
if [ -f "glyph/alexpdf.png" ]; then
    cp glyph/alexpdf.png "$BUILD_DIR/$APP_NAME/glyph/"
fi

# Приводим окончания строк к LF и выдаём права на выполнение
sed -i 's/\r$//' "$BUILD_DIR/$APP_NAME/mux_launch.sh" "$BUILD_DIR/$APP_NAME/main.py"
chmod +x "$BUILD_DIR/$APP_NAME/mux_launch.sh"

echo "=== Загрузка ARM64 библиотек (pygame, PyMuPDF) ==="
python3 -m pip install \
    --platform manylinux2014_aarch64 \
    --target "./$BUILD_DIR/$APP_NAME/site-packages" \
    --python-version "$PY_VER" \
    --only-binary=:all: \
    pygame PyMuPDF

echo "=== Упаковка в ${OUT_FILE} ==="
(cd "$BUILD_DIR" && zip -r "../$OUT_FILE" "$APP_NAME/")

echo "=== Готово! Файл ${OUT_FILE} успешно создан. ==="
