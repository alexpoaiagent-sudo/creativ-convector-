#!/usr/bin/env python3
"""
AI Agent для анализа недельных отчётов в Obsidian
"""

import os
import sys
from openai import OpenAI

def analyze_report(file_path):
    """Analyze weekly report using OpenAI"""

    # Read the report
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Ошибка чтения файла: {e}")
        return None

    # Get API key
    api_key = os.environ.get('OPENAI_API_KEY')
    if not api_key:
        print("❌ OPENAI_API_KEY не установлен")
        print("Установите ключ: export OPENAI_API_KEY='your-key'")
        return None

    client = OpenAI(api_key=api_key)

    prompt = f"""Ты эксперт по стратегическому планированию и анализу продуктивности.

Проанализируй этот недельный отчёт и предоставь:

1. **Анализ достижений**: Что сделано хорошо?
2. **Выявление паттернов**: Какие тренды видны?
3. **Рекомендации**: Что улучшить на следующей неделе?
4. **Приоритеты**: Что самое важное?
5. **Риски**: Какие потенциальные проблемы?

Отчёт:
---
{content}
---

Предоставь структурированный анализ на русском языке в формате Markdown.
"""

    try:
        print("🤖 Анализирую отчёт...")

        response = client.chat.completions.create(
            model="gpt-4",
            messages=[
                {"role": "system", "content": "Ты эксперт по стратегическому планированию и продуктивности."},
                {"role": "user", "content": prompt}
            ],
            temperature=0.7,
            max_tokens=2000
        )

        analysis = response.choices[0].message.content.strip()

        # Save analysis
        output_path = file_path.replace('.md', ' - AI Анализ.md')
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write(f"# 🤖 AI Анализ отчёта\n\n")
            f.write(f"**Дата анализа:** {os.popen('date').read().strip()}\n\n")
            f.write("---\n\n")
            f.write(analysis)

        print(f"✅ Анализ сохранён: {output_path}")
        return output_path

    except Exception as e:
        print(f"❌ Ошибка при анализе: {e}")
        return None

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("❌ Использование: python3 ai_agent.py <путь_к_отчёту>")
        sys.exit(1)

    file_path = sys.argv[1]

    if not os.path.exists(file_path):
        print(f"❌ Файл не найден: {file_path}")
        sys.exit(1)

    analyze_report(file_path)
