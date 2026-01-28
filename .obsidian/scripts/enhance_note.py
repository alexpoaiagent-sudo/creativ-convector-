#!/usr/bin/env python3
"""
AI помощник для работы с заметкой
Добавляет AI анализ и рекомендации прямо в текущую заметку.
Поддерживает Claude (Anthropic) и ChatGPT (OpenAI).
"""

import os
import sys

# Добавляем путь к скриптам
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
from ai_provider import get_provider


def enhance_note_inline(file_path, provider):
    """Улучшить заметку, добавив AI анализ в конец"""

    # Читаем заметку
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"Ошибка чтения файла: {e}")
        return False

    # Проверяем, есть ли уже AI анализ
    if "## AI Помощник" in content:
        print("AI анализ уже есть в заметке. Обновляю...")
        content = content.split("## AI Помощник")[0].rstrip()
        # Убрать разделитель перед секцией
        if content.endswith("---"):
            content = content[:-3].rstrip()

    system_prompt = "Ты эксперт по работе со знаниями и заметками."

    user_prompt = f"""Проанализируй эту заметку и предоставь:

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

Ответ должен быть кратким, структурированным, на русском языке, в формате Markdown."""

    try:
        print(f"[{provider.name}] Анализирую заметку...")

        ai_section = provider.chat(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=1500,
            temperature=0.7
        )

        # Добавляем AI анализ в конец заметки
        enhanced_content = f"""{content}

---

## AI Помощник

> Провайдер: **{provider.name}** ({provider.model})

{ai_section}

---

*AI анализ создан автоматически. Для обновления: Cmd+P -> "AI: Enhance Note"*
"""

        # Сохраняем
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(enhanced_content)

        print(f"[{provider.name}] Заметка улучшена! AI анализ добавлен.")
        return True

    except Exception as e:
        print(f"Ошибка: {e}")
        return False


def main():
    if len(sys.argv) < 2:
        print("Использование: python3 enhance_note.py <путь_к_заметке> [claude|openai]")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"Файл не найден: {file_path}")
        sys.exit(1)

    # Определяем провайдера
    provider_name = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        provider = get_provider(provider_name)
    except (ValueError, ImportError) as e:
        print(f"Ошибка: {e}")
        sys.exit(1)

    enhance_note_inline(file_path, provider)


if __name__ == "__main__":
    main()
