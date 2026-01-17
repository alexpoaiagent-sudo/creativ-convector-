#!/usr/bin/env python3
"""
Объединение связанных заметок в черновики
Находит заметки по теме и объединяет их в один черновик
"""

import os
import sys
import re
from datetime import datetime
from pathlib import Path
from openai import OpenAI
from collections import defaultdict

def find_related_notes(vault_path, source_folder="2. Исчезающие"):
    """Найти все заметки и сгруппировать по темам"""

    folder_path = os.path.join(vault_path, source_folder)
    if not os.path.exists(folder_path):
        # Пробуем старую папку
        folder_path = os.path.join(vault_path, "Изчезающие заметки")

    if not os.path.exists(folder_path):
        print(f"❌ Папка не найдена: {source_folder}")
        return {}

    notes = []
    for file in Path(folder_path).rglob("*.md"):
        try:
            with open(file, 'r', encoding='utf-8') as f:
                content = f.read()

            notes.append({
                'path': str(file),
                'name': file.stem,
                'content': content,
                'size': len(content)
            })
        except Exception as e:
            print(f"⚠️  Не удалось прочитать {file}: {e}")

    return notes

def group_notes_by_topic(notes, api_key):
    """Группировать заметки по темам через AI"""

    if not notes:
        return {}

    # Подготовка списка заметок
    notes_list = ""
    for i, note in enumerate(notes, 1):
        preview = note['content'][:200].replace('\n', ' ')
        notes_list += f"\n{i}. **{note['name']}**\n   Содержание: {preview}...\n"

    client = OpenAI(api_key=api_key)

    prompt = f"""Ты эксперт по организации заметок.

У меня есть {len(notes)} заметок:

{notes_list}

**Твоя задача:**

1. Сгруппируй заметки по темам/проектам
2. Для каждой группы предложи название черновика
3. Укажи какие заметки объединить

**Формат ответа (JSON):**
```json
{{
  "groups": [
    {{
      "draft_name": "Название черновика",
      "notes": ["Заметка 1", "Заметка 2"],
      "reason": "Почему эти заметки связаны"
    }}
  ]
}}
```

ВАЖНО: Группируй только действительно связанные заметки!
"""

    try:
        print("🤖 Анализирую заметки и группирую по темам...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты эксперт по организации знаний и заметок."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        result = response.choices[0].message.content.strip()

        # Извлекаем JSON
        if "```json" in result:
            result = result.split("```json")[1].split("```")[0]
        elif "```" in result:
            result = result.split("```")[1].split("```")[0]

        import json
        groups = json.loads(result.strip())

        return groups

    except Exception as e:
        print(f"❌ Ошибка при группировке: {e}")
        return {}

def create_draft(notes_to_merge, draft_name, vault_path, api_key):
    """Создать черновик из нескольких заметок"""

    # Объединяем содержимое
    combined_content = ""
    for note in notes_to_merge:
        combined_content += f"\n\n---\n\n## Из заметки: {note['name']}\n\n{note['content']}\n"

    # Просим AI структурировать
    client = OpenAI(api_key=api_key)

    prompt = f"""Ты эксперт по структурированию заметок.

Объедини эти заметки в один структурированный черновик:

{combined_content}

**Твоя задача:**

1. Создай единый структурированный документ
2. Убери дубликаты
3. Организуй информацию логично
4. Сохрани всю важную информацию
5. Добавь заголовки и структуру

**Формат:** Markdown, на русском языке.
**Название черновика:** {draft_name}
"""

    try:
        print(f"🤖 Создаю черновик: {draft_name}")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты эксперт по структурированию информации."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )

        structured_content = response.choices[0].message.content.strip()

        # Добавляем метаданные
        today = datetime.now().strftime('%Y-%m-%d')
        draft = f"""---
created: {today}
updated: {today}
status: черновик
source_notes: {', '.join([n['name'] for n in notes_to_merge])}
---

# {draft_name}

{structured_content}

---

## 📝 История

Черновик создан из заметок:
{chr(10).join([f'- [[{n["name"]}]]' for n in notes_to_merge])}

Дата создания: {today}
"""

        # Сохраняем черновик
        draft_path = os.path.join(vault_path, "3. Черновики", f"{draft_name}.md")
        os.makedirs(os.path.dirname(draft_path), exist_ok=True)

        with open(draft_path, 'w', encoding='utf-8') as f:
            f.write(draft)

        print(f"✅ Черновик создан: {draft_path}")

        # Перемещаем исходные заметки в архив
        archive_folder = os.path.join(vault_path, "7. Архив", "Объединённые заметки")
        os.makedirs(archive_folder, exist_ok=True)

        for note in notes_to_merge:
            archive_path = os.path.join(archive_folder, os.path.basename(note['path']))
            os.rename(note['path'], archive_path)
            print(f"   📦 Архивировано: {note['name']}")

        return draft_path

    except Exception as e:
        print(f"❌ Ошибка при создании черновика: {e}")
        return None

def main():
    vault_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Получаем API ключ
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        env_file = os.path.join(vault_path, '.env')
        if os.path.exists(env_file):
            with open(env_file, 'r') as f:
                for line in f:
                    if line.startswith('OPENAI_API_KEY='):
                        api_key = line.split('=', 1)[1].strip()
                        break

    if not api_key:
        print("❌ OPENAI_API_KEY не найден")
        sys.exit(1)

    print("📊 Объединение исчезающих заметок в черновики...")

    # Находим заметки
    notes = find_related_notes(vault_path)
    print(f"✅ Найдено заметок: {len(notes)}")

    if not notes:
        print("ℹ️  Заметок для объединения не найдено")
        return

    # Группируем по темам
    groups = group_notes_by_topic(notes, api_key)

    if not groups or 'groups' not in groups:
        print("ℹ️  Группы не найдены")
        return

    # Создаём черновики
    created_drafts = []
    for group in groups['groups']:
        draft_name = group['draft_name']
        note_names = group['notes']

        # Находим заметки по именам
        notes_to_merge = [n for n in notes if n['name'] in note_names]

        if len(notes_to_merge) > 0:
            print(f"\n📝 Группа: {draft_name}")
            print(f"   Заметок: {len(notes_to_merge)}")
            print(f"   Причина: {group.get('reason', 'Не указана')}")

            draft_path = create_draft(notes_to_merge, draft_name, vault_path, api_key)
            if draft_path:
                created_drafts.append(draft_name)

    print(f"\n✅ Создано черновиков: {len(created_drafts)}")
    for draft in created_drafts:
        print(f"   - {draft}")

if __name__ == "__main__":
    main()
