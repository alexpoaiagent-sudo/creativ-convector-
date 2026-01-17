#!/usr/bin/env python3
"""
Генератор недельного отчёта с конкретными заметками и связями
"""

import os
import sys
import re
from datetime import datetime, timedelta
from pathlib import Path
from openai import OpenAI

def get_weekly_notes(vault_path, days=7):
    """Получить все заметки за последние N дней"""

    cutoff_date = datetime.now() - timedelta(days=days)
    notes = []

    # Папки для поиска заметок
    search_folders = [
        "1. Входящие",
        "2. Исчезающие",
        "3. Черновики",
        "4. Проекты",
        # Старые папки для совместимости
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
            mtime = datetime.fromtimestamp(file.stat().st_mtime)
            ctime = datetime.fromtimestamp(file.stat().st_ctime)

            if mtime >= cutoff_date:
                try:
                    with open(file, 'r', encoding='utf-8') as f:
                        content = f.read()

                    # Определяем статус заметки
                    status = "📝 Черновик"
                    if "1. Входящие" in str(file) or "0.Входящие" in str(file):
                        status = "📥 Входящая"
                    elif "2. Исчезающие" in str(file) or "Изчезающие заметки" in str(file):
                        status = "⏱️ Исчезающая"
                    elif "4. Проекты" in str(file) or "Черновики по приоритетным проектам" in str(file):
                        status = "⭐ Приоритетный проект"

                    # Извлекаем существующие ссылки
                    links = re.findall(r'\[\[(.*?)\]\]', content)

                    notes.append({
                        'path': str(file.relative_to(vault_path)),
                        'name': file.stem,  # Имя без .md
                        'full_name': file.name,
                        'date': mtime.strftime('%Y-%m-%d %H:%M'),
                        'created': ctime.strftime('%Y-%m-%d'),
                        'content': content,
                        'size': len(content),
                        'status': status,
                        'folder': str(file.parent.relative_to(vault_path)),
                        'links': links
                    })
                except Exception as e:
                    print(f"⚠️  Не удалось прочитать {file}: {e}")

    notes.sort(key=lambda x: x['date'], reverse=True)
    return notes

def analyze_notes_with_links(notes, api_key):
    """Анализ заметок с созданием связей"""

    if not notes:
        return "Заметок для анализа не найдено.", {}

    # Подготовка контекста
    notes_list = ""
    for i, note in enumerate(notes, 1):
        preview = note['content'][:500].replace('\n', ' ')
        notes_list += f"\n{i}. **{note['name']}** ({note['status']})\n"
        notes_list += f"   Папка: {note['folder']}\n"
        notes_list += f"   Содержание: {preview}...\n"

    client = OpenAI(api_key=api_key)

    prompt = f"""Ты эксперт по управлению знаниями и работе с заметками.

Проанализируй эти {len(notes)} заметок за неделю:

{notes_list}

**Твоя задача:**

1. **Для КАЖДОЙ заметки** предоставь:
   - Краткое резюме (1-2 предложения)
   - Ключевые темы
   - Статус работы (завершена/требует доработки/в процессе)
   - Конкретные рекомендации что доработать
   - Следующие шаги

2. **Связи между заметками:**
   - Какие заметки связаны между собой?
   - Какие темы пересекаются?
   - Предложи конкретные связи (укажи названия заметок)

3. **Общий анализ:**
   - Основные темы недели
   - Прогресс по проектам
   - Приоритеты на следующую неделю

Формат ответа: структурированный Markdown на русском языке.
ВАЖНО: Для каждой заметки пиши конкретные рекомендации, а не общие слова!
"""

    try:
        print("🤖 Анализирую заметки и создаю связи...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты эксперт по управлению знаниями, продуктивности и работе с заметками в Obsidian."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=4000
        )

        analysis = response.choices[0].message.content.strip()

        # Извлекаем предложенные связи
        suggested_links = {}
        for note in notes:
            suggested_links[note['name']] = []
            # Ищем упоминания других заметок в анализе
            for other_note in notes:
                if other_note['name'] != note['name']:
                    if other_note['name'].lower() in analysis.lower():
                        suggested_links[note['name']].append(other_note['name'])

        return analysis, suggested_links

    except Exception as e:
        return f"❌ Ошибка при анализе: {e}", {}

def create_report(notes, analysis, suggested_links, vault_path):
    """Создать отчёт с кликабельными ссылками"""

    today = datetime.now()
    week_start = (today - timedelta(days=7)).strftime('%d.%m.%Y')
    week_end = today.strftime('%d.%m.%Y')

    report = f"""# 📊 Недельный отчёт: {week_start} - {week_end}

**Дата создания:** {today.strftime('%Y-%m-%d %H:%M')}
**Заметок обработано:** {len(notes)}

---

## 📝 Заметки за неделю

"""

    # Группируем по папкам
    by_folder = {}
    for note in notes:
        folder = note['folder']
        if folder not in by_folder:
            by_folder[folder] = []
        by_folder[folder].append(note)

    # Выводим по папкам
    for folder, folder_notes in by_folder.items():
        report += f"\n### 📁 {folder} ({len(folder_notes)} заметок)\n\n"

        for note in folder_notes:
            # Кликабельная ссылка на заметку
            report += f"#### [[{note['name']}]] {note['status']}\n\n"
            report += f"**Создана:** {note['created']} | **Изменена:** {note['date']}\n\n"

            # Превью содержимого
            preview = note['content'][:300].replace('\n', ' ').strip()
            if len(note['content']) > 300:
                preview += "..."
            report += f"> {preview}\n\n"

            # Существующие связи
            if note['links']:
                report += f"**Связи:** "
                report += ", ".join([f"[[{link}]]" for link in note['links'][:5]])
                report += "\n\n"

            # Предложенные связи
            if note['name'] in suggested_links and suggested_links[note['name']]:
                report += f"**💡 Предложенные связи:** "
                report += ", ".join([f"[[{link}]]" for link in suggested_links[note['name']][:3]])
                report += "\n\n"

            report += "---\n\n"

    # AI Анализ
    report += f"""
---

# 🤖 AI Анализ недели

{analysis}

---

## 📌 Действия

- [ ] Просмотреть каждую заметку по ссылкам выше
- [ ] Доработать заметки согласно рекомендациям
- [ ] Добавить предложенные связи между заметками
- [ ] Переместить завершённые заметки из "Входящих" в проекты

---

## 🔗 Быстрая навигация

"""

    # Добавляем быстрые ссылки на все заметки
    for note in notes:
        report += f"- [[{note['name']}]] - {note['status']}\n"

    report += f"""

---

*Отчёт создан автоматически. Все ссылки кликабельны - нажмите чтобы открыть заметку.*
"""

    return report

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

    print("📊 Генерирую недельный отчёт...")

    # Собираем заметки
    notes = get_weekly_notes(vault_path, days=7)
    print(f"✅ Найдено заметок: {len(notes)}")

    if not notes:
        print("ℹ️  Заметок за неделю не найдено")
        return

    # Анализируем и создаём связи
    analysis, suggested_links = analyze_notes_with_links(notes, api_key)

    # Создаём отчёт
    report = create_report(notes, analysis, suggested_links, vault_path)

    # Сохраняем
    today = datetime.now()
    week_start = (today - timedelta(days=7)).strftime('%d.%m.%Y')
    week_end = today.strftime('%d.%m.%Y')

    report_path = os.path.join(vault_path, "5. Отчёты", f"Отчёт {week_start} - {week_end}.md")

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(report)

    print(f"✅ Отчёт сохранён: {report_path}")
    print(f"\n📊 Статистика:")
    print(f"   - Заметок: {len(notes)}")
    print(f"   - Предложено связей: {sum(len(v) for v in suggested_links.values())}")
    print(f"\n💡 Откройте отчёт в Obsidian - все ссылки кликабельны!")

if __name__ == "__main__":
    main()
