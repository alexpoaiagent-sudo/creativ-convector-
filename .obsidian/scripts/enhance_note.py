#!/usr/bin/env python3
"""
AI помощник для работы с заметкой
Добавляет AI анализ и рекомендации прямо в текущую заметку
"""

import os
import sys
from openai import OpenAI

def enhance_note_inline(file_path, api_key):
    """Улучшить заметку, добавив AI анализ в конец"""

    # Читаем заметку
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return False

    # Проверяем, есть ли уже AI анализ
    if "## 🤖 AI Помощник" in content:
        print("ℹ️  AI анализ уже есть в заметке. Обновляю...")
        # Удаляем старый анализ
        content = content.split("## 🤖 AI Помощник")[0].rstrip()

    client = OpenAI(api_key=api_key)

    prompt = f"""Ты AI помощник для работы с заметками в Obsidian.

Проанализируй эту заметку и предоставь:

1. **Краткое резюме** (2-3 предложения)
2. **Ключевые идеи** (список)
3. **Что доработать**:
   - Какие части неполные?
   - Что нужно уточнить?
   - Какие вопросы остались открытыми?
4. **Следующие шаги** (конкретные действия)
5. **Связи с другими темами** (какие темы/проекты связаны)
6. **Теги** (предложи 3-5 релевантных тегов)

Заметка:
---
{content}
---

Ответ должен быть кратким, структурированным, на русском языке, в формате Markdown.
"""

    try:
        print("🤖 Анализирую заметку...")

        response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Ты эксперт по работе со знаниями и заметками."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=1500
        )

        ai_section = response.choices[0].message.content.strip()

        # Добавляем AI анализ в конец заметки
        enhanced_content = f"""{content}

---

## 🤖 AI Помощник

{ai_section}

---

*AI анализ создан автоматически. Для обновления: `Cmd + P` → "AI: Enhance Note"*
"""

        # Сохраняем
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(enhanced_content)

        print(f"✅ Заметка улучшена! AI анализ добавлен в конец файла.")
        return True

    except Exception as e:
        print(f"❌ Ошибка: {e}")
        return False

def main():
    if len(sys.argv) < 2:
        print("❌ Использование: python3 enhance_note.py <путь_к_заметке>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"❌ Файл не найден: {file_path}")
        sys.exit(1)

    # Получаем API ключ
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        # Пробуем прочитать из .env
        vault_path = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
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

    enhance_note_inline(file_path, api_key)

if __name__ == "__main__":
    main()
