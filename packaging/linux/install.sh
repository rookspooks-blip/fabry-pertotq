#!/bin/sh
# Установка в меню приложений текущего пользователя (без sudo).
# Запуск:  ./install.sh      Удаление:  ./install.sh --remove
set -e
HERE="$(cd "$(dirname "$0")" && pwd)"
BIN="$HOME/.local/bin"
APPS="$HOME/.local/share/applications"
ICONS="$HOME/.local/share/icons/hicolor/256x256/apps"
if [ "$1" = "--remove" ]; then
    rm -f "$BIN/FabryPerot" "$APPS/fabry-perot.desktop" "$ICONS/fabry-perot.png"
    echo "Удалено."
    exit 0
fi
mkdir -p "$BIN" "$APPS" "$ICONS"
cp "$HERE/FabryPerot" "$BIN/FabryPerot"
chmod +x "$BIN/FabryPerot"
cp "$HERE/fabry-perot.png" "$ICONS/fabry-perot.png"
sed "s|^Exec=.*|Exec=$BIN/FabryPerot|" "$HERE/fabry-perot.desktop" > "$APPS/fabry-perot.desktop"
update-desktop-database "$APPS" 2>/dev/null || true
echo "Готово: «Интерферометр Фабри — Перо» появился в меню приложений."
echo "Запуск из терминала: $BIN/FabryPerot"
