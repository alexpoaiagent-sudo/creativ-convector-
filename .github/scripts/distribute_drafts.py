#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для распределения черновиков по приоритетным проектам
Читает заметки из "2. Черновики/" и перемещает в "3. Приоритетные проекты/" по ролям F1-F9
"""

import os
import shutil
from datetime import datetime
from pathlib import Path
import re

# Пути
BASE_DIR = Path(__file__).parent.parent.parent
DRAFTS_DIR = BASE_DIR / "2. Черновики"
PRIORITY_DIR = BASE_DIR / "3. Приоритетные проекты"

# Маппинг ролей на папки
ROLE_FOLDERS = {
    "F1": "F1-Предприниматель-Контекст",
    "F2": "F2-Инженер-Окружение",
    "F3": "F3-Менеджер-Взаимодействие",
    "F4": "F4-Предприниматель-Требования",
    "F5": "F5-Инженер-Архитектура",
    "F6": "F6-Менеджер-Реализация",
    "F7": "F7-Предприниматель-Принципы",
    "F8": "F8-Инженер-Платформа",
    "F9": "F9-Менеджер-Команда"
}


def parse_frontmatter(content):
    """Извлекает frontmatter из заметки"""
    frontmatter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)

    if not frontmatter_match:
        return None

    frontmatter = frontmatter_match.group(1)

    # Извлекаем project и role
    project_match = re.search(r'^project:\s*(.+)$', frontmatter, re.MULTILINE)
    role_match = re.search(r'^role:\s*(\w+)', frontmatter, re.MULTILINE)

    result = {}
    if project_match:
        result['project'] = project_match.group(1).strip()
    if role_match:
        result['role'] = role_match.group(1).strip()

    return result if result else None


def distribute_drafts():
    """Распределяет черновики по приоритетным проектам"""
    print("\n" + "="*60)
    print("🎯 РАСПРЕДЕЛЕНИЕ ЧЕРНОВИКОВ ПО ПРИОРИТЕТНЫМ ПРОЕКТАМ")
    print("="*60 + "\n")

    moved_count = 0
    skipped_count = 0
    error_count = 0

    # Статистика по проектам
    stats = {}

    # Проходим по всем проектам в черновиках
    for project_dir in DRAFTS_DIR.iterdir():
        if not project_dir.is_dir():
            continue

        project_name = project_dir.name
        print(f"\n📁 Проект: {project_name}\n")

        # Проходим по всем MD файлам в проекте
        for note_path in project_dir.glob("*.md"):
            try:
                # Читаем содержимое
                with open(note_path, 'r', encoding='utf-8') as f:
                    content = f.read()

                # Парсим frontmatter
                metadata = parse_frontmatter(content)

                if not metadata:
                    print(f"⚠️  {note_path.name} - нет frontmatter")
                    skipped_count += 1
                    continue

                if 'role' not in metadata:
                    print(f"⚠️  {note_path.name} - нет роли")
                    skipped_count += 1
                    continue

                role = metadata['role']

                # Проверяем, что роль валидна
                if role not in ROLE_FOLDERS:
                    print(f"⚠️  {note_path.name} - неизвестная роль: {role}")
                    skipped_count += 1
                    continue

                # Определяем целевую папку
                # Используем project из frontmatter, если есть, иначе из имени папки
                target_project = metadata.get('project', project_name)

                # Создаем путь к целевой папке
                target_project_dir = PRIORITY_DIR / target_project
                target_role_dir = target_project_dir / ROLE_FOLDERS[role]

                # Создаем папки если не существуют
                target_role_dir.mkdir(parents=True, exist_ok=True)

                # Целевой путь для файла
                dest_path = target_role_dir / note_path.name

                # Если файл уже существует, добавляем timestamp
                if dest_path.exists():
                    timestamp = datetime.now().strftime("%H%M%S")
                    name_parts = note_path.stem, timestamp, note_path.suffix
                    dest_path = target_role_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"

                # Перемещаем файл
                shutil.move(str(note_path), str(dest_path))

                print(f"✅ {note_path.name}")
                print(f"   → {role} ({ROLE_FOLDERS[role]})")
                print(f"   → {dest_path.relative_to(BASE_DIR)}\n")

                moved_count += 1

                # Обновляем статистику
                if target_project not in stats:
                    stats[target_project] = {}
                if role not in stats[target_project]:
                    stats[target_project][role] = 0
                stats[target_project][role] += 1

            except Exception as e:
                print(f"❌ Ошибка: {note_path.name}: {e}\n")
                error_count += 1

    # Итоговая статистика
    print("\n" + "="*60)
    print("📊 ИТОГОВАЯ СТАТИСТИКА\n")

    if stats:
        for project, roles in sorted(stats.items()):
            print(f"\n📁 {project}:")
            for role, count in sorted(roles.items()):
                print(f"   {role} ({ROLE_FOLDERS[role]}): {count} заметок")

    print(f"\n✅ Перемещено: {moved_count}")
    print(f"⚠️  Пропущено: {skipped_count}")
    print(f"❌ Ошибок: {error_count}")

    print("\n" + "="*60)
    print("✅ РАСПРЕДЕЛЕНИЕ ЗАВЕРШЕНО")
    print("="*60 + "\n")


def main():
    """Главная функция"""
    distribute_drafts()


if __name__ == "__main__":
    main()
