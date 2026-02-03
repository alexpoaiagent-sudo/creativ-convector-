#!/usr/bin/env python3
"""
AI агент распределения заметок на основе методологии SRT (Systems-Roles-Table)

Источники правды:
- SRT: https://github.com/alexpoaiagent-sudo/srt-template
- FPF: Матрица 3×3 (9 семейств документов F1-F9)

Матрица SRT:
                Предприниматель    Инженер           Менеджер
                (Зачем?)          (Как устроено?)   (Как работает?)
Надсистема     F1-Контекст       F2-Окружение      F3-Взаимодействие
Целевая сист.  F4-Требования     F5-Архитектура    F6-Реализация
Конструктор    F7-Принципы       F8-Платформа      F9-Команда
"""

import os
import sys
import json
import re
from datetime import datetime
from pathlib import Path

# === НАСТРОЙКИ ===
VAULT_PATH = Path(__file__).parent.parent.parent
VANISHING_NOTES = VAULT_PATH / "1. Исчезающие заметки"
DRAFTS_PATH = VAULT_PATH / "2. Черновики"
REPORTS_PATH = VAULT_PATH / "System" / "Отчёты AI"
PROCESSED_PATH = VAULT_PATH / "System" / "Обработанные"
PRIORITY_PROJECTS = VAULT_PATH / "3. Приоритетные проекты"

# === SRT: ПРОЕКТЫ (Целевые системы) ===
# Каждый проект = целевая система в терминах SRT
# VK-Coffee — заказчик, определяет приоритетные проекты
PROJECTS = {
    "VK-Coffee": {
        "keywords": [
            "кофе", "бариста", "кофейня", "эспрессо", "латте", "капучино",
            "вк", "кофемаркет", "заказ", "меню", "напиток", "собрание",
            "смена", "кухня", "позиция", "закуп", "продажа", "цена",
            "бк", "евгений", "заявк"
        ],
        "description": "Кофейный маркет — заказчик и целевая система",
        "srt_role": "Заказчик (определяет приоритеты)"
    },
    "Marathon-v2": {
        "keywords": [
            "марафон", "адаптация", "обучение", "онбординг", "сотрудник",
            "программа", "тренинг", "курс", "бот", "лента", "задание",
            "ученик", "прогресс", "режим", "душ", "назначени"
        ],
        "description": "Программа адаптации сотрудников",
        "srt_role": "Целевая система (продукт)"
    },
    "Creative-Convector": {
        "keywords": [
            "заметки", "obsidian", "конвейер", "конвеер", "fpf", "srt",
            "агент", "автоматизация", "git", "репозитор", "стратегир",
            "черновик", "сессия", "рефакторинг", "плагин"
        ],
        "description": "Система управления знаниями (творческий конвейер)",
        "srt_role": "Конструктор (система создания)"
    }
}

# === FPF: 9 СЕМЕЙСТВ ДОКУМЕНТОВ (по SRT матрице 3×3) ===
# Каждая роль = пересечение системы и роли в матрице SRT
FPF_ROLES = {
    "F1": {
        "name": "Контекст",
        "system": "Надсистема",
        "role": "Предприниматель",
        "question": "Зачем это нужно рынку?",
        "description": "Рыночный контекст, тренды, проблемы, возможности",
        "keywords": [
            "зачем", "контекст", "рынок", "проблема", "возможность",
            "тренд", "конкурент", "спрос", "потребность", "ниша",
            "целевая аудитория", "боль клиента"
        ]
    },
    "F2": {
        "name": "Окружение",
        "system": "Надсистема",
        "role": "Инженер",
        "question": "Как интегрируется с внешним миром?",
        "description": "Интерфейсы, API, внешние системы, интеграции",
        "keywords": [
            "окружение", "интерфейс", "интеграция", "api", "внешний",
            "подключение", "синхронизация", "совместимость", "протокол",
            "webhook", "гугл", "диск"
        ]
    },
    "F3": {
        "name": "Взаимодействие",
        "system": "Надсистема",
        "role": "Менеджер",
        "question": "С кем и как взаимодействуем?",
        "description": "Партнёрства, клиенты, коммуникации, встречи",
        "keywords": [
            "взаимодействие", "партнер", "клиент", "пользователь",
            "коммуникация", "встреча", "собрание", "переговоры",
            "обратная связь", "отзыв", "поставщик"
        ]
    },
    "F4": {
        "name": "Требования",
        "system": "Целевая система",
        "role": "Предприниматель",
        "question": "Что нужно сделать?",
        "description": "Функции, фичи, пожелания, идеи, задачи",
        "keywords": [
            "требование", "функция", "фича", "нужно", "должен",
            "хочу", "идея", "задача", "сделать", "добавить",
            "улучшить", "доработать", "план"
        ]
    },
    "F5": {
        "name": "Архитектура",
        "system": "Целевая система",
        "role": "Инженер",
        "question": "Как это устроено?",
        "description": "Структура, дизайн, компоненты, схемы",
        "keywords": [
            "архитектура", "структура", "дизайн", "компонент", "модуль",
            "схема", "папка", "организация", "иерархия", "формат",
            "шаблон", "устроен"
        ]
    },
    "F6": {
        "name": "Реализация",
        "system": "Целевая система",
        "role": "Менеджер",
        "question": "Как это работает на практике?",
        "description": "Процессы, workflow, инструкции, регламенты",
        "keywords": [
            "реализация", "код", "разработка", "процесс", "workflow",
            "инструкция", "регламент", "порядок", "алгоритм", "этап",
            "шаг", "запуск", "установка", "настройка"
        ]
    },
    "F7": {
        "name": "Принципы",
        "system": "Конструктор",
        "role": "Предприниматель",
        "question": "На каких принципах строим бизнес?",
        "description": "Бизнес-модель, экономика, стратегия, принципы",
        "keywords": [
            "принцип", "экономика", "бизнес", "модель", "стратегия",
            "ценность", "миссия", "видение", "монетизация", "доход",
            "расход", "прибыль", "инвестиция"
        ]
    },
    "F8": {
        "name": "Платформа",
        "system": "Конструктор",
        "role": "Инженер",
        "question": "Какие инструменты используем?",
        "description": "Технологии, инструменты, платформы, стек",
        "keywords": [
            "платформа", "инструмент", "технология", "фреймворк",
            "библиотека", "сервис", "приложение", "программа",
            "телефон", "компьютер", "мобильн"
        ]
    },
    "F9": {
        "name": "Команда",
        "system": "Конструктор",
        "role": "Менеджер",
        "question": "Кто и как работает?",
        "description": "Команда, роли, методология, управление",
        "keywords": [
            "команда", "люди", "роль", "методология", "управление",
            "ответственность", "навык", "компетенция", "обучение",
            "наставник", "жанна", "сотрудник"
        ]
    }
}


def strip_existing_frontmatter(content):
    """Убрать существующий frontmatter если есть"""
    # Паттерн: --- ... --- в начале файла
    pattern = r'^---\s*\n.*?\n---\s*\n'
    # Убираем все frontmatter блоки в начале (могут быть множественные из-за бага)
    while content.strip().startswith('---'):
        match = re.match(pattern, content, re.DOTALL)
        if match:
            content = content[match.end():]
        else:
            break
    return content.strip()


def clean_chatgpt_artifacts(content):
    """Убрать артефакты от ChatGPT-MD плагина"""
    # Убрать <hr class="__chatgpt_plugin">
    content = re.sub(r'<hr\s+class="__chatgpt_plugin"\s*/?>', '', content)
    # Убрать role::assistant и role::user заголовки
    content = re.sub(r'###?\s*role::(assistant|user).*', '', content)
    # Убрать span с моделью
    content = re.sub(r'<span[^>]*>.*?</span>', '', content)
    # Убрать лишние пустые строки (больше 2 подряд)
    content = re.sub(r'\n{3,}', '\n\n', content)
    return content.strip()


def analyze_by_keywords(content):
    """Анализ заметки по SRT/FPF методологии"""
    content_lower = content.lower()

    # === ШАГ 1: Определить проект (целевую систему по SRT) ===
    project_scores = {}
    for project_name, project_info in PROJECTS.items():
        score = sum(1 for kw in project_info["keywords"] if kw in content_lower)
        project_scores[project_name] = score

    best_project = max(project_scores, key=project_scores.get)
    best_score = project_scores[best_project]

    if best_score < 1:
        best_project = "Разное"
        is_new = True
    else:
        is_new = False

    # === ШАГ 2: Определить роль FPF (ячейку в матрице 3×3) ===
    role_scores = {}
    for role_code, role_info in FPF_ROLES.items():
        score = sum(1 for kw in role_info["keywords"] if kw in content_lower)
        role_scores[role_code] = score

    best_role = max(role_scores, key=role_scores.get)

    # Если нет явных совпадений — определяем по контексту
    if role_scores[best_role] == 0:
        # Эвристика: если заметка короткая и начинается с идеи — F4
        best_role = "F4"

    role_info = FPF_ROLES[best_role]

    # === ШАГ 3: Извлечь описание ===
    description = content[:150].replace('\n', ' ').strip()
    if len(content) > 150:
        description += "..."

    # === ШАГ 4: Извлечь теги ===
    words = content_lower.split()
    word_freq = {}
    stop_words = {"это", "что", "как", "для", "при", "или", "все", "так", "уже",
                  "они", "она", "его", "мне", "мой", "мои", "нас", "нам", "будет",
                  "этой", "этот", "того", "тоже", "есть", "быть", "очень", "также"}
    for word in words:
        clean_word = re.sub(r'[^\w]', '', word)
        if len(clean_word) > 3 and clean_word.isalpha() and clean_word not in stop_words:
            word_freq[clean_word] = word_freq.get(clean_word, 0) + 1

    top_words = sorted(word_freq.items(), key=lambda x: x[1], reverse=True)[:5]
    tags = [word for word, freq in top_words]

    return {
        "project": best_project,
        "role": best_role,
        "role_name": role_info["name"],
        "srt_system": role_info["system"],
        "srt_role": role_info["role"],
        "srt_question": role_info["question"],
        "description": description,
        "tags": tags,
        "is_new_project": is_new,
        "confidence": best_score,
        "role_confidence": role_scores[best_role]
    }


def create_frontmatter(analysis, filename):
    """Создать frontmatter по SRT/FPF стандарту"""
    now = datetime.now().strftime("%Y-%m-%d")

    frontmatter = f"""---
project: {analysis['project']}
role: {analysis['role']}
role_name: {analysis['role_name']}
srt_system: {analysis['srt_system']}
srt_role: {analysis['srt_role']}
srt_question: "{analysis['srt_question']}"
status: черновик
created: {now}
tags: {json.dumps(analysis['tags'], ensure_ascii=False)}
original_file: {filename}
---

"""
    return frontmatter


def ensure_project_structure(project_name):
    """Создать структуру FPF папок для проекта"""
    drafts_project = DRAFTS_PATH / project_name
    drafts_project.mkdir(exist_ok=True)

    priority_project = PRIORITY_PROJECTS / project_name
    priority_project.mkdir(exist_ok=True)

    for role_code, role_info in FPF_ROLES.items():
        role_folder = priority_project / f"{role_code}-{role_info['name']}"
        role_folder.mkdir(exist_ok=True)

    print(f"  Создана структура FPF для: {project_name}")


def process_note(note_path):
    """Обработать одну заметку по SRT/FPF"""
    filename = note_path.name

    if filename == "README.md":
        return None

    print(f"\n  Обрабатываю: {filename}")

    with open(note_path, 'r', encoding='utf-8') as f:
        content = f.read()

    if not content.strip():
        print(f"  Пропускаю пустую заметку: {filename}")
        return None

    # Очистить от артефактов ChatGPT и старого frontmatter
    clean_content = strip_existing_frontmatter(content)
    clean_content = clean_chatgpt_artifacts(clean_content)

    if not clean_content.strip():
        print(f"  Пропускаю пустую заметку после очистки: {filename}")
        return None

    # Анализ по SRT/FPF
    analysis = analyze_by_keywords(clean_content)

    print(f"  Проект: {analysis['project']} (уверенность: {analysis['confidence']})")
    print(f"  Роль: {analysis['role']}-{analysis['role_name']} [{analysis['srt_system']} x {analysis['srt_role']}]")
    print(f"  Вопрос SRT: {analysis['srt_question']}")

    # Создать структуру если новый проект
    if analysis.get('is_new_project', False):
        ensure_project_structure(analysis['project'])

    # Создать frontmatter + чистый контент
    frontmatter = create_frontmatter(analysis, filename)
    new_content = frontmatter + clean_content + "\n"

    # Сохранить в черновики
    draft_folder = DRAFTS_PATH / analysis['project']
    draft_folder.mkdir(exist_ok=True)
    draft_path = draft_folder / filename

    with open(draft_path, 'w', encoding='utf-8') as f:
        f.write(new_content)

    # Сохранить оригинал в "Обработанные"
    PROCESSED_PATH.mkdir(parents=True, exist_ok=True)
    date_folder = PROCESSED_PATH / datetime.now().strftime("%Y-%m-%d")
    date_folder.mkdir(exist_ok=True)
    processed_path = date_folder / filename
    with open(processed_path, 'w', encoding='utf-8') as f:
        f.write(content)

    # Удалить из исчезающих заметок
    note_path.unlink()

    print(f"  -> {draft_path.relative_to(VAULT_PATH)}")

    return {
        "filename": filename,
        "project": analysis['project'],
        "role": analysis['role'],
        "role_name": analysis['role_name'],
        "srt_system": analysis['srt_system'],
        "srt_role": analysis['srt_role'],
        "description": analysis['description'],
        "tags": analysis['tags'],
        "is_new_project": analysis.get('is_new_project', False),
        "confidence": analysis['confidence']
    }


def create_report(processed_notes):
    """Создать отчет о распределении по SRT"""
    REPORTS_PATH.mkdir(parents=True, exist_ok=True)

    now = datetime.now()
    report_filename = f"distribution-{now.strftime('%Y-%m-%d-%H-%M-%S')}.md"
    report_path = REPORTS_PATH / report_filename

    # Группировка
    by_project = {}
    by_role = {}
    for note in processed_notes:
        proj = note['project']
        role = note['role']
        by_project.setdefault(proj, []).append(note)
        by_role.setdefault(role, []).append(note)

    # Mermaid графики
    pie_project = "```mermaid\npie title Распределение по проектам\n"
    for proj, notes in by_project.items():
        pie_project += f'    "{proj}" : {len(notes)}\n'
    pie_project += "```\n"

    pie_role = "```mermaid\npie title Распределение по ролям FPF\n"
    for role, notes in by_role.items():
        role_name = FPF_ROLES[role]['name'] if role in FPF_ROLES else role
        pie_role += f'    "{role}-{role_name}" : {len(notes)}\n'
    pie_role += "```\n"

    # Матрица заполненности 3×3
    matrix = ""
    matrix += "| | Предприниматель | Инженер | Менеджер |\n"
    matrix += "|---|---|---|---|\n"
    systems = [
        ("Надсистема", ["F1", "F2", "F3"]),
        ("Целевая система", ["F4", "F5", "F6"]),
        ("Конструктор", ["F7", "F8", "F9"]),
    ]
    for sys_name, roles in systems:
        row = f"| **{sys_name}** |"
        for r in roles:
            count = len(by_role.get(r, []))
            name = FPF_ROLES[r]['name']
            if count > 0:
                row += f" {r}: {name} ({count}) |"
            else:
                row += f" {r}: {name} (-) |"
        matrix += row + "\n"

    report = f"""# Отчет о распределении заметок (SRT/FPF)

**Дата:** {now.strftime('%Y-%m-%d %H:%M:%S')}
**Обработано:** {len(processed_notes)} заметок
**Методология:** SRT (Systems-Roles-Table) + FPF

## Распределение по проектам

{pie_project}

## Распределение по ролям FPF

{pie_role}

## Матрица заполненности SRT 3x3

{matrix}

## Детали

"""
    for proj, notes in by_project.items():
        report += f"### {proj}\n\n"
        for note in notes:
            report += f"- **{note['filename']}** -> {note['role']}-{note['role_name']} [{note['srt_system']} x {note['srt_role']}]\n"
        report += "\n"

    report += f"""---

**Оригиналы:** `System/Обработанные/{now.strftime('%Y-%m-%d')}/`
**Черновики:** `2. Черновики/[Проект]/`
"""

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"\n  Отчет: {report_path.relative_to(VAULT_PATH)}")
    return report_path


def main():
    """Главная функция — распределение по SRT/FPF"""
    print("=" * 60)
    print("AI Агент распределения заметок")
    print("Методология: SRT + FPF (матрица 3x3)")
    print("Источник: github.com/alexpoaiagent-sudo/srt-template")
    print("=" * 60)

    notes = list(VANISHING_NOTES.glob("*.md"))
    notes = [n for n in notes if n.name != "README.md"]

    if not notes:
        print("\nНет заметок для обработки")
        return

    print(f"\nНайдено: {len(notes)} заметок")

    processed = []
    for note_path in notes:
        result = process_note(note_path)
        if result:
            processed.append(result)

    if processed:
        create_report(processed)
        print(f"\nОбработано: {len(processed)} заметок")
    else:
        print("\nНи одна заметка не была обработана")


if __name__ == "__main__":
    main()
