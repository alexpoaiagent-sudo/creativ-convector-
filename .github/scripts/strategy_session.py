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
import re

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

# Расшифровка ролей FPF (таблица 3×3)
ROLE_DESCRIPTIONS = {
    "F1": {
        "name": "F1-Предприниматель-Контекст",
        "description": "Зачем нужен проект? Рынок, клиенты, проблема",
        "system": "Надсистема (Suprasystem)",
        "role": "Предприниматель"
    },
    "F2": {
        "name": "F2-Инженер-Окружение",
        "description": "С чем работает система? Интерфейсы, технологии",
        "system": "Надсистема (Suprasystem)",
        "role": "Инженер"
    },
    "F3": {
        "name": "F3-Менеджер-Взаимодействие",
        "description": "Как связана с другими? Партнёры, интеграции",
        "system": "Надсистема (Suprasystem)",
        "role": "Менеджер"
    },
    "F4": {
        "name": "F4-Предприниматель-Требования",
        "description": "Что должна делать? Ценность, функции",
        "system": "Целевая система (System-of-Interest)",
        "role": "Предприниматель"
    },
    "F5": {
        "name": "F5-Инженер-Архитектура",
        "description": "Как устроена внутри? Структура, компоненты",
        "system": "Целевая система (System-of-Interest)",
        "role": "Инженер"
    },
    "F6": {
        "name": "F6-Менеджер-Реализация",
        "description": "Как работает на практике? Процессы, операции",
        "system": "Целевая система (System-of-Interest)",
        "role": "Менеджер"
    },
    "F7": {
        "name": "F7-Предприниматель-Принципы",
        "description": "Почему именно так? Экономика, стратегия",
        "system": "Система создания (Constructor)",
        "role": "Предприниматель"
    },
    "F8": {
        "name": "F8-Инженер-Платформа",
        "description": "На чём построена? Инструменты, технологии",
        "system": "Система создания (Constructor)",
        "role": "Инженер"
    },
    "F9": {
        "name": "F9-Менеджер-Команда",
        "description": "Кто и как создаёт? Люди, методология",
        "system": "Система создания (Constructor)",
        "role": "Менеджер"
    }
}


def update_frontmatter_with_role_description(content):
    """Обновляет frontmatter, добавляя расшифровку роли"""
    # Ищем frontmatter
    frontmatter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)

    if not frontmatter_match:
        return content

    frontmatter = frontmatter_match.group(1)
    rest_content = content[frontmatter_match.end():]

    # Ищем роль в frontmatter
    role_match = re.search(r'^role:\s*(\w+)', frontmatter, re.MULTILINE)

    if not role_match:
        return content

    role_code = role_match.group(1)

    # Если роль есть в справочнике, добавляем описание
    if role_code in ROLE_DESCRIPTIONS:
        role_info = ROLE_DESCRIPTIONS[role_code]

        # Проверяем, нет ли уже расширенной информации
        if "role_full" not in frontmatter:
            # Заменяем простую роль на расширенную
            new_frontmatter = re.sub(
                r'^role:\s*\w+',
                f'role: {role_code}\nrole_full: {role_info["name"]}\nrole_description: {role_info["description"]}\nrole_system: {role_info["system"]}',
                frontmatter,
                flags=re.MULTILINE
            )

            return f'---\n{new_frontmatter}\n---\n{rest_content}'

    return content


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


def get_role_from_frontmatter(content):
    """Извлекает роль из frontmatter"""
    frontmatter_match = re.match(r'^---\n(.*?)\n---\n', content, re.DOTALL)
    if not frontmatter_match:
        return None

    frontmatter = frontmatter_match.group(1)
    role_match = re.search(r'^role:\s*(\w+)', frontmatter, re.MULTILINE)

    if role_match:
        return role_match.group(1)
    return None


# Маппинг ролей на папки FPF
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


def distribute_notes():
    """Этап 1: Распределение заметок по черновикам с структурой FPF"""
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

        # Обновляем frontmatter с расшифровкой роли
        content = update_frontmatter_with_role_description(content)

        # Определяем проект
        project = analyze_note(content)

        # Извлекаем роль из frontmatter
        role = get_role_from_frontmatter(content)

        # Если роль не определена, используем F4 по умолчанию
        if not role or role not in ROLE_FOLDERS:
            role = "F4"
            print(f"⚠️  {note_path.name} - роль не определена, используем F4")

        # Создаем путь с структурой FPF: Проект/F#-Роль/
        project_dir = DRAFTS_DIR / project
        role_dir = project_dir / ROLE_FOLDERS[role]
        role_dir.mkdir(parents=True, exist_ok=True)

        # Целевой путь для файла
        dest_path = role_dir / note_path.name

        # Если файл уже существует, добавляем timestamp
        if dest_path.exists():
            timestamp = datetime.now().strftime("%H%M%S")
            name_parts = note_path.stem, timestamp, note_path.suffix
            dest_path = role_dir / f"{name_parts[0]}_{name_parts[1]}{name_parts[2]}"

        try:
            # Записываем обновленное содержимое
            with open(dest_path, 'w', encoding='utf-8') as f:
                f.write(content)

            # Удаляем оригинальный файл
            note_path.unlink()

            print(f"✅ {note_path.name}")
            print(f"   → Проект: {project}")
            print(f"   → Роль: {role} ({ROLE_FOLDERS[role]})")
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


def update_existing_notes():
    """Обновляет существующие заметки в черновиках и приоритетных проектах, добавляя расшифровку ролей"""
    print("\n" + "="*60)
    print("🔄 ОБНОВЛЕНИЕ СУЩЕСТВУЮЩИХ ЗАМЕТОК\n")

    updated_count = 0

    # Папки для обработки
    folders_to_process = [
        (DRAFTS_DIR, "2. Черновики"),
        (BASE_DIR / "3. Приоритетные проекты", "3. Приоритетные проекты")
    ]

    for folder_path, folder_name in folders_to_process:
        if not folder_path.exists():
            continue

        print(f"\n📁 Обработка: {folder_name}\n")
        folder_updated = 0

        # Проходим по всем проектам в папке
        for project_dir in folder_path.iterdir():
            if not project_dir.is_dir():
                continue

            # Для приоритетных проектов нужно пройти по подпапкам F1-F9
            if folder_name == "3. Приоритетные проекты":
                # Проходим по папкам F1-F9
                for role_dir in project_dir.iterdir():
                    if not role_dir.is_dir():
                        continue

                    # Проходим по всем MD файлам в папке роли
                    for note_path in role_dir.glob("*.md"):
                        try:
                            # Читаем содержимое
                            with open(note_path, 'r', encoding='utf-8') as f:
                                content = f.read()

                            # Обновляем frontmatter
                            updated_content = update_frontmatter_with_role_description(content)

                            # Если содержимое изменилось, записываем обратно
                            if updated_content != content:
                                with open(note_path, 'w', encoding='utf-8') as f:
                                    f.write(updated_content)

                                folder_updated += 1
                                print(f"✅ {note_path.relative_to(BASE_DIR)}")

                        except Exception as e:
                            print(f"❌ Ошибка: {note_path.name}: {e}")
            else:
                # Для черновиков - просто проходим по MD файлам
                for note_path in project_dir.glob("*.md"):
                    try:
                        # Читаем содержимое
                        with open(note_path, 'r', encoding='utf-8') as f:
                            content = f.read()

                        # Обновляем frontmatter
                        updated_content = update_frontmatter_with_role_description(content)

                        # Если содержимое изменилось, записываем обратно
                        if updated_content != content:
                            with open(note_path, 'w', encoding='utf-8') as f:
                                f.write(updated_content)

                            folder_updated += 1
                            print(f"✅ {note_path.relative_to(BASE_DIR)}")

                    except Exception as e:
                        print(f"❌ Ошибка: {note_path.name}: {e}")

        print(f"\n   Обновлено в {folder_name}: {folder_updated}")
        updated_count += folder_updated

    print(f"\n📊 Всего обновлено заметок: {updated_count}")


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

    # Этап 3: Обновление существующих заметок
    update_existing_notes()

    print("\n" + "="*60)
    print("✅ СЕССИЯ ЗАВЕРШЕНА")
    print("="*60 + "\n")


if __name__ == "__main__":
    main()
