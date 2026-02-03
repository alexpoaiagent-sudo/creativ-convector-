#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Скрипт для проведения сессии стратегирования
Этап 1: Распределение заметок по черновикам
Этап 2: Создание консолидированного MD файла
"""

import os
import shutil
from datetime import datetime
from pathlib import Path

# Пути
BASE_DIR = Path(__file__).parent.parent.parent
INCOMING_DIR = BASE_DIR / "1. Исчезающие заметки"
DRAFTS_DIR = BASE_DIR / "2. Черновики"
SESSIONS_DIR = BASE_DIR / "System" / "Сессии стратегирования"

# Проекты и их ключевые слова
PROJECTS = {
    "VK-Coffee": ["кофе", "кофейня", "бариста", "эспрессо", "латте", "капучино", "вк", "vk", "coffee"],
    "Marathon-v2": ["марафон", "marathon", "адаптация", "сотрудник", "онбординг"],
    "Creative-Convector": ["конвейер", "convector", "заметки", "obsidian", "система"],
    "Teamlogs - «транскрибатор встреч»": ["teamlogs", "транскрибатор", "встреча", "запись"],
    "Космическая одисея 2001": ["космос", "одиссея", "2001"],
    "Разное": []  # Дефолтный проект для неопределенных заметок
}


def analyze_note(content):
    """Определяет проект по содержимому заметки"""
    content_lower = content.lower()

    # Подсчитываем совпадения для каждого проекта
    matches = {}
    for project, keywords in PROJECTS.items():
        if project == "Разное":
            continue
        count = sum(1 for keyword in keywords if keyword in content_lower)
        if count > 0:
            matches[project] = count

    # Возвращаем проект с максимальным количеством совпадений
    if matches:
        return max(matches, key=matches.get)
    return "Разное"


def distribute_notes():
    """Этап 1: Распределение заметок по черновикам"""
    print("🚀 ЭТАП 1: Распределение заметок по черновикам\n")

    processed_notes = []

    # Получаем все MD файлы из входящих
    notes = list(INCOMING_DIR.glob("*.md"))

    if not notes:
        print("📭 Нет заметок для обработки")
        return processed_notes

    print(f"📝 Найдено заметок: {len(notes)}\n")

    for note_path in notes:
        # Пропускаем .gitkeep и служебные файлы
        if note_path.name.startswith('.'):
            continue

        # Читаем содержимое
        try:
            with open(note_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except Exception as e:
            print(f"❌ Ошибка чтения {note_path.name}: {e}")
            continue

        # Определяем проект
        project = analyze_note(content)

        # Создаем папку проекта если не существует
        project_dir = DRAFTS_DIR / project
        project_dir.mkdir(parents=True, exist_ok=True)

        # Перемещаем файл
        dest_path = project_dir / note_path.name

        # Если файл уже существует, добавляем timestamp
        if dest_path.exists():
            timestamp = datetime.now().strftime("%H%M%S")
            name_parts = note_path.stem, timestamp, note_path.suffix
            dest_path = project_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"

        try:
            shutil.move(str(note_path), str(dest_path))
            print(f"✅ {note_path.name}")
            print(f"   → Проект: {project}")
            print(f"   → Путь: {dest_path.relative_to(BASE_DIR)}\n")

            # Сохраняем информацию для консолидации
            processed_notes.append({
                'filename': note_path.name,
                'project': project,
                'content': content,
                'dest_path': dest_path
            })
        except Exception as e:
            print(f"❌ Ошибка перемещения {note_path.name}: {e}\n")

    return processed_notes


def create_consolidated_file(processed_notes):
    """Этап 2: Создание консолидированного MD файла"""
    print("\n" + "="*60)
    print("🚀 ЭТАП 2: Создание консолидированного файла\n")

    if not processed_notes:
        print("📭 Нет заметок для консолидации")
        return

    # Создаем имя файла с датой
    session_date = datetime.now().strftime("%Y-%m-%d_%H-%M")
    session_file = SESSIONS_DIR / f"Сессия стратегирования {session_date}.md"

    # Формируем содержимое
    content_parts = []

    # Заголовок
    content_parts.append(f"# Сессия стратегирования {datetime.now().strftime('%d.%m.%Y %H:%M')}\n")
    content_parts.append(f"\n**Обработано заметок:** {len(processed_notes)}\n")

    # Группируем по проектам
    by_project = {}
    for note in processed_notes:
        project = note['project']
        if project not in by_project:
            by_project[project] = []
        by_project[project].append(note)

    # Статистика по проектам
    content_parts.append("\n## 📊 Статистика по проектам\n")
    for project, notes in sorted(by_project.items()):
        content_parts.append(f"- **{project}**: {len(notes)} заметок\n")

    content_parts.append("\n---\n")

    # Содержимое заметок по проектам
    for project, notes in sorted(by_project.items()):
        content_parts.append(f"\n## 📁 {project}\n")

        for note in notes:
            content_parts.append(f"\n### 📝 {note['filename']}\n")
            content_parts.append(f"\n{note['content']}\n")
            content_parts.append("\n---\n")

    # Записываем файл
    try:
        with open(session_file, 'w', encoding='utf-8') as f:
            f.write(''.join(content_parts))

        print(f"✅ Создан файл: {session_file.relative_to(BASE_DIR)}")
        print(f"📄 Размер: {session_file.stat().st_size} байт")
        print(f"📊 Проектов: {len(by_project)}")
        print(f"📝 Заметок: {len(processed_notes)}")
    except Exception as e:
        print(f"❌ Ошибка создания файла: {e}")


def main():
    """Главная функция - запуск сессии стратегирования"""
    print("\n" + "="*60)
    print("🎯 НАЧАЛО СЕССИИ СТРАТЕГИРОВАНИЯ")
    print("="*60 + "\n")

    # Этап 1: Распределение
    processed_notes = distribute_notes()

    # Этап 2: Консолидация
    if processed_notes:
        create_consolidated_file(processed_notes)

    print("\n" + "="*60)
    print("✅ СЕССИЯ ЗАВЕРШЕНА")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
