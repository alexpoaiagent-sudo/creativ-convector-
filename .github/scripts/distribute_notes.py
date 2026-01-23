#!/usr/bin/env python3
"""
Распределение заметок из "Исчезающих" по черновикам проектов
Использует Claude API для анализа и категоризации заметок
"""

import os
import sys
import json
from pathlib import Path
from datetime import datetime
import anthropic

# Конфигурация проектов
PROJECTS = {
    "VK-Coffee": {
        "keywords": ["кофе", "бариста", "кофейня", "эспрессо", "латте", "капучино", "вк", "кофемаркет"],
        "description": "Развитие сети кофеен"
    },
    "Marathon-v2": {
        "keywords": ["марафон", "адаптация", "обучение", "онбординг", "сотрудник", "программа"],
        "description": "Программа адаптации сотрудников"
    },
    "Creative-Convector": {
        "keywords": ["заметки", "obsidian", "система", "конвейер", "структура", "fpf"],
        "description": "Система управления заметками"
    }
}

# Роли FPF (таблица 3×3)
FPF_ROLES = {
    "F1": "Контекст и рынок (Предприниматель + Надсистема)",
    "F2": "Окружение и интерфейсы (Инженер + Надсистема)",
    "F3": "Взаимодействие и партнёрства (Менеджер + Надсистема)",
    "F4": "Требования и ценность (Предприниматель + Целевая система)",
    "F5": "Архитектура продукта (Инженер + Целевая система)",
    "F6": "Реализация и процессы (Менеджер + Целевая система)",
    "F7": "Принципы и экономика (Предприниматель + Система создания)",
    "F8": "Платформа и инструменты (Инженер + Система создания)",
    "F9": "Команда и методология (Менеджер + Система создания)"
}

def get_notes_from_inbox():
    """Получить все заметки из папки Исчезающие заметки"""
    inbox_path = Path("1. Исчезающие заметки")

    if not inbox_path.exists():
        print("❌ Папка '1. Исчезающие заметки' не найдена")
        return []

    notes = []
    for file in inbox_path.glob("*.md"):
        if file.name == "README.md":
            continue

        try:
            content = file.read_text(encoding='utf-8')
            notes.append({
                "path": file,
                "name": file.name,
                "content": content
            })
        except Exception as e:
            print(f"⚠️  Ошибка чтения {file.name}: {e}")

    return notes

def analyze_note_with_claude(note):
    """Анализ заметки с помощью Claude API"""
    api_key = os.environ.get('ANTHROPIC_API_KEY')
    if not api_key:
        print("❌ ANTHROPIC_API_KEY не установлен")
        return None

    client = anthropic.Anthropic(api_key=api_key)

    projects_info = "\n".join([
        f"- {name}: {info['description']} (ключевые слова: {', '.join(info['keywords'])})"
        for name, info in PROJECTS.items()
    ])

    roles_info = "\n".join([f"- {role}: {desc}" for role, desc in FPF_ROLES.items()])

    prompt = f"""Проанализируй заметку и определи:
1. К какому проекту она относится
2. Какую роль FPF она выполняет (F1-F9)

Доступные проекты:
{projects_info}

Роли FPF (таблица 3×3):
{roles_info}

Заметка:
---
{note['content'][:1000]}
---

Верни ответ в формате JSON:
{{
  "project": "название проекта",
  "role": "F1-F9",
  "confidence": 0.0-1.0,
  "reasoning": "краткое объяснение"
}}
"""

    try:
        message = client.messages.create(
            model="claude-sonnet-4-20250514",
            max_tokens=1024,
            messages=[{
                "role": "user",
                "content": prompt
            }]
        )

        response_text = message.content[0].text

        # Извлечь JSON из ответа
        if "```json" in response_text:
            response_text = response_text.split("```json")[1].split("```")[0]
        elif "```" in response_text:
            response_text = response_text.split("```")[1].split("```")[0]

        result = json.loads(response_text.strip())
        return result

    except Exception as e:
        print(f"❌ Ошибка анализа: {e}")
        return None

def create_draft(note, project, role, reasoning):
    """Создать черновик в папке проекта"""
    draft_path = Path(f"2. Черновики/{project}")
    draft_path.mkdir(parents=True, exist_ok=True)

    # Создать frontmatter
    today = datetime.now().strftime("%Y-%m-%d")

    frontmatter = f"""---
role: {role}
project: {project}
status: черновик
created: {today}
updated: {today}
---

# {note['name'].replace('.md', '')}

## Исходная заметка

{note['content']}

## Анализ AI

**Проект:** {project}
**Роль:** {role} - {FPF_ROLES[role]}
**Обоснование:** {reasoning}

## Рекомендации

- Доработать содержание
- Добавить связи с другими заметками
- Переместить в соответствующую папку проекта после доработки

---

*Создано AI агентом: {today}*
"""

    draft_file = draft_path / note['name']
    draft_file.write_text(frontmatter, encoding='utf-8')

    return draft_file

def main():
    print("=" * 60)
    print("🤖 Распределение заметок по черновикам")
    print("=" * 60)

    # Получить заметки
    notes = get_notes_from_inbox()
    print(f"\n📝 Найдено заметок: {len(notes)}")

    if not notes:
        print("ℹ️  Нет заметок для обработки")
        return

    processed = 0

    for note in notes:
        print(f"\n📄 Обработка: {note['name']}")

        # Анализ с Claude
        analysis = analyze_note_with_claude(note)

        if not analysis:
            print(f"⏭️  Пропуск: не удалось проанализировать")
            continue

        project = analysis.get('project')
        role = analysis.get('role')
        confidence = analysis.get('confidence', 0)
        reasoning = analysis.get('reasoning', '')

        if project not in PROJECTS:
            print(f"⚠️  Неизвестный проект: {project}")
            continue

        if role not in FPF_ROLES:
            print(f"⚠️  Неизвестная роль: {role}")
            continue

        print(f"   → Проект: {project}")
        print(f"   → Роль: {role}")
        print(f"   → Уверенность: {confidence:.0%}")

        # Создать черновик
        draft_file = create_draft(note, project, role, reasoning)
        print(f"   ✅ Создан черновик: {draft_file}")

        # Удалить исходную заметку
        note['path'].unlink()
        print(f"   🗑️  Удалена исходная заметка")

        processed += 1

    print("\n" + "=" * 60)
    print(f"✨ Обработано заметок: {processed}/{len(notes)}")
    print("=" * 60)

if __name__ == "__main__":
    main()
