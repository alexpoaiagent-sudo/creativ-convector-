#!/usr/bin/env python3
"""
Генератор недельного отчёта из всех заметок
Собирает все заметки за неделю и создаёт сводку
"""

import os
import sys
from datetime import datetime, timedelta
from pathlib import Path
from openai import OpenAI

def get_weekly_notes(vault_path, days=7):
    """Получить все заметки за последние N дней"""

    cutoff_date = datetime.now() - timedelta(days=days)
    notes = []

    # Папки для поиска заметок
    search_folders = [
        "0.Черновики",
        "0.Входящие",
        "Изчезающие заметки",
        "Черновики по приоритетным проектам"
    ]

    for folder in search_folders:
        folder_path = os.path.join(vault_path, folder)
        if not os.path.exists(folder_path):
            continue

        for file in Path(folder_path).rglob("*.md"):
            # Проверяем дату модификации
            mtime = datetime.fromtimestamp(file.stat().st_mtime)

            if mtime >= cutoff_date:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    notes.append({
                        'path': str(file.relative_to(vault_path)),
                        'name': file.name,
                        'date': mtime.strftime('%Y-%m-%d %H:%M'),
                        'content': content,
                        'size': len(content)
                    })
                except Exception as e:
                    print(f"⚠️  Не удалось прочитать {file}: {e}")

    # Сортируем по дате
    notes.sort(key=lambda x: x['date'], reverse=True)

    return notes

def generate_weekly_summary(notes):
    """Создать сводку заметок"""

    if not notes:
        return "## 📝 Заметки за неделю\n\nЗаметок не найдено."

    summary = f"## 📝 Заметки за неделю ({len(notes)} заметок)\n\n"

    for note in notes:
        # Берём первые 200 символов как превью
        preview = note['content'][:200].replace('\n', ' ').strip()
        if len(note['content']) > 200:
            preview += "..."

        summary += f"### 📄 {note['name']}\n"
        summary += f"**Дата:** {note['date']} | **Путь:** `{note['path']}`\n\n"
        summary += f"> {preview}\n\n"
        summary += "---\n\n"

    return summary

def analyze_weekly_notes(notes, api_key):
    """Анализ всех заметок через AI"""

    if not notes:
        return "Заметок для анализа не найдено."

    # Подготовка контекста для AI
    notes_context = ""
    for i, note in enumerate(notes, 1):
        notes_context += f"\n### Заметка {i}: {note['name']}\n"
        notes_context += f"Дата: {note['date']}\n"
        notes_context += f"Содержание:\n{note['content'][:1000]}\n"  # Первые 1000 символов
        notes_context += "\n---\n"

    client = OpenAI(api_key=api_key)

    prompt = f"""Ты эксперт по продуктивности и стратегическому планированию.

Проанализируй все заметки за неделю и создай подробный отчёт:

**Заметки ({len(notes)} шт.):**
{notes_context}

**Твоя задача:**

1. **Общий обзор**: Какие темы и проекты обсуждались?
2. **Ключевые инсайты**: Какие важные мысли и идеи были зафиксированы?
3. **Прогресс**: Что было сделано? Какие достижения?
4. **Незавершённое**: Что требует доработки или продолжения?
5. **Рекомендации по каждой заметке**:
   - Что нужно доработать?
   - Какие следующие шаги?
   - Какие связи с другими заметками?
6. **Приоритеты на следующую неделю**: Что самое важное?
7. **Паттерны и тренды**: Какие закономерности видны в работе?

Ответ должен быть структурированным, на русском языке, в формате Markdown.
"""

    try:
        print("🤖 Анализирую заметки через AI...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты эксперт по продуктивности, стратегическому планированию и работе со знаниями."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=3000
        )

        return response.choices[0].message.content.strip()

    except Exception as e:
        return f"❌ Ошибка при анализе: {e}"

def main():
    vault_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

    # Получаем API ключ
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        # Пробуем прочитать из .env
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

    print("📊 Генерирую недельный отчёт...")

    # Собираем заметки за неделю
    notes = get_weekly_notes(vault_path, days=7)
    print(f"✅ Найдено заметок: {len(notes)}")

    # Создаём сводку
    summary = generate_weekly_summary(notes)

    # Анализируем через AI
    ai_analysis = analyze_weekly_notes(notes, api_key)

    # Создаём итоговый отчёт
    today = datetime.now()
    week_start = (today - timedelta(days=7)).strftime('%d.%m.%Y')
    week_end = today.strftime('%d.%m.%Y')

    report = f"""# 📊 Недельный отчёт: {week_start} - {week_end}

**Дата создания:** {today.strftime('%Y-%m-%d %H:%M')}

---

{summary}

---

# 🤖 AI Анализ недели

{ai_analysis}

---

## 📌 Следующие шаги

- [ ] Просмотреть рекомендации по каждой заметке
- [ ] Доработать незавершённые заметки
- [ ] Создать связи между связанными заметками
- [ ] Определить приоритеты на следующую неделю

---

*Отчёт создан автоматически. Для обновления запустите: `python3 .obsidian/scripts/weekly_report.py`*
"""

    # Сохраняем отчёт
    report_path = os.path.join(vault_path, "Недельный отчёт", f"Отчёт {week_start} - {week_end}.md")

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ Отчёт сохранён: {report_path}")
    print(f"\n📊 Статистика:")
    print(f"   - Заметок проанализировано: {len(notes)}")
    print(f"   - Общий объём текста: {sum(n['size'] for n in notes)} символов")

if __name__ == "__main__":
    main()
