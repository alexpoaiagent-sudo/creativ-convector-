#!/bin/bash
# Синхронизация заметок Obsidian → GitHub creativ-convector
# Запускается через launchd каждые 15 минут

NOCLOUD="$HOME/Documents/creativ-convector.nocloud"
GITHUB="$HOME/Github/creativ-convector"
LOG="$HOME/Library/Logs/sync_obsidian.log"

echo "[$(date '+%Y-%m-%d %H:%M:%S')] Запуск синхронизации" >> "$LOG"

# Папки для синхронизации
FOLDERS=(
    "1. Исчезающие заметки"
    "2. Черновики"
    "3. Приоритетные проекты"
)

CHANGED=0

for FOLDER in "${FOLDERS[@]}"; do
    SRC="$NOCLOUD/$FOLDER"
    DST="$GITHUB/$FOLDER"

    if [ ! -d "$SRC" ]; then
        continue
    fi

    mkdir -p "$DST"

    # Копируем только новые или изменённые .md файлы
    while IFS= read -r -d '' FILE; do
        RELATIVE="${FILE#$SRC/}"
        DEST_FILE="$DST/$RELATIVE"

        mkdir -p "$(dirname "$DEST_FILE")"

        if [ ! -f "$DEST_FILE" ] || [ "$FILE" -nt "$DEST_FILE" ]; then
            cp "$FILE" "$DEST_FILE"
            echo "[$(date '+%Y-%m-%d %H:%M:%S')] Скопирован: $FOLDER/$RELATIVE" >> "$LOG"
            CHANGED=1
        fi
    done < <(find "$SRC" -name "*.md" -print0)
done

# Если есть изменения — коммитим и пушим
if [ "$CHANGED" -eq 1 ]; then
    cd "$GITHUB" || exit 1
    git add "1. Исчезающие заметки/" "2. Черновики/" "3. Приоритетные проекты/" 2>/dev/null
    git commit -m "sync: обновлены заметки из Obsidian [$(date '+%Y-%m-%d %H:%M')]" >> "$LOG" 2>&1
    git push origin main >> "$LOG" 2>&1
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Запушено в GitHub" >> "$LOG"
else
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] Изменений нет" >> "$LOG"
fi
