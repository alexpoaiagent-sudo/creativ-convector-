#!/usr/bin/env python3
"""
AI агент для распределения заметок - упрощенная версия на основе ключевых слов

Автоматически определяет проект по ключевым словам в содержимом заметки
"""

import os
import sys
import json
from datetime import datetime
from pathlib import Path

# Настройки
VAULT_PATH = Path(__file__).parent.parent.parent
VANISHING_NOTES = VAULT_PATH / "1. Исчезающие заметки"
DRAFTS_PATH = VAULT_PATH / "2. Черновики"
REPORTS_PATH = VAULT_PATH / "System" / "Отчёты AI"
PRIORITY_PROJECTS = VAULT_PATH / "3. Приоритетные проекты"

# Конфигурация проектов с ключевыми словами
PROJECTS = {
    "VK-Coffee": {
        "keywords": ["кофе", "бариста", "кофейня", "эспрессо", "латте", "капучино", "вк", "кофемаркет", "клиент", "заказ", "меню", "напиток"],
        "description": "Развитие кофейного маркета"
    },
    "Marathon-v2": {
        "keywords": ["марафон", "адаптация", "обучение", "онбординг", "сотрудник", "программа", "тренинг", "курс"],
        "description": "Программа адаптации сотрудников"
    },
    "Creative-Convector": {
        "keywords": ["заметки", "obsidian", "система", "конвейер", "структура", "fpf", "агент", "автоматизация", "git"],
        "description": "Система управления заметками"
    }
}

# FPF роли с ключевыми словами
FPF_ROLES = {
    "F1": {
        "name": "Контекст",
        "keywords": ["зачем", "контекст", "рынок", "проблема", "возможность", "тренд"]
    },
    "F2": {
        "name": "Окружение",
        "keywords": ["окружение", "интерфейс", "интеграция", "api", "внешний"]
    },
    "F3": {
        "name": "Взаимодействие",
        "keywords": ["взаимодействие", "партнер", "клиент", "пользователь", "коммуникация"]
    },
    "F4": {
        "name": "Требования",
        "keywords": ["требование", "функция", "фича", "нужно", "должен", "хочу", "идея"]
    },
    "F5": {
        "name": "Архитектура",
        "keywords": ["архитектура", "структура", "дизайн", "компонент", "модуль", "система"]
    },
    "F6": {
        "name": "Реализация",
        "keywords": ["реализация", "код", "разработка", "имплементация", "процесс", "workflow"]
    },
    "F7": {
        "name": "Принципы",
        "keywords": ["принцип", "экономика", "бизнес", "модель", "стратегия"]
    },
    "F8": {
        "name": "Платформа",
        "keywords": ["платформа", "инструмент", "технология", "фреймворк", "библиотека"]
    },
    "F9": {
        "name": "Команда",
        "keywords": ["команда", "люди", "роль", "методология", "процесс", "управление"]
    }
}


def analyze_by_keywords(content):
    """Анализ заметки по ключевым словам"""
    content_lower = content.lower()

    # Определить проект
    project_scores = {}
    for project_name, project_info in PROJECTS.items():
        score = sum(1 for keyword in project_info["keywords"] if keyword in content_lower)
        project_scores[project_name] = score

    # Выбрать проект с максимальным score
    best_project = max(project_scores, key=project_scores.get)
    best_score = project_scores[best_project]

    # Если score слишком низкий, создать новый проект
    if best_score < 2:
        # Попробовать извлечь название из первой строки
        first_line = content.split('\n')[0].strip('#').strip()
        if len(first_line) > 3 and len(first_line) < 50:
            best_project = first_line
            is_new = True
        else:
            best_project = "Разное"
            is_new = True
    else:
        is_new = False

    # Определить роль FPF
    role_scores = {}
    for role_code, role_info in FPF_ROLES.items():
        score = sum(1 for keyword in role_info["keywords"] if keyword in content_lower)
        role_scores[role_code] = score

    best_role = max(role_scores, key=role_scores.get)

    # Если нет явных ключевых слов, использовать F4 (Требования) по умолчанию
    if role_scores[best_role] == 0:
        best_role = "F4"

    # Извлечь первые 100 символов как описание
    description = content[:100].replace('\n', ' ').strip()
    if len(content) > 100:
        description += "..."

    # Извлечь теги из содержимого (слова, которые встречаются часто)
    words = content_lower.split()
    word_freq = {}
    for word in words:
        if len(word) > 3 and word.isalpha():
            word_freq[word] = word_freq.get(word, 0) + 1

    # Топ-3 слова как теги
    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:3]
    tags = [word for word, freq in top_words]

    return {
        "project": best_project,
        "role": best_role,
        "description": description,
        "tags": tags,
        "is_new_project": is_new,
        "confidence": best_score
    }


def create_frontmatter(analysis, filename):
    """Создать frontmatter для заметки"""
    now = datetime.now().strftime("%Y-%m-%d")

    frontmatter = f"""---
project: {analysis['project']}
role: {analysis['role']}
status: черновик
created: {now}
updated: {now}
tags: {json.dumps(analysis['tags'], ensure_ascii=False)}
description: {analysis['description']}
original_file: {filename}
---

"""
    return frontmatter


def ensure_project_structure(project_name):
    """Создать структуру папок для нового проекта"""
    # Создать папку в черновиках
    drafts_project = DRAFTS_PATH / project_name
    drafts_project.mkdir(exist_ok=True)

    # Создать структуру FPF в приоритетных проектах
    priority_project = PRIORITY_PROJECTS / project_name
    priority_project.mkdir(exist_ok=True)

    for role_code, role_info in FPF_ROLES.items():
        role_folder = priority_project / f"{role_code}-{role_info['name']}"
        role_folder.mkdir(exist_ok=True)

    print(f"✅ Создана структура для нового проекта: {project_name}")


def process_note(note_path):
    """Обработать одну заметку"""
    filename = note_path.name

    # Пропустить README
    if filename == "README.md":
        return None

    print(f"\n📝 Обрабатываю: {filename}")

    # Прочитать содержимое
    with open(note_path, 'r', encoding='utf-8') as f:
        content = f.read()

    # Пропустить пустые заметки
    if not content.strip():
        print(f"⚠️  Пропускаю пустую заметку: {filename}")
        return None

    # Анализ по ключевым словам
    analysis = analyze_by_keywords(content)

    print(f"   Проект: {analysis['project']} (уверенность: {analysis['confidence']})")
    print(f"   Роль: {analysis['role']} - {FPF_ROLES[analysis['role']]['name']}")
    print(f"   Описание: {analysis['description']}")
    print(f"   Теги: {', '.join(analysis['tags'])}")

    # Создать структуру для нового проекта если нужно
    if analysis.get('is_new_project', False):
        ensure_project_structure(analysis['project'])

    # Создать frontmatter
    frontmatter = create_frontmatter(analysis, filename)

    # Новое содержимое
    new_content = frontmatter + content

    # Путь к новому файлу в черновиках
    draft_folder = DRAFTS_PATH / analysis['project']
    draft_folder.mkdir(exist_ok=True)
    draft_path = draft_folder / filename

    # Сохранить в черновики
    with open(draft_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    # Удалить из исчезающих заметок
    note_path.unlink()

    print(f"✅ Перемещено в: {draft_path.relative_to(VAULT_PATH)}")

    return {
        "filename": filename,
        "project": analysis['project'],
        "role": analysis['role'],
        "description": analysis['description'],
        "tags": analysis['tags'],
        "is_new_project": analysis.get('is_new_project', False),
        "confidence": analysis['confidence']
    }


def create_report(processed_notes):
    """Создать отчет о работе"""
    REPORTS_PATH.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    report_filename = f"distribution-{now.strftime('%Y-%m-%d-%H-%M-%S')}.md"
    report_path = REPORTS_PATH / report_filename

    report = f"""# Отчет о распределении заметок

**Дата:** {now.strftime('%Y-%m-%d %H:%M:%S')}
**Обработано заметок:** {len(processed_notes)}
**Метод:** Анализ по ключевым словам

## Результаты

"""

    # Группировка по проектам
    by_project = {}
    new_projects = []

    for note in processed_notes:
        project = note['project']
        if project not in by_project:
            by_project[project] = []
        by_project[project].append(note)

        if note.get('is_new_project'):
            new_projects.append(project)

    # Новые проекты
    if new_projects:
        report += "### 🆕 Новые проекты\n\n"
        for project in set(new_projects):
            report += f"- **{project}** - создана полная структура FPF\n"
        report += "\n"

    # По проектам
    for project, notes in by_project.items():
        report += f"### 📁 {project}\n\n"
        report += f"Заметок: {len(notes)}\n\n"

        for note in notes:
            report += f"- **{note['filename']}**\n"
            report += f"  - Роль: {note['role']} - {FPF_ROLES[note['role']]['name']}\n"
            report += f"  - Уверенность: {note['confidence']}/10\n"
            report += f"  - Описание: {note['description']}\n"
            report += f"  - Теги: {', '.join(note['tags'])}\n\n"

    report += f"""
---

**Следующие шаги:**
1. Просмотрите черновики в папке `2. Черновики/`
2. Проверьте правильность распределения
3. Доработайте содержание заметок
4. Переместите готовые заметки в `3. Приоритетные проекты/`

**Статистика:**
- Всего проектов: {len(by_project)}
- Новых проектов: {len(set(new_projects))}
- Обработано заметок: {len(processed_notes)}

**Примечание:**
Распределение выполнено автоматически на основе ключевых слов.
Проверьте правильность категоризации и при необходимости переместите заметки вручную.
"""

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n📊 Отчет сохранен: {report_path.relative_to(VAULT_PATH)}")
    return report_path


def main():
    """Основная функция"""
    print("🤖 AI Агент распределения заметок (Автоматический режим)")
    print("=" * 60)
    print("Метод: Анализ по ключевым словам")
    print("=" * 60)

    # Проверить наличие заметок
    notes = list(VANISHING_NOTES.glob("*.md"))
    notes = [n for n in notes if n.name != "README.md"]

    if not notes:
        print("\n✅ Нет заметок для обработки в папке 'Исчезающие заметки'")
        return

    print(f"\n📋 Найдено заметок: {len(notes)}")

    # Обработать каждую заметку
    processed = []
    for note_path in notes:
        result = process_note(note_path)
        if result:
            processed.append(result)

    # Создать отчет
    if processed:
        create_report(processed)
        print(f"\n✅ Успешно обработано: {len(processed)} заметок")
    else:
        print("\n⚠️  Ни одна заметка не была обработана")


if __name__ == "__main__":
    main()
